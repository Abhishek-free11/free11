import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, Coins, Trophy, Info } from 'lucide-react';
import { toast } from 'sonner';
import confetti from 'canvas-confetti';
import api from '../utils/api';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

// ── Constants ──────────────────────────────────────────────────────────────
const SUITS = ['spades', 'hearts', 'diamonds', 'clubs'];
const SUIT_SYMBOLS = { spades: '♠', hearts: '♥', diamonds: '♦', clubs: '♣' };
const RANKS = ['A','2','3','4','5','6','7','8','9','10','J','Q','K'];
const RANK_VALUES = { 'A':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13 };
const RED_SUITS = new Set(['hearts','diamonds']);
const GROUP_COLORS = ['#a855f7','#22c55e','#ef4444','#f59e0b','#60a5fa'];

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

// ── Meld Finding Algorithms ─────────────────────────────────────────────────
function findPureSequences(cards) {
  const bySuit = {};
  for (const c of cards) {
    if (!bySuit[c.suit]) bySuit[c.suit] = [];
    bySuit[c.suit].push(c);
  }
  const seqs = [];
  for (const suit in bySuit) {
    const sorted = [...bySuit[suit]].sort((a, b) => RANK_VALUES[a.rank] - RANK_VALUES[b.rank]);
    let run = [sorted[0]];
    for (let i = 1; i < sorted.length; i++) {
      if (RANK_VALUES[sorted[i].rank] === RANK_VALUES[sorted[i - 1].rank] + 1) {
        run.push(sorted[i]);
      } else {
        if (run.length >= 3) seqs.push(run.slice(0, 3));
        run = [sorted[i]];
      }
    }
    if (run.length >= 3) seqs.push(run.slice(0, 3));
  }
  return seqs;
}

function findSets(cards) {
  const byRank = {};
  for (const c of cards) {
    if (!byRank[c.rank]) byRank[c.rank] = [];
    byRank[c.rank].push(c);
  }
  return Object.values(byRank).filter(g => g.length >= 3).map(g => g.slice(0, 3));
}

function findImpureSequences(cards) {
  const used = new Set();
  const rankMap = {};
  for (const c of cards) {
    const v = RANK_VALUES[c.rank];
    if (!rankMap[v]) rankMap[v] = [];
    rankMap[v].push(c);
  }
  const rankNums = Object.keys(rankMap).map(Number).sort((a, b) => a - b);
  const seqs = [];
  let run = [];
  for (let i = 0; i < rankNums.length; i++) {
    const r = rankNums[i];
    const available = rankMap[r].filter(c => !used.has(c.id));
    if (!available.length) { if (run.length >= 3) seqs.push(run.slice(0, 3)); run = []; continue; }
    if (run.length === 0 || r === rankNums[i - 1] + 1) {
      run.push(available[0]);
    } else {
      if (run.length >= 3) seqs.push(run.slice(0, 3));
      run = [available[0]];
    }
  }
  if (run.length >= 3) seqs.push(run.slice(0, 3));
  return seqs;
}

function findBestArrangement(hand) {
  let remaining = [...hand];
  const melds = [];

  const pureSeqs = findPureSequences(remaining);
  for (const seq of pureSeqs) {
    const ids = new Set(seq.map(c => c.id));
    melds.push({ type: 'pure_seq', label: 'Pure Seq', cards: seq, color: GROUP_COLORS[melds.length % GROUP_COLORS.length] });
    remaining = remaining.filter(c => !ids.has(c.id));
  }
  const sets = findSets(remaining);
  for (const set of sets) {
    const ids = new Set(set.map(c => c.id));
    melds.push({ type: 'set', label: 'Set', cards: set, color: GROUP_COLORS[melds.length % GROUP_COLORS.length] });
    remaining = remaining.filter(c => !ids.has(c.id));
  }
  const impureSeqs = findImpureSequences(remaining);
  for (const seq of impureSeqs) {
    const ids = new Set(seq.map(c => c.id));
    melds.push({ type: 'seq', label: 'Sequence', cards: seq, color: GROUP_COLORS[melds.length % GROUP_COLORS.length] });
    remaining = remaining.filter(c => !ids.has(c.id));
  }

  const pureSeqCount = melds.filter(m => m.type === 'pure_seq').length;
  const seqCount = melds.filter(m => m.type !== 'set').length;
  const isValid = remaining.length <= 1 && pureSeqCount >= 1 && seqCount >= 2;
  return { melds, invalid: remaining, isValid, pureSeqCount, seqCount };
}

