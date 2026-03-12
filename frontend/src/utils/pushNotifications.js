/**
 * Push Notification Service for FREE11
 * Handles browser push notifications and reminder scheduling
 */

// Check if browser supports notifications
export const isNotificationSupported = () => {
  return 'Notification' in window && 'serviceWorker' in navigator;
};

// Request notification permission
export const requestNotificationPermission = async () => {
  if (!isNotificationSupported()) {
    console.log('Push notifications not supported');
    return false;
  }

  try {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  } catch (error) {
    console.error('Error requesting notification permission:', error);
    return false;
  }
};

// Get current permission status
export const getNotificationPermission = () => {
  if (!isNotificationSupported()) return 'unsupported';
  return Notification.permission;
};

// Show a local notification
export const showNotification = (title, options = {}) => {
  if (!isNotificationSupported() || Notification.permission !== 'granted') {
    console.log('Notifications not available or not permitted');
    return null;
  }

  const defaultOptions = {
    icon: '/logo192.png',
    badge: '/logo192.png',
    vibrate: [200, 100, 200],
    requireInteraction: false,
    ...options
  };

  try {
    return new Notification(title, defaultOptions);
  } catch (error) {
    console.error('Error showing notification:', error);
    return null;
  }
};

// Schedule a reminder notification
export const scheduleReminder = (title, body, delayMs, options = {}) => {
  return setTimeout(() => {
    showNotification(title, { body, ...options });
  }, delayMs);
};

// Notification types for FREE11
export const NotificationTypes = {
  MATCH_STARTING: 'match_starting',
  PREDICTION_REMINDER: 'prediction_reminder',
  VOUCHER_DELIVERED: 'voucher_delivered',
  COINS_EARNED: 'coins_earned',
  STREAK_REMINDER: 'streak_reminder',
  GAME_INVITE: 'game_invite',
  LEVEL_UP: 'level_up',
  FRIEND_JOINED: 'friend_joined'
};

// Pre-defined notification templates
export const notificationTemplates = {
  [NotificationTypes.MATCH_STARTING]: (matchName) => ({
    title: '🏏 Match Starting Soon!',
    body: `${matchName} is about to begin. Make your predictions now!`,
    tag: 'match-start',
    requireInteraction: true
  }),
  
  [NotificationTypes.PREDICTION_REMINDER]: (matchName) => ({
    title: '🎯 Prediction Time!',
    body: `Don't miss out! ${matchName} predictions are open.`,
    tag: 'prediction-reminder'
  }),
  
  [NotificationTypes.VOUCHER_DELIVERED]: (voucherName) => ({
    title: '🎁 Voucher Delivered!',
    body: `Your ${voucherName} is ready. Check your rewards!`,
    tag: 'voucher-delivered',
    requireInteraction: true
  }),
  
  [NotificationTypes.COINS_EARNED]: (amount, reason) => ({
    title: '🪙 Coins Earned!',
    body: `+${amount} coins for ${reason}. Keep predicting!`,
    tag: 'coins-earned'
  }),
  
  [NotificationTypes.STREAK_REMINDER]: (days) => ({
    title: '🔥 Keep Your Streak!',
    body: `You're on a ${days}-day streak. Check in today to continue!`,
    tag: 'streak-reminder',
    requireInteraction: true
  }),
  
  [NotificationTypes.GAME_INVITE]: (friendName, gameName) => ({
    title: '🎮 Game Invite!',
    body: `${friendName} invited you to play ${gameName}. Join now!`,
    tag: 'game-invite',
    requireInteraction: true
  }),
  
  [NotificationTypes.LEVEL_UP]: (newLevel) => ({
    title: '⬆️ Level Up!',
    body: `Congratulations! You've reached ${newLevel}. New rewards unlocked!`,
    tag: 'level-up'
  }),
  
  [NotificationTypes.FRIEND_JOINED]: (friendName) => ({
    title: '👋 Friend Joined FREE11!',
    body: `${friendName} joined using your invite. You both earned bonus coins!`,
    tag: 'friend-joined'
  })
};

// Send notification using template
export const sendTemplatedNotification = (type, ...args) => {
  const template = notificationTemplates[type];
  if (!template) {
    console.error('Unknown notification type:', type);
    return null;
  }
  
  const config = template(...args);
  return showNotification(config.title, {
    body: config.body,
    tag: config.tag,
    requireInteraction: config.requireInteraction
  });
};

// Store scheduled reminders
const scheduledReminders = new Map();

// Schedule daily check-in reminder
export const scheduleDailyCheckInReminder = (userId) => {
  const key = `checkin_${userId}`;
  
  // Clear existing reminder
  if (scheduledReminders.has(key)) {
    clearTimeout(scheduledReminders.get(key));
  }
  
  // Calculate time until 9 AM tomorrow
  const now = new Date();
  const tomorrow9AM = new Date(now);
  tomorrow9AM.setDate(tomorrow9AM.getDate() + 1);
  tomorrow9AM.setHours(9, 0, 0, 0);
  
  const delay = tomorrow9AM.getTime() - now.getTime();
  
  const timerId = scheduleReminder(
    '🌅 Good Morning!',
    'Check in now to maintain your streak and earn coins!',
    delay,
    { tag: 'daily-checkin', requireInteraction: true }
  );
  
  scheduledReminders.set(key, timerId);
  return timerId;
};

// Schedule match reminder (30 mins before)
export const scheduleMatchReminder = (matchId, matchName, startTime) => {
  const key = `match_${matchId}`;
  
  // Clear existing reminder
  if (scheduledReminders.has(key)) {
    clearTimeout(scheduledReminders.get(key));
  }
  
  const now = new Date();
  const matchTime = new Date(startTime);
  const reminderTime = matchTime.getTime() - (30 * 60 * 1000); // 30 mins before
  
  if (reminderTime <= now.getTime()) {
    return null; // Match already starting/started
  }
  
  const delay = reminderTime - now.getTime();
  
  const timerId = scheduleReminder(
    '🏏 Match in 30 Minutes!',
    `${matchName} starts soon. Set your predictions now!`,
    delay,
    { tag: `match-${matchId}`, requireInteraction: true }
  );
  
  scheduledReminders.set(key, timerId);
  return timerId;
};

// Cancel all scheduled reminders
export const cancelAllReminders = () => {
  scheduledReminders.forEach((timerId) => clearTimeout(timerId));
  scheduledReminders.clear();
};

// Export for use in components
export default {
  isNotificationSupported,
  requestNotificationPermission,
  getNotificationPermission,
  showNotification,
  scheduleReminder,
  sendTemplatedNotification,
  scheduleDailyCheckInReminder,
  scheduleMatchReminder,
  cancelAllReminders,
  NotificationTypes
};
