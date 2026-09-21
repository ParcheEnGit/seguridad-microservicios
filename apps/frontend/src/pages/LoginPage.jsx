import React, { useState } from "react";
import { Mail, Shield } from "lucide-react";
import { GoogleSignInButton } from "../components/GoogleSignInButton.jsx";

const INSTITUTIONAL_EMAIL_PATTERN =
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function LoginPage({ onLoginSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [authError, setAuthError] = useState("");

  const emailInvalid =
    (emailTouched || submitAttempted) &&
    email.length > 0 &&
    !INSTITUTIONAL_EMAIL_PATTERN.test(email);
  const showEmailError = emailInvalid || (submitAttempted && email.length === 0);

  function handleSubmit(event) {
    event.preventDefault();
    setSubmitAttempted(true);
    setAuthError("Email and password sign in is not enabled yet. Use Google.");

    if (!email || !INSTITUTIONAL_EMAIL_PATTERN.test(email) || !password) {
      return;
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card" aria-labelledby="login-title">
        <div className="auth-brand" aria-hidden="true">
          <div className="auth-brand-icon">
            <Shield size={22} strokeWidth={2.2} />
          </div>
        </div>

        <h1 id="login-title" className="auth-title">
          LabSentinel
        </h1>
        <p className="auth-subtitle">Secure laboratory monitoring</p>

        {authError && (
          <p className="auth-error auth-error--banner" role="alert">
            {authError}
          </p>
        )}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label htmlFor="email">Institutional email</label>
            <div
              className={`auth-input-wrap${showEmailError ? " auth-input-wrap--error" : ""}`}
            >
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder="user@institution.edu"
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
                Invalid email
              </p>
            )}
          </div>

          <div className="auth-field">
            <label htmlFor="password">Password</label>
            <div className="auth-input-wrap">
              <input
                id="password"
                name="password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
              <button
                type="button"
                className="auth-toggle-password"
                onClick={() => setShowPassword((current) => !current)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </div>

          <button type="submit" className="auth-submit">
            Sign in
          </button>
        </form>

        <div className="auth-divider" role="separator" aria-label="Or continue with">
          <span>or</span>
        </div>

        <GoogleSignInButton
          onSuccess={onLoginSuccess}
          onError={setAuthError}
        />
      </section>

      <footer className="auth-footer">
        Mayor de San Simón University — Department of Systems and Informatics
      </footer>
    </main>
  );
}
