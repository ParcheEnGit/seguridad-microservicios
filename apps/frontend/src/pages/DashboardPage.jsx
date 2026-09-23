import React, { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { PlaceholderCard } from "../components/dashboard/PlaceholderCard.jsx";
import { DashboardLayout } from "../components/layout/DashboardLayout.jsx";
import { canRegisterDevice, isAdmin } from "../constants/roles.js";
import { fetchAlerts, fetchDevices } from "../services/dashboardApi.js";
import { SummaryCard } from "../components/reader/SummaryCard.jsx";
import { DeviceTable } from "../components/reader/DeviceTable.jsx";
import { RecentAlerts } from "../components/reader/RecentAlerts.jsx";

const STAT_CARDS = [
  "Dispositivos activos",
  "Alertas activas",
  "Tickets abiertos",
  "Lecturas hoy",
];

export function DashboardPage({ user, onLogout }) {
  const [activeItem, setActiveItem] = useState("home");
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

        const [deviceData, alertData] = await Promise.all([
          fetchDevices(),
          fetchAlerts(),
        ]);

        if (isMounted) {
          setDevices(deviceData);
          setAlerts(alertData);
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

  return (
    <DashboardLayout
      user={user}
      activeItem={activeItem}
      onNavigate={setActiveItem}
      onLogout={onLogout}
    >
      <section
        className="dashboard-grid dashboard-grid--stats"
        aria-label="Resumen"
      >
        {STAT_CARDS.map((title) => (
          <PlaceholderCard key={title} title={title} />
        ))}
      </section>

      <section
        className="dashboard-grid dashboard-grid--main"
        aria-label="Contenido principal"
      >
        <PlaceholderCard title="Temperatura y humedad — Últimas 24h" />

        <div className="dashboard-side-stack">
          <PlaceholderCard title="Alertas recientes" />

          {canRegisterDevice(user.role) && (
            <button type="button" className="dashboard-outline-btn" disabled>
              <Plus size={18} aria-hidden="true" />
              Registrar dispositivo
            </button>
          )}
        </div>
      </section>

      {!isAdmin(user.role) && (
        <p className="dashboard-role-note">
          Vista de usuario. Algunas opciones del menú estarán disponibles en
          próximas iteraciones.
        </p>
      )}
    </DashboardLayout>
  );
}
