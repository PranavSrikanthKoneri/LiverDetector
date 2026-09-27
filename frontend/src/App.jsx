import { useEffect, useRef, useState } from "react";
import { createDesignPreview } from "./design/preview";
import LandingPage from "./pages/LandingPage";
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
const previewScreen = import.meta.env.DEV ? new URLSearchParams(window.location.search).get("preview") : null;
const isDesignPreview = ["upload", "questionnaire", "results"].includes(previewScreen);

export default function App() {
  const [showLanding, setShowLanding] = useState(!isDesignPreview);
  const mainRef = useRef(null);
  const [step, setStep] = useState(previewScreen === "results" ? 2 : previewScreen === "questionnaire" ? 1 : 0); // 0=Upload, 1=Questionnaire, 2=Dashboard
  const [mriFile, setMriFile] = useState(null);
  const [result, setResult] = useState(() => isDesignPreview ? createDesignPreview() : null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
    mainRef.current?.focus({ preventScroll: true });
  }, [step, showLanding]);

  function handleStart() {
    handleReset();
    setShowLanding(false);
  }

  function handleUploadNext(file) {
    setMriFile(file);
    setStep(1);
  }

  function handleQuestionnaireBack() {
    setStep(0);
  }

  async function handleQuestionnaireSubmit(patient) {
    if (isDesignPreview) {
      setError(null);
      setResult(createDesignPreview());
      setStep(2);
      return;
    }
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
      <a className="skip-link" href="#main-content">Skip to content</a>
      <Header currentStep={showLanding ? undefined : step} onStart={handleStart} onHome={() => setShowLanding(true)} />
      <main id="main-content" className="workflow-main" ref={mainRef} tabIndex={-1}>
        {showLanding && <LandingPage onStart={handleStart} />}
        {!showLanding && <>

          {isDesignPreview && <div className="design-preview-notice" role="status">Design preview · Synthetic display values, not results from the example scan. <a href="/">Exit preview</a></div>}
          {loading && <LoadingScreen />}

          {error && (
            <div className="container" style={{ paddingTop: "var(--space-8)" }}>
              <div
                className="disclaimer-banner"
                style={{
                  borderColor: "var(--danger)",
                  color: "var(--danger)",
                  background: "var(--danger-muted)",
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
        </>}
      </main>
    </>
  );
}
