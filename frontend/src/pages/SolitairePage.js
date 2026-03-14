import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, RefreshCw, RotateCcw, Trophy, Coins } from 'lucide-react';
import { toast } from 'sonner';
import confetti from 'canvas-confetti';
import api from '../utils/api';
import Navbar from '../components/Navbar';
import { useAuth } from '../context/AuthContext';

// ─── Constants ───────────────────────────────────────────────────────────────

const SUIT_SYMBOLS = { spades: '♠', hearts: '♥', diamonds: '♦', clubs: '♣' };
const RED_SUITS = new Set(['hearts', 'diamonds']);
const SUIT_KEYS = ['spades', 'hearts', 'diamonds', 'clubs'];
const RANK_DISPLAY = { 1: 'A', 11: 'J', 12: 'Q', 13: 'K' };
const FACE_DOWN_SHOW = 10;  // px visible for face-down stacked cards
const FACE_UP_SHOW   = 20;  // px visible for face-up stacked cards

const displayRank = (r) => RANK_DISPLAY[r] || String(r);
const isRed = (suit) => RED_SUITS.has(suit);

// ─── Deck helpers ─────────────────────────────────────────────────────────────

function createShuffledDeck() {
  const deck = [];
  for (const suit of SUIT_KEYS)
    for (let rank = 1; rank <= 13; rank++)
      deck.push({ rank, suit, id: `${suit}_${rank}` });
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  return deck;
}

function initGame() {
  const deck = createShuffledDeck();
  const tableau = [];
  let di = 0;
  for (let col = 0; col < 7; col++) {
    const pile = [];
    for (let row = 0; row <= col; row++)
      pile.push({ ...deck[di++], faceUp: row === col });
    tableau.push(pile);
  }
  return {
    tableau,
    foundation: { spades: [], hearts: [], diamonds: [], clubs: [] },
    stock: deck.slice(di).map(c => ({ ...c, faceUp: false })),
    waste: [],
    moves: 0,
    gameWon: false,
    coinsEarned: false,
  };
}

function canToTableau(card, col) {
  if (!col.length) return card.rank === 13;
  const top = col[col.length - 1];
  if (!top.faceUp) return false;
  return isRed(card.suit) !== isRed(top.suit) && card.rank === top.rank - 1;
}

function canToFoundation(card, pile) {
  if (!pile.length) return card.rank === 1;
  const top = pile[pile.length - 1];
  return top.suit === card.suit && card.rank === top.rank + 1;
}

function checkWin(foundation) {
  return SUIT_KEYS.every(s => foundation[s].length === 13);
}

// ─── Deep-clone state ─────────────────────────────────────────────────────────

function cloneState(s) {
  return {
    ...s,
    tableau: s.tableau.map(col => col.map(c => ({ ...c }))),
    foundation: Object.fromEntries(SUIT_KEYS.map(k => [k, s.foundation[k].map(c => ({ ...c }))])),
    stock: s.stock.map(c => ({ ...c })),
    waste: s.waste.map(c => ({ ...c })),
  };
}

// ─── PlayCard component ───────────────────────────────────────────────────────

const CARD_W = 46;
const CARD_H = 67;

