"""LiverCast end-to-end demo pipeline: DICOM zip + questionnaire -> JSON result.

    python -m demo.pipeline path/to/case.zip --questionnaire demo/example_questionnaire.json

READ backend/demo/HANDOFF.md FIRST if you are extending this file (human or coding agent).

Steps, in the order POST /analyze should run them (docs/tasks.md):
  1. imaging.load.load_and_locate(zip)        Person 1  DONE
  2. imaging.analyze.segment_and_measure(...) Person 2  CONNECTED with diagnostics and texture QC
  3. tabular.predict.predict_stage(q)         Person 3  DONE
  4. tabular.progression.project(...)         Person 3  DONE
  5. recommend(...)                           Person 4  PLACEHOLDER rules, to be replaced/extended
     summarize(result) (LLM)                  Person 4  NOT HERE YET

Everything returned is JSON-serializable (no numpy arrays), ready for FastAPI.
"""
import argparse
import json
import base64
from pathlib import Path

from imaging.load import load_and_locate
from tabular.predict import predict_stage
from tabular.progression import project
from demo.alcohol import alcohol_consumption_info

DISCLAIMER = ("Not diagnostic. LiverCast is an educational estimate from population data, "
              "not a medical test. Discuss any concerns with a doctor.")

# p_ge_F2 risk tiers. Cut-offs chosen by Person 3; observed rate of >=F2 in each tier
# on the independent NHANES 2021-2023 sample (python -m tabular.validate data):
#   low          p < 0.10   68.9% of people, observed >=F2 5.9%
#   intermediate 0.10-0.25  22.4% of people, observed >=F2 18.7%
#   high         p >= 0.25   8.7% of people, observed >=F2 37.9%
RISK_TIERS = [(0.25, "high"), (0.10, "intermediate"), (0.0, "low")]

PROJECTION_YEARS = list(range(0, 21))  # frontend slider is 0-20 years


# ------------------------------------------------------------ step 2 (Person 2)

def measure_liver(img: dict) -> dict:
    """Run shared measurements, preserve QC, and encode selected masks as previews."""
    from imaging.analyze import segment_and_measure
    from imaging.cli import to_uint8
    import cv2
    import numpy as np

    r = segment_and_measure(img["ip"], img["op"], img["liver_slices"], img["boxes"], img["ts_mask"], spacing=img["spacing"])
    masks = {}
    for idx, mask in r["masks"].items():
        gray = to_uint8(img["ip"][idx])
        overlay = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (0, 255, 255), 1)
        def encode(image):
            ok, data = cv2.imencode(".png", image)
            if not ok:
                raise RuntimeError("Could not encode preview")
            return "data:image/png;base64," + base64.b64encode(data).decode("ascii")
        masks[str(idx)] = {"width": int(mask.shape[1]), "height": int(mask.shape[0]),
                           "liverPixels": int(mask.sum()), "image": encode(gray), "overlay": encode(overlay)}
    warnings = sorted({warning for report in r["quality_report"].values()
                       for warning in report["fat_measurement"]["warnings"]})
    return {"status": "ok", "fat_pct": float(r["fat_pct"]), "steatosis": bool(r["steatosis"]),
            "texture": {k: float(v) for k, v in r["texture"].items()},
            "masks": masks, "quality_report": r["quality_report"],
            "texture_quality": r["texture_quality"], "warnings": warnings,
            "texture_label": "exploratory"}


# ------------------------------------------------------------ step 5 (Person 4)

def risk_tier(p_ge_F2: float) -> str:
    return next(name for cutoff, name in RISK_TIERS if p_ge_F2 >= cutoff)


