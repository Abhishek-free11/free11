import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import CrowdMeter from '../components/CrowdMeter';
import { ArrowLeft, Timer, Trophy, Zap, Shield, Users, RefreshCw, Eye, EyeOff } from 'lucide-react';
import { SkillBadge } from '../components/SkillDisclaimerModal';

const POLL_INTERVAL = 5000;

export default function LiveMatch() {
  const { matchId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [match, setMatch] = useState(null);
  const [esMatch, setEsMatch] = useState(null);
  const [predictionTypes, setPredictionTypes] = useState({});
  const [myPredictions, setMyPredictions] = useState([]);
  const [myTeams, setMyTeams] = useState([]);
  const [cards, setCards] = useState([]);
  const [selectedType, setSelectedType] = useState(null);
  const [selectedValue, setSelectedValue] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [stats, setStats] = useState({ total: 0, correct: 0, accuracy: 0, total_coins: 0 });
  const [showTeam, setShowTeam] = useState(null);
  const pollRef = useRef(null);
  const [frozen, setFrozen] = useState(false);

  const loadMatch = useCallback(async () => {
    try {
      const { data } = await api.v2GetMatchState(matchId);
      setMatch(data.match);
      setFrozen(data.frozen);
    } catch {}
    try {
      const { data } = await api.v2EsGetMatchInfo(matchId);
      setEsMatch(data);
    } catch {}
  }, [matchId]);

  const loadMyTeams = useCallback(async () => {
    try {
      const { data } = await api.v2GetMyFantasyTeams(matchId);
      setMyTeams(data || []);
    } catch {}
  }, [matchId]);

  useEffect(() => {
    const init = async () => {
      await loadMatch();
      await loadMyTeams();
      try { const { data } = await api.v2GetMyPredictions(matchId); setMyPredictions(data); } catch {}
      try { const { data } = await api.v2GetPredictionTypes(); setPredictionTypes(data); } catch {}
      try { const { data } = await api.v2GetCardInventory(); setCards(data); } catch {}
      try { const { data } = await api.v2GetPredictionStats(); setStats(data); } catch {}
    };
    init();
    pollRef.current = setInterval(() => { loadMatch(); }, POLL_INTERVAL);
    return () => clearInterval(pollRef.current);
  }, [matchId, loadMatch, loadMyTeams]);

  useEffect(() => {
    if (match?.status === 'completed' || match?.status === 'abandoned') clearInterval(pollRef.current);
  }, [match?.status]);

  const submitPrediction = async () => {
    if (!selectedType || !selectedValue) return;
    setSubmitting(true);
    try {
      const overNum = selectedType.startsWith('over_') ? getCurrentOver() : null;
      await api.v2SubmitPrediction({ match_id: matchId, prediction_type: selectedType, prediction_value: selectedValue, over_number: overNum });
      toast.success('Prediction submitted!');
      setSelectedType(null);
      setSelectedValue(null);
      const { data } = await api.v2GetMyPredictions(matchId);
      setMyPredictions(data);
      const { data: s } = await api.v2GetPredictionStats();
      setStats(s);
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to submit'); }
    setSubmitting(false);
  };

  const getCurrentOver = () => {
    if (!match?.current_ball) return 0;
    return parseInt(match.current_ball.split('.')[0]) + 1;
  };

  const m = esMatch || match || {};
  const team1 = m.team1_short || m.team1 || 'TBA';
  const team2 = m.team2_short || m.team2 || 'TBA';
  const score1 = m.team1_score || match?.team1_score || '-';
  const score2 = m.team2_score || match?.team2_score || '-';
  const series = m.series || m.match_type || '';
  const statusNote = m.status_note || '';
  const currentBall = match?.current_ball || m.current_ball || '0.0';
  const isLive = match?.status === 'live' || m.status === 'live';
  const isEnded = match?.status === 'completed' || m.status === 'completed';

  if (!match && !esMatch) {
    return (
      <div className="min-h-screen bg-[#0F1115] flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 animate-spin" style={{ borderColor: '#C6A052', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F1115] text-white pb-28 md:pb-6" data-testid="live-match-page">
      {/* Broadcast glow */}
      <div className="fixed pointer-events-none" style={{ top: 0, left: '50%', transform: 'translateX(-50%)', width: '80vw', height: '35vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.04) 0%, transparent 70%)', zIndex: 0 }} />

      <Navbar />

      {/* ── Match Header Bar ── */}
      <div className="relative z-10 sticky top-14 border-b px-4 py-3 flex items-center gap-3"
        style={{ background: 'rgba(15,17,21,0.95)', borderColor: 'rgba(198,160,82,0.1)', backdropFilter: 'blur(16px)' }}>
        <button onClick={() => navigate(-1)} className="p-1 rounded-lg hover:bg-white/5" data-testid="back-button">
          <ArrowLeft className="w-5 h-5" style={{ color: '#8A9096' }} />
        </button>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-bold text-white">{team1} vs {team2}</div>
          <div className="text-xs" style={{ color: '#8A9096' }}>{series}</div>
        </div>
        <div className="flex items-center gap-2">
          {isLive && <span className="badge-live flex items-center gap-1"><span className="w-1.5 h-1.5 bg-red-400 rounded-full animate-live-pulse" /> LIVE</span>}
          {frozen && <span className="text-[10px] px-2 py-0.5 rounded-full font-bold" style={{ background: 'rgba(234,179,8,0.15)', color: '#eab308', border: '1px solid rgba(234,179,8,0.3)' }}>FROZEN</span>}
          <SkillBadge />
        </div>
      </div>

      <div className="relative z-10 max-w-2xl mx-auto px-3 py-3 space-y-3">

        {/* ── Scoreboard ── */}
        <div className="card-broadcast-gold p-4" data-testid="scoreboard">
          <div className="flex items-center justify-between">
            <div className="text-center flex-1">
              {m.team1_logo && <img src={m.team1_logo} alt="" className="w-10 h-10 rounded-full mx-auto mb-1.5 bg-white/5" onError={e => e.target.style.display='none'} />}
              <div className="text-lg font-bold text-white">{team1}</div>
              <div className="text-3xl font-black font-numbers" style={{ color: '#C6A052' }}>{score1}</div>
            </div>
            <div className="text-center px-3">
              <div className="text-[10px] uppercase tracking-widest mb-1" style={{ color: '#8A9096' }}>Over</div>
              <div className="text-2xl font-black font-numbers text-white">{currentBall}</div>
            </div>
            <div className="text-center flex-1">
              {m.team2_logo && <img src={m.team2_logo} alt="" className="w-10 h-10 rounded-full mx-auto mb-1.5 bg-white/5" onError={e => e.target.style.display='none'} />}
              <div className="text-lg font-bold text-white">{team2}</div>
              <div className="text-3xl font-black font-numbers" style={{ color: '#BFC3C8' }}>{score2}</div>
            </div>
          </div>
          {statusNote && <div className="text-xs text-center mt-3 py-1.5 rounded-lg" style={{ background: 'rgba(255,255,255,0.04)', color: '#BFC3C8' }}>{statusNote}</div>}
        </div>

        {/* ── Stats Bar ── */}
        <div className="grid grid-cols-3 gap-2" data-testid="stats-bar">
          {[
            { icon: Trophy, label: 'Accuracy', value: `${stats.accuracy || 0}%`, color: '#C6A052' },
            { icon: Zap, label: 'Coins', value: stats.total_coins || 0, color: '#4ade80' },
            { icon: Shield, label: 'Cards', value: cards.length, color: '#60a5fa' },
          ].map(({ icon: Icon, label, value, color }) => (
            <div key={label} className="card-broadcast p-3 text-center">
              <Icon className="w-4 h-4 mx-auto mb-1" style={{ color }} />
              <div className="font-numbers text-sm font-bold" style={{ color }}>{value}</div>
              <div className="text-[10px]" style={{ color: '#8A9096' }}>{label}</div>
            </div>
          ))}
        </div>

        {/* ── No team CTA ── */}
        {myTeams.length === 0 && !isEnded && (
          <div className="card-broadcast p-3 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-white">Build Your Fantasy Team</div>
              <div className="text-xs" style={{ color: '#8A9096' }}>Pick 11 players and compete</div>
            </div>
            <button onClick={() => navigate(`/team-builder/${matchId}`)} className="btn-gold px-4 h-9 rounded-lg text-xs">
              Build Team
            </button>
          </div>
        )}

        {/* ── My Fantasy Teams ── */}
        {myTeams.length > 0 && (
          <div data-testid="my-teams-section">
            <h3 className="text-sm font-medium mb-2 flex items-center gap-2" style={{ color: '#BFC3C8' }}>
              <Users className="w-4 h-4" style={{ color: '#C6A052' }} /> My Fantasy Teams ({myTeams.length})
            </h3>
            {myTeams.map((team, idx) => (
              <div key={team.id || idx} className="card-broadcast p-3 mb-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">Team {idx + 1}</span>
                  <div className="flex items-center gap-2">
                    {team.total_points > 0 && <span className="text-xs font-bold" style={{ color: '#4ade80' }}>{team.total_points} pts</span>}
                    <span className="text-xs" style={{ color: '#8A9096' }}>{team.total_credits}/100 cr</span>
                    <button onClick={() => setShowTeam(showTeam === idx ? null : idx)} style={{ color: '#8A9096' }}>
                      {showTeam === idx ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                {showTeam === idx && (
                  <div className="space-y-1 mt-2">
                    {team.players?.map(p => (
                      <div key={p.player_id} className="flex items-center justify-between py-1 px-2 rounded-lg text-xs"
                        style={{ background: 'rgba(255,255,255,0.03)' }}>
                        <div className="flex items-center gap-2">
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                            p.role === 'wk' ? 'bg-yellow-500/20 text-yellow-400' :
                            p.role === 'bat' ? 'bg-blue-500/20 text-blue-400' :
                            p.role === 'all' ? 'bg-green-500/20 text-green-400' : 'bg-purple-500/20 text-purple-400'
                          }`}>{p.role?.toUpperCase()}</span>
                          <span className="text-white">{p.name || p.short_name}</span>
                          {p.is_captain && <span className="px-1 rounded text-[9px] font-bold bg-yellow-500/20 text-yellow-400">C</span>}
                          {p.is_vc && <span className="px-1 rounded text-[9px] font-bold bg-blue-500/20 text-blue-400">VC</span>}
                        </div>
                        <span style={{ color: '#8A9096' }}>{p.credit}cr</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ── Prediction Panel ── */}
        {isLive && !frozen && (
          <div className="card-broadcast-gold p-4" data-testid="prediction-panel">
            <h3 className="text-sm font-heading tracking-wider mb-3 flex items-center gap-2" style={{ color: '#C6A052' }}>
              <Timer className="w-4 h-4" /> MAKE YOUR PREDICTION
            </h3>

            {/* Type selector */}
            <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {Object.entries(predictionTypes).map(([key, val]) => (
                <button key={key} onClick={() => { setSelectedType(key); setSelectedValue(null); }}
                  className="shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all"
                  style={selectedType === key
                    ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115', fontWeight: 700 }
                    : { background: 'rgba(255,255,255,0.05)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.08)' }}
                  data-testid={`pred-type-${key}`}>
                  {val.label} <span style={{ opacity: 0.7 }}>({val.reward}c)</span>
                </button>
              ))}
            </div>

            {/* Options grid */}
            {selectedType && predictionTypes[selectedType] && (
              <div className="grid grid-cols-2 gap-2 mt-3">
                {predictionTypes[selectedType].options.map((opt) => (
                  <button key={opt} onClick={() => setSelectedValue(opt)}
                    className="p-3 rounded-xl text-sm font-medium transition-all"
                    style={selectedValue === opt
                      ? { background: 'rgba(198,160,82,0.15)', border: '1px solid #C6A052', color: '#E0B84F' }
                      : { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)', color: '#BFC3C8' }}
                    data-testid={`pred-option-${opt}`}>{opt}</button>
                ))}
              </div>
            )}

            {selectedType && selectedValue && (
              <button onClick={submitPrediction} disabled={submitting}
                className="btn-gold w-full mt-3 py-3 rounded-xl text-sm ripple disabled:opacity-50"
                data-testid="submit-prediction-btn">
                {submitting ? 'Submitting...' : `Predict: ${selectedValue}`}
              </button>
            )}
          </div>
        )}

        {/* ── Match Ended ── */}
        {isEnded && (
          <div className="card-broadcast p-5 text-center" data-testid="match-ended">
            <Trophy className="w-10 h-10 mx-auto mb-2" style={{ color: '#C6A052' }} />
            <div className="text-lg font-heading tracking-wider text-white">MATCH ENDED</div>
            <div className="text-sm mt-1" style={{ color: '#8A9096' }}>{statusNote || 'Check your results below'}</div>
          </div>
        )}

        {/* ── Crowd Meter ── */}
        <CrowdMeter matchId={matchId} isLive={match?.status === 'live' || match?.match_status === '3'} />

        {/* ── My Predictions ── */}
        <div data-testid="my-predictions">
          <h3 className="text-sm font-medium mb-2" style={{ color: '#BFC3C8' }}>My Predictions ({myPredictions.length})</h3>
          {myPredictions.length === 0 ? (
            <div className="card-broadcast p-4 text-center text-sm" style={{ color: '#8A9096' }}>
              {isLive ? 'Make your first prediction above!' : 'No predictions for this match.'}
            </div>
          ) : (
            <div className="space-y-2">
              {myPredictions.map((p) => (
                <div key={p.id} className="card-broadcast p-3 flex items-center justify-between" data-testid={`prediction-${p.id}`}>
                  <div>
                    <div className="text-xs" style={{ color: '#8A9096' }}>{predictionTypes[p.prediction_type]?.label || p.prediction_type}</div>
                    <div className="text-sm font-semibold text-white">{p.prediction_value}</div>
                    {p.over_number && <div className="text-xs" style={{ color: '#8A9096' }}>Over {p.over_number}</div>}
                  </div>
                  <div className="text-right">
                    {p.status === 'pending' && <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(234,179,8,0.15)', color: '#eab308' }}>Pending</span>}
                    {p.status === 'resolved' && p.is_correct && (
                      <div>
                        <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(74,222,128,0.15)', color: '#4ade80' }}>Correct!</span>
                        <div className="text-xs mt-1" style={{ color: '#4ade80' }}>+{p.coins_earned}c</div>
                      </div>
                    )}
                    {p.status === 'resolved' && !p.is_correct && <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: 'rgba(248,113,113,0.15)', color: '#f87171' }}>Wrong</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
