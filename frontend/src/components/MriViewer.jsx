import { useState } from "react";
import { Component1Icon, LayersIcon, ChevronLeftIcon, ChevronRightIcon } from "@radix-ui/react-icons";
import "./MriViewer.css";

export default function MriViewer({ segmentation, projectedStageValue = null, years = null }) {
  const sliceKeys = Object.keys(segmentation.masks).map(Number).sort();
  const [currentSlice, setCurrentSlice] = useState(0);
  const [showOverlay, setShowOverlay] = useState(true);

  const sliceIdx = sliceKeys[currentSlice];
  const sliceData = segmentation.masks[sliceIdx];

  // Degradation maps 0 -> 0 (Healthy) and 4 -> 1 (Severe Cirrhosis)
  const isProjecting = projectedStageValue !== null;
  const degradation = isProjecting ? Math.max(0, Math.min(projectedStageValue / 4, 1)) : 0;
  
  const hue = 120 - degradation * 120; // 120 (Green) to 0 (Red)
  const dynamicStyle = {
    "--degradation": degradation,
    ...(showOverlay && isProjecting ? {
      background: `hsla(${hue}, 72%, 53%, 0.15)`,
      borderColor: `hsla(${hue}, 72%, 53%, 0.4)`,
    } : {})
  };

  return (
    <div className="mri-viewer" id="mri-viewer">
      <div className="mri-viewer-header">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <Component1Icon width={16} height={16} style={{ color: "var(--text-secondary)" }} />
          <h3>Liver Segmentation</h3>
        </div>
        <div
          className="toggle-container"
          onClick={() => setShowOverlay((v) => !v)}
          id="overlay-toggle"
        >
          <div className={`toggle-track ${showOverlay ? "active" : ""}`}>
            <div className="toggle-thumb" />
          </div>
          <span style={{ fontSize: "0.8125rem", fontWeight: 500, color: "var(--text-secondary)" }}>
            Overlay
          </span>
        </div>
      </div>

      <div className="mri-viewer-body">
        {isProjecting && years !== null && (
          <div className="mri-projection-banner" style={{ opacity: degradation > 0.2 ? 1 : 0.5 }}>
            Projected Liver State — Year {years}
          </div>
        )}

        <div className="mri-canvas-wrapper">
          <div className="mri-canvas" role="img" aria-label={`MRI slice ${sliceIdx}`}>
            <div className="mri-body-outline">
              <div className="mri-spine" />
              <div className="mri-organ mri-kidney-l" />
              <div className="mri-organ mri-kidney-r" />
              <div 
                className={`mri-liver ${showOverlay ? "show-overlay" : ""} ${isProjecting ? "is-projecting" : ""}`}
                style={dynamicStyle}
              >
                {showOverlay && <LayersIcon width={16} height={16} style={{ color: "rgba(255,255,255,0.5)" }} />}
                <div className="mri-liver-scarring" />
              </div>
            </div>

            <div className="mri-slice-label mono">
              Slice {sliceIdx} · {sliceData.width}×{sliceData.height}
            </div>
            {isProjecting ? (
              <div className="mri-pixel-label mono" style={{ color: `hsl(${hue}, 80%, 60%)` }}>
                F{projectedStageValue.toFixed(1)} Equivalent
              </div>
            ) : (
              <div className="mri-pixel-label mono" style={{ color: "var(--accent)" }}>
                {sliceData.liverPixels.toLocaleString()} liver px
              </div>
            )}
            <div className="mri-mock-label">MOCK VISUALIZATION</div>
          </div>
        </div>

        <div className="mri-nav">
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentSlice((i) => Math.max(0, i - 1))}
            disabled={currentSlice === 0}
            id="mri-prev-slice"
          >
            <ChevronLeftIcon width={18} height={18} />
          </button>

          <div className="mri-slice-indicators">
            {sliceKeys.map((key, i) => (
              <button
                key={key}
                className={`mri-slice-dot ${i === currentSlice ? "active" : ""}`}
                onClick={() => setCurrentSlice(i)}
                aria-label={`Go to slice ${key}`}
              />
            ))}
          </div>

          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentSlice((i) => Math.min(sliceKeys.length - 1, i + 1))}
            disabled={currentSlice === sliceKeys.length - 1}
            id="mri-next-slice"
          >
            <ChevronRightIcon width={18} height={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
