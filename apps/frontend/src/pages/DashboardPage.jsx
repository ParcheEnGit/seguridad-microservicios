import React, { useEffect, useState } from "react";
import {
  Bell,
  Database,
  Monitor,
  TrendingUp,
} from "lucide-react";

import { AdminDashboard } from "../components/dashboard/AdminDashboard.jsx";
import { DashboardLayout } from "../components/layout/DashboardLayout.jsx";
import { DeviceTable } from "../components/reader/DeviceTable.jsx";
import { RecentAlerts } from "../components/reader/RecentAlerts.jsx";
import { SummaryCard } from "../components/reader/SummaryCard.jsx";
import { isAdmin } from "../constants/roles.js";
import { fetchAlerts } from "../services/dashboardApi.js";
import { listDevices } from "../services/deviceApi.js";
import { DevicesPage } from "./DevicesPage.jsx";

export function DashboardPage({ user, onLogout }) {
  const [activeItem, setActiveItem] = useState("inicio");
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function loadDashboardData() {
      try {
        setIsLoading(true);
        setError(null);

        const [deviceResult, alertResult] = await Promise.allSettled([
          listDevices(),
          fetchAlerts(),
        ]);

        if (isMounted) {
          if (deviceResult.status === "fulfilled") {
            setDevices(deviceResult.value.items ?? []);
          } else {
            throw deviceResult.reason;
          }

          if (alertResult.status === "fulfilled") {
            const alertData = alertResult.value;

            setAlerts(
              Array.isArray(alertData) ? alertData : (alertData.items ?? []),
            );
          } else {
            setAlerts([]);
          }
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadDashboardData();

    return () => {
      isMounted = false;
    };
  }, []);

  const activeDevices = devices.filter(
    (device) => device.status === "activo",
  ).length;

  const activeAlerts = alerts.filter(
    (alert) => alert.status !== "resuelta",
  ).length;

  return (
    <DashboardLayout
      user={user}
      activeItem={activeItem}
      onNavigate={setActiveItem}
      onLogout={onLogout}
    >
      {activeItem === "dispositivos" ? (
        <DevicesPage user={user} />
      ) : activeItem === "inicio" && isAdmin(user.role) ? (
        <AdminDashboard onNavigate={setActiveItem} />
      ) : (
        <div className="reader-dashboard">
          <header className="reader-dashboard__header">
            <p className="reader-dashboard__eyebrow">
              Dashboard Lector
            </p>

            <h1>Resumen general</h1>

            <p className="reader-dashboard__subtitle">
              Estado general de los dispositivos y eventos del laboratorio.
            </p>
          </header>

          <section
            className="dashboard-grid dashboard-grid--stats"
            aria-label="Resumen del laboratorio"
          >
            <SummaryCard
              title="Dispositivos activos"
              value={isLoading ? "..." : activeDevices}
              description="Dispositivos disponibles para monitoreo"
              icon={Monitor}
              variant="green"
            />

            <SummaryCard
              title="Alertas activas"
              value={isLoading ? "..." : activeAlerts}
              description="Alertas que requieren seguimiento"
              icon={Bell}
              variant="red"
            />

            <SummaryCard
              title="Total dispositivos"
              value={isLoading ? "..." : devices.length}
              description="Dispositivos registrados"
              icon={Database}
              variant="blue"
            />

            <SummaryCard
              title="Alertas recientes"
              value={isLoading ? "..." : alerts.length}
              description="Alertas disponibles para consulta"
              icon={TrendingUp}
              variant="purple"
            />
          </section>

          {isLoading && (
            <section className="reader-state" aria-live="polite">
              <p>Cargando información del dashboard...</p>
            </section>
          )}

          {error && (
            <section
              className="reader-state reader-state--error"
              role="alert"
            >
              <p>No se pudo cargar el dashboard: {error}</p>
            </section>
          )}

          {!isLoading && !error && (
            <section
              className="dashboard-grid dashboard-grid--main"
              aria-label="Información de monitoreo"
            >
              <div className="reader-panel">
                <div className="reader-panel__header">
                  <div>
                    <h2>Dispositivos monitoreados</h2>
                    <p>
                      Estado actual de los dispositivos del laboratorio.
                    </p>
                  </div>

                  <button
                    type="button"
                    className="reader-panel__link"
                    onClick={() => setActiveItem("dispositivos")}
                  >
                    Ver todos
                    <span aria-hidden="true">→</span>
                  </button>
                </div>

                <DeviceTable devices={devices} />
              </div>

              <div className="reader-panel">
                <div className="reader-panel__header">
                  <div>
                    <h2>Alertas recientes</h2>
                    <p>
                      Últimos eventos detectados en el laboratorio.
                    </p>
                  </div>
                </div>

                <RecentAlerts alerts={alerts} />
              </div>
            </section>
          )}

          {!isAdmin(user.role) && (
            <div className="reader-role-banner">
              <span
                className="reader-role-banner__icon"
                aria-hidden="true"
              >
                i
              </span>

              <p>
                <strong>Dashboard Lector.</strong>{" "}
                Puedes consultar información autorizada y registrar tickets;
                la gestión administrativa está restringida.
              </p>
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  );
}