import { OpacityIcon, TransformIcon, LayersIcon, ActivityLogIcon } from "@radix-ui/react-icons";
import "./BiomarkerPanel.css";

export default function BiomarkerPanel({ fatPct, steatosis, texture, stage, confidence, warnings = [] }) {
  const confidencePct = (confidence * 100).toFixed(0);

  const listItems = [
    {
      icon: <OpacityIcon />,
      label: "Liver Fat",
      value: `${fatPct.toFixed(1)}%`,
      sub: warnings.length ? "Clipped estimate — review required" : steatosis ? "Above prototype 5% threshold" : "Below prototype 5% threshold",
      color: steatosis ? "var(--warning)" : "var(--success)",
      meter: Math.min(fatPct / 50, 1),
    },
    {
      icon: <TransformIcon />,
      label: "Texture entropy",
      value: texture.entropy.toFixed(2),
      sub: "Measures how varied image patterns are within sampled liver regions. Higher values mean less predictable patterns.",
      color: "var(--info)",
    },
    {
      icon: <LayersIcon />,
      label: "Most likely proxy class",
      value: stage,
      color: stage === "F0-F1" ? "var(--f0-color)" : stage === "F2" ? "var(--f2-color)" : stage === "F3" ? "var(--f3-color)" : "var(--f4-color)",
    },
    {
      icon: <ActivityLogIcon />,
      label: "Class probability",
      value: `${confidencePct}%`,
      color: confidence >= 0.6 ? "var(--success)" : confidence >= 0.4 ? "var(--warning)" : "var(--danger)",
      meter: confidence,
    },
  ];

  return (
    <div className="biomarker-panel" id="biomarker-panel">
      <h3 style={{ marginBottom: "var(--space-4)" }}>Biomarkers</h3>
      <div className="biomarker-list">
        {listItems.map((item) => (
          <div className="biomarker-list-item" key={item.label}>
            <div className="biomarker-item-icon" style={{ color: item.color }}>
              {item.icon}
            </div>
            
            <div className="biomarker-item-content">
              <div className="biomarker-item-header">
                <span className="biomarker-item-label">{item.label}</span>
                <span className="biomarker-item-value mono" style={{ color: item.color }}>
                  {item.value}
                </span>
              </div>
              
              {item.meter !== undefined && (
                <div className="meter" style={{ height: 4, marginTop: 4, marginBottom: 4 }}>
                  <div
                    className="meter-fill"
                    style={{ width: `${item.meter * 100}%`, background: item.color }}
                  />
                </div>
              )}

              <div className="biomarker-item-sub">
                <span>{item.sub}</span>
                {item.note && <span className="biomarker-item-note">{item.note}</span>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
