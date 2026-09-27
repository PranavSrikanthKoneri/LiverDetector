import { alcoholWarning } from "../api/alcohol.js";
import "./AlcoholResult.css";

export default function AlcoholResult({ result }) {
  const warning = alcoholWarning(result);
  if (!warning) return null;
  return (
    <p className={`alcohol-warning alcohol-warning-${warning.severity}`} role="note">
      {warning.message}
    </p>
  );
}
