"""Fake predict_stage / project in the exact contract shape.

Lets the frontend and backend build against the tabular stage before the
real NHANES model is trained. The numbers are made up.
"""
STAGES = ["F0-F1", "F2", "F3", "F4"]
STAGE_START = {"F0-F1": 0.5, "F2": 2.0, "F3": 3.0, "F4": 4.0}


def predict_stage_mock(q: dict) -> dict:
    # Fixed, plausible-looking probabilities (most people are F0-F1).
    probs = [0.80, 0.10, 0.06, 0.04]
    return {"stage": STAGES[probs.index(max(probs))], "probs": probs, "p_ge_F2": round(sum(probs[1:]), 4)}


def project_mock(stage: str, years: float, slow: bool) -> dict:
    rate = 14.3 if slow else 7.1  # years per fibrosis stage
    start = STAGE_START[stage]
    return {
        "stage_value": min(4.0, start + years / rate),
        "low": min(4.0, start + years / (rate * 1.5)),
        "high": min(4.0, start + years / (rate * 0.7)),
        "years_per_stage": rate,
        "source": "MOCK: Singh et al. 2015; population average, not a personal prediction",
    }
