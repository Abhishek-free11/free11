import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { 
  User, Mail, Coins, Trophy, TrendingUp, Award, Shield, Target, 
  HelpCircle, Volume2, VolumeX, Settings, LogOut, ChevronRight,
  ShoppingBag, Zap, Gift, History, Star
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { isSoundEnabled, setSoundEnabled } from '../utils/sounds';

const Profile = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [demandProgress, setDemandProgress] = useState(null);
  const [soundsEnabled, setSoundsEnabled] = useState(isSoundEnabled());

  const handleSoundToggle = (enabled) => {
    setSoundsEnabled(enabled);
    setSoundEnabled(enabled);
    toast.success(enabled ? 'Sounds enabled' : 'Sounds disabled');
  };

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  useEffect(() => {
    fetchStats();
    fetchDemandProgress();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.getUserStats();
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchDemandProgress = async () => {
    try {
      const response = await api.getDemandProgress();
      setDemandProgress(response.data);
    } catch (error) {
      console.error('Error fetching demand progress:', error);
    }
  };

  const getRankName = (level) => {
    const names = ['Rookie', 'Amateur', 'Pro', 'Expert', 'Legend'];
    return names[(level || 1) - 1] || 'Legend';
  };

  const getRankColor = (level) => {
    const colors = ['bg-slate-500', 'bg-green-500', 'bg-blue-500', 'bg-purple-500', 'bg-yellow-500'];
    return colors[(level || 1) - 1] || 'bg-yellow-500';
  };

  const menuItems = [
    { label: 'My Orders', icon: ShoppingBag, path: '/orders', color: 'text-green-400' },
    { label: 'Earn Coins', icon: Zap, path: '/earn', color: 'text-yellow-400' },
    { label: 'Redeem Shop', icon: Gift, path: '/shop', color: 'text-pink-400' },
    { label: 'Transaction History', icon: History, path: '/orders', color: 'text-blue-400' },
    { label: 'Help & Support', icon: HelpCircle, path: '/support', color: 'text-purple-400' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 pb-20 md:pb-0">
      <Navbar />
      <div className="container mx-auto px-4 py-6 max-w-lg" data-testid="profile-page">
        
        {/* Profile Header Card */}
        <Card className="bg-gradient-to-br from-slate-800 to-slate-900 border-slate-700 mb-4 overflow-hidden">
          <div className="h-20 bg-gradient-to-r from-yellow-500/20 via-orange-500/20 to-red-500/20" />
          <CardContent className="pt-0 -mt-10">
            <div className="flex items-end gap-4 mb-4">
              <div className={`w-20 h-20 rounded-2xl ${getRankColor(user?.level)} flex items-center justify-center text-3xl font-black text-white shadow-lg border-4 border-slate-800`}>
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className="flex-1 pb-1">
                <h2 className="text-xl font-bold text-white">{user?.name || 'User'}</h2>
                <p className="text-slate-400 text-sm">{user?.email}</p>
              </div>
            </div>
            
            {/* Level & Rank */}
            <div className="flex items-center justify-between bg-slate-900/50 rounded-xl p-3 mb-3">
              <div className="flex items-center gap-2">
                <Star className="h-5 w-5 text-yellow-400" />
                <span className="text-white font-medium">{getRankName(user?.level)}</span>
                <Badge className="bg-yellow-500/20 text-yellow-400 text-xs">Level {user?.level || 1}</Badge>
              </div>
              <span className="text-slate-400 text-sm">{user?.xp || 0} XP</span>
            </div>
            
            {/* XP Progress */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Progress to next level</span>
                <span className="text-yellow-400">
                  {demandProgress?.rank?.xp_to_next ? `${demandProgress.rank.xp_to_next} XP needed` : 'Max Level'}
                </span>
              </div>
              <Progress value={demandProgress?.rank?.progress || 0} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* Coins Card */}
        <Card className="bg-gradient-to-r from-yellow-500/10 to-amber-500/10 border-yellow-500/30 mb-4">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-yellow-500/20 rounded-xl">
                  <Coins className="h-6 w-6 text-yellow-400" />
                </div>
                <div>
                  <p className="text-slate-400 text-sm">Your Balance</p>
                  <p className="text-2xl font-black text-yellow-400">{user?.coins_balance || 0} <span className="text-sm font-normal">coins</span></p>
                </div>
              </div>
              <Button 
                onClick={() => navigate('/shop')}
                className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold"
              >
                Redeem
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Stats Card */}
        <Card className="bg-slate-800/50 border-slate-700 mb-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <Trophy className="h-5 w-5 text-yellow-400" />
              Your Stats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-3 bg-slate-900/50 rounded-xl">
                <p className="text-2xl font-bold text-white">{stats?.total_predictions || 0}</p>
                <p className="text-xs text-slate-400">Predictions</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded-xl">
                <p className="text-2xl font-bold text-green-400">{stats?.accuracy || 0}%</p>
                <p className="text-xs text-slate-400">Accuracy</p>
              </div>
              <div className="text-center p-3 bg-slate-900/50 rounded-xl">
                <p className="text-2xl font-bold text-yellow-400">{user?.total_earned || 0}</p>
                <p className="text-xs text-slate-400">Total Earned</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Menu Items */}
        <Card className="bg-slate-800/50 border-slate-700 mb-4">
          <CardContent className="p-2">
            {menuItems.map((item, index) => (
              <button
                key={item.label}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center justify-between p-3 rounded-xl hover:bg-slate-700/50 transition-colors ${
                  index !== menuItems.length - 1 ? 'border-b border-slate-700/50' : ''
                }`}
              >
                <div className="flex items-center gap-3">
                  <item.icon className={`h-5 w-5 ${item.color}`} />
                  <span className="text-white font-medium">{item.label}</span>
                </div>
                <ChevronRight className="h-5 w-5 text-slate-500" />
              </button>
            ))}
          </CardContent>
        </Card>

        {/* Settings Card */}
        <Card className="bg-slate-800/50 border-slate-700 mb-4">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base flex items-center gap-2">
              <Settings className="h-5 w-5 text-slate-400" />
              Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* Sound Toggle */}
            <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-xl">
              <div className="flex items-center gap-3">
                {soundsEnabled ? (
                  <Volume2 className="h-5 w-5 text-green-400" />
                ) : (
                  <VolumeX className="h-5 w-5 text-slate-500" />
                )}
                <span className="text-white">Sound Effects</span>
              </div>
              <Switch
                checked={soundsEnabled}
                onCheckedChange={handleSoundToggle}
              />
            </div>
            
            {/* Admin Panel (if admin) */}
            {user?.is_admin && (
              <button
                onClick={() => navigate('/admin')}
                className="w-full flex items-center justify-between p-3 bg-green-500/10 rounded-xl hover:bg-green-500/20 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-green-400" />
                  <span className="text-green-400 font-medium">Admin Dashboard</span>
                </div>
                <ChevronRight className="h-5 w-5 text-green-400" />
              </button>
            )}
          </CardContent>
        </Card>

        {/* Logout Button */}
        <Button
          onClick={handleLogout}
          variant="outline"
          className="w-full h-12 border-red-500/50 text-red-400 hover:bg-red-500/10 hover:text-red-300 font-bold"
          data-testid="logout-btn"
        >
          <LogOut className="h-5 w-5 mr-2" />
          Log Out
        </Button>

        {/* App Version */}
        <p className="text-center text-slate-600 text-xs mt-4">FREE11 Beta v1.0</p>
      </div>
    </div>
  );
};

export default Profile;
