import { ArrowRightIcon } from "@radix-ui/react-icons";
import "./TriagePanel.css";

function getTriageResult(stage, probs, fatPct) {
  const f3f4Prob = probs[2] + probs[3];

  if (stage === "F0-F1" && fatPct < 10) {
    return {
      level: "low",
      label: "Low Risk",
      recommendation: "Manage in primary care.",
      action: "Routine metabolic monitoring.",
      color: "var(--success)",
    };
  }

  if (stage === "F0-F1" || (stage === "F2" && f3f4Prob < 0.25)) {
    return {
      level: "moderate",
      label: "Moderate Risk",
      recommendation: "Early metabolic involvement.",
      action: "Monitor closely. Lifestyle intervention.",
      color: "var(--warning)",
    };
  }

  return {
    level: "elevated",
    label: "Elevated Risk",
    recommendation: "High probability of advanced fibrosis.",
    action: "Specialist referral / FibroScan indicated.",
    color: "var(--danger)",
  };
}

export default function TriagePanel({ stage, probs, fatPct }) {
  const triage = getTriageResult(stage, probs, fatPct);

  return (
    <div className="triage-panel" id="triage-panel">
      <h3>Action / Triage</h3>

      <div className="triage-badge" style={{ "--triage-color": triage.color }}>
        <span className="dot" style={{ background: triage.color }} />
        {triage.label}
      </div>

      <div className="triage-body">
        <p className="text-secondary">{triage.recommendation}</p>
        <div className="triage-action" style={{ borderLeftColor: triage.color }}>
          <ArrowRightIcon style={{ color: triage.color, flexShrink: 0, marginTop: 4, width: 16, height: 16 }} />
          <p>{triage.action}</p>
        </div>
      </div>
    </div>
  );
}
