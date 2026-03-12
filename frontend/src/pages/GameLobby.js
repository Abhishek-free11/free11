import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Spade, Heart, Diamond, Users, Trophy, Coins,
  Play, Plus, ChevronRight, Crown, Star, Zap, Copy, ArrowLeft
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import Navbar from '../components/Navbar';

const GAME_INFO = {
  rummy: {
    name: 'Rummy',
    description: 'Classic 13-card Indian Rummy. Form sequences & sets to win.',
    icon: Spade,
    accent: '#ef4444',
    gradient: 'linear-gradient(135deg, #ef4444, #ec4899)',
    bg: 'rgba(239,68,68,0.08)',
    border: 'rgba(239,68,68,0.25)',
    rewards: { win: 50, second: 20, participate: 5 },
  },
  teen_patti: {
    name: 'Teen Patti',
    description: '3-card Indian poker. Bluff, bet & beat your opponents.',
    icon: Heart,
    accent: '#a855f7',
    gradient: 'linear-gradient(135deg, #a855f7, #6366f1)',
    bg: 'rgba(168,85,247,0.08)',
    border: 'rgba(168,85,247,0.25)',
    rewards: { win: 40, second: 15, participate: 5 },
  },
  poker: {
    name: 'Poker',
    description: 'Texas Hold\'em. Best hand wins the pot.',
    icon: Diamond,
    accent: '#22c55e',
    gradient: 'linear-gradient(135deg, #22c55e, #10b981)',
    bg: 'rgba(34,197,94,0.08)',
    border: 'rgba(34,197,94,0.25)',
    rewards: { win: 60, second: 25, participate: 5 },
  },
};

