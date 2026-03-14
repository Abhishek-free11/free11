import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Coins } from 'lucide-react';
import { toast } from 'sonner';
import confetti from 'canvas-confetti';
import api from '../utils/api';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

// ── Constants ──────────────────────────────────────────────────────────────
const SUITS = ['spades', 'hearts', 'diamonds', 'clubs'];
const SUIT_SYMBOLS = { spades: '♠', hearts: '♥', diamonds: '♦', clubs: '♣' };
const RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'];
const RANK_VALUES = { '2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14 };
const RED_SUITS = new Set(['hearts','diamonds']);

const HAND_RANK_NAMES = {
  9: 'Royal Flush', 8: 'Straight Flush', 7: 'Four of a Kind',
  6: 'Full House', 5: 'Flush', 4: 'Straight',
  3: 'Three of a Kind', 2: 'Two Pair', 1: 'One Pair', 0: 'High Card'
};
const HAND_COLORS = {
  9: '#fbbf24', 8: '#fbbf24', 7: '#c084fc', 6: '#a855f7',
  5: '#34d399', 4: '#60a5fa', 3: '#fb923c', 2: '#f87171', 1: '#fb7185', 0: '#94a3b8'
};

function createDeck() {
  return SUITS.flatMap(suit => RANKS.map(rank => ({ suit, rank, id: `${suit}_${rank}` })));
}
function shuffle(arr) {
  const d = [...arr]; for (let i = d.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [d[i], d[j]] = [d[j], d[i]]; } return d;
}

// ── Hand Evaluation ─────────────────────────────────────────────────────────
function getCombinations(arr, k) {
  if (k === 0) return [[]];
  if (arr.length < k) return [];
  const [first, ...rest] = arr;
  return [...getCombinations(rest, k - 1).map(c => [first, ...c]), ...getCombinations(rest, k)];
}

function evalHand5(cards) {
  const rv = v => RANK_VALUES[v];
  const ranks = cards.map(c => rv(c.rank)).sort((a, b) => b - a);
  const suits = cards.map(c => c.suit);
  const isFlush = suits.every(s => s === suits[0]);
  const sorted = [...ranks].sort((a, b) => a - b);
  const isWheel = JSON.stringify(sorted) === JSON.stringify([2, 3, 4, 5, 14]);
  const isStraight = (new Set(ranks).size === 5 && sorted[4] - sorted[0] === 4) || isWheel;
  const counts = {};
  for (const r of ranks) counts[r] = (counts[r] || 0) + 1;
  const cv = Object.values(counts).sort((a, b) => b - a);
  const topRanks = Object.entries(counts).sort((a, b) => b[1] - a[1] || b[0] - a[0]).map(e => parseInt(e[0]));

  let hr, tb;
  const highCard = Math.max(...ranks);
  if (isFlush && isStraight && highCard === 14 && !isWheel) { hr = 9; tb = [14]; }
  else if (isFlush && isStraight) { hr = 8; tb = [isWheel ? 5 : highCard]; }
  else if (cv[0] === 4) { hr = 7; tb = topRanks; }
  else if (cv[0] === 3 && cv[1] === 2) { hr = 6; tb = topRanks; }
  else if (isFlush) { hr = 5; tb = ranks; }
  else if (isStraight) { hr = 4; tb = [isWheel ? 5 : highCard]; }
  else if (cv[0] === 3) { hr = 3; tb = topRanks; }
  else if (cv[0] === 2 && cv[1] === 2) { hr = 2; tb = topRanks; }
  else if (cv[0] === 2) { hr = 1; tb = topRanks; }
  else { hr = 0; tb = ranks; }
  return { handRank: hr, tiebreakers: tb, cards };
}

function getBestHand(cards) {
  const combos = getCombinations(cards, 5);
  let best = null;
  for (const combo of combos) {
    const ev = evalHand5(combo);
    if (!best || ev.handRank > best.handRank || (ev.handRank === best.handRank && ev.tiebreakers.join() > best.tiebreakers.join())) best = ev;
  }
  return best || { handRank: 0, tiebreakers: [], cards: [] };
}

// ── AI Logic ────────────────────────────────────────────────────────────────
function getAIAction(holeCards, communityCards, pot, callAmount, personality) {
  const allCards = [...holeCards, ...communityCards];
  const hand = allCards.length >= 5 ? getBestHand(allCards) : evalHand5(communityCards.length >= 3 ? [...holeCards, ...communityCards.slice(0, 3)] : [...holeCards, { suit: 'spades', rank: '2', id: 'x1' }, { suit: 'hearts', rank: '3', id: 'x2' }, { suit: 'diamonds', rank: '4', id: 'x3' }]);
  const hr = hand.handRank;
  if (personality === 'tight') {
    if (hr >= 3) return 'raise';
    if (hr >= 1) return 'call';
    return Math.random() < 0.6 ? 'fold' : 'call';
  }
  // loose
  if (hr >= 2) return 'raise';
  if (hr >= 0) return Math.random() < 0.25 ? 'fold' : 'call';
  return 'call';
}

// ── Card Component ──────────────────────────────────────────────────────────
function Card({ card, hidden, small, highlight }) {
  const w = small ? 36 : 56, h = small ? 50 : 80, r = small ? 6 : 10;
  const fs = small ? 11 : 16, fsSuit = small ? 14 : 24;
  if (hidden) {
    return <div style={{ width: w, height: h, borderRadius: r, background: 'linear-gradient(135deg,#3730a3,#1e1b4b)', border: '1.5px solid rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 2px 8px rgba(0,0,0,0.4)' }}><span style={{ fontSize: small ? 14 : 20, opacity: 0.3 }}>♠</span></div>;
  }
  const isRed = card && RED_SUITS.has(card.suit);
  const clr = isRed ? '#e53e3e' : '#1a202c';
  return (
    <div style={{ width: w, height: h, borderRadius: r, background: '#fff', flexShrink: 0, border: highlight ? '2px solid #C6A052' : '1.5px solid #e2e8f0', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'space-between', padding: 5, boxShadow: highlight ? '0 0 12px rgba(198,160,82,0.5)' : '0 2px 8px rgba(0,0,0,0.3)' }}>
      <span style={{ fontSize: fs, fontWeight: 800, color: clr, lineHeight: 1, alignSelf: 'flex-start' }}>{card?.rank}</span>
      <span style={{ fontSize: fsSuit, color: clr }}>{SUIT_SYMBOLS[card?.suit]}</span>
      <span style={{ fontSize: fs, fontWeight: 800, color: clr, lineHeight: 1, alignSelf: 'flex-end', transform: 'rotate(180deg)' }}>{card?.rank}</span>
    </div>
  );
}

// ── Poker Player Row ─────────────────────────────────────────────────────────
function PokerPlayer({ name, holeCards, folded, status, revealed, bestHand, isCurrentTurn, isMe }) {
  return (
    <div style={{
      background: isMe ? (folded ? 'rgba(239,68,68,0.05)' : 'rgba(34,197,94,0.05)') : (folded ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.04)'),
      border: `1px solid ${isCurrentTurn ? 'rgba(34,197,94,0.5)' : folded ? 'rgba(239,68,68,0.15)' : 'rgba(255,255,255,0.08)'}`,
      borderRadius: 14, padding: '12px 14px', opacity: folded ? 0.6 : 1,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 34, height: 34, borderRadius: 10, background: isMe ? 'linear-gradient(135deg,#C6A052,#E0B84F)' : 'linear-gradient(135deg,#22c55e,#10b981)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ color: '#0F1115', fontSize: 13, fontWeight: 800 }}>{name[0]}</span>
          </div>
          <div>
            <p style={{ color: '#fff', fontSize: 13, fontWeight: 700 }}>{name}</p>
            <p style={{ color: folded ? '#ef4444' : isCurrentTurn ? '#4ade80' : '#8A9096', fontSize: 10, fontWeight: 700 }}>
              {folded ? 'Folded' : status === 'thinking' ? '...' : status || 'In'}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 5 }}>
          {holeCards.map((c, i) => <Card key={i} card={c} hidden={!revealed && !isMe} small={!isMe} />)}
        </div>
      </div>
      {revealed && bestHand && !folded && (
        <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: HAND_COLORS[bestHand.handRank] }}>{HAND_RANK_NAMES[bestHand.handRank]}</span>
        </div>
      )}
    </div>
  );
}

