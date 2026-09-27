import { OpacityIcon, TransformIcon, LayersIcon, ActivityLogIcon } from "@radix-ui/react-icons";
import "./BiomarkerPanel.css";

export default function BiomarkerPanel({ fatPct, steatosis, texture, stage, confidence }) {
  const confidencePct = (confidence * 100).toFixed(0);

  const listItems = [
    {
      icon: <OpacityIcon />,
      label: "Liver Fat",
      value: `${fatPct.toFixed(1)}%`,
      sub: steatosis ? "Steatosis (>5%)" : "Normal",
      color: steatosis ? "var(--warning)" : "var(--success)",
      meter: Math.min(fatPct / 50, 1),
    },
    {
      icon: <TransformIcon />,
      label: "GLCM Texture",
      value: texture.entropy.toFixed(2),
      sub: `Contrast ${texture.contrast.toFixed(2)} · Homogeneity ${texture.homogeneity.toFixed(2)}`,
      color: "var(--info)",
      meter: texture.entropy / 8,
    },
    {
      icon: <LayersIcon />,
      label: "Fibrosis Stage",
      value: stage,
      color: stage === "F0-F1" ? "var(--f0-color)" : stage === "F2" ? "var(--f2-color)" : stage === "F3" ? "var(--f3-color)" : "var(--f4-color)",
    },
    {
      icon: <ActivityLogIcon />,
      label: "Confidence",
      value: `${confidencePct}%`,
      color: confidence >= 0.6 ? "var(--success)" : confidence >= 0.4 ? "var(--warning)" : "var(--danger)",
      meter: confidence,
    },
  ];

  return (
    <div className="biomarker-panel" id="biomarker-panel">
      <h3 style={{ marginBottom: "var(--space-4)" }}>Biomarkers</h3>
      <div className="biomarker-list">
        {listItems.map((item, i) => (
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