export default function GameLobby() {
  const navigate = useNavigate();
  const { gameType } = useParams();
  const { user } = useAuth();
  const [rooms, setRooms] = useState([]);
  const [myRooms, setMyRooms] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [joinCode, setJoinCode] = useState('');
  const [showJoin, setShowJoin] = useState(false);

  const info = GAME_INFO[gameType];

  useEffect(() => {
    if (!info) { navigate('/games'); return; }
    fetchRooms();
    fetchStats();
    fetchMyRooms();
  }, [gameType]);

  if (!info) return null;
  const Icon = info.icon;

  const fetchRooms = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/games/${gameType}/rooms`);
      setRooms(res.data.rooms || []);
    } catch {
      setRooms([]);
    } finally { setLoading(false); }
  };

  const fetchStats = async () => {
    try {
      const res = await api.get(`/games/${gameType}/stats/my`);
      setStats(res.data || {});
    } catch {}
  };

  const fetchMyRooms = async () => {
    try {
      const res = await api.get('/games/my-rooms');
      const filtered = (res.data.rooms || []).filter(r => r.game_type === gameType);
      setMyRooms(filtered);
    } catch {}
  };

  const handleQuickPlay = async () => {
    try {
      setLoading(true);
      const res = await api.post(`/games/${gameType}/quick-play`);
      toast.success(res.data.message);
      navigate(`/games/${gameType}/room/${res.data.room.id}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to start game');
    } finally { setLoading(false); }
  };

  const handleCreateRoom = async (isPrivate = false) => {
    try {
      const res = await api.post(`/games/${gameType}/rooms/create`, {
        game_type: gameType, name: `${info.name} Room`, max_players: 4, is_private: isPrivate,
      });
      if (isPrivate && res.data.room_code) {
        toast.success(`Room code: ${res.data.room_code} (copied!)`);
        navigator.clipboard.writeText(res.data.room_code).catch(() => {});
      } else {
        toast.success('Room created!');
      }
      navigate(`/games/${gameType}/room/${res.data.room.id}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to create room');
    }
  };

  const handleJoinByCode = async () => {
    if (!joinCode.trim()) { toast.error('Enter a room code'); return; }
    try {
      const res = await api.post('/games/rooms/join-by-code', null, { params: { code: joinCode.toUpperCase() } });
      toast.success(res.data.message);
      const room = res.data.room;
      navigate(`/games/${room.game_type}/room/${room.id}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Invalid room code');
    }
  };

  return (
    <div className="min-h-screen pb-28" style={{ background: '#0F1115' }}>
      <Navbar />

      {/* Hero header */}
      <div style={{ background: info.gradient, padding: '20px 16px 16px' }}>
        <div className="max-w-screen-sm mx-auto">
          <button
            onClick={() => navigate('/games')}
            style={{ color: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, marginBottom: 12 }}
            data-testid="back-to-games-btn"
          >
            <ArrowLeft size={15} /> All Games
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 56, height: 56, borderRadius: 16, background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Icon className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 style={{ color: '#fff', fontSize: 24, fontWeight: 800 }}>{info.name}</h1>
              <p style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13 }}>{info.description}</p>
            </div>
          </div>
          {/* Reward chips */}
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            {[['1st', info.rewards.win, '🥇'], ['2nd', info.rewards.second, '🥈'], ['Play', info.rewards.participate, '🎴']].map(([label, coins, emoji]) => (
              <div key={label} style={{ background: 'rgba(255,255,255,0.15)', borderRadius: 20, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ fontSize: 12 }}>{emoji}</span>
                <span style={{ color: '#fff', fontSize: 11, fontWeight: 700 }}>{label}: +{coins}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-screen-sm mx-auto px-4 mt-5 space-y-5">

        {/* Active games */}
        {myRooms.length > 0 && (
          <div>
            <p style={{ color: '#C6A052', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 8 }}>YOUR ACTIVE GAMES</p>
            {myRooms.map(room => (
              <button key={room.id} onClick={() => navigate(`/games/${gameType}/room/${room.id}`)}
                className="w-full flex items-center justify-between p-3 rounded-xl mb-2"
                style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.2)' }}
                data-testid={`active-room-${room.id}`}>
                <span className="text-white text-sm font-medium">{room.name}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 20, background: room.status === 'playing' ? 'rgba(74,222,128,0.15)' : 'rgba(96,165,250,0.15)', color: room.status === 'playing' ? '#4ade80' : '#60a5fa' }}>
                    {room.status === 'playing' ? 'In Progress' : 'Waiting'}
                  </span>
                  <ChevronRight size={14} style={{ color: '#8A9096' }} />
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Quick actions */}
        <div>
          <p style={{ color: '#8A9096', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 8 }}>START PLAYING</p>
          {/* Play vs AI — primary CTA for teen_patti, secondary for others */}
          {gameType === 'teen_patti' && (
            <button
              onClick={() => navigate('/games/teen_patti/play')}
              style={{ width: '100%', background: info.gradient, borderRadius: 14, padding: '18px 20px', textAlign: 'left', cursor: 'pointer', border: 'none', marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              data-testid="play-vs-ai-btn"
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ background: 'rgba(255,255,255,0.25)', borderRadius: 20, padding: '2px 8px', color: '#fff', fontSize: 9, fontWeight: 800 }}>INSTANT PLAY</span>
                </div>
                <p style={{ color: '#fff', fontWeight: 800, fontSize: 17 }}>Play vs AI</p>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>Start immediately · Win +40 coins</p>
              </div>
              <ChevronRight className="h-6 w-6 text-white opacity-70" />
            </button>
          )}
          {gameType === 'rummy' && (
            <button
              onClick={() => navigate('/games/rummy/play')}
              style={{ width: '100%', background: info.gradient, borderRadius: 14, padding: '18px 20px', textAlign: 'left', cursor: 'pointer', border: 'none', marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              data-testid="play-vs-ai-btn"
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ background: 'rgba(255,255,255,0.25)', borderRadius: 20, padding: '2px 8px', color: '#fff', fontSize: 9, fontWeight: 800 }}>INSTANT PLAY</span>
                </div>
                <p style={{ color: '#fff', fontWeight: 800, fontSize: 17 }}>Play vs AI</p>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>13-card Rummy · Win +50 coins</p>
              </div>
              <ChevronRight className="h-6 w-6 text-white opacity-70" />
            </button>
          )}
          {gameType === 'poker' && (
            <button
              onClick={() => navigate('/games/poker/play')}
              style={{ width: '100%', background: info.gradient, borderRadius: 14, padding: '18px 20px', textAlign: 'left', cursor: 'pointer', border: 'none', marginBottom: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
              data-testid="play-vs-ai-btn"
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ background: 'rgba(255,255,255,0.25)', borderRadius: 20, padding: '2px 8px', color: '#fff', fontSize: 9, fontWeight: 800 }}>INSTANT PLAY</span>
                </div>
                <p style={{ color: '#fff', fontWeight: 800, fontSize: 17 }}>Play vs AI</p>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>Texas Hold'em · Win +60 coins</p>
              </div>
              <ChevronRight className="h-6 w-6 text-white opacity-70" />
            </button>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <button onClick={handleQuickPlay} disabled={loading}
              style={{ background: info.gradient, borderRadius: 14, padding: '18px 16px', textAlign: 'left', cursor: 'pointer', border: 'none', opacity: loading ? 0.7 : 1 }}
              data-testid="quick-play-btn">
              <Zap className="h-5 w-5 text-white mb-2" />
              <p style={{ color: '#fff', fontWeight: 800, fontSize: 15 }}>Quick Play</p>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 11 }}>Join instantly</p>
            </button>
            <button onClick={() => handleCreateRoom(false)}
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14, padding: '18px 16px', textAlign: 'left', cursor: 'pointer' }}
              data-testid="create-room-btn">
              <Plus className="h-5 w-5 text-white mb-2" />
              <p style={{ color: '#fff', fontWeight: 800, fontSize: 15 }}>Create Room</p>
              <p style={{ color: '#8A9096', fontSize: 11 }}>Public · up to 4p</p>
            </button>
          </div>
          <button onClick={() => handleCreateRoom(true)}
            className="w-full mt-2 flex items-center justify-center gap-2 p-3.5 rounded-xl"
            style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}
            data-testid="create-private-btn">
            <Users className="h-4 w-4" style={{ color: '#8A9096' }} />
            <span style={{ color: '#BFC3C8', fontSize: 14 }}>Create Private Room (invite friends)</span>
          </button>
        </div>

        {/* Join by code */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: 16 }}>
          {!showJoin ? (
            <button onClick={() => setShowJoin(true)} className="flex items-center gap-2 text-sm" style={{ color: '#8A9096' }} data-testid="join-code-toggle">
              <Copy size={14} /> Join with a room code
            </button>
          ) : (
            <div style={{ display: 'flex', gap: 8 }}>
              <Input
                placeholder="Enter code (e.g. ABC123)"
                value={joinCode}
                onChange={e => setJoinCode(e.target.value.toUpperCase())}
                maxLength={6}
                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)', color: '#fff', borderRadius: 10 }}
                data-testid="join-code-input"
              />
              <Button onClick={handleJoinByCode} style={{ background: info.gradient, border: 'none' }} data-testid="join-code-submit">Join</Button>
              <Button variant="ghost" onClick={() => setShowJoin(false)} style={{ color: '#8A9096' }}>✕</Button>
            </div>
          )}
        </div>

        {/* My Stats */}
        <div>
          <p style={{ color: '#8A9096', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 8 }}>YOUR STATS</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
            {[
              { label: 'Played', value: stats.games_played || 0 },
              { label: 'Won', value: stats.games_won || 0, color: '#4ade80' },
              { label: 'Win%', value: `${stats.win_rate || 0}%`, color: '#C6A052' },
              { label: 'Coins', value: stats.total_coins_earned || 0, color: '#a78bfa' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '12px 8px', textAlign: 'center' }}>
                <p style={{ fontSize: 18, fontWeight: 800, color: color || '#fff' }}>{value}</p>
                <p style={{ fontSize: 10, color: '#8A9096', marginTop: 2 }}>{label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Available rooms */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <p style={{ color: '#8A9096', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em' }}>OPEN ROOMS</p>
            <button onClick={fetchRooms} style={{ color: '#C6A052', fontSize: 12 }}>Refresh</button>
          </div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: 24 }}>
              <div className="animate-spin h-6 w-6 rounded-full border-2 mx-auto" style={{ borderColor: info.accent, borderTopColor: 'transparent' }} />
            </div>
          ) : rooms.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '20px 0', color: '#8A9096', fontSize: 13 }}>
              No open rooms right now. Create one above!
            </div>
          ) : (
            rooms.map(room => (
              <button key={room.id} onClick={() => navigate(`/games/${gameType}/room/${room.id}`)}
                className="w-full flex items-center justify-between p-3 rounded-xl mb-2"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
                data-testid={`room-${room.id}`}>
                <span style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{room.name}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ color: '#8A9096', fontSize: 12, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Users size={12} /> {room.current_players || 1}/{room.max_players || 4}
                  </span>
                  <ChevronRight size={14} style={{ color: '#8A9096' }} />
                </div>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
