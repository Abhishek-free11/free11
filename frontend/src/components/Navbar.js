import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Coins, Home, Zap, ShoppingBag, Package, User, LogOut, Shield } from 'lucide-react';
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

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/earn', label: 'Earn Coins', icon: Zap },
    { path: '/shop', label: 'Shop', icon: ShoppingBag },
    { path: '/orders', label: 'My Orders', icon: Package },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/dashboard')}>
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 to-amber-600 blur-lg opacity-50"></div>
              <Coins className="h-8 w-8 text-yellow-400 relative" strokeWidth={2.5} />
            </div>
            <span className="text-2xl font-black bg-gradient-to-r from-yellow-400 via-red-500 to-blue-500 bg-clip-text text-transparent">
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
                className={isActive(item.path) ? 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30' : 'text-slate-300 hover:text-white'}
              >
                <item.icon className="h-4 w-4 mr-2" />
                {item.label}
              </Button>
            ))}
          </div>

          {/* User Menu */}
          <div className="flex items-center gap-4">
            {/* Coin Balance */}
            <div className="bg-gradient-to-r from-yellow-500/20 to-amber-600/20 border border-yellow-500/30 rounded-full px-4 py-2 flex items-center gap-2">
              <Coins className="h-5 w-5 text-yellow-400" />
              <span className="font-bold text-white">{user?.coins_balance || 0}</span>
            </div>

            {/* User Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                  <Avatar>
                    <AvatarFallback className="bg-gradient-to-br from-yellow-500 to-amber-600 text-black font-bold">
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
                <DropdownMenuItem onClick={() => navigate('/admin')} className="text-slate-200 cursor-pointer">
                  <Shield className="mr-2 h-4 w-4" />
                  Admin
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-slate-800" />
                <DropdownMenuItem onClick={logout} className="text-red-400 cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Mobile Nav */}
        <div className="md:hidden flex items-center gap-1 pb-2 overflow-x-auto">
          {navItems.map((item) => (
            <Button
              key={item.path}
              variant={isActive(item.path) ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate(item.path)}
              className={isActive(item.path) ? 'bg-yellow-500/20 text-yellow-400' : 'text-slate-300'}
            >
              <item.icon className="h-4 w-4 mr-2" />
              {item.label}
            </Button>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
