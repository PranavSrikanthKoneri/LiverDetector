"""project(): deterministic fibrosis progression over time (not ML).

Rates from Singh et al., Clin Gastroenterol Hepatol 2015 (meta-analysis of
paired-biopsy studies): on average one fibrosis stage per 14.3 years in NAFL
and per 7.1 years in NASH. Population averages, not personal predictions.
"""
from tabular.data import STAGES

# Years per fibrosis stage: (point estimate, CI shorter bound, CI longer bound).
# TODO verify CI against the paper abstract.
YEARS_PER_STAGE_SLOW = (14.3, 9.1, 50.0)   # NAFL ("slower-progression scenario")
YEARS_PER_STAGE_FAST = (7.1, 4.8, 14.3)    # NASH

STAGE_START = {"F0-F1": 0.5, "F2": 2.0, "F3": 3.0, "F4": 4.0}
MAX_STAGE = 4.0
SOURCE = "Singh et al. 2015; population average, not a personal prediction"


def project(stage: str, years: float, slow: bool) -> dict:
    if stage not in STAGE_START:
        raise ValueError(f"stage must be one of {STAGES}, got {stage!r}")
    if isinstance(years, bool) or not isinstance(years, (int, float)) or not 0 <= years <= 50:
        raise ValueError(f"years must be a number between 0 and 50, got {years!r}")
    if not isinstance(slow, bool):
        raise ValueError(f"slow must be True or False, got {slow!r}")

    rate, shortest, longest = YEARS_PER_STAGE_SLOW if slow else YEARS_PER_STAGE_FAST
    start = STAGE_START[stage]

    def at(years_per_stage):
        return min(MAX_STAGE, start + years / years_per_stage)

    return {
        "stage_value": at(rate),
        "low": at(longest),    # slower progression -> lower stage
        "high": at(shortest),  # faster progression -> higher stage
        "years_per_stage": rate,
        "source": SOURCE,
    }
