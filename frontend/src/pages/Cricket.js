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

  // Ball prediction outcomes
  const BALL_OUTCOMES = [
    { value: '0', label: 'Dot', emoji: '⚫', color: 'bg-slate-600' },
    { value: '1', label: '1 Run', emoji: '1️⃣', color: 'bg-blue-600' },
    { value: '2', label: '2 Runs', emoji: '2️⃣', color: 'bg-blue-500' },
    { value: '3', label: '3 Runs', emoji: '3️⃣', color: 'bg-green-600' },
    { value: '4', label: 'FOUR!', emoji: '4️⃣', color: 'bg-yellow-500' },
    { value: '6', label: 'SIX!', emoji: '6️⃣', color: 'bg-red-500' },
    { value: 'wicket', label: 'Wicket!', emoji: '🏏', color: 'bg-purple-600' },
    { value: 'wide', label: 'Wide', emoji: '↔️', color: 'bg-orange-500' },
  ];

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [matchesRes, leaderboardRes] = await Promise.all([
        api.getMatches(),
        api.getCricketLeaderboard()
      ]);
      
      setMatches(matchesRes.data);
      setLeaderboard(leaderboardRes.data);
      
      // Find live match
      const live = matchesRes.data.find(m => m.status === 'live');
      if (live) {
        setLiveMatch(live);
        setSelectedMatch(live);
        // Fetch predictions for live match
        const predsRes = await api.getMyPredictions(live.match_id);
        setMyPredictions(predsRes.data);
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
    if (!selectedMatch || !selectedMatch.current_ball) {
      toast.error('No live ball to predict');
      return;
    }

    setPredicting(true);
    try {
      const response = await api.predictBall({
        match_id: selectedMatch.match_id,
        ball_number: selectedMatch.current_ball,
        prediction: prediction
      });

      if (response.data.is_correct) {
        // Play celebration sound (respects user preference - OFF by default)
        playCorrectPredictionSound();
        
        // Confetti burst - triggers only once per successful prediction
        confetti({
          particleCount: 80,
          spread: 60,
          origin: { y: 0.6 },
          colors: ['#10b981', '#fbbf24', '#3b82f6']
        });
        
        // First-ever correct prediction check (persisted via user.correct_predictions)
        const isFirstEverCorrect = (user?.correct_predictions || 0) === 0;
        if (isFirstEverCorrect) {
          // First correct prediction ever - special message
          toast.success('Nice call! 🎯', {
            description: `Nice start. +${response.data.coins_earned} coins!`
          });
        } else {
          // Random celebration message for subsequent predictions
          const celebration = CELEBRATION_MESSAGES[Math.floor(Math.random() * CELEBRATION_MESSAGES.length)];
          toast.success(celebration.title, {
            description: `+${response.data.coins_earned} coins earned!`
          });
        }
        
        updateUser({ coins_balance: response.data.new_balance });
      } else {
        toast.info(response.data.message || 'Not this time — keep predicting!');
      }

      // Refresh predictions
      const predsRes = await api.getMyPredictions(selectedMatch.match_id);
      setMyPredictions(predsRes.data);
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Prediction failed');
    } finally {
      setPredicting(false);
    }
  };

  const handleMatchPrediction = async (type, value) => {
    if (!selectedMatch) return;

    try {
      await api.predictMatch({
        match_id: selectedMatch.match_id,
        prediction_type: type,
        prediction_value: value
      });
      
      playCoinSound();
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <Navbar />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin text-6xl mb-4">🏏</div>
            <p className="text-slate-400">Loading cricket matches...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-4 py-8" data-testid="cricket-page">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-black text-white mb-2 flex items-center gap-3">
              <span className="text-5xl">🏏</span> Cricket Predictions
            </h1>
            <p className="text-slate-400">Predict ball-by-ball outcomes and win coins!</p>
          </div>
          {myPredictions.stats && (
            <Card className="bg-gradient-to-r from-yellow-500/20 to-amber-500/20 border-yellow-500/30">
              <CardContent className="p-4 flex items-center gap-4">
                <Target className="h-8 w-8 text-yellow-400" />
                <div>
                  <p className="text-sm text-slate-400">Accuracy</p>
                  <p className="text-2xl font-bold text-yellow-400">{myPredictions.stats.accuracy || 0}%</p>
                </div>
                <div className="border-l border-slate-700 pl-4">
                  <p className="text-sm text-slate-400">Coins Won</p>
                  <p className="text-2xl font-bold text-yellow-400">{myPredictions.stats.total_coins_earned || 0}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Live Match Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Live Match Card */}
            {liveMatch ? (
              <Card className="bg-gradient-to-br from-red-500/10 via-slate-900/50 to-slate-900/50 border-red-500/30 overflow-hidden">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <Badge className="bg-red-500 text-white animate-pulse">
                      <span className="mr-1">●</span> LIVE
                    </Badge>
                    <Badge variant="outline" className="border-slate-600 text-slate-400">
                      {liveMatch.series}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Teams */}
                  <div className="flex items-center justify-between">
                    <div className="text-center flex-1">
                      <div className="text-4xl mb-2">🏏</div>
                      <p className="text-xl font-bold text-white">{liveMatch.team1_short}</p>
                      <p className="text-2xl font-black text-yellow-400">{liveMatch.team1_score || '-'}</p>
                    </div>
                    <div className="text-3xl font-bold text-slate-600">VS</div>
                    <div className="text-center flex-1">
                      <div className="text-4xl mb-2">🏏</div>
                      <p className="text-xl font-bold text-white">{liveMatch.team2_short}</p>
                      <p className="text-2xl font-black text-slate-400">{liveMatch.team2_score || 'Yet to bat'}</p>
                    </div>
                  </div>

                  {/* Current Over */}
                  {liveMatch.current_over_balls && (
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <p className="text-sm text-slate-400 mb-2">Current Over</p>
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
                    <p className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      <Zap className="h-5 w-5 text-yellow-400" />
                      Predict Next Ball (Ball {liveMatch.current_ball})
                    </p>
                    <div className="grid grid-cols-4 gap-2">
                      {BALL_OUTCOMES.map((outcome) => (
                        <Button
                          key={outcome.value}
                          onClick={() => handleBallPrediction(outcome.value)}
                          disabled={predicting}
                          className={`${outcome.color} hover:opacity-80 text-white h-16 flex flex-col items-center justify-center`}
                          data-testid={`predict-${outcome.value}`}
                        >
                          <span className="text-2xl">{outcome.emoji}</span>
                          <span className="text-xs">{outcome.label}</span>
                        </Button>
                      ))}
                    </div>
                  </div>

                  {/* Venue */}
                  <p className="text-sm text-slate-500 text-center">{liveMatch.venue}</p>
                </CardContent>
              </Card>
            ) : (
              <Card className="bg-slate-900/50 border-slate-800">
                <CardContent className="p-8 text-center">
                  <div className="text-6xl mb-4">🏟️</div>
                  <h3 className="text-xl font-bold text-white mb-2">No Live Match Right Now</h3>
                  <p className="text-slate-400">Check back during IPL 2026 for live predictions!</p>
                  <Badge className="mt-4 bg-yellow-500/20 text-yellow-400">IPL 2026 starts March 26</Badge>
                </CardContent>
              </Card>
            )}

            {/* Recent Predictions */}
            <Card className="bg-slate-900/50 border-slate-800">
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
                              <p className="text-sm text-slate-400">
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
                    <p className="text-slate-400">No predictions yet. Start predicting!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Prediction Stats */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  Your Stats
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Total Predictions</span>
                  <span className="text-white font-bold">{myPredictions.stats.total_predictions || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Correct</span>
                  <span className="text-green-400 font-bold">{myPredictions.stats.correct_predictions || 0}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Accuracy</span>
                  <span className="text-yellow-400 font-bold">{myPredictions.stats.accuracy || 0}%</span>
                </div>
                <Progress value={myPredictions.stats.accuracy || 0} className="h-2" />
              </CardContent>
            </Card>

            {/* Leaderboard */}
            <Card className="bg-slate-900/50 border-slate-800">
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
                            <p className="text-xs text-slate-400">{entry.correct_predictions} correct</p>
                          </div>
                        </div>
                        <Badge className="bg-yellow-500/20 text-yellow-400">
                          {entry.coins_earned}
                        </Badge>
                      </div>
                    )) : (
                      <div className="text-center py-8">
                        <Users className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                        <p className="text-slate-400">No predictions yet</p>
                      </div>
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Upcoming Matches */}
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Clock className="h-5 w-5 text-blue-400" />
                  Upcoming Matches
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {matches.filter(m => m.status === 'upcoming').slice(0, 5).map((match) => (
                    <div
                      key={match.id}
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
                          <p className="text-xs text-slate-400">
                            {new Date(match.match_date).toLocaleDateString('en-IN', {
                              weekday: 'short',
                              month: 'short',
                              day: 'numeric'
                            })}
                          </p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Match Prediction Dialog */}
      <Dialog open={predictDialogOpen} onOpenChange={setPredictDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-800 max-w-lg" data-testid="match-predict-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Award className="h-5 w-5 text-yellow-400" />
              Match Predictions
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedMatch?.team1_short} vs {selectedMatch?.team2_short}
            </DialogDescription>
          </DialogHeader>

          {selectedMatch && (
            <div className="space-y-6">
              {/* Winner Prediction */}
              <div>
                <p className="text-sm text-slate-400 mb-3">Who will win?</p>
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
                  Match starts {new Date(selectedMatch.match_date).toLocaleDateString()}
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
