import React, { useEffect, useState } from "react";
import { KeyRound, Mail } from "lucide-react";
import logoUrl from "../assets/labsentinel-mark.svg";
import { GoogleSignInButton } from "../components/GoogleSignInButton.jsx";
import { loginWithPassword } from "../services/authApi.js";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
const keycloakEnabled = import.meta.env.VITE_KEYCLOAK_ENABLED === "true";
const googleEnabled = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID);

const INSTITUTIONAL_EMAIL_PATTERN =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    const url = new URL(window.location.href);
    const error = url.searchParams.get("auth_error");
    if (!error) return;
    setAuthError(error);
    url.searchParams.delete("auth_error");
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  }, []);

  const emailInvalid =
    (emailTouched || submitAttempted) &&
    email.length > 0 &&
    !INSTITUTIONAL_EMAIL_PATTERN.test(email);
  const showEmailError = emailInvalid || (submitAttempted && email.length === 0);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitAttempted(true);
    setAuthError("");

    if (!email || !INSTITUTIONAL_EMAIL_PATTERN.test(email) || !password) {
      return;
    }

    try {
      const data = await loginWithPassword(email, password);
      onLoginSuccess(data.user);
    } catch (error) {
      setAuthError(error.message ?? "No se pudo iniciar sesión.");
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <div className="auth-brand" aria-hidden="true">
          <div className="auth-brand-icon">
            <img src={logoUrl} alt="" />
          </div>
        </div>

        <h1 id="login-title" className="auth-title">
          LabSentinel
        </h1>
        <p className="auth-subtitle">Monitoreo seguro de laboratorios</p>

        {authError && (
          <p className="auth-error auth-error--banner" role="alert">
            {authError}
          </p>
        )}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="email">Correo institucional</label>
            <div
              className={`auth-input-wrap${showEmailError ? " auth-input-wrap--error" : ""}`}
            >
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="usuario@institucion.edu"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                onBlur={() => setEmailTouched(true)}
                aria-invalid={showEmailError}
                aria-describedby={showEmailError ? "email-error" : undefined}
              />
              <Mail
                className={`auth-input-icon${showEmailError ? " auth-input-icon--error" : ""}`}
                size={18}
                aria-hidden="true"
              />
            </div>
            {showEmailError && (
              <p id="email-error" className="auth-error" role="alert">
                Ingresa un correo electrónico válido.
              </p>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="password">Contraseña</label>
            <div className="auth-input-wrap">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Ingresa tu contraseña"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              <button
                type="button"
                className="auth-toggle-password"
                onClick={() => setShowPassword((current) => !current)}
                aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              >
                {showPassword ? "Ocultar" : "Mostrar"}
              </button>
            </div>
          </div>

          <button type="submit" className="auth-submit">
            Iniciar sesión
          </button>
        </form>

        {(googleEnabled || keycloakEnabled) && (
          <div className="auth-divider" role="separator" aria-label="O continúa con">
            <span>o continúa con</span>
          </div>
        )}

        {googleEnabled && (
          <GoogleSignInButton
            onSuccess={onLoginSuccess}
            onError={setAuthError}
          />
        )}

        {keycloakEnabled && (
          <button
            type="button"
            className="auth-keycloak-button"
            onClick={() => window.location.assign(`${apiBaseUrl}/auth/keycloak/login`)}
          >
            <KeyRound size={17} aria-hidden="true" />
            Ingresar con Keycloak
          </button>
        )}
      </section>

      <footer className="auth-footer">
        Universidad Mayor de San Simón — Departamento de Sistemas e Informática
      </footer>
    </main>
  );
}
