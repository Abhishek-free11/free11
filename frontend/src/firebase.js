/**
 * FREE11 Firebase Configuration (Web)
 *
 * Used for:
 * - Web Push Notifications (FCM)
 * - Token registration with FREE11 backend
 *
 * Note: VAPID key is required for web push.
 * Generate it from Firebase Console → Project Settings → Cloud Messaging → Web Push certificates
 */

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY || 'AIzaSyBMRjuuazsPK8YXaKuI93v6yTE96k3Z0Gg',
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID || 'free11-cf539',
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID || '725923627857',
  appId: process.env.REACT_APP_FIREBASE_APP_ID || '',
};

// Vapid key for web push (generate from Firebase Console)
const VAPID_KEY = process.env.REACT_APP_FIREBASE_VAPID_KEY || '';

let messaging = null;
let firebaseApp = null;

/**
 * Initialize Firebase and return the messaging instance.
 * Returns null if Firebase is not configured.
 */
export async function initFirebase() {
  if (messaging) return messaging;
  if (!firebaseConfig.appId) {
    console.info('[FCM] Firebase appId not configured — push notifications disabled');
    return null;
  }
  try {
    const { initializeApp } = await import('firebase/app');
    const { getMessaging, getToken, onMessage } = await import('firebase/messaging');
    firebaseApp = initializeApp(firebaseConfig);
    messaging = getMessaging(firebaseApp);

    // Handle foreground messages
    onMessage(messaging, (payload) => {
      console.log('[FCM] Foreground message:', payload);
      // Show browser notification if permission granted
      if (Notification.permission === 'granted' && payload.notification) {
        new Notification(payload.notification.title || 'FREE11', {
          body: payload.notification.body,
          icon: '/free11_icon_192.png',
        });
      }
    });

    return messaging;
  } catch (e) {
    console.error('[FCM] Firebase init failed:', e);
    return null;
  }
}

/**
 * Request notification permission and get FCM token.
 * Returns token string or null.
 */
export async function requestAndGetToken() {
  if (!('Notification' in window)) return null;

  try {
    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.info('[FCM] Notification permission denied');
      return null;
    }

    const msg = await initFirebase();
    if (!msg) return null;

    const { getToken } = await import('firebase/messaging');
    if (!VAPID_KEY) {
      console.info('[FCM] VAPID key not set — skipping web push registration');
      return null;
    }

    const token = await getToken(msg, { vapidKey: VAPID_KEY });
    if (token) {
      console.info('[FCM] Token obtained:', token.substring(0, 20) + '...');
      return token;
    }
    return null;
  } catch (e) {
    console.error('[FCM] getToken failed:', e);
    return null;
  }
}
