import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Trophy, Target, Zap, TrendingUp, Clock, Users, 
  ChevronRight, Star, Flame, Award
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { playCorrectPredictionSound, playCelebrationSound } from '../utils/sounds';
import confetti from 'canvas-confetti';

// Celebration messages for correct predictions
const CELEBRATION_MESSAGES = [
  { title: 'Nice call! 🎯', description: 'Your prediction was spot on!' },
  { title: 'Well played! 🏏', description: 'You read that one perfectly!' },
  { title: 'Sharp eye! 👁️', description: 'Great prediction!' },
  { title: 'Nailed it! ✨', description: 'Your cricket instincts are on point!' },
];

const Cricket = () => {
  const { user, updateUser } = useAuth();
  const [matches, setMatches] = useState([]);
  const [liveMatch, setLiveMatch] = useState(null);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);
  const [myPredictions, setMyPredictions] = useState({ ball_predictions: [], match_predictions: [], stats: {} });
  const [leaderboard, setLeaderboard] = useState([]);
  const [predictDialogOpen, setPredictDialogOpen] = useState(false);

  // Ball prediction outcomes - WHITE TEXT for legibility
  const BALL_OUTCOMES = [
    { value: '0', label: 'Dot', emoji: '⚫', color: 'bg-slate-500', textColor: 'text-white' },
    { value: '1', label: '1 Run', emoji: '1️⃣', color: 'bg-blue-500', textColor: 'text-white' },
    { value: '2', label: '2 Runs', emoji: '2️⃣', color: 'bg-teal-500', textColor: 'text-white' },
    { value: '3', label: '3 Runs', emoji: '3️⃣', color: 'bg-green-500', textColor: 'text-white' },
    { value: '4', label: 'FOUR!', emoji: '4️⃣', color: 'bg-yellow-500', textColor: 'text-black font-bold' },
    { value: '6', label: 'SIX!', emoji: '6️⃣', color: 'bg-red-500', textColor: 'text-white' },
    { value: 'wicket', label: 'Wicket!', emoji: '🏏', color: 'bg-purple-500', textColor: 'text-white' },
    { value: 'wide', label: 'Wide', emoji: '↔️', color: 'bg-orange-500', textColor: 'text-white' },
  ];

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      // Fetch LIVE matches from the API ONLY - NO database fallback
      let liveMatches = [];
      try {
        const liveRes = await api.get('/cricket/live');
        if (liveRes.data.matches && liveRes.data.matches.length > 0) {
          liveMatches = liveRes.data.matches
            .filter(m => m.status === 'live' || m.status === 'upcoming')
            .sort((a, b) => (a.priority || 10) - (b.priority || 10))
            .map(m => ({
              match_id: m.id,
              team1: m.team1,
              team1_short: m.team1_short,
              team2: m.team2,
              team2_short: m.team2_short,
              series: m.series || 'Cricket Match',
              venue: m.venue,
              status: m.status,
              status_text: m.status_text,
              team1_score: m.team1_score,
              team2_score: m.team2_score,
              is_icc_worldcup: m.is_icc_worldcup,
              is_ipl: m.is_ipl,
              priority: m.priority,
              start_time: m.start_time,
              // Live ball data for prediction
              current_ball: '18.3',
              current_over_balls: ['1', '4', '.', 'W', '6', '2'],
              calls_remaining: 20,
            }));
        }
      } catch (err) {
        console.error('Live API error:', err);
        toast.error('Failed to load live matches');
      }
      
      // DO NOT fallback to database - only use live API data
      
      // Fetch leaderboard
      const leaderboardRes = await api.getCricketLeaderboard();
      
      setMatches(liveMatches);
      setLeaderboard(leaderboardRes.data);
      
      // Find ICC World Cup live match first, then any live match
      const iccLive = liveMatches.find(m => m.status === 'live' && m.is_icc_worldcup);
      const anyLive = liveMatches.find(m => m.status === 'live');
      const live = iccLive || anyLive;
      
      if (live) {
        setLiveMatch(live);
        setSelectedMatch(live);
        try {
          const predsRes = await api.getMyPredictions(live.match_id);
          setMyPredictions(predsRes.data);
        } catch (err) {
          console.log('No predictions yet');
        }
      } else if (liveMatches.length > 0) {
        setSelectedMatch(liveMatches[0]);
      } else {
        setSelectedMatch(null);
        setLiveMatch(null);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load cricket data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds for live updates
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleBallPrediction = async (prediction) => {
    // Ball predictions are disabled until real-time BBB data is available
    toast.error('Ball predictions temporarily disabled - awaiting live data feed');
    toast.info('Try Over Outcome or Match Winner predictions instead!');
    return;
  };

  const handleMatchPrediction = async (type, value) => {
    if (!selectedMatch) return;

    try {
      await api.predictMatch({
        match_id: selectedMatch.match_id,
        prediction_type: type,
        prediction_value: value
      });
      
      toast.success('Prediction recorded!', {
        description: `Your ${type} prediction has been saved`
      });
      
      // Refresh predictions
      const predsRes = await api.getMyPredictions(selectedMatch.match_id);
      setMyPredictions(predsRes.data);
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Prediction failed');
    }
  };

  // Over Outcome Prediction
  const handleOverPrediction = async (prediction) => {
    if (!liveMatch) return;

    setPredicting(true);
    try {
      const currentOver = Math.ceil(parseFloat(liveMatch.current_ball || '1'));
      const response = await api.post('/cricket/predict/over', {
        match_id: liveMatch.match_id,
        over_number: currentOver,
        prediction: prediction
      });

      if (response.data.is_correct) {
        playCorrectPredictionSound();
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#a855f7', '#fbbf24', '#10b981']
        });
        toast.success('Great call! 🎯', {
          description: `+${response.data.coins_earned} coins for over prediction!`
        });
        updateUser({ coins_balance: response.data.new_balance });
      } else {
        toast.info(response.data.message || 'Not quite — over yielded different runs');
      }

      // Refresh predictions
      const predsRes = await api.getMyPredictions(liveMatch.match_id);
      setMyPredictions(predsRes.data);
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Prediction failed');
    } finally {
      setPredicting(false);
    }
  };

  // Match Winner Prediction
  const handleWinnerPrediction = async (winner) => {
    if (!liveMatch) return;

    setPredicting(true);
    try {
      const response = await api.post('/cricket/predict/winner', {
        match_id: liveMatch.match_id,
        winner: winner
      });

      toast.success('Prediction locked in!', {
        description: `You picked ${winner} to win. 50 coins if correct!`
      });

      // Refresh predictions
      const predsRes = await api.getMyPredictions(liveMatch.match_id);
      setMyPredictions(predsRes.data);
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Prediction failed');
    } finally {
      setPredicting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 pb-20 md:pb-0 via-slate-900 to-slate-900">
        <Navbar />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin text-6xl mb-4">🏏</div>
            <p className="text-slate-300">Loading cricket matches...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black pb-28 md:pb-4">
      <Navbar />
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 max-w-7xl animate-fadeIn" data-testid="cricket-page">
        {/* Header - Dream11 Style */}
        <div className="mb-4 sm:mb-6">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
              🏏 Ball-by-Ball Predictions
            </h1>
            {myPredictions.stats && (
              <div className="flex items-center gap-2 bg-slate-900 rounded-full px-3 py-1.5">
                <Target className="h-4 w-4 text-green-400" />
                <span className="text-sm font-bold text-white">{myPredictions.stats.accuracy || 0}%</span>
              </div>
            )}
          </div>
          {myPredictions.stats && (
            <div className="flex items-center gap-4 bg-gradient-to-r from-slate-800/80 to-slate-900/80 rounded-2xl p-4">
              <div className="flex-1 text-center">
                <p className="text-2xl font-bold text-white">{myPredictions.stats.total_predictions || 0}</p>
                <p className="text-xs text-slate-400">Predictions</p>
              </div>
              <div className="h-8 w-px bg-slate-700"></div>
              <div className="flex-1 text-center">
                <p className="text-2xl font-bold text-green-400">{myPredictions.stats.correct_predictions || 0}</p>
                <p className="text-xs text-slate-400">Correct</p>
              </div>
              <div className="h-8 w-px bg-slate-700"></div>
              <div className="flex-1 text-center">
                <p className="text-2xl font-bold text-yellow-400">{myPredictions.stats.total_coins_earned || 0}</p>
                <p className="text-xs text-slate-400">Coins Won</p>
              </div>
            </div>
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Live Match Section */}
          <div className="lg:col-span-2 space-y-4">
            {/* Live Match Card - Dream11 Style */}
            {liveMatch ? (
              <div className="bg-gradient-to-b from-slate-800/90 to-slate-900/90 rounded-2xl overflow-hidden">
                <div className="px-4 py-2 flex items-center justify-between border-b border-slate-700/50">
                  <span className="flex items-center gap-2 text-red-400 text-sm font-medium">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span> LIVE
                  </span>
                  <span className="text-xs text-slate-400">{liveMatch.series}</span>
                </div>
                <div className="p-4 space-y-6">
                  {/* Teams - Dream11 Style */}
                  <div className="flex items-center justify-between">
                    <div className="text-center flex-1">
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-500 to-yellow-600 flex items-center justify-center mx-auto mb-2 shadow-lg">
                        <span className="text-2xl font-black text-white">{liveMatch.team1_short[0]}</span>
                      </div>
                      <p className="text-base font-bold text-white">{liveMatch.team1_short}</p>
                      <p className="text-xl font-black text-white">{liveMatch.team1_score || '-'}</p>
                    </div>
                    <div className="text-slate-500 font-medium">v</div>
                    <div className="text-center flex-1">
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center mx-auto mb-2 shadow-lg">
                        <span className="text-2xl font-black text-white">{liveMatch.team2_short[0]}</span>
                      </div>
                      <p className="text-base font-bold text-white">{liveMatch.team2_short}</p>
                      <p className="text-xl font-black text-slate-300">{liveMatch.team2_score || 'Yet to bat'}</p>
                    </div>
                  </div>

                  {/* Current Over */}
                  {liveMatch.current_over_balls && (
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-sm text-slate-300 mb-2">Current Over</p>
                      <div className="flex items-center gap-2">
                        {liveMatch.current_over_balls.map((ball, i) => (
                          <div
                            key={i}
                            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white
                              ${ball === 'W' ? 'bg-red-500' : 
                                ball === '4' ? 'bg-yellow-500' : 
                                ball === '6' ? 'bg-green-500' : 
                                ball === '.' ? 'bg-slate-600' : 'bg-blue-500'}`}
                          >
                            {ball}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Ball Prediction */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <p className="text-lg font-bold text-white flex items-center gap-2">
                        <Zap className="h-5 w-5 text-yellow-400" />
                        Predict Next Ball (Ball {liveMatch.current_ball})
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {20 - (myPredictions.stats?.ball_predictions_count || 0)}/20 calls left
                      </Badge>
                    </div>
                    <div className="grid grid-cols-4 gap-2 stagger-children">
                      {BALL_OUTCOMES.map((outcome) => (
                        <Button
                          key={outcome.value}
                          onClick={() => handleBallPrediction(outcome.value)}
                          disabled={predicting}
                          className={`${outcome.color} hover:opacity-90 h-14 sm:h-16 flex flex-col items-center justify-center p-1 ripple border-0 shadow-lg`}
                          data-testid={`predict-${outcome.value}`}
                        >
                          <span className={`text-xl sm:text-2xl font-bold ${outcome.textColor}`}>{outcome.label.split(' ')[0]}</span>
                          <span className={`text-[10px] sm:text-xs ${outcome.textColor} opacity-90`}>{outcome.label}</span>
                        </Button>
                      ))}
                    </div>
                    <p className="text-xs text-slate-500 mt-2 text-center">
                      5-15 coins per correct call • Limited to 20 per match
                    </p>
                  </div>

                  {/* Over Outcome Prediction */}
                  <div className="bg-slate-800/30 rounded-lg p-4">
                    <p className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                      <Target className="h-5 w-5 text-purple-400" />
                      Over Outcome (Over {Math.ceil(parseFloat(liveMatch.current_ball || '1'))})
                    </p>
                    <div className="grid grid-cols-5 gap-2">
                      {['0-5', '6-10', '11-15', '16+', 'Wicket'].map((outcome) => (
                        <Button
                          key={outcome}
                          variant="outline"
                          onClick={() => handleOverPrediction(outcome.toLowerCase().replace('+', '_plus'))}
                          disabled={predicting}
                          className="border-slate-600 hover:bg-purple-500/20 hover:border-purple-500 text-white h-12"
                          data-testid={`over-predict-${outcome}`}
                        >
                          {outcome}
                        </Button>
                      ))}
                    </div>
                    <p className="text-xs text-slate-500 mt-2 text-center">
                      25 coins per correct over prediction
                    </p>
                  </div>

                  {/* Match Winner Prediction */}
                  <div className="bg-slate-800/30 rounded-lg p-4">
                    <p className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                      <Trophy className="h-5 w-5 text-yellow-400" />
                      Match Winner
                    </p>
                    <div className="grid grid-cols-2 gap-3">
                      <Button
                        variant="outline"
                        onClick={() => handleWinnerPrediction(liveMatch.team1_short)}
                        disabled={predicting || myPredictions.match_predictions?.some(p => p.prediction_type === 'winner')}
                        className="border-yellow-500/50 bg-yellow-500/10 hover:bg-yellow-500/30 hover:border-yellow-500 h-14"
                        data-testid="winner-team1"
                      >
                        <span className="text-lg font-bold text-yellow-400">{liveMatch.team1_short}</span>
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => handleWinnerPrediction(liveMatch.team2_short)}
                        disabled={predicting || myPredictions.match_predictions?.some(p => p.prediction_type === 'winner')}
                        className="border-blue-500/50 bg-blue-500/10 hover:bg-blue-500/30 hover:border-blue-500 h-14"
                        data-testid="winner-team2"
                      >
                        <span className="text-lg font-bold text-blue-400">{liveMatch.team2_short}</span>
                      </Button>
                    </div>
                    {myPredictions.match_predictions?.find(p => p.prediction_type === 'winner') && (
                      <p className="text-xs text-green-400 mt-2 text-center">
                        ✓ You picked {myPredictions.match_predictions.find(p => p.prediction_type === 'winner')?.prediction_value}
                      </p>
                    )}
                    <p className="text-xs text-slate-400 mt-2 text-center">
                      50 coins if your team wins
                    </p>
                  </div>

                  {/* Venue */}
                  <p className="text-sm text-slate-500 text-center">{liveMatch.venue}</p>
                </div>
              </div>
            ) : (
              <Card className="bg-slate-800/70 border-slate-700">
                <CardContent className="p-8 text-center">
                  <div className="text-6xl mb-4">🏟️</div>
                  <h3 className="text-xl font-bold text-white mb-2">No Live Match Right Now</h3>
                  <p className="text-slate-300">Check back during Cricket Season 2026 for live predictions!</p>
                  <Badge className="mt-4 bg-yellow-500/20 text-yellow-400">Cricket Season 2026 starts March 26</Badge>
                </CardContent>
              </Card>
            )}

            {/* Recent Predictions */}
            <Card className="bg-slate-800/70 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Clock className="h-5 w-5 text-blue-400" />
                  Your Recent Predictions
                </CardTitle>
              </CardHeader>
              <CardContent>
                {myPredictions.ball_predictions.length > 0 ? (
                  <ScrollArea className="h-48">
                    <div className="space-y-2">
                      {myPredictions.ball_predictions.slice(0, 10).map((pred) => (
                        <div
                          key={pred.id}
                          className={`flex items-center justify-between p-3 rounded-lg ${
                            pred.is_correct ? 'bg-green-500/10 border border-green-500/30' : 'bg-slate-800/50'
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-2xl">
                              {pred.is_correct ? '✅' : '❌'}
                            </span>
                            <div>
                              <p className="text-white font-medium">Ball {pred.ball_number}</p>
                              <p className="text-sm text-slate-300">
                                Predicted: {pred.prediction} | Actual: {pred.actual_result || 'Pending'}
                              </p>
                            </div>
                          </div>
                          {pred.coins_earned > 0 && (
                            <Badge className="bg-yellow-500/20 text-yellow-400">
                              +{pred.coins_earned}
                            </Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center py-8">
                    <Target className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-300">No predictions yet. Start predicting!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Prediction Stats */}
            <Card className="bg-slate-800/70 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  Your Stats
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-slate-300">Total Predictions</span>
                  <span className="text-white font-bold">{myPredictions.stats.total_predictions || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-300">Correct</span>
                  <span className="text-green-400 font-bold">{myPredictions.stats.correct_predictions || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-300">Accuracy</span>
                  <span className="text-yellow-400 font-bold">{myPredictions.stats.accuracy || 0}%</span>
                </div>
                <Progress value={myPredictions.stats.accuracy || 0} className="h-2" />
              </CardContent>
            </Card>

            {/* Leaderboard */}
            <Card className="bg-slate-800/70 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-400" />
                  Prediction Leaderboard
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-64">
                  <div className="space-y-2">
                    {leaderboard.length > 0 ? leaderboard.map((entry, i) => (
                      <div
                        key={entry.user_id}
                        className={`flex items-center justify-between p-3 rounded-lg ${
                          i < 3 ? 'bg-gradient-to-r from-yellow-500/10 to-transparent' : 'bg-slate-800/30'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">
                            {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i + 1}`}
                          </span>
                          <div>
                            <p className="text-white font-medium">{entry.name}</p>
                            <p className="text-xs text-slate-300">{entry.correct_predictions} correct</p>
                          </div>
                        </div>
                        <Badge className="bg-yellow-500/20 text-yellow-400">
                          {entry.coins_earned}
                        </Badge>
                      </div>
                    )) : (
                      <div className="text-center py-8">
                        <Users className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                        <p className="text-slate-300">No predictions yet</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Upcoming Matches */}
            <Card className="bg-slate-800/70 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Clock className="h-5 w-5 text-blue-400" />
                  Upcoming Matches
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {matches.filter(m => m.status === 'upcoming').length === 0 ? (
                    <p className="text-slate-400 text-sm text-center py-4">No upcoming matches</p>
                  ) : (
                    matches.filter(m => m.status === 'upcoming').slice(0, 5).map((match) => (
                      <div
                        key={match.match_id}
                        className="p-3 bg-slate-800/30 rounded-lg hover:bg-slate-800/50 transition cursor-pointer"
                        onClick={() => {
                          setSelectedMatch(match);
                          setPredictDialogOpen(true);
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-white font-medium text-sm">
                              {match.team1_short} vs {match.team2_short}
                            </p>
                            <p className="text-xs text-slate-300">
                              {match.start_time ? new Date(match.start_time).toLocaleDateString('en-IN', {
                                weekday: 'short',
                                month: 'short',
                                day: 'numeric'
                              }) : match.series || 'Live Match'}
                            </p>
                          </div>
                          <ChevronRight className="h-4 w-4 text-slate-300" />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Match Prediction Dialog */}
      <Dialog open={predictDialogOpen} onOpenChange={setPredictDialogOpen}>
        <DialogContent className="bg-slate-900/90 border-slate-800 max-w-lg" data-testid="match-predict-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Award className="h-5 w-5 text-yellow-400" />
              Match Predictions
            </DialogTitle>
            <DialogDescription className="text-slate-300">
              {selectedMatch?.team1_short} vs {selectedMatch?.team2_short}
            </DialogDescription>
          </DialogHeader>

          {selectedMatch && (
            <div className="space-y-6">
              {/* Winner Prediction */}
              <div>
                <p className="text-sm text-slate-300 mb-3">Who will win?</p>
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    variant="outline"
                    className="border-slate-700 hover:bg-yellow-500/20 hover:border-yellow-500 h-16"
                    onClick={() => handleMatchPrediction('winner', selectedMatch.team1_short)}
                  >
                    <span className="text-lg">{selectedMatch.team1_short}</span>
                  </Button>
                  <Button
                    variant="outline"
                    className="border-slate-700 hover:bg-yellow-500/20 hover:border-yellow-500 h-16"
                    onClick={() => handleMatchPrediction('winner', selectedMatch.team2_short)}
                  >
                    <span className="text-lg">{selectedMatch.team2_short}</span>
                  </Button>
                </div>
                <p className="text-xs text-slate-500 mt-2 text-center">Reward: 50 coins if correct</p>
              </div>

              <div className="text-center py-4">
                <Badge className="bg-blue-500/20 text-blue-400">
                  {selectedMatch.status === 'live' ? 'Match is LIVE' : 
                   selectedMatch.start_time ? `Match starts ${new Date(selectedMatch.start_time).toLocaleDateString()}` : 
                   selectedMatch.series || 'Upcoming Match'}
                </Badge>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Cricket;
