import React, { useState } from "react";
import { Plus } from "lucide-react";
import { PlaceholderCard } from "../components/dashboard/PlaceholderCard.jsx";
import { DashboardLayout } from "../components/layout/DashboardLayout.jsx";
import { canRegisterDevice, isAdmin } from "../constants/roles.js";
import { DevicesPage } from "./DevicesPage.jsx";
import { AdminDashboard } from "../components/dashboard/AdminDashboard.jsx";

const STAT_CARDS = [
  "Dispositivos activos",
  "Alertas activas",
  "Tickets abiertos",
  "Lecturas hoy",
];

export function DashboardPage({ user, onLogout }) {
  const [activeItem, setActiveItem] = useState("inicio");

  return (
    <DashboardLayout
      user={user}
      activeItem={activeItem}
      onNavigate={setActiveItem}
      onLogout={onLogout}
    >
      {activeItem === "dispositivos" ? <DevicesPage user={user} /> : activeItem === "inicio" && isAdmin(user.role) ? <AdminDashboard onNavigate={setActiveItem} /> : <>
      <section className="dashboard-grid dashboard-grid--stats" aria-label="Resumen">
        {STAT_CARDS.map((title) => (
          <PlaceholderCard key={title} title={title} />
        ))}
      </section>

      <section className="dashboard-grid dashboard-grid--main" aria-label="Contenido principal">
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
          Dashboard Lector. Puedes consultar información autorizada y registrar tickets; la gestión administrativa está restringida.
        </p>
      )}
      </>}
    </DashboardLayout>
  );
}
