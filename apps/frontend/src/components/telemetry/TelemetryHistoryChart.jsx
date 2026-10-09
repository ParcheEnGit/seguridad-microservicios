import React, { useMemo } from "react";

const WIDTH = 900;
const HEIGHT = 280;

const PAD = {
  top: 24,
  right: 28,
  bottom: 42,
  left: 52,
};

function formatChartTime(value) {
  return new Intl.DateTimeFormat("es-BO", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function TelemetryHistoryChart({ readings, metricCode }) {
  const chart = useMemo(() => {
    if (!readings?.length) {
      return null;
    }

    const ordered = [...readings]
      .sort(
        (a, b) =>
          new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime(),
      )
      .map((reading) => ({
        ...reading,
        numericValue: Number(reading.value),
        timestamp: new Date(reading.recorded_at).getTime(),
      }));

    const values = ordered.map((reading) => reading.numericValue);
    const timestamps = ordered.map((reading) => reading.timestamp);

    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);

    const startTime = Math.min(...timestamps);
    const endTime = Math.max(...timestamps);

    const valueRange = maxValue - minValue || 1;
    const timeRange = endTime - startTime || 1;

    const innerWidth = WIDTH - PAD.left - PAD.right;
    const innerHeight = HEIGHT - PAD.top - PAD.bottom;

    const x = (timestamp) =>
      PAD.left + ((timestamp - startTime) / timeRange) * innerWidth;

    const y = (value) =>
      PAD.top + innerHeight - ((value - minValue) / valueRange) * innerHeight;

    const points = ordered.map((reading) => ({
      ...reading,
      x: x(reading.timestamp),
      y: y(reading.numericValue),
    }));

    const path = points
      .map(
        (point, index) =>
          `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`,
      )
      .join(" ");

    const yTicks = Array.from({ length: 5 }, (_, index) => {
      const ratio = index / 4;
      const value = maxValue - valueRange * ratio;

      return {
        value,
        y: PAD.top + innerHeight * ratio,
      };
    });

    const xTickIndexes = [
      0,
      Math.floor((points.length - 1) * 0.25),
      Math.floor((points.length - 1) * 0.5),
      Math.floor((points.length - 1) * 0.75),
      points.length - 1,
    ];

    const xTicks = [...new Set(xTickIndexes)].map((index) => points[index]);

    return {
      points,
      path,
      yTicks,
      xTicks,
      minValue,
      maxValue,
    };
  }, [readings]);

  if (!chart) {
    return (
      <div className="history-chart-empty">
        <p>No hay datos disponibles para graficar.</p>
      </div>
    );
  }

  const metricLabel =
    metricCode === "humedad"
      ? "Humedad (%)"
      : metricCode === "temperatura"
        ? "Temperatura (°C)"
        : "Lecturas";

  return (
    <div className="history-chart-container">
      <div className="history-chart-summary">
        <span>
          <i />
          {metricLabel}
        </span>

        <span>
          Mín. <strong>{chart.minValue.toFixed(2)}</strong>
        </span>

        <span>
          Máx. <strong>{chart.maxValue.toFixed(2)}</strong>
        </span>
      </div>

      <div className="history-chart-scroll">
        <svg
          className="history-chart"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-label={`Gráfica histórica de ${metricLabel}`}
        >
          {chart.yTicks.map((tick) => (
            <g key={tick.y}>
              <line
                className="history-chart__grid"
                x1={PAD.left}
                x2={WIDTH - PAD.right}
                y1={tick.y}
                y2={tick.y}
              />

              <text
                className="history-chart__axis-label"
                x={PAD.left - 10}
                y={tick.y + 4}
                textAnchor="end"
              >
                {tick.value.toFixed(1)}
              </text>
            </g>
          ))}

          {chart.xTicks.map((tick, index) => {
            const isFirst = index === 0;
            const isLast = index === chart.xTicks.length - 1;

            return (
              <text
                key={`${tick.id}-${tick.x}`}
                className="history-chart__axis-label"
                x={tick.x}
                y={HEIGHT - 12}
                textAnchor={isFirst ? "start" : isLast ? "end" : "middle"}
              >
                {formatChartTime(tick.recorded_at)}
              </text>
            );
          })}

          <path className="history-chart__line" d={chart.path} />

          {chart.points.map((point) => (
            <circle
              key={point.id}
              className="history-chart__point"
              cx={point.x}
              cy={point.y}
              r="3"
            >
              <title>
                {`${formatChartTime(point.recorded_at)} · ${point.numericValue.toFixed(2)} ${point.unit}`}
              </title>
            </circle>
          ))}
        </svg>
      </div>
    </div>
  );
}
