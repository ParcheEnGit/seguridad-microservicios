import React from "react";
import { Bell, Menu, Search, Shield, X } from "lucide-react";

export function Topbar({ isMobileMenuOpen, onToggleMobileMenu }) {
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

        <button type="button" className="dashboard-icon-btn" aria-label="Notificaciones">
          <Bell size={18} />
          <span className="dashboard-icon-btn__badge">3</span>
        </button>
      </div>
    </header>
  );
}
