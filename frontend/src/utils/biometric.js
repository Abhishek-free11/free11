/**
 * Biometric / Credential Management utilities for FREE11 PWA
 * - Primary: PasswordCredential API (Android Chrome — triggers native biometric/PIN)
 * - Fallback: localStorage token persistence with device-lock UX
 */

const BIOMETRIC_KEY = 'f11_biometric_enabled';
const BIOMETRIC_EMAIL_KEY = 'f11_biometric_email';
const BIOMETRIC_TOKEN_KEY = 'f11_biometric_token';
const BIOMETRIC_NAME_KEY = 'f11_biometric_name';

/** Check if this device/browser supports the PasswordCredential API (real OS biometric prompt) */
export const hasPasswordCredentialSupport = () =>
  typeof window !== 'undefined' && 'PasswordCredential' in window && 'credentials' in navigator;

/** Check if biometric was previously enabled */
export const isBiometricEnabled = () =>
  localStorage.getItem(BIOMETRIC_KEY) === 'true';

/** Get the stored email for biometric login */
export const getBiometricEmail = () => localStorage.getItem(BIOMETRIC_EMAIL_KEY);
export const getBiometricName = () => localStorage.getItem(BIOMETRIC_NAME_KEY);

/**
 * Save credentials for biometric quick-login.
 * On Android Chrome, also stores in OS credential manager (triggers fingerprint next login).
 */
export const enableBiometric = async (email, token, name) => {
  localStorage.setItem(BIOMETRIC_KEY, 'true');
  localStorage.setItem(BIOMETRIC_EMAIL_KEY, email);
  localStorage.setItem(BIOMETRIC_TOKEN_KEY, token);
  localStorage.setItem(BIOMETRIC_NAME_KEY, name || 'FREE11 User');

  if (hasPasswordCredentialSupport()) {
    try {
      const cred = new window.PasswordCredential({
        id: email,
        password: token,
        name: name || 'FREE11 User',
        iconURL: `${window.location.origin}/free11_icon_192.png`,
      });
      await navigator.credentials.store(cred);
    } catch {
      // Silently ignore — localStorage fallback is set above
    }
  }
};

/**
 * Retrieve stored token using biometric authentication.
 * On Android Chrome: triggers OS biometric/PIN prompt via PasswordCredential API.
 * On other browsers: returns stored token directly (device lock is the protection layer).
 * Returns token string or null.
 */
export const getBiometricToken = async () => {
  if (hasPasswordCredentialSupport()) {
    try {
      const cred = await navigator.credentials.get({
        password: true,
        mediation: 'required', // always prompt — triggers biometric/PIN on Android
      });
      if (cred && cred.password) return cred.password;
    } catch {
      // User cancelled biometric or it failed
      return null;
    }
  }
  // Fallback: return localStorage token
  return localStorage.getItem(BIOMETRIC_TOKEN_KEY) || null;
};

/**
 * Update the stored biometric token (call after token refresh or re-login)
 */
export const updateBiometricToken = (token) => {
  if (isBiometricEnabled()) {
    localStorage.setItem(BIOMETRIC_TOKEN_KEY, token);
  }
};

/** Clear all biometric data */
export const disableBiometric = () => {
  localStorage.removeItem(BIOMETRIC_KEY);
  localStorage.removeItem(BIOMETRIC_EMAIL_KEY);
  localStorage.removeItem(BIOMETRIC_TOKEN_KEY);
  localStorage.removeItem(BIOMETRIC_NAME_KEY);
  if (hasPasswordCredentialSupport()) {
    navigator.credentials.preventSilentAccess?.();
  }
};
