import { useRef, useState } from 'react';
import { toPng } from 'html-to-image';
import { toast } from 'sonner';
import { Share2, X, Download } from 'lucide-react';

/**
 * SharePredictionCard — Section 8
 * Renders a branded card as a DOM element, converts to PNG via html-to-image,
 * then opens native share / fallback to download.
 *
 * Props:
 *   match  { team1, team2, match_id, series }
 *   prediction  { prediction_type, prediction_value, is_correct, coins_earned }
 *   user   { name }
 *   onClose  () => void
 */

const WHATSAPP_GREEN = '#25D366';
const TWITTER_BLUE  = '#1DA1F2';

export default function SharePredictionCard({ match, prediction, user, onClose }) {
  const cardRef = useRef(null);
  const [generating, setGenerating] = useState(false);

  const matchLink = `${window.location.origin}/match/${match?.match_id}`;
  const shortDesc = prediction?.prediction_type?.replace(/_/g, ' ') || 'Prediction';
  const predValue = String(prediction?.prediction_value || '');
  const isWin = prediction?.is_correct === true;

  const generateImage = async () => {
    if (!cardRef.current) return null;
    setGenerating(true);
    try {
      const dataUrl = await toPng(cardRef.current, { cacheBust: true, pixelRatio: 2 });
      return dataUrl;
    } finally {
      setGenerating(false);
    }
  };

  const handleWhatsApp = async () => {
    const text = `${isWin ? '🏆 I nailed it!' : '🏏 I predicted'} "${shortDesc}: ${predValue}" for ${match?.team1} vs ${match?.team2} on FREE11!\n\nJoin me → ${matchLink}`;
    window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`, '_blank');
    toast.success('Opening WhatsApp...');
  };

  const handleTwitter = async () => {
    const text = `${isWin ? '🏆 Called it!' : '🏏 My prediction:'} ${shortDesc}: ${predValue} — ${match?.team1} vs ${match?.team2} on @FREE11app!\n${matchLink}`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, '_blank');
    toast.success('Opening Twitter/X...');
  };

  const handleInstagram = async () => {
    const dataUrl = await generateImage();
    if (!dataUrl) { toast.error('Failed to generate image'); return; }
    // Instagram doesn't support direct share URL; copy link + download image
    await navigator.clipboard.writeText(matchLink).catch(() => {});
    const link = document.createElement('a');
    link.download = `free11-prediction-${match?.match_id}.png`;
    link.href = dataUrl;
    link.click();
    toast.success('Image downloaded + link copied! Open Instagram and share.');
  };

  const handleDownload = async () => {
    const dataUrl = await generateImage();
    if (!dataUrl) { toast.error('Failed to generate'); return; }
    const link = document.createElement('a');
    link.download = `free11-prediction.png`;
    link.href = dataUrl;
    link.click();
    toast.success('Card downloaded!');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center" data-testid="share-modal">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-md mx-4 mb-4 z-10">
        {/* Close */}
        <button onClick={onClose} className="absolute -top-10 right-0 p-2 text-white/60 hover:text-white">
          <X className="w-5 h-5" />
        </button>

        {/* The shareable card (will be captured as PNG) */}
        <div
          ref={cardRef}
          className="bg-[#0a0e17] border border-yellow-500/30 rounded-2xl p-5 overflow-hidden"
          style={{ fontFamily: 'system-ui, sans-serif' }}
          data-testid="share-card"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-yellow-500 flex items-center justify-center font-black text-black text-sm">F</div>
              <span className="font-black text-white text-lg tracking-tight">FREE<span className="text-yellow-400">11</span></span>
            </div>
            <span className="text-xs text-slate-500">{new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
          </div>

          {/* Match */}
          <div className="bg-white/5 rounded-xl px-4 py-2 mb-3 text-center">
            <p className="text-xs text-slate-400 mb-0.5">{match?.series || 'Cricket Match'}</p>
            <p className="font-bold text-white text-sm">{match?.team1} <span className="text-slate-500">vs</span> {match?.team2}</p>
          </div>

          {/* Prediction */}
          <div className={`rounded-xl p-3 mb-3 border ${isWin ? 'bg-green-500/10 border-green-500/30' : 'bg-yellow-500/10 border-yellow-500/30'}`}>
            <p className="text-xs text-slate-400 capitalize mb-1">{shortDesc}</p>
            <p className="text-xl font-black text-white">{predValue}</p>
            {isWin && <p className="text-green-400 text-xs font-bold mt-1">✓ Correct Prediction!</p>}
          </div>

          {/* User + CTA */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-500">Predicted by</p>
              <p className="text-sm font-bold text-white">{user?.name || 'A Cricket Fan'}</p>
            </div>
            <div className="text-right">
              <p className="text-[10px] text-slate-600">free11.com</p>
              <p className="text-[10px] text-yellow-500 font-medium">Predict. Earn. Win.</p>
            </div>
          </div>
        </div>

        {/* Share Buttons */}
        <div className="mt-3 grid grid-cols-2 gap-2">
          <button
            onClick={handleWhatsApp}
            className="flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-white text-sm transition-opacity hover:opacity-90 active:scale-95"
            style={{ backgroundColor: WHATSAPP_GREEN }}
            data-testid="share-whatsapp"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
            </svg>
            WhatsApp
          </button>

          <button
            onClick={handleTwitter}
            className="flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-white text-sm transition-opacity hover:opacity-90 active:scale-95"
            style={{ backgroundColor: TWITTER_BLUE }}
            data-testid="share-twitter"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.747l7.73-8.835L1.254 2.25H8.08l4.253 5.622L18.244 2.25zm-1.161 17.52h1.833L7.084 4.126H5.117L17.083 19.77z"/>
            </svg>
            Twitter/X
          </button>

          <button
            onClick={handleInstagram}
            className="flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-white text-sm bg-gradient-to-r from-purple-600 to-pink-500 hover:opacity-90 active:scale-95 transition-opacity"
            data-testid="share-instagram"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
            </svg>
            Instagram
          </button>

          <button
            onClick={handleDownload}
            disabled={generating}
            className="flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-white text-sm bg-white/10 hover:bg-white/15 active:scale-95 transition-all"
            data-testid="share-download"
          >
            <Download className="w-4 h-4" />
            {generating ? 'Generating...' : 'Download'}
          </button>
        </div>
      </div>
    </div>
  );
}
