import React from "react";
import { Bell, Search } from "lucide-react";

export function Topbar() {
  return (
    <header className="dashboard-topbar">
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

        <button type="button" className="dashboard-icon-btn" aria-label="Notificaciones">
          <Bell size={18} />
          <span className="dashboard-icon-btn__badge">3</span>
        </button>
      </div>
    </header>
  );
}
