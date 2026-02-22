import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Users, ShoppingBag, Coins, TrendingUp, Package, Plus } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const Admin = () => {
  const [analytics, setAnalytics] = useState(null);
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

  useEffect(() => {
    fetchAnalytics();
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

  const fetchAllOrders = async () => {
    try {
      const response = await api.getAllRedemptions();
      setAllOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
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
      <div className="container mx-auto px-4 py-8" data-testid="admin-page">
        <div className="mb-8">
          <h1 className="text-4xl font-black text-white mb-2">Admin Dashboard 🛡️</h1>
          <p className="text-slate-400">Manage products and track platform analytics</p>
        </div>

        {/* Analytics Cards */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="bg-gradient-to-br from-blue-500/20 to-cyan-600/20 border-blue-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-blue-200">Total Users</CardTitle>
              <Users className="h-4 w-4 text-blue-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-400">{analytics?.total_users || 0}</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500/20 to-emerald-600/20 border-green-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-green-200">Total Products</CardTitle>
              <ShoppingBag className="h-4 w-4 text-green-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-400">{analytics?.total_products || 0}</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-yellow-500/20 to-amber-600/20 border-yellow-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-yellow-200">Total Redemptions</CardTitle>
              <Package className="h-4 w-4 text-yellow-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-400">{analytics?.total_redemptions || 0}</div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500/20 to-pink-600/20 border-purple-500/30">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-purple-200">Coins in Circulation</CardTitle>
              <Coins className="h-4 w-4 text-purple-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-400">{analytics?.total_coins_in_circulation || 0}</div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="products" className="space-y-6">
          <TabsList className="bg-slate-900/50 border border-slate-800">
            <TabsTrigger value="products" className="data-[state=active]:bg-yellow-500/20 data-[state=active]:text-yellow-400">
              <Plus className="h-4 w-4 mr-2" />
              Add Product
            </TabsTrigger>
            <TabsTrigger value="orders" className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-400">
              <Package className="h-4 w-4 mr-2" />
              All Orders
            </TabsTrigger>
          </TabsList>

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