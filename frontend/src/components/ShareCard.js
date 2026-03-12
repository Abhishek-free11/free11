import { useRef } from 'react';
import { Share2, Trophy, Coins, Zap, IndianRupee, Star } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

// ShareCard — auto-generated after redemption / quest completion / leaderboard win
// Section 4 — Distribution Engine
export default function ShareCard({ type = 'redemption', data = {}, onClose }) {
  const cardRef = useRef(null);

  // ₹ value: conservative ₹0.80 per coin
  const rupeeValue = data.coinsUsed ? Math.round(data.coinsUsed * 0.8) : null;

  const configs = {
    redemption: {
      headline: rupeeValue ? `I saved ₹${rupeeValue} — FREE!` : 'I redeemed for FREE!',
      subline: data.productName || 'Grocery reward',
      detail: `${data.coinsUsed || 0} FREE Coins · earned through cricket skill predictions`,
      color: '#C6A052',
      icon: Coins,
      badge: 'REDEEMED FREE',
      valueChip: rupeeValue ? `≈ ₹${rupeeValue} saved` : null,
    },
    quest: {
      headline: 'Quest Complete!',
      subline: `+${data.coinsEarned || 20} FREE Coins earned`,
      detail: 'Skill prediction → earn → redeem real groceries',
      color: '#4ade80',
      icon: Zap,
      badge: 'QUEST WIN',
      valueChip: null,
    },
    leaderboard: {
      headline: `Rank #${data.rank || 1} — India's Best!`,
      subline: `${data.accuracy || 0}% prediction accuracy`,
      detail: 'Skill-based cricket predictions · FREE11 leaderboard',
      color: '#E0B84F',
      icon: Trophy,
      badge: 'TOP PREDICTOR',
      valueChip: null,
    },
  };

  const config = configs[type] || configs.redemption;
  const Icon = config.icon;

  const shareText = type === 'redemption'
    ? `🏏 Just redeemed ${data.productName || 'a reward'} for FREE on FREE11!\n\nI earned ${data.coinsUsed || 0} coins by predicting cricket correctly — no money needed.\n\nJoin me 👉 https://free11.com`
    : `${config.headline} — ${config.subline}\n\nPlay Cricket. Earn Essentials. No deposits.\nhttps://free11.com`;

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({ title: 'FREE11 — Play Cricket. Earn Essentials.', text: shareText, url: 'https://free11.com' });
      } else {
        await navigator.clipboard.writeText(shareText);
        toast.success('Share text copied!');
      }
    } catch {}
  };

  return (
    <motion.div
      className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.88)' }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      data-testid="share-card-modal"
    >
      <motion.div
        className="w-full max-w-sm mx-4 mb-4 sm:mb-0"
        initial={{ y: 60, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ type: 'spring', damping: 22, stiffness: 300 }}
      >
        {/* The shareable card */}
        <div
          ref={cardRef}
          className="rounded-2xl overflow-hidden mb-3"
          style={{ background: 'linear-gradient(160deg, #12151a 0%, #1B1E23 100%)', border: `1px solid ${config.color}50`, boxShadow: `0 0 40px ${config.color}15` }}
        >
          {/* Top accent bar */}
          <div className="h-1 w-full" style={{ background: `linear-gradient(90deg, ${config.color}, ${config.color}44)` }} />

          {/* Header row */}
          <div className="flex items-center justify-between px-4 pt-3 pb-2">
            <div className="flex items-center gap-1.5">
              <img src="/free11_icon_192.png" alt="FREE11" className="h-5 w-5 rounded-md" />
              <span className="text-sm font-black tracking-widest" style={{ color: config.color, fontFamily: 'Bebas Neue, sans-serif' }}>FREE11</span>
            </div>
            <span className="text-[10px] px-2.5 py-0.5 rounded-full font-bold tracking-wider"
              style={{ background: `${config.color}20`, color: config.color, border: `1px solid ${config.color}30` }}>
              {config.badge}
            </span>
          </div>

          <div className="px-4 pb-4">
            {/* Product image + icon row */}
            <div className="flex items-start gap-3 mb-3">
              {data.imageUrl ? (
                <div className="w-16 h-16 rounded-xl overflow-hidden flex-shrink-0 border"
                  style={{ borderColor: `${config.color}30` }}>
                  <img src={data.imageUrl} alt={data.productName} className="w-full h-full object-cover" />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-xl flex items-center justify-center flex-shrink-0"
                  style={{ background: `${config.color}12`, border: `1px solid ${config.color}25` }}>
                  <Icon className="w-8 h-8" style={{ color: config.color }} />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <h2 className="text-xl font-black text-white leading-tight"
                  style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.04em' }}>
                  {config.headline}
                </h2>
                <p className="text-sm font-semibold mt-0.5 truncate" style={{ color: config.color }}>
                  {config.subline}
                </p>
                {config.valueChip && (
                  <span className="inline-flex items-center gap-1 text-xs mt-1 px-2 py-0.5 rounded-full font-bold"
                    style={{ background: 'rgba(74,222,128,0.12)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.25)' }}>
                    <IndianRupee className="w-2.5 h-2.5" />{config.valueChip.replace('≈ ₹', '')} saved
                  </span>
                )}
              </div>
            </div>

            <p className="text-xs mb-3" style={{ color: '#8A9096' }}>{config.detail}</p>

            {/* Receipt-style detail for redemptions */}
            {type === 'redemption' && (
              <div className="rounded-xl p-2.5 mb-3 flex items-center justify-between"
                style={{ background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.07)' }}>
                <div className="flex items-center gap-1.5">
                  <Coins className="w-3.5 h-3.5" style={{ color: '#C6A052' }} />
                  <span className="text-xs" style={{ color: '#BFC3C8' }}>{data.coinsUsed || 0} coins redeemed</span>
                </div>
                <div className="flex items-center gap-0.5">
                  <Star className="w-3 h-3 fill-current" style={{ color: '#C6A052' }} />
                  <Star className="w-3 h-3 fill-current" style={{ color: '#C6A052' }} />
                  <Star className="w-3 h-3 fill-current" style={{ color: '#C6A052' }} />
                  <span className="text-[10px] ml-1" style={{ color: '#8A9096' }}>Skill-earned</span>
                </div>
              </div>
            )}

            {/* CTA tagline */}
            <div className="p-2.5 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <p className="text-xs font-bold text-white">Play Cricket. Earn Essentials.</p>
              <p className="text-[10px] mt-0.5" style={{ color: '#8A9096' }}>free11.com · No deposits · Skill-based · Online Gaming Act compliant</p>
            </div>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleShare}
            className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold"
            style={{ background: `linear-gradient(135deg, ${config.color}, ${config.color}cc)`, color: '#0F1115' }}
            data-testid="share-card-share-btn"
          >
            <Share2 className="w-4 h-4" />
            Share with Friends
          </button>
          <button
            onClick={onClose}
            className="px-4 py-3 rounded-xl text-sm"
            style={{ background: 'rgba(255,255,255,0.06)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.08)' }}
            data-testid="share-card-close"
          >
            Close
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}
