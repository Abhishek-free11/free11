import { useState, useEffect } from 'react';
import { X, TrendingUp, TrendingDown, Minus, Trophy, Target, Coins, Share2, Calendar } from 'lucide-react';
import { Button } from './ui/button';
import api from '../utils/api';

export default function WeeklyReportCard({ onDismiss }) {
  const [report, setReport] = useState(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    api.v2GetWeeklyReport()
      .then(r => {
        if (r.data?.is_new && r.data?.predictions_total > 0) {
          setReport(r.data);
          setVisible(true);
        }
      })
      .catch(() => {});
  }, []);

  const handleDismiss = async () => {
    setVisible(false);
    await api.v2DismissWeeklyReport().catch(() => {});
    onDismiss?.();
  };

  if (!visible || !report) return null;

  const rankDelta = report.rank_change;
  const RankIcon = rankDelta > 0 ? TrendingUp : rankDelta < 0 ? TrendingDown : Minus;
  const rankColor = rankDelta > 0 ? 'text-green-400' : rankDelta < 0 ? 'text-red-400' : 'text-slate-400';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm" data-testid="weekly-report-modal">
      <div className="bg-gradient-to-b from-slate-800 to-slate-900 border border-slate-700 rounded-2xl p-5 w-full max-w-sm shadow-2xl">

        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-yellow-400" />
            <span className="text-base font-bold text-white">Your Weekly Report</span>
          </div>
          <button onClick={handleDismiss} className="text-slate-500 hover:text-slate-300" data-testid="dismiss-report-btn">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Week label */}
        <p className="text-xs text-slate-500 mb-4">
          Week of {new Date(report.week_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </p>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-800/80 rounded-xl p-3 text-center">
            <div className="text-2xl font-black text-yellow-400">{report.accuracy}%</div>
            <div className="text-xs text-slate-400 flex items-center justify-center gap-1 mt-0.5">
              <Target className="h-3 w-3" /> Accuracy
            </div>
          </div>

          <div className="bg-slate-800/80 rounded-xl p-3 text-center">
            <div className={`text-2xl font-black flex items-center justify-center gap-1 ${rankColor}`}>
              <RankIcon className="h-5 w-5" />
              {rankDelta > 0 ? `+${rankDelta}` : rankDelta === 0 ? '—' : rankDelta}
            </div>
            <div className="text-xs text-slate-400 mt-0.5">Rank Change</div>
          </div>

          <div className="bg-slate-800/80 rounded-xl p-3 text-center">
            <div className="text-2xl font-black text-green-400">{report.predictions_total}</div>
            <div className="text-xs text-slate-400 mt-0.5">Predictions Made</div>
          </div>

          <div className="bg-slate-800/80 rounded-xl p-3 text-center">
            <div className="text-2xl font-black text-purple-400">{report.contests_joined}</div>
            <div className="text-xs text-slate-400 flex items-center justify-center gap-1 mt-0.5">
              <Trophy className="h-3 w-3" /> Contests
            </div>
          </div>
        </div>

        {/* Coins earned banner */}
        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-3 mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Coins className="h-5 w-5 text-yellow-400" />
            <span className="text-sm text-slate-300">Coins earned this week</span>
          </div>
          <span className="text-xl font-black text-yellow-400" data-testid="weekly-coins">{report.coins_earned_this_week}</span>
        </div>

        {/* Current rank */}
        <p className="text-center text-xs text-slate-500 mb-4">
          You are currently ranked <span className="text-white font-bold">#{report.rank}</span> globally
        </p>

        {/* Actions */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 border-slate-700 text-slate-300 text-xs"
            onClick={handleDismiss}
            data-testid="close-report-btn"
          >
            Close
          </Button>
          <Button
            size="sm"
            className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black text-xs font-bold"
            onClick={() => { window.location.href = '/predict'; }}
            data-testid="keep-predicting-btn"
          >
            Keep predicting!
          </Button>
        </div>
      </div>
    </div>
  );
}
