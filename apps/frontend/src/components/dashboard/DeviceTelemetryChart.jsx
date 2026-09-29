import React, { useEffect, useMemo, useState } from "react";
import { Eye, EyeOff, LoaderCircle, Maximize2, Minimize2 } from "lucide-react";
import { getDeviceTelemetry } from "../../services/reportApi.js";

const WIDTH = 900;
const HEIGHT = 290;
const PAD = { top: 22, right: 24, bottom: 38, left: 24 };
const COLORS = ["#0b5a3b", "#1a73e8", "#c98a00", "#8e44ad", "#d35400", "#00838f", "#c0392b", "#546e7a"];
const PERIODS = [["1h", "1 h"], ["6h", "6 h"], ["24h", "24 h"], ["7d", "7 días"], ["30d", "30 días"]];
const RESOLUTIONS = [["15s", "15 s"], ["1m", "1 min"], ["5m", "5 min"], ["15m", "15 min"], ["1h", "1 h"], ["1d", "1 día"]];
const metricLabel = { temperatura: "Temperatura (°C)", humedad: "Humedad (%)" };

const formatTime = (value, period) => new Date(value).toLocaleString("es-BO", period === "1h" || period === "6h" ? { hour: "2-digit", minute: "2-digit", hourCycle: "h23" } : { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" });

export function DeviceTelemetryChart() {
  const [period, setPeriod] = useState("24h");
  const [resolution, setResolution] = useState("5m");
  const [metric, setMetric] = useState("temperatura");
  const [data, setData] = useState(null);
  const [visible, setVisible] = useState(null);
  const [hovered, setHovered] = useState(null);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let mounted = true;
    getDeviceTelemetry({ period, resolution }).then((result) => {
      if (!mounted) return;
      setData(result);
      setVisible((current) => current === null ? new Set(result.devices.slice(0, 1).map((device) => device.id)) : new Set([...current].filter((id) => result.devices.some((device) => device.id === id))));
      setError("");
    }).catch((requestError) => mounted && setError(requestError.message));
    return () => { mounted = false; };
  }, [period, resolution]);

  const { lines, start, end } = useMemo(() => {
    if (!data) return { lines: [], start: 0, end: 1 };
    const filtered = data.points.filter((point) => point.metric_code === metric);
    const timestamps = filtered.map((point) => new Date(point.bucket).getTime());
    const endTime = timestamps.length ? Math.max(...timestamps) : Date.now();
    const spanMs = { "1h": 3600000, "6h": 21600000, "24h": 86400000, "7d": 604800000, "30d": 2592000000 }[period];
    const startTime = endTime - spanMs;
    return { start: startTime, end: endTime, lines: data.devices.map((device, index) => ({ ...device, color: COLORS[index % COLORS.length], values: filtered.filter((point) => point.device_id === device.id).map((point) => ({ ...point, time: new Date(point.bucket).getTime(), value: Number(point.value) })) })).filter((line) => line.values.length) };
  }, [data, metric, period]);

  const activeLines = lines.filter((line) => visible?.has(line.id));
  const values = activeLines.flatMap((line) => line.values.map((point) => point.value));
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;
  const range = max - min || 1;
  const innerW = WIDTH - PAD.left - PAD.right;
  const innerH = HEIGHT - PAD.top - PAD.bottom;
  const pointX = (time) => PAD.left + Math.max(0, Math.min(1, (time - start) / (end - start || 1))) * innerW;
  const pointY = (value) => PAD.top + innerH * (0.88 - ((value - min) / range) * 0.76);
  const setOnly = (id) => setVisible(new Set([id]));
  const chooseNearest = (event, line) => {
    const bounds = event.currentTarget.ownerSVGElement.getBoundingClientRect();
    const scale = Math.min(bounds.width / WIDTH, bounds.height / HEIGHT);
    const offsetX = (bounds.width - WIDTH * scale) / 2;
    const offsetY = (bounds.height - HEIGHT * scale) / 2;
    const px = (event.clientX - bounds.left - offsetX) / scale;
    const py = (event.clientY - bounds.top - offsetY) / scale;
    const nearest = line.values.reduce((best, value) => {
      const a = (pointX(best.time) - px) ** 2 + (pointY(best.value) - py) ** 2;
      const b = (pointX(value.time) - px) ** 2 + (pointY(value.value) - py) ** 2;
      return b < a ? value : best;
    });
    setHovered({ ...nearest, device: line.name, color: line.color });
  };
  const tooltipX = hovered ? Math.min(Math.max(pointX(hovered.time) - 74, PAD.left), WIDTH - PAD.right - 148) : 0;
  const tooltipY = hovered ? Math.max(pointY(hovered.value) - 58, PAD.top) : 0;

  const denseView = activeLines.length > 3 && ["15s", "1m"].includes(resolution);
  return <article className={`dashboard-card device-telemetry-card${expanded ? " device-telemetry-card--expanded" : ""}`}><header className="admin-card-header"><div><h2 className="dashboard-card__title">Lecturas por dispositivo</h2><p className="device-telemetry-card__subtitle">Selecciona la métrica, el periodo y la resolución de visualización.</p></div><button type="button" className="device-telemetry-card__expand" onClick={() => setExpanded((current) => !current)}>{expanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}{expanded ? "Vista normal" : "Vista amplia"}</button></header><div className="telemetry-controls"><div><span>Periodo</span>{PERIODS.map(([value, label]) => <button key={value} type="button" className={period === value ? "is-active" : ""} onClick={() => setPeriod(value)}>{label}</button>)}</div><div><span>Resolución</span>{RESOLUTIONS.map(([value, label]) => <button key={value} type="button" className={resolution === value ? "is-active" : ""} onClick={() => setResolution(value)}>{label}</button>)}</div><div><span>Métrica</span>{Object.entries(metricLabel).map(([value, label]) => <button key={value} type="button" className={metric === value ? "is-active" : ""} onClick={() => setMetric(value)}>{label}</button>)}</div></div>{data && <div className="telemetry-devices"><button type="button" onClick={() => setVisible(new Set(data.devices.map((device) => device.id)))}><Eye size={14} /> Todos</button><button type="button" onClick={() => setVisible(new Set())}><EyeOff size={14} /> Ocultar todos</button>{lines.map((line) => <span key={line.id}><button type="button" className={visible?.has(line.id) ? "is-visible" : ""} onClick={() => setVisible((current) => { const next = new Set(current ?? []); next.has(line.id) ? next.delete(line.id) : next.add(line.id); return next; })}><i style={{ background: line.color }} />{line.name}</button><button type="button" className="telemetry-devices__only" onClick={() => setOnly(line.id)}>Solo</button></span>)}</div>}{denseView && <p className="telemetry-density-note">Vista de alta densidad: para una lectura más clara usa “Solo” o una resolución de 5 min o mayor.</p>}{!data && !error && <p className="device-muted"><LoaderCircle size={16} className="telemetry-loading" /> Cargando lecturas por dispositivo...</p>}{error && <p className="device-form-error">{error}</p>}{data && <div className="device-telemetry-chart-wrap"><svg className="device-telemetry-chart" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} preserveAspectRatio="xMidYMid meet" onMouseLeave={() => setHovered(null)}>{[0, 1, 2, 3, 4].map((index) => <line key={index} x1={PAD.left} x2={WIDTH - PAD.right} y1={PAD.top + (index * innerH) / 4} y2={PAD.top + (index * innerH) / 4} className="admin-chart__grid" />)}{activeLines.map((line) => <g key={line.id}><polyline points={line.values.map((value) => `${pointX(value.time)},${pointY(value.value)}`).join(" ")} fill="none" stroke={line.color} strokeWidth={denseView ? "1.5" : "2.3"} strokeOpacity={denseView ? ".72" : "1"} strokeLinejoin="round" strokeLinecap="round" /><polyline points={line.values.map((value) => `${pointX(value.time)},${pointY(value.value)}`).join(" ")} fill="none" stroke="transparent" strokeWidth="18" onMouseMove={(event) => chooseNearest(event, line)} /></g>)}{hovered && <><line x1={pointX(hovered.time)} x2={pointX(hovered.time)} y1={PAD.top} y2={HEIGHT - PAD.bottom} className="admin-chart__guide" /><g transform={`translate(${tooltipX} ${tooltipY})`} className="admin-chart__tooltip" pointerEvents="none"><rect width="148" height="46" rx="7" /><text x="9" y="18" className="admin-chart__tooltip-title">{hovered.device}: {hovered.value.toFixed(2)}</text><text x="9" y="34" className="admin-chart__tooltip-time">{formatTime(hovered.bucket, period)}</text></g></>}<text x={PAD.left} y={HEIGHT - 10} className="admin-chart__label">{formatTime(start, period)}</text><text x={WIDTH - PAD.right} y={HEIGHT - 10} textAnchor="end" className="admin-chart__label">Ahora</text></svg>{values.length > 0 && <p className="device-telemetry-chart__range">Rango visible: {min.toFixed(2)}–{max.toFixed(2)} {metric === "temperatura" ? "°C" : "%"}</p>}{values.length === 0 && <p className="device-muted">No hay dispositivos seleccionados o lecturas para este periodo.</p>}</div>}</article>;
}
