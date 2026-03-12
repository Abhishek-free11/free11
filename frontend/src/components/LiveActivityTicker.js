import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Coins, ShoppingBag, Trophy, Zap } from 'lucide-react';

const CITIES = ['Mumbai', 'Delhi', 'Bengaluru', 'Chennai', 'Hyderabad', 'Kolkata', 'Pune', 'Jaipur', 'Ahmedabad', 'Lucknow'];
const NAMES = ['Rahul', 'Priya', 'Amit', 'Deepika', 'Vikas', 'Sunita', 'Arjun', 'Kavya', 'Rohit', 'Ananya', 'Sachin', 'Pooja', 'Dev', 'Riya', 'Karan'];

const ACTIVITIES = [
  (n, c) => ({ icon: Coins, color: '#C6A052', text: `${n} from ${c} earned 75 coins predicting correctly!` }),
  (n, c) => ({ icon: ShoppingBag, color: '#4ade80', text: `${n} from ${c} just redeemed Atta 5kg — FREE!` }),
  (n, c) => ({ icon: Trophy, color: '#a855f7', text: `${n} from ${c} climbed to Top 10 on the leaderboard` }),
  (n, c) => ({ icon: Coins, color: '#C6A052', text: `${n} from ${c} hit a 5-day prediction streak!` }),
  (n, c) => ({ icon: ShoppingBag, color: '#4ade80', text: `${n} from ${c} redeemed Mobile Recharge ₹10` }),
  (n, c) => ({ icon: Zap, color: '#3b82f6', text: `${n} from ${c} completed the Daily Puzzle +15 coins` }),
  (n, c) => ({ icon: Coins, color: '#C6A052', text: `${n} from ${c} earned 120 coins in last 24 hours` }),
  (n, c) => ({ icon: ShoppingBag, color: '#4ade80', text: `${n} from ${c} redeemed Cola Drink 2L — first redeem!` }),
];

function randomActivity() {
  const name = NAMES[Math.floor(Math.random() * NAMES.length)];
  const city = CITIES[Math.floor(Math.random() * CITIES.length)];
  const template = ACTIVITIES[Math.floor(Math.random() * ACTIVITIES.length)];
  return { id: Date.now() + Math.random(), ...template(name, city) };
}

export default function LiveActivityTicker({ className = '' }) {
  const [current, setCurrent] = useState(randomActivity);
  const timerRef = useRef(null);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setCurrent(randomActivity());
    }, 3500);
    return () => clearInterval(timerRef.current);
  }, []);

  const Icon = current.icon;

  return (
    <div
      className={`flex items-center gap-2.5 rounded-xl px-3 py-2 overflow-hidden ${className}`}
      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
    >
      <span className="flex items-center gap-1 shrink-0 text-[9px] font-bold uppercase tracking-widest"
        style={{ color: '#C6A052' }}>
        <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: '#4ade80' }} />
        LIVE
      </span>
      <div className="flex-1 min-w-0 overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={current.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.35 }}
            className="flex items-center gap-1.5"
          >
            <Icon className="h-3 w-3 shrink-0" style={{ color: current.color }} />
            <p className="text-xs truncate" style={{ color: '#BFC3C8' }}>{current.text}</p>
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
