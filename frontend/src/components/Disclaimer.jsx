import { ExclamationTriangleIcon } from "@radix-ui/react-icons";

import "./Disclaimer.css";

export default function Disclaimer({ variant = "banner" }) {
  return (
    <div
      className={`site-disclaimer disclaimer-banner ${
        variant === "sticky" ? "disclaimer-banner-persistent" : ""
      }`}
      role="alert"
      id="disclaimer-banner"
    >
      <ExclamationTriangleIcon width={16} height={16} style={{ flexShrink: 0 }} />
      <span>
        <strong>Not Diagnostic — Clinical Decision Support / Educational Tool.</strong>{" "}
        FibroLens does not replace specialist evaluation, FibroScan, biopsy, or
        physician judgment. All projections are population-based educational estimates.
      </span>
    </div>
  );
}
