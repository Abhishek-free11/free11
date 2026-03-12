import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Spade, Heart, Diamond, Club, Users, ChevronRight, Copy, Layers, Flame, Trophy, Zap
} from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import api from '../utils/api';
import Navbar from '../components/Navbar';

const GAMES = [
  {
    key: 'rummy',
    name: 'Rummy',
    tagline: 'vs AI · Play instantly!',
    icon: Spade,
    gradient: 'linear-gradient(135deg, #ef4444 0%, #ec4899 100%)',
    accent: '#ef4444',
    rewards: '+50 coins to win',
    players: 'vs AI or multiplayer',
    badge: 'PLAYABLE',
  },
  {
    key: 'teen_patti',
    name: 'Teen Patti',
    tagline: 'vs AI · Play instantly!',
    icon: Heart,
    gradient: 'linear-gradient(135deg, #a855f7 0%, #6366f1 100%)',
    accent: '#a855f7',
    rewards: '+40 coins to win',
    players: 'vs AI or multiplayer',
    badge: 'PLAYABLE',
  },
  {
    key: 'poker',
    name: 'Poker',
    tagline: "Texas Hold'em · vs AI!",
    icon: Diamond,
    gradient: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
    accent: '#22c55e',
    rewards: '+60 coins to win',
    players: 'vs AI or multiplayer',
    badge: 'PLAYABLE',
  },
  {
    key: 'solitaire',
    name: 'Solitaire',
    tagline: 'Solo Klondike — beat the deck',
    icon: Layers,
    gradient: 'linear-gradient(135deg, #f59e0b 0%, #C6A052 100%)',
    accent: '#f59e0b',
    rewards: '+25 coins on win',
    players: 'Solo game',
    badge: 'NEW',
  },
];

