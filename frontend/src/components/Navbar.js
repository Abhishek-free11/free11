import React, { useState, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { AnimatePresence } from 'framer-motion';
import {
  Coins, User, Search, Home, Target, ShoppingBag, Bell, Club, Sparkles
} from 'lucide-react';
import AppSearch from './AppSearch';
import { trackButtonClick } from '../utils/analytics';
import NotificationPanel, { useNotificationCount } from './NotificationPanel';

// Bottom nav — 5 tabs (original structure restored)
const BOTTOM_NAV = [
  { path: '/match-centre', label: 'Home',     icon: Home      },
  { path: '/predict',      label: 'Play',      icon: Target    },
  { path: '/games',        label: 'Games',     icon: Club      },
  { path: '/earn',         label: 'Missions',  icon: Sparkles  },
  { path: '/profile',      label: 'Profile',   icon: User      },
];

const Navbar = () => {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchOpen, setSearchOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const { count: unreadCount, refresh: refreshCount } = useNotificationCount();

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <>
      {/* ─── TOP BAR ─── */}
      <nav
        className="sticky top-0 z-50 border-b"
        style={{
          background: 'rgba(15, 17, 21, 0.92)',
          borderColor: 'rgba(198, 160, 82, 0.12)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
        }}
        data-testid="top-navbar"
      >
        <div className="flex items-center justify-between h-14 px-3 max-w-screen-xl mx-auto">

          {/* Logo */}
          <button
            className="flex items-center gap-2 cursor-pointer flex-shrink-0"
            onClick={() => navigate('/match-centre')}
            data-testid="navbar-logo"
          >
            <img src="/free11_icon_192.png" alt="FREE11" className="h-8 w-8 rounded-xl animate-coin-glow" />
            <span className="text-xl font-heading tracking-widest hidden sm:inline" style={{ color: '#C6A052', letterSpacing: '0.12em' }}>
              FREE11
            </span>
          </button>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {BOTTOM_NAV.map((item) => (
              <button key={item.path} onClick={() => navigate(item.path)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
                style={isActive(item.path) ? { color: '#C6A052' } : { color: '#8A9096' }}>
                <item.icon className="h-4 w-4" />
                {item.label}
              </button>
            ))}
          </div>

          {/* Right: icon buttons */}
          <div className="flex items-center gap-1">
            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => { setNotifOpen(o => !o); trackButtonClick('notification_bell'); }}
                className="flex flex-col items-center justify-center h-10 w-11 rounded-xl transition-all relative"
                style={{ background: notifOpen ? 'rgba(198,160,82,0.12)' : 'transparent' }}
                data-testid="notification-bell-btn"
                aria-label="Notifications"
              >
                <Bell className="h-4 w-4" style={{ color: notifOpen ? '#C6A052' : '#8A9096' }} />
                <span className="text-[9px] mt-0.5 font-medium" style={{ color: notifOpen ? '#C6A052' : '#8A9096' }}>Alerts</span>
                {unreadCount > 0 && (
                  <span
                    className="absolute top-1.5 right-1.5 min-w-[14px] h-[14px] rounded-full text-[9px] font-black flex items-center justify-center px-0.5"
                    style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)', color: '#0F1115' }}
                    data-testid="notification-badge"
                  >
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>
              <AnimatePresence>
                {notifOpen && (
                  <NotificationPanel
                    onClose={() => setNotifOpen(false)}
                    onRead={() => refreshCount()}
                  />
                )}
              </AnimatePresence>
            </div>

            {/* Shop */}
            <button onClick={() => navigate('/shop')}
              className="flex flex-col items-center justify-center h-10 w-11 rounded-xl transition-all"
              style={{ background: isActive('/shop') ? 'rgba(198,160,82,0.12)' : 'transparent' }}
              data-testid="shop-btn">
              <ShoppingBag className="h-4 w-4" style={{ color: isActive('/shop') ? '#C6A052' : '#8A9096' }} />
              <span className="text-[9px] mt-0.5 font-medium" style={{ color: isActive('/shop') ? '#C6A052' : '#8A9096' }}>Shop</span>
            </button>

            {/* Search */}
            <button onClick={() => setSearchOpen(true)}
              className="flex flex-col items-center justify-center h-10 w-11 rounded-xl transition-all"
              data-testid="search-btn">
              <Search className="h-4 w-4" style={{ color: '#8A9096' }} />
              <span className="text-[9px] mt-0.5 font-medium" style={{ color: '#8A9096' }}>Search</span>
            </button>

            {/* Wallet */}
            <button onClick={() => navigate('/ledger')}
              className="flex flex-col items-center justify-center h-10 w-11 rounded-xl transition-all"
              style={{ background: isActive('/ledger') ? 'rgba(198,160,82,0.12)' : 'transparent' }}
              data-testid="wallet-btn">
              <Coins className="h-4 w-4" style={{ color: isActive('/ledger') ? '#C6A052' : '#8A9096' }} />
              <span className="text-[9px] mt-0.5 font-medium" style={{ color: isActive('/ledger') ? '#C6A052' : '#8A9096' }}>Wallet</span>
            </button>

            {/* Coin Balance Pill */}
            {user && (
              <button className="coin-indicator flex items-center gap-1 px-2.5 py-1 transition-all"
                onClick={() => navigate('/ledger')} data-testid="coin-balance-display">
                <Coins className="h-3.5 w-3.5 animate-coin-glow" />
                <span className="font-numbers font-semibold text-xs">{user.coins_balance || 0}</span>
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* ─── MOBILE BOTTOM NAV ─── */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-[9999]"
        style={{ background: 'rgba(15, 17, 21, 0.97)', borderTop: '1px solid rgba(198, 160, 82, 0.12)', backdropFilter: 'blur(20px)', paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
        data-testid="bottom-navbar">
        <div className="flex items-center justify-around py-2 px-1">
          {BOTTOM_NAV.map((item) => {
            const active = isActive(item.path);
            return (
              <button key={item.path}
                onClick={() => { navigate(item.path); trackButtonClick(`bottom_nav_${item.label.toLowerCase()}`); }}
                className="flex flex-col items-center py-1 px-3 rounded-xl transition-all relative"
                style={{ minWidth: 52 }}
                data-testid={`bottom-nav-${item.label.toLowerCase()}`}>
                {item.label === 'Games' && !active && (
                  <span className="absolute top-0.5 right-1.5 text-[8px] font-black px-1 rounded-full animate-live-pulse"
                    style={{ background: '#C6A052', color: '#0F1115' }}>NEW</span>
                )}
                <div className="flex items-center justify-center h-7 w-7 rounded-lg mb-0.5 transition-all"
                  style={{ background: active ? 'rgba(198,160,82,0.15)' : 'transparent' }}>
                  <item.icon className="h-5 w-5 transition-all"
                    style={{ color: active ? '#C6A052' : '#8A9096' }} strokeWidth={active ? 2 : 1.5} />
                </div>
                <span className="text-[10px] font-medium transition-all" style={{ color: active ? '#C6A052' : '#8A9096' }}>
                  {item.label}
                </span>
                {active && <div className="h-0.5 w-4 rounded-full mt-0.5" style={{ background: '#C6A052', boxShadow: '0 0 6px rgba(198,160,82,0.6)' }} />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Search Overlay */}
      <AppSearch isOpen={searchOpen} onClose={() => setSearchOpen(false)} />
    </>
  );
};

export default Navbar;


