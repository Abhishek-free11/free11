import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Bell, BellOff, Smartphone, Check, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import {
  isNotificationSupported,
  requestNotificationPermission,
  getNotificationPermission,
  scheduleDailyCheckInReminder,
  cancelAllReminders
} from '../utils/pushNotifications';

const NotificationSettings = ({ userId }) => {
  const [permission, setPermission] = useState('default');
  const [settings, setSettings] = useState({
    matchReminders: true,
    dailyCheckIn: true,
    voucherDelivery: true,
    coinsEarned: true,
    gameInvites: true,
    streakReminders: true
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check current permission status
    setPermission(getNotificationPermission());
    
    // Load saved settings from localStorage
    const savedSettings = localStorage.getItem('free11_notification_settings');
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
      } catch (e) {
        console.error('Failed to parse notification settings');
      }
    }
  }, []);

  // Save settings when changed
  useEffect(() => {
    localStorage.setItem('free11_notification_settings', JSON.stringify(settings));
    
    // Schedule/cancel reminders based on settings
    if (permission === 'granted' && settings.dailyCheckIn && userId) {
      scheduleDailyCheckInReminder(userId);
    } else {
      cancelAllReminders();
    }
  }, [settings, permission, userId]);

  const handleEnableNotifications = async () => {
    setLoading(true);
    try {
      const granted = await requestNotificationPermission();
      setPermission(granted ? 'granted' : 'denied');
      
      if (granted) {
        toast.success('Notifications enabled! You\'ll now receive updates.');
        
        // Schedule daily check-in reminder if enabled
        if (settings.dailyCheckIn && userId) {
          scheduleDailyCheckInReminder(userId);
        }
      } else {
        toast.error('Notification permission denied. You can enable it in browser settings.');
      }
    } catch (error) {
      toast.error('Failed to enable notifications');
    } finally {
      setLoading(false);
    }
  };

  const toggleSetting = (key) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const notSupported = !isNotificationSupported();

  if (notSupported) {
    return (
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-6">
          <div className="flex items-center gap-3 text-slate-400">
            <AlertCircle className="h-5 w-5" />
            <p className="text-sm">Push notifications are not supported in this browser.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg text-white flex items-center gap-2">
          <Bell className="h-5 w-5 text-yellow-400" />
          Push Notifications
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {permission !== 'granted' ? (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Smartphone className="h-5 w-5 text-yellow-400 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-white font-medium mb-1">Enable Notifications</p>
                <p className="text-xs text-slate-400 mb-3">
                  Get alerts for matches, voucher deliveries, and daily reminders!
                </p>
                <Button
                  onClick={handleEnableNotifications}
                  disabled={loading || permission === 'denied'}
                  className="bg-yellow-500 hover:bg-yellow-600 text-black"
                  data-testid="enable-notifications-btn"
                >
                  {loading ? 'Enabling...' : permission === 'denied' ? 'Blocked in Browser' : 'Enable Notifications'}
                </Button>
                {permission === 'denied' && (
                  <p className="text-xs text-red-400 mt-2">
                    Notifications are blocked. Please enable them in your browser settings.
                  </p>
                )}
              </div>
            </div>
          </div>
        ) : (
          <>
            <div className="flex items-center gap-2 text-green-400 text-sm mb-4">
              <Check className="h-4 w-4" />
              Notifications enabled
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="match-reminders" className="text-white text-sm flex items-center gap-2 cursor-pointer">
                  <span>🏏</span> Match Reminders
                </Label>
                <Switch
                  id="match-reminders"
                  checked={settings.matchReminders}
                  onCheckedChange={() => toggleSetting('matchReminders')}
                  data-testid="toggle-match-reminders"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="daily-checkin" className="text-white text-sm flex items-center gap-2 cursor-pointer">
                  <span>🌅</span> Daily Check-in Reminder
                </Label>
                <Switch
                  id="daily-checkin"
                  checked={settings.dailyCheckIn}
                  onCheckedChange={() => toggleSetting('dailyCheckIn')}
                  data-testid="toggle-daily-checkin"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="voucher-delivery" className="text-white text-sm flex items-center gap-2 cursor-pointer">
                  <span>🎁</span> Voucher Delivery
                </Label>
                <Switch
                  id="voucher-delivery"
                  checked={settings.voucherDelivery}
                  onCheckedChange={() => toggleSetting('voucherDelivery')}
                  data-testid="toggle-voucher-delivery"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="coins-earned" className="text-white text-sm flex items-center gap-2 cursor-pointer">
                  <span>🪙</span> Coins Earned
                </Label>
                <Switch
                  id="coins-earned"
                  checked={settings.coinsEarned}
                  onCheckedChange={() => toggleSetting('coinsEarned')}
                  data-testid="toggle-coins-earned"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="game-invites" className="text-white text-sm flex items-center gap-2 cursor-pointer">
                  <span>🎮</span> Game Invites
                </Label>
                <Switch
                  id="game-invites"
                  checked={settings.gameInvites}
                  onCheckedChange={() => toggleSetting('gameInvites')}
                  data-testid="toggle-game-invites"
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="streak-reminders" className="text-white text-sm flex items-center gap-2 cursor-pointer">
                  <span>🔥</span> Streak Reminders
                </Label>
                <Switch
                  id="streak-reminders"
                  checked={settings.streakReminders}
                  onCheckedChange={() => toggleSetting('streakReminders')}
                  data-testid="toggle-streak-reminders"
                />
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default NotificationSettings;