export default function CardGames() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const [myRooms, setMyRooms] = useState([]);
  const [showJoin, setShowJoin] = useState(false);
  const [joinCode, setJoinCode] = useState('');
  const [leaderboard, setLeaderboard] = useState([]);
  const [streak, setStreak] = useState(0);
  const [playedToday, setPlayedToday] = useState(false);

  // Handle ?join= invite links
  useEffect(() => {
    const code = searchParams.get('join');
    if (code) { setJoinCode(code); setShowJoin(true); }
  }, [searchParams]);

  useEffect(() => {
    fetchMyRooms();
    fetchLeaderboard();
    fetchStreak();
  }, []);

  const fetchMyRooms = async () => {
    try {
      const res = await api.get('/games/my-rooms');
      setMyRooms(res.data.rooms || []);
    } catch {}
  };

  const fetchLeaderboard = async () => {
    try {
      const res = await api.get('/v2/games/card-leaderboard');
      setLeaderboard(res.data.leaderboard || []);
    } catch {}
  };

  const fetchStreak = async () => {
    try {
      const res = await api.get('/v2/games/card-streak');
      setStreak(res.data.streak || 0);
      setPlayedToday(res.data.played_today || false);
    } catch {}
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

  const handleGameClick = (game) => {
    if (game.key === 'solitaire') {
      navigate('/games/solitaire');
    } else {
      navigate(`/games/${game.key}`);
    }
  };

  const GAME_ICONS = { rummy: Spade, teen_patti: Heart, poker: Diamond, solitaire: Layers };

  return (
    <div className="min-h-screen pb-28" style={{ background: '#0F1115' }}>
      <Navbar />

      {/* Page header */}
      <div className="max-w-screen-sm mx-auto px-4 pt-5 pb-2">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg,#C6A052,#E0B84F)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Club className="h-5 w-5" style={{ color: '#0F1115' }} />
          </div>
          <div>
            <h1 style={{ color: '#fff', fontSize: 22, fontWeight: 800, letterSpacing: '-0.02em' }}>Card Games</h1>
            <p style={{ color: '#8A9096', fontSize: 12 }}>FREE to play · Earn coins every game</p>
          </div>
        </div>
      </div>

      <div className="max-w-screen-sm mx-auto px-4 space-y-4">

        {/* Join by code */}
        {showJoin ? (
          <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 14, padding: 14, display: 'flex', gap: 8 }}>
            <Input
              placeholder="Room code (e.g. ABC123)"
              value={joinCode}
              onChange={e => setJoinCode(e.target.value.toUpperCase())}
              maxLength={6}
              style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)', color: '#fff', borderRadius: 10, flex: 1 }}
              data-testid="join-code-input-hub"
            />
            <Button onClick={handleJoinByCode} style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)', color: '#0F1115', fontWeight: 700, border: 'none' }} data-testid="join-code-submit-hub">Join</Button>
            <Button variant="ghost" onClick={() => setShowJoin(false)} style={{ color: '#8A9096' }}>✕</Button>
          </div>
        ) : (
          <button onClick={() => setShowJoin(true)}
            className="flex items-center gap-2 py-2 text-sm"
            style={{ color: '#8A9096' }}
            data-testid="join-private-room-btn">
            <Copy size={14} /> Join a private room with code
          </button>
        )}

        {/* Active rooms banner */}
        {myRooms.length > 0 && (
          <div style={{ background: 'rgba(198,160,82,0.07)', border: '1px solid rgba(198,160,82,0.2)', borderRadius: 14, padding: '12px 16px' }}>
            <p style={{ color: '#C6A052', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 8 }}>ACTIVE GAMES</p>
            {myRooms.map(room => {
              const RoomIcon = GAME_ICONS[room.game_type] || Club;
              return (
                <button key={room.id} onClick={() => navigate(`/games/${room.game_type}/room/${room.id}`)}
                  className="w-full flex items-center gap-3 py-2"
                  data-testid={`active-room-hub-${room.id}`}>
                  <RoomIcon size={16} style={{ color: '#C6A052' }} />
                  <span style={{ color: '#fff', fontSize: 13, flex: 1, textAlign: 'left' }}>{room.name}</span>
                  <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 20, background: 'rgba(74,222,128,0.12)', color: '#4ade80' }}>
                    {room.status === 'playing' ? 'Playing' : 'Waiting'}
                  </span>
                  <ChevronRight size={14} style={{ color: '#8A9096' }} />
                </button>
              );
            })}
          </div>
        )}

        {/* Game grid */}
        <div>
          <p style={{ color: '#8A9096', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 10 }}>CHOOSE A GAME</p>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {GAMES.map((game, i) => {
              const Icon = game.icon;
              return (
                <motion.button
                  key={game.key}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  onClick={() => handleGameClick(game)}
                  style={{
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 16,
                    padding: '18px 14px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    position: 'relative',
                    overflow: 'hidden',
                  }}
                  whileHover={{ scale: 1.02, borderColor: game.accent }}
                  whileTap={{ scale: 0.97 }}
                  data-testid={`game-card-${game.key}`}
                >
                  {/* Glow background */}
                  <div style={{ position: 'absolute', top: -20, right: -20, width: 80, height: 80, borderRadius: '50%', background: game.gradient, opacity: 0.12, filter: 'blur(20px)' }} />

                  {/* Badge */}
                  {game.badge && (
                    <div style={{ position: 'absolute', top: 8, right: 8, background: game.gradient, color: '#fff', fontSize: 8, fontWeight: 800, padding: '2px 6px', borderRadius: 20, letterSpacing: '0.05em' }}>
                      {game.badge}
                    </div>
                  )}

                  {/* Icon */}
                  <div style={{ width: 44, height: 44, borderRadius: 12, background: game.gradient, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                    <Icon className="h-5 w-5 text-white" />
                  </div>

                  <p style={{ color: '#fff', fontWeight: 800, fontSize: 15, marginBottom: 2 }}>{game.name}</p>
                  <p style={{ color: '#8A9096', fontSize: 11, marginBottom: 10, lineHeight: 1.4 }}>{game.tagline}</p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    <span style={{ fontSize: 10, color: '#C6A052', fontWeight: 700 }}>{game.rewards}</span>
                    <span style={{ fontSize: 10, color: '#8A9096', display: 'flex', alignItems: 'center', gap: 3 }}>
                      <Users size={9} /> {game.players}
                    </span>
                  </div>
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* Streak + Leaderboard */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {/* Daily Streak */}
          <div style={{
            background: streak > 0 ? 'rgba(251,146,60,0.08)' : 'rgba(255,255,255,0.03)',
            border: `1px solid ${streak > 0 ? 'rgba(251,146,60,0.3)' : 'rgba(255,255,255,0.07)'}`,
            borderRadius: 14, padding: 14, textAlign: 'center',
          }} data-testid="streak-card">
            <Flame size={20} style={{ color: streak > 0 ? '#fb923c' : '#8A9096', margin: '0 auto 6px' }} />
            <p style={{ color: streak > 0 ? '#fb923c' : '#8A9096', fontSize: 28, fontWeight: 800, lineHeight: 1 }}>{streak}</p>
            <p style={{ color: '#fff', fontSize: 12, fontWeight: 700 }}>Day Streak</p>
            <p style={{ color: '#8A9096', fontSize: 10, marginTop: 3 }}>
              {playedToday ? 'Played today!' : 'Play to continue'}
            </p>
            {streak >= 3 && (
              <div style={{ marginTop: 6, background: 'rgba(251,146,60,0.15)', borderRadius: 8, padding: '3px 0' }}>
                <span style={{ color: '#fb923c', fontSize: 9, fontWeight: 800 }}>
                  {streak >= 7 ? 'LEGENDARY!' : streak >= 5 ? 'ON FIRE!' : 'STREAK BONUS!'}
                </span>
              </div>
            )}
          </div>

          {/* Top Player */}
          <div style={{
            background: 'rgba(198,160,82,0.06)',
            border: '1px solid rgba(198,160,82,0.2)',
            borderRadius: 14, padding: 14, textAlign: 'center',
          }} data-testid="leaderboard-preview">
            <Trophy size={20} style={{ color: '#C6A052', margin: '0 auto 6px' }} />
            <p style={{ color: '#C6A052', fontSize: 11, fontWeight: 800, letterSpacing: '0.06em' }}>THIS WEEK</p>
            {leaderboard.length > 0 ? (
              <>
                <p style={{ color: '#fff', fontSize: 13, fontWeight: 800, marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {leaderboard[0].name || 'Player'}
                </p>
                <p style={{ color: '#C6A052', fontSize: 12, fontWeight: 700 }}>{leaderboard[0].total_coins} coins</p>
                <p style={{ color: '#8A9096', fontSize: 10 }}>{leaderboard[0].wins} wins</p>
              </>
            ) : (
              <p style={{ color: '#8A9096', fontSize: 12, marginTop: 8 }}>No games yet</p>
            )}
          </div>
        </div>

        {/* Full Leaderboard (if data exists) */}
        {leaderboard.length > 1 && (
          <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 14, padding: '14px' }} data-testid="full-leaderboard">
            <p style={{ color: '#8A9096', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 10 }}>TOP CARD GAME PLAYERS THIS WEEK</p>
            {leaderboard.slice(0, 5).map((entry, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, paddingBottom: 8, borderBottom: i < 4 ? '1px solid rgba(255,255,255,0.05)' : 'none', marginBottom: i < 4 ? 8 : 0 }}>
                <span style={{ color: i === 0 ? '#C6A052' : i === 1 ? '#94a3b8' : i === 2 ? '#f97316' : '#8A9096', fontSize: 14, fontWeight: 800, width: 20, textAlign: 'center' }}>
                  {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}`}
                </span>
                <span style={{ color: '#fff', fontSize: 13, flex: 1, fontWeight: entry.user_id === user?.id ? 700 : 400 }}>
                  {entry.name || 'Player'}{entry.user_id === user?.id ? ' (You)' : ''}
                </span>
                <span style={{ color: '#C6A052', fontSize: 12, fontWeight: 700 }}>{entry.total_coins} coins</span>
                <span style={{ color: '#8A9096', fontSize: 10 }}>{entry.wins}W</span>
              </div>
            ))}
          </div>
        )}

        {/* How it works */}
        <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 14, padding: 16 }}>
          <p style={{ color: '#8A9096', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 12 }}>HOW IT WORKS</p>
          {[
            { n: '1', t: 'Pick a game above', s: 'Tap any game card to enter its lobby' },
            { n: '2', t: 'Join or create a room', s: 'Play with random players or invite friends' },
            { n: '3', t: 'Play & earn coins', s: 'Win coins instantly — no entry fee ever' },
          ].map(({ n, t, s }) => (
            <div key={n} style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
              <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'rgba(198,160,82,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                <span style={{ color: '#C6A052', fontSize: 11, fontWeight: 800 }}>{n}</span>
              </div>
              <div>
                <p style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{t}</p>
                <p style={{ color: '#8A9096', fontSize: 11 }}>{s}</p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
