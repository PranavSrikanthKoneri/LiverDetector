import { useId } from "react";
import scan from "../assets/design/chaos-scan.png";
import mask from "../assets/design/chaos-mask.png";
import outline from "../assets/design/chaos-outline.png";

const liverPath = "M95 175C115 134 163 126 206 145C238 158 284 137 303 157C312 171 281 185 256 190C229 194 222 217 203 220C180 225 192 258 162 273C130 288 99 265 91 237C83 211 83 196 95 175Z";

export default function ScanIllustration({ real = false, layer = 1, compact = false }) {
  const patternId = useId();
  return (
    <div className={`scan-illustration ${real ? "scan-real" : "scan-abstract"} ${compact ? "scan-compact" : ""}`} data-layer={layer}>
      <div className="scan-figure-top"><span>{real ? "Example MRI" : "Inside the image"}</span><span>Axial view</span></div>
      <div className="scan-art">
        {real ? <>
          {layer === 3 ? (
            <div className="scan-context" aria-label="Example report layout showing separate imaging measurements and questionnaire risk">
              <div className="context-heading"><img src={scan} alt="Example abdominal MRI" /><div><span>One view</span><strong>Image + context</strong></div></div>
              <div className="context-row"><span>01</span><div><strong>Fat estimate</strong><small>From the paired MRI images</small></div></div>
              <div className="context-row"><span>02</span><div><strong>Texture patterns</strong><small>Within the selected liver region</small></div></div>
              <div className="context-row"><span>03</span><div><strong>Questionnaire risk</strong><small>From the clinical answers</small></div></div>
            </div>
          ) : (
            <div className={`scan-image-stage ${layer === 2 ? "scan-isolated" : ""}`}>
              <img className="sample-scan" src={scan} alt={layer === 2 ? "Liver region isolated from the example MRI" : "Example abdominal MRI with the liver outlined"}
                style={layer === 2 ? { maskImage: `url(${mask})`, WebkitMaskImage: `url(${mask})` } : undefined} />
              <img className="sample-outline" src={outline} alt="" aria-hidden="true" style={{ opacity: layer >= 1 ? 1 : 0 }} />
            </div>
          )}
        </> : (
          <svg viewBox="0 0 400 380" role="img" aria-label="Schematic abdominal cross-section with a highlighted liver region; not a medical scan">
            <defs><pattern id={patternId} width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="0.85" fill="#225e91" opacity="0.45" /></pattern></defs>
            <g className="scan-body">
              <path d="M58 132C90 94 158 83 204 88C272 78 336 118 350 182C372 253 326 304 260 319C212 332 176 325 132 321C77 316 37 282 39 230C30 192 39 160 58 132Z" fill="#e3e7e3" stroke="#c0cbc8" strokeWidth="1.2" />
              <path d="M70 145C100 113 161 106 203 111C262 102 321 133 331 189C352 247 316 285 258 299C212 310 173 303 134 300C88 296 57 270 58 231C49 194 52 169 70 145Z" fill="#f4f5f0" stroke="#c4cfcb" />
              <path d="M264 202C282 181 310 195 313 219C320 243 301 265 287 263C267 261 252 222 264 202Z" fill="#d3dbd5" />
              <path d="M223 236C231 222 251 226 257 243C265 260 246 277 233 269C226 264 219 247 223 236Z" fill="#dce2dc" stroke="#b6c5bf" />
              <path d="M161 278C162 263 177 255 189 263L205 289L182 301Z" fill="#d3dbd5" />
              <circle cx="207" cy="267" r="17" fill="#f8f9f5" stroke="#bbc8c0" strokeWidth="5" />
              <path d={liverPath} fill="#bacac7" />
            </g>
            <path className="illustration-liver" d={liverPath} fill={layer === 2 ? `url(#${patternId})` : "#c6ddea"} fillOpacity={layer >= 1 ? 0.9 : 0} stroke="#225e91" strokeWidth="1.7" strokeOpacity={layer >= 1 ? 1 : 0} />
            <g className="scan-crosshair" fill="none" stroke="#879b9c" strokeWidth="1"><path d="M25 75V56H44M356 56H375V75M25 313V332H44M356 332H375V313" /></g>
          </svg>
        )}
      </div>
      <div className="scan-figure-bottom"><span className="scan-dot" /><span>{layer === 0 ? "The whole image" : layer === 1 ? "The liver, in focus" : real ? (layer === 3 ? "The findings, together" : "The region we measure") : "Exploring image patterns"}</span></div>
      {!real && <p className="scan-source">Schematic illustration</p>}
    </div>
  );
}
