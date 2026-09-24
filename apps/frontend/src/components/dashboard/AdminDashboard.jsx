import React, { useCallback, useEffect, useState } from "react";
import { BarChart3, Bell, ChevronRight, Plus, RefreshCw, ShieldAlert } from "lucide-react";
import { getAdminSummary } from "../../services/reportApi.js";
import { LineChart24h, SERIES } from "./LineChart24h.jsx";

const REFRESH_MS = 60 * 1000;

const METRIC_NAMES = { temperatura: "Temperatura", humedad: "Humedad" };

const formatTime = (value) =>
  new Date(value).toLocaleTimeString("es-BO", { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });

const formatNumber = (value) => Number(value).toLocaleString("es-BO", { maximumFractionDigits: 1 });

// Genera el texto de la alerta, por ejemplo "Temperatura elevada (28.5°C)".
export function describeAlert(alert) {
  const value = Number(alert.value);
  const reading = `${formatNumber(value)}${alert.unit}`;
  const name = METRIC_NAMES[alert.metric_code] ?? alert.metric_code;
  if (alert.metric_code === "humedad") return `Humedad fuera de rango (${reading})`;
  if (alert.threshold_max !== null && value > Number(alert.threshold_max)) return `${name} elevada (${reading})`;
  if (alert.threshold_min !== null && value < Number(alert.threshold_min)) return `${name} baja (${reading})`;
  return `${name} fuera de umbral (${reading})`;
}

function errorMessage(error) {
  if (error.status === 403) return "Acceso denegado: esta vista es exclusiva para administradores.";
  if (error.status === 401) return "Tu sesión expiró, vuelve a iniciar sesión.";
  return error.message;
}

function StatCard({ label, value, hint, tone }) {
  return (
    <article className="dashboard-card admin-stat">
      <p className="admin-stat__label">{label}</p>
      <div className="admin-stat__row">
        <strong className={`admin-stat__value admin-stat__value--${tone}`}>{value}</strong>
        <span className="admin-stat__hint">{hint}</span>
      </div>
    </article>
  );
}

function StatSkeleton() {
  return (
    <article className="dashboard-card admin-stat" aria-hidden="true">
      <span className="admin-skeleton admin-skeleton--label" />
      <span className="admin-skeleton admin-skeleton--value" />
    </article>
  );
}

function EmptyState({ icon: Icon, text }) {
  return (
    <div className="admin-empty">
      <Icon size={26} aria-hidden="true" />
      <p>{text}</p>
    </div>
  );
}

export function AdminDashboard({ onNavigate }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setSummary(await getAdminSummary());
      setError(null);
    } catch (requestError) {
      setError(requestError);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => clearInterval(timer);
  }, [load]);

  if (error && !summary) {
    return (
      <section className="admin-dashboard">
        <div className="dashboard-card admin-error" role="alert">
          <ShieldAlert size={22} aria-hidden="true" />
          <p>{errorMessage(error)}</p>
          {error.status !== 403 && (
            <button type="button" className="device-secondary-btn" onClick={load}>
              <RefreshCw size={16} aria-hidden="true" /> Reintentar
            </button>
          )}
        </div>
      </section>
    );
  }

  const stats = summary && buildStats(summary);

  return (
    <section className="admin-dashboard" aria-busy={loading}>
      {error && <p className="device-form-error" role="alert">{errorMessage(error)} Mostrando los últimos datos cargados.</p>}

      <section className="dashboard-grid dashboard-grid--stats" aria-label="Indicadores">
        {stats ? stats.map((stat) => <StatCard key={stat.label} {...stat} />) : [0, 1, 2, 3].map((i) => <StatSkeleton key={i} />)}
      </section>

      <section className="dashboard-grid dashboard-grid--main">
        <article className="dashboard-card admin-chart-card">
          <header className="admin-card-header">
            <h2 className="dashboard-card__title">Temperatura y Humedad — Últimas 24h</h2>
            <ul className="admin-legend">
              {SERIES.map((serie) => (
                <li key={serie.key}><span style={{ background: serie.color }} aria-hidden="true" />{serie.label}</li>
              ))}
            </ul>
          </header>
          {!summary ? (
            <p className="device-muted">Cargando lecturas...</p>
          ) : summary.chart_24h.length === 0 ? (
            <EmptyState icon={BarChart3} text="Aún no hay lecturas en las últimas 24 horas." />
          ) : (
            <LineChart24h points={summary.chart_24h} />
          )}
        </article>

        <div className="dashboard-side-stack">
          <article className="dashboard-card admin-alerts-card">
            <header className="admin-card-header">
              <h2 className="dashboard-card__title">Alertas recientes</h2>
              <button type="button" className="device-link-btn" onClick={() => onNavigate("alertas")}>Ver todo</button>
            </header>
            {!summary ? (
              <p className="device-muted">Cargando alertas...</p>
            ) : summary.recent_alerts.length === 0 ? (
              <EmptyState icon={Bell} text="No hay alertas activas." />
            ) : (
              <ul className="admin-alert-list">
                {summary.recent_alerts.map((alert) => (
                  <li key={alert.id}>
                    <button type="button" className="admin-alert-item" onClick={() => onNavigate("alertas")}>
                      <span className={`admin-alert-dot admin-alert-dot--${alert.severity}`} title={alert.severity} />
                      <span className="admin-alert-text">
                        <strong>{alert.device_name ?? "Dispositivo desconocido"}</strong>
                        <small>{describeAlert(alert)}</small>
                      </span>
                      <time dateTime={alert.created_at}>{formatTime(alert.created_at)}</time>
                      <ChevronRight size={16} aria-hidden="true" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </article>

          <button type="button" className="admin-register-btn" onClick={() => onNavigate("dispositivos")}>
            <Plus size={18} aria-hidden="true" /> Registrar dispositivo
          </button>
        </div>
      </section>
    </section>
  );
}

function buildStats({ devices, alerts, tickets, readings }) {
  const capacity = devices.total > 0 ? Math.round((devices.activo / devices.total) * 100) : null;
  return [
    {
      label: "Dispositivos activos",
      value: `${devices.activo}/${devices.total}`,
      hint: capacity === null ? "Sin dispositivos" : `${capacity}% de capacidad`,
      tone: "green",
    },
    {
      label: "Alertas activas",
      value: alerts.active,
      hint: alerts.pending_review > 0 ? "Requieren revisión" : "Todo en orden",
      tone: "amber",
    },
    {
      label: "Tickets abiertos",
      value: tickets.open,
      hint: tickets.created_today === 1 ? "1 creado hoy" : `${tickets.created_today} creados hoy`,
      tone: "blue",
    },
    {
      label: "Lecturas hoy",
      value: readings.today.toLocaleString("es-BO"),
      hint: readings.last_received_at ? `Sincronizado ${formatTime(readings.last_received_at)}` : "Sin lecturas",
      tone: "dark",
    },
  ];
}