def recommend(risk: dict, liver: dict) -> dict:
    """PLACEHOLDER rule-based recommendation. Person 4: replace or extend.

    Rules that must hold whatever replaces this (docs/tasks.md + model limits):
      - plain language; general lifestyle tips only; always suggest seeing a doctor
      - never name medications; never diagnose
      - lead with p_ge_F2 / tier, NOT risk["stage"] (argmax is ~always F0-F1)
      - never say drinking lowers risk (NHANES alcohol effect is an artifact)
      - imaging (fat %) is shown alongside the risk, it is not an input to it
    """
    tier = risk_tier(risk["p_ge_F2"])
    headline = {
        "low": "Your answers suggest a lower chance of significant liver scarring.",
        "intermediate": "Your answers suggest a moderate chance of significant liver scarring.",
        "high": "Your answers suggest a higher chance of significant liver scarring.",
    }[tier]

    points = []
    if liver.get("warnings"):
        points.append("The two-echo fat estimate includes clipping warnings and needs review; zero does not establish absence of fat.")
    elif liver["status"] == "ok" and liver["steatosis"]:
        points.append(f"The MRI estimate shows extra fat in the liver (about {liver['fat_pct']:.0f}%).")
    elif liver["status"] == "ok":
        points.append(f"The MRI estimate shows little liver fat (about {liver['fat_pct']:.0f}%).")
    else:
        points.append("The MRI fat measurement is not available yet.")

    if tier == "high" or (liver["status"] == "ok" and liver["steatosis"]):
        points.append("Consider asking a doctor about a liver check-up, such as blood tests or a liver scan.")
    points += [
        "Healthy habits that support the liver: regular physical activity, a balanced diet, "
        "keeping a healthy weight, and limiting alcohol.",
        "Talk to a doctor before making changes, especially if you have diabetes or other conditions.",
    ]
    return {"tier": tier, "headline": headline, "points": points, "disclaimer": DISCLAIMER}


# ------------------------------------------------------------ pipeline

def run_pipeline(zip_path: str, questionnaire: dict) -> dict:
    # Validate the questionnaire first: it is instant, imaging takes ~1 min.
    risk = predict_stage(questionnaire)

    img = load_and_locate(zip_path)
    liver = measure_liver(img)

    projection = {
        scenario: [{"years": y, **{k: v for k, v in project(risk["stage"], y, slow).items() if k != "source"}}
                   for y in PROJECTION_YEARS]
        for scenario, slow in (("typical", False), ("slower", True))
    }
    return {
        "imaging": {
            "liver_slices": img["liver_slices"],
            "boxes": {str(k): v for k, v in img["boxes"].items()},  # JSON keys must be strings
            "spacing_mm": list(img["spacing"]),
            **liver,
        },
        "alcohol_consumption": alcohol_consumption_info(questionnaire),
        "risk": {**risk, "tier": risk_tier(risk["p_ge_F2"])},
        "projection": {"start_stage": risk["stage"], "source": project(risk["stage"], 0, True)["source"],
                       **projection},
        "recommendation": recommend(risk, liver),
        "disclaimer": DISCLAIMER,
    }


def main():
    ap = argparse.ArgumentParser(description="Run the LiverCast demo pipeline on one case.")
    ap.add_argument("zip_path")
    ap.add_argument("--questionnaire", required=True, help="JSON file with the 6 questionnaire answers")
    ap.add_argument("--out", help="also write the JSON result here")
    args = ap.parse_args()

    with open(args.questionnaire) as f:
        q = json.load(f)
    result = run_pipeline(args.zip_path, q)
    text = json.dumps(result, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as f:
            f.write(text)

    # Short human summary, then the full JSON.
    r, rec = result["risk"], result["recommendation"]
    print(f"\nrisk: P(>=F2) = {r['p_ge_F2']:.3f} -> tier {r['tier']}   (stage argmax {r['stage']})")
    print(f"liver fat: {result['imaging']['status']} {result['imaging']['fat_pct']}")
    print(f"20 y projection (typical / slower): "
          f"{result['projection']['typical'][-1]['stage_value']:.2f} / "
          f"{result['projection']['slower'][-1]['stage_value']:.2f}")
    print(rec["headline"])
    for p in rec["points"]:
        print(f"  - {p}")
    print(rec["disclaimer"])
    print("\n" + text if not args.out else f"\nfull JSON written to {args.out}")


if __name__ == "__main__":  # required: TotalSegmentator spawns worker processes
    main()
