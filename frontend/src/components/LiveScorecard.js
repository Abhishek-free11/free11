import React from 'react';
import { motion } from 'framer-motion';
import { ChevronRight, TrendingUp, Activity, Target } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// Parse "4,0,1,W,6,2" or space/dot separated into array of ball results
function parseRecentBalls(raw) {
  if (!raw || typeof raw !== 'string' || !raw.trim()) return [];
  // Try comma-separated, then space-separated
  const balls = raw.includes(',') ? raw.split(',') : raw.split(' ');
  return balls
    .map(s => s.trim())
    .filter(Boolean)
    .slice(-6);
}

function BallDot({ ball, idx }) {
  const w = ball.toUpperCase();
  const isWicket = w === 'W' || w.startsWith('W.');
  const isSix = w === '6';
  const isFour = w === '4';
  const isExtra = w.startsWith('WD') || w.startsWith('NB') || w.startsWith('LB');

  const bg = isWicket
    ? '#ef4444'
    : isSix
    ? '#a855f7'
    : isFour
    ? '#C6A052'
    : isExtra
    ? '#3b82f6'
    : 'rgba(255,255,255,0.08)';

  const textColor = isWicket || isSix || isFour ? '#fff' : isExtra ? '#fff' : '#cbd5e1';
  const displayText = isWicket ? 'W' : ball.length > 3 ? ball.slice(0, 2) : ball;

  return (
    <motion.div
      initial={{ scale: 0.6, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: idx * 0.05, duration: 0.2 }}
      style={{
        width: 28, height: 28, borderRadius: '50%',
        background: bg,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 10, fontWeight: 800, color: textColor, flexShrink: 0,
        border: `1px solid ${isWicket ? 'rgba(239,68,68,0.4)' : isSix ? 'rgba(168,85,247,0.4)' : isFour ? 'rgba(198,160,82,0.4)' : 'rgba(255,255,255,0.06)'}`,
        boxShadow: isWicket ? '0 0 8px rgba(239,68,68,0.4)' : isSix ? '0 0 8px rgba(168,85,247,0.3)' : isFour ? '0 0 8px rgba(198,160,82,0.3)' : 'none',
      }}
    >
      {displayText}
    </motion.div>
  );
}

function StatRow({ label, value, color = '#e2e8f0', accent = false }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '2px 0' }}>
      <span style={{ color: '#8A9096', fontSize: 10 }}>{label}</span>
      <span style={{ color: accent ? '#C6A052' : color, fontSize: 11, fontWeight: accent ? 800 : 600 }}>{value}</span>
    </div>
  );
}

