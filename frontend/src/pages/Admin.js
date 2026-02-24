import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Users, ShoppingBag, Coins, TrendingUp, Package, Plus, Target, Ticket, RefreshCw, Trophy, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const Admin = () => {
  const [analytics, setAnalytics] = useState(null);
  const [betaMetrics, setBetaMetrics] = useState(null);
  const [allOrders, setAllOrders] = useState([]);
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    category: 'electronics',
    coin_price: '',
    image_url: '',
    stock: '',
    brand: ''
  });
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAnalytics();
    fetchBetaMetrics();
    fetchAllOrders();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await api.getAnalytics();
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchBetaMetrics = async () => {
    try {
      const response = await api.get('/admin/beta-metrics');
      setBetaMetrics(response.data);
    } catch (error) {
      console.error('Error fetching beta metrics:', error);
    }
  };

  const fetchAllOrders = async () => {
    try {
      const response = await api.getAllRedemptions();
      setAllOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchAnalytics(), fetchBetaMetrics(), fetchAllOrders()]);
    setRefreshing(false);
    toast.success('Data refreshed!');
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createProduct({
        ...newProduct,
        coin_price: parseInt(newProduct.coin_price),
        stock: parseInt(newProduct.stock)
      });
      toast.success('Product created successfully!');
      setNewProduct({
        name: '',
        description: '',
        category: 'electronics',
        coin_price: '',
        image_url: '',
        stock: '',
        brand: ''
      });
      fetchAnalytics();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create product');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8" data-testid="admin-page">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
          <div>
            <h1 className="text-2xl sm:text-4xl font-black text-white mb-1">Beta Dashboard 🧪</h1>
            <p className="text-slate-400 text-sm">Monitor beta metrics and validate the product</p>
          </div>
          <Button 
            onClick={handleRefresh} 
            disabled={refreshing}
            variant="outline" 
            className="border-slate-700 text-slate-300 hover:bg-slate-800"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Beta Health Summary */}
        {betaMetrics && (
          <Card className="bg-gradient-to-r from-slate-900 to-slate-800 border-slate-700 mb-6">
            <CardContent className="p-4 sm:p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h2 className="text-lg sm:text-xl font-bold text-white mb-1">Beta Health</h2>
                  <p className="text-slate-400 text-sm">
                    {betaMetrics.users?.users_completed_full_loop || 0} users completed full loop (Predict → Redeem)
                  </p>
                </div>
                <div className="text-3xl sm:text-4xl font-black">
                  {betaMetrics.summary?.health}
                </div>
              </div>
              <div className="mt-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400">Loop Completion</span>
                  <span className="text-white font-bold">{betaMetrics.summary?.loop_completion_rate}</span>
                </div>
                <Progress 
                  value={parseFloat(betaMetrics.summary?.loop_completion_rate) || 0} 
                  className="h-2 bg-slate-700"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6">
          <Card className="bg-gradient-to-br from-blue-500/20 to-cyan-600/20 border-blue-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2 px-3 sm:px-6">
              <CardTitle className="text-xs sm:text-sm font-medium text-blue-200">Beta Users</CardTitle>
              <Users className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent className="px-3 sm:px-6">
              <div className="text-2xl sm:text-3xl font-bold text-blue-400">{betaMetrics?.users?.total_beta_users || 0}</div>
              <p className="text-xs text-blue-300/70 mt-1">
                {betaMetrics?.invites?.used || 0} invites used
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-red-500/20 to-orange-600/20 border-red-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2 px-3 sm:px-6">
              <CardTitle className="text-xs sm:text-sm font-medium text-red-200">Predictions</CardTitle>
              <Target className="h-4 w-4 text-red-400" />
            </CardHeader>
            <CardContent className="px-3 sm:px-6">
              <div className="text-2xl sm:text-3xl font-bold text-red-400">{betaMetrics?.predictions?.total || 0}</div>
              <p className="text-xs text-red-300/70 mt-1">
                {betaMetrics?.predictions?.accuracy_rate} accuracy
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500/20 to-emerald-600/20 border-green-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2 px-3 sm:px-6">
              <CardTitle className="text-xs sm:text-sm font-medium text-green-200">Redemptions</CardTitle>
              <ShoppingBag className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent className="px-3 sm:px-6">
              <div className="text-2xl sm:text-3xl font-bold text-green-400">{betaMetrics?.redemptions?.total || 0}</div>
              <p className="text-xs text-green-300/70 mt-1">
                {betaMetrics?.redemptions?.adoption_rate} of users
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-yellow-500/20 to-amber-600/20 border-yellow-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2 px-3 sm:px-6">
              <CardTitle className="text-xs sm:text-sm font-medium text-yellow-200">Coins</CardTitle>
              <Coins className="h-4 w-4 text-yellow-400" />
            </CardHeader>
            <CardContent className="px-3 sm:px-6">
              <div className="text-2xl sm:text-3xl font-bold text-yellow-400">{betaMetrics?.coins?.total_in_circulation || 0}</div>
              <p className="text-xs text-yellow-300/70 mt-1">
                in circulation
              </p>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="beta" className="space-y-4 sm:space-y-6">
          <TabsList className="bg-slate-900/50 border border-slate-800 w-full sm:w-auto overflow-x-auto">
            <TabsTrigger value="beta" className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-400 text-xs sm:text-sm">
              <TrendingUp className="h-4 w-4 mr-1 sm:mr-2" />
              Beta Metrics
            </TabsTrigger>
            <TabsTrigger value="products" className="data-[state=active]:bg-yellow-500/20 data-[state=active]:text-yellow-400 text-xs sm:text-sm">
              <Plus className="h-4 w-4 mr-1 sm:mr-2" />
              Products
            </TabsTrigger>
            <TabsTrigger value="orders" className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400 text-xs sm:text-sm">
              <Package className="h-4 w-4 mr-1 sm:mr-2" />
              Orders
            </TabsTrigger>
          </TabsList>

          {/* Beta Metrics Tab */}
          <TabsContent value="beta">
            <div className="grid lg:grid-cols-2 gap-4 sm:gap-6">
              {/* Funnel Metrics */}
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Conversion Funnel</CardTitle>
                  <CardDescription className="text-slate-400">User journey through core loop</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300 text-sm">Invites Used</span>
                      <Badge className="bg-blue-500/20 text-blue-400">{betaMetrics?.invites?.used || 0}</Badge>
                    </div>
                    <Progress value={100} className="h-2 bg-slate-700" />
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300 text-sm">Tutorial Completed</span>
                      <Badge className="bg-purple-500/20 text-purple-400">{betaMetrics?.users?.tutorial_completion_rate}</Badge>
                    </div>
                    <Progress value={parseFloat(betaMetrics?.users?.tutorial_completion_rate) || 0} className="h-2 bg-slate-700" />
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300 text-sm">Made Prediction</span>
                      <Badge className="bg-red-500/20 text-red-400">{betaMetrics?.predictions?.adoption_rate}</Badge>
                    </div>
                    <Progress value={parseFloat(betaMetrics?.predictions?.adoption_rate) || 0} className="h-2 bg-slate-700" />
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300 text-sm">Redeemed Product</span>
                      <Badge className="bg-green-500/20 text-green-400">{betaMetrics?.redemptions?.adoption_rate}</Badge>
                    </div>
                    <Progress value={parseFloat(betaMetrics?.redemptions?.adoption_rate) || 0} className="h-2 bg-slate-700" />
                  </div>
                </CardContent>
              </Card>

              {/* Invite Status */}
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white text-lg flex items-center gap-2">
                    <Ticket className="h-5 w-5 text-yellow-400" />
                    Invite Codes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <div className="text-2xl font-bold text-white">{betaMetrics?.invites?.total_generated || 0}</div>
                      <div className="text-xs text-slate-400">Generated</div>
                    </div>
                    <div className="bg-green-500/10 rounded-lg p-4">
                      <div className="text-2xl font-bold text-green-400">{betaMetrics?.invites?.used || 0}</div>
                      <div className="text-xs text-slate-400">Used</div>
                    </div>
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <div className="text-2xl font-bold text-slate-300">{betaMetrics?.invites?.unused || 0}</div>
                      <div className="text-xs text-slate-400">Available</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Top Predictors */}
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white text-lg flex items-center gap-2">
                    <Trophy className="h-5 w-5 text-yellow-400" />
                    Top Predictors
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {betaMetrics?.leaderboard?.top_predictors?.length > 0 ? (
                    <div className="space-y-3">
                      {betaMetrics.leaderboard.top_predictors.map((user, idx) => (
                        <div key={idx} className="flex items-center justify-between bg-slate-800/50 rounded-lg p-3">
                          <div className="flex items-center gap-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                              idx === 0 ? 'bg-yellow-500 text-black' : 
                              idx === 1 ? 'bg-slate-400 text-black' : 
                              idx === 2 ? 'bg-amber-700 text-white' : 'bg-slate-700 text-white'
                            }`}>
                              {idx + 1}
                            </div>
                            <div>
                              <div className="text-white font-medium text-sm">{user.name}</div>
                              <div className="text-xs text-slate-400">{user.email}</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-green-400 font-bold">{user.correct_predictions || 0}</div>
                            <div className="text-xs text-slate-400">correct</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center text-slate-400 py-4">No predictions yet</p>
                  )}
                </CardContent>
              </Card>

              {/* Support Tickets */}
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white text-lg flex items-center gap-2">
                    <AlertCircle className="h-5 w-5 text-red-400" />
                    Support
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div className="bg-slate-800/50 rounded-lg p-4">
                      <div className="text-2xl font-bold text-white">{betaMetrics?.support?.total_tickets || 0}</div>
                      <div className="text-xs text-slate-400">Total Tickets</div>
                    </div>
                    <div className={`rounded-lg p-4 ${betaMetrics?.support?.open_tickets > 0 ? 'bg-red-500/10' : 'bg-green-500/10'}`}>
                      <div className={`text-2xl font-bold ${betaMetrics?.support?.open_tickets > 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {betaMetrics?.support?.open_tickets || 0}
                      </div>
                      <div className="text-xs text-slate-400">Open</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Add Product Tab */}
          <TabsContent value="products">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">Create New Product</CardTitle>
                <CardDescription className="text-slate-400">Add a new product to the shop</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateProduct} className="space-y-4">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name" className="text-slate-200">Product Name</Label>
                      <Input
                        id="name"
                        value={newProduct.name}
                        onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                        required
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="brand" className="text-slate-200">Brand</Label>
                      <Input
                        id="brand"
                        value={newProduct.brand}
                        onChange={(e) => setNewProduct({ ...newProduct, brand: e.target.value })}
                        required
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="description" className="text-slate-200">Description</Label>
                    <Textarea
                      id="description"
                      value={newProduct.description}
                      onChange={(e) => setNewProduct({ ...newProduct, description: e.target.value })}
                      required
                      className="bg-slate-800 border-slate-700 text-white"
                    />
                  </div>

                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="category" className="text-slate-200">Category</Label>
                      <select
                        id="category"
                        value={newProduct.category}
                        onChange={(e) => setNewProduct({ ...newProduct, category: e.target.value })}
                        className="w-full bg-slate-800 border border-slate-700 text-white rounded-md px-3 py-2"
                      >
                        <option value="electronics">Electronics</option>
                        <option value="vouchers">Vouchers</option>
                        <option value="fashion">Fashion</option>
                        <option value="groceries">Groceries</option>
                        <option value="recharge">Recharge</option>
                        <option value="food">Food</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="coin_price" className="text-slate-200">Coin Price</Label>
                      <Input
                        id="coin_price"
                        type="number"
                        value={newProduct.coin_price}
                        onChange={(e) => setNewProduct({ ...newProduct, coin_price: e.target.value })}
                        required
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="stock" className="text-slate-200">Stock</Label>
                      <Input
                        id="stock"
                        type="number"
                        value={newProduct.stock}
                        onChange={(e) => setNewProduct({ ...newProduct, stock: e.target.value })}
                        required
                        className="bg-slate-800 border-slate-700 text-white"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="image_url" className="text-slate-200">Image URL</Label>
                    <Input
                      id="image_url"
                      type="url"
                      value={newProduct.image_url}
                      onChange={(e) => setNewProduct({ ...newProduct, image_url: e.target.value })}
                      required
                      placeholder="https://example.com/image.jpg"
                      className="bg-slate-800 border-slate-700 text-white"
                    />
                  </div>

                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
                  >
                    {loading ? 'Creating...' : 'Create Product'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* All Orders Tab */}
          <TabsContent value="orders">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white">All Redemptions</CardTitle>
                <CardDescription className="text-slate-400">View all user redemptions</CardDescription>
              </CardHeader>
              <CardContent>
                {allOrders.length > 0 ? (
                  <div className="space-y-3">
                    {allOrders.map((order) => (
                      <div key={order.id} className="bg-slate-800/50 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h4 className="font-bold text-white">{order.product_name}</h4>
                            <p className="text-sm text-slate-400">Order ID: {order.id.slice(0, 8)}...</p>
                            <p className="text-xs text-slate-500 mt-1">
                              {new Date(order.order_date).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="text-right">
                            <Badge className="bg-yellow-500/20 text-yellow-400 mb-2">
                              {order.coins_spent} coins
                            </Badge>
                            <Badge className="bg-blue-500/20 text-blue-400 block">
                              {order.status}
                            </Badge>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-slate-400 py-8">No orders yet</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Admin;
