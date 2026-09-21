import React, { useState } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { loginWithGoogle } from "../services/authApi.js";

export function GoogleSignInButton({ onSuccess, onError }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleGoogleSuccess(credentialResponse) {
    if (!credentialResponse?.credential) {
      onError?.("Google did not return a valid credential.");
      return;
    }

    setIsSubmitting(true);
    try {
      const data = await loginWithGoogle(credentialResponse.credential);
      onSuccess?.(data.user);
    } catch (error) {
      onError?.(error.message ?? "Google sign in failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleGoogleError() {
    onError?.("Google sign in was cancelled or failed.");
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
        locale="en"
      />
    </div>
  );
}
