import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Line,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import "./ProgressionChart.css";

const STAGE_TICKS = [
  { value: 0, label: "F0" },
  { value: 1, label: "F1" },
  { value: 2, label: "F2" },
  { value: 3, label: "F3" },
  { value: 4, label: "F4" },
];

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="progression-tooltip">
      <div className="progression-tooltip-title">Year {label}</div>
      {payload.map((entry) => {
        if (entry.dataKey === "baselineRange" || entry.dataKey === "interventionRange")
          return null;
        return (
          <div key={entry.dataKey} className="progression-tooltip-row">
            <span className="dot" style={{ background: entry.color }} />
            <span className="text-secondary">{entry.name}:</span>
            <span className="mono" style={{ fontWeight: 600 }}>{entry.value?.toFixed(2)}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function ProgressionChart({ 
  baseline, 
  intervention,
  years,
  onYearsChange,
  showIntervention,
  onInterventionChange
}) {
  const chartData = baseline
    .filter((pt) => pt.year <= years)
    .map((pt, i) => ({
      year: pt.year,
      baseline: pt.stage_value,
      baselineRange: [pt.low, pt.high],
      intervention: intervention[i]?.stage_value,
      interventionRange: [intervention[i]?.low, intervention[i]?.high],
    }));

  return (
    <div className="progression-chart" id="progression-chart">
      {/* Controls */}
      <div className="progression-controls">
        <div className="progression-slider-group">
          <label className="input-label" htmlFor="year-slider">Projection horizon (Years)</label>
          <div className="progression-slider-row">
            <input
              type="range"
              id="year-slider"
              min={0}
              max={20}
              value={years}
              onChange={(e) => onYearsChange(parseInt(e.target.value, 10))}
            />
            <span className="progression-year-display mono">{years}</span>
          </div>
        </div>

        <div
          className="toggle-container"
          onClick={() => onInterventionChange((v) => !v)}
          id="intervention-toggle"
        >
          <div className={`toggle-track ${showIntervention ? "active" : ""}`}>
            <div className="toggle-thumb" />
          </div>
          <div className="progression-toggle-label">
            <span style={{ fontWeight: 500, fontSize: "0.8125rem" }}>
              Slower-progression scenario
            </span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="progression-chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <defs>
              <linearGradient id="baselineGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#60a5fa" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#60a5fa" stopOpacity={0.01} />
              </linearGradient>
              <linearGradient id="interventionGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4ade80" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#4ade80" stopOpacity={0.01} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="hsla(0, 0%, 0%, 0.04)" vertical={false} />

            <XAxis
              dataKey="year"
              tick={{ fill: "var(--text-tertiary)", fontSize: 11 }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
            />

            <YAxis
              domain={[0, 4]}
              ticks={[0, 1, 2, 3, 4]}
              tickFormatter={(v) => STAGE_TICKS.find((t) => t.value === v)?.label || v}
              tick={{ fill: "var(--text-tertiary)", fontSize: 11 }}
              axisLine={{ stroke: "var(--border)" }}
              tickLine={false}
              width={32}
            />

            <Tooltip content={<CustomTooltip />} />

            {STAGE_TICKS.map((t) => (
              <ReferenceLine key={t.value} y={t.value} stroke="hsla(0, 0%, 0%, 0.04)" />
            ))}

            <Area
              type="monotone"
              dataKey="baselineRange"
              fill="url(#baselineGrad)"
              stroke="none"
              animationDuration={400}
            />

            {showIntervention && (
              <Area
                type="monotone"
                dataKey="interventionRange"
                fill="url(#interventionGrad)"
                stroke="none"
                animationDuration={400}
              />
            )}

            <Line
              type="monotone"
              dataKey="baseline"
              name="Baseline"
              stroke="#60a5fa"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 3, strokeWidth: 0 }}
              animationDuration={400}
            />

            {showIntervention && (
              <Line
                type="monotone"
                dataKey="intervention"
                name="Slower scenario"
                stroke="#34c759"
                strokeWidth={2}
                strokeDasharray="4 3"
                dot={false}
                activeDot={{ r: 3, strokeWidth: 0 }}
                animationDuration={400}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="progression-legend">
        <div className="progression-legend-item">
          <div className="progression-legend-line" style={{ background: "#60a5fa" }} />
          <span>Baseline trajectory</span>
        </div>
        {showIntervention && (
          <div className="progression-legend-item">
            <div className="progression-legend-line progression-legend-line-dashed" style={{ borderTopColor: "#34c759" }} />
            <span>Slower population scenario</span>
          </div>
        )}
      </div>
    </div>
  );
}
