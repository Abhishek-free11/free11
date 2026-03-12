import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

const S = ({ title, children }) => <div className="mb-6"><h2 className="text-base font-bold text-white mb-2">{title}</h2><div className="text-sm text-gray-300 leading-relaxed space-y-2">{children}</div></div>;

export default function ResponsiblePlay() {
  const navigate = useNavigate();
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold">Responsible Participation</h1>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-xs text-amber-400">{t('legal.english_only_notice')}</p>
        </div>
        <S title="Our Commitment">
          <p>FREE11 promotes responsible entertainment usage. We encourage all users to participate for recreational purposes and maintain balanced digital engagement.</p>
        </S>
        <S title="Platform Safeguards">
          <p>The platform implements the following safeguards:</p>
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Daily earning caps (5,000 Free Coins per day)</li>
            <li>Daily reward redemption limits (3 per day)</li>
            <li>Session activity monitoring</li>
            <li>Age verification (18+ only)</li>
            <li>Cooldown periods on repeat actions</li>
          </ul>
        </S>
        <S title="Tips for Responsible Use">
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Set personal time limits for platform usage</li>
            <li>Participate for fun, not as a source of income</li>
            <li>Take regular breaks during gameplay</li>
            <li>Remember that Free Coins and FREE Bucks have no real-world monetary value</li>
          </ul>
        </S>
        <S title="Need Help?">
          <p>If you feel your usage is becoming excessive, contact our support team. We can help with account adjustments including self-imposed limits or temporary account suspension.</p>
        </S>
      </div>
    </div>
  );
}
