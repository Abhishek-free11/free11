import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  Building2, LayoutDashboard, Package, Target, BarChart3, 
  LogOut, Plus, TrendingUp, Users, ShoppingBag, Calendar
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || '';

// Brand API helper
const brandApi = {
  login: (email, password) => axios.post(`${API}/api/brand/auth/login`, { email, password }),
  getMe: (token) => axios.get(`${API}/api/brand/auth/me`, { headers: { Authorization: `Bearer ${token}` } }),
  getDashboard: (token) => axios.get(`${API}/api/brand/dashboard`, { headers: { Authorization: `Bearer ${token}` } }),
  getAnalytics: (token, days = 30) => axios.get(`${API}/api/brand/analytics?days=${days}`, { headers: { Authorization: `Bearer ${token}` } }),
  getCampaigns: (token) => axios.get(`${API}/api/brand/campaigns`, { headers: { Authorization: `Bearer ${token}` } }),
  getProducts: (token) => axios.get(`${API}/api/brand/products`, { headers: { Authorization: `Bearer ${token}` } }),
  getRedemptions: (token) => axios.get(`${API}/api/brand/redemptions`, { headers: { Authorization: `Bearer ${token}` } }),
  createCampaign: (token, data) => axios.post(`${API}/api/brand/campaigns`, data, { headers: { Authorization: `Bearer ${token}` } }),
  createProduct: (token, data) => axios.post(`${API}/api/brand/products`, data, { headers: { Authorization: `Bearer ${token}` } }),
};

