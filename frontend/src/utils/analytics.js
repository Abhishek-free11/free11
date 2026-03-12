/**
 * FREE11 Analytics — lightweight click/event tracker
 * Sends events to backend for product analytics.
 */
const API = process.env.REACT_APP_BACKEND_URL;

export const trackEvent = async (event, properties = {}) => {
  try {
    const token = localStorage.getItem('token');
    const endpoint = token ? '/api/v2/analytics/event' : '/api/v2/analytics/event/anon';
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    await fetch(`${API}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ event, properties: { ...properties, path: window.location.pathname, ts: Date.now() } }),
    });
  } catch (_) {
    // non-critical — never block UI
  }
};

// Quick wrappers for common events
export const trackButtonClick = (label, extra = {}) => trackEvent('button_click', { label, ...extra });
export const trackPageView = (page) => trackEvent('page_view', { page });
export const trackPWAInstall = () => trackEvent('pwa_install_click');
