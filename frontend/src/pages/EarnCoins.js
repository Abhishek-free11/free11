import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Coins, Zap, CheckCircle2, Trophy, Sparkles, Gift, Dices, Spade, Target, Star, Tv, Heart, Layers } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { playCoinSound, playCelebrationSound, playWinSound } from '../utils/sounds';
import confetti from 'canvas-confetti';

const EarnCoins = () => {
  const { user, updateUser } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('howto');

  const [quizOpen, setQuizOpen] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState([]);
  const [quizResult, setQuizResult] = useState(null);

  const [spinOpen, setSpinOpen] = useState(false);
  const [spinning, setSpinning] = useState(false);
  const [spinResult, setSpinResult] = useState(null);

  const [scratchOpen, setScratchOpen] = useState(false);
  const [scratching, setScratching] = useState(false);
  const [scratchResult, setScratchResult] = useState(null);

  useEffect(() => { fetchTasks(); }, []);

  const fetchTasks = async () => {
    try { const r = await api.getTasks(); setTasks(r.data); } catch {}
  };

  const handleCompleteTask = async (taskId) => {
    setLoading(true);
    try {
      const response = await api.completeTask(taskId);
      playCoinSound();
      confetti({ particleCount: 50, spread: 60, origin: { y: 0.6 } });
      toast.success(response.data.message, { description: `+${response.data.coins_earned} coins` });
      updateUser({ coins_balance: response.data.new_balance });
      fetchTasks();
    } catch (error) { toast.error(error.response?.data?.detail || t('earn_page.quiz_challenge')); }
    finally { setLoading(false); }
  };

  const quizQuestions = [
    { question: 'What is FREE11?', options: ['A Consumption Operating System', 'A Gaming App', 'A Payment App', 'A Social Network'], correct: 0 },
    { question: 'How do you earn Free Coins?', options: ['Buy them', 'Borrow them', 'Play games and complete tasks', 'Gift them'], correct: 2 },
    { question: 'Can you withdraw Free Coins as cash?', options: ['Yes', 'Sometimes', 'No, redeem for products only', 'Only in India'], correct: 2 },
    { question: 'What is PROGA?', options: ['A product', 'A payment method', 'A game', 'Regulatory compliance framework'], correct: 3 },
    { question: 'Best way to maximize coins?', options: ['Daily check-ins and streaks', 'Share with friends', 'Complete all tasks', 'All of the above'], correct: 0 },
  ];

  const handleQuizSubmit = async () => {
    if (quizAnswers.length !== quizQuestions.length) { toast.error(t('auth.must_answer_all')); return; }
    setLoading(true);
    try {
      const response = await api.playQuiz(quizAnswers);
      setQuizResult(response.data);
      if (response.data.coins_earned > 0) {
        playWinSound();
        confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
        updateUser({ coins_balance: response.data.new_balance });
      }
    } catch (error) { toast.error(error.response?.data?.detail || 'Quiz failed'); }
    finally { setLoading(false); }
  };

  const handleSpinWheel = async () => {
    setSpinning(true);
    try {
      const response = await api.spinWheel();
      setTimeout(() => {
        setSpinResult(response.data);
        setSpinning(false);
        if (response.data.coins_earned > 0) {
          playCelebrationSound();
          confetti({ particleCount: 80, spread: 60, origin: { y: 0.6 } });
          updateUser({ coins_balance: response.data.new_balance });
        }
      }, 2000);
    } catch (error) { setSpinning(false); toast.error(error.response?.data?.detail || 'Spin failed'); }
  };

  const handleScratchCard = async () => {
    setScratching(true);
    try {
      const response = await api.scratchCard();
      setTimeout(() => {
        setScratchResult(response.data);
        setScratching(false);
        if (response.data.coins_earned > 0) {
          playCoinSound();
          confetti({ particleCount: 60, spread: 50, origin: { y: 0.6 } });
          updateUser({ coins_balance: response.data.new_balance });
        }
      }, 1500);
    } catch (error) { setScratching(false); toast.error(error.response?.data?.detail || 'Scratch failed'); }
  };

  const TABS = [
    { key: 'howto', label: 'How to Earn', icon: Tv },
    { key: 'games', label: 'Mini Games', icon: Zap },
    { key: 'tasks', label: 'Tasks', icon: CheckCircle2 },
  ];

  const howToItems = [
    { icon: Trophy,  label: 'Fantasy Contests',       desc: 'Build a dream team & win big',        reward: 'Up to 500 coins',    color: '#C6A052', path: '/fantasy'      },
    { icon: Target,  label: 'Match Predictions',       desc: 'Predict the winning team',            reward: '+50 per correct',    color: '#60a5fa', path: '/predict'      },
    { icon: Zap,     label: 'Over Outcome',            desc: 'Predict runs each over (live)',        reward: '+25 per correct',    color: '#a78bfa', path: '/match-centre' },
    { icon: Gift,    label: 'Ball-by-Ball',            desc: 'Predict every ball outcome',          reward: '+5–15 per correct',  color: '#4ade80', path: '/match-centre' },
    { icon: Heart,   label: 'Card Games',              desc: 'Win Teen Patti, Rummy or Poker',      reward: '+25–60 coins/win',   color: '#a855f7', path: '/games'        },
    { icon: Star,    label: 'Daily Tasks',             desc: 'Complete quick tasks each day',       reward: '+10–100 coins',      color: '#f87171', path: '/earn'         },
  ];

  const miniGames = [
    { key: 'quiz', icon: '🏏', label: t('earn_page.quiz_title'), desc: t('earn_page.quiz_desc'), badge: t('earn_page.up_to_50'), btnLabel: t('earn_page.play_now'), onClick: () => setQuizOpen(true), color: '#C6A052', testId: 'quiz-card' },
    { key: 'spin', icon: '🎡', label: t('earn_page.lucky_spin'), desc: t('earn_page.spin_desc'), badge: t('earn_page.daily_spin_badge'), btnLabel: t('earn_page.spin_now'), onClick: () => setSpinOpen(true), color: '#f87171', testId: 'spin-card' },
    { key: 'scratch', icon: '🎫', label: t('earn_page.golden_scratch'), desc: t('earn_page.scratch_desc'), badge: t('earn_page.three_daily'), btnLabel: t('earn_page.scratch_now'), onClick: () => setScratchOpen(true), color: '#60a5fa', testId: 'scratch-card' },
    { key: 'teen_patti', icon: '♥', label: 'Teen Patti vs AI', desc: 'Beat the AI at 3-card poker', badge: '+40 coins daily', btnLabel: 'Play Now', onClick: () => navigate('/games/teen_patti/play'), color: '#a855f7', testId: 'teen-patti-card' },
    { key: 'rummy', icon: '♠', label: 'Rummy vs AI', desc: '13-card Indian Rummy vs AI', badge: '+50 coins daily', btnLabel: 'Play Now', onClick: () => navigate('/games/rummy/play'), color: '#ef4444', testId: 'rummy-card' },
    { key: 'poker', icon: '♦', label: 'Poker vs AI', desc: "Texas Hold'em vs AI", badge: '+60 coins daily', btnLabel: 'Play Now', onClick: () => navigate('/games/poker/play'), color: '#22c55e', testId: 'poker-card' },
    { key: 'solitaire', icon: '🂡', label: 'Solitaire', desc: 'Clear the deck and win coins', badge: '+25 coins daily', btnLabel: 'Play Now', onClick: () => navigate('/games/solitaire'), color: '#f59e0b', testId: 'solitaire-card' },
  ];

  return (
    <div className="min-h-screen bg-[#0F1115] pb-28 md:pb-6" data-testid="earn-coins-page">
      <div className="fixed pointer-events-none" style={{ top: 0, left: '50%', transform: 'translateX(-50%)', width: '70vw', height: '30vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.04) 0%, transparent 70%)', zIndex: 0 }} />
      <Navbar />

      <div className="relative z-10 max-w-screen-xl mx-auto px-3 sm:px-4 py-4 space-y-4 animate-slide-up">
        {/* Header */}
        <div>
          <h1 className="font-heading text-3xl tracking-widest text-white">COIN <span style={{ color: '#C6A052' }}>BOOSTERS</span></h1>
          <p className="text-sm mt-1" style={{ color: '#8A9096' }}>Accelerate your earnings with bonus activities</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setActiveTab(key)}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-heading tracking-wider transition-all"
              style={activeTab === key
                ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115', fontWeight: 700 }
                : { background: 'rgba(255,255,255,0.04)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.06)' }}>
              <Icon className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>

        {/* How to Earn */}
        {activeTab === 'howto' && (
          <div className="space-y-2" data-testid="how-to-earn-section">
            {howToItems.map(({ icon: Icon, label, desc, reward, color, path }) => (
              <button key={label}
                className="w-full text-left card-broadcast p-3 flex items-center gap-3 cursor-pointer hover-lift transition-all active:scale-95"
                data-testid={`earn-item-${label.replace(/\s+/g, '-').toLowerCase()}`}
                onClick={() => { if (path === '/earn') setActiveTab('tasks'); else navigate(path); }}
              >
                <div className="p-2 rounded-xl flex-shrink-0" style={{ background: `${color}18` }}>
                  <Icon className="h-5 w-5" style={{ color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <h4 className="font-bold text-white text-sm">{label}</h4>
                    <span className="text-xs font-bold flex-shrink-0" style={{ color }}>{reward}</span>
                  </div>
                  <p className="text-xs mt-0.5 truncate" style={{ color: '#8A9096' }}>{desc}</p>
                </div>
                <svg className="h-4 w-4 flex-shrink-0" style={{ color: '#8A9096' }} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7"/></svg>
              </button>
            ))}
          </div>
        )}

        {/* Mini Games */}
        {activeTab === 'games' && (
          <div className="grid sm:grid-cols-3 gap-3">
            {miniGames.map(({ key, icon, label, desc, badge, btnLabel, onClick, color, testId }) => (
              <div key={key} className="card-broadcast p-4 cursor-pointer hover-lift" onClick={onClick} data-testid={testId}>
                <div className="flex items-start justify-between mb-3">
                  <span className="text-4xl">{icon}</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-bold"
                    style={{ background: `${color}15`, color, border: `1px solid ${color}25` }}>{badge}</span>
                </div>
                <h3 className="font-bold text-white mb-1">{label}</h3>
                <p className="text-xs mb-4" style={{ color: '#8A9096' }}>{desc}</p>
                <button className="btn-gold w-full h-9 rounded-lg text-xs">{btnLabel}</button>
              </div>
            ))}
          </div>
        )}

        {/* Tasks */}
        {activeTab === 'tasks' && (
          <div className="space-y-3">
            {tasks.map((task) => (
              <div key={task.id} className="card-broadcast p-4" data-testid={`task-${task.id}`}>
                <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-bold text-white">{task.title}</h3>
                      {task.completed && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold flex items-center gap-1"
                          style={{ background: 'rgba(74,222,128,0.15)', color: '#4ade80' }}>
                          <CheckCircle2 className="h-3 w-3" /> Done
                        </span>
                      )}
                    </div>
                    <p className="text-sm" style={{ color: '#8A9096' }}>{task.description}</p>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="coin-indicator inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold">
                      <Coins className="h-3 w-3" /> {task.coins}
                    </span>
                    <button onClick={() => handleCompleteTask(task.id)} disabled={task.completed || loading}
                      className="btn-gold px-4 h-9 rounded-lg text-xs disabled:opacity-40"
                      data-testid={`complete-task-${task.id}`}>
                      {task.completed ? 'Done' : 'Complete'}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Quiz Dialog ── */}
      <Dialog open={quizOpen} onOpenChange={setQuizOpen}>
        <DialogContent className="max-w-lg" style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.2)' }} data-testid="quiz-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Trophy className="h-5 w-5" style={{ color: '#C6A052' }} /> Quiz Challenge
            </DialogTitle>
            <DialogDescription style={{ color: '#8A9096' }}>Answer correctly to maximize coins</DialogDescription>
          </DialogHeader>
          {!quizResult ? (
            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
              {quizQuestions.map((q, qi) => (
                <div key={qi} className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <p className="text-sm font-bold text-white mb-3">Q{qi + 1}. {q.question}</p>
                  <div className="space-y-2">
                    {q.options.map((opt, oi) => (
                      <button key={oi} onClick={() => { const a = [...quizAnswers]; a[qi] = oi; setQuizAnswers(a); }}
                        className="w-full text-left px-3 py-2 rounded-lg text-sm transition-all"
                        style={quizAnswers[qi] === oi
                          ? { background: 'rgba(198,160,82,0.15)', border: '1px solid #C6A052', color: '#E0B84F' }
                          : { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', color: '#BFC3C8' }}>
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <button onClick={handleQuizSubmit} disabled={quizAnswers.length !== quizQuestions.length || loading}
                className="btn-gold w-full h-11 rounded-xl text-sm disabled:opacity-40"
                data-testid="submit-quiz-btn">
                {loading ? 'Submitting...' : 'Submit Quiz'}
              </button>
            </div>
          ) : (
            <div className="text-center py-6">
              <div className="text-5xl mb-4">{quizResult.score_percentage >= 60 ? '🎉' : '😔'}</div>
              <h3 className="text-2xl font-bold text-white mb-1">Score: {quizResult.score_percentage}%</h3>
              <p className="text-sm mb-4" style={{ color: '#8A9096' }}>{quizResult.correct_count}/{quizResult.total_questions} correct</p>
              <div className="p-4 rounded-xl mb-4" style={{ background: 'rgba(198,160,82,0.1)', border: '1px solid rgba(198,160,82,0.25)' }}>
                <p className="font-numbers text-3xl font-black" style={{ color: '#C6A052' }}>+{quizResult.coins_earned} Coins</p>
              </div>
              <button onClick={() => { setQuizOpen(false); setQuizResult(null); setQuizAnswers([]); }}
                className="btn-outline-gold px-8 h-10 rounded-xl text-sm">Close</button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* ── Spin Dialog ── */}
      <Dialog open={spinOpen} onOpenChange={setSpinOpen}>
        <DialogContent className="max-w-sm" style={{ background: '#1B1E23', border: '1px solid rgba(239,68,68,0.25)' }} data-testid="spin-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Gift className="h-5 w-5 text-red-400" /> Spin the Wheel
            </DialogTitle>
            <DialogDescription style={{ color: '#8A9096' }}>One spin per day — Good luck!</DialogDescription>
          </DialogHeader>
          <div className="text-center py-8 space-y-5">
            {!spinResult ? (
              <>
                <div className={`text-7xl ${spinning ? 'animate-spin' : ''}`}>🎡</div>
                <button onClick={handleSpinWheel} disabled={spinning}
                  className="btn-gold px-10 h-12 rounded-xl text-sm disabled:opacity-50"
                  data-testid="spin-wheel-btn">
                  {spinning ? 'Spinning...' : 'SPIN!'}
                </button>
              </>
            ) : (
              <>
                <div className="text-5xl">{spinResult.coins_earned > 0 ? '🎉' : '😔'}</div>
                <div className="p-4 rounded-xl" style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)' }}>
                  <p className="text-white font-bold text-lg mb-1">{spinResult.message}</p>
                  {spinResult.coins_earned > 0 && <p className="font-numbers text-3xl font-black" style={{ color: '#C6A052' }}>+{spinResult.coins_earned} Coins</p>}
                </div>
                <button onClick={() => { setSpinOpen(false); setSpinResult(null); }} className="btn-outline-gold px-8 h-10 rounded-xl text-sm">Close</button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* ── Scratch Dialog ── */}
      <Dialog open={scratchOpen} onOpenChange={setScratchOpen}>
        <DialogContent className="max-w-sm" style={{ background: '#1B1E23', border: '1px solid rgba(96,165,250,0.25)' }} data-testid="scratch-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-400" /> Scratch Card
            </DialogTitle>
            <DialogDescription style={{ color: '#8A9096' }}>Scratch to reveal your prize! (3 attempts daily)</DialogDescription>
          </DialogHeader>
          <div className="text-center py-8 space-y-5">
            {!scratchResult ? (
              <>
                <div className={`text-7xl ${scratching ? 'blur-md' : ''}`}>🎫</div>
                <button onClick={handleScratchCard} disabled={scratching}
                  className="btn-gold px-10 h-12 rounded-xl text-sm disabled:opacity-50"
                  data-testid="scratch-card-btn">
                  {scratching ? 'Scratching...' : 'SCRATCH!'}
                </button>
              </>
            ) : (
              <>
                <div className="text-5xl">{scratchResult.coins_earned > 0 ? '🎉' : '😔'}</div>
                <div className="p-4 rounded-xl" style={{ background: 'rgba(96,165,250,0.1)', border: '1px solid rgba(96,165,250,0.25)' }}>
                  {scratchResult.coins_earned > 0
                    ? <p className="font-numbers text-3xl font-black" style={{ color: '#C6A052' }}>+{scratchResult.coins_earned} Coins</p>
                    : <p className="text-white font-bold text-lg">Better luck next time!</p>}
                  <p className="text-xs mt-1" style={{ color: '#8A9096' }}>{scratchResult.attempts_left} attempts left today</p>
                </div>
                <button onClick={() => { setScratchOpen(false); setScratchResult(null); }} className="btn-outline-gold px-8 h-10 rounded-xl text-sm">Close</button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EarnCoins;
