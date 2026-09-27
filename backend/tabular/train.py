"""Train the questionnaire-only fibrosis-stage model and write the model card.

    python -m tabular.train

5-fold stratified CV (out-of-fold probabilities) on NHANES 2017-2018, a
comparison against the NAFLD Fibrosis Score on the same people, then a final
fit on all data saved to tabular/risk_model.joblib + tabular/model_card.json.
"""
import json
import os

import joblib
import numpy as np
from sklearn.metrics import confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedKFold
from xgboost import XGBClassifier

from tabular.data import FEATURES, STAGES, load_nhanes

HERE = os.path.dirname(__file__)
MODEL_PATH = os.path.join(HERE, "risk_model.joblib")
CARD_PATH = os.path.join(HERE, "model_card.json")


def make_model() -> XGBClassifier:
    # No class weights: we want calibrated-ish probabilities, not balanced recall.
    return XGBClassifier(objective="multi:softprob", num_class=4, n_estimators=300, max_depth=3,
                         learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=42)


def nafld_fibrosis_score(df):
    """NFS = -1.675 + 0.037 age + 0.094 BMI + 1.13 IFG/diabetes + 0.99 AST/ALT
    - 0.013 platelets (10^9/L) - 0.66 albumin (g/dL)."""
    ifg_or_diabetes = ((df["diabetes"] >= 1) | (df["glucose"] >= 100)).astype(float)
    return (-1.675 + 0.037 * df["age"] + 0.094 * df["bmi"] + 1.13 * ifg_or_diabetes
            + 0.99 * df["ast"] / df["alt"] - 0.013 * df["platelets"] - 0.66 * df["albumin_gdl"])


def cross_validate(X, y, n_splits=5):
    """Out-of-fold probabilities plus per-fold AUROC for >=F2 and >=F3."""
    oof = np.zeros((len(y), 4))
    fold_auc = {"ge_F2": [], "ge_F3": []}
    for tr, te in StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42).split(X, y):
        m = make_model().fit(X.iloc[tr], y.iloc[tr])
        p = m.predict_proba(X.iloc[te])
        oof[te] = p
        fold_auc["ge_F2"].append(roc_auc_score(y.iloc[te] >= 1, p[:, 1:].sum(1)))
        fold_auc["ge_F3"].append(roc_auc_score(y.iloc[te] >= 2, p[:, 2:].sum(1)))
    return oof, fold_auc


def main():
    df = load_nhanes("J")
    X, y = df[FEATURES], df["stage"]
    counts = {STAGES[k]: int(v) for k, v in y.value_counts().sort_index().items()}
    print(f"\nn = {len(df)}; classes: {counts}")

    # ---- 5-fold CV
    oof, fold_auc = cross_validate(X, y)
    f2 = (float(np.mean(fold_auc["ge_F2"])), float(np.std(fold_auc["ge_F2"])))
    f3 = (float(np.mean(fold_auc["ge_F3"])), float(np.std(fold_auc["ge_F3"])))
    print("\n== 5-fold CV (out-of-fold), questionnaire only")
    print(f"AUROC >=F2: {f2[0]:.3f} +/- {f2[1]:.3f}   folds {np.round(fold_auc['ge_F2'], 3).tolist()}")
    print(f"AUROC >=F3: {f3[0]:.3f} +/- {f3[1]:.3f}   folds {np.round(fold_auc['ge_F3'], 3).tolist()}")

    pred = oof.argmax(1)
    cm = confusion_matrix(y, pred, labels=[0, 1, 2, 3])
    print("\nconfusion matrix (rows = true, cols = argmax prediction):")
    print("        " + " ".join(f"{s:>6s}" for s in STAGES))
    for i, row in enumerate(cm):
        print(f"{STAGES[i]:>6s}  " + " ".join(f"{v:6d}" for v in row))
    recall = {STAGES[i]: float(cm[i, i] / cm[i].sum()) for i in range(4)}
    print("per-class recall: " + ", ".join(f"{k} {v:.3f}" for k, v in recall.items()))
    print(f"predicted class counts: {dict(zip(STAGES, np.bincount(pred, minlength=4).tolist()))}")

    # ---- NFS baseline on the subset with all bloodwork, vs our OOF probs on the same rows
    nfs_cols = ["age", "bmi", "diabetes", "glucose", "ast", "alt", "platelets", "albumin_gdl"]
    sub = df[nfs_cols].notna().all(axis=1) & (df["alt"] > 0)
    nfs = nafld_fibrosis_score(df[sub])
    ys, ps = y[sub], oof[sub.values]
    nfs_f2, nfs_f3 = roc_auc_score(ys >= 1, nfs), roc_auc_score(ys >= 2, nfs)
    our_f2, our_f3 = roc_auc_score(ys >= 1, ps[:, 1:].sum(1)), roc_auc_score(ys >= 2, ps[:, 2:].sum(1))
    print(f"\n== NFS baseline (needs bloodwork) vs ours (questionnaire only), same {int(sub.sum())} people")
    print(f"             ours    NFS")
    print(f"AUROC >=F2  {our_f2:.3f}  {nfs_f2:.3f}")
    print(f"AUROC >=F3  {our_f3:.3f}  {nfs_f3:.3f}")

    # ---- final fit on all data + model card
    model = make_model().fit(X, y)
    joblib.dump(model, MODEL_PATH)
    card = {
        "model": "XGBClassifier multi:softprob (n_estimators=300, max_depth=3, lr=0.05)",
        "features": FEATURES,
        "classes": STAGES,
        "n_train": int(len(df)),
        "class_counts": counts,
        "cv_auroc_ge_F2": {"mean": round(f2[0], 4), "sd": round(f2[1], 4)},
        "cv_auroc_ge_F3": {"mean": round(f3[0], 4), "sd": round(f3[1], 4)},
        "cv_recall_per_class": {k: round(v, 4) for k, v in recall.items()},
        "nfs_auroc_ge_F2": round(float(nfs_f2), 4),
        "nfs_auroc_ge_F3": round(float(nfs_f3), 4),
        "ours_auroc_on_nfs_subset": {"ge_F2": round(float(our_f2), 4), "ge_F3": round(float(our_f3), 4)},
        "n_nfs_subset": int(sub.sum()),
        "label_source": "NHANES 2017-2018 transient elastography LSM; cutoffs 8.2/9.7/13.6 kPa, Eddowes 2019",
        "limitations": [
            "NHANES survey weights not applied; metrics describe the sample, not the US population",
            "Elastography (LSM) is a proxy for biopsy-staged fibrosis",
            "NFS computed with non-fasting serum glucose from the biochemistry panel",
            "Not diagnostic; for education and research only",
        ],
    }
    with open(CARD_PATH, "w") as f:
        json.dump(card, f, indent=2)
    print(f"\nsaved {os.path.relpath(MODEL_PATH)} and {os.path.relpath(CARD_PATH)}")


if __name__ == "__main__":
    main()
