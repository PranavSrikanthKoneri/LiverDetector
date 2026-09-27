# Integration audit

Remote heads fetched and reviewed during this integration:

| Branch | Head | Relationship to integration before this work |
| --- | --- | --- |
| main | 1710e1c | Already included |
| imaging-input | ce46b2c | Already included |
| tabular-model | 3adb7db | Already included |
| demo-pipeline | 4674459 | Already included |
| segmentation-math | 70b940c | Missing; merged |
| frontend | 6421afa | Missing; merged |

Integration was first fast-forwarded from 1710e1c to c565525, then both missing
branches were merged together without conflicts. No remote branch was deleted
or force-pushed. The merge used the identity provided by the repository owner.

## Gaps resolved

- Empty integration `imaging/analyze.py` replaced by the segmentation branch.
- Added shared `segment_and_measure`: the CLI, demo and API use the same numerical
  measurement path, including fallback checks, clipping diagnostics, and texture QC.
- Added the missing FastAPI adapter and frontend `/api` proxy.
- Replaced the default mock response with the backend result adapter.
- Corrected numeric sex/diabetes questionnaire encoding and fractional drinks.
- Kept clipping warnings and review-required texture QC visible in the dashboard.
- Replaced simulated scan drawings with real in-phase previews and selected masks.
- Moved Python packages/tests/scripts to backend and installed them with preserved
  import names. Existing saved model and QC resource are included as package data.
- Added root setup documentation and constrained pytest discovery to active tests.

Empty `__init__.py` files were intentional package markers, not missing code.
The empty imaging/tabular `.gitkeep` markers were removed now those folders have
implementation. Earlier local `models/` work and `debug/` results were preserved.

## Verification

- Backend: 99 passed, 1 optional real-data test skipped (three upstream SWIG warnings).
- Frontend: production build, lint and result-adapter test passed. Build reports a
  non-blocking bundle-size warning for the chart-containing JavaScript bundle.
- Real GPU demo: patient 33 returned five previews, 11.114634% fat, and texture
  `review_required` with boundary/spacing sensitivity flags, matching the previous
  diagnostic run. The example questionnaire returned p_ge_F2=0.163689; these
  example answers are not asserted to belong to the scan participant.
- No fetched remote branches remain unmerged after the merge commit ae643b6.

The branch merge is recorded in ae643b6. Layout and integration edits were reviewed
and subsequently approved by the repository owner for commit and push to integration.

## Still deliberately limited

Recommendations are rule-based, not an LLM. No missing branch contains an LLM
integration. Population projections, questionnaire risk, fat estimates and texture
QC retain the limitations documented in their component READMEs. This is a local
research demo, with no authentication or production deployment work included.
