import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Share2, Plus, ArrowDown, CheckCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

// Platform detection
const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent);
const isInStandaloneMode = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  window.navigator.standalone === true;

const DISMISS_KEY = 'pwa_prompt_dismissed_at';
const INSTALL_KEY = 'appInstalled';
const SHARE_DONE_KEY = 'pwa_share_done';
const DISMISS_TTL_MS = 3 * 24 * 60 * 60 * 1000; // 3 days

export default function PWAInstallPrompt() {
  const { user } = useAuth();
  const [show, setShow] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [platform, setPlatform] = useState(null); // 'ios' | 'android'
  const [shareState, setShareState] = useState('idle'); // 'idle' | 'sharing' | 'done'
  const [shareClaimed, setShareClaimed] = useState(false);

  useEffect(() => {
    if (isInStandaloneMode()) return;
    if (localStorage.getItem(INSTALL_KEY)) return;
    const dismissedAt = localStorage.getItem(DISMISS_KEY);
    if (dismissedAt && Date.now() - parseInt(dismissedAt, 10) < DISMISS_TTL_MS) return;
    if (localStorage.getItem(SHARE_DONE_KEY)) setShareClaimed(true);

    if (isIOS()) {
      setPlatform('ios');
      const t = setTimeout(() => setShow(true), 2000);
      return () => clearTimeout(t);
    }

    const handlePrompt = (e) => {
      e.preventDefault();
      window.__pwaPrompt = e;
      setDeferredPrompt(e);
      setPlatform('android');
      setShow(true);
    };
    window.addEventListener('beforeinstallprompt', handlePrompt);

    if (window.__pwaPrompt) {
      setDeferredPrompt(window.__pwaPrompt);
      setPlatform('android');
      const t = setTimeout(() => setShow(true), 1500);
      return () => {
        clearTimeout(t);
        window.removeEventListener('beforeinstallprompt', handlePrompt);
      };
    }

    const installed = () => { localStorage.setItem(INSTALL_KEY, 'true'); setShow(false); };
    window.addEventListener('appinstalled', installed);
    return () => {
      window.removeEventListener('beforeinstallprompt', handlePrompt);
      window.removeEventListener('appinstalled', installed);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') localStorage.setItem(INSTALL_KEY, 'true');
    setShow(false);
    setDeferredPrompt(null);
    window.__pwaPrompt = null;
  };

  const handleShare = async () => {
    if (shareState === 'done') return;
    setShareState('sharing');
    try {
      await navigator.share({
        title: 'FREE11 — Play Games, Earn Real Rewards',
        text: 'Play free cricket predictions & card games on FREE11. Earn coins and redeem for real rewards!',
        url: 'https://free11.com',
      });
      // Share was successful — award coins if logged in
      localStorage.setItem(SHARE_DONE_KEY, '1');
      setShareClaimed(true);

      if (user) {
        const token = localStorage.getItem('token');
        try {
          const res = await fetch(`${API}/api/v2/earn/app-share`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
          });
          const data = await res.json();
          if (res.ok && data.success) {
            setShareState('done');
          } else {
            // Already claimed — still show done state
            setShareState('done');
          }
        } catch {
          setShareState('done');
        }
      } else {
        setShareState('done');
      }
    } catch {
      // User cancelled share or share not supported
      setShareState('idle');
    }
  };

  const handleDismiss = () => {
    setShow(false);
    localStorage.setItem(DISMISS_KEY, Date.now().toString());
  };

  const canShare = typeof navigator !== 'undefined' && !!navigator.share;

  if (!show || !platform) return null;

  return (
    <AnimatePresence>
      {show && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleDismiss}
            className="fixed inset-0 z-[9990]"
            style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}
          />

          {/* Bottom Sheet */}
          <motion.div
            key="sheet"
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', stiffness: 320, damping: 30 }}
            className="fixed bottom-0 inset-x-0 z-[9999]"
            data-testid="pwa-install-sheet"
          >
            <div
              className="rounded-t-3xl p-6"
              style={{
                background: '#16181D',
                border: '1px solid rgba(198,160,82,0.25)',
                borderBottom: 'none',
                boxShadow: '0 -8px 48px rgba(0,0,0,0.7)',
                maxWidth: '480px',
                margin: '0 auto',
              }}
            >
              {/* Handle bar */}
              <div className="w-10 h-1 rounded-full mx-auto mb-5" style={{ background: 'rgba(198,160,82,0.3)' }} />

              {/* Header */}
              <div className="flex items-center gap-4 mb-5">
                <img
                  src="/free11_icon_192.png"
                  alt="FREE11"
                  className="h-14 w-14 rounded-2xl"
                  style={{ boxShadow: '0 0 20px rgba(198,160,82,0.3)' }}
                />
                <div className="flex-1">
                  <p className="font-bold text-white text-lg tracking-wide">Install FREE11</p>
                  <p className="text-sm mt-0.5" style={{ color: '#8A9096' }}>
                    Play anytime, earn real rewards
                  </p>
                </div>
                <button
                  onClick={handleDismiss}
                  className="p-2 rounded-full"
                  style={{ background: 'rgba(255,255,255,0.07)', color: '#8A9096' }}
                  data-testid="pwa-install-dismiss"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Benefits row */}
              <div className="grid grid-cols-3 gap-2 mb-4">
                {[
                  { icon: '⚡', label: 'Instant Launch' },
                  { icon: '🎯', label: 'Works Offline' },
                  { icon: '🏆', label: 'Free Rewards' },
                ].map(({ icon, label }) => (
                  <div
                    key={label}
                    className="flex flex-col items-center gap-1.5 p-2.5 rounded-2xl"
                    style={{ background: 'rgba(198,160,82,0.07)', border: '1px solid rgba(198,160,82,0.12)' }}
                  >
                    <span className="text-lg">{icon}</span>
                    <span className="text-xs text-center" style={{ color: '#BFC3C8' }}>{label}</span>
                  </div>
                ))}
              </div>

              {/* Share & Earn Row */}
              {canShare && (
                <motion.button
                  onClick={handleShare}
                  disabled={shareState === 'done' || shareClaimed}
                  whileTap={{ scale: shareState === 'done' ? 1 : 0.97 }}
                  className="w-full py-3.5 rounded-2xl flex items-center justify-between px-4 mb-3"
                  style={{
                    background: shareState === 'done' || shareClaimed
                      ? 'rgba(34,197,94,0.12)'
                      : 'rgba(198,160,82,0.1)',
                    border: `1px solid ${shareState === 'done' || shareClaimed ? 'rgba(34,197,94,0.3)' : 'rgba(198,160,82,0.25)'}`,
                    transition: 'all 0.3s ease',
                  }}
                  data-testid="pwa-share-btn"
                >
                  <div className="flex items-center gap-3">
                    {shareState === 'done' || shareClaimed ? (
                      <CheckCircle size={18} style={{ color: '#22c55e' }} />
                    ) : (
                      <Share2 size={18} style={{ color: '#C6A052' }} />
                    )}
                    <div className="text-left">
                      <p className="text-sm font-semibold" style={{ color: shareState === 'done' || shareClaimed ? '#22c55e' : '#ffffff' }}>
                        {shareState === 'done' || shareClaimed ? 'Thanks for sharing!' : 'Share with friends'}
                      </p>
                      <p className="text-xs" style={{ color: '#8A9096' }}>
                        {shareState === 'done' || shareClaimed
                          ? user ? '50 FREE Coins added to your wallet' : 'Sign up to claim your 50 FREE Coins'
                          : user ? 'Earn 50 FREE Coins instantly' : 'Sign up & earn 50 FREE Coins'}
                      </p>
                    </div>
                  </div>
                  {!(shareState === 'done' || shareClaimed) && (
                    <div
                      className="px-3 py-1.5 rounded-xl text-xs font-bold shrink-0"
                      style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                    >
                      +50
                    </div>
                  )}
                </motion.button>
              )}

              {/* Install / iOS Steps */}
              {platform === 'android' && (
                <button
                  onClick={handleInstall}
                  className="w-full py-4 rounded-2xl font-bold text-base flex items-center justify-center gap-2"
                  style={{
                    background: 'linear-gradient(135deg, #C6A052, #E0B84F)',
                    color: '#0F1115',
                  }}
                  data-testid="pwa-install-btn"
                >
                  <ArrowDown size={18} strokeWidth={2.5} />
                  Add to Home Screen
                </button>
              )}

              {platform === 'ios' && (
                <div className="space-y-2.5">
                  <p className="text-xs text-center mb-3" style={{ color: '#8A9096' }}>
                    Follow these steps in Safari:
                  </p>
                  {[
                    { step: '1', icon: <Share2 size={14} />, text: 'Tap the Share button in Safari' },
                    { step: '2', icon: <Plus size={14} />, text: 'Tap "Add to Home Screen"' },
                    { step: '3', icon: null, text: 'Tap "Add" to confirm' },
                  ].map(({ step, icon, text }) => (
                    <div
                      key={step}
                      className="flex items-center gap-3 p-3 rounded-xl"
                      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}
                    >
                      <div
                        className="h-6 w-6 rounded-full flex items-center justify-center shrink-0 font-bold text-xs"
                        style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                      >
                        {step}
                      </div>
                      <div className="flex items-center gap-2 flex-1">
                        {icon && <span style={{ color: '#C6A052' }}>{icon}</span>}
                        <span className="text-sm" style={{ color: '#BFC3C8' }}>{text}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={handleDismiss}
                className="w-full py-3 rounded-2xl text-sm mt-3"
                style={{ background: 'rgba(255,255,255,0.04)', color: '#8A9096' }}
                data-testid="pwa-install-skip"
              >
                Not now
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
