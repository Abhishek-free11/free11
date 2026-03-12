import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

const S = ({ title, children }) => <div className="mb-6"><h2 className="text-base font-bold text-white mb-2">{title}</h2><div className="text-sm text-gray-300 leading-relaxed space-y-2">{children}</div></div>;

export default function PrivacyPolicy() {
  const navigate = useNavigate();
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold">Privacy Policy</h1>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-xs text-amber-400">{t('legal.english_only_notice')}</p>
        </div>
        <p className="text-xs text-gray-500 mb-4">Last updated: March 2026</p>
        <S title="Information We Collect">
          <p>FREE11 collects limited information required to operate the platform including:</p>
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Account creation information (name, email, mobile number, date of birth)</li>
            <li>Gameplay activity and engagement data</li>
            <li>Reward fulfilment data</li>
            <li>Fraud prevention signals (device information, IP address)</li>
            <li>Payment transaction records (processed by third-party providers)</li>
          </ul>
        </S>
        <S title="How We Use Information">
          <p>We use collected information to operate the platform, deliver rewards, prevent fraud, improve user experience, and communicate important updates.</p>
        </S>
        <S title="Third-Party Services">
          <p>FREE11 may integrate with third-party services including payment processors (Razorpay), reward providers (Xoxoday), notification services (Firebase), analytics platforms, and advertising networks. These services may collect data as described in their respective privacy policies.</p>
        </S>
        <S title="Data Security">
          <p>We implement industry-standard security measures including encrypted data transmission, secure authentication, and access controls to protect user information.</p>
        </S>
        <S title="Data Retention">
          <p>We retain user data for as long as the account is active or as needed to provide services. Users may request account deletion by contacting support.</p>
        </S>
        <S title="Your Rights">
          <p>You may access, update, or delete your personal information through your account settings or by contacting support at support@free11.com.</p>
        </S>
      </div>
    </div>
  );
}
