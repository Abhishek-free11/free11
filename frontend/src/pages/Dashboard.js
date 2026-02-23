import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import FirstTimeTutorial from '../components/FirstTimeTutorial';
import EmptyState from '../components/EmptyState';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Coins, Zap, Gift, Trophy, TrendingUp, Calendar, Flame, 
  Target, ShoppingBag, Award, ChevronRight, Star, Tv, Play
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { playCelebrationSound } from '../utils/sounds';
import confetti from 'canvas-confetti';

// Rank colors
const RANK_COLORS = {
  1: { bg: 'from-slate-500/20 to-slate-600/20', border: 'border-slate-500/30', text: 'text-slate-400' },
  2: { bg: 'from-green-500/20 to-emerald-600/20', border: 'border-green-500/30', text: 'text-green-400' },
  3: { bg: 'from-blue-500/20 to-cyan-600/20', border: 'border-blue-500/30', text: 'text-blue-400' },
  4: { bg: 'from-purple-500/20 to-violet-600/20', border: 'border-purple-500/30', text: 'text-purple-400' },
  5: { bg: 'from-yellow-500/20 to-amber-600/20', border: 'border-yellow-500/30', text: 'text-yellow-400' },
};

const Dashboard = () => {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const [demandProgress, setDemandProgress] = useState(null);
  const [liveMatch, setLiveMatch] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [checkinLoading, setCheckinLoading] = useState(false);
  const [canCheckin, setCanCheckin] = useState(true);
  const [loading, setLoading] = useState(true);
  const [showTutorial, setShowTutorial] = useState(false);
  const [isFirstTimeUser, setIsFirstTimeUser] = useState(false);

  // Check tutorial status on mount
  useEffect(() => {
    const checkTutorialStatus = async () => {
      try {
        const response = await api.getTutorialStatus();
        if (!response.data.tutorial_completed) {
          setShowTutorial(true);
          setIsFirstTimeUser(true);
        }
      } catch (error) {
        console.error('Error checking tutorial status:', error);
      }
    };
    checkTutorialStatus();
  }, []);

  const handleTutorialComplete = async () => {
    try {
      await api.completeTutorial();
      setShowTutorial(false);
      toast.success('Welcome to FREE11! 🎉', {
        description: 'Start predicting to earn coins and unlock real rewards.'
      });
    } catch (error) {
      console.error('Error completing tutorial:', error);
      setShowTutorial(false);
    }
  };

  const handleTutorialSkip = async () => {
    try {
      await api.completeTutorial();
      setShowTutorial(false);
    } catch (error) {
      console.error('Error skipping tutorial:', error);
      setShowTutorial(false);
    }
  };

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [progressRes, transactionsRes, leaderboardRes, matchesRes] = await Promise.all([
        api.getDemandProgress(),
        api.getTransactions(),
        api.getLeaderboard(),
        api.getLiveMatches()
      ]);
      setDemandProgress(progressRes.data);
      setTransactions(transactionsRes.data.slice(0, 5));
      setLeaderboard(leaderboardRes.data);
      if (matchesRes.data.length > 0) {
        setLiveMatch(matchesRes.data[0]);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    const lastCheckin = user?.last_checkin;
    setCanCheckin(lastCheckin !== today);
  }, [user]);

  const handleCheckin = async () => {
    setCheckinLoading(true);
    try {
      const response = await api.dailyCheckin();
      playCelebrationSound();
      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
      toast.success(`${response.data.message}`, {
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

  const rankStyle = RANK_COLORS[user?.level || 1];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* First-Time Tutorial */}
      {showTutorial && (
        <FirstTimeTutorial 
          onComplete={handleTutorialComplete} 
          onSkip={handleTutorialSkip} 
        />
      )}
      
      <Navbar />
      <div className="container mx-auto px-4 py-6" data-testid="dashboard-page">
        
        {/* Beta Program Banner */}
        <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">🧪</span>
              <div>
                <p className="text-yellow-400 font-medium text-sm">You're in the FREE11 Beta</p>
                <p className="text-slate-400 text-xs">
                  Thanks for testing early! Things may break. 
                  <a href="/support" className="text-blue-400 hover:underline ml-1">Report issues →</a>
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* PRORGA Disclaimer Banner */}
        <div className="mb-6 p-3 bg-slate-800/50 border border-slate-700 rounded-lg text-center">
          <p className="text-xs text-slate-400">
            <span className="text-yellow-400 font-medium">FREE11 Coins</span> are non-withdrawable reward tokens redeemable only for goods/services. 
            No cash. No betting. Brand-funded rewards.
          </p>
        </div>
        
        {/* Brand Voice Line */}
        <div className="mb-6 text-center">
          <p className="text-slate-500 text-sm font-medium tracking-wide">
            <span className="text-yellow-400/80">Skill beats luck here.</span>
          </p>
        </div>

        {/* Welcome + Demand Progress Header */}
        <div className="grid lg:grid-cols-3 gap-6 mb-6">
          {/* Welcome Card */}
          <Card className={`bg-gradient-to-br ${rankStyle.bg} ${rankStyle.border} lg:col-span-1`}>
            <CardContent className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl font-black ${rankStyle.text} bg-slate-900/50`}>
                  {demandProgress?.rank?.name?.[0] || 'R'}
                </div>
                <div>
                  <h2 className="text-2xl font-black text-white">{user?.name}</h2>
                  <Badge className={`${rankStyle.text} bg-slate-900/50`}>
                    {demandProgress?.rank?.name || 'Rookie'} • Level {user?.level || 1}
                  </Badge>
                </div>
              </div>
              {demandProgress?.rank?.next_rank && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Progress to {demandProgress.rank.next_rank}</span>
                    <span className={rankStyle.text}>{user?.xp || 0} XP</span>
                  </div>
                  <Progress value={((user?.xp || 0) / (demandProgress.rank.xp_to_next + (user?.xp || 0))) * 100} className="h-2" />
                </div>
              )}
            </CardContent>
          </Card>

          {/* ENHANCED: Demand Progress - Next Reward (More Prominent) */}
          <Card className="bg-gradient-to-br from-green-500/10 via-emerald-500/5 to-teal-500/10 border-2 border-green-500/40 lg:col-span-2 shadow-lg shadow-green-500/10">
            <CardContent className="p-6">
              {/* Header with coins balance prominently displayed */}
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-black text-white flex items-center gap-2">
                    <div className="p-2 bg-green-500/20 rounded-lg">
                      <Target className="h-6 w-6 text-green-400" />
                    </div>
                    Progress to Next Reward
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">Unlock real goods through skill</p>
                </div>
                <div className="text-right bg-slate-900/50 px-4 py-3 rounded-xl border border-yellow-500/20">
                  <p className="text-4xl font-black text-yellow-400">{user?.coins_balance || 0}</p>
                  <p className="text-xs text-slate-400">coins available</p>
                </div>
              </div>
              
              {demandProgress?.next_reward ? (
                <div className="bg-slate-900/60 rounded-xl p-5 border border-slate-700/50">
                  <div className="flex items-center gap-5">
                    <div className="relative">
                      <img 
                        src={demandProgress.next_reward.image_url} 
                        alt={demandProgress.next_reward.name}
                        className="w-20 h-20 rounded-xl object-cover border-2 border-green-500/30"
                        onError={(e) => e.target.src = 'https://via.placeholder.com/80'}
                      />
                      {demandProgress.next_reward.progress >= 100 && (
                        <div className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full font-bold animate-bounce">
                          Ready!
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <p className="font-bold text-white text-lg">{demandProgress.next_reward.name}</p>
                        {/* Milestone badges */}
                        {demandProgress.next_reward.progress >= 50 && demandProgress.next_reward.progress < 80 && (
                          <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full">
                            Halfway there!
                          </span>
                        )}
                        {demandProgress.next_reward.progress >= 80 && demandProgress.next_reward.progress < 100 && (
                          <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full animate-pulse">
                            Almost unlocked!
                          </span>
                        )}
                        {demandProgress.next_reward.progress >= 100 && (
                          <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">
                            Ready to claim! 🎉
                          </span>
                        )}
                      </div>
                      
                      {/* Enhanced Progress Bar */}
                      <div className="relative mb-2">
                        <div className="h-4 bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className={`h-full rounded-full transition-all duration-500 ease-out relative ${
                              demandProgress.next_reward.progress >= 100 
                                ? 'bg-gradient-to-r from-green-400 to-emerald-300 animate-pulse' 
                                : 'bg-gradient-to-r from-green-500 to-emerald-400'
                            }`}
                            style={{ width: `${Math.min(demandProgress.next_reward.progress, 100)}%` }}
                          >
                            {demandProgress.next_reward.progress < 100 && (
                              <div className="absolute inset-0 bg-white/10" />
                            )}
                          </div>
                        </div>
                        {/* Milestone markers with labels */}
                        <div className="absolute top-0 left-1/2 h-4 w-0.5 bg-slate-600" title="50%">
                          <span className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[10px] text-slate-500">50%</span>
                        </div>
                        <div className="absolute top-0 left-[80%] h-4 w-0.5 bg-slate-600" title="80%">
                          <span className="absolute -bottom-4 left-1/2 -translate-x-1/2 text-[10px] text-slate-500">80%</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between mt-5">
                        <p className="text-sm font-bold text-green-400">
                          {Math.round(demandProgress.next_reward.progress)}% Complete
                        </p>
                        <p className="text-sm text-slate-400">
                          {demandProgress.next_reward.coins_needed > 0 
                            ? <span className="text-yellow-400 font-medium">{demandProgress.next_reward.coins_needed} coins to go</span>
                            : <span className="text-green-400 font-bold">Ready to redeem! 🎉</span>}
                        </p>
                      </div>
                    </div>
                    <Button 
                      onClick={() => navigate('/shop')}
                      disabled={demandProgress.next_reward.coins_needed > 0}
                      size="lg"
                      className="bg-green-500 hover:bg-green-600 text-white font-bold px-6"
                    >
                      {demandProgress.next_reward.coins_needed > 0 ? 'Earn More' : 'Redeem'}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="bg-slate-900/50 rounded-lg p-4 text-center">
                  <Gift className="h-10 w-10 text-green-400 mx-auto mb-2" />
                  <p className="text-white font-medium">Start earning to unlock rewards!</p>
                </div>
              )}

              {/* Consumption Unlocked */}
              <div className="mt-4 flex items-center justify-between text-sm">
                <span className="text-slate-400">Consumption Unlocked:</span>
                <span className="text-green-400 font-bold">₹{demandProgress?.consumption_unlocked || 0} of real goods</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* HERO SECTION: Live Cricket Prediction */}
        <Card className="bg-gradient-to-br from-red-500/10 via-slate-900/50 to-orange-500/10 border-red-500/30 mb-6" data-testid="live-cricket-hero">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xl text-white flex items-center gap-3">
                <span className="text-3xl">🏏</span>
                Live Cricket Prediction
                <Badge className="bg-green-500/20 text-green-400">SKILL EARNING</Badge>
              </CardTitle>
              {liveMatch && (
                <Badge className="bg-red-500 text-white animate-pulse">
                  <span className="mr-1">●</span> LIVE NOW
                </Badge>
              )}
            </div>
            <CardDescription className="text-slate-400">
              Predict ball outcomes to earn coins. Your accuracy determines your rewards.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {liveMatch ? (
              <div className="grid md:grid-cols-2 gap-6">
                {/* Match Info */}
                <div className="bg-slate-900/50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-4">
                    <div className="text-center">
                      <p className="text-2xl">🏏</p>
                      <p className="font-bold text-white">{liveMatch.team1_short}</p>
                      <p className="text-lg font-black text-yellow-400">{liveMatch.team1_score || '-'}</p>
                    </div>
                    <div className="text-2xl font-bold text-slate-600">VS</div>
                    <div className="text-center">
                      <p className="text-2xl">🏏</p>
                      <p className="font-bold text-white">{liveMatch.team2_short}</p>
                      <p className="text-lg font-black text-slate-400">{liveMatch.team2_score || 'Yet to bat'}</p>
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 text-center">{liveMatch.venue}</p>
                </div>
                
                {/* Quick Predict CTA - Enhanced */}
                <div className="flex flex-col justify-center items-center">
                  <p className="text-slate-400 mb-3">Predict the next ball outcome</p>
                  <Button 
                    onClick={() => navigate('/cricket')}
                    className="bg-gradient-to-r from-red-500 to-orange-500 hover:from-red-600 hover:to-orange-600 text-white font-bold text-lg px-8 py-6"
                    data-testid="predict-now-btn"
                  >
                    <Target className="mr-2 h-5 w-5" />
                    Start Predicting
                    <ChevronRight className="ml-2 h-5 w-5" />
                  </Button>
                  <p className="text-xs text-green-400 mt-2 font-medium">Earn 5-15 coins per correct prediction</p>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="text-6xl mb-4">🏟️</div>
                <h3 className="text-xl font-bold text-white mb-2">IPL 2026 Starts March 26</h3>
                <p className="text-slate-400 mb-4">Get ready for live ball-by-ball predictions!</p>
                <Button onClick={() => navigate('/cricket')} variant="outline" className="border-slate-600">
                  View Upcoming Matches
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Skill Stats + Daily Check-in Row */}
        <div className="grid md:grid-cols-3 gap-6 mb-6">
          {/* Prediction Stats */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-white flex items-center gap-2">
                <Target className="h-5 w-5 text-blue-400" />
                Skill Stats
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-2xl font-black text-blue-400">
                    {demandProgress?.prediction_stats?.accuracy || 0}%
                  </p>
                  <p className="text-xs text-slate-400">Accuracy</p>
                </div>
                <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-2xl font-black text-green-400">
                    {demandProgress?.prediction_stats?.correct || 0}
                  </p>
                  <p className="text-xs text-slate-400">Correct</p>
                </div>
                <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-2xl font-black text-yellow-400">
                    {demandProgress?.prediction_stats?.streak || 0}
                  </p>
                  <p className="text-xs text-slate-400">Streak</p>
                </div>
                <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                  <p className="text-2xl font-black text-slate-300">
                    {demandProgress?.prediction_stats?.total || 0}
                  </p>
                  <p className="text-xs text-slate-400">Total</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Daily Check-in */}
          <Card className="bg-slate-900/50 border-slate-800" data-testid="checkin-card">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-white">
                <Calendar className="h-5 w-5 text-yellow-400" />
                Daily Check-in
              </CardTitle>
            </CardHeader>
            <CardContent>
              {canCheckin ? (
                <div className="space-y-3">
                  <Button
                    onClick={handleCheckin}
                    disabled={checkinLoading}
                    className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
                    data-testid="checkin-btn"
                  >
                    {checkinLoading ? 'Checking in...' : 'Check In Now'}
                  </Button>
                  <div className="flex items-center justify-center gap-2">
                    <Flame className="h-4 w-4 text-red-400" />
                    <span className="text-sm text-slate-300">
                      Streak: <span className="font-bold text-red-400">{user?.streak_days || 0} days</span>
                    </span>
                  </div>
                </div>
              ) : (
                <div className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg text-center">
                  <p className="text-green-400 font-bold text-sm">Checked in today! ✓</p>
                  <p className="text-xs text-slate-400 mt-1">Come back tomorrow</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Boosters Section */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-white">
                <Zap className="h-5 w-5 text-purple-400" />
                Boosters
                <Badge className="bg-purple-500/20 text-purple-400 text-xs">BONUS</Badge>
              </CardTitle>
              <CardDescription className="text-slate-500 text-xs">
                Boosters help you earn faster. Skill drives your rewards.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                onClick={() => navigate('/earn')}
                variant="outline"
                className="w-full justify-between border-slate-700 hover:bg-purple-500/10"
              >
                <span className="flex items-center gap-2">
                  <Tv className="h-4 w-4 text-green-400" />
                  Watch Ads
                </span>
                <span className="text-green-400 text-sm">+50 coins</span>
              </Button>
              <Button
                onClick={() => navigate('/earn')}
                variant="outline"
                className="w-full justify-between border-slate-700 hover:bg-purple-500/10"
              >
                <span className="flex items-center gap-2">
                  <Play className="h-4 w-4 text-yellow-400" />
                  Mini Games
                </span>
                <span className="text-yellow-400 text-sm">Up to 100</span>
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Leaderboard + Recent Activity */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Skill Leaderboard */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-400" />
                Skill Leaderboard
              </CardTitle>
              <CardDescription className="text-slate-400">Top predictors by accuracy</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                {leaderboard.length > 0 ? (
                  <div className="space-y-2">
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
                          <p className="text-xs text-slate-400">
                            {player.accuracy !== undefined 
                              ? `${player.accuracy}% accuracy` 
                              : `Level ${player.level}`}
                          </p>
                        </div>
                        <Badge className="bg-blue-500/20 text-blue-400">
                          {player.correct_predictions !== undefined 
                            ? `${player.correct_predictions} correct`
                            : `${player.total_earned} coins`}
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-slate-400 py-8">Start predicting to join!</p>
                )}
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Recent Transactions */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-400" />
                Recent Activity
              </CardTitle>
              <CardDescription className="text-slate-400">Your coin movements</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-64">
                {transactions.length > 0 ? (
                  <div className="space-y-2">
                    {transactions.map((tx) => (
                      <div key={tx.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-white">{tx.description}</p>
                          <p className="text-xs text-slate-400">
                            {new Date(tx.timestamp).toLocaleDateString()}
                          </p>
                        </div>
                        <Badge
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
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Quick Shop Access */}
        <Card className="bg-slate-900/50 border-slate-800 mt-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ShoppingBag className="h-6 w-6 text-blue-400" />
                <div>
                  <p className="font-bold text-white">Redeem Your Coins</p>
                  <p className="text-xs text-slate-400">Starting from just 10 coins</p>
                </div>
              </div>
              <Button 
                onClick={() => navigate('/shop')}
                className="bg-blue-500 hover:bg-blue-600"
              >
                Browse Shop
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
