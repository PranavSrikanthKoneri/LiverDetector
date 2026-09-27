import { useState } from "react";
import {
  ArrowLeftIcon, ComponentInstanceIcon, PersonIcon, MagnifyingGlassIcon,
} from "@radix-ui/react-icons";
import Disclaimer from "../components/Disclaimer";
import FibrosisPanel from "../components/FibrosisPanel";
import BiomarkerPanel from "../components/BiomarkerPanel";
import TriagePanel from "../components/TriagePanel";
import ProgressionChart from "../components/ProgressionChart";
import MriViewer from "../components/MriViewer";
import "./DashboardPage.css";

export default function DashboardPage({ result, onReset }) {
  const [activeTab, setActiveTab] = useState("pcp");
  
  // Lifted progression state
  const [years, setYears] = useState(10);
  const [showIntervention, setShowIntervention] = useState(false);

  const { segmentation, prediction, progression } = result;

  // Calculate projected stage for the MRI viewer visualization
  const currentProjection = showIntervention ? progression.intervention : progression.baseline;
  const projectedStageValue = currentProjection.find(p => p.year === years)?.stage_value || prediction.stage_value || 0;

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

        {activeTab === "pcp" ? (
          <div className="dashboard-content" key="pcp">
            <div className="dashboard-main">
              <FibrosisPanel stage={prediction.stage} probs={prediction.probs} pGeF2={prediction.p_ge_F2} tier={prediction.tier} />
              <TriagePanel recommendation={result.recommendation} />
              
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
            </div>

            <div className="dashboard-sidebar">
              <MriViewer 
                segmentation={segmentation} 
                projectedStageValue={projectedStageValue} 
                years={years}
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
                  segmentation={segmentation} 
                  projectedStageValue={projectedStageValue} 
                  years={years}
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