export default function LiveScorecard({ match, liveData, onTap }) {
  const navigate = useNavigate();

  if (!match?.match_id) return null;

  const handleTap = () => {
    if (onTap) { onTap(); return; }
    navigate(match.match_id ? `/match/${match.match_id}` : '/match-centre');
  };

  const recentBalls = parseRecentBalls(liveData?.recent_scores);
  const batsmen = liveData?.batsmen || [];
  const bowlers = liveData?.bowlers || [];
  const crr = liveData?.current_run_rate;
  const rrr = liveData?.required_run_rate;
  const currentBall = liveData?.current_ball || match.current_ball;
  const isActuallyLive = match.status === 'live' || liveData?.status === 'live';

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15, duration: 0.3 }}
      onClick={handleTap}
      className="relative overflow-hidden rounded-2xl cursor-pointer active:scale-[0.99] transition-transform"
      style={{
        background: 'linear-gradient(135deg, #020f04 0%, #061208 50%, #020f04 100%)',
        border: '1px solid rgba(34,197,94,0.22)',
        boxShadow: '0 0 24px rgba(34,197,94,0.05)',
      }}
      data-testid="live-scorecard"
    >
      {/* Top green line */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 2,
        background: 'linear-gradient(90deg, transparent, #22c55e, transparent)',
      }} />

      <div style={{ padding: '12px 14px 10px' }}>

        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            {isActuallyLive ? (
              <span style={{
                display: 'flex', alignItems: 'center', gap: 4,
                background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)',
                borderRadius: 20, padding: '2px 8px',
              }}>
                <span className="animate-pulse" style={{
                  width: 6, height: 6, borderRadius: '50%', background: '#ef4444', display: 'inline-block',
                }} />
                <span style={{ color: '#f87171', fontSize: 9, fontWeight: 800, letterSpacing: '0.08em' }}>LIVE</span>
              </span>
            ) : (
              <span style={{
                background: 'rgba(251,146,60,0.12)', border: '1px solid rgba(251,146,60,0.25)',
                borderRadius: 20, padding: '2px 8px', color: '#fb923c', fontSize: 9, fontWeight: 800,
              }}>
                UPCOMING
              </span>
            )}
            <span style={{ color: '#4ade80', fontSize: 10, fontWeight: 600, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {match.series || match.match_type || 'Cricket'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 3, color: '#C6A052', fontSize: 10, fontWeight: 700 }}>
            Predict <ChevronRight size={12} />
          </div>
        </div>

        {/* Teams + scores */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <div style={{ flex: 1 }}>
            <p style={{
              color: '#fff', fontWeight: 900, fontSize: 22,
              fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.06em', lineHeight: 1,
            }}>
              {match.team1_short}
            </p>
            {match.team1_score && (
              <p style={{ color: '#C6A052', fontSize: 14, fontWeight: 800, fontFamily: 'monospace', marginTop: 2 }}>
                {match.team1_score}
              </p>
            )}
            <p style={{ color: '#8A9096', fontSize: 9, marginTop: 1 }}>
              {liveData?.batting_team && liveData.batting_team.toLowerCase().includes(match.team1?.toLowerCase() || '') ? '● batting' : ''}
            </p>
          </div>

          <div style={{ textAlign: 'center', paddingHorizontal: 12 }}>
            <p style={{ color: '#8A9096', fontSize: 10, fontWeight: 800 }}>VS</p>
            {currentBall && currentBall !== '0' && (
              <p style={{ color: '#4ade80', fontSize: 10, fontWeight: 700, marginTop: 2 }}>
                Ov {currentBall}
              </p>
            )}
          </div>

          <div style={{ flex: 1, textAlign: 'right' }}>
            <p style={{
              color: '#fff', fontWeight: 900, fontSize: 22,
              fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.06em', lineHeight: 1,
            }}>
              {match.team2_short}
            </p>
            {match.team2_score && (
              <p style={{ color: '#BFC3C8', fontSize: 14, fontWeight: 800, fontFamily: 'monospace', marginTop: 2 }}>
                {match.team2_score}
              </p>
            )}
            <p style={{ color: '#8A9096', fontSize: 9, marginTop: 1 }}>
              {liveData?.batting_team && liveData.batting_team.toLowerCase().includes(match.team2?.toLowerCase() || '') ? '● batting' : ''}
            </p>
          </div>
        </div>

        {/* Run rates */}
        {(crr > 0 || rrr) && (
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            {crr > 0 && (
              <div style={{
                background: 'rgba(74,222,128,0.06)', border: '1px solid rgba(74,222,128,0.15)',
                borderRadius: 8, padding: '3px 10px', display: 'flex', alignItems: 'center', gap: 4,
              }}>
                <TrendingUp size={10} style={{ color: '#4ade80' }} />
                <span style={{ color: '#4ade80', fontSize: 10, fontWeight: 700 }}>CRR {crr.toFixed(2)}</span>
              </div>
            )}
            {rrr && rrr !== '' && (
              <div style={{
                background: 'rgba(251,146,60,0.06)', border: '1px solid rgba(251,146,60,0.15)',
                borderRadius: 8, padding: '3px 10px', display: 'flex', alignItems: 'center', gap: 4,
              }}>
                <Activity size={10} style={{ color: '#fb923c' }} />
                <span style={{ color: '#fb923c', fontSize: 10, fontWeight: 700 }}>RRR {rrr}</span>
              </div>
            )}
          </div>
        )}

        {/* Batsmen */}
        {batsmen.length > 0 && (
          <div style={{
            background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: '8px 10px', marginBottom: 8,
            border: '1px solid rgba(255,255,255,0.05)',
          }}>
            <p style={{ color: '#8A9096', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 6 }}>
              BATTING
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto auto auto', columnGap: 6, rowGap: 3, alignItems: 'center' }}>
              {batsmen.slice(0, 2).map((b, i) => (
                <React.Fragment key={i}>
                  <span style={{ color: '#8A9096', fontSize: 9 }}>{i === 0 ? '*' : ' '}</span>
                  <span style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {b.name?.split(' ').slice(-1)[0]}
                  </span>
                  <span style={{ color: '#C6A052', fontSize: 12, fontWeight: 800 }}>{b.runs}</span>
                  <span style={{ color: '#8A9096', fontSize: 10 }}>({b.balls_faced})</span>
                  <span style={{ color: '#4ade80', fontSize: 9 }}>SR {b.strike_rate}</span>
                </React.Fragment>
              ))}
            </div>
          </div>
        )}

        {/* Current bowler */}
        {bowlers.length > 0 && (
          <div style={{
            background: 'rgba(255,255,255,0.03)', borderRadius: 10, padding: '8px 10px', marginBottom: 8,
            border: '1px solid rgba(255,255,255,0.05)',
          }}>
            <p style={{ color: '#8A9096', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 5 }}>
              BOWLING
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: '#e2e8f0', fontSize: 11, fontWeight: 600, flex: 1 }}>
                {bowlers[0].name?.split(' ').slice(-1)[0]}
              </span>
              <span style={{ color: '#BFC3C8', fontSize: 10 }}>{bowlers[0].overs} ov</span>
              <span style={{ color: '#fb7185', fontSize: 11, fontWeight: 700 }}>{bowlers[0].wickets}W</span>
              <span style={{ color: '#8A9096', fontSize: 10 }}>{bowlers[0].runs_conceded} runs</span>
              <span style={{ color: '#fb923c', fontSize: 9, fontWeight: 700 }}>E:{bowlers[0].econ}</span>
            </div>
          </div>
        )}

        {/* Ball-by-ball ticker */}
        {recentBalls.length > 0 && (
          <div style={{ marginBottom: 10 }}>
            <p style={{ color: '#8A9096', fontSize: 9, fontWeight: 700, letterSpacing: '0.06em', marginBottom: 6 }}>
              THIS OVER
            </p>
            <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
              {recentBalls.map((ball, i) => (
                <BallDot key={i} ball={ball} idx={i} />
              ))}
            </div>
          </div>
        )}

        {/* Bottom CTA */}
        <div style={{
          marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255,255,255,0.05)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Target size={12} style={{ color: '#C6A052' }} />
            <span style={{ color: '#8A9096', fontSize: 10 }}>Tap to predict · Free · +15 coins</span>
          </div>
          <span style={{ color: '#C6A052', fontSize: 10, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 2 }}>
            Open <ChevronRight size={11} />
          </span>
        </div>
      </div>
    </motion.div>
  );
}
