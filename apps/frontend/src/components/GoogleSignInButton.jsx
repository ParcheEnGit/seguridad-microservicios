import React, { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { loginWithGoogle } from "../services/authApi.js";

export function GoogleSignInButton({ onSuccess, onError }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleGoogleSuccess(credentialResponse) {
    if (!credentialResponse?.credential) {
      onError?.("Google no devolvió una credencial válida.");
      return;
    }

    setIsSubmitting(true);
    try {
      const data = await loginWithGoogle(credentialResponse.credential);
      onSuccess?.(data.user);
    } catch (error) {
      onError?.(error.message ?? "No se pudo iniciar sesión con Google.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleGoogleError() {
    onError?.("El inicio de sesión con Google fue cancelado o falló.");
  }

  return (
    <div className={`auth-google-wrapper${isSubmitting ? " auth-google-wrapper--loading" : ""}`}>
      <GoogleLogin
        onSuccess={handleGoogleSuccess}
        onError={handleGoogleError}
        theme="outline"
        size="large"
        width={360}
        text="signin_with"
        shape="rectangular"
        locale="es"
      />
    </div>
  );
}
