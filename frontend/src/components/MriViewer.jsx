import { useState } from "react";
import "./MriViewer.css";
import { projectionOpacity } from "../api/projectionDisplay.js";

export default function MriViewer({ segmentation, caseLabel = "Unidentified upload", projectedStageValue, years, lifestyleScenario = false }) {
  const keys = Object.keys(segmentation.masks ?? {}).sort((a, b) => Number(a) - Number(b));
  const [current, setCurrent] = useState(0);
  const [overlay, setOverlay] = useState(true);
  const [visualize, setVisualize] = useState(false);
  const index = keys[current];
  const slice = segmentation.masks?.[index];
  const canVisualize = Boolean(slice?.projectionMask) && Number.isFinite(projectedStageValue);
  const showingProjection = visualize && canVisualize;
  if (!slice) return <div className="mri-viewer">No scan previews available.</div>;
  return (
    <div className="mri-viewer" id="mri-viewer">
      <div className="mri-viewer-header">
        <div className="mri-case-heading">
          <h3>Case: {caseLabel}</h3>
          <p>Actual scan · Slice index {index}</p>
        </div>
      </div>
      <div className="mri-controls">
        <label className="mri-control"><input type="checkbox" checked={overlay} onChange={e => setOverlay(e.target.checked)} /><span>Selected mask</span></label>
        <label className="mri-control"><input type="checkbox" checked={visualize} disabled={!canVisualize} onChange={event => setVisualize(event.target.checked)} /><span>Visualize projection (illustrative)</span></label>
      </div>
      {!canVisualize && <small className="text-tertiary">Run an analysis with the updated backend to enable the projection overlay.</small>}
      {showingProjection && <p className="mri-projection-caption">Illustrative overlay · Year {years} · {lifestyleScenario ? "Healthy lifestyle scenario" : "Baseline scenario"} · Projected stage {projectedStageValue.toFixed(2)}</p>}
      <div className="mri-scan-frame">
      <img className="mri-source-image" src={overlay ? slice.overlay : slice.image} alt={`${caseLabel}: in-phase MRI slice ${index}${overlay ? ' with selected liver outline' : ''}`} style={{ width: '100%', imageRendering: 'pixelated', background: 'black' }} />
      {showingProjection && <img className="mri-stage-overlay" src={slice.projectionMask} alt="" aria-hidden="true" style={{ opacity: projectionOpacity(projectedStageValue) }} />}
      </div>
      <div className="mri-nav">
        <button className="btn btn-secondary" disabled={current === 0} onClick={() => setCurrent(current - 1)}>Previous</button>
        <span>Image {current + 1} of {keys.length}</span>
        <button className="btn btn-secondary" disabled={current === keys.length - 1} onClick={() => setCurrent(current + 1)}>Next</button>
      </div>
      <p className="text-tertiary">{showingProjection ? "Shading illustrates the projected stage within the liver mask; it is not a prediction of future MRI appearance. The original scan is unchanged." : "Yellow: selected mask. Enable the illustrative overlay to explore the projection slider."}</p>
    </div>
  );
}
