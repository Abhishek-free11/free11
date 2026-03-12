import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import { ArrowLeft, Wallet, Coins, CreditCard, TrendingUp, TrendingDown, Loader2, Receipt } from 'lucide-react';

const DEBIT_TYPES = new Set(['contest_entry', 'redemption', 'spent', 'feature_use', 'debit']);

function getTxnDirection(txn) {
  // Schema 1: explicit credit/debit fields
  if (txn.credit != null && txn.credit > 0) return { isCredit: true, amount: txn.credit };
  if (txn.debit != null && txn.debit > 0) return { isCredit: false, amount: txn.debit };
  // Schema 2: amount field + type
  if (txn.amount != null) {
    const isDebit = DEBIT_TYPES.has(txn.type);
    return { isCredit: !isDebit, amount: Math.abs(txn.amount) };
  }
  // Schema 3: parse from description e.g. "Spin wheel: 25 Coins"
  const match = (txn.description || '').match(/(\d+)/);
  const amt = match ? parseInt(match[1]) : 0;
  const isDebit = DEBIT_TYPES.has(txn.type);
  return { isCredit: !isDebit, amount: amt };
}

const TYPE_LABELS = {
  ad_reward: 'Ad Reward',
  prediction_reward: 'Prediction Reward',
  referral_reward: 'Referral Reward',
  referral_bonus: 'Referral Bonus',
  contest_entry: 'Contest Entry',
  contest_reward: 'Contest Reward',
  redemption: 'Redemption',
  admin_adjust: 'Admin Adjustment',
  signup_bonus: 'Signup Bonus',
  daily_checkin: 'Daily Check-in',
  puzzle_reward: 'Daily Puzzle',
  spin_reward: 'Spin Wheel',
  mission_reward: 'Mission Reward',
  streak_bonus: 'Streak Bonus',
  streak_reward: 'Streak Reward',
  earned: 'Coins Earned',
  spent: 'Coins Spent',
  debit: 'Coins Spent',
  credit: 'Coins Earned',
  feature_use: 'Feature Used',
};

const PACKAGE_LABELS = {
  starter: 'Starter Pack (50 Bucks)',
  popular: 'Popular Pack (160 Bucks)',
  value: 'Value Pack (550 Bucks)',
  mega: 'Mega Pack (1200 Bucks)',
};

