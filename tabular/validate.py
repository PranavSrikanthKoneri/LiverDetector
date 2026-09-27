"""External (temporal) validation on NHANES 2021-2023 (cycle L).

    python -m tabular.validate

The saved model (trained only on 2017-2018) is applied unchanged to a later,
independent NHANES sample with the same elastography exam and label rule.
Adds the results to tabular/model_card.json.
"""
import json

import numpy as np
from sklearn.metrics import roc_auc_score

from tabular.data import FEATURES, STAGES, load_nhanes
from tabular.predict import _model
from tabular.train import CARD_PATH, nafld_fibrosis_score


def auc_ci(y, score, n_boot=1000, seed=0):
    """AUROC with a 95% bootstrap confidence interval."""
    rng = np.random.default_rng(seed)
    y, score = np.asarray(y), np.asarray(score)
    boots = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            boots.append(roc_auc_score(y[i], score[i]))
    return float(roc_auc_score(y, score)), float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def main():
    df = load_nhanes("L")
    y = df["stage"]
    counts = {STAGES[k]: int(v) for k, v in y.value_counts().sort_index().items()}
    print(f"\nn = {len(df)}; classes: {counts}")

    x = df[FEATURES].assign(age=df["age"].clip(upper=80)).astype(float)
    p = _model().predict_proba(x)
    p_f2, p_f3 = p[:, 1:].sum(1), p[:, 2:].sum(1)

    f2, f3 = auc_ci(y >= 1, p_f2), auc_ci(y >= 2, p_f3)
    print("\n== External validation: trained on 2017-2018, tested on 2021-2023")
    print(f"AUROC >=F2: {f2[0]:.3f} (95% CI {f2[1]:.3f}-{f2[2]:.3f})")
    print(f"AUROC >=F3: {f3[0]:.3f} (95% CI {f3[1]:.3f}-{f3[2]:.3f})")

    # Calibration: does predicted risk match the observed rate?
    print(f"\ncalibration >=F2: mean predicted {p_f2.mean():.3f} vs observed {np.mean(y >= 1):.3f}")
    q = np.quantile(p_f2, [0, 0.5, 0.8, 0.95, 1.0])
    for lo, hi, name in [(q[0], q[1], "bottom 50%"), (q[1], q[2], "50-80th pct"),
                         (q[2], q[3], "80-95th pct"), (q[3], q[4], "top 5%")]:
        m = (p_f2 >= lo) & (p_f2 <= hi)
        print(f"  {name:11s} predicted {p_f2[m].mean():.3f}  observed {np.mean(y[m] >= 1):.3f}  (n={m.sum()})")

    nfs_cols = ["age", "bmi", "diabetes", "glucose", "ast", "alt", "platelets", "albumin_gdl"]
    sub = (df[nfs_cols].notna().all(axis=1) & (df["alt"] > 0)).values
    nfs = nafld_fibrosis_score(df[sub])
    ours_sub = (roc_auc_score(y[sub] >= 1, p_f2[sub]), roc_auc_score(y[sub] >= 2, p_f3[sub]))
    nfs_auc = (roc_auc_score(y[sub] >= 1, nfs), roc_auc_score(y[sub] >= 2, nfs))
    print(f"\n== vs NFS on the same {int(sub.sum())} people")
    print(f"             ours    NFS")
    print(f"AUROC >=F2  {ours_sub[0]:.3f}  {nfs_auc[0]:.3f}")
    print(f"AUROC >=F3  {ours_sub[1]:.3f}  {nfs_auc[1]:.3f}")

    with open(CARD_PATH) as f:
        card = json.load(f)
    card["external_validation"] = {
        "data": "NHANES 2021-2023 (cycle L), same inclusion and label rules; model not retrained",
        "n": int(len(df)),
        "class_counts": counts,
        "auroc_ge_F2": {"value": round(f2[0], 4), "ci95": [round(f2[1], 4), round(f2[2], 4)]},
        "auroc_ge_F3": {"value": round(f3[0], 4), "ci95": [round(f3[1], 4), round(f3[2], 4)]},
        "mean_predicted_p_ge_F2": round(float(p_f2.mean()), 4),
        "observed_rate_ge_F2": round(float(np.mean(y >= 1)), 4),
        "n_nfs_subset": int(sub.sum()),
        "ours_auroc_on_nfs_subset": {"ge_F2": round(ours_sub[0], 4), "ge_F3": round(ours_sub[1], 4)},
        "nfs_auroc": {"ge_F2": round(nfs_auc[0], 4), "ge_F3": round(nfs_auc[1], 4)},
    }
    with open(CARD_PATH, "w") as f:
        json.dump(card, f, indent=2)
    print(f"\nadded external_validation to {CARD_PATH.split('/')[-1]}")


if __name__ == "__main__":
    main()
