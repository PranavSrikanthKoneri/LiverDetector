import { adaptResult } from "./adapter";

/** Real backend inference; failures are never replaced with mock results. */
export async function analyzePatient({ mriFile, patient }) {
  if (!mriFile) throw new Error("Choose a DICOM ZIP archive first.");
  const formData = new FormData();
  formData.append("file", mriFile);
  formData.append("patient", JSON.stringify(patient));
  const response = await fetch("/api/analyze", { method: "POST", body: formData });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Analysis failed: ${response.status}`);
  }
  return adaptResult(await response.json(), patient);
}
