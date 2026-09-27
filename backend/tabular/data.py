"""NHANES download, merge and cleaning for the fibrosis-stage model.

Public data, no login. Raw .xpt files are cached in data/nhanes/ (gitignored).
Variable names and codes verified against the NHANES 2017-2018 codebooks.
"""
import os
import urllib.request

import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "nhanes")
# cycle letter -> first year in the CDC URL
CYCLES = {"J": "2017", "L": "2021"}
FILES = ["DEMO", "BMX", "DIQ", "ALQ", "LUX", "BIOPRO", "CBC"]

FEATURES = ["age", "male", "bmi", "waist_cm", "diabetes", "drinks_week"]
STAGES = ["F0-F1", "F2", "F3", "F4"]

# Liver stiffness (kPa) cutoffs for fibrosis stage, Eddowes et al. 2019.
LSM_CUTOFFS_KPA = [8.2, 9.7, 13.6]

# ALQ121 "How often did you drink in the past 12 months?" -> days per year.
# Codebook ranges are mapped to their midpoints.
ALQ121_DAYS_PER_YEAR = {
    0: 0.0,        # never in the last year
    1: 365.0,      # every day
    2: 5.5 * 52,   # nearly every day (5-6 days/week)
    3: 3.5 * 52,   # 3-4 times a week
    4: 2 * 52,     # 2 times a week
    5: 52.0,       # once a week
    6: 2.5 * 12,   # 2-3 times a month
    7: 12.0,       # once a month
    8: 9.0,        # 7-11 times in the last year
    9: 4.5,        # 3-6 times in the last year
    10: 1.5,       # 1-2 times in the last year
}  # 77 refused / 99 don't know -> NaN

# DIQ010 "Doctor told you have diabetes": 1 yes, 2 no, 3 borderline -> contract 0/1/2.
DIQ010_TO_DIABETES = {2: 0, 3: 1, 1: 2}  # 7 refused / 9 don't know -> NaN


def download(cycle: str = "J") -> None:
    """Fetch the NHANES .xpt files for a cycle into data/nhanes/ (skips existing)."""
    os.makedirs(DATA_DIR, exist_ok=True)
    for name in FILES:
        fname = f"{name}_{cycle}.xpt"
        path = os.path.join(DATA_DIR, fname)
        if os.path.exists(path):
            continue
        url = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{CYCLES[cycle]}/DataFiles/{fname}"
        print(f"downloading {url}")
        urllib.request.urlretrieve(url, path)
        with open(path, "rb") as f:
            if not f.read(6) == b"HEADER":  # CDC serves an HTML page for missing files
                os.remove(path)
                raise RuntimeError(f"{fname} is not an XPT file; download it manually from the CDC NHANES page")


def _read(name: str, cycle: str) -> pd.DataFrame:
    df = pd.read_sas(os.path.join(DATA_DIR, f"{name}_{cycle}.xpt"), format="xport")
    # SAS xport stores 0 as a tiny float (e.g. 5.4e-79); snap those back to 0.
    num = df.select_dtypes("number").columns
    # (NaN < 1e-10 is False, so missing values stay NaN.)
    df[num] = df[num].mask(df[num].abs() < 1e-10, 0.0)
    return df


def drinks_per_week(alq111: pd.Series, alq121: pd.Series, alq130: pd.Series) -> pd.Series:
    """(days per year from ALQ121) x (drinks per drinking day, ALQ130) / 52."""
    days = alq121.map(ALQ121_DAYS_PER_YEAR)
    per_day = alq130.where(~alq130.isin([777, 999]))
    out = days * per_day / 52
    out[alq121 == 0] = 0.0   # did not drink in the past year
    out[alq111 == 2] = 0.0   # never had a drink
    return out


def stage_from_lsm(lsm_kpa: pd.Series) -> pd.Series:
    """0 = F0-F1 (<8.2), 1 = F2 (8.2-9.7), 2 = F3 (9.7-13.6), 3 = F4 (>=13.6 kPa)."""
    return pd.Series(np.digitize(lsm_kpa, LSM_CUTOFFS_KPA), index=lsm_kpa.index)


def load_nhanes(cycle: str = "J", verbose: bool = True) -> pd.DataFrame:
    """Merged, cleaned adult cohort with a reliable elastography exam.

    Columns: SEQN, the model FEATURES, lsm_kpa (label source), stage (0-3), and the NFS
    inputs (ast, alt, albumin_gdl, glucose, platelets).
    """
    download(cycle)
    t = {n: _read(n, cycle) for n in FILES}

    df = t["DEMO"][["SEQN", "RIDAGEYR", "RIAGENDR"]]
    for name, cols in [("BMX", ["BMXBMI", "BMXWAIST"]), ("DIQ", ["DIQ010"]),
                       ("ALQ", ["ALQ111", "ALQ121", "ALQ130"]),
                       ("LUX", ["LUAXSTAT", "LUXSMED", "LUXSIQR"]),
                       ("BIOPRO", ["LBXSASSI", "LBXSATSI", "LBXSAL", "LBXSGL"]),
                       ("CBC", ["LBXPLTSI"])]:
        df = df.merge(t[name][["SEQN"] + cols], on="SEQN", how="left")

    log = print if verbose else (lambda *a: None)
    log(f"[{cycle}] all participants:           {len(df)}")
    df = df[df["RIDAGEYR"] >= 18]
    log(f"[{cycle}] age >= 18:                  {len(df)}")
    df = df[df["LUAXSTAT"] == 1]
    log(f"[{cycle}] elastography complete:      {len(df)}")
    df = df[df["LUXSMED"].notna() & (df["LUXSMED"] > 0)]
    df = df[df["LUXSIQR"] / df["LUXSMED"] < 0.30]
    log(f"[{cycle}] reliable (IQR/median < 0.3): {len(df)}")

    out = pd.DataFrame({
        "SEQN": df["SEQN"].astype(int),
        "age": df["RIDAGEYR"],
        "male": (df["RIAGENDR"] == 1).astype(int),
        "bmi": df["BMXBMI"],
        "waist_cm": df["BMXWAIST"],
        "diabetes": df["DIQ010"].map(DIQ010_TO_DIABETES),
        "drinks_week": drinks_per_week(df["ALQ111"], df["ALQ121"], df["ALQ130"]),
        "lsm_kpa": df["LUXSMED"],
        "ast": df["LBXSASSI"], "alt": df["LBXSATSI"], "albumin_gdl": df["LBXSAL"],
        "glucose": df["LBXSGL"], "platelets": df["LBXPLTSI"],
    }).reset_index(drop=True)
    out["stage"] = stage_from_lsm(out["lsm_kpa"])
    return out


if __name__ == "__main__":
    d = load_nhanes("J")
    print(d[FEATURES + ["lsm_kpa"]].describe().T.round(2))
    print("missing per column:\n" + d.isna().sum().to_string())
    counts = d["stage"].value_counts().sort_index()
    print("\nclass distribution (label from LSM, Eddowes 2019 cutoffs):")
    for k, n in counts.items():
        print(f"  {STAGES[k]:6s} {n:5d}  ({100 * n / len(d):.1f}%)")
