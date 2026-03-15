import { useState, useEffect, useCallback, Fragment } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts';
import {
  Users, TrendingUp, DollarSign, Activity, Target, ShoppingCart,
  Download, RefreshCw, ArrowLeft, ChevronUp, ChevronDown,
  AlertCircle, CheckCircle, Filter, Eye
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const GOLD = '#C6A052';
const GOLD2 = '#E0B84F';
const DARK = '#0F1115';
const CARD_BG = '#1B1E23';
const STEEL = '#BFC3C8';
const GREEN = '#22c55e';
const RED = '#ef4444';

// ── CSV export helper ─────────────────────────────────────────────────────
function arrayToCSV(rows, columns) {
  const header = columns.join(',');
  const body = rows.map(row =>
    columns.map(col => {
      const val = row[col] ?? '';
      const str = typeof val === 'object' ? JSON.stringify(val) : String(val);
      return str.includes(',') || str.includes('"') || str.includes('\n')
        ? `"${str.replace(/"/g, '""')}"` : str;
    }).join(',')
  );
  return [header, ...body].join('\n');
}

function downloadCSV(content, filename) {
  const blob = new Blob([content], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// ── Sort hook ─────────────────────────────────────────────────────────────
function useSortedData(data, defaultKey, defaultDir = 'desc') {
  const [sortKey, setSortKey] = useState(defaultKey);
  const [sortDir, setSortDir] = useState(defaultDir);

  const toggle = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const sorted = [...(data || [])].sort((a, b) => {
    const av = a[sortKey] ?? '';
    const bv = b[sortKey] ?? '';
    if (typeof av === 'number' && typeof bv === 'number')
      return sortDir === 'asc' ? av - bv : bv - av;
    return sortDir === 'asc'
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });

  return { sorted, sortKey, sortDir, toggle };
}

// ── Stat card ─────────────────────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, sub, color = GOLD }) {
  return (
    <div style={{ background: CARD_BG }} className="rounded-xl p-4 border border-gray-700 flex items-start gap-3">
      <div className="rounded-lg p-2 mt-0.5" style={{ background: `${color}22` }}>
        <Icon size={18} style={{ color }} />
      </div>
      <div>
        <p className="text-xs text-gray-400 mb-0.5">{label}</p>
        <p className="text-xl font-bold text-white">{value}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ── Sortable table header ─────────────────────────────────────────────────
function TH({ label, col, sortKey, sortDir, toggle }) {
  const active = sortKey === col;
  return (
    <th
      onClick={() => toggle(col)}
      className="px-3 py-2 text-left text-xs font-semibold cursor-pointer select-none whitespace-nowrap"
      style={{ color: active ? GOLD : STEEL, background: '#111316' }}
    >
      <span className="flex items-center gap-1">
        {label}
        {active ? (sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />) : null}
      </span>
    </th>
  );
}

const FUNNEL_COLORS = [GOLD, GOLD2, '#60a5fa', '#34d399', '#a78bfa', '#f472b6'];

export default function AdminAnalytics() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('overview');
  const [search, setSearch] = useState('');
  const [expandedUser, setExpandedUser] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API}/api/admin/analytics-360`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Must be before any conditional return (Rules of Hooks)
  const hl = data?.high_level || {};
  const users360 = data?.real_users_360 || [];
  const funnel = data?.funnel || [];
  const topActions = data?.top_actions || [];
  const dau = data?.dau_7d || [];
  const monetization = data?.monetization || {};

  const filteredUsers = users360.filter(u =>
    !search || u.email?.toLowerCase().includes(search.toLowerCase()) ||
    u.name?.toLowerCase().includes(search.toLowerCase()) ||
    u.user_id?.toLowerCase().includes(search.toLowerCase())
  );

  const { sorted: sortedUsers, sortKey, sortDir, toggle } = useSortedData(
    filteredUsers, 'last_active'
  );

  const tabs = ['overview', 'users', 'funnel', 'events', 'monetization'];

  if (!user?.is_admin) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: DARK }}>
        <div className="text-center">
          <AlertCircle size={48} className="mx-auto mb-3" color={RED} />
          <p className="text-white text-lg">Admin access required</p>
          <button onClick={() => navigate('/admin')} className="mt-4 px-4 py-2 rounded-lg text-sm"
            style={{ background: GOLD, color: DARK }}>Back to Admin</button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen font-sans" style={{ background: DARK, color: 'white' }}>
      {/* Header */}
      <div className="sticky top-0 z-50 border-b border-gray-800" style={{ background: DARK }}>
        <div className="max-w-screen-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/admin/v2')} className="p-2 rounded-lg hover:bg-gray-800">
              <ArrowLeft size={18} color={STEEL} />
            </button>
            <div>
              <h1 className="text-base font-bold" style={{ color: GOLD }}>FREE11 — Analytics 360°</h1>
              <p className="text-xs text-gray-500">
                {data ? `Real users only · ${hl.real_users_count ?? 0} users · Generated ${new Date(data.generated_at).toLocaleTimeString()}` : 'Loading...'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                const API_URL = process.env.REACT_APP_BACKEND_URL;
                const token = localStorage.getItem('token');
                // Use fetch + Blob to send Authorization header
                fetch(`${API_URL}/api/admin/analytics-360/export/csv`, {
                  headers: { Authorization: `Bearer ${token}` }
                }).then(r => r.blob()).then(blob => {
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url; a.download = 'free11_users_360.csv'; a.click();
                  URL.revokeObjectURL(url);
                }).catch(() => alert('Export failed. Please try again.'));
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium"
              style={{ background: '#1B1E23', border: `1px solid ${GOLD}`, color: GOLD }}
              data-testid="export-csv-btn"
            >
              <Download size={14} /> Export CSV
            </button>
            <button onClick={load} disabled={loading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium"
              style={{ background: GOLD, color: DARK }}
              data-testid="refresh-analytics-btn"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              {loading ? 'Loading…' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="max-w-screen-2xl mx-auto px-4 flex gap-1 pb-2">
          {tabs.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className="px-3 py-1 rounded-lg text-xs font-medium capitalize"
              style={{
                background: tab === t ? `${GOLD}22` : 'transparent',
                color: tab === t ? GOLD : STEEL,
                border: tab === t ? `1px solid ${GOLD}44` : '1px solid transparent',
              }}
              data-testid={`tab-${t}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-screen-2xl mx-auto px-4 py-6">
        {error && (
          <div className="rounded-xl p-4 mb-6 flex items-center gap-2" style={{ background: '#2d1515', border: '1px solid #ef4444' }}>
            <AlertCircle size={16} color={RED} />
            <span className="text-sm text-red-300">{error}</span>
          </div>
        )}

        {loading && !data && (
          <div className="flex items-center justify-center py-24">
            <RefreshCw size={32} className="animate-spin" color={GOLD} />
          </div>
        )}

        {/* ── OVERVIEW TAB ──────────────────────────────────────────────── */}
        {tab === 'overview' && data && (
          <div className="space-y-6">
            {/* KPI Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              <StatCard icon={Users} label="Real Users" value={hl.real_users_count ?? 0} sub={`${hl.test_seed_admin_count ?? 0} test/admin excluded`} />
              <StatCard icon={Activity} label="Active (7d)" value={hl.active_7d ?? 0} sub={`${Math.round((hl.active_7d || 0) / (hl.real_users_count || 1) * 100)}% of real users`} color={GREEN} />
              <StatCard icon={Target} label="Activation Rate" value={`${hl.activation_rate_pct ?? 0}%`} sub="Made ≥1 action" color={GOLD2} />
              <StatCard icon={TrendingUp} label="Total Predictions" value={hl.total_predictions ?? 0} sub={`${hl.users_with_predictions ?? 0} predictors`} color="#60a5fa" />
              <StatCard icon={ShoppingCart} label="Redemptions" value={hl.total_redemptions ?? 0} sub={`${hl.users_with_redemptions ?? 0} redeemers`} color="#a78bfa" />
              <StatCard icon={DollarSign} label="Revenue (₹)" value={`₹${(hl.total_revenue_inr || 0).toLocaleString()}`} sub={`${hl.paying_users ?? 0} paying users`} color={GREEN} />
            </div>

            {/* Coins + DAU row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* DAU 7d */}
              <div className="rounded-xl p-4 border border-gray-700" style={{ background: CARD_BG }}>
                <h3 className="text-sm font-semibold mb-3" style={{ color: GOLD }}>Daily Active Users (7d)</h3>
                <ResponsiveContainer width="100%" height={160}>
                  <BarChart data={dau}>
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: STEEL }} tickFormatter={d => d.slice(5)} />
                    <YAxis tick={{ fontSize: 10, fill: STEEL }} />
                    <Tooltip contentStyle={{ background: '#1B1E23', border: `1px solid ${GOLD}`, fontSize: 12 }} />
                    <Bar dataKey="dau" fill={GOLD} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Coins economy */}
              <div className="rounded-xl p-4 border border-gray-700" style={{ background: CARD_BG }}>
                <h3 className="text-sm font-semibold mb-3" style={{ color: GOLD }}>Coins Economy</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Total in circulation</span>
                    <span className="font-bold text-white">{(hl.coins_in_circulation || 0).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Real user coins</span>
                    <span style={{ color: GREEN }}>{(hl.real_user_coins || 0).toLocaleString()} ({hl.real_coins_pct ?? 0}%)</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Admin/seed coins</span>
                    <span className="text-gray-500">{(hl.admin_seed_coins || 0).toLocaleString()}</span>
                  </div>
                  <div className="mt-3 rounded-lg overflow-hidden h-2 bg-gray-700">
                    <div className="h-full rounded-lg" style={{ width: `${hl.real_coins_pct ?? 0}%`, background: GOLD }} />
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Real users hold {hl.real_coins_pct ?? 0}% of all coins</p>
                </div>

                {/* Tracking gaps note */}
                {data?.tracking_gaps && (
                  <div className="mt-4 rounded-lg p-2.5 text-xs" style={{ background: '#1a1a2e', border: '1px solid #333' }}>
                    <p className="text-yellow-400 font-medium">Tracking Gaps</p>
                    <p className="text-gray-400 mt-0.5">
                      {data.tracking_gaps.users_with_no_events} users have no events tracked.{' '}
                      {data.tracking_gaps.note}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Summary table */}
            <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: CARD_BG }}>
              <div className="px-4 py-3 border-b border-gray-700 flex justify-between items-center">
                <h3 className="text-sm font-semibold" style={{ color: GOLD }}>High-Level Summary</h3>
                <button onClick={() => downloadCSV(arrayToCSV([hl], Object.keys(hl)), 'free11_summary.csv')}
                  className="flex items-center gap-1 text-xs px-2 py-1 rounded" style={{ color: GOLD, border: `1px solid ${GOLD}44` }}>
                  <Download size={12} /> CSV
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <tbody>
                    {Object.entries(hl).map(([k, v]) => (
                      <tr key={k} className="border-b border-gray-800">
                        <td className="px-4 py-2 text-gray-400 font-medium">{k.replace(/_/g, ' ')}</td>
                        <td className="px-4 py-2 text-white">{typeof v === 'number' ? v.toLocaleString() : String(v)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ── USERS TAB ─────────────────────────────────────────────────── */}
        {tab === 'users' && data && (
          <div className="space-y-4">
            <div className="flex items-center justify-between gap-3">
              <div className="flex-1 relative">
                <Filter size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by email, name, or user_id…"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 rounded-lg text-sm bg-gray-800 border border-gray-700 text-white placeholder-gray-500 outline-none"
                  data-testid="user-search-input"
                />
              </div>
              <button
                onClick={() => {
                  const cols = ['user_id', 'email', 'name', 'registration_timestamp', 'last_active',
                    'coins_balance', 'predictions_count', 'redemptions_count', 'revenue_contributed_inr',
                    'login_count', 'streak_days', 'level', 'referred_by'];
                  downloadCSV(arrayToCSV(sortedUsers, cols), 'free11_users_360.csv');
                }}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium whitespace-nowrap"
                style={{ background: GOLD, color: DARK }}
                data-testid="export-users-csv-btn"
              >
                <Download size={14} /> Export {sortedUsers.length} users
              </button>
            </div>

            <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: CARD_BG }}>
              <div className="overflow-x-auto">
                <table className="w-full text-xs" data-testid="users-table">
                  <thead>
                    <tr>
                      {[
                        ['Email', 'email'], ['Name', 'name'], ['Registered', 'registration_timestamp'],
                        ['Last Active', 'last_active'], ['Coins', 'coins_balance'],
                        ['Preds', 'predictions_count'], ['Acc%', 'prediction_accuracy_pct'],
                        ['Redemptions', 'redemptions_count'], ['Revenue ₹', 'revenue_contributed_inr'],
                        ['Logins', 'login_count'], ['Streak', 'streak_days'], ['Level', 'level'],
                        ['Events', 'total_events'], ['Details', null],
                      ].map(([label, col]) => col ? (
                        <TH key={col} label={label} col={col} sortKey={sortKey} sortDir={sortDir} toggle={toggle} />
                      ) : (
                        <th key="details" className="px-3 py-2 text-xs font-semibold" style={{ color: STEEL, background: '#111316' }}>{label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sortedUsers.map((u, i) => (
                      <Fragment key={u.user_id}>
                        <tr className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors">
                          <td className="px-3 py-2 text-blue-300 font-mono text-xs max-w-[180px] truncate">{u.email}</td>
                          <td className="px-3 py-2 text-white">{u.name}</td>
                          <td className="px-3 py-2 text-gray-400">{u.registration_timestamp?.slice(0, 10)}</td>
                          <td className="px-3 py-2 text-gray-400">{u.last_active?.slice(0, 10)}</td>
                          <td className="px-3 py-2 font-bold" style={{ color: GOLD }}>{u.coins_balance?.toLocaleString()}</td>
                          <td className="px-3 py-2 text-center">{u.predictions_count}</td>
                          <td className="px-3 py-2 text-center" style={{ color: u.prediction_accuracy_pct > 50 ? GREEN : STEEL }}>
                            {u.predictions_count > 0 ? `${u.prediction_accuracy_pct}%` : '—'}
                          </td>
                          <td className="px-3 py-2 text-center">{u.redemptions_count}</td>
                          <td className="px-3 py-2 text-center" style={{ color: u.revenue_contributed_inr > 0 ? GREEN : STEEL }}>
                            {u.revenue_contributed_inr > 0 ? `₹${u.revenue_contributed_inr}` : '—'}
                          </td>
                          <td className="px-3 py-2 text-center">{u.login_count}</td>
                          <td className="px-3 py-2 text-center">{u.streak_days}</td>
                          <td className="px-3 py-2 text-center">
                            <span className="px-1.5 py-0.5 rounded text-xs font-bold" style={{ background: `${GOLD}33`, color: GOLD }}>
                              L{u.level}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-center text-gray-400">{u.total_events}</td>
                          <td className="px-3 py-2">
                            <button onClick={() => setExpandedUser(expandedUser === u.user_id ? null : u.user_id)}
                              className="p-1 rounded hover:bg-gray-700" style={{ color: GOLD }}>
                              <Eye size={14} />
                            </button>
                          </td>
                        </tr>
                        {expandedUser === u.user_id && (
                          <tr key={`${u.user_id}-detail`}>
                            <td colSpan={14} className="px-4 py-4 bg-gray-900/50">
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                                <div>
                                  <p className="text-gray-400 font-medium mb-1">Profile</p>
                                  <p>Phone: {u.phone || '—'}</p>
                                  <p>Referred by: {u.referred_by || '—'}</p>
                                  <p>Referral code: {u.referral_code || '—'}</p>
                                  <p>First action: {u.first_action_after_reg || '—'}</p>
                                  <p>Quests: {u.quests_completed}/{u.quests_offered}</p>
                                  <p>Free Bucks: {u.free_bucks}</p>
                                  <p className="text-gray-500 mt-1 break-all">UA: {u.platform_ua?.slice(0, 80)}</p>
                                </div>
                                <div>
                                  <p className="text-gray-400 font-medium mb-1">Last 10 Predictions</p>
                                  {u.prediction_list?.length ? u.prediction_list.map((p, pi) => (
                                    <p key={pi} className={p.is_correct ? 'text-green-400' : 'text-red-400'}>
                                      {p.ts?.slice(0, 10)} {p.choice} {p.is_correct ? '✓' : '✗'}
                                    </p>
                                  )) : <p className="text-gray-500">No predictions</p>}
                                </div>
                                <div>
                                  <p className="text-gray-400 font-medium mb-1">Last 10 Transactions</p>
                                  {u.coins_history?.length ? u.coins_history.map((t, ti) => (
                                    <p key={ti} style={{ color: t.amount > 0 ? GREEN : RED }}>
                                      {t.amount > 0 ? '+' : ''}{t.amount} {t.desc?.slice(0, 30)}
                                    </p>
                                  )) : <p className="text-gray-500">No transactions</p>}
                                </div>
                                <div>
                                  <p className="text-gray-400 font-medium mb-1">Orders & Payments</p>
                                  {u.redemptions_list?.map((r, ri) => (
                                    <p key={ri} className="text-purple-300">{r.ts?.slice(0, 10)} {r.product?.slice(0, 20)}</p>
                                  ))}
                                  {u.payment_list?.map((p, pi) => (
                                    <p key={pi} className="text-green-300">₹{p.amount} {p.package} {p.status}</p>
                                  ))}
                                  {!u.redemptions_list?.length && !u.payment_list?.length && (
                                    <p className="text-gray-500">No orders/payments</p>
                                  )}
                                  <p className="text-gray-400 font-medium mb-1 mt-2">Router Orders</p>
                                  {u.router_orders_list?.length ? u.router_orders_list.map((ro, ri) => (
                                    <p key={ri} className="text-blue-300">{ro.ts?.slice(0, 10)} {ro.sku} {ro.status}</p>
                                  )) : <p className="text-gray-500">None</p>}
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                    {sortedUsers.length === 0 && (
                      <tr><td colSpan={14} className="px-4 py-8 text-center text-gray-500">
                        {search ? 'No users match your search.' : 'No real users found.'}
                      </td></tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="px-4 py-2 border-t border-gray-800 text-xs text-gray-500">
                Showing {sortedUsers.length} of {users360.length} real users (test/seed/admin excluded)
              </div>
            </div>
          </div>
        )}

        {/* ── FUNNEL TAB ────────────────────────────────────────────────── */}
        {tab === 'funnel' && data && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Funnel chart */}
              <div className="rounded-xl p-4 border border-gray-700" style={{ background: CARD_BG }}>
                <h3 className="text-sm font-semibold mb-4" style={{ color: GOLD }}>User Activation Funnel</h3>
                <div className="space-y-3">
                  {funnel.map((stage, i) => (
                    <div key={stage.stage}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-300">{stage.stage}</span>
                        <span style={{ color: FUNNEL_COLORS[i] }}>{stage.count} ({stage.pct}%)</span>
                      </div>
                      <div className="rounded-full h-2 bg-gray-700 overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-500"
                          style={{ width: `${stage.pct}%`, background: FUNNEL_COLORS[i] }} />
                      </div>
                      {stage.drop_pct > 0 && i < funnel.length - 1 && (
                        <p className="text-xs text-red-400 mt-0.5">↓ {stage.drop_pct}% drop-off</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Funnel table */}
              <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: CARD_BG }}>
                <div className="px-4 py-3 border-b border-gray-700 flex justify-between">
                  <h3 className="text-sm font-semibold" style={{ color: GOLD }}>Funnel Data Table</h3>
                  <button onClick={() => downloadCSV(arrayToCSV(funnel, ['stage', 'count', 'pct', 'drop_pct']), 'free11_funnel.csv')}
                    className="flex items-center gap-1 text-xs px-2 py-1 rounded" style={{ color: GOLD, border: `1px solid ${GOLD}44` }}>
                    <Download size={12} /> CSV
                  </button>
                </div>
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ background: '#111316' }}>
                      <th className="px-4 py-2 text-left" style={{ color: STEEL }}>Stage</th>
                      <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Users</th>
                      <th className="px-4 py-2 text-right" style={{ color: STEEL }}>% of Total</th>
                      <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Drop-off %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {funnel.map((stage, i) => (
                      <tr key={stage.stage} className="border-t border-gray-800">
                        <td className="px-4 py-2 text-white">{stage.stage}</td>
                        <td className="px-4 py-2 text-right font-bold" style={{ color: FUNNEL_COLORS[i] }}>{stage.count}</td>
                        <td className="px-4 py-2 text-right text-gray-300">{stage.pct}%</td>
                        <td className="px-4 py-2 text-right" style={{ color: stage.drop_pct > 30 ? RED : stage.drop_pct > 10 ? GOLD : GREEN }}>
                          {stage.drop_pct > 0 ? `${stage.drop_pct}%` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Per-user funnel stage */}
            <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: CARD_BG }}>
              <div className="px-4 py-3 border-b border-gray-700">
                <h3 className="text-sm font-semibold" style={{ color: GOLD }}>Per-User Drop-off Stage</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead style={{ background: '#111316' }}>
                    <tr>
                      <th className="px-4 py-2 text-left" style={{ color: STEEL }}>Email</th>
                      <th className="px-4 py-2 text-left" style={{ color: STEEL }}>Drop-off Stage</th>
                      <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Preds</th>
                      <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Redemptions</th>
                      <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users360.map(u => {
                      const stage = u.revenue_contributed_inr > 0 ? 'Paying'
                        : u.redemptions_count > 0 ? 'Redeemer'
                        : u.predictions_count > 0 ? 'Predictor'
                        : u.total_events > 0 ? 'Engaged'
                        : 'Bounced';
                      const stageColor = { Paying: GREEN, Redeemer: '#a78bfa', Predictor: GOLD2, Engaged: '#60a5fa', Bounced: RED };
                      return (
                        <tr key={u.user_id} className="border-t border-gray-800">
                          <td className="px-4 py-2 text-blue-300 font-mono max-w-[200px] truncate">{u.email}</td>
                          <td className="px-4 py-2">
                            <span className="px-2 py-0.5 rounded-full text-xs" style={{ background: `${stageColor[stage]}22`, color: stageColor[stage] }}>{stage}</span>
                          </td>
                          <td className="px-4 py-2 text-right text-gray-300">{u.predictions_count}</td>
                          <td className="px-4 py-2 text-right text-gray-300">{u.redemptions_count}</td>
                          <td className="px-4 py-2 text-right" style={{ color: u.revenue_contributed_inr > 0 ? GREEN : STEEL }}>
                            {u.revenue_contributed_inr > 0 ? `₹${u.revenue_contributed_inr}` : '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ── EVENTS TAB ────────────────────────────────────────────────── */}
        {tab === 'events' && data && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Top events bar chart */}
              <div className="rounded-xl p-4 border border-gray-700" style={{ background: CARD_BG }}>
                <div className="flex justify-between mb-3">
                  <h3 className="text-sm font-semibold" style={{ color: GOLD }}>Top 15 Events</h3>
                  <button onClick={() => downloadCSV(arrayToCSV(topActions, ['event', 'count']), 'free11_events.csv')}
                    className="flex items-center gap-1 text-xs px-2 py-1 rounded" style={{ color: GOLD, border: `1px solid ${GOLD}44` }}>
                    <Download size={12} /> CSV
                  </button>
                </div>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={topActions.slice(0, 15)} layout="vertical" margin={{ left: 60 }}>
                    <XAxis type="number" tick={{ fontSize: 10, fill: STEEL }} />
                    <YAxis dataKey="event" type="category" tick={{ fontSize: 10, fill: STEEL }} width={80} />
                    <Tooltip contentStyle={{ background: '#1B1E23', border: `1px solid ${GOLD}`, fontSize: 12 }} />
                    <Bar dataKey="count" fill={GOLD} radius={[0, 3, 3, 0]}>
                      {topActions.slice(0, 15).map((_, idx) => (
                        <Cell key={idx} fill={idx < 3 ? GOLD2 : GOLD} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Full events table */}
              <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: CARD_BG }}>
                <div className="px-4 py-3 border-b border-gray-700">
                  <h3 className="text-sm font-semibold" style={{ color: GOLD }}>All Events ({topActions.length})</h3>
                </div>
                <div className="overflow-y-auto max-h-[340px]">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0" style={{ background: '#111316' }}>
                      <tr>
                        <th className="px-4 py-2 text-left" style={{ color: STEEL }}>Event</th>
                        <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Count</th>
                        <th className="px-4 py-2 text-right" style={{ color: STEEL }}>% of Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topActions.map((e, i) => {
                        const total = topActions.reduce((s, a) => s + a.count, 0);
                        return (
                          <tr key={e.event} className="border-t border-gray-800">
                            <td className="px-4 py-2 font-mono text-gray-300">{e.event}</td>
                            <td className="px-4 py-2 text-right font-bold text-white">{e.count.toLocaleString()}</td>
                            <td className="px-4 py-2 text-right text-gray-400">{(e.count / total * 100).toFixed(1)}%</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── MONETIZATION TAB ─────────────────────────────────────────── */}
        {tab === 'monetization' && data && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              <StatCard icon={DollarSign} label="Total Revenue" value={`₹${(monetization.total_revenue_inr || 0).toLocaleString()}`} color={GREEN} />
              <StatCard icon={Users} label="Paying Users" value={hl.paying_users ?? 0} sub={`${_safe_pct(hl.paying_users, hl.real_users_count)}% conversion`} color={GOLD} />
              <StatCard icon={TrendingUp} label="ARPU" value={
                hl.real_users_count > 0 ? `₹${((monetization.total_revenue_inr || 0) / hl.real_users_count).toFixed(1)}` : '₹0'
              } sub="Per real user (incl. non-payers)" color={GOLD2} />
            </div>

            {/* Revenue by user */}
            <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: CARD_BG }}>
              <div className="px-4 py-3 border-b border-gray-700 flex justify-between">
                <h3 className="text-sm font-semibold" style={{ color: GOLD }}>Revenue by User</h3>
                <button onClick={() => downloadCSV(arrayToCSV(monetization.revenue_by_user || [], ['user_id', 'email', 'revenue_inr', 'purchases']), 'free11_revenue.csv')}
                  className="flex items-center gap-1 text-xs px-2 py-1 rounded" style={{ color: GOLD, border: `1px solid ${GOLD}44` }}>
                  <Download size={12} /> CSV
                </button>
              </div>
              <table className="w-full text-xs">
                <thead style={{ background: '#111316' }}>
                  <tr>
                    <th className="px-4 py-2 text-left" style={{ color: STEEL }}>Email</th>
                    <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Revenue (₹)</th>
                    <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Purchases</th>
                  </tr>
                </thead>
                <tbody>
                  {(monetization.revenue_by_user || []).map((r, i) => (
                    <tr key={r.user_id} className="border-t border-gray-800">
                      <td className="px-4 py-2 text-blue-300 font-mono">{r.email}</td>
                      <td className="px-4 py-2 text-right font-bold" style={{ color: GREEN }}>₹{r.revenue_inr.toLocaleString()}</td>
                      <td className="px-4 py-2 text-right text-gray-300">{r.purchases}</td>
                    </tr>
                  ))}
                  {!monetization.revenue_by_user?.length && (
                    <tr><td colSpan={3} className="px-4 py-6 text-center text-gray-500">No revenue data yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Coins by source */}
            <div className="rounded-xl p-4 border border-gray-700" style={{ background: CARD_BG }}>
              <h3 className="text-sm font-semibold mb-3" style={{ color: GOLD }}>Coins Earned by Source</h3>
              {Object.keys(monetization.coins_earned_by_source || {}).length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={Object.entries(monetization.coins_earned_by_source || {}).map(([src, coins]) => ({ src, coins }))}>
                    <XAxis dataKey="src" tick={{ fontSize: 10, fill: STEEL }} />
                    <YAxis tick={{ fontSize: 10, fill: STEEL }} />
                    <Tooltip contentStyle={{ background: '#1B1E23', border: `1px solid ${GOLD}`, fontSize: 12 }} />
                    <Bar dataKey="coins" fill={GOLD} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-gray-500 text-xs">No coin source data available yet.</p>
              )}
            </div>

            {/* Top referrers */}
            {(monetization.top_referrers || []).length > 0 && (
              <div className="rounded-xl border border-gray-700 overflow-hidden" style={{ background: CARD_BG }}>
                <div className="px-4 py-3 border-b border-gray-700">
                  <h3 className="text-sm font-semibold" style={{ color: GOLD }}>Top Referrers</h3>
                </div>
                <table className="w-full text-xs">
                  <thead style={{ background: '#111316' }}>
                    <tr>
                      <th className="px-4 py-2 text-left" style={{ color: STEEL }}>User ID</th>
                      <th className="px-4 py-2 text-right" style={{ color: STEEL }}>Referrals</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monetization.top_referrers.map(r => (
                      <tr key={r.user_id} className="border-t border-gray-800">
                        <td className="px-4 py-2 font-mono text-gray-300">{r.user_id}</td>
                        <td className="px-4 py-2 text-right font-bold" style={{ color: GOLD }}>{r.referrals}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function _safe_pct(num, denom) {
  return denom ? ((num / denom) * 100).toFixed(1) : 0;
}
