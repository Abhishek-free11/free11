import { useState, useEffect } from 'react';
import { ChevronRight, ChevronLeft, X } from 'lucide-react';

const STEPS = [
  {
    target: 'Matches',
    title: 'Match Centre',
    desc: 'View live, upcoming, and completed cricket matches. Build fantasy teams and join contests from here.',
    position: 'bottom',
    icon: '/free11-icon.png',
  },
  {
    target: 'Predict',
    title: 'Predictions',
    desc: 'Predict ball outcomes, over runs, wickets, and boundaries during live matches to earn coins.',
    position: 'bottom',
  },
  {
    target: 'Earn',
    title: 'Earn Coins',
    desc: 'Play quizzes, spin the wheel, scratch cards, watch ads, and complete tasks to boost your coins.',
    position: 'bottom',
  },
  {
    target: 'Games',
    title: 'Card Games',
    desc: 'Play Rummy, Teen Patti, and Poker with friends. Create rooms and invite via WhatsApp!',
    position: 'bottom',
  },
  {
    target: 'Profile',
    title: 'Your Profile',
    desc: 'View stats, badges, and account settings. Access Power-Ups, FREE Bucks, and Wallet from the menu.',
    position: 'bottom',
  },
  {
    target: 'search-btn',
    title: 'Search',
    desc: 'Search for any feature, page, or game. Also supports voice search — just tap the mic!',
    position: 'below',
    isTestId: true,
  },
  {
    target: 'coins',
    title: 'Coin Balance',
    desc: 'Your Free Coins. Earn through skill-based predictions, games, and daily activities. Redeem for real rewards!',
    position: 'below',
  },
];

export default function HowToPlay({ onComplete }) {
  const [step, setStep] = useState(0);
  const [highlight, setHighlight] = useState(null);

  useEffect(() => {
    updateHighlight();
  }, [step]);

  const updateHighlight = () => {
    const s = STEPS[step];
    if (!s) return;

    let el = null;
    if (s.isTestId) {
      el = document.querySelector(`[data-testid="${s.target}"]`);
    } else if (s.target === 'coins') {
      el = document.querySelector('.from-yellow-500\\/20');
    } else {
      // Find bottom nav button by text
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        if (btn.textContent?.trim() === s.target) {
          el = btn;
          break;
        }
      }
    }

    if (el) {
      const rect = el.getBoundingClientRect();
      setHighlight({ x: rect.left, y: rect.top, w: rect.width, h: rect.height });
    } else {
      setHighlight(null);
    }
  };

  const next = () => {
    if (step < STEPS.length - 1) setStep(step + 1);
    else onComplete();
  };

  const prev = () => {
    if (step > 0) setStep(step - 1);
  };

  const current = STEPS[step];

  return (
    <div className="fixed inset-0 z-[200]" data-testid="how-to-play-overlay">
      {/* Dark backdrop with hole */}
      <div className="absolute inset-0 bg-black/80" onClick={(e) => e.stopPropagation()} />

      {/* Highlight ring */}
      {highlight && (
        <div
          className="absolute border-2 border-yellow-400 rounded-2xl z-[201] pointer-events-none transition-all duration-300"
          style={{
            left: highlight.x - 4,
            top: highlight.y - 4,
            width: highlight.w + 8,
            height: highlight.h + 8,
            boxShadow: '0 0 0 4000px rgba(0,0,0,0.75), 0 0 20px rgba(234,179,8,0.5)',
          }}
        >
          {/* Arrow */}
          <div className="absolute left-1/2 -translate-x-1/2 -bottom-4">
            <div className="w-0 h-0 border-l-8 border-r-8 border-t-8 border-l-transparent border-r-transparent border-t-yellow-400" />
          </div>
        </div>
      )}

      {/* Tooltip card */}
      <div
        className="absolute z-[202] w-[85vw] max-w-sm transition-all duration-300"
        style={{
          left: '50%',
          transform: 'translateX(-50%)',
          top: highlight ? (highlight.y > 400 ? highlight.y - 160 : highlight.y + highlight.h + 24) : '40%',
        }}
      >
        <div className="bg-slate-900 border border-yellow-500/30 rounded-2xl p-4 shadow-2xl shadow-yellow-500/10">
          {/* Step indicator */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <img src="/free11-icon.png" alt="" className="h-5 w-5 rounded" />
              <span className="text-xs text-yellow-400 font-medium">Step {step + 1} of {STEPS.length}</span>
            </div>
            <button onClick={onComplete} className="text-gray-500 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Progress bar */}
          <div className="h-1 bg-slate-800 rounded-full mb-3 overflow-hidden">
            <div className="h-full bg-yellow-400 rounded-full transition-all duration-300" style={{ width: `${((step + 1) / STEPS.length) * 100}%` }} />
          </div>

          <h3 className="text-white font-bold text-base mb-1">{current.title}</h3>
          <p className="text-gray-300 text-sm leading-relaxed mb-4">{current.desc}</p>

          <div className="flex items-center justify-between">
            <button
              onClick={prev}
              disabled={step === 0}
              className="flex items-center gap-1 text-sm text-gray-400 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" /> Back
            </button>
            <button
              onClick={next}
              className="flex items-center gap-1 px-4 py-2 bg-yellow-500 text-black font-bold text-sm rounded-xl hover:bg-yellow-400 transition-all"
              data-testid="tutorial-next-btn"
            >
              {step === STEPS.length - 1 ? 'Got it!' : 'Next'} <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
