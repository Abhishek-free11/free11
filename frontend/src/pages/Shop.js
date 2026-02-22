import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Coins, Package, ShoppingCart } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const Shop = () => {
  const { user, updateUser } = useAuth();
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [loading, setLoading] = useState(false);

  const categories = [
    { value: 'all', label: 'All Products' },
    { value: 'electronics', label: 'Electronics' },
    { value: 'vouchers', label: 'Vouchers' },
    { value: 'fashion', label: 'Fashion' },
    { value: 'groceries', label: 'Groceries' },
  ];

  useEffect(() => {
    fetchProducts();
  }, []);

  useEffect(() => {
    if (selectedCategory === 'all') {
      setFilteredProducts(products);
    } else {
      setFilteredProducts(products.filter(p => p.category === selectedCategory));
    }
  }, [selectedCategory, products]);

  const fetchProducts = async () => {
    try {
      const response = await api.getProducts();
      setProducts(response.data);
      setFilteredProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const handleRedeem = async () => {
    if (!deliveryAddress.trim()) {
      toast.error('Please enter delivery address');
      return;
    }

    setLoading(true);
    try {
      const response = await api.createRedemption({
        product_id: selectedProduct.id,
        delivery_address: deliveryAddress
      });
      toast.success('🎉 Redemption successful!', {
        description: `${selectedProduct.name} will be delivered soon`
      });
      updateUser({ coins_balance: response.data.new_balance });
      setSelectedProduct(null);
      setDeliveryAddress('');
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Redemption failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-4 py-8" data-testid="shop-page">
        <div className="mb-8">
          <h1 className="text-4xl font-black text-white mb-2">Shop 🛍️</h1>
          <p className="text-slate-400">Redeem your FREE11 Coins for real products</p>
        </div>

        {/* Category Tabs */}
        <div className="mb-8">
          <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
            <TabsList className="bg-slate-900/50 border border-slate-800">
              {categories.map((cat) => (
                <TabsTrigger
                  key={cat.value}
                  value={cat.value}
                  className="data-[state=active]:bg-yellow-500/20 data-[state=active]:text-yellow-400"
                  data-testid={`category-${cat.value}`}
                >
                  {cat.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {/* Products Grid */}
        <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-6">
          {filteredProducts.map((product) => (
            <Card key={product.id} className="bg-slate-900/50 border-slate-800 hover:border-yellow-500/50 transition-all" data-testid={`product-${product.id}`}>
              <CardHeader className="p-0">
                <div className="aspect-square bg-slate-800 rounded-t-lg overflow-hidden">
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                </div>
              </CardHeader>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h3 className="font-bold text-white line-clamp-1">{product.name}</h3>
                    <p className="text-xs text-slate-400">{product.brand}</p>
                  </div>
                  <Badge className="bg-blue-500/20 text-blue-400 text-xs">
                    {product.category}
                  </Badge>
                </div>
                <p className="text-sm text-slate-400 line-clamp-2 mb-4">{product.description}</p>
                <div className="flex items-center justify-between">
                  <Badge className="bg-yellow-500/20 text-yellow-400 px-3 py-1">
                    <Coins className="h-3 w-3 mr-1" />
                    {product.coin_price}
                  </Badge>
                  <Badge variant="outline" className="text-slate-300 border-slate-600">
                    Stock: {product.stock}
                  </Badge>
                </div>
              </CardContent>
              <CardFooter className="p-4 pt-0">
                <Button
                  onClick={() => setSelectedProduct(product)}
                  disabled={product.stock === 0 || user?.coins_balance < product.coin_price}
                  className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
                  data-testid={`redeem-product-${product.id}`}
                >
                  {product.stock === 0 ? 'Out of Stock' :
                   user?.coins_balance < product.coin_price ? 'Insufficient Coins' :
                   'Redeem Now'}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {filteredProducts.length === 0 && (
          <div className="text-center py-20">
            <Package className="h-20 w-20 text-slate-700 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-slate-400 mb-2">No products found</h3>
            <p className="text-slate-500">Try selecting a different category</p>
          </div>
        )}
      </div>

      {/* Redemption Dialog */}
      <Dialog open={!!selectedProduct} onOpenChange={() => setSelectedProduct(null)}>
        <DialogContent className="bg-slate-900 border-slate-800" data-testid="redemption-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl text-white flex items-center gap-2">
              <ShoppingCart className="h-6 w-6 text-yellow-400" />
              Confirm Redemption
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Review your order details and provide delivery address
            </DialogDescription>
          </DialogHeader>

          {selectedProduct && (
            <div className="space-y-6">
              <div className="flex gap-4">
                <img
                  src={selectedProduct.image_url}
                  alt={selectedProduct.name}
                  className="w-24 h-24 object-cover rounded-lg bg-slate-800"
                />
                <div className="flex-1">
                  <h3 className="font-bold text-white text-lg">{selectedProduct.name}</h3>
                  <p className="text-sm text-slate-400">{selectedProduct.brand}</p>
                  <Badge className="bg-yellow-500/20 text-yellow-400 mt-2">
                    <Coins className="h-3 w-3 mr-1" />
                    {selectedProduct.coin_price} coins
                  </Badge>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="address" className="text-slate-200">Delivery Address</Label>
                <Input
                  id="address"
                  placeholder="Enter your full delivery address"
                  value={deliveryAddress}
                  onChange={(e) => setDeliveryAddress(e.target.value)}
                  className="bg-slate-800 border-slate-700 text-white"
                  data-testid="delivery-address-input"
                />
              </div>

              <div className="bg-slate-800/50 rounded-lg p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Your Balance</span>
                  <span className="text-white font-bold">{user?.coins_balance} coins</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Product Cost</span>
                  <span className="text-yellow-400 font-bold">-{selectedProduct.coin_price} coins</span>
                </div>
                <div className="border-t border-slate-700 pt-2 flex justify-between">
                  <span className="text-white font-bold">New Balance</span>
                  <span className="text-white font-bold">{user?.coins_balance - selectedProduct.coin_price} coins</span>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setSelectedProduct(null)}
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Cancel
            </Button>
            <Button
              onClick={handleRedeem}
              disabled={loading}
              className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
              data-testid="confirm-redemption-btn"
            >
              {loading ? 'Processing...' : 'Confirm Redemption'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Shop;
