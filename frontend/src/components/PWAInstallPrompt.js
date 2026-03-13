import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Share, Plus, ArrowDown } from 'lucide-react';

// Detect platform
const isIOS = () => /iphone|ipad|ipod/i.test(navigator.userAgent);
const isInStandaloneMode = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  window.navigator.standalone === true;

const DISMISS_KEY = 'pwa_prompt_dismissed_at';
const INSTALL_KEY = 'appInstalled';
// Re-show after 3 days if dismissed
const DISMISS_TTL_MS = 3 * 24 * 60 * 60 * 1000;

export default function PWAInstallPrompt() {
  const [show, setShow] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [platform, setPlatform] = useState(null); // 'ios' | 'android' | null

  useEffect(() => {
    // Already installed as standalone app — never show
    if (isInStandaloneMode()) return;
    // Already installed
    if (localStorage.getItem(INSTALL_KEY)) return;
    // Dismissed recently
    const dismissedAt = localStorage.getItem(DISMISS_KEY);
    if (dismissedAt && Date.now() - parseInt(dismissedAt, 10) < DISMISS_TTL_MS) return;

    if (isIOS()) {
      setPlatform('ios');
      // Show iOS instructions after 2s
      const t = setTimeout(() => setShow(true), 2000);
      return () => clearTimeout(t);
    }

    // Android / Chrome: wait for beforeinstallprompt
    const handlePrompt = (e) => {
      e.preventDefault();
      window.__pwaPrompt = e;
      setDeferredPrompt(e);
      setPlatform('android');
      setShow(true);
    };

    window.addEventListener('beforeinstallprompt', handlePrompt);

    // If already captured before React mounted
    if (window.__pwaPrompt) {
      setDeferredPrompt(window.__pwaPrompt);
      setPlatform('android');
      const t = setTimeout(() => setShow(true), 1500);
      return () => {
        clearTimeout(t);
        window.removeEventListener('beforeinstallprompt', handlePrompt);
      };
    }

    const installed = () => {
      localStorage.setItem(INSTALL_KEY, 'true');
      setShow(false);
    };
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
    if (outcome === 'accepted') {
      localStorage.setItem(INSTALL_KEY, 'true');
    }
    setShow(false);
    setDeferredPrompt(null);
    window.__pwaPrompt = null;
  };

  const handleDismiss = () => {
    setShow(false);
    localStorage.setItem(DISMISS_KEY, Date.now().toString());
  };

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
            className="fixed bottom-0 inset-x-0 z-[9999] px-0"
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
                  className="h-16 w-16 rounded-2xl"
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
              <div className="grid grid-cols-3 gap-3 mb-5">
                {[
                  { icon: '⚡', label: 'Instant Launch' },
                  { icon: '🎯', label: 'Works Offline' },
                  { icon: '🏆', label: 'Free Rewards' },
                ].map(({ icon, label }) => (
                  <div
                    key={label}
                    className="flex flex-col items-center gap-1.5 p-3 rounded-2xl"
                    style={{ background: 'rgba(198,160,82,0.07)', border: '1px solid rgba(198,160,82,0.12)' }}
                  >
                    <span className="text-xl">{icon}</span>
                    <span className="text-xs text-center" style={{ color: '#BFC3C8' }}>{label}</span>
                  </div>
                ))}
              </div>

              {platform === 'android' && (
                <button
                  onClick={handleInstall}
                  className="w-full py-4 rounded-2xl font-bold text-base flex items-center justify-center gap-2"
                  style={{
                    background: 'linear-gradient(135deg, #C6A052, #E0B84F)',
                    color: '#0F1115',
                    fontSize: '16px',
                  }}
                  data-testid="pwa-install-btn"
                >
                  <ArrowDown size={18} strokeWidth={2.5} />
                  Add to Home Screen
                </button>
              )}

              {platform === 'ios' && (
                <div className="space-y-3">
                  <p className="text-xs text-center mb-3" style={{ color: '#8A9096' }}>
                    Follow these steps in Safari to install:
                  </p>
                  {[
                    { step: '1', icon: <Share size={16} />, text: 'Tap the Share button at the bottom of Safari' },
                    { step: '2', icon: <Plus size={16} />, text: 'Tap "Add to Home Screen"' },
                    { step: '3', icon: null, text: 'Tap "Add" to confirm' },
                  ].map(({ step, icon, text }) => (
                    <div
                      key={step}
                      className="flex items-center gap-3 p-3 rounded-xl"
                      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)' }}
                    >
                      <div
                        className="h-7 w-7 rounded-full flex items-center justify-center shrink-0 font-bold text-sm"
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
                  <button
                    onClick={handleDismiss}
                    className="w-full py-3 rounded-2xl text-sm mt-2"
                    style={{ background: 'rgba(255,255,255,0.06)', color: '#8A9096' }}
                    data-testid="pwa-ios-dismiss"
                  >
                    Maybe later
                  </button>
                </div>
              )}

              {platform === 'android' && (
                <button
                  onClick={handleDismiss}
                  className="w-full py-3 rounded-2xl text-sm mt-3"
                  style={{ background: 'rgba(255,255,255,0.04)', color: '#8A9096' }}
                  data-testid="pwa-install-skip"
                >
                  Not now
                </button>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
