import { useState } from "react";
import "./MriViewer.css";

export default function MriViewer({ segmentation }) {
  const keys = Object.keys(segmentation.masks ?? {}).sort((a, b) => Number(a) - Number(b));
  const [current, setCurrent] = useState(0);
  const [overlay, setOverlay] = useState(true);
  const index = keys[current];
  const slice = segmentation.masks?.[index];
  if (!slice) return <div className="mri-viewer">No scan previews available.</div>;
  return (
    <div className="mri-viewer" id="mri-viewer">
      <div className="mri-viewer-header">
        <h3>Actual scan: slice {index}</h3>
        <label><input type="checkbox" checked={overlay} onChange={e => setOverlay(e.target.checked)} /> Selected mask</label>
      </div>
      <img src={overlay ? slice.overlay : slice.image} alt={`In-phase MRI slice ${index}${overlay ? ' with selected liver outline' : ''}`} style={{ width: '100%', imageRendering: 'pixelated', background: 'black' }} />
      <p>{slice.width} ? {slice.height} ? {slice.liverPixels.toLocaleString()} liver pixels</p>
      <p className="text-tertiary">Yellow: selected mask. This scan does not change with the projection slider.</p>
      <div className="mri-nav">
        <button className="btn btn-secondary" disabled={current === 0} onClick={() => setCurrent(current - 1)}>Previous</button>
        <span>{current + 1} / {keys.length}</span>
        <button className="btn btn-secondary" disabled={current === keys.length - 1} onClick={() => setCurrent(current + 1)}>Next</button>
      </div>
    </div>
  );
}
