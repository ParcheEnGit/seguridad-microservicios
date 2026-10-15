import React, { useEffect, useState } from "react";
import { Bell, Menu, Search, Shield, X } from "lucide-react";
import { fetchAlerts } from "../../services/dashboardApi.js";

export function Topbar({ isMobileMenuOpen, onToggleMobileMenu, onOpenNotifications }) {
  const [notificationCount, setNotificationCount] = useState(0);

  useEffect(() => {
    let mounted = true;
    const loadNotifications = async () => {
      try {
        const alerts = await fetchAlerts();
        if (mounted) setNotificationCount(Array.isArray(alerts) ? alerts.length : alerts.items?.length ?? 0);
      } catch {
        if (mounted) setNotificationCount(0);
      }
    };
    loadNotifications();
    const timer = setInterval(loadNotifications, 15_000);
    return () => { mounted = false; clearInterval(timer); };
  }, []);

  return (
    <header className="dashboard-topbar">
      <button
        type="button"
        className="dashboard-menu-btn"
        onClick={onToggleMobileMenu}
        aria-label={isMobileMenuOpen ? "Cerrar menú" : "Abrir menú"}
        aria-expanded={isMobileMenuOpen}
      >
        {isMobileMenuOpen ? <X size={21} /> : <Menu size={21} />}
      </button>
      <div className="dashboard-mobile-brand" aria-hidden="true">
        <Shield size={17} />
        <strong>LabSentinel</strong>
      </div>
      <label className="dashboard-search" htmlFor="dashboard-search-input">
        <Search size={18} aria-hidden="true" />
        <input
          id="dashboard-search-input"
          type="search"
          placeholder="Buscar dispositivo o alerta..."
          disabled
        />
      </label>

      <div className="dashboard-topbar__actions">
        <div className="dashboard-status">
          <span className="dashboard-status__dot" aria-hidden="true" />
          Conectado
        </div>

        <button type="button" className="dashboard-icon-btn" aria-label={`Notificaciones${notificationCount ? `: ${notificationCount} activas` : ""}`} onClick={onOpenNotifications}>
          <Bell size={18} />
          {notificationCount > 0 && <span className="dashboard-icon-btn__badge">{notificationCount > 99 ? "99+" : notificationCount}</span>}
        </button>
      </div>
    </header>
  );
}
