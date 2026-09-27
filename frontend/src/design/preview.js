// Development-only layout fixture. Never used as an inference fallback.
import scan from "../assets/design/chaos-scan.png";
import overlay from "../assets/design/chaos-overlay.png";
import mask from "../assets/design/chaos-mask.png";

export function createDesignPreview() {
  const projection = rate => Array.from({ length: 21 }, (_, year) => ({ year, stage_value: Math.min(4, 0.5 + year * rate), low: 0.25, high: Math.min(4, 1 + year * rate) }));
  return {
    scanIdentity: { label: "Design preview", filename: "Example image · synthetic display values" },
    prediction: { stage: "F0-F1", probs: [0.92, 0.05, 0.02, 0.01], p_ge_F2: 0.08, tier: "low" },
    segmentation: { fat_pct: 12.3, steatosis: true, warnings: [], texture: { entropy: 7.6, contrast: 9.3, homogeneity: 0.44 },
      masks: { "Example": { image: scan, overlay, projectionMask: mask } } },
    progression: { baseline: projection(0.12), intervention: projection(0.06) },
    recommendation: { tier: "low", headline: "This is a layout preview using synthetic values.", points: ["These numbers are not measurements of the example scan.", "Run a real analysis to see an actual case report."], disclaimer: "Design preview only. Not a medical result." },
    disclaimer: "Design preview only. Not a medical result.",
  };
}
