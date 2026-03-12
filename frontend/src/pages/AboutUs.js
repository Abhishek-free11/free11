import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

const S = ({ title, children }) => <div className="mb-6"><h2 className="text-base font-bold text-white mb-2">{title}</h2><div className="text-sm text-gray-300 leading-relaxed space-y-2">{children}</div></div>;

export default function AboutUs() {
  const navigate = useNavigate();
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold">About FREE11</h1>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-xs text-amber-400">{t('legal.english_only_notice')}</p>
        </div>
        <S title="What is FREE11?">
          <p>FREE11 is a <strong>Social Entertainment Sports Platform</strong> where users participate in prediction challenges, sports-based contests, and interactive gameplay built around sports knowledge and engagement.</p>
          <p>The platform focuses on rewarding correct calls, strategy, and sports understanding through engaging entertainment experiences.</p>
          <p>FREE11 is designed purely for social entertainment and engagement. FREE11 does not offer gambling, betting, or real-money wagering services.</p>
        </S>
        <S title="Game and Engagement Experiences">
          <p>FREE11 includes interactive sports entertainment features such as:</p>
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Prediction challenges</li>
            <li>Fantasy-style sports contests</li>
            <li>Engagement missions and challenges</li>
            <li>Social leaderboards</li>
            <li>Squad competitions</li>
            <li>Card games (Rummy, Teen Patti, Poker)</li>
            <li>Reward-based activities</li>
          </ul>
        </S>
        <S title="Virtual Currency System">
          <p><strong>Free Coins</strong> — Earned through participation, missions, referrals, streaks, contests, and engagement activities.</p>
          <p><strong>FREE Bucks</strong> — May be purchased to enhance participation in platform activities or unlock certain experiences.</p>
          <p>Both currencies exist only within the FREE11 ecosystem. They have no real-world monetary value and cannot be withdrawn as cash.</p>
        </S>
        <S title="Rewards">
          <p>Users may redeem accumulated platform currencies for promotional rewards such as brand vouchers, digital coupons, merchandise, and partner-provided products.</p>
          <p>Rewards are promotional incentives. They cannot be redeemed for cash, are subject to availability, and may change at the platform's discretion.</p>
        </S>
        <S title="Contact">
          <p>For support, reach us through the in-app Support section or email <strong>support@free11.com</strong></p>
        </S>
      </div>
    </div>
  );
}