// ── Card Component ──────────────────────────────────────────────────────────
function Card({ card, hidden, selected, groupColor, onClick }) {
  const isRed = card && RED_SUITS.has(card.suit);
  const clr = isRed ? '#e53e3e' : '#1a202c';
  if (hidden) {
    return (
      <div onClick={onClick} style={{ width: 38, height: 54, borderRadius: 6, background: 'linear-gradient(135deg,#3730a3,#1e1b4b)', border: '1.5px solid rgba(255,255,255,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, cursor: onClick ? 'pointer' : 'default' }}>
        <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 16 }}>♠</span>
      </div>
    );
  }
  return (
    <div onClick={onClick} style={{
      width: 38, height: 54, borderRadius: 6, background: '#fff', flexShrink: 0,
      border: selected ? `2px solid #C6A052` : groupColor ? `2px solid ${groupColor}` : '1.5px solid #e2e8f0',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'space-between',
      padding: 3, cursor: onClick ? 'pointer' : 'default',
      boxShadow: selected ? '0 0 8px rgba(198,160,82,0.6)' : groupColor ? `0 0 6px ${groupColor}50` : '0 2px 6px rgba(0,0,0,0.3)',
      transition: 'all 0.15s', transform: selected ? 'translateY(-6px)' : 'none',
    }}>
      <span style={{ fontSize: 11, fontWeight: 800, color: clr, lineHeight: 1, alignSelf: 'flex-start' }}>{card.rank}</span>
      <span style={{ fontSize: 16, color: clr }}>{SUIT_SYMBOLS[card.suit]}</span>
      <span style={{ fontSize: 11, fontWeight: 800, color: clr, lineHeight: 1, alignSelf: 'flex-end', transform: 'rotate(180deg)' }}>{card.rank}</span>
    </div>
  );
}

// ── AI Logic ────────────────────────────────────────────────────────────────
function aiDraw(hand, discardTop) {
  if (!discardTop) return 'deck';
  // Pick discard if it helps complete a meld
  const testHand = [...hand, discardTop];
  const withDiscard = findBestArrangement(testHand);
  const withoutDiscard = findBestArrangement(hand);
  return withDiscard.melds.length > withoutDiscard.melds.length ? 'discard' : 'deck';
}

function aiDiscard(hand) {
  // Discard the card least likely to form melds
  const arr = findBestArrangement(hand);
  if (arr.invalid.length > 0) return arr.invalid[Math.floor(Math.random() * arr.invalid.length)];
  // All cards in melds — discard random card from smallest meld
  const last = arr.melds[arr.melds.length - 1];
  return last ? last.cards[Math.floor(Math.random() * last.cards.length)] : hand[hand.length - 1];
}

// ── Game Initialization ─────────────────────────────────────────────────────
function newGame() {
  const deck = shuffle(createDeck());
  const playerHand = deck.slice(0, 13).map(c => ({ ...c }));
  const aiHand = deck.slice(13, 26).map(c => ({ ...c }));
  const drawPile = deck.slice(26);
  const firstDiscard = drawPile.pop();
  return {
    playerHand: [...playerHand].sort((a, b) => {
      const si = SUITS.indexOf(a.suit) - SUITS.indexOf(b.suit);
      return si !== 0 ? si : RANK_VALUES[a.rank] - RANK_VALUES[b.rank];
    }),
    aiHand,
    drawPile,
    discardPile: [firstDiscard],
    selectedIdx: null,
    phase: 'player_draw', // player_draw | player_discard | ai_turn | result
    turns: 0,
    winner: null,
    aiTurnsLeft: 8 + Math.floor(Math.random() * 6), // AI declares after 8-13 turns
  };
}

