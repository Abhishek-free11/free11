/**
 * Sentry Error Tracking Configuration for FREE11
 * 
 * To enable Sentry:
 * 1. Create a free account at https://sentry.io
 * 2. Create a new React project
 * 3. Get your DSN from Project Settings > Client Keys (DSN)
 * 4. Add REACT_APP_SENTRY_DSN to your .env file
 */

import * as Sentry from '@sentry/react';

const SENTRY_DSN = process.env.REACT_APP_SENTRY_DSN;

export const initSentry = () => {
  if (!SENTRY_DSN) {
    console.log('Sentry DSN not configured. Error tracking disabled.');
    return;
  }

  Sentry.init({
    dsn: SENTRY_DSN,
    environment: process.env.NODE_ENV,
    
    // Performance Monitoring
    tracesSampleRate: 0.1, // 10% of transactions for performance monitoring
    
    // Session Replay (for debugging)
    replaysSessionSampleRate: 0.1, // 10% of sessions
    replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors
    
    // Filter out known non-critical errors
    beforeSend(event, hint) {
      const error = hint.originalException;
      
      // Ignore network errors (user's connection issue)
      if (error && error.message && error.message.includes('Network Error')) {
        return null;
      }
      
      // Ignore chunk loading errors (deployment timing)
      if (error && error.message && error.message.includes('Loading chunk')) {
        return null;
      }
      
      return event;
    },
    
    // Additional context
    initialScope: {
      tags: {
        app: 'free11',
        platform: 'web'
      }
    }
  });
  
  console.log('Sentry initialized for error tracking');
};

// Error boundary wrapper for React components
export const SentryErrorBoundary = Sentry.ErrorBoundary;

// Capture custom errors
export const captureError = (error, context = {}) => {
  Sentry.captureException(error, {
    extra: context
  });
};

// Capture custom messages/events
export const captureMessage = (message, level = 'info') => {
  Sentry.captureMessage(message, level);
};

// Set user context
export const setUser = (user) => {
  if (user) {
    Sentry.setUser({
      id: user.id,
      email: user.email,
      username: user.name
    });
  } else {
    Sentry.setUser(null);
  }
};

// Add breadcrumb for debugging
export const addBreadcrumb = (category, message, data = {}) => {
  Sentry.addBreadcrumb({
    category,
    message,
    data,
    level: 'info'
  });
};

export default Sentry;
