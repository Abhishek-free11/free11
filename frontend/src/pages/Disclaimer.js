import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

const S = ({ title, children }) => <div className="mb-6"><h2 className="text-base font-bold text-white mb-2">{title}</h2><div className="text-sm text-gray-300 leading-relaxed space-y-2">{children}</div></div>;

export default function Disclaimer() {
  const navigate = useNavigate();
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold">Disclaimer</h1>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-xs text-amber-400">{t('legal.english_only_notice')}</p>
        </div>
        <S title="Platform Nature">
          <p>FREE11 operates as a <strong>Social Entertainment Sports Platform</strong>. Participation on the platform is intended for entertainment and engagement purposes only.</p>
          <p>The platform does not provide gambling services, betting opportunities, or financial investment products.</p>
        </S>
        <S title="Virtual Currencies">
          <p>Free Coins and FREE Bucks are virtual currencies that exist solely within the FREE11 ecosystem. They have no real-world monetary value and cannot be withdrawn as cash, converted to legal tender, or transferred outside the platform.</p>
        </S>
        <S title="Rewards">
          <p>Rewards available on the platform are promotional incentives provided by FREE11 and its partners. They cannot be redeemed for cash and are subject to availability and change without notice.</p>
        </S>
        <S title="Limitation of Liability">
          <p>FREE11 is not responsible for:</p>
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Temporary service interruptions</li>
            <li>Third-party partner outages</li>
            <li>Delays in reward delivery</li>
            <li>Gameplay outcomes</li>
            <li>Changes in reward availability</li>
          </ul>
        </S>
        <S title="Sports Data">
          <p>Sports data displayed on the platform is sourced from third-party providers and is presented for entertainment purposes. FREE11 does not guarantee the accuracy or timeliness of sports data.</p>
        </S>
      </div>
    </div>
  );
}
