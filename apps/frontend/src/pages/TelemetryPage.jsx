import React, { useEffect, useState } from "react";
import { CalendarDays, Search } from "lucide-react";

import { TelemetryHistoryChart } from "../components/telemetry/TelemetryHistoryChart.jsx";
import { listDevices } from "../services/deviceApi.js";
import { getTelemetryHistory } from "../services/telemetryApi.js";

const PAGE_SIZE = 10;

function toDateTimeLocal(date) {
  const offset = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - offset * 60 * 1000);
  return localDate.toISOString().slice(0, 16);
}

function createInitialFilters() {
  const end = new Date();
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);

  return {
    deviceId: "",
    metricCode: "",
    startAt: toDateTimeLocal(start),
    endAt: toDateTimeLocal(end),
  };
}

function formatDate(timestamp) {
  return new Intl.DateTimeFormat("es-BO", {
    dateStyle: "short",
    timeStyle: "medium",
  }).format(new Date(timestamp));
}

export function TelemetryPage() {
  const [devices, setDevices] = useState([]);
  const [filters, setFilters] = useState(createInitialFilters);
  const [appliedFilters, setAppliedFilters] = useState(null);

  const [readings, setReadings] = useState([]);
  const [chartReadings, setChartReadings] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);

  const [loadingDevices, setLoadingDevices] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [loadingChart, setLoadingChart] = useState(false);
  const [error, setError] = useState("");

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    let mounted = true;

    async function loadDevices() {
      try {
        setLoadingDevices(true);

        const data = await listDevices({
          limit: 100,
          offset: 0,
        });

        if (!mounted) return;

        const availableDevices = data.items ?? [];
        setDevices(availableDevices);

        if (availableDevices.length > 0) {
          setFilters((current) => ({
            ...current,
            deviceId: current.deviceId || availableDevices[0].id,
          }));
        }
      } catch (requestError) {
        if (mounted) setError(requestError.message);
      } finally {
        if (mounted) setLoadingDevices(false);
      }
    }

    loadDevices();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!appliedFilters) return;

    let mounted = true;

    async function loadHistory() {
      try {
        setLoadingHistory(true);
        setError("");

        const data = await getTelemetryHistory({
          ...appliedFilters,
          limit: PAGE_SIZE,
          offset: page * PAGE_SIZE,
        });

        if (!mounted) return;

        setReadings(data.items ?? []);
        setTotal(data.total ?? 0);
      } catch (requestError) {
        if (!mounted) return;

        setReadings([]);
        setTotal(0);
        setError(requestError.message);
      } finally {
        if (mounted) setLoadingHistory(false);
      }
    }

    loadHistory();

    return () => {
      mounted = false;
    };
  }, [appliedFilters, page]);
  useEffect(() => {
    if (!appliedFilters) return;

    let mounted = true;

    async function loadChartHistory() {
      try {
        setLoadingChart(true);

        const metricCodes = appliedFilters.metricCode
          ? [appliedFilters.metricCode]
          : ["temperatura", "humedad"];

        const responses = await Promise.all(
          metricCodes.map((metricCode) =>
            getTelemetryHistory({
              ...appliedFilters,
              metricCode,
              limit: 100,
              offset: 0,
            }),
          ),
        );

        if (!mounted) return;

        const chartData = responses.flatMap((response) => response.items ?? []);
        setChartReadings(chartData);
      } catch (requestError) {
        if (!mounted) return;

        setChartReadings([]);
        setError(requestError.message);
      } finally {
        if (mounted) setLoadingChart(false);
      }
    }

    loadChartHistory();

    return () => {
      mounted = false;
    };
  }, [appliedFilters]);

  function updateFilter(field, value) {
    setFilters((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function submit(event) {
    event.preventDefault();
    setError("");

    if (!filters.deviceId) {
      setError("Selecciona un dispositivo.");
      return;
    }

    if (!filters.startAt || !filters.endAt) {
      setError("Selecciona una fecha inicial y una fecha final.");
      return;
    }

    const start = new Date(filters.startAt);
    const end = new Date(filters.endAt);

    if (start > end) {
      setError("La fecha inicial no puede ser posterior a la fecha final.");
      return;
    }

    setPage(0);
    setAppliedFilters({
      deviceId: filters.deviceId,
      metricCode: filters.metricCode,
      startAt: start.toISOString(),
      endAt: end.toISOString(),
    });
  }

  return (
    <section className="telemetry-history-page">
      <header className="telemetry-history-header">
        <div>
          <p className="telemetry-history-header__eyebrow">Monitoreo</p>
          <h1>Historial de lecturas</h1>
          <p>
            Consulta y analiza las métricas registradas por los dispositivos del
            laboratorio.
          </p>
        </div>
      </header>

      <form className="history-filter-card" onSubmit={submit}>
        <div className="history-filter-card__heading">
          <div>
            <h2>Filtros de consulta</h2>
            <p>
              Selecciona el dispositivo, la métrica y el período a analizar.
            </p>
          </div>

          <Search size={20} aria-hidden="true" />
        </div>

        <div className="history-filter-grid">
          <label>
            Dispositivo
            <select
              value={filters.deviceId}
              disabled={loadingDevices}
              onChange={(event) => updateFilter("deviceId", event.target.value)}
            >
              {devices.length === 0 && (
                <option value="">
                  {loadingDevices
                    ? "Cargando dispositivos..."
                    : "No hay dispositivos"}
                </option>
              )}

              {devices.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name} · {device.device_code}
                </option>
              ))}
            </select>
          </label>

          <label>
            Métrica
            <select
              value={filters.metricCode}
              onChange={(event) =>
                updateFilter("metricCode", event.target.value)
              }
            >
              <option value="">Todas las métricas</option>
              <option value="temperatura">Temperatura</option>
              <option value="humedad">Humedad</option>
            </select>
          </label>

          <label>
            Fecha inicial
            <div className="history-date-field">
              <CalendarDays size={16} aria-hidden="true" />
              <input
                type="datetime-local"
                value={filters.startAt}
                onChange={(event) =>
                  updateFilter("startAt", event.target.value)
                }
              />
            </div>
          </label>

          <label>
            Fecha final
            <div className="history-date-field">
              <CalendarDays size={16} aria-hidden="true" />
              <input
                type="datetime-local"
                value={filters.endAt}
                onChange={(event) => updateFilter("endAt", event.target.value)}
              />
            </div>
          </label>
        </div>

        <div className="history-filter-actions">
          <button
            type="submit"
            className="device-primary-btn"
            disabled={loadingDevices || devices.length === 0}
          >
            <Search size={16} />
            Consultar historial
          </button>
        </div>
      </form>

      {error && (
        <p className="device-form-error" role="alert">
          {error}
        </p>
      )}
      <div className="history-chart-card">
        <div className="history-chart-card__header">
          <div>
            <p className="telemetry-history-header__eyebrow">
              COMPORTAMIENTO HISTÓRICO
            </p>
            <h2>Lecturas en el período seleccionado</h2>
            <p>Evolución de las métricas registradas por el dispositivo.</p>
          </div>
        </div>

        {loadingChart ? (
          <div className="history-chart-empty">
            <p>Cargando gráfica...</p>
          </div>
        ) : chartReadings.length === 0 ? (
          <div className="history-chart-empty">
            <p>
              {appliedFilters
                ? "No hay lecturas disponibles para graficar en este período."
                : "Selecciona los filtros y consulta el historial para visualizar la gráfica."}
            </p>
          </div>
        ) : appliedFilters?.metricCode ? (
          <TelemetryHistoryChart
            readings={chartReadings}
            metricCode={appliedFilters.metricCode}
          />
        ) : (
          <div className="history-chart-groups">
            <div className="history-chart-group">
              <h3>Temperatura</h3>
              <TelemetryHistoryChart
                readings={chartReadings.filter(
                  (reading) => reading.metric_code === "temperatura",
                )}
                metricCode="temperatura"
              />
            </div>

            <div className="history-chart-group">
              <h3>Humedad</h3>
              <TelemetryHistoryChart
                readings={chartReadings.filter(
                  (reading) => reading.metric_code === "humedad",
                )}
                metricCode="humedad"
              />
            </div>
          </div>
        )}
      </div>
      <section className="history-results-card">
        <header className="history-results-card__header">
          <div>
            <h2>Lecturas registradas</h2>
            <p>
              {appliedFilters
                ? `${total} lectura${total === 1 ? "" : "s"} encontrada${total === 1 ? "" : "s"}`
                : "Aplica los filtros para consultar el historial."}
            </p>
          </div>
        </header>

        {loadingHistory ? (
          <div className="history-empty-state">
            <p>Cargando historial de lecturas...</p>
          </div>
        ) : !appliedFilters ? (
          <div className="history-empty-state">
            <Search size={28} />
            <p>Selecciona los filtros para comenzar.</p>
            <span>El historial del dispositivo aparecerá en esta sección.</span>
          </div>
        ) : readings.length === 0 ? (
          <div className="history-empty-state">
            <Search size={28} />
            <p>No se encontraron lecturas.</p>
            <span>Prueba con otro período, dispositivo o métrica.</span>
          </div>
        ) : (
          <>
            <div className="history-table-wrap">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Fecha y hora</th>
                    <th>Métrica</th>
                    <th>Valor</th>
                    <th>Unidad</th>
                    <th>Estado equipo</th>
                    <th>Fuente</th>
                  </tr>
                </thead>

                <tbody>
                  {readings.map((reading) => (
                    <tr key={reading.id}>
                      <td>{formatDate(reading.recorded_at)}</td>
                      <td className="history-metric">{reading.metric_code}</td>
                      <td>
                        <strong>{Number(reading.value).toFixed(2)}</strong>
                      </td>
                      <td>{reading.unit}</td>
                      <td>{reading.equipment_status ?? "Sin estado"}</td>
                      <td>{reading.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <footer className="history-pagination">
              <span>
                Mostrando {page * PAGE_SIZE + 1}–
                {Math.min((page + 1) * PAGE_SIZE, total)} de {total}
              </span>

              <div>
                <button
                  type="button"
                  disabled={page === 0 || loadingHistory}
                  onClick={() => setPage((current) => Math.max(0, current - 1))}
                >
                  Anterior
                </button>

                <span>
                  {page + 1} / {totalPages}
                </span>

                <button
                  type="button"
                  disabled={page + 1 >= totalPages || loadingHistory}
                  onClick={() => setPage((current) => current + 1)}
                >
                  Siguiente
                </button>
              </div>
            </footer>
          </>
        )}
      </section>
    </section>
  );
}
