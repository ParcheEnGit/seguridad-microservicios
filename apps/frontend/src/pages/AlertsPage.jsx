import React, { useEffect, useState } from "react";
import {
  AlertTriangle,
  Check,
  Clock3,
  Eye,
  RefreshCw,
  ShieldAlert,
  X,
} from "lucide-react";
import { isAdmin } from "../constants/roles.js";
import {
  fetchAlertDetail,
  fetchManagedAlerts,
  setAlertStatus,
} from "../services/alertsApi.js";
import { listDevices } from "../services/deviceApi.js";
import "./alerts.css";

const STATUS_LABELS = {
  abierta: "Pendiente",
  revisada: "En atención",
  cerrada: "Cerrada",
};

const SEVERITY_LABELS = {
  critica: "Crítica",
  advertencia: "Advertencia",
};

const METRIC_LABELS = {
  temperatura: "Temperatura",
  humedad: "Humedad",
};

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString("es-BO", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/La_Paz",
  });
}

function formatValue(value, unit = "") {
  if (value === null || value === undefined) return "—";
  const number = Number(value);
  const formatted = Number.isFinite(number)
    ? number.toLocaleString("es-BO", { maximumFractionDigits: 2 })
    : value;
  return `${formatted}${unit ? ` ${unit}` : ""}`;
}

function thresholdDescription(alert) {
  const value = Number(alert.value);
  if (alert.threshold_max !== null && value > Number(alert.threshold_max)) {
    return `Sobre el máximo (${formatValue(alert.threshold_max, alert.unit)})`;
  }
  if (alert.threshold_min !== null && value < Number(alert.threshold_min)) {
    return `Bajo el mínimo (${formatValue(alert.threshold_min, alert.unit)})`;
  }
  return `${formatValue(alert.threshold_min, alert.unit)} – ${formatValue(alert.threshold_max, alert.unit)}`;
}

function requestMessage(error) {
  if (error.status === 401) return "Tu sesión expiró. Inicia sesión nuevamente.";
  if (error.status === 403) return "No tienes permisos para realizar esta acción.";
  return error.message || "No se pudo completar la solicitud.";
}

