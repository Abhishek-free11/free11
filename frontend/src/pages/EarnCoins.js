import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Coins, Zap, CheckCircle2, Trophy, Sparkles, Gift, Dices, Spade, Play, Tv, Target, Star } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { playCoinSound, playCelebrationSound, playWinSound } from '../utils/sounds';
import confetti from 'canvas-confetti';

const EarnCoins = () => {
  const { user, updateUser } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);

  // Quiz state
  const [quizOpen, setQuizOpen] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState([]);
  const [quizResult, setQuizResult] = useState(null);

  // Spin wheel state
  const [spinOpen, setSpinOpen] = useState(false);
  const [spinning, setSpinning] = useState(false);
  const [spinResult, setSpinResult] = useState(null);

  // Scratch card state
  const [scratchOpen, setScratchOpen] = useState(false);
  const [scratching, setScratching] = useState(false);
  const [scratchResult, setScratchResult] = useState(null);

  // Watch Ad state
  const [adStatus, setAdStatus] = useState(null);
  const [watchingAd, setWatchingAd] = useState(false);
  const [adProgress, setAdProgress] = useState(0);

  useEffect(() => {
    fetchTasks();
    fetchAdStatus();
  }, []);

  const fetchTasks = async () => {
    try {
      const response = await api.getTasks();
      setTasks(response.data);
    } catch (error) {
      console.error('Error fetching tasks:', error);
    }
  };

  const fetchAdStatus = async () => {
    try {
      const response = await api.getAdStatus();
      setAdStatus(response.data);
    } catch (error) {
      console.error('Error fetching ad status:', error);
    }
  };

  const handleWatchAd = async () => {
    if (!adStatus?.can_watch) {
      toast.error('Daily ad limit reached!');
      return;
    }

    setWatchingAd(true);
    setAdProgress(0);

    // Simulate ad playback (in production, this would be real AdMob integration)
    const interval = setInterval(() => {
      setAdProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 5;
      });
    }, 150);

    // After "ad" completes (3 seconds simulation)
    setTimeout(async () => {
      clearInterval(interval);
      setAdProgress(100);
      
      try {
        const response = await api.claimAdReward({ ad_type: 'rewarded' });
        playCelebrationSound();
        confetti({
          particleCount: 80,
          spread: 60,
          origin: { y: 0.6 }
        });
        toast.success(response.data.message, {
          description: `${response.data.ads_remaining} ads remaining today`
        });
        updateUser({ coins_balance: response.data.new_balance });
        fetchAdStatus();
      } catch (error) {
        toast.error(error.response?.data?.detail || 'Failed to claim reward');
      } finally {
        setWatchingAd(false);
        setAdProgress(0);
      }
    }, 3000);
  };

  const handleCompleteTask = async (taskId) => {
    setLoading(true);
    try {
      const response = await api.completeTask(taskId);
      playCoinSound();
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.6 }
      });
      toast.success(response.data.message, {
        description: `+${response.data.coins_earned} coins 🪙`
      });
      updateUser({ coins_balance: response.data.new_balance });
      fetchTasks();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Task completion failed');
    } finally {
      setLoading(false);
    }
  };

  // Quiz questions
  const quizQuestions = [
    {
      question: 'What is FREE11?',
      options: ['A Consumption Operating System', 'A Gaming App', 'A Payment App', 'A Social Network'],
      correct: 0
    },
    {
      question: 'How do you earn FREE11 Coins?',
      options: ['Buy them', 'Borrow them', 'Play games and complete tasks', 'Gift them'],
      correct: 2
    },
    {
      question: 'Can you withdraw FREE11 Coins as cash?',
      options: ['Yes', 'Sometimes', 'No, redeem for products only', 'Only in India'],
      correct: 2
    },
    {
      question: 'What is PRORGA?',
      options: ['A product', 'A payment method', 'A game', 'Regulatory compliance framework'],
      correct: 3
    },
    {
      question: 'What is the best way to maximize coins?',
      options: ['Daily check-ins and streaks', 'Share with friends', 'Complete all tasks', 'All of the above'],
      correct: 0
    }
  ];

  const handleQuizSubmit = async () => {
    if (quizAnswers.length !== quizQuestions.length) {
      toast.error('Please answer all questions');
      return;
    }

    setLoading(true);
    try {
      const response = await api.playQuiz(quizAnswers);
      setQuizResult(response.data);
      if (response.data.coins_earned > 0) {
        playWinSound();
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        });
        toast.success(`Quiz completed!`, {
          description: `You scored ${response.data.score_percentage}% and earned ${response.data.coins_earned} coins! 🎉`
        });
        updateUser({ coins_balance: response.data.new_balance });
      } else {
        toast.info('Try again tomorrow!', {
          description: 'Better luck next time!'
        });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Quiz failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSpinWheel = async () => {
    setSpinning(true);
    try {
      const response = await api.spinWheel();
      
      // Simulate spin animation
      setTimeout(() => {
        setSpinResult(response.data);
        setSpinning(false);
        if (response.data.coins_earned > 0) {
          playCelebrationSound();
          confetti({
            particleCount: 80,
            spread: 60,
            origin: { y: 0.6 }
          });
          toast.success(response.data.message, {
            description: `+${response.data.coins_earned} coins! 🎉`
          });
          updateUser({ coins_balance: response.data.new_balance });
        } else {
          toast.info(response.data.message);
        }
      }, 2000);
    } catch (error) {
      setSpinning(false);
      toast.error(error.response?.data?.detail || 'Spin failed');
    }
  };

  const handleScratchCard = async () => {
    setScratching(true);
    try {
      const response = await api.scratchCard();
      
      // Simulate scratch animation
      setTimeout(() => {
        setScratchResult(response.data);
        setScratching(false);
        if (response.data.coins_earned > 0) {
          playCoinSound();
          confetti({
            particleCount: 60,
            spread: 50,
            origin: { y: 0.6 }
          });
          toast.success('You won!', {
            description: `+${response.data.coins_earned} coins! 💰`
          });
          updateUser({ coins_balance: response.data.new_balance });
        } else {
          toast.info('Try again!', {
            description: `${response.data.attempts_left} attempts left today`
          });
        }
      }, 1500);
    } catch (error) {
      setScratching(false);
      toast.error(error.response?.data?.detail || 'Scratch failed');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-900 to-slate-900 pb-20 md:pb-0">
      <Navbar />
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl" data-testid="earn-coins-page">
        <div className="mb-4 sm:mb-8">
          <h1 className="text-2xl sm:text-4xl font-black text-white mb-1 sm:mb-2">Coin Boosters ⚡</h1>
          <p className="text-slate-300 text-sm sm:text-base">Accelerate your earnings with bonus activities</p>
          <p className="text-xs text-purple-400 mt-1">These are supplementary to skill-based cricket predictions</p>
        </div>

        <Tabs defaultValue="ads" className="space-y-4 sm:space-y-6">
          <TabsList className="bg-slate-800/70 border border-slate-700 w-full sm:w-auto overflow-x-auto">
            <TabsTrigger value="howto" className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-400 text-xs sm:text-sm">
              <Tv className="h-4 w-4 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">How to</span> Earn
            </TabsTrigger>
            <TabsTrigger value="games" className="data-[state=active]:bg-yellow-500/20 data-[state=active]:text-yellow-400 text-xs sm:text-sm">
              <Zap className="h-4 w-4 mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Mini</span> Games
            </TabsTrigger>
            <TabsTrigger value="tasks" className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400 text-xs sm:text-sm">
              <CheckCircle2 className="h-4 w-4 mr-1 sm:mr-2" />
              Tasks
            </TabsTrigger>
          </TabsList>

          {/* How to Earn Tab */}
          <TabsContent value="howto" className="space-y-6">
            <Card className="bg-gradient-to-br from-green-500/10 via-slate-900/50 to-slate-900/50 border-green-500/30" data-testid="how-to-earn-section">
              <CardHeader>
                <CardTitle className="text-2xl text-white">Ways to Earn Coins</CardTitle>
                <CardDescription className="text-slate-300">
                  FREE11 coins are earned through skill and engagement - never purchased!
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4">
                  <div className="bg-slate-800/50 rounded-lg p-4 flex items-start gap-4">
                    <div className="p-2 bg-yellow-500/20 rounded-lg">
                      <Trophy className="h-6 w-6 text-yellow-400" />
                    </div>
                    <div>
                      <h4 className="font-bold text-white">Fantasy Contests</h4>
                      <p className="text-sm text-slate-300">Build your dream team and compete in contests. Top performers win big coins!</p>
                      <p className="text-xs text-yellow-400 mt-1">Up to 500 coins per contest</p>
                    </div>
                  </div>
                  
                  <div className="bg-slate-800/50 rounded-lg p-4 flex items-start gap-4">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                      <Target className="h-6 w-6 text-blue-400" />
                    </div>
                    <div>
                      <h4 className="font-bold text-white">Match Winner Predictions</h4>
                      <p className="text-sm text-slate-300">Predict the winning team before or during the match.</p>
                      <p className="text-xs text-blue-400 mt-1">50 coins per correct prediction</p>
                    </div>
                  </div>
                  
                  <div className="bg-slate-800/50 rounded-lg p-4 flex items-start gap-4">
                    <div className="p-2 bg-purple-500/20 rounded-lg">
                      <Zap className="h-6 w-6 text-purple-400" />
                    </div>
                    <div>
                      <h4 className="font-bold text-white">Over Outcome Predictions</h4>
                      <p className="text-sm text-slate-300">Predict runs scored in each over during live matches.</p>
                      <p className="text-xs text-purple-400 mt-1">25 coins per correct prediction</p>
                    </div>
                  </div>
                  
                  <div className="bg-slate-800/50 rounded-lg p-4 flex items-start gap-4">
                    <div className="p-2 bg-green-500/20 rounded-lg">
                      <Gift className="h-6 w-6 text-green-400" />
                    </div>
                    <div>
                      <h4 className="font-bold text-white">Ball-by-Ball (Limited)</h4>
                      <p className="text-sm text-slate-300">Predict delivery outcomes - 20 predictions per match.</p>
                      <p className="text-xs text-green-400 mt-1">5-15 coins per correct call</p>
                    </div>
                  </div>
                  
                  <div className="bg-slate-800/50 rounded-lg p-4 flex items-start gap-4">
                    <div className="p-2 bg-red-500/20 rounded-lg">
                      <Star className="h-6 w-6 text-red-400" />
                    </div>
                    <div>
                      <h4 className="font-bold text-white">Mini Games & Tasks</h4>
                      <p className="text-sm text-slate-300">Play daily games and complete tasks for bonus coins.</p>
                      <p className="text-xs text-red-400 mt-1">10-100 coins per activity</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Mini Games Tab */}
          <TabsContent value="games" className="space-y-6">
            <div className="grid md:grid-cols-3 gap-6">
              {/* Quiz - Cricket themed */}
              <Card className="bg-slate-800/70 border-slate-700 hover:border-yellow-500/50 transition-all cursor-pointer group" onClick={() => setQuizOpen(true)} data-testid="quiz-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="relative">
                      <Trophy className="h-10 w-10 text-yellow-400 group-hover:scale-110 transition-transform" />
                      <span className="absolute -top-1 -right-1 text-2xl">🏏</span>
                    </div>
                    <Badge className="bg-yellow-500/20 text-yellow-400">Up to 50 coins</Badge>
                  </div>
                  <CardTitle className="text-white">Cricket Quiz Challenge</CardTitle>
                  <CardDescription className="text-slate-300">
                    Test your cricket knowledge and earn coins
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold">
                    🏏 Play Now
                  </Button>
                </CardContent>
              </Card>

              {/* Spin Wheel - RMG themed */}
              <Card className="bg-slate-800/70 border-slate-700 hover:border-red-500/50 transition-all cursor-pointer group" onClick={() => setSpinOpen(true)} data-testid="spin-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="relative">
                      <Gift className="h-10 w-10 text-red-400 group-hover:rotate-12 transition-transform" />
                      <Dices className="absolute -bottom-1 -right-1 h-5 w-5 text-red-300" />
                    </div>
                    <Badge className="bg-red-500/20 text-red-400">Daily Spin</Badge>
                  </div>
                  <CardTitle className="text-white">Lucky Spin Wheel</CardTitle>
                  <CardDescription className="text-slate-300">
                    Spin once per day for instant rewards
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white font-bold">
                    🎰 Spin Now
                  </Button>
                </CardContent>
              </Card>

              {/* Scratch Card - Cards themed */}
              <Card className="bg-slate-800/70 border-slate-700 hover:border-blue-500/50 transition-all cursor-pointer group" onClick={() => setScratchOpen(true)} data-testid="scratch-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="relative">
                      <Sparkles className="h-10 w-10 text-blue-400 group-hover:scale-110 transition-transform" />
                      <Spade className="absolute -bottom-1 -right-1 h-5 w-5 text-blue-300" />
                    </div>
                    <Badge className="bg-blue-500/20 text-blue-400">3x Daily</Badge>
                  </div>
                  <CardTitle className="text-white">Golden Scratch Card</CardTitle>
                  <CardDescription className="text-slate-300">
                    Instant win prizes, 3 attempts daily
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button className="w-full bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white font-bold">
                    🃏 Scratch Now
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Tasks Tab */}
          <TabsContent value="tasks" className="space-y-6">
            <div className="grid gap-4">
              {tasks.map((task) => (
                <Card key={task.id} className="bg-slate-800/70 border-slate-700" data-testid={`task-${task.id}`}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-bold text-white">{task.title}</h3>
                          {task.completed && (
                            <Badge className="bg-green-500/20 text-green-400">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Completed
                            </Badge>
                          )}
                        </div>
                        <p className="text-slate-300 text-sm">{task.description}</p>
                      </div>
                      <div className="flex items-center gap-4">
                        <Badge className="bg-yellow-500/20 text-yellow-400 px-4 py-2">
                          <Coins className="h-4 w-4 mr-1" />
                          {task.coins}
                        </Badge>
                        <Button
                          onClick={() => handleCompleteTask(task.id)}
                          disabled={task.completed || loading}
                          className="bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white font-bold"
                          data-testid={`complete-task-${task.id}`}
                        >
                          {task.completed ? 'Completed' : 'Complete'}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Quiz Dialog */}
      <Dialog open={quizOpen} onOpenChange={setQuizOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 max-w-2xl" data-testid="quiz-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl text-white flex items-center gap-2">
              <Trophy className="h-6 w-6 text-yellow-400" />
              Quiz Challenge
            </DialogTitle>
            <DialogDescription className="text-slate-300">
              Answer all questions correctly to maximize your coin earnings
            </DialogDescription>
          </DialogHeader>

          {!quizResult ? (
            <div className="space-y-6 max-h-[60vh] overflow-y-auto">
              {quizQuestions.map((q, qIndex) => (
                <Card key={qIndex} className="bg-slate-800/50 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-lg text-white">
                      Q{qIndex + 1}. {q.question}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {q.options.map((option, oIndex) => (
                      <Button
                        key={oIndex}
                        variant="outline"
                        className={`w-full justify-start ${
                          quizAnswers[qIndex] === oIndex
                            ? 'bg-yellow-500/20 border-yellow-500 text-yellow-400'
                            : 'bg-slate-700/50 border-slate-600 text-slate-200'
                        }`}
                        onClick={() => {
                          const newAnswers = [...quizAnswers];
                          newAnswers[qIndex] = oIndex;
                          setQuizAnswers(newAnswers);
                        }}
                      >
                        {option}
                      </Button>
                    ))}
                  </CardContent>
                </Card>
              ))}

              <Button
                onClick={handleQuizSubmit}
                disabled={quizAnswers.length !== quizQuestions.length || loading}
                className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold py-6"
                data-testid="submit-quiz-btn"
              >
                {loading ? 'Submitting...' : 'Submit Quiz'}
              </Button>
            </div>
          ) : (
            <div className="text-center space-y-6 py-8">
              <div className="text-6xl">{quizResult.score_percentage >= 60 ? '🎉' : '😔'}</div>
              <div>
                <h3 className="text-2xl font-bold text-white mb-2">
                  Score: {quizResult.score_percentage}%
                </h3>
                <p className="text-slate-300">
                  {quizResult.correct_count} out of {quizResult.total_questions} correct
                </p>
              </div>
              <div className="bg-gradient-to-r from-yellow-500/20 to-amber-600/20 border border-yellow-500/30 rounded-lg p-6">
                <p className="text-yellow-400 font-bold text-3xl">+{quizResult.coins_earned} Coins</p>
              </div>
              <Button
                onClick={() => {
                  setQuizOpen(false);
                  setQuizResult(null);
                  setQuizAnswers([]);
                }}
                className="bg-slate-700 hover:bg-slate-600 text-white"
              >
                Close
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Spin Wheel Dialog */}
      <Dialog open={spinOpen} onOpenChange={setSpinOpen}>
        <DialogContent className="bg-slate-900 border-slate-700" data-testid="spin-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl text-white flex items-center gap-2">
              <Gift className="h-6 w-6 text-red-400" />
              Spin the Wheel
            </DialogTitle>
            <DialogDescription className="text-slate-300">
              One spin per day - Good luck!
            </DialogDescription>
          </DialogHeader>

          <div className="text-center space-y-6 py-8">
            {!spinResult ? (
              <>
                <div className={`text-8xl ${spinning ? 'animate-spin' : ''}`}>🎡</div>
                <Button
                  onClick={handleSpinWheel}
                  disabled={spinning}
                  className="bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white font-bold px-8 py-6"
                  data-testid="spin-wheel-btn"
                >
                  {spinning ? 'Spinning...' : 'SPIN!'}
                </Button>
              </>
            ) : (
              <>
                <div className="text-6xl">{spinResult.coins_earned > 0 ? '🎉' : '😔'}</div>
                <div className="bg-gradient-to-r from-red-500/20 to-pink-600/20 border border-red-500/30 rounded-lg p-6">
                  <p className="text-white font-bold text-2xl mb-2">{spinResult.message}</p>
                  {spinResult.coins_earned > 0 && (
                    <p className="text-yellow-400 font-bold text-3xl">+{spinResult.coins_earned} Coins</p>
                  )}
                </div>
                <Button
                  onClick={() => {
                    setSpinOpen(false);
                    setSpinResult(null);
                  }}
                  className="bg-slate-700 hover:bg-slate-600 text-white"
                >
                  Close
                </Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Scratch Card Dialog */}
      <Dialog open={scratchOpen} onOpenChange={setScratchOpen}>
        <DialogContent className="bg-slate-900 border-slate-700" data-testid="scratch-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl text-white flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-blue-400" />
              Scratch Card
            </DialogTitle>
            <DialogDescription className="text-slate-300">
              Scratch to reveal your prize! (3 attempts daily)
            </DialogDescription>
          </DialogHeader>

          <div className="text-center space-y-6 py-8">
            {!scratchResult ? (
              <>
                <div className="relative">
                  <div className={`text-8xl ${scratching ? 'blur-md' : ''}`}>🎫</div>
                  {scratching && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="animate-spin text-4xl">✨</div>
                    </div>
                  )}
                </div>
                <Button
                  onClick={handleScratchCard}
                  disabled={scratching}
                  className="bg-gradient-to-r from-blue-500 to-cyan-600 hover:from-blue-600 hover:to-cyan-700 text-white font-bold px-8 py-6"
                  data-testid="scratch-card-btn"
                >
                  {scratching ? 'Scratching...' : 'SCRATCH!'}
                </Button>
              </>
            ) : (
              <>
                <div className="text-6xl">{scratchResult.coins_earned > 0 ? '🎉' : '😔'}</div>
                <div className="bg-gradient-to-r from-blue-500/20 to-cyan-600/20 border border-blue-500/30 rounded-lg p-6">
                  {scratchResult.coins_earned > 0 ? (
                    <p className="text-yellow-400 font-bold text-3xl">+{scratchResult.coins_earned} Coins</p>
                  ) : (
                    <p className="text-slate-300 font-bold text-xl">Better luck next time!</p>
                  )}
                  <p className="text-sm text-slate-300 mt-2">{scratchResult.attempts_left} attempts left today</p>
                </div>
                <Button
                  onClick={() => {
                    setScratchOpen(false);
                    setScratchResult(null);
                  }}
                  className="bg-slate-700 hover:bg-slate-600 text-white"
                >
                  Close
                </Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EarnCoins;
