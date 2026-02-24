import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Coins, Home, ShoppingBag, Package, User, LogOut, Shield, Zap, Target, Users, Trophy, MessageCircle, Spade } from 'lucide-react';
import LanguageSelector from './LanguageSelector';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // New navigation structure - Contests first!
  const navItems = [
    { path: '/contests', label: 'Contests', icon: Trophy, highlight: true }, // Dream11-style - PRIMARY
    { path: '/cricket', label: 'Predict', icon: Target }, // Ball-by-ball predictions
    { path: '/games', label: 'Cards', icon: Spade }, // Card Games
    { path: '/leaderboards', label: 'Ranks', icon: Users }, // Leaderboards
    { path: '/profile', label: 'Profile', icon: User }, // Profile with logout
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="border-b border-slate-700 bg-slate-900/95 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-2 sm:px-4">
        {/* Top bar */}
        <div className="flex items-center justify-between h-14 sm:h-16">
          {/* Logo */}
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/contests')}>
            <img 
              src="/app-icon.png" 
              alt="FREE11" 
              className="h-8 w-8 sm:h-10 sm:w-10 rounded-lg"
            />
            <span className="text-xl sm:text-2xl font-black bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
              FREE11
            </span>
          </div>

          {/* Nav Items - Desktop */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              <Button
                key={item.path}
                variant={isActive(item.path) ? 'default' : 'ghost'}
                onClick={() => navigate(item.path)}
                className={
                  isActive(item.path) 
                    ? 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30' 
                    : item.highlight 
                      ? 'text-red-400 hover:text-red-300 hover:bg-red-500/10' 
                      : 'text-slate-300 hover:text-white'
                }
              >
                {item.path === '/cricket' ? (
                  <span className="text-lg mr-1">🏏</span>
                ) : (
                  <item.icon className="h-4 w-4 mr-2" />
                )}
                {item.label}
              </Button>
            ))}
          </div>

          {/* User Menu - Compact on mobile */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Language Selector - Hide on small mobile */}
            <div className="hidden sm:block">
              <LanguageSelector variant="ghost" />
            </div>
            
            {/* Coin Balance */}
            <div className="bg-gradient-to-r from-yellow-500/20 to-amber-600/20 border border-yellow-500/30 rounded-full px-3 sm:px-4 py-1.5 sm:py-2 flex items-center gap-1.5 sm:gap-2">
              <Coins className="h-4 w-4 sm:h-5 sm:w-5 text-yellow-400" />
              <span className="font-bold text-white text-sm sm:text-base">{user?.coins_balance || 0}</span>
            </div>

            {/* User Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-8 w-8 sm:h-10 sm:w-10 rounded-full p-0">
                  <Avatar className="h-8 w-8 sm:h-10 sm:w-10">
                    <AvatarFallback className="bg-gradient-to-br from-yellow-500 to-amber-600 text-black font-bold text-sm sm:text-base">
                      {user?.name?.[0]?.toUpperCase() || 'U'}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56 bg-slate-900 border-slate-800" align="end">
                <DropdownMenuLabel className="text-slate-200">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{user?.name}</p>
                    <p className="text-xs text-slate-400">{user?.email}</p>
                    <p className="text-xs text-yellow-400">Level {user?.level || 1}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-slate-800" />
                <DropdownMenuItem onClick={() => navigate('/profile')} className="text-slate-200 cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/support')} className="text-slate-200 cursor-pointer">
                  <MessageCircle className="mr-2 h-4 w-4" />
                  Help & Support
                </DropdownMenuItem>
                {user?.is_admin && (
                  <DropdownMenuItem onClick={() => navigate('/admin')} className="text-green-400 cursor-pointer">
                    <Shield className="mr-2 h-4 w-4" />
                    Beta Dashboard
                  </DropdownMenuItem>
                )}
                <DropdownMenuSeparator className="bg-slate-800" />
                <DropdownMenuItem onClick={logout} className="text-red-400 cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Mobile Nav - Bottom fixed tabs */}
        <div className="md:hidden fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-700 z-50 safe-area-bottom">
          <div className="flex items-center justify-around py-2 px-1">
            {navItems.map((item) => (
              <Button
                key={item.path}
                variant="ghost"
                size="sm"
                onClick={() => navigate(item.path)}
                className={`flex-col h-auto py-1.5 px-3 gap-0.5 ${
                  isActive(item.path) 
                    ? 'text-yellow-400 bg-yellow-500/15' 
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                <item.icon className={`h-5 w-5 ${item.highlight && !isActive(item.path) ? 'text-yellow-500' : ''}`} />
                <span className="text-[10px] font-medium">{item.label}</span>
              </Button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
