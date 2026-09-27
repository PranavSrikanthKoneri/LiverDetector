import { ArrowRightIcon } from "@radix-ui/react-icons";
import "./Header.css";

export default function Header({ currentStep, onStart, onHome }) {
  const steps = ["Upload", "Questionnaire", "Results"];
  const isLanding = currentStep === undefined;
  return (
    <header className="app-header" id="app-header">
      <div className="container header-inner">
        <button className="header-brand" onClick={onHome} aria-label="FibroLens home">
          <span className="brand-mark" aria-hidden="true"><span /></span>
          <span className="header-title">FibroLens<span className="brand-period">.</span></span>
        </button>
        {isLanding ? (
          <nav className="landing-nav" aria-label="Main navigation">
            <a className="nav-approach" href="#how-it-works">The approach</a>
            <button className="btn btn-primary btn-sm" onClick={onStart}>Start analysis <ArrowRightIcon /></button>
          </nav>
        ) : (
          <nav className="header-steps" aria-label="Workflow progress">
            {steps.map((label, i) => (
              <div key={label} aria-current={i === currentStep ? "step" : undefined}
                className={`header-step ${i === currentStep ? "active" : ""} ${i < currentStep ? "completed" : ""}`}>
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
