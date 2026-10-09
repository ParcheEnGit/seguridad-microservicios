import React from "react";
import { Shield, X } from "lucide-react";
import { getNavItemsForRole } from "../../constants/navigation.js";
import { UserAvatar } from "../common/UserAvatar.jsx";
import { getRoleLabelForDisplay } from "../../utils/userDisplay.js";

export function Sidebar({ user, activeItem, onNavigate, onLogout, isMobileOpen, onCloseMobileMenu }) {
  const navItems = getNavItemsForRole(user.role);

  return (
    <aside className={`dashboard-sidebar${isMobileOpen ? " dashboard-sidebar--mobile-open" : ""}`} aria-label="Navegación principal">
      <div className="dashboard-sidebar__brand">
        <div className="dashboard-sidebar__logo" aria-hidden="true">
          <Shield size={18} strokeWidth={2.2} />
        </div>
        <span>LabSentinel</span>
        <button type="button" className="dashboard-sidebar__close" onClick={onCloseMobileMenu} aria-label="Cerrar menú">
          <X size={20} />
        </button>
      </div>

      <nav className="dashboard-sidebar__nav">
        {navItems.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            className={`dashboard-nav-item${activeItem === id ? " dashboard-nav-item--active" : ""}`}
            onClick={() => onNavigate(id)}
          >
            <Icon size={18} aria-hidden="true" />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="dashboard-sidebar__footer">
        <div className="dashboard-user-chip">
          <UserAvatar user={user} />
          <div className="dashboard-user-chip__meta">
            <strong>{user.name}</strong>
            <span>{getRoleLabelForDisplay(user.role)}</span>
          </div>
        </div>
        <button type="button" className="dashboard-logout-btn" onClick={onLogout}>
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
