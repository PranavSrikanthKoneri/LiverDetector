import { useState } from "react";
import {
  ArrowLeftIcon, ComponentInstanceIcon, PersonIcon, MagnifyingGlassIcon,
} from "@radix-ui/react-icons";
import Disclaimer from "../components/Disclaimer";
import AlcoholResult from "../components/AlcoholResult";
import FibrosisPanel from "../components/FibrosisPanel";
import BiomarkerPanel from "../components/BiomarkerPanel";
import TriagePanel from "../components/TriagePanel";
import ProgressionChart from "../components/ProgressionChart";
import { projectionAtYear } from "../api/projectionDisplay.js";
import MriViewer from "../components/MriViewer";
import "./DashboardPage.css";

export default function DashboardPage({ result, onReset }) {
  const [activeTab, setActiveTab] = useState("pcp");

  // Lifted progression state
  const [years, setYears] = useState(10);
  const [showIntervention, setShowIntervention] = useState(false);

  const { segmentation, prediction, progression } = result;

  // Calculate projected stage for the MRI viewer visualization
  const projectedStageValue = projectionAtYear(progression, years, showIntervention);

  return (
    <div className="dashboard-page">
      <Disclaimer variant="sticky" />

      <div className="container stack stack-xl" style={{ padding: "var(--space-8) var(--space-6)" }}>
        {/* Top bar */}
        <div className="dashboard-topbar">
          <button className="btn btn-ghost btn-sm" onClick={onReset} id="dashboard-new-analysis-btn">
            <ArrowLeftIcon />
            New Analysis
          </button>

          <div className="dashboard-tab-switcher">
            <button
              className={`dashboard-tab ${activeTab === "pcp" ? "active" : ""}`}
              onClick={() => setActiveTab("pcp")}
              id="tab-pcp-view"
            >
              <ComponentInstanceIcon />
              PCP View
            </button>
            <button
              className={`dashboard-tab ${activeTab === "patient" ? "active" : ""}`}
              onClick={() => setActiveTab("patient")}
              id="tab-patient-view"
            >
              <PersonIcon />
              Patient View
            </button>
          </div>
        </div>

        <div className="dashboard-case" aria-label="Current scan case">
          <strong>Case: {result.scanIdentity?.label ?? "Unidentified upload"}</strong>
          {result.scanIdentity?.filename && <span>Uploaded file: {result.scanIdentity.filename}</span>}
        </div>

        {activeTab === "pcp" ? (
          <div className="dashboard-content" key="pcp">
            <div className="dashboard-main">
              <FibrosisPanel stage={prediction.stage} probs={prediction.probs} pGeF2={prediction.p_ge_F2} tier={prediction.tier} />
              <AlcoholResult result={result.alcoholConsumption} />

              <BiomarkerPanel
                fatPct={segmentation.fat_pct}
                steatosis={segmentation.steatosis}
                texture={segmentation.texture}
                stage={prediction.stage}
                confidence={Math.max(...prediction.probs)}
                warnings={segmentation.warnings}
                textureQuality={segmentation.texture_quality}
              />

              <div className="dashboard-progression-section">
                <div className="dashboard-section-header">
                  <MagnifyingGlassIcon />
                  <div>
                    <h3>Progression Trajectory</h3>
                    <p className="text-tertiary" style={{ fontSize: "0.75rem" }}>
                      Population-based projection
                    </p>
                  </div>
                </div>
                <ProgressionChart
                  baseline={progression.baseline}
                  intervention={progression.intervention}
                  years={years}
                  onYearsChange={setYears}
                  showIntervention={showIntervention}
                  onInterventionChange={setShowIntervention}
                />
              </div>

              <TriagePanel recommendation={result.recommendation} />
            </div>

            <div className="dashboard-sidebar">
              <MriViewer
                key={segmentation.texture_quality?.image_fingerprint ?? result.scanIdentity?.filename}
                caseLabel={result.scanIdentity?.label}
                segmentation={segmentation}
                projectedStageValue={projectedStageValue}
                years={years}
                lifestyleScenario={showIntervention}
              />
            </div>
          </div>
        ) : (
          <div className="dashboard-content patient-content" key="patient">
            <div className="dashboard-main">
              <div className="patient-view-header">
                <h3>Your Results — What They Mean</h3>
              </div>

              <FibrosisPanel stage={prediction.stage} probs={prediction.probs} pGeF2={prediction.p_ge_F2} tier={prediction.tier} simplified />
              <AlcoholResult result={result.alcoholConsumption} />
              <TriagePanel recommendation={result.recommendation} />

              <div className="dashboard-progression-section">
                <div className="dashboard-section-header">
                  <MagnifyingGlassIcon />
                  <div>
                    <h3>Progression Trajectory</h3>
                    <p className="text-tertiary" style={{ fontSize: "0.75rem" }}>
                      Population-based projection
                    </p>
                  </div>
                </div>
                <ProgressionChart
                  baseline={progression.baseline}
                  intervention={progression.intervention}
                  years={years}
                  onYearsChange={setYears}
                  showIntervention={showIntervention}
                  onInterventionChange={setShowIntervention}
                />
              </div>

              <div className="dashboard-progression-section">
                <MriViewer
                  key={segmentation.texture_quality?.image_fingerprint ?? result.scanIdentity?.filename}
                  caseLabel={result.scanIdentity?.label}
                  segmentation={segmentation}
                  projectedStageValue={projectedStageValue}
                  years={years}
                  lifestyleScenario={showIntervention}
                />
              </div>

              <Disclaimer />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
