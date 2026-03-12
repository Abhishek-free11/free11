import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Gift, Target, X, ShoppingBag } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import api from '../utils/api';

export default function WishlistGoal({ coinsBalance }) {
  const navigate = useNavigate();
  const [goal, setGoal] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.v2GetWishlist()
      .then(r => setGoal(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [coinsBalance]); // re-fetch when balance changes so progress is live

  const handleUnpin = async () => {
    await api.v2UnpinWishlist().catch(() => {});
    setGoal({ pinned: false, product: null });
    toast.success('Goal cleared');
  };

  if (loading) return null;

  // If no goal pinned, show a soft CTA
  if (!goal?.pinned) {
    return (
      <div
        className="flex items-center justify-between p-3 bg-slate-800/60 border border-dashed border-slate-700 rounded-xl cursor-pointer hover:border-yellow-500/50 transition-colors"
        onClick={() => navigate('/shop')}
        data-testid="wishlist-empty-cta"
      >
        <div className="flex items-center gap-2">
          <Gift className="h-4 w-4 text-yellow-500 flex-shrink-0" />
          <span className="text-sm text-slate-400">Set a reward goal — track your progress here</span>
        </div>
        <ShoppingBag className="h-4 w-4 text-slate-500" />
      </div>
    );
  }

  const { product, progress, coins_needed } = goal;
  const canRedeem = coins_needed === 0;

  return (
    <div className="bg-gradient-to-r from-yellow-500/10 to-amber-500/5 border border-yellow-500/30 rounded-xl p-3" data-testid="wishlist-goal">
      <div className="flex items-center gap-3">
        {/* Product image */}
        <img
          src={product.image_url}
          alt={product.name}
          className="w-12 h-12 rounded-lg object-cover border border-yellow-500/20 flex-shrink-0"
          onError={e => (e.target.src = 'https://via.placeholder.com/48')}
        />

        {/* Info + bar */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold text-white truncate pr-2">{product.name}</p>
            <button onClick={handleUnpin} className="text-slate-600 hover:text-slate-400 flex-shrink-0" data-testid="unpin-wishlist-btn">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden mb-1">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                canRedeem
                  ? 'bg-gradient-to-r from-green-400 to-emerald-300 animate-pulse'
                  : 'bg-gradient-to-r from-yellow-500 to-amber-400'
              }`}
              style={{ width: `${Math.min(progress, 100)}%` }}
              data-testid="wishlist-progress-bar"
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[10px] text-slate-400">{Math.round(progress)}% saved</span>
            {canRedeem ? (
              <Button
                size="sm"
                className="h-5 px-2 text-[10px] bg-green-500 hover:bg-green-600 text-white"
                onClick={() => navigate('/shop')}
                data-testid="wishlist-redeem-btn"
              >
                Redeem now!
              </Button>
            ) : (
              <span className="text-[10px] text-yellow-400 font-medium">{coins_needed} coins to go</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
