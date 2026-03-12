import { useState, useEffect } from 'react';
import { Coins, Brain, CheckCircle, XCircle, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import api from '../utils/api';

export default function DailyPuzzle({ onCoinsEarned }) {
  const [puzzle, setPuzzle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.v2GetTodayPuzzle()
      .then(r => {
        setPuzzle(r.data);
        if (r.data.already_answered) {
          setResult(r.data.previous_result);
          setSelected(r.data.previous_answer);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleAnswer = async (option) => {
    if (result || submitting) return;
    setSelected(option);
    setSubmitting(true);
    try {
      const r = await api.v2AnswerPuzzle(option);
      setResult(r.data);
      if (r.data.is_correct && r.data.coins_earned > 0) {
        toast.success(`Correct! +${r.data.coins_earned} FREE Coins`, { description: r.data.explanation });
        onCoinsEarned?.(r.data.coins_earned);
      } else if (r.data.is_correct) {
        toast.success('Correct!', { description: r.data.explanation });
      } else {
        toast.error('Not quite!', { description: `Answer: ${r.data.correct_answer}` });
      }
    } catch {
      toast.error('Could not submit. Try again.');
      setSelected(null);
    }
    setSubmitting(false);
  };

  if (loading) return null;
  if (!puzzle) return null;

  const answered = !!result;

  return (
    <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl p-4" data-testid="daily-puzzle">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-purple-400" />
          <span className="text-sm font-semibold text-white">Daily Cricket Puzzle</span>
        </div>
        <div className="flex items-center gap-1 text-xs text-slate-400">
          <Coins className="h-3 w-3 text-yellow-400" />
          <span>Win up to <span className="text-yellow-400 font-bold">{puzzle.first_100_reward}</span> coins</span>
        </div>
      </div>

      {/* Question */}
      <p className="text-sm text-slate-200 mb-3 leading-relaxed">{puzzle.question}</p>

      {/* Options */}
      <div className="grid grid-cols-1 gap-2">
        {puzzle.options?.map(option => {
          const isSelected = selected === option;
          const isCorrect = result && option === result.correct_answer;
          const isWrong = result && isSelected && !result.is_correct;

          let cls = 'w-full text-left px-3 py-2 rounded-lg text-sm border transition-all ';
          if (isCorrect && answered) {
            cls += 'bg-green-500/20 border-green-500/60 text-green-300';
          } else if (isWrong) {
            cls += 'bg-red-500/20 border-red-500/60 text-red-300';
          } else if (isSelected && !answered) {
            cls += 'bg-purple-500/20 border-purple-500/60 text-purple-300';
          } else {
            cls += 'bg-slate-800/50 border-slate-700/50 text-slate-300 hover:border-purple-500/40 hover:bg-purple-500/10';
          }

          return (
            <button
              key={option}
              className={cls}
              onClick={() => handleAnswer(option)}
              disabled={answered || submitting}
              data-testid={`puzzle-option-${option.replace(/\s+/g, '-').toLowerCase()}`}
            >
              <span className="flex items-center gap-2">
                {isCorrect && answered && <CheckCircle className="h-3.5 w-3.5 text-green-400 flex-shrink-0" />}
                {isWrong && <XCircle className="h-3.5 w-3.5 text-red-400 flex-shrink-0" />}
                {option}
              </span>
            </button>
          );
        })}
      </div>

      {/* Result */}
      {result && (
        <div className={`mt-3 p-2.5 rounded-lg text-xs ${result.is_correct ? 'bg-green-500/10 border border-green-500/30 text-green-300' : 'bg-slate-800/60 border border-slate-700/50 text-slate-400'}`} data-testid="puzzle-result">
          {result.is_correct && result.coins_earned > 0 && (
            <div className="flex items-center gap-1 mb-1 font-semibold text-yellow-400">
              <Coins className="h-3 w-3" /> +{result.coins_earned} coins earned!
            </div>
          )}
          <p>{result.explanation}</p>
          <p className="mt-1 text-slate-500 flex items-center gap-1">
            <Clock className="h-2.5 w-2.5" /> New puzzle tomorrow
          </p>
        </div>
      )}
    </div>
  );
}
