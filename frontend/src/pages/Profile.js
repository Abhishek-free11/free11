import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import Navbar from '../components/Navbar';
import NotificationSettings from '../components/NotificationSettings';
import LanguageSelector from '../components/LanguageSelector';
import WishlistGoal from '../components/WishlistGoal';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { User, Mail, Coins, Trophy, TrendingUp, Shield, HelpCircle, Volume2, VolumeX, Settings, LogOut, ChevronRight, ShoppingBag, Zap, Gift, Star, UserPlus, Fingerprint, Wallet, Target, Download } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { isSoundEnabled, setSoundEnabled } from '../utils/sounds';
import { isBiometricEnabled, disableBiometric } from '../utils/biometric';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();
  const [stats, setStats] = useState(null);
  const [demandProgress, setDemandProgress] = useState(null);
  const [soundsEnabled, setSoundsEnabled] = useState(isSoundEnabled());
  const [biometricOn, setBiometricOn] = useState(isBiometricEnabled());
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [installPrompt, setInstallPrompt] = useState(null);
  const [canInstall, setCanInstall] = useState(false);

  useEffect(() => {
    const isInstalled = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone;
    if (isInstalled) return;
    if (window.__pwaPrompt) { setInstallPrompt(window.__pwaPrompt); setCanInstall(true); return; }
    const handler = (e) => { e.preventDefault(); window.__pwaPrompt = e; setInstallPrompt(e); setCanInstall(true); };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstallApp = async () => {
    if (installPrompt) {
      installPrompt.prompt();
      const { outcome } = await installPrompt.userChoice;
      if (outcome === 'accepted') { setCanInstall(false); toast.success('FREE11 installed! Check your home screen.'); }
    } else {
      toast.info('To install: tap the browser menu → "Add to Home Screen"');
    }
  };

  const handleSoundToggle = (enabled) => {
    setSoundsEnabled(enabled);
    setSoundEnabled(enabled);
    toast.success(enabled ? t('profile_page.sounds_enabled_msg') : t('profile_page.sounds_disabled_msg'));
  };

  const handleLogout = () => { logout(); toast.success(t('profile_page.logged_out_msg')); navigate('/login'); };

  useEffect(() => {
    api.getUserStats().then(r => setStats(r.data)).catch(() => {});
    api.getDemandProgress().then(r => setDemandProgress(r.data)).catch(() => {});
  }, []);

  const getRankName = (level) => {
    const names = [t('profile_page.rookie'), t('profile_page.amateur'), t('profile_page.pro'), t('profile_page.expert'), t('profile_page.legend')];
    return names[(level || 1) - 1] || t('profile_page.legend');
  };

  const menuItems = [
    { label: t('profile_page.invite_friends'), icon: UserPlus, path: '/invite', color: '#4ade80', highlight: true },
    { label: t('profile_page.my_orders'), icon: ShoppingBag, path: '/orders', color: '#60a5fa' },
    { label: 'Wallet History', icon: Wallet, path: '/wallet', color: '#C6A052' },
    { label: t('profile_page.earn_coins'), icon: Zap, path: '/earn', color: '#C6A052' },
    { label: t('profile_page.redeem_shop'), icon: Gift, path: '/shop', color: '#f472b6' },
    { label: t('profile_page.help_support'), icon: HelpCircle, path: '/support', color: '#a78bfa' },
  ];

  const legalLinks = [
    { label: t('profile_page.about_free11'), path: '/about' },
    { label: t('profile_page.terms_conditions'), path: '/terms' },
    { label: t('profile_page.privacy_policy'), path: '/privacy' },
    { label: t('profile_page.community_guidelines'), path: '/guidelines' },
    { label: t('profile_page.faq'), path: '/faq' },
  ];

  return (
    <div className="min-h-screen bg-[#0F1115] pb-28 md:pb-6">
      <div className="fixed pointer-events-none" style={{ top: 0, left: '50%', transform: 'translateX(-50%)', width: '70vw', height: '30vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.04) 0%, transparent 70%)', zIndex: 0 }} />
      <Navbar />

      <div className="relative z-10 max-w-lg mx-auto px-4 py-4 space-y-4 animate-slide-up" data-testid="profile-page">

        {/* ── Profile Header ── */}
        <div className="card-broadcast-gold overflow-hidden">
          {/* Banner */}
          <div className="h-16" style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.2), rgba(224,184,79,0.05), transparent)' }} />
          <div className="px-4 pb-4 -mt-8">
            <div className="flex items-end gap-3 mb-3">
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl font-black text-[#0F1115] flex-shrink-0 border-4 animate-coin-glow"
                style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', borderColor: '#0F1115' }}>
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="flex-1 pb-1">
                <h2 className="text-xl font-bold text-white">{user?.name || 'User'}</h2>
                <p className="text-xs" style={{ color: '#8A9096' }}>{user?.email}</p>
              </div>
            </div>

            {/* Rank badge */}
            <div className="flex items-center justify-between p-3 rounded-xl mb-3"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div className="flex items-center gap-2">
                <Star className="h-4 w-4" style={{ color: '#C6A052' }} />
                <span className="text-white font-medium">{getRankName(user?.level)}</span>
                <span className="text-xs px-2 py-0.5 rounded-full font-bold"
                  style={{ background: 'rgba(198,160,82,0.15)', color: '#C6A052' }}>
                  {t('profile_page.level')} {user?.level || 1}
                </span>
              </div>
              <span className="text-sm font-numbers font-bold" style={{ color: '#8A9096' }}>{user?.xp || 0} {t('profile_page.xp')}</span>
            </div>

            {/* XP progress */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span style={{ color: '#8A9096' }}>{t('profile_page.progress_next')}</span>
                <span style={{ color: '#C6A052' }}>
                  {demandProgress?.rank?.xp_to_next ? `${demandProgress.rank.xp_to_next} ${t('profile_page.xp_needed')}` : t('profile_page.max_level')}
                </span>
              </div>
              <div className="h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
                <div className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${demandProgress?.rank?.progress || 0}%`, background: 'linear-gradient(90deg, #C6A052, #E0B84F)' }} />
              </div>
            </div>
          </div>
        </div>

        {/* ── Coins Card ── */}
        <div className="card-broadcast p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl" style={{ background: 'rgba(198,160,82,0.12)' }}>
              <Coins className="h-6 w-6" style={{ color: '#C6A052' }} />
            </div>
            <div>
              <p className="text-xs" style={{ color: '#8A9096' }}>{t('profile_page.your_balance')}</p>
              <p className="font-numbers text-2xl font-black" style={{ color: '#C6A052' }}>{user?.coins_balance || 0}
                <span className="text-sm font-normal ml-1" style={{ color: '#8A9096' }}>{t('profile_page.coins_label')}</span>
              </p>
            </div>
          </div>
          <button onClick={() => navigate('/shop')} className="btn-gold px-4 h-10 rounded-xl text-sm">
            {t('profile_page.redeem_btn')}
          </button>
        </div>

        {/* ── Goal Tracker (WishlistGoal) ── */}
        <WishlistGoal coinsBalance={user?.coins_balance || 0} />

        {/* ── Stats ── */}
        <div className="card-broadcast p-4">
          <h3 className="font-medium text-white mb-3 flex items-center gap-2">
            <Trophy className="h-4 w-4" style={{ color: '#C6A052' }} /> {t('profile_page.your_stats')}
          </h3>
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: t('profile_page.predictions'), value: stats?.total_predictions || 0, color: '#fff' },
              { label: t('profile_page.accuracy'), value: `${stats?.accuracy || 0}%`, color: '#4ade80' },
              { label: t('profile_page.total_earned'), value: user?.total_earned || 0, color: '#C6A052' },
            ].map(({ label, value, color }) => (
              <div key={label} className="text-center p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                <p className="text-2xl font-numbers font-black" style={{ color }}>{value}</p>
                <p className="text-[10px] mt-0.5" style={{ color: '#8A9096' }}>{label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Menu Items ── */}
        <div className="card-broadcast overflow-hidden">
          {menuItems.map((item, index) => (
            <button key={item.label} onClick={() => navigate(item.path)}
              className="w-full flex items-center justify-between px-4 py-3 transition-colors hover:bg-white/3"
              style={{
                borderBottom: index !== menuItems.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                background: item.highlight ? 'rgba(74,222,128,0.04)' : 'transparent',
              }}>
              <div className="flex items-center gap-3">
                <item.icon className="h-5 w-5" style={{ color: item.color }} />
                <span className="font-medium" style={{ color: item.highlight ? '#4ade80' : '#fff' }}>{item.label}</span>
                {item.highlight && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-bold"
                    style={{ background: 'rgba(74,222,128,0.15)', color: '#4ade80' }}>
                    {t('profile_page.earn_badge')}
                  </span>
                )}
              </div>
              <ChevronRight className="h-4 w-4" style={{ color: '#8A9096' }} />
            </button>
          ))}
        </div>

        {/* ── Notifications ── */}
        <NotificationSettings userId={user?.id} />

        {/* ── Settings ── */}
        <div className="card-broadcast overflow-hidden">
          <div className="px-4 py-3 border-b" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
            <h3 className="font-medium text-white flex items-center gap-2">
              <Settings className="h-4 w-4" style={{ color: '#8A9096' }} /> {t('profile_page.settings_title')}
            </h3>
          </div>
          <div className="px-4 py-3">
            {/* Language */}
            <div className="flex items-center justify-between mb-3 pb-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <span className="text-white">Language</span>
              <LanguageSelector />
            </div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                {soundsEnabled ? <Volume2 className="h-5 w-5 text-green-400" /> : <VolumeX className="h-5 w-5" style={{ color: '#8A9096' }} />}
                <span className="text-white">{t('profile_page.sound_effects')}</span>
              </div>
              <Switch checked={soundsEnabled} onCheckedChange={handleSoundToggle} />
            </div>
            <div className="flex items-center justify-between pt-3 border-t" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
              <div className="flex items-center gap-3">
                <Fingerprint className={`h-5 w-5 ${biometricOn ? 'text-yellow-400' : ''}`} style={biometricOn ? {} : { color: '#8A9096' }} />
                <div>
                  <span className="text-white">Biometric Login</span>
                  <p className="text-[10px]" style={{ color: '#8A9096' }}>Fingerprint / Face ID quick sign-in</p>
                </div>
              </div>
              <Switch checked={biometricOn} onCheckedChange={(v) => {
                if (!v) { disableBiometric(); setBiometricOn(false); toast.success('Biometric login disabled'); }
                else { toast.info('Log out and log in again to enable biometric'); }
              }} />
            </div>
          </div>
          {user?.is_admin && (
            <button onClick={() => navigate('/admin')}
              className="w-full flex items-center justify-between px-4 py-3 border-t transition-colors hover:bg-white/3"
              style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
              <div className="flex items-center gap-3">
                <Shield className="h-5 w-5 text-green-400" />
                <span className="font-medium text-green-400">{t('profile_page.admin_dashboard')}</span>
              </div>
              <ChevronRight className="h-4 w-4 text-green-400" />
            </button>
          )}
          {/* Install App */}
          <button onClick={handleInstallApp}
            className="w-full flex items-center justify-between px-4 py-3 border-t transition-colors hover:bg-white/3"
            style={{ borderColor: 'rgba(255,255,255,0.05)' }}
            data-testid="profile-install-app-btn">
            <div className="flex items-center gap-3">
              <Download className="h-5 w-5" style={{ color: '#C6A052' }} />
              <div>
                <span className="text-white">Install FREE11 App</span>
                <p className="text-[10px]" style={{ color: '#8A9096' }}>Add to your home screen for the best experience</p>
              </div>
            </div>
            <ChevronRight className="h-4 w-4" style={{ color: '#8A9096' }} />
          </button>
        </div>

        {/* ── Legal ── */}
        <div className="card-broadcast overflow-hidden">
          <div className="px-4 py-3 border-b" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
            <h3 className="font-medium text-white">{t('profile_page.legal_info')}</h3>
          </div>
          {legalLinks.map((item, index) => (
            <button key={item.label} onClick={() => navigate(item.path)}
              className="w-full flex items-center justify-between px-4 py-3 transition-colors hover:bg-white/3"
              style={{ borderBottom: index !== legalLinks.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none' }}>
              <span className="text-sm" style={{ color: '#BFC3C8' }}>{item.label}</span>
              <ChevronRight className="h-4 w-4" style={{ color: '#8A9096' }} />
            </button>
          ))}
        </div>

        {/* ── Logout ── */}
        <button onClick={() => setShowLogoutDialog(true)}
          className="w-full h-12 rounded-xl font-bold transition-all hover:bg-red-500/10"
          style={{ border: '1px solid rgba(239,68,68,0.35)', color: '#f87171' }}
          data-testid="logout-btn">
          <LogOut className="h-5 w-5 inline mr-2" />
          {t('profile_page.log_out')}
        </button>

        <p className="text-center text-xs pb-2" style={{ color: '#2A2D33' }}>{t('profile_page.version')}</p>
      </div>

      <AlertDialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
        <AlertDialogContent className="max-w-sm mx-4" style={{ background: '#1B1E23', border: '1px solid rgba(255,255,255,0.08)' }}>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">{t('profile_page.logout_confirm_title')}</AlertDialogTitle>
            <AlertDialogDescription style={{ color: '#8A9096' }}>{t('profile_page.logout_message')}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel style={{ background: '#1B1E23', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}>{t('common.cancel')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleLogout} style={{ background: '#ef4444', color: '#fff' }}>{t('profile_page.yes_logout')}</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Profile;
