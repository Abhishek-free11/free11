import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { User, Mail, Coins, Trophy, Flame, TrendingUp, Award } from 'lucide-react';
import api from '../utils/api';

const Profile = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await api.getUserStats();
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
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

  const getLevelName = (level) => {
    const names = ['Newbie', 'Bronze', 'Silver', 'Gold', 'Diamond'];
    return names[level - 1] || 'Diamond';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-4 py-8" data-testid="profile-page">
        <div className="mb-8">
          <h1 className="text-4xl font-black text-white mb-2">My Profile 👤</h1>
          <p className="text-slate-400">View your stats and achievements</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {/* Profile Card */}
          <Card className="bg-slate-900/50 border-slate-800 md:col-span-1">
            <CardHeader>
              <div className="flex items-center justify-center mb-4">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-yellow-500 to-amber-600 flex items-center justify-center">
                  <span className="text-4xl font-black text-black">
                    {user?.name?.[0]?.toUpperCase()}
                  </span>
                </div>
              </div>
              <CardTitle className="text-center text-white text-2xl">{user?.name}</CardTitle>
              <CardDescription className="text-center text-slate-400">{user?.email}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center">
                <Badge className="bg-blue-500/20 text-blue-400 text-lg px-4 py-2">
                  Level {user?.level} - {getLevelName(user?.level)}
                </Badge>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Progress to next level</span>
                  <span className="text-white font-bold">{Math.round(getLevelProgress())}%</span>
                </div>
                <Progress value={getLevelProgress()} className="h-2" />
                <p className="text-xs text-slate-400 text-center">{user?.xp || 0} XP</p>
              </div>
            </CardContent>
          </Card>

          {/* Stats Cards */}
          <div className="md:col-span-2 space-y-6">
            {/* Coin Stats */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Coins className="h-5 w-5 text-yellow-400" />
                  Coin Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Current Balance</p>
                    <p className="text-3xl font-bold text-yellow-400">{user?.coins_balance || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Total Earned</p>
                    <p className="text-3xl font-bold text-green-400">{user?.total_earned || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Total Redeemed</p>
                    <p className="text-3xl font-bold text-red-400">{user?.total_redeemed || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Activity Stats */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-blue-400" />
                  Activity Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Streak Days</p>
                    <div className="flex items-center gap-2">
                      <Flame className="h-6 w-6 text-red-400" />
                      <p className="text-3xl font-bold text-white">{user?.streak_days || 0}</p>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Activities Completed</p>
                    <p className="text-3xl font-bold text-white">{stats?.activities_count || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm text-slate-400 mb-1">Products Redeemed</p>
                    <p className="text-3xl font-bold text-white">{stats?.redemptions_count || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Achievements */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Award className="h-5 w-5 text-yellow-400" />
                  Achievements
                </CardTitle>
              </CardHeader>
              <CardContent>
                {stats?.achievements && stats.achievements.length > 0 ? (
                  <div className="grid md:grid-cols-2 gap-4">
                    {stats.achievements.map((achievement) => (
                      <div key={achievement.id} className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-start gap-3">
                          <Trophy className="h-8 w-8 text-yellow-400 flex-shrink-0" />
                          <div>
                            <h4 className="font-bold text-white">{achievement.title}</h4>
                            <p className="text-sm text-slate-400">{achievement.description}</p>
                            <p className="text-xs text-slate-500 mt-1">
                              {new Date(achievement.earned_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Trophy className="h-16 w-16 text-slate-700 mx-auto mb-3" />
                    <p className="text-slate-400">No achievements yet. Keep earning!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;