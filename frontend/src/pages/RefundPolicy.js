import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

const S = ({ title, children }) => <div className="mb-6"><h2 className="text-base font-bold text-white mb-2">{title}</h2><div className="text-sm text-gray-300 leading-relaxed space-y-2">{children}</div></div>;

export default function RefundPolicy() {
  const navigate = useNavigate();
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold">Refund & Cancellation Policy</h1>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-xs text-amber-400">{t('legal.english_only_notice')}</p>
        </div>
        <S title="Digital Currency Purchases">
          <p>Due to the digital nature of platform currencies, purchases of FREE Bucks are generally non-refundable once credited to your account.</p>
        </S>
        <S title="Eligible Refund Cases">
          <p>Refunds may only be considered in the following cases:</p>
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Verified technical errors resulting in incorrect charges</li>
            <li>Duplicate payment processing</li>
            <li>Payment charged but FREE Bucks not credited due to system failure</li>
          </ul>
        </S>
        <S title="Refund Process">
          <p>To request a refund, contact support with your transaction details. Requests are reviewed within 3-5 business days. Approved refunds are processed to the original payment method.</p>
        </S>
        <S title="Reward Redemptions">
          <p>Once Free Coins are spent on reward redemption and a voucher code is delivered, the transaction cannot be reversed. The coins are permanently deducted from your balance.</p>
        </S>
        <S title="Contact">
          <p>For refund inquiries, contact <strong>support@free11.com</strong> with your registered email and transaction ID.</p>
        </S>
      </div>
    </div>
  );
}
