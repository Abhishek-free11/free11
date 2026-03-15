/**
 * NotificationPanel — slide-in in-app notification center
 * Shows push notifications that were also stored in db.notifications
 * Covers: activation_trigger, streak_reminder, coin_expiry, match_starting, quest_available
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell, X, BellOff, Target, Flame, ShoppingBag,
  Trophy, Zap, CheckCheck, ChevronRight
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;
const POLL_MS = 30_000; // refresh every 30s when panel is open

const TYPE_META = {
  activation_trigger: { icon: Target,    color: '#C6A052', bg: 'rgba(198,160,82,0.12)' },
  streak_reminder:    { icon: Flame,     color: '#f97316', bg: 'rgba(249,115,22,0.1)'  },
  coin_expiry:        { icon: ShoppingBag, color: '#a78bfa', bg: 'rgba(167,139,250,0.1)' },
  match_starting:     { icon: Trophy,    color: '#4ade80', bg: 'rgba(74,222,128,0.1)'  },
  quest_available:    { icon: Zap,       color: '#facc15', bg: 'rgba(250,204,21,0.1)'  },
};

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)  return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

// ── Exposed hook for unread count badge ──────────────────────────────────────
export function useNotificationCount() {
  const [count, setCount] = useState(0);

  const refresh = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const res = await fetch(`${API}/api/v2/notifications`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCount(data.unread || 0);
      }
    } catch (_) {}
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 60_000); // Poll every 60s
    return () => clearInterval(id);
  }, [refresh]);

  return { count, refresh };
}

// ── Main panel ───────────────────────────────────────────────────────────────
export default function NotificationPanel({ onClose, onRead }) {
  const navigate = useNavigate();
  const [notifs, setNotifs] = useState([]);
  const [loading, setLoading] = useState(true);
  const panelRef = useRef(null);

  const load = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) return;
    try {
      const res = await fetch(`${API}/api/v2/notifications`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setNotifs(data.notifications || []);
      }
    } catch (_) {}
    setLoading(false);
  }, []);

  // Mark all read on open
  useEffect(() => {
    load();
    const markRead = async () => {
      const token = localStorage.getItem('token');
      if (!token) return;
      await fetch(`${API}/api/v2/notifications/read-all`, {
        method: 'POST', headers: { Authorization: `Bearer ${token}` },
      });
      onRead?.();
    };
    const t = setTimeout(markRead, 1200); // slight delay for visual
    const poll = setInterval(load, POLL_MS);
    return () => { clearTimeout(t); clearInterval(poll); };
  }, [load, onRead]);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  const handleNotifClick = (notif) => {
    onClose();
    if (notif.deep_link) navigate(notif.deep_link);
  };

  return (
    <motion.div
      ref={panelRef}
      initial={{ opacity: 0, x: 20, scale: 0.97 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 20, scale: 0.97 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className="absolute right-0 top-10 z-[10000] w-80 max-w-[calc(100vw-24px)] rounded-2xl overflow-hidden shadow-2xl"
      style={{
        background: '#12151A',
        border: '1px solid rgba(198,160,82,0.18)',
        boxShadow: '0 16px 48px rgba(0,0,0,0.7), 0 0 0 1px rgba(198,160,82,0.08)',
      }}
      data-testid="notification-panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Bell size={15} style={{ color: '#C6A052' }} />
          <span className="text-sm font-bold text-white">Notifications</span>
          {notifs.filter(n => !n.read).length > 0 && (
            <span className="text-[10px] font-black px-1.5 py-0.5 rounded-full"
              style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)', color: '#0F1115' }}>
              {notifs.filter(n => !n.read).length}
            </span>
          )}
        </div>
        <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/8 transition-colors"
          data-testid="close-notification-panel">
          <X size={14} style={{ color: '#8A9096' }} />
        </button>
      </div>

      {/* Body */}
      <div className="overflow-y-auto max-h-[420px]">
        {loading && (
          <div className="flex items-center justify-center py-10">
            <div className="w-5 h-5 rounded-full border-2 border-[#C6A052] border-t-transparent animate-spin" />
          </div>
        )}

        {!loading && notifs.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 gap-2">
            <BellOff size={28} style={{ color: '#3A3D42' }} />
            <p className="text-xs text-center" style={{ color: '#8A9096' }}>
              No notifications yet.<br />We'll nudge you when it matters.
            </p>
          </div>
        )}

        {!loading && notifs.map((n, i) => {
          const meta = TYPE_META[n.type] || TYPE_META['match_starting'];
          const Icon = meta.icon;
          const isUnread = !n.read;
          return (
            <motion.div
              key={n.id || i}
              initial={isUnread ? { opacity: 0, x: -8 } : false}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              onClick={() => handleNotifClick(n)}
              className="flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors border-b border-white/[0.04] last:border-0"
              style={{ background: isUnread ? 'rgba(255,255,255,0.02)' : 'transparent' }}
              data-testid={`notification-item-${n.type}`}
            >
              {/* Icon */}
              <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
                style={{ background: meta.bg }}>
                <Icon size={14} style={{ color: meta.color }} />
              </div>

              {/* Text */}
              <div className="flex-1 min-w-0">
                <p className={`text-xs font-semibold leading-tight ${isUnread ? 'text-white' : 'text-gray-300'}`}>
                  {n.title}
                </p>
                <p className="text-[11px] mt-0.5 leading-tight" style={{ color: '#8A9096' }}>
                  {n.body?.slice(0, 80)}{n.body?.length > 80 ? '…' : ''}
                </p>
                <p className="text-[10px] mt-1" style={{ color: '#5A5E64' }}>
                  {timeAgo(n.created_at)}
                </p>
              </div>

              {/* Unread dot + arrow */}
              <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                {isUnread && (
                  <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#C6A052' }} />
                )}
                {n.deep_link && (
                  <ChevronRight size={12} style={{ color: '#5A5E64' }} />
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Footer */}
      {notifs.length > 0 && (
        <div className="px-4 py-2.5 border-t border-white/5 flex items-center justify-between">
          <span className="text-[10px]" style={{ color: '#5A5E64' }}>
            {notifs.length} notification{notifs.length !== 1 ? 's' : ''}
          </span>
          <button
            onClick={onClose}
            className="flex items-center gap-1 text-[10px] font-medium"
            style={{ color: '#C6A052' }}
          >
            <CheckCheck size={11} /> All read
          </button>
        </div>
      )}
    </motion.div>
  );
}
