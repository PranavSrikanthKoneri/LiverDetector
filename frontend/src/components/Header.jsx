import { ActivityLogIcon } from "@radix-ui/react-icons";
import "./Header.css";

export default function Header({ currentStep }) {
  const steps = ["Upload", "Questionnaire", "Results"];

  return (
    <header className="app-header" id="app-header">
      <div className="container header-inner">
        <div className="header-brand">
          <ActivityLogIcon width={18} height={18} style={{ color: "var(--accent)" }} />
          <span className="header-title">FibroLens</span>
        </div>

        {currentStep !== undefined && (
          <nav className="header-steps" aria-label="Workflow progress">
            {steps.map((label, i) => (
              <div
                key={label}
                className={`header-step ${
                  i === currentStep ? "active" : ""
                } ${i < currentStep ? "completed" : ""}`}
              >
                <span className="header-step-num">{i + 1}</span>
                <span className="header-step-label">{label}</span>
              </div>
            ))}
          </nav>
        )}
      </div>
    </header>
  );
}
