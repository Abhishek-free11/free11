import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import { Target, Zap, Trophy, Timer, TrendingUp, ChevronRight, RefreshCw, Shield, Flame } from 'lucide-react';
import { SkillBadge } from '../components/SkillDisclaimerModal';

export default function Predict() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useI18n();
  const [liveMatches, setLiveMatches] = useState([]);
  const [upcomingMatches, setUpcomingMatches] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeCards, setActiveCards] = useState([]);
  const [streakData, setStreakData] = useState({ streak: 0, multiplier: 1, hot_hand: false });

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [liveRes, upRes, statsRes, cardsRes, streakRes] = await Promise.all([
        api.v2EsGetMatches('3', 10).catch(() => ({ data: [] })),
        api.v2EsGetMatches('1', 5).catch(() => ({ data: [] })),
        api.v2GetPredictionStats().catch(() => ({ data: {} })),
        api.v2GetCardInventory().catch(() => ({ data: [] })),
        api.v2GetPredictionStreak().catch(() => ({ data: { streak: 0, multiplier: 1, hot_hand: false } })),
      ]);
      setLiveMatches(Array.isArray(liveRes.data) ? liveRes.data : []);
      setUpcomingMatches(Array.isArray(upRes.data) ? upRes.data : []);
      setStats(statsRes.data || {});
      setActiveCards(Array.isArray(cardsRes.data) ? cardsRes.data : []);
      setStreakData(streakRes.data || { streak: 0, multiplier: 1, hot_hand: false });
    } catch {}
    setLoading(false);
  };

  const predictionTypes = [
    { id: 'over_runs', label: t('predict_page.types.over_runs'), desc: 'Predict runs in next over', reward: '15', icon: TrendingUp, color: '#4ade80' },
    { id: 'over_wicket', label: t('predict_page.types.over_wicket'), desc: 'Will a wicket fall?', reward: '10', icon: Target, color: '#f87171' },
    { id: 'over_boundary', label: t('predict_page.types.over_boundary'), desc: 'Boundary in next over?', reward: '10', icon: Zap, color: '#C6A052' },
    { id: 'milestone', label: t('predict_page.types.milestone'), desc: 'Predict milestones', reward: '20', icon: Trophy, color: '#a78bfa' },
  ];

  return (
    <div className="min-h-screen bg-[#0F1115] text-white pb-28 md:pb-6" data-testid="predict-page">
      <div className="fixed pointer-events-none" style={{ top: 0, left: '50%', transform: 'translateX(-50%)', width: '70vw', height: '30vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.04) 0%, transparent 70%)', zIndex: 0 }} />
      <Navbar />

      <div className="relative z-10 max-w-2xl mx-auto px-3 py-4 space-y-4 animate-slide-up">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="font-heading text-2xl tracking-widest" style={{ color: '#C6A052' }}>
              {t('predict_page.title')}
            </h1>
            <SkillBadge />
          </div>
          <button onClick={loadData} className="p-2 rounded-lg hover:bg-white/5" data-testid="refresh-btn">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} style={{ color: '#8A9096' }} />
          </button>
        </div>

        {/* Stats Bar */}
        {stats && (
          <div className="grid grid-cols-4 gap-2" data-testid="prediction-stats">
            {[
              { label: t('predict_page.total'), value: stats.total || 0, color: '#fff' },
              { label: t('predict_page.correct'), value: stats.correct || 0, color: '#4ade80' },
              { label: t('predict_page.accuracy'), value: `${stats.accuracy || 0}%`, color: '#C6A052' },
              { label: t('predict_page.streak'), value: streakData.streak, color: streakData.hot_hand ? '#fb923c' : '#a78bfa', suffix: streakData.hot_hand ? ' 🔥' : '' },
            ].map(({ label, value, color, suffix }) => (
              <div key={label} className="card-broadcast p-3 text-center">
                <div className="text-lg font-numbers font-bold" style={{ color }}>{value}{suffix}</div>
                <div className="text-[10px]" style={{ color: '#8A9096' }}>{label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Hot Hand Banner */}
        {streakData.hot_hand && (
          <div className="p-3 rounded-xl flex items-center gap-3 border"
            style={{ background: 'linear-gradient(135deg, rgba(251,146,60,0.12), rgba(234,88,12,0.08))', borderColor: 'rgba(251,146,60,0.35)' }}
            data-testid="hot-hand-banner">
            <Flame className="h-5 w-5 text-orange-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-bold text-orange-300">Hot Hand — {streakData.streak} in a row!</p>
              <p className="text-[10px] text-orange-400/70">Next correct earns <span className="font-bold">{streakData.multiplier}x coins</span></p>
            </div>
            <div className="text-2xl font-numbers font-black text-orange-400">{streakData.multiplier}x</div>
          </div>
        )}

        {/* Power-Up Cards */}
        {activeCards.length > 0 && (
          <div className="card-broadcast p-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4" style={{ color: '#C6A052' }} />
              <span className="text-xs font-medium" style={{ color: '#C6A052' }}>{activeCards.length} Power-Up Cards Available</span>
            </div>
            <button onClick={() => navigate('/cards')} className="text-xs" style={{ color: '#8A9096' }}>Manage →</button>
          </div>
        )}

        {/* Prediction Types */}
        <div>
          <h3 className="text-xs uppercase tracking-widest font-heading mb-2" style={{ color: '#8A9096' }}>Prediction Types</h3>
          <div className="grid grid-cols-2 gap-2">
            {predictionTypes.map(pt => (
              <div key={pt.id} className="card-broadcast p-3" data-testid={`pred-type-${pt.id}`}>
                <pt.icon className="w-5 h-5 mb-2" style={{ color: pt.color }} />
                <div className="text-sm font-bold text-white">{pt.label}</div>
                <div className="text-[10px] mb-2" style={{ color: '#8A9096' }}>{pt.desc}</div>
                <div className="coin-indicator inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold">
                  +{pt.reward} coins
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live Matches */}
        <div>
          <h3 className="text-xs uppercase tracking-widest font-heading mb-2" style={{ color: '#8A9096' }}>
            {liveMatches.length > 0 ? t('predict_page.live_now') : t('predict_page.no_live')}
          </h3>
          {liveMatches.length > 0 ? (
            <div className="space-y-2">
              {liveMatches.map(m => (
                <button key={m.match_id} onClick={() => navigate(`/match/${m.match_id}`)}
                  className="w-full flex items-center justify-between p-3 rounded-xl transition-all border ripple"
                  style={{ background: 'rgba(239,68,68,0.08)', borderColor: 'rgba(239,68,68,0.2)' }}
                  data-testid={`live-${m.match_id}`}>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-live-pulse" />
                      <span className="text-[10px] text-red-400 font-bold">LIVE</span>
                    </div>
                    <div className="text-left">
                      <div className="text-sm font-bold text-white">{m.short_title || m.title}</div>
                      <div className="text-[10px]" style={{ color: '#8A9096' }}>{m.series}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-red-400 font-medium">{t('match_centre.predict_btn')}</span>
                    <ChevronRight className="w-4 h-4 text-red-400" />
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="card-broadcast p-6 text-center">
              <Timer className="w-8 h-8 mx-auto mb-2" style={{ color: '#2A2D33' }} />
              <div className="text-sm" style={{ color: '#8A9096' }}>No live matches right now</div>
              <div className="text-xs mt-1" style={{ color: '#2A2D33' }}>Predictions open when matches go live</div>
            </div>
          )}
        </div>

        {/* Upcoming Matches */}
        {upcomingMatches.length > 0 && (
          <div>
            <h3 className="text-xs uppercase tracking-widest font-heading mb-2" style={{ color: '#8A9096' }}>{t('predict_page.coming_up')}</h3>
            <div className="space-y-2">
              {upcomingMatches.slice(0, 3).map(m => (
                <div key={m.match_id} className="card-broadcast flex items-center justify-between p-3">
                  <div>
                    <div className="text-sm font-bold text-white">{m.short_title}</div>
                    <div className="text-[10px]" style={{ color: '#8A9096' }}>
                      {new Date(m.match_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full"
                    style={{ background: 'rgba(96,165,250,0.12)', color: '#60a5fa' }}>Upcoming</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
