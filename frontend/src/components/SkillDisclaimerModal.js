import { useState } from 'react';
import { X, Shield, Award } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Section 2 — Legal / Skill Compliance Modal
// Displayed in Shop, Sponsored Pools, Quest modal, Landing footer
export default function SkillDisclaimerModal({ isOpen, onClose }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center"
          style={{ background: 'rgba(0,0,0,0.8)' }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          data-testid="skill-disclaimer-modal"
        >
          <motion.div
            className="w-full max-w-sm mx-4 mb-4 sm:mb-0 rounded-2xl overflow-hidden"
            style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.3)' }}
            initial={{ y: 60, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 60, opacity: 0 }}
            transition={{ type: 'spring', damping: 25 }}
            onClick={e => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 pt-4 pb-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'rgba(198,160,82,0.1)' }}>
                  <Shield className="w-4 h-4" style={{ color: '#C6A052' }} />
                </div>
                <p className="text-sm font-bold text-white">Skill-Based Platform</p>
              </div>
              <button onClick={onClose} className="p-1 rounded-lg" style={{ color: '#8A9096' }} data-testid="disclaimer-close">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Body */}
            <div className="px-4 py-4">
              <p className="text-sm text-white mb-3 leading-relaxed">
                FREE11 is a skill-based sports prediction platform. No deposits or cash wagering. Rewards are promotional benefits only.
              </p>

              <div className="space-y-2 mb-4">
                <p className="text-xs font-bold" style={{ color: '#C6A052' }}>Skill Inputs Used:</p>
                {[
                  'Player statistics & historical performance',
                  'Match conditions (pitch, weather, venue)',
                  'Crowd prediction trends & Crowd Meter data',
                  'Streak analysis & contest strategy',
                  'Live ball-by-ball inference',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-2">
                    <Award className="w-3 h-3 mt-0.5 flex-shrink-0" style={{ color: '#4ade80' }} />
                    <p className="text-xs" style={{ color: '#BFC3C8' }}>{item}</p>
                  </div>
                ))}
              </div>

              <div className="p-3 rounded-xl mb-4" style={{ background: 'rgba(198,160,82,0.06)', border: '1px solid rgba(198,160,82,0.15)' }}>
                <p className="text-xs" style={{ color: '#8A9096' }}>
                  FREE11 operates under the PROGA (Promotion and Regulation of Online Gaming Act, 2025) skill-game framework. All rewards are sponsored promotional perks earned through demonstrated prediction skill. There are no deposits, no cash prizes, and no real-money wagering of any kind.
                </p>
              </div>

              <button
                onClick={onClose}
                className="w-full py-2.5 rounded-xl text-sm font-bold"
                style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                data-testid="disclaimer-understood"
              >
                I Understand — Play Free!
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// Inline badge version — use next to prediction/contest titles
export function SkillBadge({ className = '' }) {
  return (
    <span
      className={`inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded-full ${className}`}
      style={{ background: 'rgba(74,222,128,0.1)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.2)' }}
      data-testid="skill-badge"
    >
      <Shield className="w-2.5 h-2.5" />
      Skill-Based
    </span>
  );
}
