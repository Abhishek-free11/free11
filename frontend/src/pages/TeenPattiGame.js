import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Coins, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import api from '../utils/api';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

// ── Card constants ──────────────────────────────────────────────────────────
const SUITS = ['spades', 'hearts', 'diamonds', 'clubs'];
const SUIT_SYMBOLS = { spades: '♠', hearts: '♥', diamonds: '♦', clubs: '♣' };
const RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'];
const RANK_VALUES = { '2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14 };
const RED_SUITS = new Set(['hearts','diamonds']);
const HAND_COLORS = { Trail: '#fbbf24', 'Pure Sequence': '#c084fc', Sequence: '#60a5fa', Color: '#34d399', Pair: '#fb7185', 'High Card': '#94a3b8', '–': '#64748b' };
const BOOT_OPTIONS = [10, 20, 50];

function createDeck() {
  return SUITS.flatMap(suit => RANKS.map(rank => ({ suit, rank, id: `${suit}_${rank}` })));
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
  const isSeq = sorted[2] - sorted[0] === 2 && rankSet.size === 3;
  const isAce23 = rankSet.has(14) && rankSet.has(2) && rankSet.has(3) && rankSet.size === 3;
  if (rankSet.size === 1) return { rank: 6, name: 'Trail' };
  if (isFlush && (isSeq || isAce23)) return { rank: 5, name: 'Pure Sequence' };
  if (isSeq || isAce23) return { rank: 4, name: 'Sequence' };
  if (isFlush) return { rank: 3, name: 'Color' };
  if (rankSet.size === 2) return { rank: 2, name: 'Pair' };
  return { rank: 1, name: 'High Card' };
}

function compareHands(c1, c2) {
  const h1 = evaluateHand(c1), h2 = evaluateHand(c2);
  if (h1.rank !== h2.rank) return h1.rank > h2.rank ? 1 : -1;
  const v1 = c1.map(c => RANK_VALUES[c.rank]).sort((a, b) => b - a);
  const v2 = c2.map(c => RANK_VALUES[c.rank]).sort((a, b) => b - a);
  for (let i = 0; i < 3; i++) if (v1[i] !== v2[i]) return v1[i] > v2[i] ? 1 : -1;
  return 0;
}

function getAIAction(cards, isSeen, pot, personality) {
  const hand = evaluateHand(cards);
  if (personality === 'conservative') {
    if (!isSeen && hand.rank >= 3) return 'see';
    if (hand.rank >= 5) return 'raise';
    if (hand.rank >= 3) return 'chaal';
    return Math.random() < 0.4 ? 'pack' : 'chaal';
  }
  // aggressive
  if (!isSeen && hand.rank >= 4) return 'see';
  if (hand.rank >= 4) return 'raise';
  if (hand.rank >= 2) return 'chaal';
  return Math.random() < 0.2 ? 'pack' : 'chaal';
}

// ── PlayingCard component ────────────────────────────────────────────────────
function Card({ card, hidden = false, small = false, glow = false, flip = false }) {
  const w = small ? 44 : 64;
  const h = small ? 62 : 90;
  const r = small ? 8 : 11;
  const fsMain = small ? 13 : 18;
  const fsSuit = small ? 15 : 24;

  return (
    <motion.div
      initial={flip ? { rotateY: 180 } : false}
      animate={flip ? { rotateY: 0 } : false}
      transition={{ duration: 0.4 }}
      style={{ perspective: 600, flexShrink: 0 }}
    >
      {hidden ? (
        <div style={{
          width: w, height: h, borderRadius: r, flexShrink: 0,
          background: 'linear-gradient(135deg,#3730a3,#1e1b4b)',
          border: '1.5px solid rgba(255,255,255,0.18)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
        }}>
          <span style={{ fontSize: small ? 16 : 22, opacity: 0.25 }}>♠</span>
        </div>
      ) : (
        <div style={{
          width: w, height: h, borderRadius: r, flexShrink: 0,
          background: '#fff', border: glow ? '2px solid #C6A052' : '1.5px solid #e2e8f0',
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          justifyContent: 'space-between', padding: 5,
          boxShadow: glow ? '0 0 14px rgba(198,160,82,0.55)' : '0 4px 12px rgba(0,0,0,0.4)',
          transition: 'box-shadow 0.2s',
        }}>
          <span style={{ fontSize: fsMain, fontWeight: 800, color: RED_SUITS.has(card?.suit) ? '#e53e3e' : '#1a202c', lineHeight: 1, alignSelf: 'flex-start' }}>
            {card?.rank}
          </span>
          <span style={{ fontSize: fsSuit, color: RED_SUITS.has(card?.suit) ? '#e53e3e' : '#1a202c' }}>
            {SUIT_SYMBOLS[card?.suit]}
          </span>
          <span style={{ fontSize: fsMain, fontWeight: 800, color: RED_SUITS.has(card?.suit) ? '#e53e3e' : '#1a202c', lineHeight: 1, alignSelf: 'flex-end', transform: 'rotate(180deg)' }}>
            {card?.rank}
          </span>
        </div>
      )}
    </motion.div>
  );
}

// ── AI Player Row ─────────────────────────────────────────────────────────────
function AIPlayerRow({ name, cards, folded, isBlind, action, revealed, pot }) {
  const statusColor = folded ? '#ef4444' : action === 'raise' ? '#C6A052' : action === 'chaal' ? '#4ade80' : action === 'see' ? '#a855f7' : '#8A9096';
  const statusLabel = folded ? 'Packed' : action === 'raise' ? 'Raised!' : action === 'chaal' ? 'Chaal' : action === 'see' ? 'Seen Cards' : action === 'thinking' ? '...' : isBlind ? 'Blind' : 'In';

  return (
    <motion.div
      layout
      style={{
        background: folded ? 'rgba(239,68,68,0.04)' : 'rgba(255,255,255,0.03)',
        border: `1px solid ${folded ? 'rgba(239,68,68,0.12)' : 'rgba(255,255,255,0.07)'}`,
        borderRadius: 14, padding: '10px 12px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        opacity: folded ? 0.55 : 1,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
        <div style={{
          width: 34, height: 34, borderRadius: 10, flexShrink: 0,
          background: folded ? 'rgba(239,68,68,0.12)' : 'linear-gradient(135deg,#a855f7,#6366f1)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ color: '#fff', fontSize: 13, fontWeight: 800 }}>{name[0]}</span>
        </div>
        <div>
          <p style={{ color: folded ? '#8A9096' : '#fff', fontSize: 12, fontWeight: 700 }}>{name}</p>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
            <span style={{
              background: `${statusColor}18`, color: statusColor,
              fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 20,
            }}>
              {statusLabel}
            </span>
            {!folded && !isBlind && (
              <span style={{ background: 'rgba(168,85,247,0.12)', color: '#a855f7', fontSize: 9, fontWeight: 700, padding: '1px 5px', borderRadius: 20 }}>
                SEEN
              </span>
            )}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        {(cards || []).map((card, i) => (
          <Card key={i} card={revealed ? card : null} hidden={!revealed} small />
        ))}
      </div>
    </motion.div>
  );
}

// ── Setup screen ──────────────────────────────────────────────────────────────
function SetupScreen({ onStart }) {
  const [boot, setBoot] = useState(20);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 20, padding: 24, textAlign: 'center',
      }}
      data-testid="setup-screen"
    >
      <div style={{ fontSize: 44, marginBottom: 12 }}>🃏</div>
      <h2 style={{ color: '#fff', fontSize: 22, fontWeight: 900, marginBottom: 4, fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.06em' }}>
        TEEN PATTI
      </h2>
      <p style={{ color: '#8A9096', fontSize: 12, marginBottom: 20 }}>3-card Indian Poker · vs AI · Real rules</p>

      <div style={{ marginBottom: 20 }}>
        <p style={{ color: '#C6A052', fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 10 }}>
          BOOT AMOUNT (coins)
        </p>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
          {BOOT_OPTIONS.map(b => (
            <button
              key={b}
              onClick={() => setBoot(b)}
              data-testid={`boot-option-${b}`}
              style={{
                padding: '10px 20px', borderRadius: 12, fontWeight: 800, fontSize: 15, cursor: 'pointer',
                background: boot === b ? 'linear-gradient(135deg,#C6A052,#E0B84F)' : 'rgba(255,255,255,0.05)',
                border: `1.5px solid ${boot === b ? '#C6A052' : 'rgba(255,255,255,0.1)'}`,
                color: boot === b ? '#0F1115' : '#e2e8f0',
                transition: 'all 0.15s',
              }}
            >
              {b}
            </button>
          ))}
        </div>
      </div>

      <div style={{ background: 'rgba(198,160,82,0.06)', border: '1px solid rgba(198,160,82,0.15)', borderRadius: 12, padding: 12, marginBottom: 20, textAlign: 'left' }}>
        <p style={{ color: '#C6A052', fontSize: 11, fontWeight: 700, marginBottom: 6 }}>HOW TO PLAY</p>
        {[
          ['Boot', `Each player puts ${boot} coins in the pot`],
          ['Blind', 'Play without seeing your cards (cheaper bet)'],
          ['Seen', 'See cards — pay double the chaal'],
          ['Pack', 'Fold at any time to exit the round'],
          ['Sideshow', 'Ask to compare hands with opponent'],
          ['Show', 'Force reveal — best hand wins the pot'],
        ].map(([term, desc]) => (
          <p key={term} style={{ color: '#8A9096', fontSize: 10, marginBottom: 3 }}>
            <span style={{ color: '#e2e8f0', fontWeight: 700 }}>{term}:</span> {desc}
          </p>
        ))}
      </div>

      <div style={{ background: 'rgba(74,222,128,0.07)', border: '1px solid rgba(74,222,128,0.2)', borderRadius: 10, padding: '8px 12px', marginBottom: 16 }}>
        <p style={{ color: '#4ade80', fontSize: 12, fontWeight: 700 }}>
          Win → <span style={{ color: '#C6A052' }}>+40 FREE coins</span> credited instantly!
        </p>
      </div>

      <button
        onClick={() => onStart(boot)}
        data-testid="start-game-btn"
        style={{
          width: '100%', background: 'linear-gradient(135deg,#a855f7,#6366f1)',
          border: 'none', borderRadius: 14, padding: '16px 0', color: '#fff',
          fontWeight: 900, fontSize: 17, cursor: 'pointer',
          fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.08em',
        }}
      >
        DEAL CARDS →
      </button>
    </motion.div>
  );
}

// ── Main Game ─────────────────────────────────────────────────────────────────
function newGameState(bootAmount) {
  const deck = shuffle(createDeck());
  return {
    phase: 'player_turn',
    playerCards: deck.slice(0, 3),
    ai1Cards: deck.slice(3, 6),
    ai2Cards: deck.slice(6, 9),
    playerBlind: true,
    ai1Blind: true,
    ai2Blind: true,
    playerFolded: false,
    ai1Folded: false,
    ai2Folded: false,
    ai1Action: null,
    ai2Action: null,
    round: 0,
    bootAmount,
    currentBet: bootAmount,
    pot: bootAmount * 3,
    winner: null,
    showAI: false,
    sideshowPending: false,
    sideshowResult: null,
    lastMessage: null,
  };
}

export default function TeenPattiGame() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [bootAmount, setBootAmount] = useState(null); // null = setup screen
  const [game, setGame] = useState(null);
  const [claiming, setClaiming] = useState(false);
  const [alreadyClaimed, setAlreadyClaimed] = useState(false);
  const [coinsEarned, setCoinsEarned] = useState(0);
  const [showCards, setShowCards] = useState(false); // has player revealed?
  const resolvedRef = useRef(false);

  const startGame = (boot) => {
    setBootAmount(boot);
    setShowCards(false);
    resolvedRef.current = false;
    setCoinsEarned(0);
    setAlreadyClaimed(false);
    setGame(newGameState(boot));
  };

  const restartGame = () => {
    setBootAmount(null);
    setGame(null);
    setShowCards(false);
    resolvedRef.current = false;
    setCoinsEarned(0);
    setAlreadyClaimed(false);
  };

  // ── Player Actions ────────────────────────────────────────────────────────
  const handleSeeCards = () => {
    setShowCards(true);
    setGame(g => ({ ...g, playerBlind: false, lastMessage: 'You saw your cards — now pay double to chaal' }));
  };

  const handleChaal = () => {
    if (!game || game.phase !== 'player_turn') return;
    const betAmount = game.playerBlind ? game.currentBet : game.currentBet * 2;
    setGame(g => ({
      ...g,
      pot: g.pot + betAmount,
      round: g.round + 1,
      phase: 'ai_turn',
      lastMessage: `You chaal'd ${betAmount} coins`,
    }));
  };

  const handlePack = () => {
    if (!game || game.phase !== 'player_turn') return;
    setGame(g => {
      const active = [false, !g.ai1Folded, !g.ai2Folded].filter(Boolean);
      if (active.length === 1) {
        // Only one AI left — they win
        const winner = !g.ai1Folded ? 'ai1' : 'ai2';
        return { ...g, playerFolded: true, phase: 'result', winner, showAI: true, lastMessage: 'You packed!' };
      }
      return { ...g, playerFolded: true, phase: 'ai_turn', lastMessage: 'You packed — AI continue...' };
    });
  };

  const handleSideshow = () => {
    if (!game || game.phase !== 'player_turn' || game.playerBlind) return;
    // Request sideshow with AI1 if still active
    const target = !game.ai1Folded ? 'ai1' : null;
    if (!target) { toast.info('No eligible opponent for sideshow'); return; }

    // AI1 accepts/rejects (conservative personality: accepts if strong hand)
    const ai1Strength = evaluateHand(game.ai1Cards).rank;
    const accepted = ai1Strength >= 3 ? false : true; // AI rejects if it has strong hand

    if (!accepted) {
      toast.info('Rohan (AI) rejected the sideshow request');
      setGame(g => ({ ...g, lastMessage: 'Sideshow rejected — game continues' }));
      return;
    }

    // Compare: lower hand packs
    const cmp = compareHands(game.playerCards, game.ai1Cards);
    if (cmp >= 0) {
      // AI1 packs
      toast.success('Sideshow: Rohan packed — your hand was stronger!');
      setGame(g => ({
        ...g,
        ai1Folded: true,
        ai1Action: 'pack',
        sideshowResult: 'You won the sideshow!',
        phase: 'player_turn',
        lastMessage: 'Rohan packed after sideshow',
      }));
    } else {
      // Player packs
      toast.warning('Sideshow: Your hand is weaker — you pack');
      setGame(g => {
        const active = [false, !g.ai1Folded, !g.ai2Folded].filter(Boolean);
        const winner = active.length === 1 ? (!g.ai1Folded ? 'ai1' : 'ai2') : null;
        return {
          ...g,
          playerFolded: true,
          sideshowResult: 'Rohan had a stronger hand!',
          phase: winner ? 'result' : 'ai_turn',
          winner: winner || null,
          showAI: winner ? true : false,
          lastMessage: 'You packed after sideshow',
        };
      });
    }
  };

  const handleShow = () => {
    if (!game || game.phase !== 'player_turn') return;
    setGame(g => ({ ...g, phase: 'showdown' }));
  };

  // ── AI Turn Logic ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (!game || game.phase !== 'ai_turn') return;
    const timer = setTimeout(() => {
      setGame(g => {
        if (!g || g.phase !== 'ai_turn') return g;
        let newPot = g.pot;
        let ai1Folded = g.ai1Folded;
        let ai2Folded = g.ai2Folded;
        let ai1Blind = g.ai1Blind;
        let ai2Blind = g.ai2Blind;
        let ai1Action = g.ai1Action;
        let ai2Action = g.ai2Action;

        if (!g.ai1Folded) {
          const act = getAIAction(g.ai1Cards, !g.ai1Blind, g.pot, 'conservative');
          if (act === 'pack') { ai1Folded = true; ai1Action = 'pack'; }
          else if (act === 'see') { ai1Blind = false; ai1Action = 'see'; }
          else if (act === 'raise') { newPot += g.ai1Blind ? g.currentBet : g.currentBet * 2 + g.currentBet; ai1Action = 'raise'; }
          else { newPot += g.ai1Blind ? g.currentBet : g.currentBet * 2; ai1Action = 'chaal'; }
        }
        if (!g.ai2Folded) {
          const act = getAIAction(g.ai2Cards, !g.ai2Blind, g.pot, 'aggressive');
          if (act === 'pack') { ai2Folded = true; ai2Action = 'pack'; }
          else if (act === 'see') { ai2Blind = false; ai2Action = 'see'; }
          else if (act === 'raise') { newPot += g.ai2Blind ? g.currentBet : g.currentBet * 2 + g.currentBet; ai2Action = 'raise'; }
          else { newPot += g.ai2Blind ? g.currentBet : g.currentBet * 2; ai2Action = 'chaal'; }
        }

        const newRound = g.round + 1;
        const activePlayers = [!g.playerFolded, !ai1Folded, !ai2Folded].filter(Boolean).length;
        const goShowdown = activePlayers <= 1 || newRound >= 4;

        // If only one AI and player left, go to player_turn
        return {
          ...g,
          ai1Folded, ai2Folded, ai1Blind, ai2Blind,
          ai1Action, ai2Action,
          pot: newPot,
          round: newRound,
          currentBet: Math.min(g.currentBet + Math.floor(g.currentBet * 0.5), g.bootAmount * 4),
          phase: goShowdown ? 'showdown' : 'player_turn',
          lastMessage: null,
        };
      });
    }, 1200);
    return () => clearTimeout(timer);
  }, [game?.phase, game?.round]);

  // ── Showdown → Result ──────────────────────────────────────────────────────
  useEffect(() => {
    if (!game || game.phase !== 'showdown') return;
    const timer = setTimeout(() => {
      setGame(g => {
        if (!g) return g;
        const active = [];
        if (!g.playerFolded) active.push({ id: 'player', cards: g.playerCards });
        if (!g.ai1Folded) active.push({ id: 'ai1', cards: g.ai1Cards });
        if (!g.ai2Folded) active.push({ id: 'ai2', cards: g.ai2Cards });
        let winner = active[0]?.id || 'ai1';
        for (let i = 1; i < active.length; i++) {
          if (compareHands(active[i].cards, active.find(p => p.id === winner).cards) > 0)
            winner = active[i].id;
        }
        return { ...g, phase: 'result', winner, showAI: true };
      });
    }, 700);
    return () => clearTimeout(timer);
  }, [game?.phase]);

  // ── Result: fire confetti & claim coins ────────────────────────────────────
  useEffect(() => {
    if (!game || game.phase !== 'result' || resolvedRef.current) return;
    resolvedRef.current = true;
    if (game.winner === 'player') {
      confetti({ particleCount: 160, spread: 100, origin: { y: 0.55 }, colors: ['#C6A052', '#E0B84F', '#fff', '#a855f7'] });
      claimWinCoins();
    }
  }, [game?.phase, game?.winner]);

  const claimWinCoins = async () => {
    if (claiming || alreadyClaimed) return;
    setClaiming(true);
    try {
      const res = await api.post('/v2/earn/teen-patti-win');
      const earned = res.data.coins_earned || 40;
      setCoinsEarned(earned);
      if (res.data.new_balance !== undefined) updateUser({ coins_balance: res.data.new_balance });
      toast.success(`+${earned} coins earned!`, { description: 'Teen Patti daily win reward' });
    } catch (e) {
      if (e.response?.status === 400) {
        setAlreadyClaimed(true);
        setCoinsEarned(0);
        toast.info('Daily reward already claimed — come back tomorrow!');
      }
    } finally { setClaiming(false); }
  };

  // ── Setup screen ──────────────────────────────────────────────────────────
  if (!bootAmount || !game) {
    return (
      <div style={{ minHeight: '100vh', background: '#0F1115', paddingBottom: 120 }}>
        <Navbar />
        <div style={{ background: 'linear-gradient(135deg,#a855f7,#6366f1)', padding: '16px 16px 14px' }}>
          <div className="max-w-screen-sm mx-auto">
            <button onClick={() => navigate('/games/teen_patti')} style={{ color: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, marginBottom: 4 }}>
              <ArrowLeft size={14} /> Back
            </button>
          </div>
        </div>
        <div className="max-w-screen-sm mx-auto px-4 mt-4">
          <SetupScreen onStart={startGame} />
        </div>
      </div>
    );
  }

  const playerHand = evaluateHand(game.playerCards);
  const ai1Hand = evaluateHand(game.ai1Cards);
  const ai2Hand = evaluateHand(game.ai2Cards);
  const isResult = game.phase === 'result';
  const isPlayerTurn = game.phase === 'player_turn' && !game.playerFolded;
  const isAIThinking = game.phase === 'ai_turn';
  const isShowdown = game.phase === 'showdown';
  const playerWon = isResult && game.winner === 'player';
  const activePlayers = [!game.playerFolded, !game.ai1Folded, !game.ai2Folded].filter(Boolean).length;

  const winnerLabel = isResult
    ? game.winner === 'player' ? 'You' : game.winner === 'ai1' ? 'Rohan (AI)' : 'Priya (AI)'
    : null;
  const winnerCards = isResult
    ? game.winner === 'player' ? game.playerCards : game.winner === 'ai1' ? game.ai1Cards : game.ai2Cards
    : null;

  return (
    <div style={{ minHeight: '100vh', background: '#0F1115', paddingBottom: 120 }}>
      <Navbar />

      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,#a855f7,#6366f1)', padding: '14px 16px 12px' }}>
        <div className="max-w-screen-sm mx-auto">
          <button onClick={() => navigate('/games/teen_patti')} style={{ color: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, marginBottom: 8 }}>
            <ArrowLeft size={13} /> Back to Lobby
          </button>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{ color: '#fff', fontSize: 20, fontWeight: 900, fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.06em' }}>
                TEEN PATTI
              </h1>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 11 }}>Boot: {game.bootAmount} · Real rules · vs AI</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 9, fontWeight: 700 }}>POT</p>
              <motion.p
                key={game.pot}
                initial={{ scale: 1.2, color: '#E0B84F' }}
                animate={{ scale: 1, color: '#fbbf24' }}
                style={{ fontSize: 24, fontWeight: 900, lineHeight: 1 }}
              >
                {game.pot}
              </motion.p>
              <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 9 }}>Round {Math.min(game.round + 1, 5)}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-screen-sm mx-auto px-4 mt-4 space-y-3" data-testid="teen-patti-game">

        {/* AI Players */}
        <AIPlayerRow
          name="Rohan (AI)"
          cards={game.ai1Cards}
          folded={game.ai1Folded}
          isBlind={game.ai1Blind}
          action={isAIThinking ? 'thinking' : game.ai1Action}
          revealed={game.showAI}
        />
        <AIPlayerRow
          name="Priya (AI)"
          cards={game.ai2Cards}
          folded={game.ai2Folded}
          isBlind={game.ai2Blind}
          action={isAIThinking ? 'thinking' : game.ai2Action}
          revealed={game.showAI}
        />

        {/* Player hand */}
        <div style={{
          background: playerWon ? 'rgba(198,160,82,0.08)' : game.playerFolded ? 'rgba(239,68,68,0.04)' : 'rgba(255,255,255,0.04)',
          border: `1px solid ${playerWon ? 'rgba(198,160,82,0.4)' : game.playerFolded ? 'rgba(239,68,68,0.18)' : isPlayerTurn ? 'rgba(168,85,247,0.45)' : 'rgba(255,255,255,0.08)'}`,
          borderRadius: 16, padding: 14,
          boxShadow: isPlayerTurn && !game.playerFolded ? '0 0 0 2px rgba(168,85,247,0.18)' : 'none',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <div>
              <p style={{ color: '#fff', fontSize: 13, fontWeight: 800 }}>You</p>
              <div style={{ display: 'flex', gap: 4, marginTop: 2 }}>
                {!game.playerFolded && (
                  <span style={{ background: game.playerBlind ? 'rgba(100,116,139,0.15)' : 'rgba(168,85,247,0.15)', color: game.playerBlind ? '#94a3b8' : '#a855f7', fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 20, border: `1px solid ${game.playerBlind ? 'rgba(100,116,139,0.2)' : 'rgba(168,85,247,0.25)'}` }}>
                    {game.playerBlind ? 'BLIND' : 'SEEN'}
                  </span>
                )}
                {!game.playerFolded && !game.playerBlind && showCards && (
                  <span style={{ color: HAND_COLORS[playerHand.name], fontSize: 10, fontWeight: 700 }}>
                    {playerHand.name}
                  </span>
                )}
              </div>
            </div>
            {game.playerFolded
              ? <span style={{ background: 'rgba(239,68,68,0.12)', color: '#ef4444', fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 20 }}>PACKED</span>
              : isPlayerTurn
              ? <span style={{ background: 'rgba(168,85,247,0.12)', color: '#a855f7', fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 20 }}>YOUR TURN</span>
              : null
            }
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            {game.playerCards.map((card, i) => (
              <Card
                key={i}
                card={card}
                hidden={!showCards}
                glow={isPlayerTurn}
                flip={showCards && i === game.playerCards.length - 1}
                data-testid={`player-card-${i}`}
              />
            ))}
          </div>
        </div>

        {/* ── Action buttons ── */}
        <AnimatePresence>
          {isPlayerTurn && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
            >
              {/* Blind mode actions */}
              {game.playerBlind ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }} data-testid="blind-action-buttons">
                  <button
                    onClick={handleSeeCards}
                    style={{ background: 'rgba(168,85,247,0.12)', border: '1px solid rgba(168,85,247,0.3)', borderRadius: 12, padding: '12px 6px', color: '#a855f7', fontWeight: 800, fontSize: 12, cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}
                    data-testid="btn-see-cards"
                  >
                    <Eye size={14} /> See Cards
                  </button>
                  <button
                    onClick={handleChaal}
                    style={{ background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.3)', borderRadius: 12, padding: '12px 6px', color: '#4ade80', fontWeight: 800, fontSize: 12, cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}
                    data-testid="btn-blind-chaal"
                  >
                    <span>Blind Chaal</span>
                    <span style={{ fontSize: 10, opacity: 0.8 }}>+{game.currentBet}</span>
                  </button>
                  <button
                    onClick={handlePack}
                    style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 12, padding: '12px 6px', color: '#ef4444', fontWeight: 800, fontSize: 12, cursor: 'pointer' }}
                    data-testid="btn-pack"
                  >
                    Pack
                  </button>
                </div>
              ) : (
                /* Seen mode actions */
                <div style={{ display: 'grid', gridTemplateColumns: activePlayers > 2 ? '1fr 1fr 1fr 1fr' : '1fr 1fr 1fr', gap: 8 }} data-testid="seen-action-buttons">
                  <button
                    onClick={handleChaal}
                    style={{ background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.3)', borderRadius: 12, padding: '12px 6px', color: '#4ade80', fontWeight: 800, fontSize: 12, cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}
                    data-testid="btn-chaal"
                  >
                    <span>Chaal</span>
                    <span style={{ fontSize: 10, opacity: 0.8 }}>+{game.currentBet * 2}</span>
                  </button>
                  {activePlayers > 2 && (
                    <button
                      onClick={handleSideshow}
                      style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', borderRadius: 12, padding: '12px 6px', color: '#60a5fa', fontWeight: 800, fontSize: 12, cursor: 'pointer' }}
                      data-testid="btn-sideshow"
                    >
                      Sideshow
                    </button>
                  )}
                  {activePlayers <= 2 && (
                    <button
                      onClick={handleShow}
                      style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)', border: 'none', borderRadius: 12, padding: '12px 6px', color: '#0F1115', fontWeight: 900, fontSize: 12, cursor: 'pointer' }}
                      data-testid="btn-show"
                    >
                      Show
                    </button>
                  )}
                  <button
                    onClick={handlePack}
                    style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: 12, padding: '12px 6px', color: '#ef4444', fontWeight: 800, fontSize: 12, cursor: 'pointer' }}
                    data-testid="btn-pack"
                  >
                    Pack
                  </button>
                </div>
              )}

              {/* Bet info line */}
              <p style={{ color: '#8A9096', fontSize: 10, textAlign: 'center', marginTop: 6 }}>
                {game.playerBlind
                  ? `Blind chaal: ${game.currentBet} · See to play: ${game.currentBet * 2} per chaal`
                  : `Seen chaal: ${game.currentBet * 2} coins · Pot: ${game.pot}`}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Status messages */}
        <AnimatePresence>
          {isAIThinking && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{ textAlign: 'center', color: '#8A9096', fontSize: 12, padding: '6px 0' }}
              data-testid="ai-thinking">
              <span className="animate-pulse">AIs are thinking...</span>
            </motion.p>
          )}
          {isShowdown && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              style={{ textAlign: 'center', color: '#C6A052', fontSize: 13, fontWeight: 700, padding: '6px 0' }}
              data-testid="showdown-reveal">
              Revealing cards...
            </motion.p>
          )}
          {game.lastMessage && !isResult && !isAIThinking && (
            <motion.p initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              key={game.lastMessage}
              style={{ textAlign: 'center', color: '#8A9096', fontSize: 11, padding: '4px 0' }}>
              {game.lastMessage}
            </motion.p>
          )}
        </AnimatePresence>

        {/* ── Result ── */}
        <AnimatePresence>
          {isResult && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 18 }}
              style={{
                background: playerWon ? 'rgba(198,160,82,0.08)' : 'rgba(239,68,68,0.05)',
                border: `1px solid ${playerWon ? 'rgba(198,160,82,0.4)' : 'rgba(239,68,68,0.2)'}`,
                borderRadius: 18, padding: 20, textAlign: 'center',
              }}
              data-testid="game-result"
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.15, type: 'spring', stiffness: 260, damping: 14 }}
                style={{ fontSize: 50, marginBottom: 8 }}
              >
                {playerWon ? '🏆' : '😔'}
              </motion.div>

              <h2 style={{ color: playerWon ? '#C6A052' : '#ef4444', fontSize: 24, fontWeight: 900, marginBottom: 4, fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.06em' }}>
                {playerWon ? 'YOU WIN!' : `${winnerLabel} WINS!`}
              </h2>

              {/* Pot animation */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 10 }}
              >
                <Coins size={16} style={{ color: '#C6A052' }} />
                <span style={{ color: '#C6A052', fontWeight: 800, fontSize: 15 }}>
                  {playerWon ? `+${coinsEarned > 0 ? coinsEarned : 40} coins` : `Pot: ${game.pot} coins`}
                </span>
              </motion.div>

              {/* Winner hand */}
              {winnerCards && (
                <div style={{ marginBottom: 12 }}>
                  <p style={{ color: '#8A9096', fontSize: 11, marginBottom: 8 }}>
                    Winning hand: <span style={{ color: HAND_COLORS[evaluateHand(winnerCards).name], fontWeight: 700 }}>
                      {evaluateHand(winnerCards).name}
                    </span>
                    {!playerWon && (
                      <> · Your hand: <span style={{ color: HAND_COLORS[playerHand.name], fontWeight: 700 }}>{playerHand.name}</span></>
                    )}
                  </p>
                  <div style={{ display: 'flex', gap: 6, justifyContent: 'center' }}>
                    {winnerCards.map((card, i) => (
                      <Card key={i} card={card} glow={playerWon} />
                    ))}
                  </div>
                </div>
              )}

              {alreadyClaimed && (
                <p style={{ color: '#8A9096', fontSize: 11, marginBottom: 10 }}>
                  Daily reward already claimed — come back tomorrow!
                </p>
              )}

              <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
                <button
                  onClick={restartGame}
                  style={{ background: 'linear-gradient(135deg,#a855f7,#6366f1)', border: 'none', borderRadius: 12, padding: '12px 22px', color: '#fff', fontWeight: 900, fontSize: 14, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
                  data-testid="play-again-btn"
                >
                  <RefreshCw size={14} /> Play Again
                </button>
                <button
                  onClick={() => navigate('/games')}
                  style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '12px 18px', color: '#BFC3C8', fontWeight: 700, fontSize: 14, cursor: 'pointer' }}
                  data-testid="back-to-games-result"
                >
                  All Games
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Hand rankings guide */}
        {!isResult && (
          <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 12, padding: '10px 12px' }}>
            <p style={{ color: '#8A9096', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 6 }}>
              HAND RANKINGS (BEST → WORST)
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px 10px' }}>
              {[['Trail', '#fbbf24'], ['Pure Seq', '#c084fc'], ['Sequence', '#60a5fa'], ['Color', '#34d399'], ['Pair', '#fb7185'], ['High Card', '#94a3b8']].map(([name, color]) => (
                <span key={name} style={{ color, fontSize: 10, fontWeight: 700 }}>{name}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