function AlertDetailDialog({ alertId, onClose }) {
  const [alert, setAlert] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    fetchAlertDetail(alertId)
      .then((data) => {
        if (mounted) setAlert(data);
      })
      .catch((requestError) => {
        if (mounted) setError(requestMessage(requestError));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [alertId]);

  return (
    <div
      className="alerts-dialog-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        className="alerts-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="alert-detail-title"
      >
        <header className="alerts-dialog__header">
          <div>
            <p className="alerts-eyebrow">Registro de monitoreo</p>
            <h2 id="alert-detail-title">Detalle de alerta</h2>
          </div>
          <button type="button" className="alerts-icon-button" onClick={onClose} aria-label="Cerrar detalle">
            <X size={19} />
          </button>
        </header>
        <div className="alerts-dialog__body" aria-busy={loading}>
          {loading && <p className="alerts-muted">Cargando detalle...</p>}
          {error && <p className="alerts-error" role="alert">{error}</p>}
          {alert && !loading && (
            <>
              <section className="alerts-detail-block">
                <h3>Alerta</h3>
                <dl className="alerts-detail-grid">
                  <div><dt>Dispositivo</dt><dd>{alert.device_name ?? "Desconocido"}{alert.device_code ? ` · ${alert.device_code}` : ""}</dd></div>
                  <div><dt>Métrica</dt><dd>{METRIC_LABELS[alert.metric_code] ?? alert.metric_code}</dd></div>
                  <div><dt>Valor registrado</dt><dd>{formatValue(alert.value, alert.unit)}</dd></div>
                  <div><dt>Condición</dt><dd>{thresholdDescription(alert)}</dd></div>
                  <div><dt>Umbral mínimo</dt><dd>{formatValue(alert.threshold_min, alert.unit)}</dd></div>
                  <div><dt>Umbral máximo</dt><dd>{formatValue(alert.threshold_max, alert.unit)}</dd></div>
                  <div><dt>Severidad</dt><dd><span className={`alert-badge alert-badge--${alert.severity}`}>{SEVERITY_LABELS[alert.severity] ?? alert.severity}</span></dd></div>
                  <div><dt>Estado</dt><dd><span className={`alert-badge alert-badge--${alert.status}`}>{STATUS_LABELS[alert.status] ?? alert.status}</span></dd></div>
                  <div><dt>Generada</dt><dd>{formatDate(alert.created_at)}</dd></div>
                </dl>
              </section>
              <section className="alerts-detail-block">
                <h3>Lectura que generó la alerta</h3>
                <dl className="alerts-detail-grid">
                  <div><dt>Fecha de registro</dt><dd>{formatDate(alert.reading.recorded_at)}</dd></div>
                  <div><dt>Fecha de recepción</dt><dd>{formatDate(alert.reading.received_at)}</dd></div>
                  <div><dt>Valor</dt><dd>{formatValue(alert.reading.value, alert.reading.unit)}</dd></div>
                  <div><dt>Origen</dt><dd>{alert.reading.source}</dd></div>
                  <div><dt>Estado del equipo</dt><dd>{alert.reading.equipment_status ?? "No informado"}</dd></div>
                </dl>
                {Object.keys(alert.reading.payload ?? {}).length > 0 && (
                  <details className="alerts-payload">
                    <summary>Datos adicionales de la lectura</summary>
                    <pre>{JSON.stringify(alert.reading.payload, null, 2)}</pre>
                  </details>
                )}
              </section>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

export function AlertsPage({ user }) {
  const admin = isAdmin(user.role);
  const [alerts, setAlerts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [filters, setFilters] = useState({ device_id: "", severity: "", status: "active" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [devicesError, setDevicesError] = useState("");
  const [actionError, setActionError] = useState("");
  const [notice, setNotice] = useState("");
  const [savingAlertId, setSavingAlertId] = useState("");
  const [detailAlertId, setDetailAlertId] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let mounted = true;
    listDevices()
      .then((result) => {
        if (mounted) setDevices(result.items ?? []);
      })
      .catch((requestError) => {
        if (mounted) setDevicesError(requestMessage(requestError));
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError("");
    fetchManagedAlerts(filters)
      .then((result) => {
        if (mounted) setAlerts(Array.isArray(result) ? result : []);
      })
      .catch((requestError) => {
        if (mounted) setError(requestMessage(requestError));
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [filters, refreshKey]);

  function updateFilter(name, value) {
    setFilters((current) => ({ ...current, [name]: value }));
    setActionError("");
    setNotice("");
  }

  async function changeStatus(alert, nextStatus) {
    setSavingAlertId(alert.id);
    setActionError("");
    setNotice("");
    try {
      await setAlertStatus(alert.id, nextStatus);
      setNotice(`Alerta actualizada: ${STATUS_LABELS[nextStatus]}.`);
      setRefreshKey((key) => key + 1);
    } catch (requestError) {
      setActionError(requestMessage(requestError));
    } finally {
      setSavingAlertId("");
    }
  }

  const openCount = alerts.filter((alert) => alert.status === "abierta").length;
  const reviewCount = alerts.filter((alert) => alert.status === "revisada").length;
  const criticalCount = alerts.filter((alert) => alert.severity === "critica").length;

  return (
    <section className="alerts-page">
      <header className="alerts-page__header">
        <div>
          <p className="alerts-eyebrow">Monitoreo del laboratorio</p>
          <h1>Gestión de alertas</h1>
          <p>Consulta anomalías detectadas al comparar las lecturas con los umbrales configurados.</p>
        </div>
        <button
          type="button"
          className="alerts-refresh-button"
          onClick={() => setRefreshKey((key) => key + 1)}
          disabled={loading}
        >
          <RefreshCw size={17} aria-hidden="true" />
          Actualizar
        </button>
      </header>

      <div className="alerts-summary-grid" aria-label="Resumen de alertas">
        <article className="alerts-summary-card">
          <span className="alerts-summary-card__icon alerts-summary-card__icon--red"><AlertTriangle size={19} /></span>
          <div><span>Pendientes</span><strong>{loading ? "…" : openCount}</strong></div>
        </article>
        <article className="alerts-summary-card">
          <span className="alerts-summary-card__icon alerts-summary-card__icon--amber"><Clock3 size={19} /></span>
          <div><span>En atención</span><strong>{loading ? "…" : reviewCount}</strong></div>
        </article>
        <article className="alerts-summary-card">
          <span className="alerts-summary-card__icon alerts-summary-card__icon--purple"><ShieldAlert size={19} /></span>
          <div><span>Críticas</span><strong>{loading ? "…" : criticalCount}</strong></div>
        </article>
      </div>

      <section className="alerts-panel">
        <div className="alerts-panel__header">
          <div><h2>Alertas registradas</h2><p>Abiertas y revisadas permanecen activas hasta su cierre.</p></div>
        </div>
        <div className="alerts-filters">
          <label>
            <span>Dispositivo</span>
            <select value={filters.device_id} onChange={(event) => updateFilter("device_id", event.target.value)}>
              <option value="">Todos los dispositivos</option>
              {devices.map((device) => (
                <option key={device.id} value={device.id}>{device.name} · {device.device_code}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Severidad</span>
            <select value={filters.severity} onChange={(event) => updateFilter("severity", event.target.value)}>
              <option value="">Todas</option>
              <option value="advertencia">Advertencia</option>
              <option value="critica">Crítica</option>
            </select>
          </label>
          <label>
            <span>Estado</span>
            <select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
              <option value="active">Activas</option>
              <option value="abierta">Pendientes</option>
              <option value="revisada">En atención</option>
              <option value="cerrada">Cerradas</option>
              <option value="all">Todas</option>
            </select>
          </label>
        </div>

        {devicesError && <p className="alerts-warning" role="status">{devicesError}</p>}
        {error && <p className="alerts-error" role="alert">{error}</p>}
        {actionError && <p className="alerts-error" role="alert">{actionError}</p>}
        {notice && <p className="alerts-notice" role="status">{notice}</p>}

        {loading ? (
          <p className="alerts-state">Cargando alertas…</p>
        ) : error ? null : alerts.length === 0 ? (
          <p className="alerts-state">No hay alertas que coincidan con estos filtros.</p>
        ) : (
          <div className="alerts-table-wrap">
            <table className="alerts-table">
              <thead>
                <tr>
                  <th>Dispositivo</th><th>Métrica</th><th>Lectura / umbral</th>
                  <th>Severidad</th><th>Estado</th><th>Fecha</th><th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td><strong>{alert.device_name ?? "Desconocido"}</strong><small>{alert.device_code ?? "—"}</small></td>
                    <td>{METRIC_LABELS[alert.metric_code] ?? alert.metric_code}</td>
                    <td><strong>{formatValue(alert.value, alert.unit)}</strong><small>{thresholdDescription(alert)}</small></td>
                    <td><span className={`alert-badge alert-badge--${alert.severity}`}>{SEVERITY_LABELS[alert.severity] ?? alert.severity}</span></td>
                    <td><span className={`alert-badge alert-badge--${alert.status}`}>{STATUS_LABELS[alert.status] ?? alert.status}</span></td>
                    <td>{formatDate(alert.created_at)}</td>
                    <td>
                      <div className="alerts-row-actions">
                        <button type="button" className="alerts-icon-button" onClick={() => setDetailAlertId(alert.id)} aria-label="Ver detalle">
                          <Eye size={17} />
                        </button>
                        {admin && alert.status === "abierta" && (
                          <button
                            type="button"
                            className="alerts-action-button"
                            onClick={() => changeStatus(alert, "revisada")}
                            disabled={savingAlertId === alert.id}
                          >
                            <Clock3 size={15} /> Revisar
                          </button>
                        )}
                        {admin && alert.status === "revisada" && (
                          <button
                            type="button"
                            className="alerts-action-button alerts-action-button--close"
                            onClick={() => changeStatus(alert, "cerrada")}
                            disabled={savingAlertId === alert.id}
                          >
                            <Check size={15} /> Cerrar
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      {detailAlertId && <AlertDetailDialog alertId={detailAlertId} onClose={() => setDetailAlertId("")} />}
    </section>
  );
}