function formatDate(ts) {
  if (!ts) return '—';
  return new Date(ts).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function truncate(str, n = 16) {
  if (!str) return '—';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

export default function WalletHistory() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('coins');

  useEffect(() => {
    (async () => {
      try {
        const { data: res } = await api.v2GetWalletHistory();
        setData(res);
      } catch {
        toast.error('Failed to load wallet history');
      }
      setLoading(false);
    })();
  }, []);

  const purchases = data?.free_bucks_purchases || [];
  const coinTxns = data?.coin_transactions || [];
  const paidPurchases = purchases.filter(p => p.payment_status === 'paid');

  return (
    <div className="min-h-screen bg-[#0F1115] text-white pb-28 md:pb-6" data-testid="wallet-history-page">
      <Navbar />
      <div className="max-w-lg mx-auto px-4 pt-4">

        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <button onClick={() => navigate('/profile')}
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}
            data-testid="wallet-back-btn">
            <ArrowLeft className="w-4 h-4 text-white" />
          </button>
          <div>
            <h1 className="font-heading text-xl text-white tracking-wide">Wallet History</h1>
            <p className="text-xs" style={{ color: '#8A9096' }}>All your transactions in one place</p>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-2 gap-3 mb-5">
          <div className="rounded-2xl p-4" style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.2)' }}
            data-testid="wallet-coins-summary">
            <Coins className="w-5 h-5 mb-2" style={{ color: '#C6A052' }} />
            <p className="text-2xl font-black font-numbers" style={{ color: '#C6A052' }}>{user?.coins_balance || 0}</p>
            <p className="text-[11px] mt-0.5" style={{ color: '#8A9096' }}>Coins Balance</p>
          </div>
          <div className="rounded-2xl p-4" style={{ background: 'rgba(74,222,128,0.06)', border: '1px solid rgba(74,222,128,0.15)' }}
            data-testid="wallet-bucks-summary">
            <CreditCard className="w-5 h-5 mb-2 text-emerald-400" />
            <p className="text-2xl font-black font-numbers text-emerald-400">{paidPurchases.length}</p>
            <p className="text-[11px] mt-0.5" style={{ color: '#8A9096' }}>Completed Purchases</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex rounded-xl p-1 mb-4" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
          {[
            { key: 'coins', label: 'Coin History', icon: Coins },
            { key: 'bucks', label: 'FREE Bucks', icon: CreditCard },
          ].map(({ key, label, icon: Icon }) => (
            <button key={key} onClick={() => setTab(key)}
              className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition-all"
              style={{
                background: tab === key ? 'rgba(198,160,82,0.15)' : 'transparent',
                color: tab === key ? '#C6A052' : '#8A9096',
                border: tab === key ? '1px solid rgba(198,160,82,0.25)' : '1px solid transparent',
              }}
              data-testid={`wallet-tab-${key}`}>
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin" style={{ color: '#C6A052' }} />
          </div>
        ) : (
          <>
            {/* Coin Transactions Tab */}
            {tab === 'coins' && (
              <div data-testid="coin-transactions-section">
                {coinTxns.length === 0 ? (
                  <div className="text-center py-12">
                    <Coins className="w-10 h-10 mx-auto mb-3 opacity-20" style={{ color: '#C6A052' }} />
                    <p className="text-sm" style={{ color: '#8A9096' }}>No coin transactions yet</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {coinTxns.map((txn, i) => {
                      const { isCredit, amount } = getTxnDirection(txn);
                      return (
                        <div key={txn.id || i}
                          className="flex items-center justify-between p-3.5 rounded-xl"
                          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
                          data-testid={`coin-txn-${i}`}>
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                              style={{ background: isCredit ? 'rgba(74,222,128,0.1)' : 'rgba(248,113,113,0.1)' }}>
                              {isCredit
                                ? <TrendingUp className="w-4 h-4 text-emerald-400" />
                                : <TrendingDown className="w-4 h-4 text-red-400" />}
                            </div>
                            <div>
                              <p className="text-sm font-medium text-white">
                                {TYPE_LABELS[txn.type] || txn.type || 'Transaction'}
                              </p>
                              <p className="text-[11px]" style={{ color: '#8A9096' }}>{formatDate(txn.timestamp)}</p>
                            </div>
                          </div>
                          <div className={`text-sm font-bold font-numbers ${isCredit ? 'text-emerald-400' : 'text-red-400'}`}>
                            {isCredit ? '+' : '-'}{amount}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* FREE Bucks Purchases Tab */}
            {tab === 'bucks' && (
              <div data-testid="freebucks-purchases-section">
                {purchases.length === 0 ? (
                  <div className="text-center py-12">
                    <Receipt className="w-10 h-10 mx-auto mb-3 opacity-20 text-emerald-400" />
                    <p className="text-sm mb-1" style={{ color: '#8A9096' }}>No purchases yet</p>
                    <button onClick={() => navigate('/freebucks')}
                      className="text-xs text-emerald-400 underline underline-offset-2 mt-1">
                      Buy FREE Bucks
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {purchases.map((p, i) => (
                      <div key={p.order_id || i}
                        className="p-4 rounded-xl"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
                        data-testid={`purchase-${i}`}>
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <p className="text-sm font-semibold text-white">
                              {PACKAGE_LABELS[p.package_id] || `${p.bucks || 0} FREE Bucks`}
                            </p>
                            <p className="text-[11px] mt-0.5" style={{ color: '#8A9096' }}>
                              {formatDate(p.paid_at || p.created_at)}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-base font-black font-numbers" style={{ color: '#C6A052' }}>₹{p.amount}</p>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                              p.payment_status === 'paid'
                                ? 'text-emerald-400 bg-emerald-400/10'
                                : 'text-yellow-400 bg-yellow-400/10'
                            }`}>
                              {p.payment_status === 'paid' ? 'PAID' : p.payment_status?.toUpperCase() || 'PENDING'}
                            </span>
                          </div>
                        </div>
                        {p.razorpay_payment_id && (
                          <p className="text-[10px] font-mono" style={{ color: '#5a6270' }}>
                            ID: {truncate(p.razorpay_payment_id, 22)}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