const BrandPortal = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState(null);
  const [brand, setBrand] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Login form
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  
  // Dashboard data
  const [dashboard, setDashboard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [products, setProducts] = useState([]);
  const [redemptions, setRedemptions] = useState([]);

  useEffect(() => {
    // Check for stored token
    const storedToken = localStorage.getItem('brand_token');
    if (storedToken) {
      setToken(storedToken);
      verifyToken(storedToken);
    } else {
      setLoading(false);
    }
  }, []);

  const verifyToken = async (t) => {
    try {
      const res = await brandApi.getMe(t);
      setBrand(res.data);
      setIsLoggedIn(true);
      setToken(t);
      fetchDashboardData(t);
    } catch (error) {
      localStorage.removeItem('brand_token');
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    setLoginLoading(true);
    try {
      const res = await brandApi.login(loginEmail, loginPassword);
      const newToken = res.data.access_token;
      localStorage.setItem('brand_token', newToken);
      setToken(newToken);
      setBrand(res.data.brand);
      setIsLoggedIn(true);
      fetchDashboardData(newToken);
      toast.success('Welcome to your brand dashboard!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('brand_token');
    setToken(null);
    setBrand(null);
    setIsLoggedIn(false);
    setDashboard(null);
  };

  const fetchDashboardData = async (t) => {
    setLoading(true);
    try {
      const [dashRes, analyticsRes, campaignsRes, productsRes, redemptionsRes] = await Promise.all([
        brandApi.getDashboard(t),
        brandApi.getAnalytics(t),
        brandApi.getCampaigns(t),
        brandApi.getProducts(t),
        brandApi.getRedemptions(t)
      ]);
      
      setDashboard(dashRes.data);
      setAnalytics(analyticsRes.data);
      setCampaigns(campaignsRes.data.campaigns || []);
      setProducts(productsRes.data.products || []);
      setRedemptions(redemptionsRes.data.redemptions || []);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  // Login Page
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 flex items-center justify-center p-4">
        <Card className="w-full max-w-md bg-slate-900/80 border-slate-800 backdrop-blur-sm">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-4">
              <Building2 className="h-8 w-8 text-white" />
            </div>
            <CardTitle className="text-2xl text-white">Brand Portal</CardTitle>
            <CardDescription className="text-slate-400">
              FREE11 Partner Dashboard
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-slate-300">Email</label>
              <Input
                type="email"
                placeholder="brand@company.com"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                className="bg-slate-800 border-slate-700 text-white"
                data-testid="brand-email-input"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">Password</label>
              <Input
                type="password"
                placeholder="••••••••"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                className="bg-slate-800 border-slate-700 text-white"
                data-testid="brand-password-input"
              />
            </div>
            <Button 
              onClick={handleLogin}
              disabled={loginLoading}
              className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
              data-testid="brand-login-btn"
            >
              {loginLoading ? 'Signing in...' : 'Sign In to Dashboard'}
            </Button>
            
            <div className="text-center text-sm text-slate-500 pt-4 border-t border-slate-800">
              <p>New brand partner?</p>
              <p className="text-blue-400">Contact partnerships@free11.com</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-4 border-blue-400 border-t-transparent rounded-full mx-auto"></div>
          <p className="text-slate-400 mt-4">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Dashboard
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <Building2 className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-white font-bold">{brand?.brand_name || 'Brand'} Portal</h1>
              <p className="text-xs text-slate-400">FREE11 Partner Dashboard</p>
            </div>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleLogout}
            className="border-slate-700 text-slate-400"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8" data-testid="brand-dashboard">
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="bg-slate-800/50 border border-slate-700">
            <TabsTrigger value="overview" className="data-[state=active]:bg-blue-500">
              <LayoutDashboard className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="campaigns" className="data-[state=active]:bg-blue-500">
              <Target className="h-4 w-4 mr-2" />
              Campaigns
            </TabsTrigger>
            <TabsTrigger value="products" className="data-[state=active]:bg-blue-500">
              <Package className="h-4 w-4 mr-2" />
              Products
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-blue-500">
              <BarChart3 className="h-4 w-4 mr-2" />
              Analytics
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            {/* SANDBOX MODE BANNER */}
            {dashboard?.environment?.is_sandbox && (
              <div className="mb-6 p-4 bg-amber-500/20 border-2 border-dashed border-amber-500/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="bg-amber-500 text-black px-3 py-1 rounded font-bold text-sm">
                    SANDBOX / TEST DATA
                  </div>
                  <p className="text-amber-300 text-sm">
                    This dashboard shows test data. ROAS calculations will be available with live brand budgets.
                  </p>
                </div>
              </div>
            )}

            {/* Key Metrics */}
            <div className="grid md:grid-cols-4 gap-6 mb-8">
              <Card className="bg-gradient-to-br from-green-500/20 to-green-500/5 border-green-500/30">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-green-400 text-sm">
                        {dashboard?.environment?.is_sandbox ? 'Test Consumption' : 'Verified Consumption'}
                      </p>
                      <p className="text-3xl font-bold text-white">
                        ₹{(dashboard?.demand_metrics?.verified_consumption_value || 0).toLocaleString()}
                      </p>
                    </div>
                    <TrendingUp className="h-8 w-8 text-green-400" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-blue-500/20 to-blue-500/5 border-blue-500/30">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-blue-400 text-sm">Total Redemptions</p>
                      <p className="text-3xl font-bold text-white">
                        {dashboard?.demand_metrics?.total_redemptions || 0}
                      </p>
                    </div>
                    <ShoppingBag className="h-8 w-8 text-blue-400" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className="bg-gradient-to-br from-purple-500/20 to-purple-500/5 border-purple-500/30">
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-purple-400 text-sm">Unique Consumers</p>
                      <p className="text-3xl font-bold text-white">
                        {dashboard?.demand_metrics?.unique_consumers_reached || 0}
                      </p>
                    </div>
                    <Users className="h-8 w-8 text-purple-400" />
                  </div>
                </CardContent>
              </Card>
              
              <Card className={`bg-gradient-to-br ${dashboard?.environment?.is_sandbox ? 'from-slate-500/20 to-slate-500/5 border-slate-500/30' : 'from-yellow-500/20 to-yellow-500/5 border-yellow-500/30'}`}>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`text-sm ${dashboard?.environment?.is_sandbox ? 'text-slate-400' : 'text-yellow-400'}`}>ROAS</p>
                      <p className="text-3xl font-bold text-white">
                        {dashboard?.roas?.sandbox_hidden ? 'N/A' : `${dashboard?.roas?.value || 0}x`}
                      </p>
                      {dashboard?.roas?.sandbox_hidden && (
                        <p className="text-xs text-slate-500">Hidden in sandbox</p>
                      )}
                    </div>
                    <BarChart3 className={`h-8 w-8 ${dashboard?.environment?.is_sandbox ? 'text-slate-400' : 'text-yellow-400'}`} />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* ROAS Explanation */}
            <Card className="bg-slate-900/50 border-slate-800 mb-8">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  Return on Demand Creation
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`p-4 ${dashboard?.environment?.is_sandbox ? 'bg-slate-500/10 border-slate-500/30' : 'bg-green-500/10 border-green-500/30'} border rounded-lg`}>
                  <p className={`text-lg ${dashboard?.environment?.is_sandbox ? 'text-slate-300' : 'text-green-300'}`}>
                    {dashboard?.roas?.description || "Track your verified consumption metrics"}
                  </p>
                  <p className="text-slate-400 text-sm mt-2">
                    {dashboard?.roas?.note || "ROAS = Total Value of Goods Consumed / Budget Invested"}
                  </p>
                </div>
                
                {/* Attribution Integrity Note */}
                {dashboard?.attribution_integrity && (
                  <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <p className="text-blue-300 text-sm font-medium">Attribution Integrity</p>
                    <p className="text-slate-400 text-xs mt-1">
                      {dashboard.attribution_integrity.explanation}
                    </p>
                    <div className="flex flex-wrap gap-2 mt-2">
                      <span className="text-xs text-slate-500">Not based on:</span>
                      {dashboard.attribution_integrity.not_based_on?.map(item => (
                        <Badge key={item} variant="outline" className="text-xs border-slate-600 text-slate-400">
                          {item}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="grid md:grid-cols-2 gap-4 mt-6">
                  <div className="p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-slate-400 text-sm">Last 7 Days</p>
                    <p className="text-2xl font-bold text-white">
                      {dashboard?.recent_activity?.last_7_days_redemptions || 0} redemptions
                    </p>
                  </div>
                  <div className="p-4 bg-slate-800/50 rounded-lg">
                    <p className="text-slate-400 text-sm">Last 30 Days</p>
                    <p className="text-2xl font-bold text-white">
                      {dashboard?.recent_activity?.last_30_days_redemptions || 0} redemptions
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Active Campaigns & Products Summary */}
            <div className="grid md:grid-cols-2 gap-6">
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white">Active Campaigns</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-4xl font-bold text-blue-400">
                    {dashboard?.demand_metrics?.active_campaigns || 0}
                  </p>
                  <p className="text-slate-400 text-sm mt-2">campaigns running</p>
                </CardContent>
              </Card>
              
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white">Active Products</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-4xl font-bold text-purple-400">
                    {dashboard?.demand_metrics?.active_products || 0}
                  </p>
                  <p className="text-slate-400 text-sm mt-2">products available for redemption</p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Campaigns Tab */}
          <TabsContent value="campaigns">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white">Your Campaigns</CardTitle>
                  <CardDescription className="text-slate-400">
                    Manage demand creation campaigns
                  </CardDescription>
                </div>
                <Button className="bg-blue-500 hover:bg-blue-600">
                  <Plus className="h-4 w-4 mr-2" />
                  New Campaign
                </Button>
              </CardHeader>
              <CardContent>
                {campaigns.length === 0 ? (
                  <div className="text-center py-12">
                    <Target className="h-16 w-16 text-slate-700 mx-auto mb-4" />
                    <p className="text-slate-400">No campaigns yet. Create your first campaign!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {campaigns.map((campaign) => (
                      <div 
                        key={campaign.id}
                        className="p-4 bg-slate-800/50 rounded-lg"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="text-white font-medium">{campaign.name}</p>
                            <p className="text-sm text-slate-400">{campaign.objective}</p>
                          </div>
                          <Badge className={campaign.is_active ? 'bg-green-500/20 text-green-400' : 'bg-slate-500/20 text-slate-400'}>
                            {campaign.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-4 mt-4 text-center">
                          <div>
                            <p className="text-xl font-bold text-blue-400">{campaign.total_redemptions || 0}</p>
                            <p className="text-xs text-slate-500">Redemptions</p>
                          </div>
                          <div>
                            <p className="text-xl font-bold text-green-400">₹{campaign.total_value_delivered || 0}</p>
                            <p className="text-xs text-slate-500">Value Delivered</p>
                          </div>
                          <div>
                            <p className="text-xl font-bold text-purple-400">{campaign.unique_users_reached || 0}</p>
                            <p className="text-xs text-slate-500">Consumers</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Products Tab */}
          <TabsContent value="products">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white">Your Products</CardTitle>
                  <CardDescription className="text-slate-400">
                    Manage products available for redemption
                  </CardDescription>
                </div>
                <Button className="bg-purple-500 hover:bg-purple-600">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Product
                </Button>
              </CardHeader>
              <CardContent>
                {products.length === 0 ? (
                  <div className="text-center py-12">
                    <Package className="h-16 w-16 text-slate-700 mx-auto mb-4" />
                    <p className="text-slate-400">No products yet. Add your first product!</p>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {products.map((product) => (
                      <div 
                        key={product.id}
                        className="p-4 bg-slate-800/50 rounded-lg"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <p className="text-white font-medium">{product.name}</p>
                          <Badge className={product.is_active ? 'bg-green-500/20 text-green-400' : 'bg-slate-500/20 text-slate-400'}>
                            {product.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-400 mb-3">{product.category}</p>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Cost:</span>
                          <span className="text-yellow-400">{product.cost_in_coins} coins</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Value:</span>
                          <span className="text-green-400">₹{product.value_in_inr}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Redeemed:</span>
                          <span className="text-blue-400">{product.redeemed_count || 0}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            {/* SANDBOX MODE BANNER */}
            {analytics?.environment?.is_sandbox && (
              <div className="mb-6 p-4 bg-amber-500/20 border-2 border-dashed border-amber-500/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="bg-amber-500 text-black px-3 py-1 rounded font-bold text-sm">
                    SANDBOX / TEST DATA
                  </div>
                  <p className="text-amber-300 text-sm">
                    Analytics shown are from test data. Production metrics will be available with live campaigns.
                  </p>
                </div>
              </div>
            )}

            <Card className="bg-slate-900/50 border-slate-800 mb-6">
              <CardHeader>
                <CardTitle className="text-white">Demand Analytics</CardTitle>
                <CardDescription className="text-slate-400">
                  Verified consumption metrics - {analytics?.period || 'Last 30 days'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Attribution Note */}
                {analytics?.attribution_note && (
                  <div className="mb-6 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <p className="text-blue-300 text-sm">{analytics.attribution_note}</p>
                  </div>
                )}

                {/* ROAS by Campaign */}
                <div className="mb-8">
                  <h3 className="text-lg font-bold text-white mb-4">ROAS by Campaign</h3>
                  {analytics?.roas_by_campaign?.length > 0 ? (
                    <div className="space-y-3">
                      {analytics.roas_by_campaign.map((campaign, idx) => (
                        <div key={idx} className="p-4 bg-slate-800/50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-white font-medium">{campaign.campaign_name}</span>
                            <span className={`font-bold ${analytics?.environment?.is_sandbox ? 'text-slate-400' : 'text-green-400'}`}>
                              {campaign.roas_display || 'N/A'}
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div>
                              <p className="text-slate-500">Redemptions</p>
                              <p className="text-blue-400 font-medium">{campaign.redemptions}</p>
                            </div>
                            <div>
                              <p className="text-slate-500">Value Delivered</p>
                              <p className="text-green-400 font-medium">₹{campaign.value_delivered}</p>
                            </div>
                            <div>
                              <p className="text-slate-500">Budget</p>
                              <p className="text-yellow-400 font-medium">₹{campaign.budget_allocated}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400">No campaign data yet</p>
                  )}
                </div>

                {/* ROAS by SKU (Top Products) */}
                <div className="mb-8">
                  <h3 className="text-lg font-bold text-white mb-4">ROAS by SKU (Top Products)</h3>
                  {(analytics?.roas_by_sku || analytics?.top_products)?.length > 0 ? (
                    <div className="space-y-3">
                      {(analytics.roas_by_sku || analytics.top_products).map((product, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                          <div className="flex items-center gap-3">
                            <span className="text-slate-500 font-mono w-6">#{idx + 1}</span>
                            <div>
                              <span className="text-white">{product.product_name || product.name}</span>
                              <p className="text-xs text-slate-500">₹{product.value_per_unit || product.cost_per_redemption} per redemption</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-blue-400 font-bold">{product.redemptions} redeemed</p>
                            <p className="text-xs text-green-400">₹{product.total_value_delivered || (product.redemptions * (product.value_per_unit || 0))} delivered</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400">No product data yet</p>
                  )}
                </div>

                {/* ROAS by Day - Daily Trend */}
                {analytics?.roas_by_day?.length > 0 && (
                  <div className="mb-8">
                    <h3 className="text-lg font-bold text-white mb-4">Daily Redemptions (Last 14 Days)</h3>
                    <div className="grid grid-cols-7 gap-2">
                      {analytics.roas_by_day.slice(0, 14).map((day, idx) => (
                        <div key={idx} className="text-center p-2 bg-slate-800/50 rounded-lg">
                          <p className="text-xs text-slate-500">{day.date?.split('-').slice(1).join('/')}</p>
                          <p className="text-sm font-bold text-blue-400">{day.redemptions}</p>
                          <p className="text-xs text-green-400">₹{day.value_delivered}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Consumer Segments */}
                <div>
                  <h3 className="text-lg font-bold text-white mb-4">Consumer Segments</h3>
                  {analytics?.consumer_segments?.length > 0 ? (
                    <div className="grid grid-cols-5 gap-4">
                      {analytics.consumer_segments.map((segment, idx) => (
                        <div key={idx} className="text-center p-3 bg-slate-800/50 rounded-lg">
                          <p className="text-2xl font-bold text-purple-400">{segment.consumers}</p>
                          <p className="text-xs text-slate-500">Level {segment.level}</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400">No segment data yet</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default BrandPortal;