const PlayCard = React.memo(({ card, selected, onClick, placeholder }) => {
  const baseStyle = {
    width: CARD_W, height: CARD_H, borderRadius: 6, cursor: 'pointer',
    userSelect: 'none', flexShrink: 0, position: 'relative',
  };

  if (placeholder) {
    return (
      <div onClick={onClick} style={{
        ...baseStyle, border: '1.5px dashed rgba(198,160,82,0.25)',
        background: 'rgba(255,255,255,0.02)',
      }} />
    );
  }

  if (!card.faceUp) {
    return (
      <div onClick={onClick} style={{
        ...baseStyle,
        background: 'linear-gradient(135deg, #1a3a6e 0%, #0d2249 100%)',
        border: '1.5px solid rgba(100,149,237,0.3)',
        boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', inset: 4, borderRadius: 3,
          border: '1px solid rgba(100,149,237,0.2)',
          backgroundImage: 'repeating-linear-gradient(45deg, rgba(100,149,237,0.07) 0,rgba(100,149,237,0.07) 1px,transparent 1px,transparent 6px)',
        }} />
      </div>
    );
  }

  const color = isRed(card.suit) ? '#dc2626' : '#0f172a';
  return (
    <div onClick={onClick} style={{
      ...baseStyle,
      background: selected ? '#fffde7' : '#fff',
      border: selected ? '2px solid #C6A052' : '1.5px solid #d1d5db',
      boxShadow: selected
        ? '0 0 0 2px rgba(198,160,82,0.45), 0 4px 14px rgba(0,0,0,0.45)'
        : '0 2px 6px rgba(0,0,0,0.35)',
      transition: 'box-shadow 0.1s, border-color 0.1s',
    }}>
      {/* top-left */}
      <div style={{ position: 'absolute', top: 2, left: 3, color, fontSize: 10, fontWeight: 700, lineHeight: 1.1 }}>
        {displayRank(card.rank)}<br />{SUIT_SYMBOLS[card.suit]}
      </div>
      {/* center */}
      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', fontSize: 22, color, lineHeight: 1 }}>
        {SUIT_SYMBOLS[card.suit]}
      </div>
      {/* bottom-right rotated */}
      <div style={{ position: 'absolute', bottom: 2, right: 3, color, fontSize: 10, fontWeight: 700, lineHeight: 1.1, transform: 'rotate(180deg)' }}>
        {displayRank(card.rank)}<br />{SUIT_SYMBOLS[card.suit]}
      </div>
    </div>
  );
});

// ─── Tableau Column ───────────────────────────────────────────────────────────

const TableauColumn = ({ pile, selectedSrc, onCardClick, colIdx }) => {
  const colHeight = pile.length === 0 ? CARD_H :
    pile.slice(0, -1).reduce((h, c) => h + (c.faceUp ? FACE_UP_SHOW : FACE_DOWN_SHOW), 0) + CARD_H;

  return (
    <div style={{ position: 'relative', width: CARD_W, height: colHeight, minHeight: CARD_H, flexShrink: 0 }}>
      {/* Empty placeholder */}
      {pile.length === 0 && (
        <PlayCard placeholder onClick={() => onCardClick('tableau', colIdx, -1)} />
      )}
      {pile.map((card, cardIdx) => {
        const topPx = pile.slice(0, cardIdx).reduce((h, c) => h + (c.faceUp ? FACE_UP_SHOW : FACE_DOWN_SHOW), 0);
        const isSel = selectedSrc?.area === 'tableau' && selectedSrc.col === colIdx && cardIdx >= selectedSrc.idx;
        return (
          <div key={card.id} style={{ position: 'absolute', top: topPx, left: 0, zIndex: cardIdx }}>
            <PlayCard
              card={card}
              selected={isSel}
              onClick={() => onCardClick('tableau', colIdx, cardIdx)}
            />
          </div>
        );
      })}
    </div>
  );
};

// ─── Main SolitairePage ───────────────────────────────────────────────────────

