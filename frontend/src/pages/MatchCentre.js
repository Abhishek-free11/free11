import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import HowToPlay from '../components/HowToPlay';
import SharePredictionCard from '../components/SharePredictionCard';
import { Calendar, MapPin, Trophy, Timer, Users, Share2, RefreshCw, ChevronRight, Zap, Flame } from 'lucide-react';

function T20SeasonCountdown({ navigate }) {
  const [timeLeft, setTimeLeft] = React.useState({});
  React.useEffect(() => {
    const target = new Date('2026-03-26T18:00:00+05:30');
    const tick = () => {
      const diff = target - Date.now();
      if (diff <= 0) return setTimeLeft({ days: 0, hours: 0, mins: 0 });
      setTimeLeft({ days: Math.floor(diff / 86400000), hours: Math.floor((diff % 86400000) / 3600000), mins: Math.floor((diff % 3600000) / 60000) });
    };
    tick();
    const id = setInterval(tick, 30000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="py-4 animate-fadeIn">
      <div className="rounded-2xl p-4 mb-4 text-center"
        style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.08), rgba(198,160,82,0.03))', border: '1px solid rgba(198,160,82,0.2)' }}>
        <p className="text-xs font-bold tracking-widest mb-2" style={{ color: '#C6A052' }}>T20 SEASON 2026 COUNTDOWN</p>
        <div className="flex justify-center gap-4 mb-2">
          {[['Days', timeLeft.days], ['Hrs', timeLeft.hours], ['Min', timeLeft.mins]].map(([label, val]) => (
            <div key={label} className="text-center">
              <div className="text-4xl font-black text-white" style={{ fontFamily: 'Bebas Neue, sans-serif', lineHeight: 1 }}>
                {String(val ?? '--').padStart(2, '0')}
              </div>
              <div className="text-[9px] uppercase tracking-widest mt-1" style={{ color: '#8A9096' }}>{label}</div>
            </div>
          ))}
        </div>
        <p className="text-xs" style={{ color: '#8A9096' }}>Live ball-by-ball predictions begin March 26 at 6 PM IST</p>
      </div>

      {/* Card Games CTA — highlighted when no live match */}
      <div className="rounded-2xl p-4 mb-4"
        style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.12), rgba(168,85,247,0.08))', border: '1px solid rgba(198,160,82,0.3)' }}>
        <p className="text-xs font-bold tracking-widest mb-2" style={{ color: '#C6A052' }}>PLAY CARD GAMES WHILE YOU WAIT</p>
        <p className="text-sm text-white mb-3">Rummy, Teen Patti, Poker & Solitaire — earn coins right now!</p>
        <div className="grid grid-cols-4 gap-2 mb-3">
          {[
            { name: 'Rummy', symbol: '♠', color: '#ef4444', path: '/games/rummy' },
            { name: 'Teen Patti', symbol: '♥', color: '#a855f7', path: '/games/teen_patti' },
            { name: 'Poker', symbol: '♦', color: '#22c55e', path: '/games/poker' },
            { name: 'Solitaire', symbol: '⊞', color: '#f59e0b', path: '/games/solitaire' },
          ].map(g => (
            <button key={g.name} onClick={() => navigate(g.path)}
              className="flex flex-col items-center p-2 rounded-xl"
              style={{ background: `${g.color}14`, border: `1px solid ${g.color}30` }}
              data-testid={`empty-state-game-${g.name.toLowerCase().replace(' ', '-')}`}>
              <span style={{ fontSize: 22, color: g.color }}>{g.symbol}</span>
              <span style={{ fontSize: 9, color: '#BFC3C8', marginTop: 2, textAlign: 'center', lineHeight: 1.2 }}>{g.name}</span>
            </button>
          ))}
        </div>
        <button onClick={() => navigate('/games')}
          className="w-full py-2.5 rounded-xl text-sm font-bold flex items-center justify-center gap-2"
          style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)', color: '#0F1115' }}
          data-testid="empty-state-play-games-btn">
          Open Card Games
        </button>
      </div>

      <p className="text-xs font-bold tracking-widest mb-3" style={{ color: '#8A9096' }}>MORE WAYS TO EARN COINS</p>
      <div className="space-y-2">
        {[
          { icon: Zap, color: '#4ade80', bg: 'rgba(74,222,128,0.06)', border: 'rgba(74,222,128,0.15)', title: 'Daily Puzzle', sub: 'Answer today\'s cricket question · Up to 15 coins', path: '/earn' },
          { icon: Flame, color: '#C6A052', bg: 'rgba(198,160,82,0.06)', border: 'rgba(198,160,82,0.15)', title: 'Login Streak Bonus', sub: 'Check in daily · Streak bonuses up to 75 coins', path: '/earn' },
          { icon: Trophy, color: '#a855f7', bg: 'rgba(168,85,247,0.06)', border: 'rgba(168,85,247,0.15)', title: 'Leaderboard', sub: 'Top predictors earn extra bonuses at season end', path: '/leaderboards' },
        ].map(({ icon: Icon, color, bg, border, title, sub, path }) => (
          <button key={title} onClick={() => navigate(path)}
            className="w-full flex items-center gap-3 p-3.5 rounded-xl text-left"
            style={{ background: bg, border: `1px solid ${border}` }}>
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: `${color}18` }}>
              <Icon className="h-4 w-4" style={{ color }} />
            </div>
            <div className="flex-1">
              <p className="text-sm font-bold text-white">{title}</p>
              <p className="text-xs" style={{ color: '#8A9096' }}>{sub}</p>
            </div>
            <ChevronRight className="h-4 w-4" style={{ color: '#8A9096' }} />
          </button>
        ))}
      </div>
    </div>
  );
}

