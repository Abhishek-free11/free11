import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import { toast } from 'sonner';
import { X, Zap, ShoppingBag, Play, ChevronRight, Clock, Tag } from 'lucide-react';
import SkillDisclaimerModal, { SkillBadge } from './SkillDisclaimerModal';
import ShareCard from './ShareCard';
import { AnimatePresence } from 'framer-motion';

// Quest Modal — Rebound Quest (opt-in only, no locks, no stakes)
// Triggers after prediction loss when streak < 3
export default function QuestModal({ onDismiss }) {
  const navigate = useNavigate();
  const [questSession, setQuestSession] = useState(null);
  const [rationData, setRationData] = useState(null);
  const [view, setView] = useState('menu'); // menu | ration_tease
  const [loading, setLoading] = useState(false);
  const [adLoading, setAdLoading] = useState(false);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [showShareCard, setShowShareCard] = useState(false);
  const [coinsEarned, setCoinsEarned] = useState(20);

  useEffect(() => {
    initQuest();
  }, []);

  const initQuest = async () => {
    try {
      const { data } = await api.v2QuestOffer();
      setQuestSession(data);
    } catch {}
  };

  const handleAdPath = async () => {
    if (!questSession?.id || adLoading) return;
    setAdLoading(true);
    try {
      const adRes = await api.v2ClaimAdMobReward({ reward_type: 'quest_rebound' });
      await api.v2QuestClaimAd(questSession.id);
      const earned = adRes.data.reward_coins || 20;
      setCoinsEarned(earned);
      toast.success(`+${earned} coins earned!`);
      setShowShareCard(true);
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Ad not available right now';
      toast.error(msg);
    } finally {
      setAdLoading(false);
    }
  };

  const handleRationPath = async () => {
    if (!questSession?.id || loading) return;
    setLoading(true);
    try {
      const [teaseRes] = await Promise.all([
        api.v2RouterTease('cola_2l', 'MH'),
        api.v2QuestRationViewed(questSession.id),
      ]);
      setRationData(teaseRes.data);
      setView('ration_tease');
    } catch {
      toast.error('Could not load deals right now');
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = async () => {
    if (questSession?.id) {
      api.v2QuestDismiss(questSession.id).catch(() => {});
    }
    onDismiss?.();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center sm:items-center"
      style={{ background: 'rgba(0,0,0,0.85)' }}
      data-testid="quest-modal"
    >
      <div
        className="w-full max-w-sm mx-4 mb-4 sm:mb-0 rounded-2xl overflow-hidden"
        style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.35)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 pt-4 pb-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: 'rgba(198,160,82,0.15)' }}>
              <Zap className="w-4 h-4" style={{ color: '#C6A052' }} />
            </div>
            <div>
              <p className="text-sm font-bold" style={{ color: '#C6A052', fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.05em' }}>REBOUND QUEST</p>
              <p className="text-xs" style={{ color: '#8A9096' }}>Skill fun — no stakes, sponsored perks only</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowDisclaimer(true)} data-testid="quest-skill-badge">
              <SkillBadge />
            </button>
            <button onClick={handleDismiss} className="p-1 rounded-lg" style={{ color: '#8A9096' }} data-testid="quest-modal-dismiss">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {view === 'menu' && (
          <div className="px-4 pb-5">
            <p className="text-base font-bold text-white mt-1 mb-3">Streak reset? Bounce back!</p>
            <p className="text-xs mb-4" style={{ color: '#8A9096' }}>
              Pick a path below. Both are optional — no obligation, no lock-in.
            </p>

            {/* Path A — Ad */}
            <button
              onClick={handleAdPath}
              disabled={adLoading}
              className="w-full flex items-center gap-3 p-3 rounded-xl mb-3 transition-all hover:scale-[1.01] active:scale-[0.99]"
              style={{ background: 'rgba(198,160,82,0.1)', border: '1px solid rgba(198,160,82,0.3)' }}
              data-testid="quest-ad-path"
            >
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(198,160,82,0.15)' }}>
                <Play className="w-5 h-5" style={{ color: '#C6A052' }} />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-bold text-white">{adLoading ? 'Loading ad...' : 'Watch Short Ad'}</p>
                <p className="text-xs" style={{ color: '#8A9096' }}>30 seconds → earn +20 Free Coins</p>
              </div>
              <span className="text-xs font-bold px-2 py-1 rounded-full" style={{ background: 'rgba(198,160,82,0.2)', color: '#C6A052' }}>+20</span>
            </button>

            {/* Path B — Ration Tease */}
            <button
              onClick={handleRationPath}
              disabled={loading}
              className="w-full flex items-center gap-3 p-3 rounded-xl mb-4 transition-all hover:scale-[1.01] active:scale-[0.99]"
              style={{ background: 'rgba(74,222,128,0.08)', border: '1px solid rgba(74,222,128,0.25)' }}
              data-testid="quest-ration-path"
            >
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(74,222,128,0.1)' }}>
                <ShoppingBag className="w-5 h-5" style={{ color: '#4ade80' }} />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-bold text-white">{loading ? 'Checking deals...' : 'See Ration Deal'}</p>
                <p className="text-xs" style={{ color: '#8A9096' }}>Best grocery deal near you via Router</p>
              </div>
              <ChevronRight className="w-4 h-4" style={{ color: '#4ade80' }} />
            </button>

            <p className="text-center text-xs" style={{ color: '#8A9096' }}>
              Online Gaming Act, 2025 compliant — skill fun only. No cash, no deposits.
            </p>
          </div>
        )}

        {view === 'ration_tease' && rationData && (
          <RouterTeaseView rationData={rationData} onDismiss={handleDismiss} navigate={navigate} />
        )}
      </div>

      <SkillDisclaimerModal isOpen={showDisclaimer} onClose={() => setShowDisclaimer(false)} />
      <AnimatePresence>
        {showShareCard && (
          <ShareCard
            type="quest"
            data={{ coinsEarned }}
            onClose={() => { setShowShareCard(false); onDismiss?.(); }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function RouterTeaseView({ rationData, onDismiss, navigate }) {
  const best = rationData.best;
  if (!best) return null;

  return (
    <div className="px-4 pb-5">
      <p className="text-sm font-bold text-white mt-1 mb-1">Best deal found!</p>
      <p className="text-xs mb-3" style={{ color: '#8A9096' }}>Powered by FREE11 Router — scored for speed, savings & your location</p>

      <div className="rounded-xl overflow-hidden mb-3" style={{ border: '1px solid rgba(74,222,128,0.25)', background: 'rgba(74,222,128,0.05)' }}>
        <img src={best.image} alt={best.sku_name} className="w-full h-28 object-cover" />
        <div className="p-3">
          <div className="flex items-start justify-between mb-1">
            <p className="text-sm font-bold text-white">{best.sku_name}</p>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ background: 'rgba(74,222,128,0.2)', color: '#4ade80' }}>{best.badge}</span>
          </div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-lg font-bold" style={{ color: '#C6A052', fontFamily: 'Oswald, sans-serif' }}>₹{best.discounted_price}</span>
            <span className="text-xs line-through" style={{ color: '#8A9096' }}>₹{best.mrp}</span>
            <span className="text-xs font-bold" style={{ color: '#4ade80' }}>Save ₹{best.savings}</span>
          </div>
          <div className="flex items-center gap-3 text-xs" style={{ color: '#8A9096' }}>
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{best.eta_minutes} min</span>
            <span className="flex items-center gap-1"><Tag className="w-3 h-3" />{best.discount_pct}% off</span>
            <span className="flex items-center gap-1"><ChevronRight className="w-3 h-3" />{best.provider_name}</span>
          </div>
        </div>
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => { onDismiss(); navigate('/shop'); }}
          className="flex-1 py-2.5 rounded-xl text-sm font-bold transition-all"
          style={{ background: 'rgba(198,160,82,0.15)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.3)' }}
          data-testid="quest-shop-cta"
        >
          Shop Now
        </button>
        <button
          onClick={onDismiss}
          className="px-4 py-2.5 rounded-xl text-sm"
          style={{ background: 'rgba(255,255,255,0.05)', color: '#8A9096' }}
        >
          Later
        </button>
      </div>

      <p className="text-center text-xs mt-3" style={{ color: '#8A9096' }}>
        Prices indicative. Availability varies by location. Sponsored perks — Online Gaming Act, 2025 compliant.
      </p>
    </div>
  );
}
