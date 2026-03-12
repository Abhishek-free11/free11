import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { toast } from 'sonner';
import { ArrowLeft, Star, Shield, Zap, Check, X, Users, Info, ChevronDown } from 'lucide-react';

const ROLE_LABELS = { wk: 'WK', bat: 'BAT', all: 'AR', bowl: 'BOWL' };
const ROLE_COLORS = { wk: 'text-yellow-400', bat: 'text-blue-400', all: 'text-emerald-400', bowl: 'text-purple-400' };
const ROLE_BG = { wk: 'bg-yellow-500/20', bat: 'bg-blue-500/20', all: 'bg-emerald-500/20', bowl: 'bg-purple-500/20' };

export default function TeamBuilder() {
  const { matchId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [squads, setSquads] = useState(null);
  const [matchInfo, setMatchInfo] = useState(null);
  const [selected, setSelected] = useState([]);
  const [captain, setCaptain] = useState(null);
  const [vc, setVc] = useState(null);
  const [step, setStep] = useState('select'); // select -> captain -> preview
  const [filter, setFilter] = useState(null); // null = show all
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadData();
  }, [matchId]);

  const loadData = async () => {
    try {
      const [sqRes, matchRes] = await Promise.all([
        api.v2EsGetSquads(matchId),
        api.v2EsGetMatchInfo(matchId),
      ]);
      setSquads(sqRes.data);
      setMatchInfo(matchRes.data);
    } catch (e) {
      toast.error('Failed to load squad data');
    }
  };

  const allPlayers = useMemo(() => {
    if (!squads) return [];
    const all = [...(squads.team_a?.squad || []), ...(squads.team_b?.squad || [])];
    // Filter to confirmed playing XI only
    const playing = all.filter(p => p.playing11 === true);
    // If playing 11 not announced yet, fall back to full squad
    return playing.length >= 11 ? playing : all;
  }, [squads]);

  // True when the playing 11 is confirmed
  const playing11Confirmed = useMemo(() => {
    if (!squads) return false;
    const all = [...(squads.team_a?.squad || []), ...(squads.team_b?.squad || [])];
    return all.filter(p => p.playing11 === true).length >= 11;
  }, [squads]);

  const filtered = useMemo(() => {
    if (!filter) return allPlayers;
    return allPlayers.filter(p => p.role === filter);
  }, [allPlayers, filter]);

  const teamA = squads?.team_a?.name || 'Team A';
  const teamB = squads?.team_b?.name || 'Team B';

  const totalCredits = selected.reduce((s, p) => s + p.credit, 0);
  const remaining = Math.round((100 - totalCredits) * 10) / 10;

  const teamCounts = useMemo(() => {
    const c = {};
    selected.forEach(p => { c[p.team] = (c[p.team] || 0) + 1; });
    return c;
  }, [selected]);

  const roleCounts = useMemo(() => {
    const c = { wk: 0, bat: 0, all: 0, bowl: 0 };
    selected.forEach(p => { c[p.role] = (c[p.role] || 0) + 1; });
    return c;
  }, [selected]);

  const canSelect = (p) => {
    if (selected.find(s => s.player_id === p.player_id)) return false;
    if (selected.length >= 11) return false;
    if (totalCredits + p.credit > 100) return false;
    if ((teamCounts[p.team] || 0) >= 7) return false;
    return true;
  };

  const togglePlayer = (p) => {
    const exists = selected.find(s => s.player_id === p.player_id);
    if (exists) {
      setSelected(selected.filter(s => s.player_id !== p.player_id));
      if (captain === p.player_id) setCaptain(null);
      if (vc === p.player_id) setVc(null);
    } else if (canSelect(p)) {
      setSelected([...selected, p]);
    }
  };

  const validateTeam = () => {
    if (selected.length !== 11) return 'Select exactly 11 players';
    if (roleCounts.wk < 1) return 'Need at least 1 WK';
    if (roleCounts.bat < 3) return 'Need at least 3 BAT';
    if (roleCounts.all < 1) return 'Need at least 1 AR';
    if (roleCounts.bowl < 3) return 'Need at least 3 BOWL';
    return null;
  };

  const proceedToCaptain = () => {
    const err = validateTeam();
    if (err) { toast.error(err); return; }
    setStep('captain');
  };

  const proceedToPreview = () => {
    if (!captain || !vc) { toast.error('Select Captain and Vice-Captain'); return; }
    if (captain === vc) { toast.error('C and VC must be different'); return; }
    setStep('preview');
  };

  const createTeam = async () => {
    setCreating(true);
    try {
      await api.v2CreateFantasyTeam({
        match_id: matchId,
        players: selected,
        captain_id: captain,
        vc_id: vc,
      });
      toast.success('Fantasy team created!');
      navigate(`/contest-hub/${matchId}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create team');
    }
    setCreating(false);
  };

  if (!squads) {
    return <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
      <div className="animate-spin h-6 w-6 border-2 border-emerald-400 border-t-transparent rounded-full" />
    </div>;
  }

  // ── Step 1: Player Selection ──
  if (step === 'select') return (
    <div className="min-h-screen bg-[#0a0e17] text-white pb-24" data-testid="team-builder-select">
      {/* Header */}
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3">
        <div className="flex items-center gap-3 mb-2">
          <button onClick={() => navigate(-1)} data-testid="back-button"><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
          <div className="flex-1">
            <div className="text-sm font-bold">{matchInfo?.short_title || 'Create Team'}</div>
            <div className="text-xs text-gray-500">{matchInfo?.series}</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400">Credits Left</div>
            <div className={`text-lg font-black ${remaining < 10 ? 'text-red-400' : 'text-emerald-400'}`}>{remaining}</div>
          </div>
        </div>
        {/* Team count bar */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-gray-500">{teamA}:</span>
          <span className="font-bold">{teamCounts[teamA] || 0}</span>
          <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 transition-all" style={{ width: `${(selected.length / 11) * 100}%` }} />
          </div>
          <span className="font-bold">{teamCounts[teamB] || 0}</span>
          <span className="text-gray-500">:{teamB}</span>
        </div>
      </div>

      {/* Role counts */}
      <div className="flex justify-around px-4 py-2 bg-white/5 border-b border-white/5">
        {Object.entries(ROLE_LABELS).map(([role, label]) => (
          <div key={role} className="text-center">
            <div className={`text-xs ${ROLE_COLORS[role]}`}>{label}</div>
            <div className="text-sm font-bold">{roleCounts[role]}</div>
          </div>
        ))}
        <div className="text-center">
          <div className="text-xs text-white">Total</div>
          <div className={`text-sm font-bold ${selected.length === 11 ? 'text-emerald-400' : ''}`}>{selected.length}/11</div>
        </div>
      </div>

      {/* Playing 11 status banner */}
      {!playing11Confirmed && (
        <div className="mx-3 mt-2 px-3 py-2 rounded-lg text-xs flex items-center gap-2"
          style={{ background: 'rgba(251,191,36,0.08)', border: '1px solid rgba(251,191,36,0.2)', color: '#fbbf24' }}>
          <span>⚠</span>
          <span>Playing XI not announced yet — showing full squad. Update your team once lineups are confirmed.</span>
        </div>
      )}
      {playing11Confirmed && (
        <div className="mx-3 mt-2 px-3 py-2 rounded-lg text-xs flex items-center gap-2"
          style={{ background: 'rgba(74,222,128,0.06)', border: '1px solid rgba(74,222,128,0.15)', color: '#4ade80' }}>
          <span>✓</span>
          <span>Showing confirmed Playing XI only</span>
        </div>
      )}

      {/* Role filter tabs */}
      <div className="flex gap-1 px-3 py-2 overflow-x-auto no-scrollbar">
        {[{ key: 'filter-all', label: 'ALL' }, ...Object.entries(ROLE_LABELS).map(([k, v]) => ({ key: k, label: v }))].map(({ key, label }) => (
          <button key={key} onClick={() => setFilter(key === 'filter-all' ? null : key)}
            className={`px-3 py-1 rounded-full text-xs font-medium ${filter === (key === 'filter-all' ? null : key) ? 'bg-emerald-500 text-white' : 'bg-white/5 text-gray-400'}`}
            data-testid={`filter-${key === 'filter-all' ? 'all' : key}`}
          >{label} {key === 'filter-all' ? `(${allPlayers.length})` : `(${allPlayers.filter(p => p.role === key).length})`}</button>
        ))}
      </div>

      {/* Player list */}
      <div className="px-3 space-y-1 mt-1">
        {filtered.map(p => {
          const isSelected = selected.find(s => s.player_id === p.player_id);
          const canAdd = !isSelected && canSelect(p);
          return (
            <button key={p.player_id} onClick={() => togglePlayer(p)}
              className={`w-full flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                isSelected ? 'bg-emerald-500/15 border border-emerald-500/30' :
                canAdd ? 'bg-white/5 border border-transparent hover:bg-white/10' :
                'bg-white/3 border border-transparent opacity-40'
              }`}
              disabled={!isSelected && !canAdd}
              data-testid={`player-${p.player_id}`}
            >
              <div className={`w-8 h-8 rounded-full ${ROLE_BG[p.role]} flex items-center justify-center`}>
                <span className={`text-[10px] font-bold ${ROLE_COLORS[p.role]}`}>{ROLE_LABELS[p.role]}</span>
              </div>
              <div className="flex-1 text-left min-w-0">
                <div className="text-sm font-medium truncate">{p.short_name || p.name}</div>
                <div className="text-[10px] text-gray-500">{p.team}</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-bold">{p.credit}</div>
              </div>
              <div className="w-6">
                {isSelected ? <Check className="w-5 h-5 text-emerald-400" /> : null}
              </div>
            </button>
          );
        })}
      </div>

      {/* Bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-[#0f1520] border-t border-white/10 p-4">
        <button onClick={proceedToCaptain}
          disabled={selected.length !== 11}
          className="w-full py-3 bg-emerald-500 text-white font-bold rounded-xl disabled:opacity-40 transition-all"
          data-testid="proceed-captain-btn"
        >
          {selected.length === 11 ? 'Choose Captain & VC' : `Select ${11 - selected.length} more`}
        </button>
      </div>
    </div>
  );

  // ── Step 2: Captain / VC Selection ──
  if (step === 'captain') return (
    <div className="min-h-screen bg-[#0a0e17] text-white pb-24" data-testid="team-builder-captain">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3">
        <button onClick={() => setStep('select')} data-testid="back-button"><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-base font-bold">Choose Captain & Vice-Captain</h1>
      </div>

      <div className="px-4 py-3 bg-gradient-to-r from-yellow-900/20 to-blue-900/20 border-b border-white/5">
        <div className="flex gap-4 text-center text-xs">
          <div className="flex-1">
            <div className="text-yellow-400 font-bold">Captain (C)</div>
            <div className="text-gray-400">Gets 2x points</div>
          </div>
          <div className="flex-1">
            <div className="text-blue-400 font-bold">Vice-Captain (VC)</div>
            <div className="text-gray-400">Gets 1.5x points</div>
          </div>
        </div>
      </div>

      <div className="px-3 mt-2 space-y-1">
        {selected.map(p => (
          <div key={p.player_id} className="flex items-center gap-3 p-2.5 bg-white/5 rounded-xl" data-testid={`cv-player-${p.player_id}`}>
            <div className={`w-8 h-8 rounded-full ${ROLE_BG[p.role]} flex items-center justify-center`}>
              <span className={`text-[10px] font-bold ${ROLE_COLORS[p.role]}`}>{ROLE_LABELS[p.role]}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{p.short_name || p.name}</div>
              <div className="text-[10px] text-gray-500">{p.team}</div>
            </div>
            <button onClick={() => { setCaptain(p.player_id); if (vc === p.player_id) setVc(null); }}
              className={`w-10 h-10 rounded-full border-2 flex items-center justify-center text-xs font-black transition-all ${
                captain === p.player_id ? 'border-yellow-400 bg-yellow-500/20 text-yellow-400' : 'border-white/20 text-gray-500 hover:border-yellow-400/50'
              }`} data-testid={`captain-${p.player_id}`}
            >C</button>
            <button onClick={() => { setVc(p.player_id); if (captain === p.player_id) setCaptain(null); }}
              className={`w-10 h-10 rounded-full border-2 flex items-center justify-center text-xs font-black transition-all ${
                vc === p.player_id ? 'border-blue-400 bg-blue-500/20 text-blue-400' : 'border-white/20 text-gray-500 hover:border-blue-400/50'
              }`} data-testid={`vc-${p.player_id}`}
            >VC</button>
          </div>
        ))}
      </div>

      <div className="fixed bottom-0 left-0 right-0 bg-[#0f1520] border-t border-white/10 p-4">
        <button onClick={proceedToPreview}
          disabled={!captain || !vc}
          className="w-full py-3 bg-emerald-500 text-white font-bold rounded-xl disabled:opacity-40 transition-all"
          data-testid="proceed-preview-btn"
        >Preview Team</button>
      </div>
    </div>
  );

  // ── Step 3: Preview & Confirm ──
  const captainPlayer = selected.find(p => p.player_id === captain);
  const vcPlayer = selected.find(p => p.player_id === vc);

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white pb-24" data-testid="team-builder-preview">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3">
        <button onClick={() => setStep('captain')} data-testid="back-button"><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-base font-bold">Team Preview</h1>
      </div>

      {/* Captain/VC highlight */}
      <div className="flex gap-3 px-4 mt-4">
        <div className="flex-1 bg-gradient-to-br from-yellow-900/30 to-yellow-800/10 rounded-xl p-3 border border-yellow-500/20 text-center" data-testid="captain-card">
          <div className="text-[10px] text-yellow-400/60 uppercase">Captain</div>
          <div className="text-sm font-bold mt-1">{captainPlayer?.short_name}</div>
          <div className="text-xs text-yellow-400 mt-0.5">2x Points</div>
        </div>
        <div className="flex-1 bg-gradient-to-br from-blue-900/30 to-blue-800/10 rounded-xl p-3 border border-blue-500/20 text-center" data-testid="vc-card">
          <div className="text-[10px] text-blue-400/60 uppercase">Vice-Captain</div>
          <div className="text-sm font-bold mt-1">{vcPlayer?.short_name}</div>
          <div className="text-xs text-blue-400 mt-0.5">1.5x Points</div>
        </div>
      </div>

      {/* Team summary */}
      <div className="mx-4 mt-3 bg-white/5 rounded-xl p-3 flex justify-between text-xs" data-testid="team-summary">
        <span>Credits: <strong className="text-emerald-400">{totalCredits}/100</strong></span>
        <span>Players: <strong>11</strong></span>
        {Object.entries(roleCounts).map(([r, c]) => (
          <span key={r}><span className={ROLE_COLORS[r]}>{ROLE_LABELS[r]}</span>: {c}</span>
        ))}
      </div>

      {/* Player list */}
      <div className="px-3 mt-3 space-y-1">
        {selected.map(p => (
          <div key={p.player_id} className="flex items-center gap-3 p-2 bg-white/5 rounded-lg" data-testid={`preview-${p.player_id}`}>
            <div className={`w-7 h-7 rounded-full ${ROLE_BG[p.role]} flex items-center justify-center`}>
              <span className={`text-[9px] font-bold ${ROLE_COLORS[p.role]}`}>{ROLE_LABELS[p.role]}</span>
            </div>
            <span className="flex-1 text-sm truncate">{p.short_name || p.name}</span>
            {p.player_id === captain && <span className="px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 text-[10px] rounded font-bold">C</span>}
            {p.player_id === vc && <span className="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 text-[10px] rounded font-bold">VC</span>}
            <span className="text-xs text-gray-400">{p.credit}</span>
          </div>
        ))}
      </div>

      <div className="fixed bottom-0 left-0 right-0 bg-[#0f1520] border-t border-white/10 p-4 flex gap-2">
        <button onClick={() => setStep('select')} className="px-4 py-3 bg-white/10 text-white rounded-xl text-sm">Edit</button>
        <button onClick={createTeam} disabled={creating}
          className="flex-1 py-3 bg-emerald-500 text-white font-bold rounded-xl disabled:opacity-50 transition-all"
          data-testid="create-team-btn"
        >{creating ? 'Creating...' : 'Create Team'}</button>
      </div>
    </div>
  );
}
