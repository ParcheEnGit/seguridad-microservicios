import React from "react";
import { Sidebar } from "./Sidebar.jsx";
import { Topbar } from "./Topbar.jsx";

export function DashboardLayout({
  user,
  activeItem,
  onNavigate,
  onLogout,
  children,
}) {
  return (
    <div className="dashboard-shell">
      <Sidebar
        user={user}
        activeItem={activeItem}
        onNavigate={onNavigate}
        onLogout={onLogout}
      />

      <div className="dashboard-main">
        <Topbar />
        <main className="dashboard-content">{children}</main>
      </div>
    </div>
  );
}
