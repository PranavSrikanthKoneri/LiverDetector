"""Project-defined informational drinking categories, independent of prediction."""
import math
import json
from pathlib import Path

POLICY = json.loads(Path(__file__).with_name("alcohol_policy.json").read_text(encoding="utf-8"))


def alcohol_consumption_info(questionnaire: dict) -> dict:
    drinks = questionnaire['drinks_week']
    male = questionnaire['male']
    if isinstance(drinks, bool) or not isinstance(drinks, (int, float)) or not math.isfinite(drinks) or not 0 <= drinks <= POLICY["maximum_drinks"]:
        raise ValueError('drinks_week must be finite and between 0 and 200')
    if isinstance(male, bool) or male not in (0, 1):
        raise ValueError('male must be 0 or 1')
    elevated_from = POLICY["elevated_from"]["men" if male == 1 else "women"]
    # Check critical first: it overrides the overlapping elevated category.
    category = 'critical' if drinks >= POLICY["critical_from"] else 'elevated' if drinks >= elevated_from else 'low'
    return {
        'category': category,
        'label': {'low': 'Low risk', 'elevated': 'Elevated', 'critical': 'Critical'}[category],
        'drinks_week': drinks,
        'sex_label': 'Men' if male == 1 else 'Women',
        'model_independent': True,
        'ranges': POLICY['ranges'],
        'range_note': POLICY['range_note'],
        'caveat': POLICY['caveat'],
    }