export default function SolitairePage() {
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [game, setGame] = useState(() => initGame());
  const [selected, setSelected] = useState(null); // { area, col?, idx? }
  const [history, setHistory] = useState([]);       // undo stack
  const timerRef = useRef(null);
  const [elapsed, setElapsed] = useState(0);

  // Timer
  useEffect(() => {
    timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000);
    return () => clearInterval(timerRef.current);
  }, [game.gameWon]);

  useEffect(() => {
    if (game.gameWon) clearInterval(timerRef.current);
  }, [game.gameWon]);

  const formatTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;

  // ── Commit a move (save to history, update state) ──────────────────────────

  const commit = useCallback((newGame) => {
    setHistory(h => [...h.slice(-19), game]);
    setGame(newGame);
    setSelected(null);
  }, [game]);

  // ── Draw from stock ────────────────────────────────────────────────────────

  const drawStock = useCallback(() => {
    const g = cloneState(game);
    if (g.stock.length === 0) {
      if (g.waste.length === 0) return;
      g.stock = g.waste.reverse().map(c => ({ ...c, faceUp: false }));
      g.waste = [];
    } else {
      const card = { ...g.stock.pop(), faceUp: true };
      g.waste.push(card);
      g.moves++;
    }
    commit(g);
  }, [game, commit]);

  // ── Try to auto-move to foundation ────────────────────────────────────────

  const tryAutoFoundation = useCallback((g, card) => {
    for (const suit of SUIT_KEYS) {
      if (canToFoundation(card, g.foundation[suit])) {
        return suit;
      }
    }
    return null;
  }, []);

  // ── Handle card click ──────────────────────────────────────────────────────

  const handleCardClick = useCallback((area, col, idx) => {
    if (game.gameWon) return;

    // Stock click: draw
    if (area === 'stock') { drawStock(); return; }

    // Get the card being clicked
    const getCard = (a, c, i) => {
      if (a === 'waste') return game.waste[game.waste.length - 1];
      if (a === 'tableau') return game.tableau[c]?.[i];
      if (a === 'foundation') return game.foundation[SUIT_KEYS[c]]?.[game.foundation[SUIT_KEYS[c]].length - 1];
      return null;
    };

    // ── Nothing selected yet ─────────────────────────────────────────────────
    if (!selected) {
      if (area === 'waste' && game.waste.length > 0) {
        setSelected({ area: 'waste' });
        return;
      }
      if (area === 'tableau') {
        const card = game.tableau[col]?.[idx];
        if (!card?.faceUp) return;
        setSelected({ area: 'tableau', col, idx });
        return;
      }
      if (area === 'foundation') {
        const pile = game.foundation[SUIT_KEYS[col]];
        if (pile?.length > 0) setSelected({ area: 'foundation', col });
        return;
      }
      return;
    }

    // ── Something is selected ────────────────────────────────────────────────
    const sel = selected;

    // Get moving cards
    let movingCards;
    if (sel.area === 'waste') {
      movingCards = [game.waste[game.waste.length - 1]];
    } else if (sel.area === 'tableau') {
      movingCards = game.tableau[sel.col].slice(sel.idx);
    } else if (sel.area === 'foundation') {
      const p = game.foundation[SUIT_KEYS[sel.col]];
      movingCards = [p[p.length - 1]];
    }

    const topCard = movingCards[0];

    // Deselect if clicking same card
    if (area === sel.area && col === sel.col && idx === sel.idx) {
      setSelected(null);
      return;
    }

    // ── Move to TABLEAU ──────────────────────────────────────────────────────
    if (area === 'tableau') {
      const targetCol = game.tableau[col];
      if (canToTableau(topCard, targetCol)) {
        const g = cloneState(game);
        // Remove from source
        if (sel.area === 'waste') {
          g.waste.pop();
        } else if (sel.area === 'tableau') {
          g.tableau[sel.col].splice(sel.idx);
          // Flip newly exposed card
          const exposedCol = g.tableau[sel.col];
          if (exposedCol.length > 0 && !exposedCol[exposedCol.length - 1].faceUp) {
            exposedCol[exposedCol.length - 1].faceUp = true;
          }
        } else if (sel.area === 'foundation') {
          g.foundation[SUIT_KEYS[sel.col]].pop();
        }
        // Add to target
        g.tableau[col].push(...movingCards);
        g.moves++;
        commit(g);
        return;
      }
      // Failed move: change selection or deselect
      const clickedCard = game.tableau[col]?.[idx];
      if (clickedCard?.faceUp) {
        setSelected({ area: 'tableau', col, idx });
      } else {
        setSelected(null);
      }
      return;
    }

    // ── Move to FOUNDATION ───────────────────────────────────────────────────
    if (area === 'foundation' && movingCards.length === 1) {
      const targetSuit = SUIT_KEYS[col];
      const targetPile = game.foundation[targetSuit];
      if (canToFoundation(topCard, targetPile)) {
        const g = cloneState(game);
        if (sel.area === 'waste') {
          g.waste.pop();
        } else if (sel.area === 'tableau') {
          g.tableau[sel.col].splice(sel.idx);
          const exposedCol = g.tableau[sel.col];
          if (exposedCol.length > 0 && !exposedCol[exposedCol.length - 1].faceUp) {
            exposedCol[exposedCol.length - 1].faceUp = true;
          }
        } else if (sel.area === 'foundation') {
          g.foundation[SUIT_KEYS[sel.col]].pop();
        }
        g.foundation[targetSuit].push(topCard);
        g.moves++;
        // Check win
        if (checkWin(g.foundation)) {
          g.gameWon = true;
          triggerWin(g);
        }
        commit(g);
        return;
      }
      setSelected(null);
      return;
    }

    setSelected(null);
  }, [game, selected, drawStock, commit]);

  // ── Double-click: auto-move to foundation ─────────────────────────────────

  const handleDoubleClick = useCallback((area, col, idx) => {
    if (game.gameWon) return;
    let card, srcInfo;

    if (area === 'waste' && game.waste.length > 0) {
      card = game.waste[game.waste.length - 1];
      srcInfo = { area: 'waste' };
    } else if (area === 'tableau') {
      const c = game.tableau[col]?.[idx];
      if (!c?.faceUp || idx !== game.tableau[col].length - 1) return;
      card = c;
      srcInfo = { area: 'tableau', col, idx };
    } else return;

    for (const suit of SUIT_KEYS) {
      if (canToFoundation(card, game.foundation[suit])) {
        const g = cloneState(game);
        if (srcInfo.area === 'waste') {
          g.waste.pop();
        } else {
          g.tableau[col].splice(idx);
          const exp = g.tableau[col];
          if (exp.length > 0 && !exp[exp.length - 1].faceUp) exp[exp.length - 1].faceUp = true;
        }
        g.foundation[suit].push(card);
        g.moves++;
        if (checkWin(g.foundation)) { g.gameWon = true; triggerWin(g); }
        commit(g);
        setSelected(null);
        return;
      }
    }
  }, [game, commit]);

  // ── Win celebration ────────────────────────────────────────────────────────

  const triggerWin = useCallback(async (g) => {
    confetti({ particleCount: 200, spread: 90, origin: { y: 0.5 }, colors: ['#C6A052', '#E0B84F', '#fff', '#f87171', '#60a5fa'] });
    toast.success('You won Solitaire! +25 coins earned!', { duration: 5000 });
    if (!g.coinsEarned) {
      try {
        const res = await api.post('/v2/earn/solitaire-win');
        if (res.data?.new_balance !== undefined) updateUser({ coins_balance: res.data.new_balance });
      } catch {
        // Silent fail — already claimed today
      }
    }
  }, [updateUser]);

  // ── Undo ──────────────────────────────────────────────────────────────────

  const undo = useCallback(() => {
    if (history.length === 0) { toast.info('Nothing to undo'); return; }
    const prev = history[history.length - 1];
    setHistory(h => h.slice(0, -1));
    setGame(prev);
    setSelected(null);
  }, [history]);

  // ── New Game ──────────────────────────────────────────────────────────────

  const newGame = useCallback(() => {
    setGame(initGame());
    setSelected(null);
    setHistory([]);
    setElapsed(0);
  }, []);

  const { tableau, foundation, stock, waste } = game;
  const wasteTop = waste.length > 0 ? waste[waste.length - 1] : null;

  return (
    <div className="min-h-screen pb-28" style={{ background: '#0a3d1f' }}>
      <Navbar />

      {/* Header */}
      <div style={{ background: 'rgba(10,61,31,0.95)', borderBottom: '1px solid rgba(255,255,255,0.1)', padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <button onClick={() => navigate('/games')} style={{ color: '#C6A052', display: 'flex', alignItems: 'center', gap: 6, fontSize: 14, fontWeight: 600 }}>
          <ArrowLeft size={16} /> Back
        </button>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: '#fff', fontWeight: 700, fontSize: 16 }}>Solitaire</p>
          <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11 }}>Moves: {game.moves} · {formatTime(elapsed)}</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={undo} disabled={history.length === 0} style={{ color: history.length > 0 ? '#C6A052' : 'rgba(255,255,255,0.25)', padding: 6 }} data-testid="undo-btn">
            <RotateCcw size={18} />
          </button>
          <button onClick={newGame} style={{ color: '#4ade80', padding: 6 }} data-testid="new-game-btn">
            <RefreshCw size={18} />
          </button>
        </div>
      </div>

      {/* Win Banner */}
      {game.gameWon && (
        <div style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)', padding: '12px 16px', textAlign: 'center' }}>
          <p style={{ color: '#0F1115', fontWeight: 800, fontSize: 18 }}>You Won!</p>
          <p style={{ color: '#0F1115', fontSize: 13, opacity: 0.8 }}>+25 coins earned · {game.moves} moves · {formatTime(elapsed)}</p>
          <button onClick={newGame} style={{ marginTop: 8, background: '#0F1115', color: '#C6A052', border: 'none', borderRadius: 20, padding: '6px 20px', fontWeight: 700, cursor: 'pointer' }}>
            Play Again
          </button>
        </div>
      )}

      {/* Game Board */}
      <div style={{ overflowX: 'auto', padding: '12px 8px 0' }}>
        <div style={{ minWidth: 340, maxWidth: 560, margin: '0 auto' }}>

          {/* Top Row: Stock + Waste + Foundation */}
          <div style={{ display: 'flex', gap: 5, marginBottom: 12, justifyContent: 'space-between', alignItems: 'flex-start' }}>
            {/* Stock */}
            <div style={{ flexShrink: 0 }}>
              {stock.length > 0 ? (
                <PlayCard card={{ faceUp: false, suit: 'spades', rank: 1 }} onClick={drawStock} />
              ) : (
                <PlayCard placeholder onClick={drawStock} />
              )}
              <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 9, textAlign: 'center', marginTop: 2 }}>{stock.length}</p>
            </div>

            {/* Waste */}
            <div style={{ flexShrink: 0 }}>
              {wasteTop ? (
                <PlayCard
                  card={wasteTop}
                  selected={selected?.area === 'waste'}
                  onClick={() => handleCardClick('waste', 0, 0)}
                  onDoubleClick={() => handleDoubleClick('waste', 0, 0)}
                />
              ) : (
                <PlayCard placeholder onClick={() => {}} />
              )}
            </div>

            {/* Spacer */}
            <div style={{ flex: 1 }} />

            {/* Foundation piles */}
            {SUIT_KEYS.map((suit, fi) => {
              const pile = foundation[suit];
              const topCard = pile.length > 0 ? pile[pile.length - 1] : null;
              return (
                <div key={suit} style={{ flexShrink: 0 }}>
                  {topCard ? (
                    <PlayCard
                      card={topCard}
                      selected={selected?.area === 'foundation' && selected.col === fi}
                      onClick={() => handleCardClick('foundation', fi, 0)}
                    />
                  ) : (
                    <div onClick={() => handleCardClick('foundation', fi, 0)} style={{
                      width: CARD_W, height: CARD_H, borderRadius: 6,
                      border: '1.5px dashed rgba(255,255,255,0.15)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 20, color: 'rgba(255,255,255,0.2)', cursor: 'pointer',
                    }}>
                      {SUIT_SYMBOLS[suit]}
                    </div>
                  )}
                  <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 9, textAlign: 'center', marginTop: 2 }}>{pile.length}/13</p>
                </div>
              );
            })}
          </div>

          {/* Tableau */}
          <div style={{ display: 'flex', gap: 5, alignItems: 'flex-start' }}>
            {tableau.map((pile, colIdx) => (
              <TableauColumn
                key={colIdx}
                pile={pile}
                selectedSrc={selected}
                onCardClick={(area, col, idx) => handleCardClick(area, col, idx)}
                colIdx={colIdx}
              />
            ))}
          </div>

          {/* Padding for bottom nav */}
          <div style={{ height: 80 }} />
        </div>
      </div>

      {/* Instructions */}
      {!game.gameWon && game.moves === 0 && (
        <div style={{ textAlign: 'center', marginTop: 16, padding: '0 16px' }}>
          <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11 }}>Tap a card to select · Tap again to move · Double-tap to auto-send to foundation</p>
        </div>
      )}
    </div>
  );
}
