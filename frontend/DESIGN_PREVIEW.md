# FibroLens: local design exploration

All changes are frontend-only. Six branches compare three visual directions and two motion treatments. Nothing is pushed without the user's confirmation. Existing model calculations and the API contract are unchanged.

## Compare all six on this Windows machine

These previews live in a separate clone; the original LiverDetector integration checkout is untouched. Nothing has been pushed. The clone's origin points to the local bundle, not GitHub.

```powershell
cd "E:\Personal\Build Fest 2026\FibroLens-previews"
node frontend/scripts/preview-designs.mjs
```

Open http://127.0.0.1:5180. Keep the terminal open; Ctrl+C stops all six servers. The launcher discovers worktrees through Git. Ports 5180-5186 must be free.

| Branch | Worktree folder | Port |
| --- | --- | --- |
| frontend/abstract-subtle | FibroLens-previews | 5181 |
| frontend/abstract-cinematic | FibroLens-abstract-cinematic | 5182 |
| frontend/mri-subtle | FibroLens-mri-subtle | 5183 |
| frontend/mri-cinematic | FibroLens-mri-cinematic | 5184 |
| frontend/type-subtle | FibroLens-type-subtle | 5185 |
| frontend/type-cinematic | FibroLens-type-cinematic | 5186 |

All folders are siblings under `E:\Personal\Build Fest 2026`. Frontend dependencies are shared by local directory junctions. On a different machine, run `npm --prefix frontend ci` in each worktree; the launcher is also compatible with macOS.

Submitting a valid development questionnaire preview shows explicitly labeled synthetic results without an API request. Starting at `/` retains the real upload and analysis workflow. Exit preview to use real inference.

## Run one version

In that branch's worktree, run `npm --prefix frontend run dev -- --port 5181 --strictPort`. Stop the comparison launcher first to free that port. You do not need to switch the original repository's branch.

- `/`: landing page and normal upload workflow.
- `/?preview=upload`: upload layout.
- `/?preview=questionnaire`: questionnaire layout.
- `/?preview=results`: clearly labeled synthetic results, for visual inspection without a GPU.

Preview query parameters only work in the development server. They never replace failed real inference. The actual analysis workflow still sends data to `/api/analyze`, using the existing port-8000 backend. The synthetic fixture does not describe the example scan.

## Design rationale and reference material

Preferences confirmed with the user: light editorial direction, warm white, dark text, restrained blue, with coordinated changes to landing/upload/questionnaire/results. Three visual choices and both motion options requested for comparison.

- *lec05-design-thinking.pdf*, pp. 7–15, 30–35, 39–43: start with user needs, storyboard the journey, prototype, and return to the user for feedback. Applied to progressive introduction → upload → context → results, and separate runnable design alternatives. No user-study results are claimed.
- *lec07-visual-design.pdf*, pp. 5–8 and 13–26: negative space, scale, focal point, contrast, balance, movement, rhythm, unity. Applied through one prominent visual, consistent spacing, aligned controls, fine dividing lines, and a quiet shared palette.
- Same deck, pp. 29–48: type and purposeful color, including alternatives to color-only meaning. Applied to readable text contrast, restrained type hierarchy, labels alongside status colors, and visible keyboard focus.
- [Apple iPhone reference](https://www.apple.com/iphone-18-pro/): inspiration for staged product explanation and large focal visuals. No Apple assets or product claims are reused.

Motion uses native scrolling with one sticky visual. Subtle has small reveals; cinematic adds longer chapters, scaling, and perspective. Both respect `prefers-reduced-motion` and provide direct controls. No scroll interception or autoplay audio/video.

## Research-image provenance

`src/assets/design/chaos-scan.png` is a grayscale pixel-only export from the user's existing CHAOS patient 1 T1 dual-echo example (`IMG-0004-00070.dcm`). No DICOM metadata is embedded. The blue outline and selected-mask/black-mask assets derive from the corresponding expert liver label (`Ground/IMG-0004-00070.png`, liver values 55–70). These are labeled research examples, not a visitor's uploaded image. The schematic SVG is an original simplified illustration, not diagnostic anatomy.

## What to evaluate

1. Read the opening screen: is the purpose clear without scrolling?
2. Scroll through the three chapters; compare subtle versus cinematic motion.
3. Use Start analysis, choose a ZIP, and continue to the questionnaire.
4. Inspect the synthetic results on desktop and mobile; toggle the two views and the projection controls.
5. Choose a visual and motion treatment; describe what feels distracting or unclear before approving any push.
