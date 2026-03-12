import { useState, useEffect, useRef } from 'react';
import { Users } from 'lucide-react';
import api from '../utils/api';

const TYPE_LABELS = {
  over_runs: 'Runs this over',
  over_wicket: 'Wicket this over?',
  over_boundary: 'Boundary this over?',
  match_winner: 'Match winner',
  match_total: 'Match total',
  milestone_team_score: 'Team score at 6 overs',
  milestone_powerplay: 'Powerplay wickets',
};

const OPTION_COLORS = [
  'bg-blue-500',
  'bg-green-500',
  'bg-yellow-500',
  'bg-red-500',
  'bg-purple-500',
  'bg-teal-500',
];

export default function CrowdMeter({ matchId, isLive }) {
  const [meter, setMeter] = useState(null);
  const intervalRef = useRef(null);

  const fetchMeter = async () => {
    try {
      const r = await api.v2GetCrowdMeter(matchId);
      if (r.data?.meter && Object.keys(r.data.meter).length > 0) {
        setMeter(r.data);
      }
    } catch {}
  };

  useEffect(() => {
    fetchMeter();
    if (isLive) {
      intervalRef.current = setInterval(fetchMeter, 10000); // 10s for live
    }
    return () => clearInterval(intervalRef.current);
  }, [matchId, isLive]);

  if (!meter || !Object.keys(meter.meter).length) return null;

  return (
    <div className="bg-slate-900/80 border border-slate-700/50 rounded-xl p-4" data-testid="crowd-meter">
      <div className="flex items-center gap-2 mb-3">
        <Users className="h-4 w-4 text-blue-400" />
        <span className="text-sm font-semibold text-white">Crowd Predictions</span>
        {isLive && (
          <span className="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded-full animate-pulse">LIVE</span>
        )}
      </div>

      <div className="space-y-4">
        {Object.entries(meter.meter).map(([type, data]) => (
          <div key={type} data-testid={`crowd-${type}`}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-slate-400">{TYPE_LABELS[type] || type}</span>
              <span className="text-xs text-slate-500">{data.total_predictions} predictions</span>
            </div>
            <div className="space-y-1.5">
              {Object.entries(data.options).map(([option, stats], idx) => (
                <div key={option}>
                  <div className="flex items-center justify-between text-xs mb-0.5">
                    <span className="text-slate-300 truncate flex-1 pr-2">{option}</span>
                    <span className="font-bold text-white flex-shrink-0">{stats.pct}%</span>
                  </div>
                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-700 ${OPTION_COLORS[idx % OPTION_COLORS.length]}`}
                      style={{ width: `${stats.pct}%`, opacity: 0.75 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
