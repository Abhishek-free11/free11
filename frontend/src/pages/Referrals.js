import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import { ArrowLeft, Copy, Users, Gift, Share2, Check, ChevronRight, Zap } from 'lucide-react';

export default function Referrals() {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [stats, setStats] = useState(null);
  const [bindCode, setBindCode] = useState('');
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [showQR, setShowQR] = useState(false);

  useEffect(() => { loadStats(); }, []);

  const loadStats = async () => {
    try {
      const { data } = await api.v2GetReferralStats();
      setStats(data);
    } catch {}
    setLoading(false);
  };

  const referralUrl = stats?.referral_code
    ? `${window.location.origin}/register?ref=${stats.referral_code}`
    : '';

  const copyLink = () => {
    if (!referralUrl) return;
    navigator.clipboard.writeText(referralUrl).then(() => {
      setCopied(true);
      toast.success('Link copied!');
      setTimeout(() => setCopied(false), 2500);
    });
  };

  const shareLink = () => {
    if (!referralUrl) return;
    if (navigator.share) {
      navigator.share({
        title: 'Join FREE11 — Predict Cricket, Earn Essentials',
        text: `I'm on FREE11 — predict cricket matches and earn free groceries & vouchers. Join with my link and get bonus coins!`,
        url: referralUrl,
      }).catch(() => copyLink());
    } else {
      copyLink();
    }
  };

  const applyCode = async () => {
    if (!bindCode.trim()) return;
    try {
      const { data } = await api.v2BindReferral({ referral_code: bindCode.trim() });
      toast.success(`Referral applied! You'll earn coins after your first prediction.`);
      setBindCode('');
      loadStats();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Invalid or already used code');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F1115] flex items-center justify-center">
        <div className="animate-spin h-6 w-6 border-2 border-[#C6A052] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F1115] text-white pb-28 md:pb-4" data-testid="referrals-page">
      <Navbar />

      {/* Header */}
      <div className="bg-[#0F1115] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)} data-testid="back-button" className="p-1">
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </button>
        <h1 className="text-lg font-bold">Invite Friends</h1>
      </div>

      <div className="px-4 mt-4 space-y-4 max-w-lg mx-auto">

        {/* Hero banner */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl p-5 relative overflow-hidden"
          style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.18) 0%, rgba(198,160,82,0.06) 100%)', border: '1px solid rgba(198,160,82,0.25)' }}
          data-testid="referral-hero"
        >
          {/* Background glow */}
          <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse at 80% 20%, rgba(198,160,82,0.12) 0%, transparent 60%)' }} />
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-4 h-4" style={{ color: '#C6A052' }} />
              <span className="text-xs font-bold tracking-widest uppercase" style={{ color: '#C6A052' }}>Earn Together</span>
            </div>
            <h2 className="text-xl font-black text-white mb-1">
              You get <span style={{ color: '#C6A052' }}>+50 coins</span>.<br />
              They get <span style={{ color: '#C6A052' }}>+25 coins</span>.
            </h2>
            <p className="text-xs" style={{ color: '#8A9096' }}>
              Reward unlocks after your friend makes 3 predictions on FREE11.
            </p>
          </div>
        </motion.div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="grid grid-cols-3 gap-2"
        >
          {[
            { icon: Users, value: stats?.total_referrals || 0, label: 'Friends Joined', color: '#60a5fa' },
            { icon: Gift, value: stats?.total_earned || 0, label: 'Coins Earned', color: '#C6A052' },
            { icon: Zap, value: stats?.reward_per_referral || 50, label: 'Per Referral', color: '#4ade80' },
          ].map(({ icon: Icon, value, label, color }) => (
            <div key={label} className="rounded-xl p-3 text-center" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
              data-testid={`stat-${label.toLowerCase().replace(' ', '-')}`}>
              <Icon className="w-4 h-4 mx-auto mb-1" style={{ color }} />
              <div className="text-xl font-black text-white font-numbers">{value}</div>
              <div className="text-[10px] mt-0.5" style={{ color: '#8A9096' }}>{label}</div>
            </div>
          ))}
        </motion.div>

        {/* Your referral code */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl p-5"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
          data-testid="my-referral-card"
        >
          <p className="text-xs uppercase tracking-widest mb-2" style={{ color: '#8A9096' }}>Your Referral Code</p>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl font-black tracking-widest flex-1" style={{ color: '#C6A052', fontFamily: 'monospace' }} data-testid="referral-code">
              {stats?.referral_code || '...'}
            </span>
            <button
              onClick={copyLink}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all"
              style={{ background: copied ? 'rgba(74,222,128,0.15)' : 'rgba(255,255,255,0.07)', border: `1px solid ${copied ? 'rgba(74,222,128,0.3)' : 'rgba(255,255,255,0.1)'}`, color: copied ? '#4ade80' : '#fff' }}
              data-testid="copy-link-btn"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
              {copied ? 'Copied!' : 'Copy Link'}
            </button>
          </div>

          {/* Referral URL preview */}
          <div className="flex items-center gap-2 mb-4 px-3 py-2 rounded-xl overflow-hidden" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <span className="text-xs truncate flex-1" style={{ color: '#8A9096' }}>{referralUrl || 'Loading...'}</span>
          </div>

          {/* Action buttons */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={shareLink}
              className="flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all"
              style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
              data-testid="share-link-btn"
            >
              <Share2 className="w-4 h-4" />
              Share Invite
            </button>
            <button
              onClick={() => setShowQR(v => !v)}
              className="flex items-center justify-center gap-2 py-3 rounded-xl font-bold text-sm transition-all"
              style={{ background: showQR ? 'rgba(198,160,82,0.15)' : 'rgba(255,255,255,0.06)', border: `1px solid ${showQR ? 'rgba(198,160,82,0.4)' : 'rgba(255,255,255,0.1)'}`, color: '#fff' }}
              data-testid="show-qr-btn"
            >
              {showQR ? 'Hide QR' : 'Show QR'}
            </button>
          </div>

          {/* QR Code */}
          {showQR && referralUrl && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 flex flex-col items-center gap-2"
              data-testid="qr-code-container"
            >
              <div className="p-4 rounded-2xl" style={{ background: '#fff' }}>
                <QRCodeSVG
                  value={referralUrl}
                  size={180}
                  bgColor="#ffffff"
                  fgColor="#0F1115"
                  level="M"
                />
              </div>
              <p className="text-xs text-center" style={{ color: '#8A9096' }}>
                Friend scans this to join FREE11 with your code pre-filled
              </p>
            </motion.div>
          )}
        </motion.div>

        {/* Apply a friend's code */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-2xl p-4"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
          data-testid="apply-code-section"
        >
          <h3 className="text-sm font-bold mb-3 text-white">Have a friend's code?</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={bindCode}
              onChange={e => setBindCode(e.target.value.toUpperCase())}
              placeholder="e.g. F11-ABC123"
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-[#C6A052] uppercase tracking-widest placeholder-gray-600"
              data-testid="referral-code-input"
            />
            <button
              onClick={applyCode}
              disabled={!bindCode.trim()}
              className="px-5 py-2.5 rounded-xl font-bold text-sm transition disabled:opacity-40"
              style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
              data-testid="apply-code-btn"
            >
              Apply
            </button>
          </div>
        </motion.div>

        {/* How it works */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-2xl p-4"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}
        >
          <h3 className="text-sm font-bold mb-3 text-white">How it works</h3>
          <div className="space-y-3">
            {[
              { step: '1', text: 'Share your unique link or code with friends' },
              { step: '2', text: 'Friend registers on FREE11 using your link' },
              { step: '3', text: 'They make 3 predictions — both of you get coins!' },
            ].map(({ step, text }) => (
              <div key={step} className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{ background: 'rgba(198,160,82,0.15)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.3)' }}>
                  {step}
                </div>
                <span className="text-sm" style={{ color: '#BFC3C8' }}>{text}</span>
              </div>
            ))}
          </div>
          <button
            onClick={() => navigate('/predict')}
            className="mt-4 w-full flex items-center justify-center gap-1 text-xs font-medium py-2.5 rounded-xl transition"
            style={{ background: 'rgba(198,160,82,0.08)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.15)' }}
          >
            Start Predicting Now <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </motion.div>

      </div>
    </div>
  );
}
