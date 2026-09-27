import { UpdateIcon } from "@radix-ui/react-icons";
import "./LoadingScreen.css";

export default function LoadingScreen() {
  return (
    <div className="loading-screen" id="loading-screen">
      <div className="loading-content">
        <div className="loading-spinner">
          <UpdateIcon width={24} height={24} />
        </div>
        <p style={{ fontSize: "0.875rem", fontWeight: 500 }}>Analyzing…</p>
        <p className="text-tertiary" style={{ fontSize: "0.8125rem" }}>
          Running segmentation, biomarker extraction, and risk modeling.
        </p>
      </div>
    </div>
  );
}