export default function MatchCentre() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useI18n();
  const [tab, setTab] = useState(null); // null while auto-detecting best tab
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showTutorial, setShowTutorial] = useState(false);
  const [shareContext, setShareContext] = useState(null);

  const statusMap = { upcoming: '1', live: '3', completed: '2' };

  useEffect(() => {
    detectDefaultTab();
    if (user) checkTutorial();
  }, []);

  const detectDefaultTab = async () => {
    try {
      const { data: live } = await api.v2EsGetMatches('3', 1);
      if (Array.isArray(live) && live.length > 0) { setTab('live'); return; }
      const { data: upcoming } = await api.v2EsGetMatches('1', 1);
      if (Array.isArray(upcoming) && upcoming.length > 0) { setTab('upcoming'); return; }
    } catch {}
    setTab('completed');
  };

  const checkTutorial = async () => {
    try {
      const { data } = await api.getTutorialStatus();
      if (!data.tutorial_completed) setTimeout(() => setShowTutorial(true), 1500);
    } catch {}
  };

  useEffect(() => { if (tab) loadMatches(); }, [tab]);

  const handleTutorialComplete = async () => {
    setShowTutorial(false);
    try { await api.completeTutorial(); } catch {}
  };

  const loadMatches = async () => {
    setLoading(true);
    try {
      const { data } = await api.v2EsGetMatches(statusMap[tab], 20);
      setMatches(data);
    } catch {
      toast.error(t('match_centre.failed_load'));
    }
    setLoading(false);
  };

  const TABS = [
    { key: 'live', label: t('match_centre.live') },
    { key: 'upcoming', label: t('match_centre.upcoming') },
    { key: 'completed', label: t('match_centre.completed') },
  ];

  return (
    <div className="min-h-screen bg-[#0F1115] text-white pb-28 md:pb-6" data-testid="match-centre-page">
      {/* Subtle top glow */}
      <div className="fixed pointer-events-none" style={{ top: 0, left: '50%', transform: 'translateX(-50%)', width: '70vw', height: '30vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.04) 0%, transparent 70%)', zIndex: 0 }} />

      <Navbar />
      {showTutorial && <HowToPlay onComplete={handleTutorialComplete} />}

      {/* Page header */}
      <div className="relative z-10 sticky top-14 border-b" style={{ background: 'rgba(15,17,21,0.95)', borderColor: 'rgba(198,160,82,0.1)', backdropFilter: 'blur(16px)' }}>
        <div className="max-w-screen-xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/free11_icon_192.png" alt="" className="h-6 w-6 rounded-lg" />
            <h1 className="font-heading text-xl tracking-widest" style={{ color: '#C6A052' }}>{t('match_centre.title')}</h1>
          </div>
          <button onClick={loadMatches} data-testid="refresh-btn"
            className="p-1.5 rounded-lg transition-colors hover:bg-white/5">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} style={{ color: '#8A9096' }} />
          </button>
        </div>

        {/* Tabs */}
        <div className="max-w-screen-xl mx-auto px-4 pb-3 flex gap-2">
        {TABS.map(({ key, label }) => (
            <button key={key} onClick={() => setTab(key)}
              className="flex-1 py-2 rounded-lg text-xs font-heading tracking-wider transition-all"
              style={tab === key
                ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115', fontWeight: 700 }
                : { background: 'rgba(255,255,255,0.04)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.06)' }}
              data-testid={`tab-${key}`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Match list */}
      <div className="relative z-10 max-w-screen-xl mx-auto px-3 mt-3 space-y-3 pb-24" data-testid="match-list">
        {loading ? (
          <div className="text-center py-16">
            <div className="h-6 w-6 rounded-full border-2 animate-spin mx-auto" style={{ borderColor: '#C6A052', borderTopColor: 'transparent' }} />
            <p className="text-sm mt-3" style={{ color: '#8A9096' }}>{t('match_centre.loading')}</p>
          </div>
        ) : matches.length === 0 ? (
          <T20SeasonCountdown navigate={navigate} />
        ) : (
          matches.map(m => (
            <div key={m.match_id} className="card-broadcast overflow-hidden hover-lift" data-testid={`match-${m.match_id}`}>
              {/* Series + status row */}
              <div className="px-4 py-2 flex items-center justify-between border-b" style={{ borderColor: 'rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
                <span className="text-[10px] truncate" style={{ color: '#8A9096' }}>{m.series}</span>
                {m.status === 'live'
                  ? <span className="badge-live flex items-center gap-1"><span className="w-1 h-1 rounded-full bg-red-400 animate-live-pulse" /> LIVE</span>
                  : <span className="text-[10px] px-2 py-0.5 rounded-full font-medium capitalize"
                      style={{ background: m.status === 'upcoming' ? 'rgba(96,165,250,0.12)' : 'rgba(255,255,255,0.05)', color: m.status === 'upcoming' ? '#60a5fa' : '#8A9096' }}>
                      {m.status}
                    </span>
                }
              </div>

              {/* Teams */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 flex-1">
                    {m.team1_logo && <img src={m.team1_logo} alt="" className="w-8 h-8 rounded-full bg-white/5" onError={e => e.target.style.display='none'} />}
                    <div>
                      <div className="text-sm font-bold text-white">{m.team1_short || m.team1}</div>
                      {m.team1_score && <div className="text-xs font-numbers font-bold" style={{ color: '#C6A052' }}>{m.team1_score}</div>}
                    </div>
                  </div>
                  <div className="text-xs font-bold px-3" style={{ color: '#8A9096' }}>vs</div>
                  <div className="flex items-center gap-2 flex-1 justify-end text-right">
                    <div>
                      <div className="text-sm font-bold text-white">{m.team2_short || m.team2}</div>
                      {m.team2_score && <div className="text-xs font-numbers font-bold" style={{ color: '#BFC3C8' }}>{m.team2_score}</div>}
                    </div>
                    {m.team2_logo && <img src={m.team2_logo} alt="" className="w-8 h-8 rounded-full bg-white/5" onError={e => e.target.style.display='none'} />}
                  </div>
                </div>

                {m.status_note && <div className="text-[10px] text-center mb-2" style={{ color: '#8A9096' }}>{m.status_note}</div>}

                {/* Meta */}
                <div className="flex items-center gap-3 text-[10px] mb-3" style={{ color: '#8A9096' }}>
                  <span className="flex items-center gap-1"><Calendar className="w-3 h-3" /> {new Date(m.match_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}</span>
                  {m.venue && <span className="flex items-center gap-1 truncate max-w-[150px]"><MapPin className="w-3 h-3" /> {m.venue}</span>}
                </div>

                {/* Action buttons */}
                <div className="flex gap-2 flex-wrap">
                  {m.status === 'live' && (
                    <button onClick={() => navigate(`/match/${m.match_id}`)}
                      className="flex-1 min-w-[80px] px-3 py-2 rounded-lg text-xs font-heading tracking-wider flex items-center justify-center gap-1.5 ripple"
                      style={{ background: 'rgba(239,68,68,0.15)', color: '#f87171', border: '1px solid rgba(239,68,68,0.3)' }}
                      data-testid={`predict-${m.match_id}`}>
                      <Timer className="w-3 h-3" /> {t('match_centre.predict_btn')}
                    </button>
                  )}
                  {(m.status === 'upcoming' || m.status === 'live') && (
                    <button onClick={() => navigate(`/team-builder/${m.match_id}`)}
                      className="flex-1 min-w-[80px] px-3 py-2 rounded-lg text-xs font-heading tracking-wider flex items-center justify-center gap-1.5 ripple"
                      style={{ background: 'rgba(198,160,82,0.1)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.25)' }}
                      data-testid={`build-team-${m.match_id}`}>
                      <Users className="w-3 h-3" /> {t('match_centre.build_team_btn')}
                    </button>
                  )}
                  <button onClick={() => navigate(`/contest-hub/${m.match_id}`)}
                    className="flex-1 min-w-[80px] px-3 py-2 rounded-lg text-xs font-heading tracking-wider flex items-center justify-center gap-1.5 ripple"
                    style={{ background: 'rgba(255,255,255,0.04)', color: '#BFC3C8', border: '1px solid rgba(255,255,255,0.08)' }}
                    data-testid={`contests-${m.match_id}`}>
                    <Trophy className="w-3 h-3" /> {t('match_centre.contests_btn')}
                  </button>
                  <button
                    onClick={() => setShareContext({ match: m, prediction: { prediction_type: 'match_winner', prediction_value: m.team1_short || m.team1 } })}
                    className="px-3 py-2 rounded-lg text-xs flex items-center justify-center gap-1 ripple"
                    style={{ background: 'rgba(96,165,250,0.08)', color: '#60a5fa', border: '1px solid rgba(96,165,250,0.2)' }}
                    data-testid={`share-${m.match_id}`}>
                    <Share2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {shareContext && (
        <SharePredictionCard
          match={shareContext.match}
          prediction={shareContext.prediction}
          user={user}
          onClose={() => setShareContext(null)}
        />
      )}
    </div>
  );
}
