import React from "react";

// Gráfico de líneas en SVG puro (sin librerías) para temperatura y humedad de las últimas 24 h.
// Cada métrica usa su propia escala vertical para que ambas líneas se lean bien.

const WIDTH = 720;
const HEIGHT = 280;
const PAD = { top: 16, right: 16, bottom: 30, left: 16 };
const GRID_LINES = 5;
const HOUR_MS = 60 * 60 * 1000;

export const SERIES = [
  { key: "temperatura", label: "Temp (°C)", unit: "°C", color: "#c98a00" },
  { key: "humedad", label: "Humedad (%)", unit: "%", color: "#1a73e8" },
];

const formatHour = (date) => date.toLocaleTimeString("es-BO", { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });

export function LineChart24h({ points }) {
  const end = Date.now();
  const start = end - 24 * HOUR_MS;
  const innerW = WIDTH - PAD.left - PAD.right;
  const innerH = HEIGHT - PAD.top - PAD.bottom;
  const x = (time) => PAD.left + ((time - start) / (end - start)) * innerW;

  const lines = SERIES.map((serie) => {
    const values = points
      .filter((p) => p[serie.key] !== null && p[serie.key] !== undefined)
      .map((p) => ({ time: new Date(p.hour).getTime(), value: Number(p[serie.key]) }));
    if (values.length === 0) return { ...serie, values: [] };
    const min = Math.min(...values.map((v) => v.value));
    const max = Math.max(...values.map((v) => v.value));
    const range = max - min || 1;
    // Margen de 15 % arriba y abajo para que la línea no toque los bordes.
    const y = (value) => PAD.top + innerH * (0.85 - ((value - min) / range) * 0.7);
    return { ...serie, values: values.map((v) => ({ ...v, cx: x(v.time), cy: y(v.value) })) };
  });

  const ticks = Array.from({ length: 7 }, (_, i) => start + (i * 24 * HOUR_MS) / 6);

  return (
    <svg className="admin-chart" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img"
      aria-label="Gráfico de temperatura y humedad de las últimas 24 horas" preserveAspectRatio="none">
      {Array.from({ length: GRID_LINES }, (_, i) => {
        const gy = PAD.top + (i * innerH) / (GRID_LINES - 1);
        return <line key={i} x1={PAD.left} x2={WIDTH - PAD.right} y1={gy} y2={gy} className="admin-chart__grid" />;
      })}
      {ticks.map((tick, i) => (
        <text key={tick} x={x(tick)} y={HEIGHT - 8} className="admin-chart__label"
          textAnchor={i === 0 ? "start" : i === ticks.length - 1 ? "end" : "middle"}>
          {i === ticks.length - 1 ? "Ahora" : formatHour(new Date(tick))}
        </text>
      ))}
      {lines.map((line) => line.values.length > 0 && (
        <g key={line.key}>
          <polyline points={line.values.map((v) => `${v.cx},${v.cy}`).join(" ")} fill="none"
            stroke={line.color} strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round"
            vectorEffect="non-scaling-stroke" />
          {line.values.map((v) => (
            <circle key={v.time} cx={v.cx} cy={v.cy} r="7" className="admin-chart__hit">
              <title>{`${line.label.split(" ")[0]}: ${v.value.toFixed(1)} ${line.unit} · ${formatHour(new Date(v.time))}`}</title>
            </circle>
          ))}
        </g>
      ))}
    </svg>
  );
}
