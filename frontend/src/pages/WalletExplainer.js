import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Coins, Zap } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

const S = ({ title, children }) => <div className="mb-6"><h2 className="text-base font-bold text-white mb-2">{title}</h2><div className="text-sm text-gray-300 leading-relaxed space-y-2">{children}</div></div>;

export default function WalletExplainer() {
  const navigate = useNavigate();
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold">Wallet & Currencies</h1>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-xs text-amber-400">{t('legal.english_only_notice')}</p>
        </div>
        <S title="FREE11 Currency System">
          <p>FREE11 uses two in-platform virtual currencies designed for engagement and entertainment.</p>
        </S>

        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 mb-4">
          <div className="flex items-center gap-2 mb-2">
            <Coins className="w-5 h-5 text-yellow-400" />
            <h3 className="font-bold text-yellow-400">Free Coins</h3>
          </div>
          <p className="text-sm text-gray-300 mb-2">Earned through participation and gameplay.</p>
          <ul className="text-xs text-gray-400 space-y-1">
            <li>Earned via: contests, card games, predictions, missions, streaks, spin wheel, referrals</li>
            <li>Used for: contest entry, card game entry, reward store redemption, progression</li>
            <li>Daily earning cap: 5,000 Free Coins</li>
          </ul>
        </div>

        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-emerald-400" />
            <h3 className="font-bold text-emerald-400">FREE Bucks</h3>
          </div>
          <p className="text-sm text-gray-300 mb-2">Premium currency purchased with real money.</p>
          <ul className="text-xs text-gray-400 space-y-1">
            <li>Purchased via: Razorpay (UPI, cards, net banking)</li>
            <li>Used for: power cards, premium contests, extra spins, reward discounts, faster progression</li>
            <li>Packs: ₹49 (50), ₹149 (160), ₹499 (550), ₹999 (1200)</li>
          </ul>
        </div>

        <S title="Important Information">
          <p>Free Coins and FREE Bucks:</p>
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Have no real-world monetary value</li>
            <li>Cannot be withdrawn as cash</li>
            <li>Cannot be converted to legal tender</li>
            <li>Cannot be transferred outside the platform</li>
            <li>Cannot be traded between users</li>
          </ul>
          <p>These currencies are used solely for participation and engagement within the FREE11 platform.</p>
        </S>

        <S title="Rewards">
          <p>Accumulated Free Coins can be redeemed for promotional rewards including brand vouchers, digital coupons, and merchandise from partners like Amazon, Flipkart, Swiggy, and more.</p>
          <p>Rewards are promotional incentives, subject to availability, and cannot be redeemed for cash.</p>
        </S>
      </div>
    </div>
  );
}
