"""Project-defined informational drinking categories, independent of prediction."""
import math


def alcohol_consumption_info(questionnaire: dict) -> dict:
    drinks = questionnaire['drinks_week']
    male = questionnaire['male']
    if isinstance(drinks, bool) or not isinstance(drinks, (int, float)) or not math.isfinite(drinks) or not 0 <= drinks <= 200:
        raise ValueError('drinks_week must be finite and between 0 and 200')
    if isinstance(male, bool) or male not in (0, 1):
        raise ValueError('male must be 0 or 1')
    elevated_from = 15 if male == 1 else 8
    # Check critical first: it overrides the overlapping elevated category.
    category = 'critical' if drinks >= 20 else 'elevated' if drinks >= elevated_from else 'low'
    return {
        'category': category,
        'label': {'low': 'Low risk', 'elevated': 'Elevated', 'critical': 'Critical'}[category],
        'drinks_week': drinks,
        'sex_label': 'Men' if male == 1 else 'Women',
        'model_independent': True,
        'ranges': [
            {'category': 'low', 'label': 'Low risk', 'women': '0–7 drinks', 'men': '0–14 drinks'},
            {'category': 'elevated', 'label': 'Elevated', 'women': '8 or more drinks', 'men': '15 or more drinks'},
            {'category': 'critical', 'label': 'Critical', 'women': '20 or more drinks', 'men': '20 or more drinks'},
        ],
        'range_note': 'Ranges are per week. At 20 or more drinks, Critical takes precedence. '
                      'For fractional weekly averages, Elevated starts at 8 for women or 15 for men; values below those thresholds stay in Low risk.',
        'caveat': 'Project-defined informational categories, not validated probabilities of liver disease or a clinical severity scale. '
                  'Low risk does not mean drinking is safe. This separate indicator does not change the model prediction.',
    }
