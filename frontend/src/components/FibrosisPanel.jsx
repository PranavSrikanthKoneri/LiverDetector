import { ExclamationTriangleIcon } from "@radix-ui/react-icons";
import "./FibrosisPanel.css";

const STAGE_CONFIG = {
  "F0-F1": { label: "F0–F1", color: "var(--f0-color)", level: "Minimal", idx: 0 },
  F2: { label: "F2", color: "var(--f2-color)", level: "Moderate", idx: 1 },
  F3: { label: "F3", color: "var(--f3-color)", level: "Significant", idx: 2 },
  F4: { label: "F4", color: "var(--f4-color)", level: "Advanced", idx: 3 },
};

const STAGE_LABELS = ["F0–F1", "F2", "F3", "F4"];

export default function FibrosisPanel({ stage, probs, pGeF2, tier, simplified = false }) {
  const config = STAGE_CONFIG[stage] || STAGE_CONFIG["F0-F1"];
  const confidence = pGeF2 ?? probs.slice(1).reduce((a, b) => a + b, 0);
  const confidencePct = (confidence * 100).toFixed(0);

  return (
    <div className="fibrosis-panel" id="fibrosis-panel">
      <div className="fibrosis-header">
        <ExclamationTriangleIcon style={{ color: config.color, width: 18, height: 18 }} />
        <h3>Questionnaire Risk Estimate</h3>
      </div>

      <div className="fibrosis-stage-display">
        <div className="fibrosis-stage-badge" style={{ "--stage-color": config.color }}>
          <span className="fibrosis-stage-value">{confidencePct}%</span>
          <span className="fibrosis-stage-level">{tier} risk of ≥F2 (proxy labels)</span>
        </div>

        <div className="fibrosis-confidence">
          <div className="fibrosis-confidence-ring">
            <svg viewBox="0 0 72 72">
              <circle cx="36" cy="36" r="30" fill="none" stroke="var(--bg-hover)" strokeWidth="4" />
              <circle
                cx="36" cy="36" r="30"
                fill="none"
                stroke={config.color}
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray={`${confidence * 188.5} 188.5`}
                transform="rotate(-90 36 36)"
              />
            </svg>
            <span className="fibrosis-confidence-value mono">{confidencePct}%</span>
          </div>
          <span className="text-tertiary" style={{ fontSize: "0.6875rem" }}>Questionnaire only; not diagnostic</span>
        </div>
      </div>

      {!simplified && (
        <div className="fibrosis-probs">
          <span className="text-tertiary" style={{ fontSize: "0.6875rem", marginBottom: 4 }}>
            Probability
          </span>
          {probs.map((p, i) => (
            <div className="fibrosis-prob-row" key={i}>
              <span className="fibrosis-prob-label mono">{STAGE_LABELS[i]}</span>
              <div className="meter" style={{ flex: 1 }}>
                <div
                  className="meter-fill"
                  style={{
                    width: `${p * 100}%`,
                    background: i === config.idx ? config.color : "var(--text-tertiary)",
                    opacity: i === config.idx ? 1 : 0.3,
                  }}
                />
              </div>
              <span
                className="fibrosis-prob-value mono"
                style={{ color: i === config.idx ? config.color : "var(--text-tertiary)" }}
              >
                {(p * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
