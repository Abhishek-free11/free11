import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

const S = ({ title, children }) => <div className="mb-6"><h2 className="text-base font-bold text-white mb-2">{title}</h2><div className="text-sm text-gray-300 leading-relaxed space-y-2">{children}</div></div>;

export default function TermsAndConditions() {
  const navigate = useNavigate();
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold">Terms & Conditions</h1>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-xs text-amber-400">{t('legal.english_only_notice')}</p>
        </div>
        <p className="text-xs text-gray-500 mb-4">Last updated: March 2026</p>
        <S title="1. Platform Description">
          <p>FREE11 is a Social Entertainment Sports Platform. Participation on the platform is intended for entertainment and engagement purposes. The platform does not provide gambling services, betting opportunities, or financial investment products.</p>
        </S>
        <S title="2. Virtual Currencies">
          <p><strong>Free Coins</strong> are earned through gameplay. <strong>FREE Bucks</strong> may be purchased to enhance participation.</p>
          <p>Both currencies have no real-world monetary value, cannot be withdrawn as cash, cannot be converted to legal tender, cannot be transferred outside the platform, and cannot be traded between users.</p>
        </S>
        <S title="3. Rewards">
          <p>Users may redeem platform currencies for promotional rewards such as brand vouchers, digital coupons, and merchandise. Rewards are promotional incentives, cannot be redeemed for cash, are subject to availability, and may change at the platform's discretion.</p>
        </S>
        <S title="4. Payments">
          <p>Users may purchase FREE Bucks using supported payment methods. All payments are processed through secure third-party payment processors. FREE11 does not store sensitive payment information.</p>
        </S>
        <S title="5. Refunds">
          <p>Due to the digital nature of platform currencies, purchases of FREE Bucks are generally non-refundable once credited. Refunds may only be considered in cases of verified technical errors.</p>
        </S>
        <S title="6. Account Termination">
          <p>FREE11 reserves the right to suspend or terminate accounts involved in fraud, abuse, or violation of platform rules.</p>
        </S>
        <S title="7. Age Requirement">
          <p>Users must be 18 years or older and meet the minimum legal age requirement applicable in their jurisdiction.</p>
        </S>
        <S title="8. Limitation of Liability">
          <p>FREE11 is not responsible for temporary service interruptions, third-party partner outages, delays in reward delivery, or gameplay outcomes.</p>
        </S>
        <S title="9. Third-Party Services">
          <p>FREE11 may integrate with third-party services including payment processors, reward providers, notification services, analytics platforms, and advertising networks.</p>
        </S>
        <S title="10. Changes">
          <p>FREE11 may update these terms at any time. Continued use of the platform constitutes acceptance of the updated terms.</p>
        </S>
      </div>
    </div>
  );
}
