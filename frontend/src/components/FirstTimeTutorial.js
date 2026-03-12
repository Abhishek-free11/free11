import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Target, Coins, Gift, Trophy, Gamepad2, Star, CheckCircle2, ChevronRight } from 'lucide-react';

const STEPS = [
  {
    id: 1,
    icon: Target,
    iconColor: '#ef4444',
    title: 'Make the right calls.',
    subtitle: 'Predict ball-by-ball outcomes during live T20 cricket matches.',
    detail: 'Your accuracy determines your rewards — it\'s pure skill.',
    targetTab: 'bottom-nav-play',
    arrowDir: 'down',
  },
  {
    id: 2,
    icon: Coins,
    iconColor: '#C6A052',
    title: 'Earn FREE Coins.',
    subtitle: 'Every correct prediction earns you FREE Coins.',
    detail: 'Also earn via Daily Puzzles, Crowd Meter, Ad Rewards & more.',
    targetTab: 'bottom-nav-missions',
    arrowDir: 'down',
  },
  {
    id: 3,
    icon: Gift,
    iconColor: '#22c55e',
    title: 'Redeem real groceries.',
    subtitle: 'Coins → cold drinks, groceries, mobile recharges & more.',
    detail: 'No deposits. No risk. Real rewards delivered via ONDC/Zepto.',
    targetTab: 'bottom-nav-home',
    arrowDir: 'down',
  },
  {
    id: 4,
    icon: Trophy,
    iconColor: '#a855f7',
    title: 'Climb the leaderboard.',
    subtitle: 'Top predictors get bonus coin drops & sponsored prizes.',
    detail: 'Streak multipliers boost your accuracy rank.',
    targetTab: 'bottom-nav-leaderboard',
    arrowDir: 'down',
  },
  {
    id: 5,
    icon: Gamepad2,
    iconColor: '#3b82f6',
    title: 'Play Card Games.',
    subtitle: 'Between matches? Earn extra coins with Rummy, Teen Patti & more.',
    detail: 'Create rooms, invite friends via WhatsApp — all skill-based.',
    targetTab: 'bottom-nav-play',
    arrowDir: 'down',
  },
  {
    id: 6,
    icon: Star,
    iconColor: '#f59e0b',
    title: 'Join Sponsored Pools.',
    subtitle: 'Brand-funded prize pools with real product rewards.',
    detail: 'Brands sponsor Cricket prediction pools with grocery prizes.',
    targetTab: 'bottom-nav-home',
    arrowDir: 'down',
  },
  {
    id: 7,
    icon: CheckCircle2,
    iconColor: '#22c55e',
    title: "You're ready!",
    subtitle: '"Play Cricket. Earn Essentials."',
    detail: 'Skill-based, free-to-play, no deposits. Start predicting now.',
    targetTab: null,
    arrowDir: null,
  },
];

const GoldArrow = ({ x }) => (
  <svg
    width="24" height="18" viewBox="0 0 24 18"
    style={{ position: 'fixed', bottom: 72, left: x - 12, zIndex: 10001, pointerEvents: 'none', filter: 'drop-shadow(0 0 6px rgba(198,160,82,0.8))' }}
  >
    <polygon points="12,18 0,0 24,0" fill="#C6A052" />
  </svg>
);

