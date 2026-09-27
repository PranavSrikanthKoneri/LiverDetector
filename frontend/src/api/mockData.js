/**
 * Mock data matching the backend contract from docs/interfaces.md
 *
 * Fields included:
 *  - patient inputs (questionnaire)
 *  - segmentation information (masks metadata, slice info)
 *  - fat_pct (liver fat %)
 *  - texture score (contrast, homogeneity, entropy)
 *  - fibrosis stage + confidence (probs array)
 *  - progression data (0–20 year trajectory)
 *  - intervention scenario (slower-progression)
 */

// ── Patient Inputs (questionnaire) ────────────────
export const mockPatientInputs = {
  age: 54,
  male: true,
  bmi: 31.2,
  waist_cm: 104,
  diabetes: true,
  drinks_week: 3,
};

// ── Segmentation / Imaging Results ────────────────
// Mirrors: segment_and_measure() return shape
export const mockSegmentationResults = {
  masks: {
    45: { width: 256, height: 256, liverPixels: 4820 },
    46: { width: 256, height: 256, liverPixels: 5130 },
    47: { width: 256, height: 256, liverPixels: 5390 },
    48: { width: 256, height: 256, liverPixels: 4970 },
    49: { width: 256, height: 256, liverPixels: 4650 },
  },
  fat_pct: 18.4,
  steatosis: true,
  texture: {
    contrast: 0.42,
    homogeneity: 0.78,
    entropy: 4.31,
  },
};

// ── Fibrosis Stage Prediction ─────────────────────
// Mirrors: predict_stage() return shape
export const mockPrediction = {
  stage: "F2",
  probs: [0.12, 0.54, 0.26, 0.08], // [F0-F1, F2, F3, F4]
};

// ── Progression Data ──────────────────────────────
// Mirrors: project() called for years 0–20 with slow=false and slow=true
// Each entry: { year, stage_value, low, high }
function generateProjection(baseStage, slow) {
  const ratePerYear = slow ? 1 / 14.3 : 1 / 7.1;
  const points = [];
  for (let y = 0; y <= 20; y++) {
    const raw = baseStage + ratePerYear * y;
    const stage_value = Math.min(raw, 4);
    const spread = 0.3 + y * 0.06;
    points.push({
      year: y,
      stage_value: parseFloat(stage_value.toFixed(2)),
      low: parseFloat(Math.max(0, stage_value - spread).toFixed(2)),
      high: parseFloat(Math.min(4, stage_value + spread).toFixed(2)),
    });
  }
  return points;
}

export const mockBaselineProjection = generateProjection(1.5, false); // F2 ≈ 1.5
export const mockInterventionProjection = generateProjection(1.5, true);

// ── LLM Summaries ─────────────────────────────────
// Mirrors: summarize() return shape, extended with two summaries
export const mockSummaries = {
  pcp_summary:
    `Based on the imaging and clinical data, this patient's estimated liver fat is 18.4%, ` +
    `which is above the 5% threshold typically associated with hepatic steatosis. The GLCM ` +
    `texture analysis shows moderate heterogeneity (entropy 4.31), which may reflect early ` +
    `parenchymal changes. The tabular risk model estimates fibrosis at stage F2 with 54% ` +
    `confidence, with a 34% probability of being F3 or higher.\n\n` +
    `Key risk factors contributing to this estimate include the patient's BMI (31.2), ` +
    `central adiposity (waist 104 cm), and Type 2 diabetes status. Weekly alcohol intake ` +
    `of 3 drinks is within moderate range but is an additive stressor in the context of ` +
    `metabolic risk.\n\n` +
    `Given the combination of elevated fat fraction, moderate fibrosis estimate, and ` +
    `metabolic risk profile, additional liver evaluation may be warranted to clarify ` +
    `fibrosis severity. This tool's output supports clinical decision-making and does ` +
    `not replace specialist assessment, FibroScan, or liver biopsy.`,

  patient_explanation:
    `Your liver scan and health information have been analyzed. The results suggest ` +
    `that your liver has a higher-than-usual amount of fat (about 18%). This is ` +
    `sometimes called fatty liver.\n\n` +
    `The analysis also looked at signs that might suggest your liver is working ` +
    `harder than normal. The estimated stage is "F2," which is a moderate level on ` +
    `a scale from F0 (no significant changes) to F4 (advanced changes). The model ` +
    `is moderately confident in this estimate.\n\n` +
    `Some of your health factors — like your weight, waist size, and diabetes — may ` +
    `be contributing to these changes. The good news is that lifestyle adjustments ` +
    `such as balanced eating, regular physical activity, and limiting alcohol ` +
    `can support liver health over time.\n\n` +
    `Your doctor will review these results with you and decide if any additional ` +
    `evaluation is needed. Please follow up with your physician to discuss next steps.`,
};

// ── Full combined result (matches the POST /analyze response shape) ──
export const mockFullResult = {
  patient: mockPatientInputs,
  segmentation: mockSegmentationResults,
  prediction: mockPrediction,
  progression: {
    baseline: mockBaselineProjection,
    intervention: mockInterventionProjection,
  },
  summaries: mockSummaries,
};
