import React, { useState } from "react";

const WIDTH = 720;
const HEIGHT = 300;
const PAD = { top: 22, right: 22, bottom: 42, left: 22 };
const GRID_LINES = 5;
const HOUR_MS = 60 * 60 * 1000;

export const SERIES = [
  { key: "temperatura", label: "Temp (°C)", unit: "°C", color: "#c98a00" },
  { key: "humedad", label: "Humedad (%)", unit: "%", color: "#1a73e8" },
];

const formatHour = (date) => date.toLocaleTimeString("es-BO", { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
const formatDateTime = (date) => date.toLocaleString("es-BO", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit", hourCycle: "h23" });

export function LineChart24h({ points }) {
  const [hovered, setHovered] = useState(null);
  const end = Date.now();
  const start = end - 24 * HOUR_MS;
  const innerW = WIDTH - PAD.left - PAD.right;
  const innerH = HEIGHT - PAD.top - PAD.bottom;
  const x = (time) => PAD.left + Math.max(0, Math.min(1, (time - start) / (end - start))) * innerW;

  const lines = SERIES.map((serie) => {
    const values = points.filter((point) => point[serie.key] !== null && point[serie.key] !== undefined).map((point) => ({ time: new Date(point.hour).getTime(), value: Number(point[serie.key]) }));
    if (!values.length) return { ...serie, values: [], min: null, max: null };
    const min = Math.min(...values.map((value) => value.value));
    const max = Math.max(...values.map((value) => value.value));
    const range = max - min || 1;
    const y = (value) => PAD.top + innerH * (0.88 - ((value - min) / range) * 0.76);
    return { ...serie, min, max, values: values.map((value) => ({ ...value, cx: x(value.time), cy: y(value.value) })) };
  });

  const ticks = Array.from({ length: 7 }, (_, index) => start + (index * 24 * HOUR_MS) / 6);
  const tooltipX = hovered ? Math.min(Math.max(hovered.cx - 82, PAD.left), WIDTH - PAD.right - 164) : 0;
  const tooltipY = hovered ? Math.max(hovered.cy - 72, PAD.top) : 0;
  const selectNearest = (event, line) => {
    const bounds = event.currentTarget.ownerSVGElement.getBoundingClientRect();
    const scale = Math.min(bounds.width / WIDTH, bounds.height / HEIGHT);
    const offsetX = (bounds.width - WIDTH * scale) / 2;
    const offsetY = (bounds.height - HEIGHT * scale) / 2;
    const pointerX = (event.clientX - bounds.left - offsetX) / scale;
    const pointerY = (event.clientY - bounds.top - offsetY) / scale;
    const value = line.values.reduce((nearest, current) => {
      const nearestDistance = (nearest.cx - pointerX) ** 2 + (nearest.cy - pointerY) ** 2;
      const currentDistance = (current.cx - pointerX) ** 2 + (current.cy - pointerY) ** 2;
      return currentDistance < nearestDistance ? current : nearest;
    });
    setHovered({ ...value, key: line.key, label: line.label, unit: line.unit });
  };

  return <div className="admin-chart-wrap"><svg className="admin-chart" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Gráfico interactivo de temperatura y humedad de las últimas 24 horas" preserveAspectRatio="xMidYMid meet" onMouseLeave={() => setHovered(null)}>
    {Array.from({ length: GRID_LINES }, (_, index) => { const gy = PAD.top + (index * innerH) / (GRID_LINES - 1); return <line key={index} x1={PAD.left} x2={WIDTH - PAD.right} y1={gy} y2={gy} className="admin-chart__grid" />; })}
    {ticks.map((tick, index) => <text key={tick} x={x(tick)} y={HEIGHT - 12} className="admin-chart__label" textAnchor={index === 0 ? "start" : index === ticks.length - 1 ? "end" : "middle"}>{index === ticks.length - 1 ? "Ahora" : formatHour(new Date(tick))}</text>)}
    {hovered && <line x1={hovered.cx} x2={hovered.cx} y1={PAD.top} y2={HEIGHT - PAD.bottom} className="admin-chart__guide" />}
    {lines.map((line) => line.values.length > 0 && <g key={line.key}><polyline points={line.values.map((value) => `${value.cx},${value.cy}`).join(" ")} fill="none" stroke={line.color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" /><polyline points={line.values.map((value) => `${value.cx},${value.cy}`).join(" ")} fill="none" stroke="transparent" strokeWidth="18" strokeLinejoin="round" strokeLinecap="round" onMouseMove={(event) => selectNearest(event, line)} />{line.values.map((value) => <circle key={value.time} cx={value.cx} cy={value.cy} r={hovered?.key === line.key && hovered.time === value.time ? 5.5 : 4} className="admin-chart__point" fill={line.color} onMouseEnter={() => setHovered({ ...value, key: line.key, label: line.label, unit: line.unit })} />)}</g>)}
    {hovered && <g className="admin-chart__tooltip" transform={`translate(${tooltipX} ${tooltipY})`} pointerEvents="none"><rect width="164" height="56" rx="7" /><text x="10" y="20" className="admin-chart__tooltip-title">{hovered.label}: {hovered.value.toFixed(1)} {hovered.unit}</text><text x="10" y="40" className="admin-chart__tooltip-time">{formatDateTime(new Date(hovered.time))}</text></g>}
  </svg><div className="admin-chart-summary" aria-label="Resumen de rangos">{lines.filter((line) => line.values.length).map((line) => <span key={line.key}><i style={{ background: line.color }} />{line.label}: {line.min.toFixed(1)}–{line.max.toFixed(1)} {line.unit}</span>)}</div></div>;
}
