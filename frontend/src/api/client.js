/**
 * API layer — abstracts data fetching so the frontend can swap from
 * mock data to the real FastAPI backend with a single config change.
 *
 * Set USE_MOCK = false and update API_BASE when the backend is ready.
 */

import { mockFullResult } from "./mockData";

// ── Configuration ─────────────────────────────────
const USE_MOCK = true;
const API_BASE = "/api"; // Change to the real backend URL when ready

// ── Simulated network delay for realistic feel ───
function delay(ms = 800) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * POST /analyze
 * Sends patient inputs + MRI file, returns the full result object.
 *
 * @param {object} params
 * @param {File|null} params.mriFile  - the uploaded MRI zip
 * @param {object}    params.patient  - questionnaire answers
 * @returns {Promise<object>} full analysis result
 */
export async function analyzePatient({ mriFile, patient }) {
  if (USE_MOCK) {
    await delay(1200);
    // Merge submitted patient data into the mock result
    return {
      ...mockFullResult,
      patient: { ...mockFullResult.patient, ...patient },
    };
  }

  const formData = new FormData();
  if (mriFile) formData.append("file", mriFile);
  formData.append("patient", JSON.stringify(patient));

  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Analysis failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}
