import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { toast } from 'sonner';
import {
  ArrowLeft, Users, Trophy, Lock, Plus, Copy, ChevronRight,
  Coins, Crown, Zap, Medal, Target, ChevronDown, ChevronUp,
  Loader2, RefreshCw, Share2
} from 'lucide-react';

// ── Prize Distribution Table ─────────────────────────────────────────────────
const PrizeTable = ({ distribution }) => {
  const entries = Object.entries(distribution)
    .map(([rank, coins]) => ({ rank: parseInt(rank), coins }))
    .sort((a, b) => a.rank - b.rank);
  if (entries.length === 0) return null;
  const rankLabel = (r) => {
    if (r === 1) return <span className="flex items-center gap-1" style={{ color: '#C6A052' }}><Crown className="w-3 h-3" /> 1st</span>;
    if (r === 2) return <span style={{ color: '#BFC3C8' }}>2nd</span>;
    if (r === 3) return <span style={{ color: '#CD7F32' }}>3rd</span>;
    return <span style={{ color: '#8A9096' }}>Rank {r}</span>;
  };
  return (
    <div className="mt-3 rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.06)' }} data-testid="prize-table">
      <div className="grid grid-cols-2 text-[10px] uppercase tracking-wider px-3 py-2" style={{ background: 'rgba(255,255,255,0.03)', color: '#8A9096' }}>
        <span>Rank</span><span className="text-right">Prize (Coins)</span>
      </div>
      {entries.map(({ rank, coins }) => (
        <div key={rank} className="grid grid-cols-2 px-3 py-2 text-sm border-t" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
          <span>{rankLabel(rank)}</span>
          <span className="text-right flex items-center justify-end gap-1 font-bold font-numbers" style={{ color: '#C6A052' }}>
            <Coins className="w-3 h-3" />{coins.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
};

// ── Tier configs ──────────────────────────────────────────────────────────────
const TIER_CONFIG = {
  mega:     { label: 'MEGA',       color: '#C6A052', icon: Crown,  bg: 'rgba(198,160,82,0.08)',  border: 'rgba(198,160,82,0.3)' },
  standard: { label: 'STANDARD',   color: '#60a5fa', icon: Trophy, bg: 'rgba(96,165,250,0.08)',  border: 'rgba(96,165,250,0.3)' },
  practice: { label: 'PRACTICE',   color: '#4ade80', icon: Target, bg: 'rgba(74,222,128,0.08)',  border: 'rgba(74,222,128,0.3)' },
  h2h:      { label: 'H2H',        color: '#f87171', icon: Zap,    bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.3)' },
  user:     { label: 'PRIVATE',    color: '#8A9096', icon: Lock,   bg: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.1)' },
};

// ── Contest Card ─────────────────────────────────────────────────────────────
const ContestCard = ({ contest, user, onJoin, onViewLeaderboard }) => {
  const [expanded, setExpanded] = useState(false);
  const cfg = TIER_CONFIG[contest.tier] || TIER_CONFIG.user;
  const Icon = cfg.icon;
  const fill = contest.max_participants > 0 ? Math.min(100, (contest.current_participants / contest.max_participants) * 100) : 0;
  const spotsLeft = contest.max_participants - contest.current_participants;
  const joined = contest.participants?.includes(user?.id);
  const isOpen = !contest.locked && contest.status === 'open';
  const dist = contest.prize_distribution || {};
  const topPrize = dist[1] || dist['1'] || 0;

  const handleShare = async () => {
    const code = contest.invite_code;
    const shareText = code
      ? `Join my "${contest.name}" contest on FREE11! Use code: ${code}\nDownload: https://free11.com`
      : `Join "${contest.name}" on FREE11 — predict cricket & win coins!\nhttps://free11.com`;

    if (navigator.share) {
      try {
        await navigator.share({ title: 'FREE11 Contest', text: shareText, url: 'https://free11.com' });
      } catch {}
    } else {
      await navigator.clipboard.writeText(shareText);
      toast.success('Contest link copied! Share it with friends.');
    }
  };

  return (
    <div className="card-broadcast overflow-hidden" style={{ borderColor: cfg.border }} data-testid={`contest-card-${contest.id}`}>
      {/* Header */}
      <div className="px-4 pt-3 pb-2 flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <div className="p-1.5 rounded-lg flex-shrink-0" style={{ background: cfg.bg, border: `1px solid ${cfg.border}` }}>
            <Icon className="w-3.5 h-3.5" style={{ color: cfg.color }} />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-bold text-white text-sm truncate">{contest.name}</span>
              {contest.is_platform_contest && (
                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full" style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}>
                  {cfg.label}
                </span>
              )}
              {contest.type === 'private' && <Lock className="w-3 h-3 flex-shrink-0" style={{ color: '#C6A052' }} />}
            </div>
            <p className="text-[10px] mt-0.5" style={{ color: '#8A9096' }}>{contest.description || 'Join and compete'}</p>
          </div>
        </div>
        {contest.prize_pool > 0 && (
          <div className="text-right flex-shrink-0">
            <div className="flex items-center gap-1 justify-end">
              <Coins className="w-3.5 h-3.5" style={{ color: '#C6A052' }} />
              <span className="font-numbers font-black" style={{ color: '#C6A052' }}>{contest.prize_pool.toLocaleString()}</span>
            </div>
            <p className="text-[10px]" style={{ color: '#8A9096' }}>Prize Pool</p>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="px-4 pb-2 flex items-center gap-4 text-xs" style={{ color: '#8A9096' }}>
        <span className="flex items-center gap-1"><Users className="w-3 h-3" />{contest.current_participants}/{contest.max_participants}</span>
        {contest.entry_fee === 0 && <span style={{ color: '#4ade80' }} className="font-medium">FREE Entry</span>}
        {topPrize > 0 && <span className="flex items-center gap-1" style={{ color: '#C6A052' }}><Crown className="w-3 h-3" />Win {topPrize.toLocaleString()}</span>}
        {joined && <span className="ml-auto font-medium" style={{ color: '#4ade80' }}>✓ Joined</span>}
      </div>

      {/* Fill bar */}
      <div className="px-4 pb-2">
        <div className="h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
          <div className="h-full rounded-full transition-all duration-500"
            style={{ width: `${fill}%`, background: 'linear-gradient(90deg, #C6A052, #E0B84F)' }} />
        </div>
        <div className="flex justify-between mt-1 text-[10px]" style={{ color: '#8A9096' }}>
          <span>{contest.current_participants} joined</span>
          <span style={spotsLeft <= 10 ? { color: '#f87171', fontWeight: 600 } : {}}>{spotsLeft > 0 ? `${spotsLeft} spots left` : 'FULL'}</span>
        </div>
      </div>

      {/* Actions */}
      <div className="px-4 pb-3">
        {/* Top action row: Prizes / Leaderboard / Share */}
        <div className="flex items-center gap-3 mb-2">
          {Object.keys(dist).length > 0 && (
            <button onClick={() => setExpanded(e => !e)} className="flex items-center gap-1 text-xs transition-colors hover:text-white" style={{ color: '#8A9096' }}
              data-testid={`expand-prizes-${contest.id}`}>
              {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />} Prizes
            </button>
          )}
          <button onClick={() => onViewLeaderboard(contest)} className="flex items-center gap-1 text-xs transition-colors hover:text-white" style={{ color: '#8A9096' }}
            data-testid={`view-lb-${contest.id}`}>
            <Medal className="w-3.5 h-3.5" /> Leaderboard
          </button>
          {/* Share — always visible */}
          <button onClick={handleShare}
            className="flex items-center gap-1 text-xs font-semibold transition-all hover:opacity-80 active:scale-95 ml-auto"
            style={{ color: '#4ade80' }}
            data-testid={`share-contest-${contest.id}`}>
            <Share2 className="w-3.5 h-3.5" />
            {contest.invite_code ? `Share (${contest.invite_code})` : 'Share'}
          </button>
        </div>

        {/* Bottom row: primary CTA */}
        <div className="flex items-center gap-2">
          {joined ? (
            <>
              <button onClick={handleShare}
                className="flex-1 py-2 rounded-xl text-xs font-bold flex items-center justify-center gap-1.5 transition-all active:scale-95"
                style={{ background: 'rgba(74,222,128,0.1)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.2)' }}
                data-testid={`share-joined-${contest.id}`}>
                <Share2 className="w-3.5 h-3.5" /> Invite Friends
              </button>
              <button onClick={() => onViewLeaderboard(contest)}
                className="flex-1 py-2 rounded-xl text-xs font-semibold flex items-center justify-center gap-1 transition-all"
                style={{ background: 'rgba(255,255,255,0.06)', color: '#BFC3C8', border: '1px solid rgba(255,255,255,0.08)' }}
                data-testid={`play-${contest.id}`}>
                View Standing <ChevronRight className="w-3 h-3" />
              </button>
            </>
          ) : isOpen ? (
            <button onClick={() => onJoin(contest)}
              className="btn-gold w-full py-2 rounded-xl text-xs flex items-center justify-center gap-1"
              data-testid={`join-btn-${contest.id}`}>
              <Zap className="w-3 h-3" /> {contest.entry_fee > 0 ? `Join (${contest.entry_fee}c)` : 'Join Free'}
            </button>
          ) : (
            <span className="text-xs px-3 py-1.5 rounded-xl w-full text-center"
              style={{
                background: contest.status === 'voided' ? 'rgba(248,113,113,0.08)' : 'rgba(255,255,255,0.04)',
                color: contest.status === 'voided' ? '#f87171' : '#8A9096',
                border: `1px solid ${contest.status === 'voided' ? 'rgba(248,113,113,0.2)' : 'transparent'}`,
              }}>
              {contest.locked ? 'Match Locked' : contest.status === 'voided' ? 'Contest Voided' : contest.status}
            </span>
          )}
        </div>
      </div>

      {expanded && <div className="px-4 pb-3"><PrizeTable distribution={dist} /></div>}
    </div>
  );
};

// ── Leaderboard Drawer ───────────────────────────────────────────────────────
const LeaderboardDrawer = ({ contest, user, isLiveMatch = false, onClose }) => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try { const { data } = await api.v2GetContestLeaderboard(contest.id); setEntries(data || []); } catch { setEntries([]); }
    setLoading(false);
  }, [contest.id]);

  useEffect(() => {
    load();
    if (!isLiveMatch) return;
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [load, isLiveMatch]);

  const rankIcon = (r) => {
    if (r === 1) return <Crown className="w-4 h-4" style={{ color: '#C6A052' }} />;
    if (r === 2) return <Medal className="w-4 h-4" style={{ color: '#BFC3C8' }} />;
    if (r === 3) return <Medal className="w-4 h-4" style={{ color: '#CD7F32' }} />;
    return <span className="text-xs w-4 text-center" style={{ color: '#8A9096' }}>{r}</span>;
  };

  return (
    <div className="fixed inset-0 z-50 flex flex-col" data-testid="leaderboard-drawer">
      <div className="absolute inset-0" style={{ background: 'rgba(0,0,0,0.75)' }} onClick={onClose} />
      <div className="absolute bottom-0 left-0 right-0 rounded-t-3xl max-h-[75vh] flex flex-col"
        style={{ background: '#1B1E23', borderTop: '1px solid rgba(198,160,82,0.15)' }}>
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 rounded-full" style={{ background: 'rgba(255,255,255,0.15)' }} />
        </div>
        <div className="px-4 pb-3 flex items-center justify-between border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <div>
            <h2 className="font-bold text-white">{contest.name}</h2>
            <p className="text-xs flex items-center gap-1" style={{ color: '#8A9096' }}>
              Live Standings · {entries.length} participants
              {isLiveMatch && <span className="inline-flex items-center gap-1 text-[10px]" style={{ color: '#4ade80' }}><span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-live-pulse" />Auto-updates</span>}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={load} className="p-1.5 rounded-full transition-colors hover:bg-white/8" style={{ background: 'rgba(255,255,255,0.06)' }} data-testid="refresh-lb">
              <RefreshCw className="w-3.5 h-3.5" style={{ color: '#BFC3C8' }} />
            </button>
            <button onClick={onClose} className="p-1.5 rounded-full text-sm transition-colors" style={{ background: 'rgba(255,255,255,0.06)', color: '#BFC3C8' }} data-testid="close-lb">✕</button>
          </div>
        </div>
        <div className="grid grid-cols-12 px-4 py-2 text-[10px] uppercase tracking-wider font-medium" style={{ color: '#8A9096' }}>
          <span className="col-span-1">#</span>
          <span className="col-span-5">Player</span>
          <span className="col-span-3 text-center">Points</span>
          <span className="col-span-3 text-right">Prize</span>
        </div>
        <div className="overflow-y-auto flex-1 px-4 pb-20 space-y-1.5">
          {loading ? (
            <div className="text-center py-8"><Loader2 className="w-6 h-6 mx-auto animate-spin" style={{ color: '#C6A052' }} /></div>
          ) : entries.length === 0 ? (
            <div className="text-center py-12">
              <Trophy className="w-10 h-10 mx-auto mb-2 opacity-20" style={{ color: '#C6A052' }} />
              <p className="text-sm" style={{ color: '#8A9096' }}>No entries yet — be the first!</p>
            </div>
          ) : (
            entries.map((e) => {
              const isMe = e.user_id === user?.id;
              return (
                <div key={e.user_id}
                  className="grid grid-cols-12 items-center py-2.5 px-3 rounded-xl text-sm"
                  style={{ background: isMe ? 'rgba(198,160,82,0.08)' : 'rgba(255,255,255,0.03)', border: isMe ? '1px solid rgba(198,160,82,0.25)' : '1px solid transparent' }}
                  data-testid={`lb-row-${e.user_id}`}>
                  <span className="col-span-1 flex items-center">{rankIcon(e.rank)}</span>
                  <span className="col-span-5 font-medium truncate" style={{ color: isMe ? '#C6A052' : '#fff' }}>
                    {e.user_name}{isMe && <span className="text-[10px] ml-1" style={{ color: '#8A9096' }}>(you)</span>}
                  </span>
                  <span className="col-span-3 text-center text-xs font-numbers" style={{ color: '#BFC3C8' }}>{e.points?.toFixed(1) ?? '0.0'}</span>
                  <span className="col-span-3 text-right">
                    {e.prize_coins > 0 ? (
                      <span className="flex items-center justify-end gap-1 text-xs font-bold font-numbers" style={{ color: '#C6A052' }}>
                        <Coins className="w-3 h-3" />{e.prize_coins.toLocaleString()}
                      </span>
                    ) : <span className="text-xs" style={{ color: '#2A2D33' }}>—</span>}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

// ── Main ContestHub Page ─────────────────────────────────────────────────────
export default function ContestHub() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [contests, setContests] = useState([]);
  const [match, setMatch] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showJoinCode, setShowJoinCode] = useState(false);
  const [joinCode, setJoinCode] = useState('');
  const [newContest, setNewContest] = useState({ name: '', type: 'public', max: 100 });
  const [loading, setLoading] = useState(true);
  const [selectedLbContest, setSelectedLbContest] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      await api.v2SeedContests(matchId).catch(() => {});
      const [contestRes, matchRes, liveRes] = await Promise.all([
        api.v2GetMatchContests(matchId),
        api.v2GetMatchState(matchId),
        api.v2GetLiveMatches().catch(() => ({ data: [] })),
      ]);
      setContests(contestRes.data || []);
      let matchData = matchRes.data?.match || null;
      if (!matchData || (!matchData.team1 && !matchData.team1_short)) {
        const allMatches = Array.isArray(liveRes.data) ? liveRes.data : [];
        const found = allMatches.find(m => String(m.match_id) === String(matchId));
        if (found) matchData = found;
      }
      setMatch(matchData);
    } catch {}
    setLoading(false);
  }, [matchId]);

  useEffect(() => { loadData(); }, [loadData]);

  const createContest = async () => {
    if (!newContest.name.trim()) { toast.error('Enter a contest name'); return; }
    try {
      const { data } = await api.v2CreateContest({ match_id: matchId, name: newContest.name, contest_type: newContest.type, max_participants: parseInt(newContest.max) });
      toast.success('Contest created!');
      if (data.invite_code) toast.info(`Invite code: ${data.invite_code}`);
      setShowCreate(false);
      setNewContest({ name: '', type: 'public', max: 100 });
      await loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to create'); }
  };

  const joinContest = async (contest) => {
    try { await api.v2JoinContest({ contest_id: contest.id }); toast.success(`Joined "${contest.name}"!`); await loadData(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
  };

  const joinByCode = async () => {
    if (!joinCode.trim()) return;
    try { await api.v2JoinByCode({ invite_code: joinCode.trim() }); toast.success('Joined!'); setShowJoinCode(false); setJoinCode(''); await loadData(); }
    catch (e) { toast.error(e.response?.data?.detail || 'Invalid code'); }
  };

  const filteredContests = contests.filter(c => {
    if (activeFilter === 'all') return true;
    if (activeFilter === 'platform') return c.is_platform_contest;
    if (activeFilter === 'mine') return c.participants?.includes(user?.id);
    if (activeFilter === 'user') return !c.is_platform_contest;
    return true;
  });

  const platformContests = filteredContests.filter(c => c.is_platform_contest);
  const userContests = filteredContests.filter(c => !c.is_platform_contest);
  const totalPrizePool = contests.filter(c => c.is_platform_contest).reduce((sum, c) => sum + (c.prize_pool || 0), 0);

  return (
    <div className="min-h-screen bg-[#0F1115] text-white" data-testid="contest-hub-page">
      <div className="fixed pointer-events-none" style={{ top: 0, left: '50%', transform: 'translateX(-50%)', width: '70vw', height: '30vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.04) 0%, transparent 70%)', zIndex: 0 }} />

      {/* Header */}
      <div className="relative z-20 sticky top-0 border-b px-4 py-3 flex items-center gap-3"
        style={{ background: 'rgba(15,17,21,0.95)', borderColor: 'rgba(198,160,82,0.1)', backdropFilter: 'blur(16px)' }}>
        <button onClick={() => navigate(-1)} className="p-1.5 rounded-lg hover:bg-white/5" data-testid="back-button">
          <ArrowLeft className="w-5 h-5" style={{ color: '#8A9096' }} />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="font-heading text-lg tracking-widest" style={{ color: '#C6A052' }}>CONTESTS</h1>
          {match && (
            <div className="text-xs truncate" style={{ color: '#8A9096' }}>
              {match.team1_short || match.team1} vs {match.team2_short || match.team2}
            </div>
          )}
        </div>
        <button onClick={loadData} className="p-1.5 rounded-lg hover:bg-white/5" data-testid="refresh-btn">
          <RefreshCw className="w-4 h-4" style={{ color: '#8A9096' }} />
        </button>
      </div>

      <div className="relative z-10 max-w-2xl mx-auto px-4 py-4 space-y-3">

        {/* Prize Pool Banner */}
        {totalPrizePool > 0 && (
          <div className="card-broadcast-gold p-3 flex items-center gap-3" data-testid="prize-banner">
            <div className="p-2 rounded-xl" style={{ background: 'rgba(198,160,82,0.15)' }}>
              <Trophy className="w-5 h-5" style={{ color: '#C6A052' }} />
            </div>
            <div className="flex-1">
              <p className="font-bold text-sm" style={{ color: '#C6A052' }}>Total Prize Pool</p>
              <p className="text-[10px]" style={{ color: '#8A9096' }}>Win FREE Coins — no real money</p>
            </div>
            <div className="text-right">
              <div className="flex items-center gap-1">
                <Coins className="w-4 h-4" style={{ color: '#C6A052' }} />
                <span className="font-numbers font-black text-xl" style={{ color: '#C6A052' }}>{totalPrizePool.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}

        {/* Filter tabs */}
        <div className="flex gap-2 overflow-x-auto scrollbar-hide">
          {[{ key: 'all', label: 'All' }, { key: 'platform', label: 'Official' }, { key: 'mine', label: 'Joined' }, { key: 'user', label: 'Community' }].map(f => (
            <button key={f.key} onClick={() => setActiveFilter(f.key)}
              className="px-3 py-1.5 rounded-full text-xs font-heading tracking-wider whitespace-nowrap transition-all"
              style={activeFilter === f.key
                ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115', fontWeight: 700 }
                : { background: 'rgba(255,255,255,0.04)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.06)' }}
              data-testid={`filter-${f.key}`}>
              {f.label}
            </button>
          ))}
        </div>

        {/* Sponsored Pools Banner */}
        <button
          onClick={() => navigate('/sponsored')}
          className="w-full p-3 rounded-2xl flex items-center gap-3 text-left transition-all hover:scale-[1.01] active:scale-[0.99]"
          style={{ background: 'linear-gradient(135deg, rgba(0,160,233,0.12), rgba(198,160,82,0.12))', border: '1px solid rgba(198,160,82,0.25)' }}
          data-testid="sponsored-pools-banner"
        >
          <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(198,160,82,0.15)' }}>
            <Trophy className="w-5 h-5" style={{ color: '#C6A052' }} />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-white">Sponsored Pools</p>
            <p className="text-xs" style={{ color: '#8A9096' }}>Popular brands · Snacks · Oils — brand-funded prizes, skill-only!</p>
          </div>
          <ChevronRight className="w-4 h-4" style={{ color: '#C6A052' }} />
        </button>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button onClick={() => setShowCreate(!showCreate)}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium flex items-center justify-center gap-1.5 ripple"
            style={{ background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.2)', color: '#4ade80' }}
            data-testid="create-contest-btn">
            <Plus className="w-4 h-4" /> Create
          </button>
          <button onClick={() => setShowJoinCode(!showJoinCode)}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium flex items-center justify-center gap-1.5 ripple"
            style={{ background: 'rgba(96,165,250,0.08)', border: '1px solid rgba(96,165,250,0.2)', color: '#60a5fa' }}
            data-testid="join-code-btn">
            <Copy className="w-4 h-4" /> Join by Code
          </button>
        </div>

        {/* Create form */}
        {showCreate && (
          <div className="card-broadcast p-4 space-y-2" data-testid="create-contest-form">
            <input value={newContest.name} onChange={e => setNewContest(p => ({ ...p, name: e.target.value }))}
              placeholder="Contest name" className="w-full bg-transparent rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)' }}
              data-testid="contest-name-input" />
            <div className="flex gap-2">
              {['public', 'private'].map(type => (
                <button key={type} onClick={() => setNewContest(p => ({ ...p, type }))}
                  className="flex-1 py-1.5 rounded-lg text-xs font-medium capitalize transition-all"
                  style={newContest.type === type
                    ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115', fontWeight: 700 }
                    : { background: 'rgba(255,255,255,0.04)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.06)' }}
                  data-testid={`contest-type-${type}`}>
                  {type === 'private' ? 'Private' : 'Public'}
                </button>
              ))}
            </div>
            <button onClick={createContest} className="btn-gold w-full h-10 rounded-xl text-sm" data-testid="create-submit-btn">
              Create Contest
            </button>
          </div>
        )}

        {/* Join by code */}
        {showJoinCode && (
          <div className="card-broadcast p-4 flex gap-2" data-testid="join-code-form">
            <input value={joinCode} onChange={e => setJoinCode(e.target.value.toUpperCase())}
              placeholder="Enter invite code" className="flex-1 bg-transparent rounded-lg px-3 py-2 text-sm text-white uppercase tracking-widest focus:outline-none"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)' }}
              data-testid="join-code-input" />
            <button onClick={joinByCode} className="btn-gold px-5 h-10 rounded-xl text-sm" data-testid="join-submit-btn">Join</button>
          </div>
        )}

        {/* Contest list */}
        <div className="space-y-4 pb-24" data-testid="contest-list">
          {loading ? (
            <div className="text-center py-12">
              <Loader2 className="w-8 h-8 mx-auto animate-spin mb-3" style={{ color: '#C6A052' }} />
              <p className="text-sm" style={{ color: '#8A9096' }}>Loading contests...</p>
            </div>
          ) : (
            <>
              {platformContests.length > 0 && (
                <section>
                  <h2 className="text-xs font-heading tracking-widest mb-3 flex items-center gap-2" style={{ color: '#8A9096' }}>
                    <Trophy className="w-3.5 h-3.5" style={{ color: '#C6A052' }} /> OFFICIAL CONTESTS
                  </h2>
                  <div className="space-y-3">
                    {platformContests.map(c => (
                      <ContestCard key={c.id} contest={c} user={user} onJoin={joinContest} onViewLeaderboard={setSelectedLbContest} />
                    ))}
                  </div>
                </section>
              )}
              {userContests.length > 0 && (
                <section>
                  <h2 className="text-xs font-heading tracking-widest mb-3 flex items-center gap-2" style={{ color: '#8A9096' }}>
                    <Users className="w-3.5 h-3.5" /> COMMUNITY CONTESTS
                  </h2>
                  <div className="space-y-3">
                    {userContests.map(c => (
                      <ContestCard key={c.id} contest={c} user={user} onJoin={joinContest} onViewLeaderboard={setSelectedLbContest} />
                    ))}
                  </div>
                </section>
              )}
              {filteredContests.length === 0 && (
                <div className="text-center py-14">
                  <Trophy className="w-12 h-12 mx-auto mb-3" style={{ color: '#2A2D33' }} />
                  <p className="font-medium text-white">No contests yet</p>
                  <p className="text-sm mt-1" style={{ color: '#8A9096' }}>Create one or check back soon!</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {selectedLbContest && (
        <LeaderboardDrawer contest={selectedLbContest} user={user} isLiveMatch={match?.status === 'live'} onClose={() => setSelectedLbContest(null)} />
      )}
    </div>
  );
}
