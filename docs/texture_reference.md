# Earlier acquisition-matched texture comparison

For the implemented CHAOS measurement-quality workflow and friend instructions,
see [texture_quality.md](texture_quality.md). It includes a packaged reference
measured from all 20 training patients and requires no cohort GPU rerun.

The older `python -m imaging.texture_reference MANIFEST --out OUT` remains
available for strict acquisition-matched comparisons of native texture features.
It rejects missing scanner metadata and requires 10 compatible other patients.
That limitation remains for our existing exports. It is distinct from the new
within-scan perturbation checks and their heterogeneous CHAOS stability context.
Neither method is a disease classifier.
