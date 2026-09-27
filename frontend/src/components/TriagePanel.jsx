import "./TriagePanel.css";
import AlcoholCaveat from "./AlcoholCaveat";

export default function TriagePanel({ recommendation }) {
  if (!recommendation) return null;
  return (
    <div className="triage-panel" id="triage-panel">
      <h3>Research summary</h3>
      <p>{recommendation.headline}</p>
      <ul>{recommendation.points.map(point => <li key={point}>{point}</li>)}</ul>
      <AlcoholCaveat guidance={recommendation.alcohol_caveat} />
      <p className="text-tertiary">{recommendation.disclaimer}</p>
    </div>
  );
}
