
import React from "react";

// Configuración de las series según el tipo de reporte.
const CHART_SERIES = {
  devices: [
    { key: "total", label: "Dispositivos registrados", color: "#059669" },
  ],
  alerts: [
    { key: "criticas", label: "Críticas", color: "#dc2626" },
    { key: "advertencias", label: "Advertencias", color: "#f59e0b" },
  ],
  tickets: [
    { key: "abiertos", label: "Abiertos", color: "#2563eb" },
    { key: "en_revision", label: "En revisión", color: "#f59e0b" },
    { key: "resueltos", label: "Resueltos", color: "#059669" },
    { key: "cerrados", label: "Cerrados", color: "#64748b" },
  ],
};

const chartContainerStyle = {
  padding: "24px",
  marginBottom: "30px",
  background: "#ffffff",
  border: "1px solid #e2e8f0",
  borderRadius: "16px",
  boxShadow: "0 6px 20px rgba(15, 23, 42, 0.04)",
};

function formatDay(day) {
  if (!day) return "";

  const parts = String(day).slice(0, 10).split("-");

  if (parts.length !== 3) return String(day);

  return `${parts[2]}/${parts[1]}`;
}

function getNumericValue(point, key) {
  const value = Number(point?.[key] ?? 0);

  return Number.isFinite(value) && value > 0 ? value : 0;
}

export function ReportTimelineChart({
  type,
  timeline = [],
  title = "Evolución histórica",
}) {
  const series = CHART_SERIES[type] ?? CHART_SERIES.devices;

  const points = Array.isArray(timeline)
    ? [...timeline]
        .filter((point) => point && point.day)
        .sort((a, b) => String(a.day).localeCompare(String(b.day)))
    : [];

  const hasData = points.some((point) =>
    series.some((item) => getNumericValue(point, item.key) > 0)
  );

  if (!hasData) {
    return (
      <section style={chartContainerStyle}>
        <h3 style={{ margin: "0 0 12px", color: "#0f172a" }}>
          {title}
        </h3>

        <p
          style={{
            margin: 0,
            padding: "24px",
            textAlign: "center",
            color: "#64748b",
            background: "#f8fafc",
            borderRadius: "10px",
          }}
        >
          No hay datos históricos para mostrar con los filtros seleccionados.
        </p>
      </section>
    );
  }

  // Dimensiones internas del SVG.
  const width = 900;
  const height = 320;

  const padding = {
    top: 25,
    right: 20,
    bottom: 65,
    left: 55,
  };

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  const maximum = Math.max(
    1,
    ...points.map((point) =>
      series.reduce(
        (sum, item) => sum + getNumericValue(point, item.key),
        0
      )
    )
  );

  // Redondear la escala vertical para facilitar su lectura.
  const steps = 4;
  const stepValue = Math.max(1, Math.ceil(maximum / steps));
  const chartMaximum = stepValue * steps;

  const groupWidth = plotWidth / points.length;
  const barWidth = Math.min(48, groupWidth * 0.65);

  // Evitar etiquetas amontonadas cuando existen muchas fechas.
  const labelInterval = Math.max(1, Math.ceil(points.length / 9));

  return (
    <section style={chartContainerStyle}>
      <h3
        style={{
          margin: "0 0 8px",
          color: "#0f172a",
          fontSize: "18px",
        }}
      >
        {title}
      </h3>

      <p
        style={{
          margin: "0 0 20px",
          color: "#64748b",
          fontSize: "14px",
        }}
      >
        Registros agrupados por fecha, según los filtros seleccionados.
      </p>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "12px 20px",
          marginBottom: "18px",
        }}
      >
        {series.map((item) => (
          <div
            key={item.key}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "13px",
              color: "#475569",
            }}
          >
            <span
              aria-hidden="true"
              style={{
                width: "12px",
                height: "12px",
                borderRadius: "3px",
                backgroundColor: item.color,
              }}
            />

            {item.label}
          </div>
        ))}
      </div>

      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label={`${title}. Gráfico de barras con registros por fecha.`}
          style={{
            display: "block",
            width: "100%",
            minWidth: "500px",
            height: "auto",
          }}
        >
          {/* Líneas horizontales y escala vertical */}
          {Array.from({ length: steps + 1 }, (_, index) => {
            const value = index * stepValue;
            const y =
              padding.top +
              plotHeight -
              (value / chartMaximum) * plotHeight;

            return (
              <g key={`grid-${index}`}>
                <line
                  x1={padding.left}
                  x2={width - padding.right}
                  y1={y}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeDasharray="4 4"
                />

                <text
                  x={padding.left - 12}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="12"
                  fill="#64748b"
                >
                  {value}
                </text>
              </g>
            );
          })}

          {/* Barras apiladas por fecha */}
          {points.map((point, index) => {
            const centerX =
              padding.left + index * groupWidth + groupWidth / 2;

            let accumulated = 0;

            return (
              <g key={`${point.day}-${index}`}>
                {series.map((item) => {
                  const value = getNumericValue(point, item.key);

                  const barHeight =
                    (value / chartMaximum) * plotHeight;

                  const y =
                    padding.top +
                    plotHeight -
                    ((accumulated + value) / chartMaximum) *
                      plotHeight;

                  accumulated += value;

                  if (value === 0) return null;

                  return (
                    <rect
                      key={item.key}
                      x={centerX - barWidth / 2}
                      y={y}
                      width={barWidth}
                      height={barHeight}
                      rx={2}
                      fill={item.color}
                    >
                      <title>
                        {`${point.day} — ${item.label}: ${value}`}
                      </title>
                    </rect>
                  );
                })}

                {(index % labelInterval === 0 ||
                  index === points.length - 1) && (
                  <text
                    x={centerX}
                    y={height - padding.bottom + 22}
                    textAnchor="middle"
                    fontSize="12"
                    fill="#64748b"
                  >
                    {formatDay(point.day)}
                  </text>
                )}
              </g>
            );
          })}

          {/* Línea base */}
          <line
            x1={padding.left}
            x2={width - padding.right}
            y1={padding.top + plotHeight}
            y2={padding.top + plotHeight}
            stroke="#94a3b8"
          />

          <text
            x={width / 2}
            y={height - 12}
            textAnchor="middle"
            fontSize="12"
            fill="#64748b"
          >
            Fecha (día/mes)
          </text>
        </svg>
      </div>

      <p
        style={{
          margin: "12px 0 0",
          fontSize: "12px",
          color: "#64748b",
        }}
      >
        Pasa el cursor sobre una barra para consultar su fecha y cantidad.
      </p>
    </section>
  );
}

export default ReportTimelineChart;
