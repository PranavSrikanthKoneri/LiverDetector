import "./SummaryPanel.css";

/**
 * LLM-generated summary display — PCP or Patient variant.
 */
export default function SummaryPanel({ title, icon, text, variant = "pcp" }) {
  const paragraphs = text.split("\n\n").filter(Boolean);

  return (
    <div className={`summary-panel card summary-${variant}`} id={`summary-panel-${variant}`}>
      <div className="summary-header">
        <span className="summary-icon">{icon}</span>
        <h4>{title}</h4>
        <span className="badge badge-info" style={{ marginLeft: "auto" }}>AI-Generated</span>
      </div>

      <div className="summary-body">
        {paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </div>

      <div className="summary-footer text-tertiary">
        AI-generated from structured data. Not a diagnosis.
      </div>
    </div>
  );
}
