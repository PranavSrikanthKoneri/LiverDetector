import pytest
from demo.alcohol import alcohol_consumption_info
from demo import pipeline


@pytest.mark.parametrize('male,drinks,expected', [
    (0, 0, 'low'), (0, 7, 'low'), (0, 7.9, 'low'), (0, 8, 'elevated'),
    (1, 0, 'low'), (1, 14, 'low'), (1, 14.9, 'low'), (1, 15, 'elevated'),
    (0, 19.9, 'elevated'), (1, 19.9, 'elevated'),
    (0, 20, 'critical'), (1, 20, 'critical'), (0, 200, 'critical'), (1, 200, 'critical'),
])
def test_ranges_and_critical_precedence(male, drinks, expected):
    q = {'male': male, 'drinks_week': drinks}
    result = alcohol_consumption_info(q)
    assert result['category'] == expected
    assert result['drinks_week'] == drinks
    assert q == {'male': male, 'drinks_week': drinks}
    assert result['model_independent'] is True


@pytest.mark.parametrize('male,drinks', [(None, 2), (True, 2), (2, 2), (0, None), (0, True), (0, -1), (1, float('nan')), (1, float('inf'))])
def test_invalid_values_do_not_default_to_low(male, drinks):
    with pytest.raises(ValueError):
        alcohol_consumption_info({'male': male, 'drinks_week': drinks})


def test_pipeline_keeps_information_separate_from_model(monkeypatch):
    q = {'age': 50, 'male': 0, 'bmi': 25, 'waist_cm': None, 'diabetes': 0, 'drinks_week': 20}
    expected = {'stage': 'F0-F1', 'probs': [.98, .01, .01, 0], 'p_ge_F2': .02}
    seen = []
    def predict(answers):
        seen.append(answers.copy())
        return expected.copy()
    monkeypatch.setattr(pipeline, 'predict_stage', predict)
    monkeypatch.setattr(pipeline, 'load_and_locate', lambda _: {'liver_slices': [], 'boxes': {}, 'spacing': [1, 1, 1]})
    monkeypatch.setattr(pipeline, 'measure_liver', lambda _: {'status': 'ok', 'fat_pct': 0, 'steatosis': False})
    result = pipeline.run_pipeline('unused.zip', q)
    assert seen == [q]
    assert result['risk'] == {**expected, 'tier': 'low'}
    assert result['alcohol_consumption']['category'] == 'critical'
    assert 'alcohol_caveat' not in result['recommendation']
