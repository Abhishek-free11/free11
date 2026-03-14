import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import Navbar from '../components/Navbar';
import FirstTimeTutorial from '../components/FirstTimeTutorial';
import WishlistGoal from '../components/WishlistGoal';
import DailyPuzzle from '../components/DailyPuzzle';
import WeeklyReportCard from '../components/WeeklyReportCard';
import IPLCarousel from '../components/IPLCarousel';
import QuestModal from '../components/QuestModal';
import LiveActivityTicker from '../components/LiveActivityTicker';
import {
  Coins, Zap, Gift, Trophy, TrendingUp, Calendar, Flame,
  Target, ShoppingBag, ChevronRight, Star, Play, Award, Users,
  CheckCircle, Circle, ArrowRight, Sparkles, X
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { playCelebrationSound } from '../utils/sounds';
import confetti from 'canvas-confetti';

import dayjs from 'dayjs';

// IPL 2026 Countdown banner — shows only while days > 0
function IPLCountdown() {
  const days = dayjs('2026-03-28').diff(dayjs(), 'day');
  if (days <= 0) return null;
  return (
    <div className="w-full text-center py-2.5 px-4 font-heading text-sm sm:text-base tracking-wider"
      style={{ background: 'linear-gradient(90deg,#C6A052,#E0B84F,#C6A052)', color: '#0F1115', fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.08em' }}
      data-testid="ipl-countdown-banner">
      T20 League 2026 Starts in {days} Days! — Get Ready for Predictions &amp; Rewards
    </div>
  );
}

// ── Onboarding Checklist — shows until all steps complete ──────────────────
const STEPS = [
  { id: 'checkin',    label: 'Complete daily check-in',       coins: '+15',  path: null },
  { id: 'predict',   label: 'Make your first prediction',     coins: '+20',  path: '/match-centre' },
  { id: 'shop',      label: 'Browse the rewards shop',        coins: null,   path: '/shop' },
  { id: 'earn',      label: 'Play a mini-game',               coins: '+25',  path: '/earn' },
];

function OnboardingChecklist({ user, hasCheckedIn, onDismiss }) {
  const navigate = useNavigate();
  const hasPredicted   = (user?.total_predictions || 0) > 0;
  const hasPlayedGame  = (user?.xp || 0) > 50;
  const dismissed      = sessionStorage.getItem('onboarding_dismissed') === '1';

  const done = { checkin: hasCheckedIn, predict: hasPredicted, shop: false, earn: hasPlayedGame };
  const completedCount = Object.values(done).filter(Boolean).length;
  const allDone = completedCount === STEPS.length;

  // Don't show if all done or dismissed this session
  if (allDone || dismissed) return null;

  return (
    <div
      className="card-broadcast-gold p-4 relative"
      style={{ border: '1px solid rgba(198,160,82,0.4)', background: 'linear-gradient(135deg, rgba(198,160,82,0.08) 0%, rgba(15,17,21,0.95) 100%)' }}
      data-testid="onboarding-checklist"
    >
      <button
        className="absolute top-3 right-3 text-gray-500 hover:text-white"
        onClick={() => { sessionStorage.setItem('onboarding_dismissed', '1'); onDismiss(); }}
        data-testid="dismiss-onboarding-btn"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="h-4 w-4" style={{ color: '#E0B84F' }} />
        <h3 className="font-bold text-white text-sm">Get Started — Earn Your First Rewards</h3>
        <span className="ml-auto text-xs font-bold" style={{ color: '#C6A052' }}>{completedCount}/{STEPS.length}</span>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 rounded-full mb-3" style={{ background: 'rgba(255,255,255,0.06)' }}>
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${(completedCount / STEPS.length) * 100}%`, background: 'linear-gradient(90deg,#C6A052,#E0B84F)' }}
        />
      </div>

      <div className="space-y-2">
        {STEPS.map((step) => {
          const isComplete = done[step.id];
          return (
            <div
              key={step.id}
              onClick={() => !isComplete && step.path && navigate(step.path)}
              className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${!isComplete && step.path ? 'cursor-pointer hover:bg-white/5' : ''}`}
              style={{ background: isComplete ? 'rgba(74,222,128,0.06)' : 'rgba(255,255,255,0.02)', border: `1px solid ${isComplete ? 'rgba(74,222,128,0.2)' : 'rgba(255,255,255,0.05)'}` }}
              data-testid={`onboarding-step-${step.id}`}
            >
              {isComplete
                ? <CheckCircle className="h-4 w-4 flex-shrink-0 text-green-400" />
                : <Circle className="h-4 w-4 flex-shrink-0" style={{ color: '#8A9096' }} />
              }
              <span className={`text-xs flex-1 ${isComplete ? 'line-through' : 'text-white'}`} style={{ color: isComplete ? '#8A9096' : undefined }}>
                {step.label}
              </span>
              {step.coins && !isComplete && (
                <span className="text-xs font-bold" style={{ color: '#4ade80' }}>{step.coins}</span>
              )}
              {!isComplete && step.path && (
                <ArrowRight className="h-3.5 w-3.5" style={{ color: '#C6A052' }} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── First Prediction Hero Banner ────────────────────────────────────────────
function FirstPredictionBanner({ liveMatch, onNavigate }) {
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem('first_pred_banner_dismissed') === '1'
  );
  if (dismissed) return null;
  return (
    <div
      className="relative overflow-hidden rounded-2xl p-5"
      style={{
        background: 'linear-gradient(135deg, #1a1300 0%, #2a1f00 50%, #1a1300 100%)',
        border: '1px solid rgba(198,160,82,0.5)',
        boxShadow: '0 0 30px rgba(198,160,82,0.12)'
      }}
      data-testid="first-prediction-banner"
    >
      {/* Dismiss button */}
      <button
        className="absolute top-3 right-3 text-gray-600 hover:text-white"
        onClick={() => { sessionStorage.setItem('first_pred_banner_dismissed', '1'); setDismissed(true); }}
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>

      {/* Glow */}
      <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse at 50% -20%, rgba(198,160,82,0.15) 0%, transparent 70%)' }} />

      <div className="relative">
        <div className="flex items-start gap-3 mb-4">
          <div className="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)' }}>
            <Target className="h-5 w-5 text-[#0F1115]" />
          </div>
          <div>
            <h3 className="font-heading text-lg text-white tracking-wide" style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.06em' }}>
              MAKE YOUR FIRST PREDICTION
            </h3>
            <p className="text-xs mt-0.5" style={{ color: '#8A9096' }}>Predict cricket outcomes and earn FREE Coins</p>
          </div>
        </div>

        {/* How it works - 3 steps */}
        <div className="grid grid-cols-3 gap-2 mb-4">
          {[
            { step: '1', text: 'Pick a live or upcoming match' },
            { step: '2', text: 'Make your prediction (free)' },
            { step: '3', text: 'Win up to +100 coins if correct' },
          ].map(({ step, text }) => (
            <div key={step} className="text-center p-2 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
              <div className="w-6 h-6 rounded-full mx-auto mb-1.5 flex items-center justify-center text-xs font-black"
                style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)', color: '#0F1115' }}>{step}</div>
              <p className="text-[10px] leading-tight" style={{ color: '#8A9096' }}>{text}</p>
            </div>
          ))}
        </div>

        <button
          onClick={() => onNavigate(liveMatch?.match_id ? `/match/${liveMatch.match_id}` : '/match-centre')}
          className="btn-gold w-full h-11 rounded-xl text-sm font-bold ripple"
          style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.08em', fontSize: '15px' }}
          data-testid="first-prediction-cta"
        >
          {liveMatch ? `PREDICT ${liveMatch.team1_short} vs ${liveMatch.team2_short}` : 'VIEW UPCOMING MATCHES'} →
        </button>
      </div>
    </div>
  );
}

const Dashboard = () => {
  const { user, updateUser } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();
  const [demandProgress, setDemandProgress] = useState(null);
  const [liveMatch, setLiveMatch] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [checkinLoading, setCheckinLoading] = useState(false);
  const [canCheckin, setCanCheckin] = useState(true);
  const [loading, setLoading] = useState(true);
  const [showTutorial, setShowTutorial] = useState(false);
  const [showQuestModal, setShowQuestModal] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(true);

  const isNewUser   = !user?.total_predictions || user.total_predictions === 0;
  const hasCheckedIn = user?.last_checkin === new Date().toISOString().split('T')[0];

  useEffect(() => {
    const checkTutorialStatus = async () => {
      try {
        const response = await api.getTutorialStatus();
        if (!response.data.tutorial_completed) setShowTutorial(true);
      } catch {}
    };
    checkTutorialStatus();
  }, []);

  // Check quest eligibility after data loads
  useEffect(() => {
    if (!loading && user) {
      const checkQuest = async () => {
        try {
          // Only show quest modal if not shown today
          const seenKey = `quest_seen_${new Date().toISOString().split('T')[0]}`;
          if (sessionStorage.getItem(seenKey)) return;
          const { data } = await api.v2QuestStatus();
          if (data.eligible) {
            // Slight delay so dashboard loads first
            setTimeout(() => setShowQuestModal(true), 2500);
          }
        } catch {}
      };
      checkQuest();
    }
  }, [loading, user]);

  const handleQuestDismiss = () => {
    const seenKey = `quest_seen_${new Date().toISOString().split('T')[0]}`;
    sessionStorage.setItem(seenKey, '1');
    setShowQuestModal(false);
  };

  const handleTutorialComplete = async () => {
    try { await api.completeTutorial(); } catch {}
    setShowTutorial(false);
    toast.success('Welcome to FREE11!');
  };

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [progressRes, transactionsRes, leaderboardRes, matchesRes] = await Promise.all([
        api.getDemandProgress(),
        api.getTransactions(0, 5),
        api.getLeaderboard(),
        api.v2EsGetMatches('3', 5).catch(() => ({ data: [] }))
      ]);
      setDemandProgress(progressRes.data);
      // Handle both paginated ({transactions: []}) and legacy ([]) response shapes
      const txData = transactionsRes.data;
      const txList = Array.isArray(txData) ? txData : (txData?.transactions || []);
      setTransactions(txList.slice(0, 5));
      setLeaderboard(leaderboardRes.data);
      const esMatches = Array.isArray(matchesRes.data) ? matchesRes.data : [];
      if (esMatches.length > 0) {
        const m = esMatches[0];
        setLiveMatch({ team1_short: m.team1_short, team2_short: m.team2_short, team1_score: m.team1_score, team2_score: m.team2_score, venue: m.venue, match_id: m.match_id, status: m.status, short_title: m.short_title, series: m.series });
      } else {
        const upcomingRes = await api.v2EsGetMatches('1', 5).catch(() => ({ data: [] }));
        const upMatches = Array.isArray(upcomingRes.data) ? upcomingRes.data : [];
        if (upMatches.length > 0) {
          const m = upMatches[0];
          setLiveMatch({ team1_short: m.team1_short, team2_short: m.team2_short, team1_score: m.team1_score, team2_score: m.team2_score, venue: m.venue, match_id: m.match_id, status: m.status, short_title: m.short_title, series: m.series });
        }
      }
    } catch {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchDashboardData(); }, [fetchDashboardData]);

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    setCanCheckin(user?.last_checkin !== today);
  }, [user]);

  const handleCheckin = async () => {
    setCheckinLoading(true);
    try {
      const response = await api.dailyCheckin();
      playCelebrationSound();
      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
      toast.success(`${response.data.message}`, { description: `Streak: ${response.data.streak_days} days | +${response.data.coins_earned} coins` });
      updateUser({ coins_balance: response.data.new_balance, streak_days: response.data.streak_days, last_checkin: new Date().toISOString().split('T')[0] });
      setCanCheckin(false);
      fetchDashboardData();
    } catch (error) {
      toast.error(error.response?.data?.detail || t('dashboard.checkin_failed'));
    } finally { setCheckinLoading(false); }
  };

  const accuracy = user?.total_predictions > 0 ? Math.round((user.correct_predictions / user.total_predictions) * 100) : 0;

  return (
    <div className="min-h-screen bg-[#0F1115] pb-28 md:pb-6" data-testid="dashboard-page">
      {/* Glow orb */}
      <div className="fixed pointer-events-none" style={{ top: '-10%', left: '50%', transform: 'translateX(-50%)', width: '80vw', height: '40vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.05) 0%, transparent 70%)', zIndex: 0 }} />
      {showTutorial && <FirstTimeTutorial onComplete={handleTutorialComplete} onSkip={handleTutorialComplete} />}
      {showQuestModal && <QuestModal onDismiss={handleQuestDismiss} />}
      <Navbar />
      <IPLCountdown />

      <div className="relative z-10 max-w-screen-xl mx-auto px-3 sm:px-4 py-4 space-y-4 animate-slide-up">

        {/* ── IPL Carousel ── */}
        <IPLCarousel />

        {/* ── ONBOARDING CHECKLIST — show for new users until dismissed ── */}
        {showOnboarding && (
          <OnboardingChecklist
            user={user}
            hasCheckedIn={hasCheckedIn}
            onDismiss={() => setShowOnboarding(false)}
          />
        )}

        {/* ── FIRST PREDICTION HERO BANNER — users with 0 predictions ── */}
        {isNewUser && (
          <FirstPredictionBanner
            liveMatch={liveMatch}
            onNavigate={navigate}
          />
        )}

        {/* ── User Header ── */}
        <div className="card-broadcast-gold p-4 flex items-center gap-3" data-testid="user-header">
          <div className="w-12 h-12 rounded-2xl flex-shrink-0 flex items-center justify-center text-xl font-black text-[#0F1115] animate-coin-glow"
            style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)' }}>
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-base font-bold text-white truncate">{user?.name?.split(' ')[0]}'s XI</h2>
            <div className="flex items-center gap-1.5 text-xs">
              <span style={{ color: '#8A9096' }}>Lv {user?.level || 1}</span>
              <span style={{ color: '#8A9096' }}>·</span>
              <span style={{ color: '#C6A052' }} className="font-medium">{demandProgress?.rank?.name || (['Rookie','Amateur','Pro','Expert','Legend'][(user?.level || 1) - 1] || 'Rookie')}</span>
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="flex items-center gap-1 justify-end">
              <Coins className="h-4 w-4" style={{ color: '#C6A052' }} />
              <span className="text-xl font-black text-white font-numbers">{user?.coins_balance || 0}</span>
            </div>
            <p className="text-[10px]" style={{ color: '#8A9096' }}>{t('dashboard.balance')}</p>
          </div>
        </div>

        {/* ── Quick Stats Bar ── */}
        <div className="grid grid-cols-3 gap-2">
          {[
            { icon: Flame, label: t('dashboard.streak'), value: `${user?.streak_days || 0}d`, color: '#E0B84F' },
            { icon: Target, label: t('dashboard.accuracy'), value: `${accuracy}%`, color: '#4ade80' },
            { icon: Award, label: 'XP', value: user?.xp || 0, color: '#a78bfa' },
          ].map(({ icon: Icon, label, value, color }) => (
            <div key={label} className="card-broadcast p-3 text-center">
              <Icon className="h-4 w-4 mx-auto mb-1" style={{ color }} />
              <div className="font-numbers font-bold text-base text-white">{value}</div>
              <div className="text-[10px]" style={{ color: '#8A9096' }}>{label}</div>
            </div>
          ))}
        </div>

        {/* ── XP Progress ── */}
        {demandProgress?.rank?.next_rank && (
          <div className="card-broadcast px-4 py-3">
            <div className="flex justify-between text-xs mb-2">
              <span style={{ color: '#8A9096' }}>Next rank: <span className="text-white font-medium">{demandProgress.rank.next_rank}</span></span>
              <span style={{ color: '#C6A052' }}>{demandProgress.rank.xp_to_next} XP left</span>
            </div>
            <div className="h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <div className="h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, ((user?.xp || 0) / ((demandProgress.rank.xp_to_next || 1) + (user?.xp || 0))) * 100)}%`, background: 'linear-gradient(90deg, #C6A052, #E0B84F)' }} />
            </div>
          </div>
        )}

        {/* ── Wishlist Goal ── */}
        <WishlistGoal coinsBalance={user?.coins_balance || 0} />

        {/* ── Daily Puzzle ── */}
        <DailyPuzzle onCoinsEarned={(amt) => updateUser({ coins_balance: (user?.coins_balance || 0) + amt })} />

        {/* ── Live Match Hero ── */}
        <div className="card-broadcast-gold p-4" data-testid="live-cricket-hero">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-heading text-xl tracking-wider text-white">{t('dashboard.live_cricket')}</h3>
            {liveMatch?.status === 'live' && (
              <span className="badge-live flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-live-pulse" />
                {t('dashboard.live_now_badge')}
              </span>
            )}
          </div>

          {liveMatch ? (
            <div>
              <div className="flex items-center justify-between mb-3 px-2">
                <div className="text-center flex-1">
                  <div className="text-lg font-black text-white">{liveMatch.team1_short}</div>
                  <div className="font-numbers text-xl font-bold" style={{ color: '#C6A052' }}>{liveMatch.team1_score || '-'}</div>
                </div>
                <div className="text-xs font-bold px-3" style={{ color: '#8A9096' }}>VS</div>
                <div className="text-center flex-1">
                  <div className="text-lg font-black text-white">{liveMatch.team2_short}</div>
                  <div className="font-numbers text-xl font-bold" style={{ color: '#BFC3C8' }}>{liveMatch.team2_score || '-'}</div>
                </div>
              </div>
              {liveMatch.venue && <p className="text-[10px] text-center mb-3" style={{ color: '#8A9096' }}>{liveMatch.venue}</p>}
              <button
                onClick={() => navigate(`/match/${liveMatch.match_id || 'upcoming'}`)}
                className="btn-gold w-full h-11 rounded-xl text-sm ripple"
                data-testid="predict-now-btn"
              >
                {liveMatch.status === 'live' ? t('match_centre.live') : t('dashboard.view_match')} →
              </button>
            </div>
          ) : (
            <div className="text-center py-6">
              <div className="text-4xl mb-3">🏏</div>
              <p className="text-white font-medium mb-1">{t('dashboard.ipl_coming')}</p>
              <p className="text-sm mb-4" style={{ color: '#8A9096' }}>{t('dashboard.get_ready')}</p>
              <button onClick={() => navigate('/match-centre')} className="btn-outline-gold px-6 h-9 rounded-lg text-sm">
                {t('dashboard.view_upcoming')}
              </button>
            </div>
          )}
        </div>

        {/* ── Daily Check-in ── */}
        <div className="card-broadcast p-4" data-testid="checkin-card">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" style={{ color: '#C6A052' }} />
              <span className="font-medium text-white">{t('dashboard.daily_checkin')}</span>
            </div>
            <div className="flex items-center gap-1">
              <Flame className="h-4 w-4 text-orange-400" />
              <span className="text-sm font-bold text-orange-400">{user?.streak_days || 0} {t('dashboard.days')}</span>
            </div>
          </div>
          {canCheckin ? (
            <button onClick={handleCheckin} disabled={checkinLoading}
              className="btn-gold w-full h-11 rounded-xl text-sm ripple disabled:opacity-50"
              data-testid="checkin-btn">
              {checkinLoading ? t('dashboard.checking_in') : t('dashboard.check_in_now')}
            </button>
          ) : (
            <div className="p-3 rounded-xl text-center" style={{ background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)' }}>
              <p className="text-green-400 font-medium text-sm">{t('dashboard.checked_in_today')} ✓</p>
              <p className="text-xs mt-0.5" style={{ color: '#8A9096' }}>{t('dashboard.come_back_tomorrow')}</p>
            </div>
          )}
        </div>

        {/* ── Next Reward Progress ── */}
        {demandProgress?.next_reward && (
          <div className="card-broadcast p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-white">{t('dashboard.progress_reward')}</h3>
              <span className="text-xl font-numbers font-black" style={{ color: '#C6A052' }}>{user?.coins_balance || 0}</span>
            </div>
            <div className="flex items-center gap-3">
              <img src={demandProgress.next_reward.image_url} alt={demandProgress.next_reward.name}
                className="w-14 h-14 rounded-xl object-cover flex-shrink-0"
                onError={(e) => e.target.src = 'https://via.placeholder.com/56'}
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-white truncate">{demandProgress.next_reward.name}</p>
                <div className="h-2 rounded-full my-1.5" style={{ background: 'rgba(255,255,255,0.06)' }}>
                  <div className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, demandProgress.next_reward.progress)}%`, background: 'linear-gradient(90deg, #C6A052, #E0B84F)' }} />
                </div>
                <p className="text-xs" style={{ color: '#8A9096' }}>
                  {demandProgress.next_reward.coins_needed > 0
                    ? <span style={{ color: '#C6A052' }}>{demandProgress.next_reward.coins_needed} coins to go</span>
                    : <span className="text-green-400 font-bold">{t('dashboard.ready_redeem')} 🎉</span>}
                </p>
              </div>
              <button onClick={() => navigate('/shop')} disabled={demandProgress.next_reward.coins_needed > 0}
                className="btn-gold px-3 h-9 rounded-lg text-xs flex-shrink-0 disabled:opacity-40">
                {demandProgress.next_reward.coins_needed > 0 ? t('dashboard.earn_more') : t('dashboard.redeem')}
              </button>
            </div>
          </div>
        )}

        {/* ── Skill Stats ── */}
        <div className="card-broadcast p-4">
          <h3 className="font-medium text-white mb-3 flex items-center gap-2">
            <Target className="h-4 w-4" style={{ color: '#C6A052' }} />
            {t('dashboard.skill_stats')}
          </h3>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: t('dashboard.accuracy_label'), value: `${demandProgress?.prediction_stats?.accuracy || 0}%`, color: '#4ade80' },
              { label: t('dashboard.correct_label'), value: demandProgress?.prediction_stats?.correct || 0, color: '#4ade80' },
              { label: t('dashboard.streak_label'), value: demandProgress?.prediction_stats?.streak || 0, color: '#E0B84F' },
              { label: t('dashboard.total_label'), value: demandProgress?.prediction_stats?.total || 0, color: '#BFC3C8' },
            ].map(({ label, value, color }) => (
              <div key={label} className="p-3 rounded-xl text-center" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div className="text-2xl font-black font-numbers" style={{ color }}>{value}</div>
                <div className="text-xs mt-0.5" style={{ color: '#8A9096' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Top Leaderboard ── */}
        <div className="card-broadcast p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-white flex items-center gap-2">
              <Trophy className="h-4 w-4" style={{ color: '#C6A052' }} />
              {t('dashboard.skill_leaderboard')}
            </h3>
            <button onClick={() => navigate('/leaderboards')} className="text-xs" style={{ color: '#C6A052' }}>
              View all →
            </button>
          </div>
          {leaderboard.length === 0 ? (
            <p className="text-sm text-center py-4" style={{ color: '#8A9096' }}>{t('dashboard.start_predicting')}</p>
          ) : (
            <div className="space-y-1.5">
              {leaderboard.slice(0, 5).map((player, index) => (
                <div key={player.id} className="flex items-center gap-3 py-2 px-3 rounded-lg"
                  style={{ background: index === 0 ? 'rgba(198,160,82,0.08)' : 'rgba(255,255,255,0.02)', border: index === 0 ? '1px solid rgba(198,160,82,0.2)' : '1px solid transparent' }}>
                  <div className="w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-black"
                    style={{ background: index === 0 ? 'linear-gradient(135deg,#C6A052,#E0B84F)' : index === 1 ? '#BFC3C8' : index === 2 ? '#CD7F32' : '#2A2D33', color: index < 3 ? '#0F1115' : '#8A9096' }}>
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{player.name}</p>
                  </div>
                  <span className="text-xs font-bold" style={{ color: '#4ade80' }}>
                    {player.accuracy !== undefined ? `${player.accuracy}%` : `${player.total_earned}c`}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Community Activity ── */}
        <LiveActivityTicker className="mx-0" />

        {/* ── Recent Transactions ── */}
        <div className="card-broadcast p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium text-white flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-400" />
              {t('dashboard.recent_activity')}
            </h3>
            <button onClick={() => navigate('/ledger')} className="text-xs" style={{ color: '#C6A052' }}>
              View all →
            </button>
          </div>
          {transactions.length === 0 ? (
            <p className="text-sm text-center py-4" style={{ color: '#8A9096' }}>{t('dashboard.no_transactions')}</p>
          ) : (
            <div className="space-y-1.5">
              {transactions.map((tx) => (
                <div key={tx.id} className="flex items-center justify-between py-2 px-3 rounded-lg"
                  style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{tx.description}</p>
                    <p className="text-xs" style={{ color: '#8A9096' }}>{new Date(tx.timestamp).toLocaleDateString()}</p>
                  </div>
                  <span className="text-sm font-bold ml-3 font-numbers" style={{ color: tx.amount > 0 ? '#4ade80' : '#f87171' }}>
                    {tx.amount > 0 ? '+' : ''}{tx.amount}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ── Quick Actions ── */}
        <div className="grid grid-cols-3 gap-2">
          {[
            { icon: Play, label: 'Earn Coins', path: '/earn', color: '#a78bfa' },
            { icon: ShoppingBag, label: 'Shop', path: '/shop', color: '#C6A052' },
            { icon: Trophy, label: 'Contests', path: '/match-centre', color: '#4ade80' },
          ].map(({ icon: Icon, label, path, color }) => (
            <button key={path} onClick={() => navigate(path)}
              className="card-broadcast p-4 text-center hover-lift ripple">
              <Icon className="h-6 w-6 mx-auto mb-1.5" style={{ color }} />
              <p className="text-xs font-medium text-white">{label}</p>
            </button>
          ))}
        </div>

        {/* ── Refer a Friend Nudge ── */}
        <div
          className="card-broadcast p-4 flex items-center gap-3 cursor-pointer hover-lift"
          onClick={() => navigate('/referrals')}
          data-testid="referral-nudge"
        >
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(198,160,82,0.15)', border: '1px solid rgba(198,160,82,0.3)' }}>
            <Users className="h-5 w-5" style={{ color: '#C6A052' }} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-white">Invite Friends, Earn Together</p>
            <p className="text-xs mt-0.5" style={{ color: '#8A9096' }}>You get +50 coins for every friend who joins</p>
          </div>
          <ChevronRight className="h-4 w-4 flex-shrink-0" style={{ color: '#8A9096' }} />
        </div>

        {/* Skill disclaimer */}
        <p className="text-center text-xs pb-2" style={{ color: 'rgba(255,255,255,0.2)' }}>
          FREE11 — skill-based entertainment. No real-money stakes. No deposits. Sponsored perks only.
        </p>

      </div>
      <WeeklyReportCard />
    </div>
  );
};

export default Dashboard;
