import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { User, Mail, Coins, Trophy, Flame, TrendingUp, Award, Wallet, Shield, Target, HelpCircle, PlayCircle, Volume2, VolumeX, Settings } from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { isSoundEnabled, setSoundEnabled } from '../utils/sounds';

const Profile = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [replayingTutorial, setReplayingTutorial] = useState(false);
  const [demandProgress, setDemandProgress] = useState(null);
  const [soundsEnabled, setSoundsEnabled] = useState(isSoundEnabled());

  const handleSoundToggle = (enabled) => {
    setSoundsEnabled(enabled);
    setSoundEnabled(enabled);
    toast.success(enabled ? 'Celebration sounds enabled' : 'Sounds disabled');
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

  const getLevelProgress = () => {
    const xp = user?.xp || 0;
    const levelThresholds = [0, 100, 500, 1500, 5000];
    const currentLevel = user?.level || 1;
    if (currentLevel >= 5) return 100;
    const currentThreshold = levelThresholds[currentLevel - 1];
    const nextThreshold = levelThresholds[currentLevel];
    return ((xp - currentThreshold) / (nextThreshold - currentThreshold)) * 100;
  };

  // Updated rank names to match Demand Rail system
  const getRankName = (level) => {
    const names = ['Rookie', 'Amateur', 'Pro', 'Expert', 'Legend'];
    return names[(level || 1) - 1] || 'Legend';
  };

  const getRankColor = (level) => {
    const colors = ['text-slate-400', 'text-green-400', 'text-blue-400', 'text-purple-400', 'text-yellow-400'];
    return colors[(level || 1) - 1] || 'text-yellow-400';
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
                <Badge className={`${getRankColor(user?.level)} bg-slate-800/50 text-lg px-4 py-2`}>
                  Level {user?.level} - {getRankName(user?.level)}
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

              {/* Skill Accuracy Badge */}
              {demandProgress?.prediction_stats && (
                <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg text-center">
                  <div className="flex items-center justify-center gap-2 mb-1">
                    <Target className="h-4 w-4 text-blue-400" />
                    <span className="text-sm text-slate-400">Skill Accuracy</span>
                  </div>
                  <p className="text-2xl font-black text-blue-400">
                    {demandProgress.prediction_stats.accuracy}%
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Stats Cards */}
          <div className="md:col-span-2 space-y-6">
            {/* Wallet Section with PRORGA Disclaimer */}
            <Card className="bg-gradient-to-br from-yellow-500/10 to-amber-600/10 border-yellow-500/30" data-testid="wallet-section">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Wallet className="h-5 w-5 text-yellow-400" />
                  My Wallet
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6 mb-6">
                  <div className="text-center p-4 bg-slate-900/50 rounded-lg">
                    <p className="text-sm text-slate-400 mb-1">Current Balance</p>
                    <p className="text-3xl font-bold text-yellow-400">{user?.coins_balance || 0}</p>
                    <p className="text-xs text-slate-500">coins</p>
                  </div>
                  <div className="text-center p-4 bg-slate-900/50 rounded-lg">
                    <p className="text-sm text-slate-400 mb-1">Total Earned</p>
                    <p className="text-3xl font-bold text-green-400">{user?.total_earned || 0}</p>
                    <p className="text-xs text-slate-500">coins</p>
                  </div>
                  <div className="text-center p-4 bg-slate-900/50 rounded-lg">
                    <p className="text-sm text-slate-400 mb-1">Consumption Unlocked</p>
                    <p className="text-3xl font-bold text-blue-400">₹{demandProgress?.consumption_unlocked || 0}</p>
                    <p className="text-xs text-slate-500">of real goods</p>
                  </div>
                </div>

                {/* PRORGA Disclaimer */}
                <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg" data-testid="coin-disclaimer">
                  <div className="flex items-start gap-3">
                    <Shield className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm text-slate-300 font-medium mb-1">About FREE11 Coins</p>
                      <p className="text-xs text-slate-400 mb-3">
                        FREE11 Coins are non-withdrawable reward tokens redeemable only for goods/services. 
                        No cash. No betting. Brand-funded rewards.
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate('/faq')}
                          className="border-blue-500/50 text-blue-400 hover:bg-blue-500/10"
                          data-testid="profile-faq-link"
                        >
                          <HelpCircle className="h-4 w-4 mr-2" />
                          View FAQ
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={replayingTutorial}
                          onClick={async () => {
                            setReplayingTutorial(true);
                            try {
                              await api.resetTutorial();
                              toast.success('Tutorial reset!', {
                                description: 'Go to Dashboard to view the tutorial again.'
                              });
                              navigate('/');
                            } catch (error) {
                              toast.error('Failed to reset tutorial');
                            } finally {
                              setReplayingTutorial(false);
                            }
                          }}
                          className="border-purple-500/50 text-purple-400 hover:bg-purple-500/10"
                          data-testid="replay-tutorial-btn"
                        >
                          <PlayCircle className="h-4 w-4 mr-2" />
                          {replayingTutorial ? 'Resetting...' : 'Replay Tutorial'}
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Skill Stats */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Target className="h-5 w-5 text-blue-400" />
                  Prediction Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-4 gap-4">
                  <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-400">
                      {demandProgress?.prediction_stats?.total || 0}
                    </p>
                    <p className="text-xs text-slate-400">Total Predictions</p>
                  </div>
                  <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-green-400">
                      {demandProgress?.prediction_stats?.correct || 0}
                    </p>
                    <p className="text-xs text-slate-400">Correct</p>
                  </div>
                  <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-400">
                      {demandProgress?.prediction_stats?.accuracy || 0}%
                    </p>
                    <p className="text-xs text-slate-400">Accuracy</p>
                  </div>
                  <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-red-400">
                      {demandProgress?.prediction_stats?.streak || 0}
                    </p>
                    <p className="text-xs text-slate-400">Current Streak</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Activity Stats */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-400" />
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

            {/* Badges */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Award className="h-5 w-5 text-yellow-400" />
                  Badges
                </CardTitle>
              </CardHeader>
              <CardContent>
                {demandProgress?.badges && demandProgress.badges.length > 0 ? (
                  <div className="grid md:grid-cols-3 gap-4">
                    {demandProgress.badges.map((badgeId) => (
                      <div key={badgeId} className="bg-slate-800/50 rounded-lg p-4 text-center">
                        <Trophy className="h-8 w-8 text-yellow-400 mx-auto mb-2" />
                        <p className="text-sm font-bold text-white capitalize">{badgeId.replace(/_/g, ' ')}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Trophy className="h-16 w-16 text-slate-700 mx-auto mb-3" />
                    <p className="text-slate-400">No badges yet. Keep predicting to earn badges!</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Settings */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Settings className="h-5 w-5 text-slate-400" />
                  Settings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Sound Settings */}
                  <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      {soundsEnabled ? (
                        <Volume2 className="h-5 w-5 text-green-400" />
                      ) : (
                        <VolumeX className="h-5 w-5 text-slate-500" />
                      )}
                      <div>
                        <p className="text-white font-medium">Celebration Sounds</p>
                        <p className="text-xs text-slate-400">
                          Play sounds on correct predictions and voucher redemptions
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={soundsEnabled}
                      onCheckedChange={handleSoundToggle}
                      data-testid="sound-toggle"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;