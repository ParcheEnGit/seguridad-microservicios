import React, { useState } from "react";
import { Sidebar } from "./Sidebar.jsx";
import { Topbar } from "./Topbar.jsx";

export function DashboardLayout({
  user,
  activeItem,
  onNavigate,
  onLogout,
  children,
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  function navigate(item) {
    onNavigate(item);
    setMobileMenuOpen(false);
  }

  return (
    <div className="dashboard-shell">
      {mobileMenuOpen && (
        <button
          type="button"
          className="dashboard-menu-backdrop"
          aria-label="Cerrar menú"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}
      <Sidebar
        user={user}
        activeItem={activeItem}
        onNavigate={navigate}
        onLogout={onLogout}
        isMobileOpen={mobileMenuOpen}
        onCloseMobileMenu={() => setMobileMenuOpen(false)}
      />

      <div className="dashboard-main">
        <Topbar
          isMobileMenuOpen={mobileMenuOpen}
          onToggleMobileMenu={() => setMobileMenuOpen((current) => !current)}
        />
        <main className="dashboard-content">{children}</main>
      </div>
    </div>
  );
}
