import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import api from '../utils/api';
import { toast } from 'sonner';
import { Trophy, Users, Coins, ChevronRight, Zap, Crown, Medal, Target, ArrowLeft, Star } from 'lucide-react';
import SkillDisclaimerModal, { SkillBadge } from '../components/SkillDisclaimerModal';

const BRAND_COLORS = {
  pepsi:    { bg: '#1a3a6b', accent: '#00a0e9' },
  parle:    { bg: '#1a0a00', accent: '#C6A052' },
  fortune:  { bg: '#0a1a00', accent: '#4ade80' },
  default:  { bg: '#1B1E23', accent: '#C6A052' },
};

function PoolCard({ pool, user, onJoin }) {
  const brand = BRAND_COLORS[pool.brand_logo] || BRAND_COLORS.default;
  const fill = pool.max_participants > 0 ? Math.min(100, (pool.current_participants / pool.max_participants) * 100) : 0;
  const joined = pool.participants?.includes(user?.id);

  return (
    <div
      className="rounded-2xl overflow-hidden mb-3"
      style={{ border: `1px solid ${pool.accent || brand.accent}40`, background: '#15181d' }}
      data-testid={`sponsored-pool-${pool.id}`}
    >
      {/* Brand Banner */}
      <div className="px-4 py-3 flex items-center justify-between" style={{ background: `${pool.banner_color || brand.bg}` }}>
        <div>
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-full mr-2"
            style={{ background: `${pool.accent || brand.accent}20`, color: pool.accent || brand.accent, border: `1px solid ${pool.accent || brand.accent}50` }}
          >
            {pool.badge}
          </span>
          <span className="text-xs" style={{ color: 'rgba(255,255,255,0.6)' }}>{pool.brand_name}</span>
        </div>
        <div className="flex items-center gap-1">
          <Coins className="w-3.5 h-3.5" style={{ color: pool.accent || '#C6A052' }} />
          <span className="text-sm font-bold font-numbers" style={{ color: pool.accent || '#C6A052' }}>
            {pool.net_prize_pool?.toLocaleString()}
          </span>
        </div>
      </div>

      <div className="p-4">
        <h3 className="text-base font-bold text-white mb-1">{pool.title}</h3>
        <p className="text-xs mb-3" style={{ color: '#8A9096' }}>{pool.description}</p>

        {/* SKU tie */}
        {pool.sku_name && (
          <div className="flex items-center gap-2 mb-3 p-2 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
            <Star className="w-3.5 h-3.5" style={{ color: pool.accent || '#C6A052' }} />
            <span className="text-xs" style={{ color: '#BFC3C8' }}>Win + redeem: <strong style={{ color: pool.accent || '#C6A052' }}>{pool.sku_name}</strong></span>
          </div>
        )}

        {/* Progress bar */}
        <div className="mb-3">
          <div className="flex justify-between text-xs mb-1" style={{ color: '#8A9096' }}>
            <span><Users className="w-3 h-3 inline mr-1" />{pool.current_participants}/{pool.max_participants} joined</span>
            <span>{Math.round(fill)}% full</span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${fill}%`, background: pool.accent || '#C6A052' }}
            />
          </div>
        </div>

        {/* Prize top 3 */}
        <div className="flex gap-2 mb-3">
          {[1, 2, 3].map(rank => {
            const coins = (pool.prize_distribution || {})[String(rank)] || 0;
            if (!coins) return null;
            return (
              <div key={rank} className="flex-1 rounded-xl p-2 text-center" style={{ background: 'rgba(255,255,255,0.04)' }}>
                {rank === 1 ? <Crown className="w-3 h-3 mx-auto mb-0.5" style={{ color: '#C6A052' }} /> :
                 rank === 2 ? <Medal className="w-3 h-3 mx-auto mb-0.5" style={{ color: '#BFC3C8' }} /> :
                              <Target className="w-3 h-3 mx-auto mb-0.5" style={{ color: '#CD7F32' }} />}
                <p className="text-xs font-bold font-numbers" style={{ color: '#E0B84F' }}>{coins}</p>
                <p className="text-xs" style={{ color: '#8A9096' }}>#{rank}</p>
              </div>
            );
          })}
        </div>

        <button
          onClick={() => onJoin(pool)}
          disabled={joined || pool.status !== 'open'}
          className="w-full py-2.5 rounded-xl text-sm font-bold transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
          style={joined
            ? { background: 'rgba(74,222,128,0.1)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.3)' }
            : { background: pool.accent || '#C6A052', color: '#0F1115' }
          }
          data-testid={`sponsored-join-${pool.id}`}
        >
          {joined ? 'Joined' : pool.status !== 'open' ? `Pool ${pool.status}` : 'Join Pool — Free'}
        </button>
      </div>

      {/* PROGA disclaimer */}
      <div className="px-4 pb-3">
        <p className="text-xs text-center" style={{ color: 'rgba(255,255,255,0.25)' }}>
          Sponsored perk — skill-based only. No deposits. No cash outs. PROGA compliant.
        </p>
      </div>
    </div>
  );
}

export default function SponsoredPools() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [pools, setPools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  useEffect(() => { fetchPools(); }, []);

  const fetchPools = async () => {
    try {
      const { data } = await api.v2GetSponsoredPools('open');
      setPools(Array.isArray(data) ? data : []);
    } catch {
      toast.error('Could not load sponsored pools');
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async (pool) => {
    try {
      await api.v2JoinSponsoredPool(pool.id);
      toast.success(`Joined "${pool.title}"!`);
      fetchPools();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Could not join');
    }
  };

  return (
    <div className="min-h-screen pb-24" style={{ background: '#0F1115' }}>
      <div className="max-w-md mx-auto px-4 pt-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate(-1)} className="p-2 rounded-xl" style={{ background: 'rgba(255,255,255,0.05)' }}>
              <ArrowLeft className="w-4 h-4 text-white" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.05em' }}>SPONSORED POOLS</h1>
              <p className="text-xs" style={{ color: '#8A9096' }}>Brand-funded prizes — predict & win rations</p>
            </div>
          </div>
          <button
            onClick={() => setShowDisclaimer(true)}
            className="flex-shrink-0"
            data-testid="sponsored-skill-badge"
          >
            <SkillBadge />
          </button>
        </div>
        <SkillDisclaimerModal isOpen={showDisclaimer} onClose={() => setShowDisclaimer(false)} />

        {/* Info banner */}
        <div className="rounded-2xl p-4 mb-5 flex items-start gap-3" style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.2)' }}>
          <Zap className="w-5 h-5 mt-0.5 flex-shrink-0" style={{ color: '#C6A052' }} />
          <div>
            <p className="text-sm font-bold text-white mb-0.5">How it works</p>
            <p className="text-xs" style={{ color: '#8A9096' }}>
              Brands fund prize pools tied to their products. Predict cricket, earn points, win coins — then redeem for that brand's product in the Shop. Free to join, zero stakes.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-16">
            <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin mx-auto mb-3" style={{ borderColor: '#C6A052', borderTopColor: 'transparent' }} />
            <p className="text-sm" style={{ color: '#8A9096' }}>Loading pools...</p>
          </div>
        ) : pools.length === 0 ? (
          <div className="text-center py-16" style={{ color: '#8A9096' }}>
            <Trophy className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No sponsored pools active right now</p>
            <p className="text-xs mt-1">Check back during cricket matches!</p>
          </div>
        ) : (
          pools.map(pool => (
            <PoolCard key={pool.id} pool={pool} user={user} onJoin={handleJoin} />
          ))
        )}
      </div>
      <Navbar />
    </div>
  );
}