export default function FirstTimeTutorial({ onComplete, onSkip }) {
  const [step, setStep] = useState(0);
  const [arrowX, setArrowX] = useState(null);
  const highlightRef = useRef(null);
  const current = STEPS[step];

  const applySpotlight = useCallback((testId) => {
    // Remove previous spotlight
    if (highlightRef.current) {
      highlightRef.current.style.boxShadow = '';
      highlightRef.current.style.transform = '';
      highlightRef.current.style.zIndex = '';
      highlightRef.current.style.position = '';
      highlightRef.current.style.outline = '';
      highlightRef.current = null;
    }
    if (!testId) { setArrowX(null); return; }

    const el = document.querySelector(`[data-testid="${testId}"]`);
    if (!el) { setArrowX(null); return; }

    const rect = el.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    setArrowX(centerX);

    // Apply gold glow spotlight — keeps element visible above overlay
    el.style.boxShadow = '0 0 0 9999px rgba(0,0,0,0.75), 0 0 0 3px rgba(198,160,82,0.8), 0 0 20px rgba(198,160,82,0.5)';
    el.style.transform = 'scale(1.08)';
    el.style.zIndex = '10002';
    el.style.position = 'relative';
    el.style.outline = 'none';
    el.style.borderRadius = '12px';
    highlightRef.current = el;
  }, []);

  useEffect(() => {
    applySpotlight(current.targetTab);
    return () => {
      if (highlightRef.current) {
        highlightRef.current.style.boxShadow = '';
        highlightRef.current.style.transform = '';
        highlightRef.current.style.zIndex = '';
        highlightRef.current.style.position = '';
      }
    };
  }, [step, applySpotlight, current.targetTab]);

  // Cleanup on unmount
  useEffect(() => () => {
    if (highlightRef.current) {
      highlightRef.current.style.boxShadow = '';
      highlightRef.current.style.transform = '';
      highlightRef.current.style.zIndex = '';
      highlightRef.current.style.position = '';
    }
  }, []);

  const next = () => {
    if (step < STEPS.length - 1) setStep(s => s + 1);
    else onComplete();
  };

  const Icon = current.icon;
  const isLast = step === STEPS.length - 1;

  return (
    <>
      {/* Dim overlay — pointer-events-none so spotlight element remains clickable */}
      <div
        className="fixed inset-0 z-[10000] pointer-events-none"
        style={{ background: 'rgba(0,0,0,0.0)' }}
        data-testid="first-time-tutorial"
      />
      {/* Invisible click-catch layer below modal */}
      <div className="fixed inset-0 z-[10000]" onClick={onSkip} />

      {/* Gold pointing arrow — positioned using getBoundingClientRect */}
      {arrowX !== null && current.arrowDir === 'down' && <GoldArrow x={arrowX} />}

      {/* Tutorial card — positioned above the bottom nav */}
      <motion.div
        key={step}
        initial={{ opacity: 0, y: 24, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -12, scale: 0.97 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        className="fixed z-[10003] left-0 right-0 mx-auto px-4"
        style={{ bottom: current.targetTab ? 100 : '50%', transform: current.targetTab ? 'none' : 'translateY(50%)', maxWidth: 400 }}
        onClick={e => e.stopPropagation()}
      >
        <div className="rounded-2xl overflow-hidden"
          style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.35)', boxShadow: '0 24px 64px rgba(0,0,0,0.8)' }}>

          {/* Header */}
          <div className="flex items-center justify-between px-4 pt-4 pb-2">
            {/* Progress pills */}
            <div className="flex gap-1.5">
              {STEPS.map((_, i) => (
                <div key={i}
                  className="h-1.5 rounded-full transition-all duration-300"
                  style={{ width: i === step ? 20 : 6, background: i <= step ? '#C6A052' : 'rgba(255,255,255,0.1)' }} />
              ))}
            </div>
            <button onClick={onSkip} className="p-1 rounded-lg transition-colors" style={{ color: '#8A9096' }}
              data-testid="tutorial-skip-btn">
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body */}
          <div className="px-5 pb-2">
            {/* Icon */}
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ background: `${current.iconColor}22`, border: `1px solid ${current.iconColor}44` }}>
                <Icon className="w-5 h-5" style={{ color: current.iconColor }} />
              </div>
              <div>
                <p className="text-base font-black text-white leading-tight"
                  style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.04em', fontSize: '1.1rem' }}>
                  {current.title}
                </p>
                <p className="text-xs" style={{ color: '#C6A052' }}>{current.subtitle}</p>
              </div>
            </div>
            <p className="text-xs leading-relaxed mb-4" style={{ color: '#8A9096' }}>{current.detail}</p>
          </div>

          {/* Footer */}
          <div className="flex items-center gap-2 px-5 pb-4">
            {!isLast && (
              <button onClick={onSkip} className="text-xs py-2 px-3 rounded-lg" style={{ color: '#8A9096' }}>
                Skip tour
              </button>
            )}
            <button onClick={next}
              className="flex-1 h-10 rounded-xl text-sm font-bold flex items-center justify-center gap-1.5"
              style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
              data-testid="tutorial-next-btn">
              {isLast ? 'Start Playing' : (<>Next <ChevronRight className="w-3.5 h-3.5" /></>)}
            </button>
          </div>
        </div>
      </motion.div>
    </>
  );
}
