import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Trophy, Coins, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import confetti from 'canvas-confetti';
import api from '../utils/api';
import Navbar from '../components/Navbar';

// ── Card constants ──────────────────────────────────────────────────────────
const SUITS = ['spades', 'hearts', 'diamonds', 'clubs'];
const SUIT_SYMBOLS = { spades: '♠', hearts: '♥', diamonds: '♦', clubs: '♣' };
const RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'];
const RANK_VALUES = { '2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14 };
const RED_SUITS = new Set(['hearts','diamonds']);

function createDeck() {
  const deck = [];
  for (const suit of SUITS)
    for (const rank of RANKS)
      deck.push({ suit, rank, id: `${suit}_${rank}` });
  return deck;
}

function shuffle(arr) {
  const d = [...arr];
  for (let i = d.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [d[i], d[j]] = [d[j], d[i]];
  }
  return d;
}

// ── Hand evaluation ──────────────────────────────────────────────────────────
function evaluateHand(cards) {
  if (!cards || cards.length < 3) return { rank: 0, name: '–' };
  const ranks = cards.map(c => RANK_VALUES[c.rank]);
  const suits = cards.map(c => c.suit);
  const rankSet = new Set(ranks);
  const isFlush = suits.every(s => s === suits[0]);
  const sorted = [...ranks].sort((a, b) => a - b);
  const isSeq = sorted[2] - sorted[0] === 2 && sorted[1] - sorted[0] === 1;
  const isAce23 = rankSet.has(14) && rankSet.has(2) && rankSet.has(3) && rankSet.size === 3;
  if (rankSet.size === 1) return { rank: 6, name: 'Trail' };
  if (isFlush && (isSeq || isAce23)) return { rank: 5, name: 'Pure Sequence' };
  if (isSeq || isAce23) return { rank: 4, name: 'Sequence' };
  if (isFlush) return { rank: 3, name: 'Color' };
  if (rankSet.size === 2) return { rank: 2, name: 'Pair' };
  return { rank: 1, name: 'High Card' };
}

function compareHands(cards1, cards2) {
  const h1 = evaluateHand(cards1);
  const h2 = evaluateHand(cards2);
  if (h1.rank !== h2.rank) return h1.rank > h2.rank ? 1 : -1;
  const v1 = cards1.map(c => RANK_VALUES[c.rank]).sort((a, b) => b - a);
  const v2 = cards2.map(c => RANK_VALUES[c.rank]).sort((a, b) => b - a);
  for (let i = 0; i < 3; i++) {
    if (v1[i] !== v2[i]) return v1[i] > v2[i] ? 1 : -1;
  }
  return 0;
}

function getAIAction(cards, personality, round) {
  const hand = evaluateHand(cards);
  if (personality === 'conservative') {
    if (hand.rank >= 5) return 'raise';
    if (hand.rank >= 3) return 'call';
    if (hand.rank === 2) return 'call';
    return Math.random() < 0.55 ? 'fold' : 'call';
  }
  // aggressive
  if (hand.rank >= 4) return 'raise';
  if (hand.rank >= 2) return 'call';
  return Math.random() < 0.15 ? 'fold' : 'call';
}

// ── PlayingCard ──────────────────────────────────────────────────────────────
function Card({ card, hidden = false, small = false, glow = false }) {
  const w = small ? 44 : 66;
  const h = small ? 62 : 94;
  const r = small ? 8 : 12;
  const fsMain = small ? 14 : 20;
  const fsSuit = small ? 16 : 28;

  if (hidden) {
    return (
      <div style={{
        width: w, height: h, borderRadius: r, flexShrink: 0,
        background: 'linear-gradient(135deg,#3730a3,#1e1b4b)',
        border: '1.5px solid rgba(255,255,255,0.18)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
      }}>
        <span style={{ fontSize: small ? 18 : 26, opacity: 0.3 }}>♠</span>
      </div>
    );
  }

  const isRed = RED_SUITS.has(card?.suit);
  const clr = isRed ? '#e53e3e' : '#1a202c';

  return (
    <div style={{
      width: w, height: h, borderRadius: r, flexShrink: 0,
      background: '#fff',
      border: glow ? '2px solid #C6A052' : '1.5px solid #e2e8f0',
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'space-between', padding: 6,
      boxShadow: glow ? '0 0 14px rgba(198,160,82,0.6)' : '0 4px 12px rgba(0,0,0,0.35)',
      transition: 'box-shadow 0.2s',
    }}>
      <span style={{ fontSize: fsMain, fontWeight: 800, color: clr, lineHeight: 1, alignSelf: 'flex-start' }}>{card?.rank}</span>
      <span style={{ fontSize: fsSuit, color: clr }}>{SUIT_SYMBOLS[card?.suit]}</span>
      <span style={{ fontSize: fsMain, fontWeight: 800, color: clr, lineHeight: 1, alignSelf: 'flex-end', transform: 'rotate(180deg)' }}>{card?.rank}</span>
    </div>
  );
}

// ── Chip / badge ─────────────────────────────────────────────────────────────
function Chip({ label, color = '#8A9096', bg = 'rgba(255,255,255,0.06)' }) {
  return (
    <span style={{ background: bg, color, fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 20 }}>
      {label}
    </span>
  );
}

// ── AI Player Row ─────────────────────────────────────────────────────────────
function AIPlayer({ name, cards, folded, action, revealed }) {
  const statusColor = folded ? '#ef4444' : action === 'raise' ? '#C6A052' : action === 'call' ? '#4ade80' : '#8A9096';
  const statusLabel = folded ? 'Folded' : action === 'raise' ? 'Raised +10' : action === 'call' ? 'Called' : action === 'thinking' ? '...' : 'In';

  return (
    <div style={{
      background: folded ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.04)',
      border: `1px solid ${folded ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.08)'}`,
      borderRadius: 14, padding: '12px 14px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      opacity: folded ? 0.6 : 1,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: folded ? 'rgba(239,68,68,0.15)' : 'linear-gradient(135deg,#a855f7,#6366f1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ color: '#fff', fontSize: 14, fontWeight: 800 }}>{name[0]}</span>
        </div>
        <div>
          <p style={{ color: folded ? '#8A9096' : '#fff', fontSize: 13, fontWeight: 700 }}>{name}</p>
          <Chip label={statusLabel} color={statusColor} bg={`${statusColor}18`} />
        </div>
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        {cards.map((card, i) => (
          <Card key={i} card={revealed ? card : null} hidden={!revealed} small />
        ))}
      </div>
    </div>
  );
}

// ── Hand label with color ─────────────────────────────────────────────────────
const HAND_COLORS = { 'Trail': '#fbbf24', 'Pure Sequence': '#c084fc', 'Sequence': '#60a5fa', 'Color': '#34d399', 'Pair': '#fb7185', 'High Card': '#94a3b8', '–': '#64748b' };

// ── Main Game ────────────────────────────────────────────────────────────────
function newGameState() {
  const deck = shuffle(createDeck());
  return {
    phase: 'player_turn', // player_turn | ai_turn | showdown | result
    playerCards: deck.slice(0, 3),
    ai1Cards: deck.slice(3, 6),
    ai2Cards: deck.slice(6, 9),
    playerFolded: false,
    ai1Folded: false,
    ai2Folded: false,
    ai1Action: null,
    ai2Action: null,
    round: 0,
    pot: 30,
    winner: null,
    showAI: false,
  };
}

export default function TeenPattiGame() {
  const navigate = useNavigate();
  const [game, setGame] = useState(() => newGameState());
  const [claiming, setClaiming] = useState(false);
  const [alreadyClaimed, setAlreadyClaimed] = useState(false);
  const [coinsEarned, setCoinsEarned] = useState(0);
  const resolvedRef = useRef(false);

  const startNewGame = () => {
    resolvedRef.current = false;
    setCoinsEarned(0);
    setGame(newGameState());
  };

  // Player action
  const doPlayerAction = (action) => {
    if (!game || game.phase !== 'player_turn') return;
    setGame(g => {
      const playerFolded = action === 'fold';
      const newPot = g.pot + (action === 'call' ? 10 : action === 'raise' ? 20 : 0);
      const active = [!playerFolded, !g.ai1Folded, !g.ai2Folded].filter(Boolean).length;
      return {
        ...g,
        playerFolded,
        pot: newPot,
        phase: active <= 1 || action === 'fold' ? 'showdown' : 'ai_turn',
      };
    });
  };

  // AI turn
  useEffect(() => {
    if (!game || game.phase !== 'ai_turn') return;
    const timer = setTimeout(() => {
      setGame(g => {
        if (!g || g.phase !== 'ai_turn') return g;
        const ai1Act = !g.ai1Folded ? getAIAction(g.ai1Cards, 'conservative', g.round) : null;
        const ai2Act = !g.ai2Folded ? getAIAction(g.ai2Cards, 'aggressive', g.round) : null;
        const ai1Folded = g.ai1Folded || ai1Act === 'fold';
        const ai2Folded = g.ai2Folded || ai2Act === 'fold';
        let newPot = g.pot;
        if (!g.ai1Folded && ai1Act !== 'fold') newPot += ai1Act === 'raise' ? 20 : 10;
        if (!g.ai2Folded && ai2Act !== 'fold') newPot += ai2Act === 'raise' ? 20 : 10;
        const newRound = g.round + 1;
        const active = [!g.playerFolded, !ai1Folded, !ai2Folded].filter(Boolean).length;
        const goShowdown = active <= 1 || newRound >= 3;
        return {
          ...g,
          ai1Folded,
          ai2Folded,
          ai1Action: ai1Act === 'fold' ? 'fold' : ai1Act,
          ai2Action: ai2Act === 'fold' ? 'fold' : ai2Act,
          pot: newPot,
          round: newRound,
          phase: goShowdown ? 'showdown' : 'player_turn',
        };
      });
    }, 1000);
    return () => clearTimeout(timer);
  }, [game?.phase, game?.round]);

  // Showdown → reveal → result
  useEffect(() => {
    if (!game || game.phase !== 'showdown') return;
    const timer = setTimeout(() => {
      setGame(g => {
        if (!g) return g;
        const active = [];
        if (!g.playerFolded) active.push({ id: 'player', cards: g.playerCards });
        if (!g.ai1Folded) active.push({ id: 'ai1', cards: g.ai1Cards });
        if (!g.ai2Folded) active.push({ id: 'ai2', cards: g.ai2Cards });
        let winner = active[0]?.id || 'player';
        for (let i = 1; i < active.length; i++) {
          if (compareHands(active[i].cards, active.find(p => p.id === winner).cards) > 0)
            winner = active[i].id;
        }
        return { ...g, phase: 'result', winner, showAI: true };
      });
    }, 600);
    return () => clearTimeout(timer);
  }, [game?.phase]);

  // Result - fire confetti & claim coins
  useEffect(() => {
    if (!game || game.phase !== 'result' || resolvedRef.current) return;
    resolvedRef.current = true;
    if (game.winner === 'player') {
      confetti({ particleCount: 140, spread: 90, origin: { y: 0.55 } });
      claimWinCoins();
    }
  }, [game?.phase, game?.winner]);

  const claimWinCoins = async () => {
    if (claiming || alreadyClaimed) return;
    setClaiming(true);
    try {
      const res = await api.post('/v2/earn/teen-patti-win');
      setCoinsEarned(res.data.coins_earned || 40);
      toast.success(`+${res.data.coins_earned} coins earned!`, { description: 'Daily Teen Patti win reward' });
    } catch (e) {
      if (e.response?.status === 400) {
        setAlreadyClaimed(true);
        setCoinsEarned(0);
      }
    } finally { setClaiming(false); }
  };

  if (!game) return null;

  const playerHand = evaluateHand(game.playerCards);
  const ai1Hand = evaluateHand(game.ai1Cards);
  const ai2Hand = evaluateHand(game.ai2Cards);
  const isResult = game.phase === 'result';
  const isPlayerTurn = game.phase === 'player_turn';
  const isAIThinking = game.phase === 'ai_turn';
  const playerWon = isResult && game.winner === 'player';

  const winnerName = isResult
    ? game.winner === 'player' ? 'You' : game.winner === 'ai1' ? 'Rohan (AI)' : 'Priya (AI)'
    : null;

  return (
    <div style={{ minHeight: '100vh', background: '#0F1115', paddingBottom: 120 }}>
      <Navbar />

      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,#a855f7,#6366f1)', padding: '16px 16px 14px' }}>
        <div className="max-w-screen-sm mx-auto">
          <button onClick={() => navigate('/games/teen_patti')} style={{ color: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, marginBottom: 10 }}>
            <ArrowLeft size={14} /> Back to Lobby
          </button>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{ color: '#fff', fontSize: 22, fontWeight: 800 }}>Teen Patti</h1>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>3-card Indian Poker · vs AI</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 10, fontWeight: 700 }}>POT</p>
              <p style={{ color: '#fbbf24', fontSize: 22, fontWeight: 800 }}>{game.pot}</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <div style={{ background: 'rgba(255,255,255,0.15)', borderRadius: 20, padding: '3px 10px' }}>
              <span style={{ color: '#fff', fontSize: 11, fontWeight: 700 }}>Round {Math.min(game.round + 1, 3)}/3</span>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.15)', borderRadius: 20, padding: '3px 10px' }}>
              <span style={{ color: '#fbbf24', fontSize: 11, fontWeight: 700 }}>Win = +40 coins</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-screen-sm mx-auto px-4 mt-4 space-y-3" data-testid="teen-patti-game">

        {/* AI Players */}
        <AIPlayer
          name="Rohan (AI)"
          cards={game.ai1Cards}
          folded={game.ai1Folded}
          action={isAIThinking ? 'thinking' : game.ai1Action}
          revealed={game.showAI}
        />
        <AIPlayer
          name="Priya (AI)"
          cards={game.ai2Cards}
          folded={game.ai2Folded}
          action={isAIThinking ? 'thinking' : game.ai2Action}
          revealed={game.showAI}
        />

        {/* Player hand */}
        <div style={{
          background: playerWon ? 'rgba(198,160,82,0.08)' : game.playerFolded ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.05)',
          border: `1px solid ${playerWon ? 'rgba(198,160,82,0.4)' : game.playerFolded ? 'rgba(239,68,68,0.2)' : isPlayerTurn ? 'rgba(168,85,247,0.5)' : 'rgba(255,255,255,0.1)'}`,
          borderRadius: 16, padding: 16,
          boxShadow: isPlayerTurn ? '0 0 0 2px rgba(168,85,247,0.25)' : 'none',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div>
              <p style={{ color: '#fff', fontSize: 14, fontWeight: 800 }}>You</p>
              {!game.playerFolded && (
                <span style={{ fontSize: 11, fontWeight: 700, color: HAND_COLORS[playerHand.name] || '#8A9096' }}>
                  {playerHand.name}
                </span>
              )}
            </div>
            {game.playerFolded
              ? <Chip label="Folded" color="#ef4444" bg="rgba(239,68,68,0.12)" />
              : isPlayerTurn
                ? <Chip label="Your Turn" color="#a855f7" bg="rgba(168,85,247,0.12)" />
                : null
            }
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            {game.playerCards.map((card, i) => (
              <Card key={i} card={card} glow={isPlayerTurn} data-testid={`player-card-${i}`} />
            ))}
          </div>
        </div>

        {/* Action buttons */}
        {isPlayerTurn && !game.playerFolded && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }} data-testid="action-buttons">
            <button
              onClick={() => doPlayerAction('fold')}
              style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 12, padding: '14px 8px', color: '#ef4444', fontWeight: 800, fontSize: 14, cursor: 'pointer' }}
              data-testid="btn-fold"
            >
              Fold
            </button>
            <button
              onClick={() => doPlayerAction('call')}
              style={{ background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.3)', borderRadius: 12, padding: '14px 8px', color: '#4ade80', fontWeight: 800, fontSize: 14, cursor: 'pointer' }}
              data-testid="btn-call"
            >
              Call +10
            </button>
            <button
              onClick={() => doPlayerAction('raise')}
              style={{ background: 'linear-gradient(135deg,#a855f7,#6366f1)', border: 'none', borderRadius: 12, padding: '14px 8px', color: '#fff', fontWeight: 800, fontSize: 14, cursor: 'pointer' }}
              data-testid="btn-raise"
            >
              Raise +20
            </button>
          </div>
        )}

        {/* AI thinking indicator */}
        {isAIThinking && (
          <div style={{ textAlign: 'center', padding: '10px 0', color: '#8A9096', fontSize: 13 }} data-testid="ai-thinking">
            <span className="animate-pulse">AI is thinking...</span>
          </div>
        )}

        {/* Showdown indicator */}
        {game.phase === 'showdown' && (
          <div style={{ textAlign: 'center', padding: '10px 0', color: '#C6A052', fontSize: 13, fontWeight: 700 }} data-testid="showdown-reveal">
            Revealing cards...
          </div>
        )}

        {/* Result */}
        {isResult && (
          <div style={{
            background: playerWon ? 'rgba(198,160,82,0.1)' : 'rgba(239,68,68,0.07)',
            border: `1px solid ${playerWon ? 'rgba(198,160,82,0.4)' : 'rgba(239,68,68,0.2)'}`,
            borderRadius: 16, padding: 20, textAlign: 'center',
          }} data-testid="game-result">
            <div style={{ fontSize: 44, marginBottom: 8 }}>{playerWon ? '🏆' : '😔'}</div>
            <h2 style={{ color: playerWon ? '#C6A052' : '#ef4444', fontSize: 22, fontWeight: 800, marginBottom: 4 }}>
              {playerWon ? 'You Win!' : `${winnerName} Wins!`}
            </h2>
            {playerWon && coinsEarned > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 8 }}>
                <Coins size={18} style={{ color: '#C6A052' }} />
                <span style={{ color: '#C6A052', fontWeight: 800, fontSize: 18 }}>+{coinsEarned} coins earned!</span>
              </div>
            )}
            {playerWon && alreadyClaimed && (
              <p style={{ color: '#8A9096', fontSize: 12, marginBottom: 8 }}>
                Daily reward already claimed. Come back tomorrow!
              </p>
            )}
            {!playerWon && (
              <div style={{ marginBottom: 8 }}>
                <p style={{ color: '#8A9096', fontSize: 12 }}>
                  Winner's hand: <span style={{ color: HAND_COLORS[evaluateHand(game.winner === 'ai1' ? game.ai1Cards : game.ai2Cards).name], fontWeight: 700 }}>
                    {evaluateHand(game.winner === 'ai1' ? game.ai1Cards : game.ai2Cards).name}
                  </span>
                  {' '}vs your <span style={{ color: HAND_COLORS[playerHand.name], fontWeight: 700 }}>{playerHand.name}</span>
                </p>
              </div>
            )}
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
              <button
                onClick={startNewGame}
                style={{ background: 'linear-gradient(135deg,#a855f7,#6366f1)', border: 'none', borderRadius: 12, padding: '12px 24px', color: '#fff', fontWeight: 800, fontSize: 14, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
                data-testid="play-again-btn"
              >
                <RefreshCw size={14} /> Play Again
              </button>
              <button
                onClick={() => navigate('/games')}
                style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '12px 20px', color: '#BFC3C8', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}
                data-testid="back-to-games-result"
              >
                All Games
              </button>
            </div>
          </div>
        )}

        {/* Hand rankings guide */}
        {!isResult && (
          <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 12, padding: '12px 14px' }}>
            <p style={{ color: '#8A9096', fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 8 }}>HAND RANKINGS (BEST → WORST)</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 8px' }}>
              {[['Trail','#fbbf24'],['Pure Seq','#c084fc'],['Sequence','#60a5fa'],['Color','#34d399'],['Pair','#fb7185'],['High Card','#94a3b8']].map(([name, color]) => (
                <span key={name} style={{ color, fontSize: 10, fontWeight: 700 }}>{name}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
