import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useI18n } from '../context/I18nContext';

const S = ({ title, children }) => <div className="mb-6"><h2 className="text-base font-bold text-white mb-2">{title}</h2><div className="text-sm text-gray-300 leading-relaxed space-y-2">{children}</div></div>;

export default function CommunityGuidelines() {
  const navigate = useNavigate();
  const { t } = useI18n();
  return (
    <div className="min-h-screen bg-[#0a0e17] text-white">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold">Community Guidelines</h1>
      </div>
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <p className="text-xs text-amber-400">{t('legal.english_only_notice')}</p>
        </div>
        <S title="Respectful Participation">
          <p>Users must maintain respectful and fair behaviour at all times. FREE11 is a community-driven Social Entertainment Sports Platform.</p>
        </S>
        <S title="Prohibited Conduct">
          <p>Users must not:</p>
          <ul className="list-disc list-inside space-y-1 text-gray-400">
            <li>Abuse, harass, or threaten other users</li>
            <li>Manipulate platform systems or exploit bugs</li>
            <li>Create multiple accounts for unfair advantage</li>
            <li>Use automated tools or bots</li>
            <li>Attempt unauthorized access to platform systems</li>
            <li>Farm rewards through illegitimate means</li>
            <li>Share account credentials with others</li>
          </ul>
        </S>
        <S title="Fair Play & Anti-Fraud">
          <p>FREE11 actively monitors the platform for multiple account abuse, automated gameplay, reward farming, manipulation of contests, and exploitation of system vulnerabilities.</p>
          <p>Accounts violating platform rules may be suspended or terminated without prior notice.</p>
        </S>
        <S title="Reporting">
          <p>Users can report violations through the in-app Support section. All reports are reviewed by our moderation team.</p>
        </S>
      </div>
    </div>
  );
}
