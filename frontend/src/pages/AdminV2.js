import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { toast } from 'sonner';
import { ArrowLeft, Zap, Shield, AlertTriangle, Play, SkipForward, DollarSign, Eye, RefreshCw, ToggleLeft, ToggleRight, BarChart2, Trophy, Users, TrendingUp, CheckCircle, Loader2, ShoppingCart, Package } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function AdminV2() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [testMatch, setTestMatch] = useState(null);
  const [flags, setFlags] = useState([]);
  const [logs, setLogs] = useState([]);
  const [tab, setTab] = useState('analytics');
  const [adjustForm, setAdjustForm] = useState({ user_id: '', amount: 0, reason: '' });
  const [resolveForm, setResolveForm] = useState({ match_id: '', over_number: 1, runs: 0, wickets: 0, boundaries: 0 });
  const [kpis, setKpis] = useState(null);
  const [cohort, setCohort] = useState([]);
  const [kpiLoading, setKpiLoading] = useState(false);
  const [sponsoredPools, setSponsoredPools] = useState([]);
  const [finalizing, setFinalizing] = useState(null);
  const [forecastData, setForecastData] = useState([]);
  const [routerKpis, setRouterKpis] = useState(null);
  const [routerKpiLoading, setRouterKpiLoading] = useState(false);

  useEffect(() => { loadData(); }, []);
  useEffect(() => {
    if (tab === 'analytics') loadKPIs();
    if (tab === 'sponsored') loadSponsored();
    if (tab === 'router') loadRouterKPIs();
  }, [tab]);

  const loadData = async () => {
    try {
      const [flagRes, logRes] = await Promise.all([
        api.v2AdminGetFeatureFlags(),
        api.v2AdminGetActionLog(20),
      ]);
      setFlags(flagRes.data);
      setLogs(logRes.data);
    } catch {}
  };

  const loadKPIs = async () => {
    setKpiLoading(true);
    try {
      const [kpiRes, cohortRes] = await Promise.all([api.v2GetKPIs(), api.v2GetCohortCsv()]);
      setKpis(kpiRes.data);
      setCohort(cohortRes.data.rows || []);
      // Build ARR forecast (Section 13)
      const totalUsers = kpiRes.data.users.total || 100;
      const repeatRate = kpiRes.data.redemptions.repeat_rate_30d_pct / 100 || 0.20;
      const months = Array.from({ length: 12 }, (_, i) => {
        const userGrowth = Math.round(totalUsers * Math.pow(1.15, i));      // 15% MoM
        const admob = parseFloat((userGrowth * 5).toFixed(0));               // ₹5/user/mo
        const commission = parseFloat((userGrowth * repeatRate * 50 * 0.08).toFixed(0)); // 8% on ₹50 avg order
        const arr = admob + commission;
        return { month: `M${i + 1}`, users: userGrowth, admob, commission, arr };
      });
      setForecastData(months);
    } catch (e) { toast.error('Could not load KPIs'); }
    setKpiLoading(false);
  };

  const loadSponsored = async () => {
    try {
      const { data } = await api.v2GetSponsoredPools('open');
      setSponsoredPools(Array.isArray(data) ? data : []);
    } catch {}
  };

  const loadRouterKPIs = async () => {
    setRouterKpiLoading(true);
    try {
      const { data } = await api.v2GetRouterKPIs();
      setRouterKpis(data);
    } catch { toast.error('Could not load Router KPIs'); }
    setRouterKpiLoading(false);
  };

  const finalizePool = async (poolId, poolTitle) => {
    if (!window.confirm(`Finalize "${poolTitle}"? This pays out all prizes.`)) return;
    setFinalizing(poolId);
    try {
      const { data } = await api.v2FinalizeSponsoredPool(poolId);
      toast.success(`Finalized! ${data.payouts?.length || 0} payouts, ${data.total_paid} coins`);
      loadSponsored();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
    setFinalizing(null);
  };

  const createTestMatch = async () => {
    try {
      const { data } = await api.v2AdminCreateTestMatch();
      setTestMatch(data);
      setResolveForm(f => ({ ...f, match_id: data.match_id }));
      toast.success(`Test match created: ${data.match_id}`);
    } catch { toast.error('Failed to create test match'); }
  };

  const advanceBall = async (runs, wicket = false) => {
    if (!testMatch?.match_id) return;
    try {
      const { data } = await api.v2AdminAdvanceTestMatch({ match_id: testMatch.match_id, runs, wicket });
      setTestMatch(prev => ({ ...prev, ...data }));
      toast.success(`Ball: ${data.result} | Score: ${data.score}`);
    } catch { toast.error('Failed to advance'); }
  };

  const resolveOver = async () => {
    try {
      const { data } = await api.v2AdminResolveOver(resolveForm);
      toast.success(`Resolved ${data.resolved} predictions`);
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to resolve'); }
  };

  const adjustCoins = async () => {
    if (!adjustForm.user_id || !adjustForm.amount) return;
    try {
      await api.v2AdminAdjustCoins(adjustForm);
      toast.success('Coins adjusted');
      setAdjustForm({ user_id: '', amount: 0, reason: '' });
      loadData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
  };

  const toggleFlag = async (flag, currentEnabled) => {
    try {
      await api.v2AdminSetFeatureFlag({ flag, enabled: !currentEnabled });
      toast.success(`${flag}: ${!currentEnabled ? 'ON' : 'OFF'}`);
      loadData();
    } catch {}
  };

  const reconcileAll = async () => {
    try {
      const { data } = await api.v2AdminReconcileAll();
      toast.success(`Reconciled. Mismatches: ${data.count}`);
    } catch { toast.error('Failed'); }
  };

  const toggleTestMode = async () => {
    try {
      const { data } = await api.v2AdminToggleTestMode();
      toast.success(`Test mode: ${data.test_mode ? 'ON' : 'OFF'}`);
      loadData();
    } catch {}
  };

  const tabs = [
    { key: 'analytics', label: 'Analytics' },
    { key: 'router', label: 'Router' },
    { key: 'sponsored', label: 'Sponsored' },
    { key: 'match', label: 'Match' },
    { key: 'resolve', label: 'Resolve' },
    { key: 'wallet', label: 'Wallet' },
    { key: 'flags', label: 'Flags' },
    { key: 'logs', label: 'Logs' },
  ];

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white" data-testid="admin-v2-page">
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate('/admin')} data-testid="back-button">
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </button>
        <h1 className="text-lg font-bold">Admin Control Panel</h1>
        <button
          onClick={() => navigate('/admin/analytics')}
          className="ml-auto flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium"
          style={{ background: '#C6A05222', border: '1px solid #C6A05244', color: '#C6A052' }}
          data-testid="open-analytics-360-btn"
        >
          <BarChart2 className="w-3.5 h-3.5" /> Analytics 360°
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-3 mt-3 overflow-x-auto no-scrollbar">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium shrink-0 ${tab === t.key ? 'bg-emerald-500 text-white' : 'bg-white/5 text-gray-400'}`}
            data-testid={`tab-${t.key}`}
          >{t.label}</button>
        ))}
      </div>

      <div className="px-4 mt-4 pb-6">

        {/* ── Analytics Dashboard ── */}
        {tab === 'analytics' && (
          <div className="space-y-4" data-testid="analytics-tab">
            {kpiLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
              </div>
            ) : kpis ? (
              <>
                {/* KPI Cards */}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Total Users', value: kpis.users.total, sub: `${kpis.users.active_7d} active 7d`, icon: Users, color: '#60a5fa' },
                    { label: 'Quest Opt-In', value: `${kpis.quests.opt_in_rate_pct}%`, sub: `${kpis.quests.engaged}/${kpis.quests.total_offered}`, icon: Zap, color: '#C6A052' },
                    { label: 'Repeat Redemptions', value: `${kpis.redemptions.repeat_rate_30d_pct}%`, sub: `${kpis.redemptions.repeat_users_30d} users (30d)`, icon: TrendingUp, color: '#4ade80' },
                    { label: 'Households Reached', value: kpis.redemptions.household_estimate, sub: 'unique redeemers', icon: CheckCircle, color: '#a78bfa' },
                  ].map(({ label, value, sub, icon: Icon, color }) => (
                    <div key={label} className="bg-white/5 rounded-xl p-3 border border-white/10">
                      <div className="flex items-center gap-2 mb-1.5">
                        <Icon className="w-4 h-4" style={{ color }} />
                        <span className="text-xs text-gray-400">{label}</span>
                      </div>
                      <div className="text-2xl font-bold" style={{ color }}>{value}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{sub}</div>
                    </div>
                  ))}
                </div>

                {/* Pool Lift */}
                <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                  <p className="text-xs text-gray-400 mb-2 flex items-center gap-2"><Trophy className="w-3.5 h-3.5 text-yellow-400" /> Sponsored Pool Lift</p>
                  <div className="flex items-end gap-3">
                    <div className="text-3xl font-bold text-yellow-400">{kpis.sponsored_pools.pool_lift_pct}%</div>
                    <div className="text-sm text-gray-400">of users engaged with sponsored pools<br/><span className="text-xs">{kpis.sponsored_pools.total_participants} total participants · {kpis.sponsored_pools.active_pools} active pools</span></div>
                  </div>
                </div>

                {/* Revenue Estimates */}
                <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                  <p className="text-xs text-gray-400 mb-3 flex items-center gap-2"><BarChart2 className="w-3.5 h-3.5 text-emerald-400" /> Revenue Estimates (indicative)</p>
                  <div className="space-y-2">
                    {[
                      { label: 'AdMob', value: `₹${kpis.revenue_estimates.admob_inr}` },
                      { label: 'Commission (8%)', value: `₹${kpis.revenue_estimates.commission_inr}` },
                      { label: 'Total', value: `₹${kpis.revenue_estimates.total_inr}`, bold: true },
                    ].map(({ label, value, bold }) => (
                      <div key={label} className={`flex justify-between text-sm ${bold ? 'border-t border-white/10 pt-2 font-bold text-emerald-400' : 'text-gray-300'}`}>
                        <span>{label}</span><span>{value}</span>
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{kpis.revenue_estimates.note}</p>
                </div>

                {/* 7-Day Cohort Chart */}
                {cohort.length > 0 && (
                  <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                    <p className="text-xs text-gray-400 mb-3">7-Day Registrations vs Redemptions</p>
                    <ResponsiveContainer width="100%" height={140}>
                      <BarChart data={cohort} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                        <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 9 }} tickFormatter={v => v.slice(5)} />
                        <YAxis tick={{ fill: '#6b7280', fontSize: 9 }} />
                        <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} labelStyle={{ color: '#9ca3af' }} />
                        <Bar dataKey="registrations" fill="#60a5fa" radius={[3, 3, 0, 0]} name="Registrations" />
                        <Bar dataKey="redemptions" fill="#4ade80" radius={[3, 3, 0, 0]} name="Redemptions" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Section 13 — ARR Forecast Chart */}
                {forecastData.length > 0 && (
                  <div className="bg-white/5 rounded-xl p-4 border border-white/10" data-testid="arr-forecast-chart">
                    <p className="text-xs text-gray-400 mb-1">12-Month ARR Forecast (15% MoM growth)</p>
                    <p className="text-xs text-gray-500 mb-3">AdMob ₹5/user/mo + 8% commission on ₹50 avg redemption</p>
                    <ResponsiveContainer width="100%" height={160}>
                      <LineChart data={forecastData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                        <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 9 }} />
                        <YAxis tick={{ fill: '#6b7280', fontSize: 9 }} tickFormatter={v => `₹${v}`} />
                        <Tooltip
                          contentStyle={{ background: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                          labelStyle={{ color: '#9ca3af' }}
                          formatter={(val, name) => [`₹${val}`, name === 'arr' ? 'Total Revenue' : name]}
                        />
                        <Line type="monotone" dataKey="admob" stroke="#C6A052" strokeWidth={1.5} dot={false} name="AdMob" />
                        <Line type="monotone" dataKey="commission" stroke="#4ade80" strokeWidth={1.5} dot={false} name="Commission" />
                        <Line type="monotone" dataKey="arr" stroke="#60a5fa" strokeWidth={2} dot={false} name="arr" strokeDasharray="4 2" />
                      </LineChart>
                    </ResponsiveContainer>
                    <div className="flex gap-4 mt-2 text-xs text-gray-500 justify-end">
                      <span className="flex items-center gap-1"><span className="w-3 h-0.5 inline-block" style={{ background: '#C6A052' }} />AdMob</span>
                      <span className="flex items-center gap-1"><span className="w-3 h-0.5 inline-block" style={{ background: '#4ade80' }} />Commission</span>
                      <span className="flex items-center gap-1"><span className="w-3 h-0.5 inline-block" style={{ background: '#60a5fa' }} />Total</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">M12 Projected ARR: <span className="text-emerald-400 font-bold">₹{forecastData[11]?.arr?.toLocaleString()}/mo</span> (~₹{Math.round((forecastData[11]?.arr || 0) * 12 / 100000)}L/yr)</p>
                  </div>
                )}

                <button onClick={loadKPIs} className="w-full py-2.5 bg-white/5 border border-white/10 rounded-xl text-sm text-gray-400 flex items-center justify-center gap-2" data-testid="refresh-kpis-btn">
                  <RefreshCw className="w-4 h-4" /> Refresh KPIs
                </button>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <BarChart2 className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <button onClick={loadKPIs} className="text-emerald-400 text-sm">Load Analytics</button>
              </div>
            )}
          </div>
        )}

        {/* ── Router KPI Dashboard ── */}
        {tab === 'router' && (
          <div className="space-y-4" data-testid="router-kpi-tab">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4" style={{ color: '#C6A052' }} />
                <span className="text-sm font-bold text-white">Smart Commerce Router</span>
              </div>
              <button onClick={loadRouterKPIs} className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg"
                style={{ background: 'rgba(255,255,255,0.05)', color: '#9ca3af' }} data-testid="refresh-router-kpis">
                <RefreshCw className="w-3 h-3" /> Refresh
              </button>
            </div>

            {routerKpiLoading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
              </div>
            ) : routerKpis ? (
              <>
                {/* Summary KPI cards */}
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { label: 'Total Orders', value: routerKpis.orders.total, sub: `${routerKpis.orders.last_30d} last 30d`, icon: ShoppingCart, color: '#C6A052' },
                    { label: 'Avg Coin Price', value: routerKpis.avg_coin_price, sub: 'per redemption', icon: Zap, color: '#60a5fa' },
                    { label: 'Avg Value Score', value: routerKpis.avg_value_score, sub: '1.0 = cheapest always won', icon: TrendingUp, color: '#4ade80' },
                    { label: 'Conversion Rate', value: `${routerKpis.conversion_rate_pct}%`, sub: `${routerKpis.tease_views} tease views`, icon: BarChart2, color: '#a855f7' },
                  ].map(({ label, value, sub, icon: Icon, color }) => (
                    <div key={label} className="bg-white/5 rounded-xl p-3 border border-white/10">
                      <div className="flex items-center gap-2 mb-1.5">
                        <Icon className="w-4 h-4" style={{ color }} />
                        <span className="text-xs text-gray-400">{label}</span>
                      </div>
                      <div className="text-2xl font-bold" style={{ color }}>{value}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{sub}</div>
                    </div>
                  ))}
                </div>

                {/* Provider Distribution Pie Chart */}
                {routerKpis.provider_distribution?.length > 0 ? (
                  <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                    <p className="text-xs text-gray-400 mb-3 flex items-center gap-2">
                      <Package className="w-3.5 h-3.5 text-yellow-400" /> Provider Distribution
                    </p>
                    <div className="flex items-center gap-4">
                      <ResponsiveContainer width="50%" height={120}>
                        <PieChart>
                          <Pie data={routerKpis.provider_distribution} dataKey="count" nameKey="provider"
                            cx="50%" cy="50%" outerRadius={50} innerRadius={25}>
                            {routerKpis.provider_distribution.map((entry, i) => (
                              <Cell key={i} fill={['#C6A052', '#4ade80', '#60a5fa', '#a855f7'][i % 4]} />
                            ))}
                          </Pie>
                          <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="flex-1 space-y-1.5">
                        {routerKpis.provider_distribution.map((p, i) => (
                          <div key={p.provider} className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-1.5">
                              <div className="w-2.5 h-2.5 rounded-full"
                                style={{ background: ['#C6A052', '#4ade80', '#60a5fa', '#a855f7'][i % 4] }} />
                              <span className="text-gray-300 capitalize">{p.provider}</span>
                            </div>
                            <span className="text-gray-400">{p.pct}% ({p.count})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white/5 rounded-xl p-6 border border-white/10 text-center">
                    <Package className="w-8 h-8 mx-auto mb-2 opacity-20" />
                    <p className="text-xs text-gray-500">No orders yet. Provider distribution will show here.</p>
                  </div>
                )}

                {/* Top SKUs */}
                {routerKpis.top_skus?.length > 0 && (
                  <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                    <p className="text-xs text-gray-400 mb-3">Top Redeemed SKUs</p>
                    <div className="space-y-1.5">
                      {routerKpis.top_skus.map((s, i) => (
                        <div key={s.sku} className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-600">#{i + 1}</span>
                            <span className="text-gray-300 font-mono text-xs">{s.sku}</span>
                          </div>
                          <span className="text-emerald-400 font-bold">{s.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <p className="text-xs text-center text-gray-600">{routerKpis.note}</p>
              </>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Zap className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <button onClick={loadRouterKPIs} className="text-emerald-400 text-sm">Load Router KPIs</button>
              </div>
            )}
          </div>
        )}

        {/* ── Sponsored Pools (Bulk Finalize) ── */}
        {tab === 'sponsored' && (
          <div className="space-y-3" data-testid="sponsored-tab">
            <div className="flex items-center justify-between mb-1">
              <p className="text-sm font-bold text-white">Sponsored Pools</p>
              <button onClick={loadSponsored} className="p-1.5 rounded-lg bg-white/5" data-testid="refresh-sponsored-btn">
                <RefreshCw className="w-3.5 h-3.5 text-gray-400" />
              </button>
            </div>
            {sponsoredPools.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">No open sponsored pools</div>
            ) : (
              sponsoredPools.map(pool => (
                <div key={pool.id} className="bg-white/5 rounded-xl p-4 border border-white/10" data-testid={`admin-pool-${pool.id}`}>
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <p className="font-bold text-sm text-white">{pool.title}</p>
                      <p className="text-xs text-gray-400">{pool.brand_name} · {pool.current_participants}/{pool.max_participants} joined</p>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-500/15 text-yellow-400">{pool.badge}</span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mb-3">
                    <span>Prize: {pool.net_prize_pool} coins</span>
                    <span>Platform cut: {pool.platform_cut} coins (20%)</span>
                  </div>
                  <button
                    onClick={() => finalizePool(pool.id, pool.title)}
                    disabled={!!finalizing}
                    className="w-full py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-sm text-emerald-400 font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                    data-testid={`finalize-pool-${pool.id}`}
                  >
                    {finalizing === pool.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                    Finalize & Pay Out
                  </button>
                </div>
              ))
            )}
          </div>
        )}

        {/* Match Control */}
        {tab === 'match' && (
          <div className="space-y-4" data-testid="match-controls">
            <button onClick={createTestMatch} className="w-full py-3 bg-emerald-500/20 border border-emerald-500/30 rounded-xl text-sm font-medium text-emerald-400 flex items-center justify-center gap-2" data-testid="create-test-match-btn">
              <Play className="w-4 h-4" /> Create Test Match
            </button>

            {testMatch && (
              <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                <div className="text-xs text-gray-400 mb-1">Match: {testMatch.match_id}</div>
                <div className="text-lg font-bold mb-1">{testMatch.team1_short || testMatch.team1} vs {testMatch.team2_short || testMatch.team2}</div>
                <div className="text-sm text-emerald-400 font-mono mb-3">
                  Score: {testMatch.score || testMatch.team1_score || '0/0'} | Ball: {testMatch.ball || testMatch.current_ball || '0.1'}
                </div>
                <div className="text-xs text-gray-400 mb-2">Advance by:</div>
                <div className="flex flex-wrap gap-2">
                  {[0, 1, 2, 3, 4, 6].map(r => (
                    <button key={r} onClick={() => advanceBall(r)}
                      className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold ${
                        r === 4 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                        r === 6 ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                        'bg-white/10 text-gray-300'
                      }`}
                      data-testid={`advance-${r}`}
                    >{r}</button>
                  ))}
                  <button onClick={() => advanceBall(0, true)}
                    className="px-3 h-10 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 text-sm font-bold"
                    data-testid="advance-wicket"
                  >W</button>
                </div>
              </div>
            )}

            <button onClick={toggleTestMode} className="w-full py-2.5 bg-yellow-500/20 border border-yellow-500/30 rounded-xl text-sm text-yellow-400 flex items-center justify-center gap-2" data-testid="toggle-test-mode-btn">
              <AlertTriangle className="w-4 h-4" /> Toggle Test Mode
            </button>
          </div>
        )}

        {/* Resolve Over */}
        {tab === 'resolve' && (
          <div className="space-y-3" data-testid="resolve-controls">
            <input value={resolveForm.match_id} onChange={e => setResolveForm(p => ({ ...p, match_id: e.target.value }))}
              placeholder="Match ID" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm" data-testid="resolve-match-id" />
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="text-xs text-gray-400">Over #</label>
                <input type="number" value={resolveForm.over_number} onChange={e => setResolveForm(p => ({ ...p, over_number: parseInt(e.target.value) || 0 }))}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm mt-1" data-testid="resolve-over" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Runs</label>
                <input type="number" value={resolveForm.runs} onChange={e => setResolveForm(p => ({ ...p, runs: parseInt(e.target.value) || 0 }))}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm mt-1" data-testid="resolve-runs" />
              </div>
              <div>
                <label className="text-xs text-gray-400">Wickets</label>
                <input type="number" value={resolveForm.wickets} onChange={e => setResolveForm(p => ({ ...p, wickets: parseInt(e.target.value) || 0 }))}
                  className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm mt-1" data-testid="resolve-wickets" />
              </div>
            </div>
            <button onClick={resolveOver} className="w-full py-2.5 bg-emerald-500 text-white font-medium rounded-xl text-sm" data-testid="resolve-btn">
              Resolve Over
            </button>
          </div>
        )}

        {/* Wallet Controls */}
        {tab === 'wallet' && (
          <div className="space-y-3" data-testid="wallet-controls">
            <input value={adjustForm.user_id} onChange={e => setAdjustForm(p => ({ ...p, user_id: e.target.value }))}
              placeholder="User ID" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm" data-testid="adjust-user-id" />
            <input type="number" value={adjustForm.amount} onChange={e => setAdjustForm(p => ({ ...p, amount: parseInt(e.target.value) || 0 }))}
              placeholder="Amount (+/-)" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm" data-testid="adjust-amount" />
            <input value={adjustForm.reason} onChange={e => setAdjustForm(p => ({ ...p, reason: e.target.value }))}
              placeholder="Reason" className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm" data-testid="adjust-reason" />
            <button onClick={adjustCoins} className="w-full py-2.5 bg-emerald-500 text-white font-medium rounded-xl text-sm" data-testid="adjust-btn">
              Adjust Coins
            </button>
            <button onClick={reconcileAll} className="w-full py-2.5 bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-xl text-sm flex items-center justify-center gap-2" data-testid="reconcile-btn">
              <RefreshCw className="w-4 h-4" /> Reconcile All Ledgers
            </button>
          </div>
        )}

        {/* Feature Flags */}
        {tab === 'flags' && (
          <div className="space-y-2" data-testid="flag-controls">
            {['test_mode', 'predictions_enabled', 'contests_enabled', 'ads_enabled', 'referrals_enabled', 'redemption_enabled'].map(flag => {
              const f = flags.find(fl => fl.flag === flag);
              const enabled = f?.enabled || false;
              return (
                <div key={flag} className="bg-white/5 rounded-xl p-3 flex items-center justify-between" data-testid={`flag-${flag}`}>
                  <span className="text-sm">{flag.replace(/_/g, ' ')}</span>
                  <button onClick={() => toggleFlag(flag, enabled)}>
                    {enabled ? <ToggleRight className="w-6 h-6 text-emerald-400" /> : <ToggleLeft className="w-6 h-6 text-gray-500" />}
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {/* Admin Logs */}
        {tab === 'logs' && (
          <div className="space-y-2" data-testid="admin-logs">
            {logs.length === 0 ? (
              <div className="text-center py-6 text-gray-500 text-sm">No admin actions yet</div>
            ) : (
              logs.map(log => (
                <div key={log.id} className="bg-white/5 rounded-xl p-3 text-xs" data-testid={`log-${log.id}`}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-medium text-emerald-400">{log.action}</span>
                    <span className="text-gray-500">{new Date(log.timestamp).toLocaleString('en-IN')}</span>
                  </div>
                  <div className="text-gray-400 font-mono truncate">{JSON.stringify(log.details)}</div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}
