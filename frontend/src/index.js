import React from "react";
import ReactDOM from "react-dom/client";
import * as Sentry from "@sentry/react";
import "@/index.css";
import App from "@/App";

// Initialize Sentry for crash monitoring
if (process.env.REACT_APP_SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.REACT_APP_SENTRY_DSN,
    environment: process.env.NODE_ENV,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
  console.log('Sentry initialized for crash monitoring');
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <Sentry.ErrorBoundary fallback={<p>Something went wrong. Please refresh.</p>}>
      <App />
    </Sentry.ErrorBoundary>
  </React.StrictMode>,
);
