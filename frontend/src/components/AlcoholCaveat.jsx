import defaultGuidance from "../../../backend/demo/alcohol_guidance.json";
import "./AlcoholCaveat.css";

export default function AlcoholCaveat({ guidance = defaultGuidance }) {
  return (
    <aside className="alcohol-caveat" aria-label={guidance.title}>
      <strong>{guidance.title}</strong>
      <p>{guidance.caveat}</p>
      <details>
        <summary>Weekly drinking ranges and standard drinks</summary>
        <p>{guidance.intro}</p>
        <div className="alcohol-table-scroll">
          <table>
            <caption>U.S. weekly drinking thresholds</caption>
            <thead><tr><th scope="col">Range</th><th scope="col">Women</th><th scope="col">Men</th><th scope="col">Meaning</th></tr></thead>
            <tbody>{guidance.ranges.map(row => (
              <tr key={row.label}><th scope="row">{row.label}</th><td>{row.women}</td><td>{row.men}</td><td>{row.note}</td></tr>
            ))}</tbody>
          </table>
        </div>
        <p>{guidance.standard_drink}</p>
        <p className="alcohol-sources">{guidance.sources.map(source => (
          <a key={source.url} href={source.url} target="_blank" rel="noreferrer">{source.label}</a>
        ))}</p>
      </details>
    </aside>
  );
}
