import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import { Coins, Zap, ShieldCheck, Star, Loader2, Gift, ChevronRight } from 'lucide-react';

const PACK_ICONS = { starter: Coins, popular: Zap, value: Star, mega: ShieldCheck };
const PACK_COLORS = { starter: 'border-gray-500/20', popular: 'border-blue-500/30 ring-1 ring-blue-500/20', value: 'border-purple-500/30', mega: 'border-yellow-500/30' };
const PACK_BADGES = { popular: 'POPULAR', mega: 'BEST VALUE' };

export default function FreeBucks() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useI18n();
  const [searchParams] = useSearchParams();
  const [balance, setBalance] = useState(0);
  const [wallet, setWallet] = useState({});
  const [packages, setPackages] = useState({});
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [balRes, pkgRes, histRes] = await Promise.all([
        api.v2GetFreeBucksBalance(),
        api.v2GetFreeBucksPackages(),
        api.v2GetFreeBucksHistory(20),
      ]);
      setBalance(balRes.data?.balance || 0);
      setWallet(balRes.data?.wallet || {});
      setPackages(pkgRes.data || {});
      setHistory(histRes.data || []);
    } catch { toast.error(t('freebucks.failed_load')); }
    setLoading(false);
  };

  const buyPackage = async (pkgId) => {
    setBuying(pkgId);
    try {
      // Try Cashfree first (faster activation), fall back to Razorpay
      const cfStatus = await api.get('/cashfree/status').catch(() => ({ data: { enabled: false } }));
      const rzpStatus = await api.get('/razorpay/status').catch(() => ({ data: { enabled: false } }));

      if (cfStatus.data?.enabled) {
        // ── Cashfree flow ──────────────────────────────────────────
        const { data } = await api.post('/cashfree/create-order', { package_id: pkgId });
        if (data.payment_session_id) {
          // Load Cashfree JS SDK dynamically
          if (!window.Cashfree) {
            await new Promise((resolve, reject) => {
              const s = document.createElement('script');
              s.src = 'https://sdk.cashfree.com/js/v3/cashfree.js';
              s.onload = resolve; s.onerror = reject;
              document.head.appendChild(s);
            });
          }
          const cashfree = await window.Cashfree({ mode: data.environment === 'production' ? 'production' : 'sandbox' });
          const checkoutOptions = {
            paymentSessionId: data.payment_session_id,
            returnUrl: `${window.location.origin}/freebucks?cf_order_id=${data.order_id}&payment_status=SUCCESS`,
          };
          await cashfree.checkout(checkoutOptions);
        }
      } else if (rzpStatus.data?.enabled) {
        // ── Razorpay flow ──────────────────────────────────────────
        const { data } = await api.post('/razorpay/create-order', { package_id: pkgId });
        if (data.key_id && window.Razorpay) {
          const options = {
            key: data.key_id,
            amount: data.amount,
            currency: data.currency,
            name: 'FREE11',
            description: `${data.package.label} - ${data.package.bucks} FREE Bucks`,
            order_id: data.order_id,
            handler: async (response) => {
              try {
                await api.post('/razorpay/verify', {
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature,
                });
                toast.success(t('freebucks.payment_success'));
                loadData();
              } catch { toast.error(t('freebucks.payment_failed')); }
            },
            prefill: { email: user?.email || '', name: user?.name || '' },
            theme: { color: '#C6A052' },
          };
          new window.Razorpay(options).open();
        }
      } else {
        toast.info('Payments activating soon — keys under review.');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Payment failed. Please try again.');
    }
    setBuying(null);
  };

  // Handle Cashfree return redirect
  useEffect(() => {
    const cfOrderId = searchParams.get('cf_order_id');
    const paymentStatus = searchParams.get('payment_status');
    if (cfOrderId && paymentStatus === 'SUCCESS') {
      api.post('/cashfree/verify', { order_id: cfOrderId })
        .then(() => { toast.success('Payment successful! FREE Bucks credited.'); loadData(); })
        .catch(() => toast.error('Could not verify payment. Contact support.'));
    }
  }, []);

  const useCases = [
    { icon: Zap, label: t('freebucks.power_cards'), desc: 'Buy double coins, shields, multipliers' },
    { icon: Star, label: t('freebucks.premium_contests'), desc: 'Unlock exclusive high-reward contests' },
    { icon: Gift, label: t('freebucks.reward_discounts'), desc: '100 Bucks = 10% off redemption cost' },
    { icon: ShieldCheck, label: t('freebucks.faster_progression'), desc: 'XP boosts and tier acceleration' },
  ];

  if (loading) return <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center"><Loader2 className="w-6 h-6 text-emerald-400 animate-spin" /></div>;

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white pb-28 md:pb-4" data-testid="freebucks-page">
      <Navbar />
      <div className="max-w-lg mx-auto px-4 py-4">
        {/* Balance */}
        <div className="bg-gradient-to-br from-emerald-900/40 to-teal-900/20 rounded-2xl p-5 border border-emerald-500/20 mb-4" data-testid="fb-balance-card">
          <div className="text-xs text-emerald-400/70 uppercase tracking-wider">{t('freebucks.title')}</div>
          <div className="text-4xl font-black text-emerald-400 mt-1">{balance}</div>
          <div className="text-xs text-gray-400 mt-1">{t('freebucks.subtitle')}</div>
          <div className="flex gap-4 mt-3 text-xs text-gray-500">
            <span>{t('freebucks.purchased')}: {wallet.total_purchased || 0}</span>
            <span>{t('freebucks.spent')}: {wallet.total_spent || 0}</span>
          </div>
        </div>

        {/* Packs */}
        <h3 className="text-sm font-semibold text-gray-400 mb-3">{t('freebucks.buy_label')}</h3>
        <div className="space-y-2 mb-5">
          {Object.entries(packages).map(([id, pkg]) => {
            const Icon = PACK_ICONS[id] || Coins;
            const badge = PACK_BADGES[id];
            return (
              <button key={id} onClick={() => buyPackage(id)} disabled={!!buying}
                className={`w-full flex items-center gap-3 p-4 bg-white/5 rounded-xl border ${PACK_COLORS[id] || 'border-white/5'} hover:bg-white/10 transition-all disabled:opacity-50 relative`}
                data-testid={`pkg-${id}`}>
                {badge && <span className="absolute -top-2 right-3 px-2 py-0.5 bg-emerald-500 text-white text-[10px] font-bold rounded-full">{badge}</span>}
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <Icon className="w-5 h-5 text-emerald-400" />
                </div>
                <div className="flex-1 text-left">
                  <div className="text-sm font-bold">{pkg.label}</div>
                  <div className="text-xs text-gray-400">{pkg.bucks} FREE Bucks {pkg.bonus > 0 ? `(incl. ${pkg.bonus} bonus)` : ''}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-bold text-emerald-400">
                    {buying === id ? <Loader2 className="w-4 h-4 animate-spin" /> : `₹${pkg.amount}`}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* What FREE Bucks Do */}
        <h3 className="text-sm font-semibold text-gray-400 mb-3">{t('freebucks.what_for_label')}</h3>
        <div className="grid grid-cols-2 gap-2 mb-5">
          {useCases.map(uc => (
            <div key={uc.label} className="bg-white/5 rounded-xl p-3 border border-white/5">
              <uc.icon className="w-5 h-5 text-emerald-400 mb-1.5" />
              <div className="text-xs font-bold text-white">{uc.label}</div>
              <div className="text-[10px] text-gray-400 mt-0.5">{uc.desc}</div>
            </div>
          ))}
        </div>

        {/* History */}
        <h3 className="text-sm font-semibold text-gray-400 mb-3">{t('freebucks.history_label')}</h3>
        {history.length === 0 ? (
          <div className="text-center py-6 text-gray-500 text-sm">{t('freebucks.no_history')}</div>
        ) : (
          <div className="space-y-1.5">
            {history.map(h => (
              <div key={h.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                <div>
                  <div className="text-xs font-medium text-white">{h.source || h.feature || h.type}</div>
                  <div className="text-[10px] text-gray-500">{new Date(h.timestamp).toLocaleDateString()}</div>
                </div>
                <div className={`text-sm font-bold ${h.type === 'credit' ? 'text-emerald-400' : 'text-red-400'}`}>
                  {h.type === 'credit' ? '+' : '-'}{h.amount}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
