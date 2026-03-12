import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import { ArrowLeft, Coins, ArrowDown, ArrowUp, Filter, RefreshCw } from 'lucide-react';

export default function Ledger() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();
  const [balance, setBalance] = useState(0);
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadLedger();
  }, []);

  const loadLedger = async () => {
    setLoading(true);
    try {
      const { data } = await api.v2GetLedgerHistory(100, 0);
      // Use user.coins_balance as authoritative balance (LedgerEngine may lag)
      setBalance(user?.coins_balance ?? data.balance);
      setEntries(data.entries);
    } catch (e) {
      toast.error(t('ledger_page.failed'));
    }
    setLoading(false);
  };

  const filteredEntries = filter === 'all' ? entries :
    filter === 'credits' ? entries.filter(e => e.credit > 0) :
    entries.filter(e => e.debit > 0);

  const typeLabels = {
    ad_reward: t('ledger_page.ad_reward'),
    prediction_reward: t('ledger_page.prediction_reward'),
    referral_reward: t('ledger_page.referral_reward'),
    referral_bonus: t('ledger_page.referral_bonus'),
    contest_entry: t('ledger_page.contest_entry'),
    redemption: t('ledger_page.redemption'),
    admin_adjust: t('ledger_page.admin_adjust'),
    signup_bonus: t('ledger_page.signup_bonus'),
    daily_checkin: t('ledger_page.daily_checkin'),
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white pb-28 md:pb-4" data-testid="ledger-page">
      <Navbar />
      {/* Header */}
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate(-1)} data-testid="back-button">
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </button>
        <h1 className="text-lg font-bold">{t('ledger_page.title')}</h1>
        <button onClick={loadLedger} className="ml-auto" data-testid="refresh-ledger">
          <RefreshCw className={`w-4 h-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Balance Card */}
      <div className="mx-4 mt-4 p-5 bg-gradient-to-br from-emerald-900/40 to-emerald-800/20 rounded-2xl border border-emerald-500/20" data-testid="balance-card">
        <div className="text-sm text-emerald-300/60">{t('ledger_page.available_balance')}</div>
        <div className="text-4xl font-black text-emerald-400 mt-1 flex items-center gap-2">
          <Coins className="w-8 h-8" />
          {balance.toLocaleString()}
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 px-4 mt-4" data-testid="ledger-filters">
        {['all', 'credits', 'debits'].map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-full text-xs font-medium capitalize transition-all ${
              filter === f ? 'bg-emerald-500 text-white' : 'bg-white/5 text-gray-400'
            }`}
            data-testid={`filter-${f}`}
          >
            {t(`ledger_page.${f}`)}
          </button>
        ))}
      </div>

      {/* Transaction List */}
      <div className="px-4 mt-4 pb-6 space-y-2" data-testid="transaction-list">
        {loading ? (
          <div className="text-center py-8 text-gray-500">{t('ledger_page.loading')}</div>
        ) : filteredEntries.length === 0 ? (
          <div className="text-center py-8 text-gray-500">{t('ledger_page.no_transactions')}</div>
        ) : (
          filteredEntries.map(entry => (
            <div key={entry.id} className="bg-white/5 rounded-xl p-3 flex items-center gap-3" data-testid={`tx-${entry.id}`}>
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                entry.credit > 0 ? 'bg-emerald-500/20' : 'bg-red-500/20'
              }`}>
                {entry.credit > 0 ? (
                  <ArrowDown className="w-5 h-5 text-emerald-400" />
                ) : (
                  <ArrowUp className="w-5 h-5 text-red-400" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{entry.description || typeLabels[entry.type] || entry.type}</div>
                <div className="text-xs text-gray-500">{new Date(entry.timestamp).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</div>
              </div>
              <div className={`text-sm font-bold ${entry.credit > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                {entry.credit > 0 ? `+${entry.credit}` : `-${entry.debit}`}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
