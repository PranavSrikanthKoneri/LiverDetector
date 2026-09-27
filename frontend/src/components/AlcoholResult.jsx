import "./AlcoholResult.css";

export default function AlcoholResult({ result }) {
  if (!result) return <section className="alcohol-result"><h3>Alcohol consumption — informational</h3><p>Alcohol information is unavailable because the submitted weekly intake or sex is missing or invalid.</p></section>;
  return (
    <section className="alcohol-result" aria-label="Alcohol consumption information">
      <h3>Alcohol consumption — informational</h3>
      <div className="alcohol-result-heading">
        <strong className={`alcohol-category alcohol-category-${result.category}`}>{result.label}</strong>
        <span>{result.drinks_week} drinks per week · {result.sex_label}’s range</span>
      </div>
      <p>{result.caveat}</p>
      <details>
        <summary>View weekly ranges</summary>
        <div className="alcohol-table-scroll">
          <table>
            <thead><tr><th scope="col">Informational category</th><th scope="col">Women</th><th scope="col">Men</th></tr></thead>
            <tbody>{result.ranges.map(row => (
              <tr key={row.category} className={row.category === result.category ? 'alcohol-selected' : ''}>
                <th scope="row">{row.label}{row.category === result.category ? ' (selected)' : ''}</th>
                <td>{row.women}</td><td>{row.men}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
        <p>{result.range_note}</p>
      </details>
    </section>
  );
}