// ── Game Phases ──────────────────────────────────────────────────────────────
const PHASES = ['preflop', 'flop', 'turn', 'river', 'showdown', 'result'];
const COMMUNITY_COUNT = { preflop: 0, flop: 3, turn: 4, river: 5, showdown: 5, result: 5 };

function newGame() {
  const deck = shuffle(createDeck());
  return {
    deck: deck.slice(9),
    playerHole: [deck[0], deck[1]],
    ai1Hole: [deck[2], deck[3]],
    ai2Hole: [deck[4], deck[5]],
    communityCards: deck.slice(6, 11), // pre-dealt, revealed progressively
    phase: 'preflop',
    pot: 30, currentBet: 10,
    playerFolded: false, ai1Folded: false, ai2Folded: false,
    ai1Status: null, ai2Status: null,
    winner: null, winnerHand: null,
    playerBestHand: null, ai1BestHand: null, ai2BestHand: null,
  };
}

export default function PokerGame() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [game, setGame] = useState(() => newGame());
  const [claiming, setClaiming] = useState(false);
  const [alreadyClaimed, setAlreadyClaimed] = useState(false);
  const [coinsEarned, setCoinsEarned] = useState(0);
  const resolvedRef = useRef(false);

  const visibleCommunity = game.communityCards.slice(0, COMMUNITY_COUNT[game.phase] || 0);
  const isPlayerTurn = ['preflop', 'flop', 'turn', 'river'].includes(game.phase) && !game.playerFolded;
  const isAITurn = game.phase === 'ai_thinking';

  // Player action
  const handlePlayerAction = (action) => {
    setGame(g => {
      const pFolded = action === 'fold';
      const newPot = g.pot + (action === 'call' ? 10 : action === 'raise' ? 20 : 0);
      const active = [!pFolded, !g.ai1Folded, !g.ai2Folded].filter(Boolean).length;
      if (active <= 1 || action === 'fold') {
        return { ...g, playerFolded: pFolded, pot: newPot, phase: 'showdown', lastPlayerPhase: g.phase };
      }
      return { ...g, playerFolded: pFolded, pot: newPot, phase: 'ai_thinking', lastPlayerPhase: g.phase };
    });
  };

  function nextPhase(p) {
    const idx = PHASES.indexOf(p);
    return PHASES[Math.min(idx + 1, 4)];
  }

  // AI thinking
  useEffect(() => {
    if (game.phase !== 'ai_thinking') return;
    const timer = setTimeout(() => {
      setGame(g => {
        if (g.phase !== 'ai_thinking') return g;
        const comm = g.communityCards.slice(0, COMMUNITY_COUNT[nextPhase(g.lastPlayerPhase || 'preflop')]);
        const ai1Act = !g.ai1Folded ? getAIAction(g.ai1Hole, comm, g.pot, 10, 'tight') : 'fold';
        const ai2Act = !g.ai2Folded ? getAIAction(g.ai2Hole, comm, g.pot, 10, 'loose') : 'fold';
        const ai1Folded = g.ai1Folded || ai1Act === 'fold';
        const ai2Folded = g.ai2Folded || ai2Act === 'fold';
        let newPot = g.pot;
        if (!g.ai1Folded && ai1Act !== 'fold') newPot += ai1Act === 'raise' ? 20 : 10;
        if (!g.ai2Folded && ai2Act !== 'fold') newPot += ai2Act === 'raise' ? 20 : 10;
        const active = [!g.playerFolded, !ai1Folded, !ai2Folded].filter(Boolean).length;
        const currentPhaseIdx = PHASES.indexOf(g.lastPlayerPhase || 'preflop');
        const next = active <= 1 ? 'showdown' : PHASES[Math.min(currentPhaseIdx + 1, 4)];
        return {
          ...g, ai1Folded, ai2Folded,
          ai1Status: ai1Act === 'fold' ? 'Folded' : ai1Act === 'raise' ? 'Raised' : 'Called',
          ai2Status: ai2Act === 'fold' ? 'Folded' : ai2Act === 'raise' ? 'Raised' : 'Called',
          pot: newPot, phase: next,
        };
      });
    }, 900);
    return () => clearTimeout(timer);
  }, [game.phase]);

  // Showdown → compute hands → result
  useEffect(() => {
    if (game.phase !== 'showdown') return;
    const timer = setTimeout(() => {
      setGame(g => {
        const comm = g.communityCards.slice(0, 5);
        const pHand = !g.playerFolded && comm.length >= 3 ? getBestHand([...g.playerHole, ...comm]) : null;
        const a1Hand = !g.ai1Folded && comm.length >= 3 ? getBestHand([...g.ai1Hole, ...comm]) : null;
        const a2Hand = !g.ai2Folded && comm.length >= 3 ? getBestHand([...g.ai2Hole, ...comm]) : null;
        const hands = [
          { id: 'player', hand: pHand },
          { id: 'ai1', hand: a1Hand },
          { id: 'ai2', hand: a2Hand },
        ].filter(x => x.hand);
        let winner = hands[0]?.id || 'player';
        for (let i = 1; i < hands.length; i++) {
          const curr = hands[i];
          const best = hands.find(h => h.id === winner);
          if (!best || curr.hand.handRank > best.hand.handRank ||
              (curr.hand.handRank === best.hand.handRank && curr.hand.tiebreakers.join(',') > best.hand.tiebreakers.join(','))) {
            winner = curr.id;
          }
        }
        return { ...g, phase: 'result', winner, playerBestHand: pHand, ai1BestHand: a1Hand, ai2BestHand: a2Hand };
      });
    }, 500);
    return () => clearTimeout(timer);
  }, [game.phase]);

  // Result → confetti + coins
  useEffect(() => {
    if (game.phase !== 'result' || resolvedRef.current) return;
    resolvedRef.current = true;
    if (game.winner === 'player') {
      confetti({ particleCount: 150, spread: 90, origin: { y: 0.55 } });
      claimCoins();
    }
  }, [game.phase, game.winner]);

  const claimCoins = async () => {
    if (claiming || alreadyClaimed) return;
    setClaiming(true);
    try {
      const res = await api.post('/v2/earn/poker-win');
      setCoinsEarned(res.data.coins_earned || 60);
      if (res.data.new_balance !== undefined) updateUser({ coins_balance: res.data.new_balance });
      toast.success(`+${res.data.coins_earned} coins earned!`);
    } catch (e) {
      if (e.response?.status === 400) setAlreadyClaimed(true);
    } finally { setClaiming(false); }
  };

  const startNew = () => { resolvedRef.current = false; setCoinsEarned(0); setGame(newGame()); };

  const phaseLabel = { preflop: 'Pre-Flop', flop: 'Flop', turn: 'Turn', river: 'River', showdown: 'Showdown', result: 'Result', ai_thinking: 'AI Thinking...' };
  const isResult = game.phase === 'result';
  const playerWon = isResult && game.winner === 'player';
  const winnerName = isResult ? (game.winner === 'player' ? 'You' : game.winner === 'ai1' ? 'Vikram (AI)' : 'Neha (AI)') : null;

  return (
    <div style={{ minHeight: '100vh', background: '#0F1115', paddingBottom: 120 }}>
      <Navbar />
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,#22c55e,#10b981)', padding: '16px 16px 14px' }}>
        <div className="max-w-screen-sm mx-auto">
          <button onClick={() => navigate('/games/poker')} style={{ color: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, marginBottom: 10 }}>
            <ArrowLeft size={14} /> Back to Lobby
          </button>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{ color: '#fff', fontSize: 22, fontWeight: 800 }}>Poker</h1>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>Texas Hold'em · vs AI</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 10, fontWeight: 700 }}>POT</p>
              <p style={{ color: '#fbbf24', fontSize: 22, fontWeight: 800 }}>{game.pot}</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            {PHASES.slice(0, 4).map(p => (
              <div key={p} style={{ background: game.phase === p || (game.phase === 'ai_thinking' && game.lastPlayerPhase === p) ? 'rgba(255,255,255,0.3)' : PHASES.indexOf(p) < PHASES.indexOf(game.phase === 'ai_thinking' ? game.lastPlayerPhase || 'preflop' : game.phase) ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.08)', borderRadius: 20, padding: '3px 10px' }}>
                <span style={{ color: '#fff', fontSize: 10, fontWeight: 700 }}>{phaseLabel[p]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-screen-sm mx-auto px-3 mt-4 space-y-3" data-testid="poker-game">
        {/* AI Players */}
        <PokerPlayer name="Vikram (AI)" holeCards={game.ai1Hole} folded={game.ai1Folded} status={game.phase === 'ai_thinking' ? 'Thinking...' : game.ai1Status} revealed={isResult && !game.ai1Folded} bestHand={game.ai1BestHand} />
        <PokerPlayer name="Neha (AI)" holeCards={game.ai2Hole} folded={game.ai2Folded} status={game.phase === 'ai_thinking' ? 'Thinking...' : game.ai2Status} revealed={isResult && !game.ai2Folded} bestHand={game.ai2BestHand} />

        {/* Community cards */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: 14 }}>
          <p style={{ color: '#8A9096', fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 10 }}>
            COMMUNITY CARDS · {phaseLabel[game.phase] || phaseLabel['preflop']}
          </p>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            {[0, 1, 2, 3, 4].map(i => (
              <Card key={i} card={i < visibleCommunity.length ? visibleCommunity[i] : null} hidden={i >= visibleCommunity.length} />
            ))}
          </div>
          {visibleCommunity.length === 0 && (
            <p style={{ color: '#8A9096', fontSize: 11, textAlign: 'center', marginTop: 6 }}>Cards reveal after each round</p>
          )}
        </div>

        {/* Player hand */}
        <PokerPlayer
          name="You"
          holeCards={game.playerHole}
          folded={game.playerFolded}
          status={isPlayerTurn ? 'Your Turn' : game.playerFolded ? 'Folded' : 'Waiting'}
          revealed={true}
          bestHand={isResult ? game.playerBestHand : null}
          isCurrentTurn={isPlayerTurn}
          isMe={true}
        />

        {/* Player actions */}
        {isPlayerTurn && !game.playerFolded && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }} data-testid="poker-actions">
            <button onClick={() => handlePlayerAction('fold')} style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 12, padding: '14px 8px', color: '#ef4444', fontWeight: 800, fontSize: 14, cursor: 'pointer' }} data-testid="poker-fold">Fold</button>
            <button onClick={() => handlePlayerAction('call')} style={{ background: 'rgba(74,222,128,0.1)', border: '1px solid rgba(74,222,128,0.3)', borderRadius: 12, padding: '14px 8px', color: '#4ade80', fontWeight: 800, fontSize: 14, cursor: 'pointer' }} data-testid="poker-call">Call +10</button>
            <button onClick={() => handlePlayerAction('raise')} style={{ background: 'linear-gradient(135deg,#22c55e,#10b981)', border: 'none', borderRadius: 12, padding: '14px 8px', color: '#fff', fontWeight: 800, fontSize: 14, cursor: 'pointer' }} data-testid="poker-raise">Raise +20</button>
          </div>
        )}

        {game.phase === 'ai_thinking' && (
          <div style={{ textAlign: 'center', padding: '8px 0', color: '#8A9096', fontSize: 13 }} className="animate-pulse" data-testid="poker-ai-thinking">AI is deciding...</div>
        )}

        {/* Hand rankings reference */}
        {!isResult && (
          <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 12, padding: '10px 12px' }}>
            <p style={{ color: '#8A9096', fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 6 }}>HAND RANKINGS</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px 10px' }}>
              {[9,8,7,6,5,4,3,2,1,0].map(r => (
                <span key={r} style={{ color: HAND_COLORS[r], fontSize: 10, fontWeight: 700 }}>{HAND_RANK_NAMES[r]}</span>
              ))}
            </div>
          </div>
        )}

        {/* Result */}
        {isResult && (
          <div style={{
            background: playerWon ? 'rgba(198,160,82,0.1)' : 'rgba(239,68,68,0.07)',
            border: `1px solid ${playerWon ? 'rgba(198,160,82,0.4)' : 'rgba(239,68,68,0.2)'}`,
            borderRadius: 16, padding: 20, textAlign: 'center',
          }} data-testid="poker-result">
            <div style={{ fontSize: 44, marginBottom: 8 }}>{playerWon ? '🏆' : '😔'}</div>
            <h2 style={{ color: playerWon ? '#C6A052' : '#ef4444', fontSize: 22, fontWeight: 800, marginBottom: 4 }}>
              {playerWon ? 'You Win the Pot!' : `${winnerName} Wins!`}
            </h2>
            {game.playerBestHand && (
              <p style={{ color: '#8A9096', fontSize: 13, marginBottom: 6 }}>
                Your hand: <span style={{ color: HAND_COLORS[game.playerBestHand.handRank], fontWeight: 700 }}>{HAND_RANK_NAMES[game.playerBestHand.handRank]}</span>
              </p>
            )}
            {playerWon && coinsEarned > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 10 }}>
                <Coins size={18} style={{ color: '#C6A052' }} />
                <span style={{ color: '#C6A052', fontWeight: 800, fontSize: 18 }}>+{coinsEarned} coins!</span>
              </div>
            )}
            {playerWon && alreadyClaimed && <p style={{ color: '#8A9096', fontSize: 12, marginBottom: 8 }}>Daily reward already claimed. Come back tomorrow!</p>}
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
              <button onClick={startNew} style={{ background: 'linear-gradient(135deg,#22c55e,#10b981)', border: 'none', borderRadius: 12, padding: '12px 24px', color: '#fff', fontWeight: 800, fontSize: 14, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }} data-testid="poker-play-again">
                <RefreshCw size={14} /> Play Again
              </button>
              <button onClick={() => navigate('/games')} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '12px 20px', color: '#BFC3C8', fontWeight: 700, fontSize: 14, cursor: 'pointer' }} data-testid="poker-back-games">
                All Games
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
