import React from "react";
import { Shield } from "lucide-react";

export function DashboardPage({ user, onLogout }) {
  return (
    <main className="auth-page">
      <section className="auth-card dashboard-card" aria-labelledby="dashboard-title">
        <div className="auth-brand" aria-hidden="true">
          <div className="auth-brand-icon">
            <Shield size={22} strokeWidth={2.2} />
          </div>
        </div>

        <h1 id="dashboard-title" className="auth-title">
          Welcome, {user.name}
        </h1>
        <p className="auth-subtitle">{user.email}</p>

        <div className="auth-session-badge">You are signed in to LabSentinel</div>

        <button type="button" className="auth-submit" onClick={onLogout}>
          Sign out
        </button>
      </section>
    </main>
  );
}
