import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Coins, Zap, Gift, Trophy, TrendingUp, Calendar, Flame } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const Dashboard = () => {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [checkinLoading, setCheckinLoading] = useState(false);
  const [canCheckin, setCanCheckin] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    // Check if already checked in today
    const today = new Date().toISOString().split('T')[0];
    const lastCheckin = user?.last_checkin;
    setCanCheckin(lastCheckin !== today);
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, transactionsRes, leaderboardRes] = await Promise.all([
        api.getUserStats(),
        api.getTransactions(),
        api.getLeaderboard()
      ]);
      setStats(statsRes.data);
      setTransactions(transactionsRes.data.slice(0, 5));
      setLeaderboard(leaderboardRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const handleCheckin = async () => {
    setCheckinLoading(true);
    try {
      const response = await api.dailyCheckin();
      toast.success(`🎉 ${response.data.message}`, {
        description: `Streak: ${response.data.streak_days} days | +${response.data.coins_earned} coins`
      });
      updateUser({ 
        coins_balance: response.data.new_balance,
        streak_days: response.data.streak_days,
        last_checkin: new Date().toISOString().split('T')[0]
      });
      setCanCheckin(false);
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Check-in failed');
    } finally {
      setCheckinLoading(false);
    }
  };

  const getLevelProgress = () => {
    const xp = user?.xp || 0;
    const levelThresholds = [0, 100, 500, 1500, 5000];
    const currentLevel = user?.level || 1;
    if (currentLevel >= 5) return 100;
    const currentThreshold = levelThresholds[currentLevel - 1];
    const nextThreshold = levelThresholds[currentLevel];
    return ((xp - currentThreshold) / (nextThreshold - currentThreshold)) * 100;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-4 py-8" data-testid="dashboard-page">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-4xl font-black text-white mb-2">Welcome back, {user?.name}! 👋</h1>
          <p className="text-slate-400">Here's what's happening with your FREE11 account</p>
        </div>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-gradient-to-br from-yellow-500/20 to-amber-600/20 border-yellow-500/30" data-testid="coin-balance-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-yellow-200">Coin Balance</CardTitle>
              <Coins className="h-4 w-4 text-yellow-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-400">{user?.coins_balance || 0}</div>
              <p className="text-xs text-yellow-200/70 mt-1">Total earned: {user?.total_earned || 0}</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-blue-500/20 to-cyan-600/20 border-blue-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-blue-200">Level</CardTitle>
              <Trophy className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-400">Level {user?.level || 1}</div>
              <Progress value={getLevelProgress()} className="mt-2 h-2" />
              <p className="text-xs text-blue-200/70 mt-1">{user?.xp || 0} XP</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-red-500/20 to-pink-600/20 border-red-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-red-200">Streak</CardTitle>
              <Flame className="h-4 w-4 text-red-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-400">{user?.streak_days || 0} Days</div>
              <p className="text-xs text-red-200/70 mt-1">Keep it going!</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500/20 to-emerald-600/20 border-green-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-green-200">Redeemed</CardTitle>
              <Gift className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-400">{stats?.redemptions_count || 0}</div>
              <p className="text-xs text-green-200/70 mt-1">{user?.total_redeemed || 0} coins spent</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {/* Daily Check-in */}
          <Card className="bg-slate-900/50 border-slate-800 md:col-span-2" data-testid="checkin-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-white">
                <Calendar className="h-5 w-5 text-yellow-400" />
                Daily Check-in
              </CardTitle>
              <CardDescription className="text-slate-400">
                Maintain your streak and earn bonus coins
              </CardDescription>
            </CardHeader>
            <CardContent>
              {canCheckin ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                    <div>
                      <p className="font-bold text-white">Check in now!</p>
                      <p className="text-sm text-slate-400">Earn coins and extend your streak</p>
                    </div>
                    <Button
                      onClick={handleCheckin}
                      disabled={checkinLoading}
                      className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
                      data-testid="checkin-btn"
                    >
                      {checkinLoading ? 'Checking in...' : 'Check In'}
                    </Button>
                  </div>
                  <div className="flex items-center gap-2">
                    <Flame className="h-5 w-5 text-red-400" />
                    <span className="text-sm text-slate-300">Current Streak: <span className="font-bold text-red-400">{user?.streak_days || 0} days</span></span>
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="flex items-center gap-2 text-green-400 mb-2">
                    <Coins className="h-5 w-5" />
                    <span className="font-bold">Already checked in today! ✓</span>
                  </div>
                  <p className="text-sm text-slate-400">Come back tomorrow to continue your streak</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={() => navigate('/earn')}
                className="w-full justify-start bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 border border-yellow-500/30"
                data-testid="earn-coins-btn"
              >
                <Zap className="mr-2 h-4 w-4" />
                Earn More Coins
              </Button>
              <Button
                onClick={() => navigate('/shop')}
                className="w-full justify-start bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 border border-blue-500/30"
                data-testid="browse-shop-btn"
              >
                <Gift className="mr-2 h-4 w-4" />
                Browse Shop
              </Button>
              <Button
                onClick={() => navigate('/orders')}
                className="w-full justify-start bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30"
              >
                <TrendingUp className="mr-2 h-4 w-4" />
                My Orders
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Recent Transactions */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white">Recent Transactions</CardTitle>
              <CardDescription className="text-slate-400">Your latest coin activities</CardDescription>
            </CardHeader>
            <CardContent>
              {transactions.length > 0 ? (
                <div className="space-y-3">
                  {transactions.map((tx) => (
                    <div key={tx.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">{tx.description}</p>
                        <p className="text-xs text-slate-400">
                          {new Date(tx.timestamp).toLocaleDateString()}
                        </p>
                      </div>
                      <Badge
                        variant={tx.amount > 0 ? 'default' : 'destructive'}
                        className={tx.amount > 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}
                      >
                        {tx.amount > 0 ? '+' : ''}{tx.amount}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-400 py-8">No transactions yet</p>
              )}
            </CardContent>
          </Card>

          {/* Leaderboard */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-400" />
                Leaderboard
              </CardTitle>
              <CardDescription className="text-slate-400">Top earners this month</CardDescription>
            </CardHeader>
            <CardContent>
              {leaderboard.length > 0 ? (
                <div className="space-y-3">
                  {leaderboard.map((player, index) => (
                    <div key={player.id} className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                        index === 0 ? 'bg-yellow-500 text-black' :
                        index === 1 ? 'bg-slate-400 text-black' :
                        index === 2 ? 'bg-amber-700 text-white' :
                        'bg-slate-700 text-slate-300'
                      }`}>
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">{player.name}</p>
                        <p className="text-xs text-slate-400">Level {player.level}</p>
                      </div>
                      <Badge className="bg-yellow-500/20 text-yellow-400">
                        {player.total_earned} coins
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-400 py-8">No data yet</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