// ── Main Component ───────────────────────────────────────────────────────────
export default function RummyGame() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [game, setGame] = useState(() => newGame());
  const [claiming, setClaiming] = useState(false);
  const [alreadyClaimed, setAlreadyClaimed] = useState(false);
  const [coinsEarned, setCoinsEarned] = useState(0);
  const [claimedOnce, setClaimedOnce] = useState(false);

  const arrangement = useMemo(() => findBestArrangement(game.playerHand), [game.playerHand]);

  // Get group color for a card
  const getCardGroupColor = useCallback((cardId) => {
    for (const meld of arrangement.melds) {
      if (meld.cards.find(c => c.id === cardId)) return meld.color;
    }
    return null;
  }, [arrangement]);

  // Player draws from deck
  const drawFromDeck = () => {
    if (game.phase !== 'player_draw' || !game.drawPile.length) return;
    setGame(g => {
      const pile = [...g.drawPile];
      const card = pile.pop();
      const sorted = [...g.playerHand, card].sort((a, b) => {
        const si = SUITS.indexOf(a.suit) - SUITS.indexOf(b.suit);
        return si !== 0 ? si : RANK_VALUES[a.rank] - RANK_VALUES[b.rank];
      });
      return { ...g, playerHand: sorted, drawPile: pile, phase: 'player_discard' };
    });
    toast.info('Drew from deck');
  };

  // Player picks top discard
  const pickDiscard = () => {
    if (game.phase !== 'player_draw' || !game.discardPile.length) return;
    setGame(g => {
      const pile = [...g.discardPile];
      const card = pile.pop();
      const sorted = [...g.playerHand, card].sort((a, b) => {
        const si = SUITS.indexOf(a.suit) - SUITS.indexOf(b.suit);
        return si !== 0 ? si : RANK_VALUES[a.rank] - RANK_VALUES[b.rank];
      });
      return { ...g, playerHand: sorted, discardPile: pile, phase: 'player_discard' };
    });
    toast.info(`Picked ${game.discardPile[game.discardPile.length - 1]?.rank}`);
  };

  // Select card to discard
  const selectCard = (idx) => {
    if (game.phase !== 'player_discard') return;
    setGame(g => ({ ...g, selectedIdx: g.selectedIdx === idx ? null : idx }));
  };

  // Discard selected card
  const doDiscard = () => {
    if (game.phase !== 'player_discard' || game.selectedIdx === null) return;
    setGame(g => {
      const hand = [...g.playerHand];
      const [discarded] = hand.splice(g.selectedIdx, 1);
      const sorted = hand.sort((a, b) => {
        const si = SUITS.indexOf(a.suit) - SUITS.indexOf(b.suit);
        return si !== 0 ? si : RANK_VALUES[a.rank] - RANK_VALUES[b.rank];
      });
      return {
        ...g, playerHand: sorted,
        discardPile: [...g.discardPile, discarded],
        selectedIdx: null, phase: 'ai_turn', turns: g.turns + 1,
      };
    });
  };

  // Declare (player wins)
  const handleDeclare = () => {
    if (!arrangement.isValid) { toast.error('Hand not valid yet! Keep drawing.'); return; }
    setGame(g => ({ ...g, phase: 'result', winner: 'player' }));
  };

  // AI turn
  useEffect(() => {
    if (game.phase !== 'ai_turn') return;
    const timer = setTimeout(() => {
      setGame(g => {
        if (g.phase !== 'ai_turn') return g;
        const discardTop = g.discardPile[g.discardPile.length - 1];
        const drawChoice = aiDraw(g.aiHand, discardTop);
        let pile = [...g.drawPile];
        let discards = [...g.discardPile];
        let aiHand = [...g.aiHand];

        if (drawChoice === 'discard' && discards.length > 0) {
          aiHand = [...aiHand, discards.pop()];
        } else if (pile.length > 0) {
          aiHand = [...aiHand, pile.pop()];
        }
        const toDiscard = aiDiscard(aiHand);
        aiHand = aiHand.filter(c => c.id !== toDiscard.id);
        discards.push(toDiscard);

        // AI declares after enough turns
        const aiArr = findBestArrangement(aiHand);
        const aiDeclaresNow = aiArr.isValid || g.turns >= g.aiTurnsLeft;

        return {
          ...g, aiHand, drawPile: pile, discardPile: discards,
          phase: aiDeclaresNow ? 'result' : 'player_draw',
          winner: aiDeclaresNow ? 'ai' : g.winner,
        };
      });
    }, 800);
    return () => clearTimeout(timer);
  }, [game.phase, game.turns]);

  // Result → confetti + coins
  useEffect(() => {
    if (game.phase !== 'result' || claimedOnce) return;
    setClaimedOnce(true);
    if (game.winner === 'player') {
      confetti({ particleCount: 150, spread: 90, origin: { y: 0.55 } });
      claimCoins();
    }
  }, [game.phase, game.winner]);

  const claimCoins = async () => {
    if (claiming || alreadyClaimed) return;
    setClaiming(true);
    try {
      const res = await api.post('/v2/earn/rummy-win');
      setCoinsEarned(res.data.coins_earned || 50);
      if (res.data.new_balance !== undefined) updateUser({ coins_balance: res.data.new_balance });
      toast.success(`+${res.data.coins_earned} coins earned!`, { description: 'Daily Rummy win reward' });
    } catch (e) {
      if (e.response?.status === 400) { setAlreadyClaimed(true); }
    } finally { setClaiming(false); }
  };

  const startNew = () => { setClaimedOnce(false); setCoinsEarned(0); setGame(newGame()); };

  const topDiscard = game.discardPile[game.discardPile.length - 1];
  const isPlayerDraw = game.phase === 'player_draw';
  const isPlayerDiscard = game.phase === 'player_discard';
  const isResult = game.phase === 'result';
  const isAITurn = game.phase === 'ai_turn';

  return (
    <div style={{ minHeight: '100vh', background: '#0F1115', paddingBottom: 120 }}>
      <Navbar />
      {/* Header */}
      <div style={{ background: 'linear-gradient(135deg,#ef4444,#ec4899)', padding: '16px 16px 14px' }}>
        <div className="max-w-screen-sm mx-auto">
          <button onClick={() => navigate('/games/rummy')} style={{ color: 'rgba(255,255,255,0.8)', display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, marginBottom: 10 }}>
            <ArrowLeft size={14} /> Back to Lobby
          </button>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h1 style={{ color: '#fff', fontSize: 22, fontWeight: 800 }}>Rummy</h1>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>13-Card Indian Rummy · vs AI</p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: 10, fontWeight: 700 }}>TURN {game.turns + 1}</p>
              <p style={{ color: '#fbbf24', fontSize: 14, fontWeight: 800 }}>Win = +50 coins</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-screen-sm mx-auto px-3 mt-4 space-y-3" data-testid="rummy-game">

        {/* AI hand */}
        <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: '12px 14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg,#ef4444,#ec4899)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ color: '#fff', fontSize: 12, fontWeight: 800 }}>A</span>
              </div>
              <div>
                <p style={{ color: '#fff', fontSize: 12, fontWeight: 700 }}>Ananya (AI)</p>
                <p style={{ color: '#8A9096', fontSize: 10 }}>{game.aiHand.length} cards</p>
              </div>
            </div>
            {isAITurn && <span style={{ color: '#60a5fa', fontSize: 11, fontWeight: 700 }} className="animate-pulse">Thinking...</span>}
          </div>
          <div style={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
            {game.aiHand.map((_, i) => <Card key={i} card={null} hidden />)}
          </div>
        </div>

        {/* Draw pile + Discard pile */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          <button onClick={drawFromDeck} disabled={!isPlayerDraw}
            style={{ background: isPlayerDraw ? 'rgba(198,160,82,0.1)' : 'rgba(255,255,255,0.03)', border: `1px solid ${isPlayerDraw ? 'rgba(198,160,82,0.4)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 12, padding: '12px', textAlign: 'center', cursor: isPlayerDraw ? 'pointer' : 'not-allowed', opacity: isPlayerDraw ? 1 : 0.5 }}
            data-testid="draw-deck-btn">
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 6 }}>
              <Card card={null} hidden />
            </div>
            <p style={{ color: isPlayerDraw ? '#C6A052' : '#8A9096', fontSize: 12, fontWeight: 700 }}>Draw Deck</p>
            <p style={{ color: '#8A9096', fontSize: 10 }}>{game.drawPile.length} cards</p>
          </button>
          <button onClick={pickDiscard} disabled={!isPlayerDraw || !topDiscard}
            style={{ background: isPlayerDraw ? 'rgba(96,165,250,0.08)' : 'rgba(255,255,255,0.03)', border: `1px solid ${isPlayerDraw ? 'rgba(96,165,250,0.3)' : 'rgba(255,255,255,0.07)'}`, borderRadius: 12, padding: '12px', textAlign: 'center', cursor: isPlayerDraw ? 'pointer' : 'not-allowed', opacity: isPlayerDraw ? 1 : 0.5 }}
            data-testid="draw-discard-btn">
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 6 }}>
              {topDiscard ? <Card card={topDiscard} /> : <Card card={null} hidden />}
            </div>
            <p style={{ color: isPlayerDraw ? '#60a5fa' : '#8A9096', fontSize: 12, fontWeight: 700 }}>Discard Pile</p>
            <p style={{ color: '#8A9096', fontSize: 10 }}>{topDiscard ? `Top: ${topDiscard.rank}${SUIT_SYMBOLS[topDiscard.suit]}` : 'Empty'}</p>
          </button>
        </div>

        {/* Player hand */}
        <div style={{
          background: isPlayerDiscard ? 'rgba(168,85,247,0.05)' : 'rgba(255,255,255,0.03)',
          border: `1px solid ${isPlayerDiscard ? 'rgba(168,85,247,0.3)' : 'rgba(255,255,255,0.07)'}`,
          borderRadius: 14, padding: 14,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <div>
              <p style={{ color: '#fff', fontSize: 13, fontWeight: 800 }}>Your Hand ({game.playerHand.length} cards)</p>
              <p style={{ color: arrangement.isValid ? '#4ade80' : '#8A9096', fontSize: 11, fontWeight: 700 }}>
                {arrangement.isValid ? 'Valid hand! Ready to declare' : `${arrangement.melds.length} melds found · ${arrangement.invalid.length} ungrouped`}
              </p>
            </div>
            {isPlayerDiscard && game.selectedIdx !== null && (
              <button onClick={doDiscard} style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 10, padding: '6px 14px', color: '#ef4444', fontSize: 12, fontWeight: 800, cursor: 'pointer' }} data-testid="discard-btn">
                Discard
              </button>
            )}
          </div>

          {/* Cards — 2 rows */}
          <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            {game.playerHand.map((card, idx) => (
              <Card
                key={card.id}
                card={card}
                selected={game.selectedIdx === idx}
                groupColor={getCardGroupColor(card.id)}
                onClick={() => selectCard(idx)}
              />
            ))}
          </div>

          {/* Meld legend */}
          {arrangement.melds.length > 0 && (
            <div style={{ marginTop: 10, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {arrangement.melds.map((m, i) => (
                <span key={i} style={{ background: `${m.color}18`, border: `1px solid ${m.color}50`, borderRadius: 20, padding: '2px 8px', color: m.color, fontSize: 10, fontWeight: 700 }}>
                  {m.label}
                </span>
              ))}
              {arrangement.invalid.length > 0 && (
                <span style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 20, padding: '2px 8px', color: '#ef4444', fontSize: 10, fontWeight: 700 }}>
                  {arrangement.invalid.length} ungrouped
                </span>
              )}
            </div>
          )}
        </div>

        {/* Phase instruction */}
        <div style={{ textAlign: 'center', padding: '4px 0' }}>
          {isPlayerDraw && <p style={{ color: '#C6A052', fontSize: 13, fontWeight: 700 }}>Draw a card to continue</p>}
          {isPlayerDiscard && <p style={{ color: '#a855f7', fontSize: 13, fontWeight: 700 }}>Select a card to discard</p>}
          {isAITurn && <p style={{ color: '#60a5fa', fontSize: 13 }} className="animate-pulse">Ananya is playing...</p>}
        </div>

        {/* Declare button */}
        {(isPlayerDraw || isPlayerDiscard) && (
          <button onClick={handleDeclare} disabled={!arrangement.isValid}
            style={{
              width: '100%', background: arrangement.isValid ? 'linear-gradient(135deg,#C6A052,#E0B84F)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${arrangement.isValid ? 'rgba(198,160,82,0.5)' : 'rgba(255,255,255,0.08)'}`,
              borderRadius: 14, padding: '16px', color: arrangement.isValid ? '#0F1115' : '#8A9096', fontWeight: 800, fontSize: 16, cursor: arrangement.isValid ? 'pointer' : 'not-allowed',
            }}
            data-testid="declare-btn">
            {arrangement.isValid ? 'Declare & Win!' : `Complete melds to Declare (${arrangement.melds.length}/4 found)`}
          </button>
        )}

        {/* How to play guide */}
        <div style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 12, padding: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <Info size={12} style={{ color: '#8A9096' }} />
            <p style={{ color: '#8A9096', fontSize: 10, fontWeight: 700, letterSpacing: '0.06em' }}>HOW TO PLAY</p>
          </div>
          <p style={{ color: '#8A9096', fontSize: 11, lineHeight: 1.5 }}>
            Form <span style={{ color: '#a855f7' }}>sequences</span> (consecutive same suit) and <span style={{ color: '#22c55e' }}>sets</span> (same rank). Need 1 pure sequence + 2 total sequences. Coloured cards = in a valid group. Declare when your whole hand is grouped!
          </p>
        </div>

        {/* Result */}
        {isResult && (
          <div style={{
            background: game.winner === 'player' ? 'rgba(198,160,82,0.1)' : 'rgba(239,68,68,0.07)',
            border: `1px solid ${game.winner === 'player' ? 'rgba(198,160,82,0.4)' : 'rgba(239,68,68,0.2)'}`,
            borderRadius: 16, padding: 20, textAlign: 'center',
          }} data-testid="rummy-result">
            <div style={{ fontSize: 44, marginBottom: 8 }}>{game.winner === 'player' ? '🏆' : '😔'}</div>
            <h2 style={{ color: game.winner === 'player' ? '#C6A052' : '#ef4444', fontSize: 22, fontWeight: 800, marginBottom: 4 }}>
              {game.winner === 'player' ? 'You Declared! You Win!' : 'Ananya Declared First!'}
            </h2>
            {game.winner === 'player' && coinsEarned > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 8 }}>
                <Coins size={18} style={{ color: '#C6A052' }} />
                <span style={{ color: '#C6A052', fontWeight: 800, fontSize: 18 }}>+{coinsEarned} coins!</span>
              </div>
            )}
            {game.winner === 'player' && alreadyClaimed && (
              <p style={{ color: '#8A9096', fontSize: 12, marginBottom: 8 }}>Daily reward already claimed. Come back tomorrow!</p>
            )}
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
              <button onClick={startNew} style={{ background: 'linear-gradient(135deg,#ef4444,#ec4899)', border: 'none', borderRadius: 12, padding: '12px 24px', color: '#fff', fontWeight: 800, fontSize: 14, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }} data-testid="rummy-play-again">
                <RefreshCw size={14} /> Play Again
              </button>
              <button onClick={() => navigate('/games')} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 12, padding: '12px 20px', color: '#BFC3C8', fontWeight: 700, fontSize: 14, cursor: 'pointer' }} data-testid="rummy-back-games">
                All Games
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
