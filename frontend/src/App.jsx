import { useState } from "react";
import Header from "./components/Header";
import LoadingScreen from "./components/LoadingScreen";
import UploadPage from "./pages/UploadPage";
import QuestionnairePage from "./pages/QuestionnairePage";
import DashboardPage from "./pages/DashboardPage";
import { analyzePatient } from "./api/client";
import "./App.css";

/**
 * FibroLens — PCP-facing liver risk assessment workflow.
 *
 * 3-step flow:
 *  1. Upload MRI .zip
 *  2. Clinical questionnaire
 *  3. Results dashboard
 */
export default function App() {
  const [step, setStep] = useState(0); // 0=Upload, 1=Questionnaire, 2=Dashboard
  const [mriFile, setMriFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function handleUploadNext(file) {
    setMriFile(file);
    setStep(1);
  }

  function handleQuestionnaireBack() {
    setStep(0);
  }

  async function handleQuestionnaireSubmit(patient) {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzePatient({ mriFile, patient });
      setResult(data);
      setStep(2);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setStep(0);
    setMriFile(null);
    setResult(null);
    setError(null);
  }

  return (
    <>
      <Header currentStep={step} />

      {loading && <LoadingScreen />}

      {error && (
        <div className="container" style={{ paddingTop: "var(--space-xl)" }}>
          <div
            className="disclaimer-banner"
            style={{
              borderColor: "var(--danger)",
              color: "var(--danger)",
              background: "var(--danger-bg)",
            }}
          >
            <strong>Error:</strong> {error}
            <button
              className="btn btn-ghost btn-sm"
              onClick={() => setError(null)}
              style={{ marginLeft: "auto" }}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {step === 0 && <UploadPage onNext={handleUploadNext} />}
      {step === 1 && (
        <QuestionnairePage
          onBack={handleQuestionnaireBack}
          onSubmit={handleQuestionnaireSubmit}
        />
      )}
      {step === 2 && result && (
        <DashboardPage result={result} onReset={handleReset} />
      )}
    </>
  );
}
