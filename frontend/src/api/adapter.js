import { alcoholFromAnswers } from "./alcohol.js";

const brandText = text => typeof text === "string" ? text.replace(/\b(?:LiverCast|HepatoCast)\b/g, "FibroLens") : text;

/** Map the backend's documented result into the existing dashboard props. */
export function adaptResult(result, patient, uploadName = "") {
  const points = (rows) => rows.map(({ years, ...row }) => ({ year: years, ...row }));
  const filename = uploadName.split(/[\\/]/).pop() || "";
  return {
    scanIdentity: {
      label: filename.replace(/\.zip$/i, "") || "Unidentified upload",
      filename,
    },
    patient,
    alcoholConsumption: result.alcohol_consumption ?? alcoholFromAnswers(patient),
    segmentation: result.imaging,
    prediction: result.risk,
    progression: {
      baseline: points(result.projection.typical),
      intervention: points(result.projection.slower),
    },
    recommendation: result.recommendation ? { ...result.recommendation, disclaimer: brandText(result.recommendation.disclaimer) } : result.recommendation,
    disclaimer: brandText(result.disclaimer),
  };
}
