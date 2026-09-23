import React, { useEffect, useState } from "react";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { DashboardPage } from "../pages/DashboardPage.jsx";
import { LoginPage } from "../pages/LoginPage.jsx";
import { fetchCurrentUser, logout } from "../services/authApi.js";

const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function AppContent() {
  const [user, setUser] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadSession() {
      try {
        const currentUser = await fetchCurrentUser();
        if (isMounted && currentUser) {
          setUser(currentUser);
        }
      } catch {
      } finally {
        if (isMounted) {
          setIsCheckingSession(false);
        }
      }
    }

    loadSession();
    return () => {
      isMounted = false;
    };
  }, []);

  async function handleLogout() {
    try {
      await logout();
    } finally {
      setUser(null);
    }
  }

  if (isCheckingSession) {
    return (
      <main className="auth-page">
        <section className="auth-card">
          <p className="auth-subtitle">Cargando...</p>
        </section>
      </main>
    );
  }

  if (user) {
    return <DashboardPage user={user} onLogout={handleLogout} />;
  }

  return (
    <LoginPage
      onLoginSuccess={setUser}
    />
  );
}

export function App() {
  if (!googleClientId) {
    return (
      <main className="auth-page">
        <section className="auth-card">
          <h1 className="auth-title">Configuración requerida</h1>
          <p className="auth-subtitle">
            Configura <code>VITE_GOOGLE_CLIENT_ID</code> en el archivo <code>.env</code>
            para habilitar el inicio de sesión con Google.
          </p>
        </section>
      </main>
    );
  }

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <AppContent />
    </GoogleOAuthProvider>
  );
}
