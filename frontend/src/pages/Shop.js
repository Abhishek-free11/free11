import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import EmptyState from '../components/EmptyState';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Coins, Package, ShoppingCart, Tag, Shield, Lock, Gift, CheckCircle, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { playCelebrationSound } from '../utils/sounds';
import confetti from 'canvas-confetti';

const Shop = () => {
  const { user, updateUser } = useAuth();
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [isFirstRedemption, setIsFirstRedemption] = useState(true);
  const [myVouchers, setMyVouchers] = useState([]);
  const [loadingVouchers, setLoadingVouchers] = useState(false);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [lastRedeemedProduct, setLastRedeemedProduct] = useState(null);

  const categories = [
    { value: 'all', label: 'All Products' },
    { value: 'recharge', label: 'Recharge' },
    { value: 'ott', label: 'OTT' },
    { value: 'food', label: 'Food' },
    { value: 'vouchers', label: 'Vouchers' },
    { value: 'electronics', label: 'Electronics' },
    { value: 'fashion', label: 'Fashion' },
    { value: 'groceries', label: 'Groceries' },
  ];

  useEffect(() => {
    fetchProducts();
    checkFirstRedemption();
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
      // Sort by coin_price ascending so impulse rewards show first
      const sorted = response.data.sort((a, b) => a.coin_price - b.coin_price);
      setProducts(sorted);
      setFilteredProducts(sorted);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  const checkFirstRedemption = async () => {
    try {
      const response = await api.getRedemptions();
      setIsFirstRedemption(response.data.length === 0);
    } catch (error) {
      console.error('Error checking redemptions:', error);
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
      
      // Store product for success dialog
      setLastRedeemedProduct(selectedProduct);
      
      // Close redemption dialog
      setSelectedProduct(null);
      setDeliveryAddress('');
      
      // Update user balance
      updateUser({ coins_balance: response.data.new_balance });
      
      // GUARDRAIL: Celebration triggers only once per redemption (inside API success handler)
      // Sound respects user preference (OFF by default, opt-in via settings)
      playCelebrationSound();
      
      // Confetti burst for delight - single trigger per redemption
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#fbbf24', '#10b981', '#3b82f6', '#a855f7']
      });
      
      // Show success dialog with delight message
      setShowSuccessDialog(true);
      
      setIsFirstRedemption(false);
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Redemption failed');
    } finally {
      setLoading(false);
    }
  };

  const getCoinsAway = (product) => {
    const diff = product.coin_price - (user?.coins_balance || 0);
    return diff > 0 ? diff : 0;
  };

  const canAfford = (product) => {
    return (user?.coins_balance || 0) >= product.coin_price;
  };

  const meetsLevelRequirement = (product) => {
    return (user?.level || 1) >= (product.min_level_required || 1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 pb-20 md:pb-0">
      <Navbar />
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl" data-testid="shop-page">
        <div className="mb-4 sm:mb-8">
          <h1 className="text-2xl sm:text-4xl font-black text-white mb-1 sm:mb-2">Shop 🛍️</h1>
          <p className="text-slate-400 text-sm sm:text-base">Redeem your FREE11 Coins for real products</p>
        </div>

        {/* Category Tabs */}
        <div className="mb-4 sm:mb-8 overflow-x-auto -mx-3 px-3 sm:mx-0 sm:px-0">
          <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
            <TabsList className="bg-slate-900/50 border border-slate-800 inline-flex w-auto">
              {categories.map((cat) => (
                <TabsTrigger
                  key={cat.value}
                  value={cat.value}
                  className="data-[state=active]:bg-yellow-500/20 data-[state=active]:text-yellow-400 whitespace-nowrap text-xs sm:text-sm"
                  data-testid={`category-${cat.value}`}
                >
                  {cat.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {/* Products Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-6">
          {filteredProducts.map((product) => (
            <Card 
              key={product.id} 
              className={`bg-slate-900/50 border-slate-800 hover:border-yellow-500/50 transition-all ${
                !meetsLevelRequirement(product) ? 'opacity-60' : ''
              }`} 
              data-testid={`product-${product.id}`}
            >
              <CardHeader className="p-0 relative">
                <div className="aspect-square bg-slate-800 rounded-t-lg overflow-hidden relative">
                  <img
                    src={product.image_url}
                    alt={product.name}
                    className="w-full h-full object-cover"
                  />
                  {/* Brand-funded tag */}
                  {product.funded_by_brand && (
                    <Badge className="absolute top-2 left-2 bg-green-500/90 text-white text-xs">
                      <Tag className="h-3 w-3 mr-1" />
                      Brand-funded
                    </Badge>
                  )}
                  {/* Limited drop badge */}
                  {product.is_limited_drop && (
                    <Badge className="absolute top-2 right-2 bg-red-500/90 text-white text-xs animate-pulse">
                      Limited Drop
                    </Badge>
                  )}
                  {/* Level lock overlay */}
                  {!meetsLevelRequirement(product) && (
                    <div className="absolute inset-0 bg-slate-900/80 flex items-center justify-center">
                      <div className="text-center">
                        <Lock className="h-8 w-8 text-slate-400 mx-auto mb-2" />
                        <p className="text-sm text-slate-300">Level {product.min_level_required}+ required</p>
                      </div>
                    </div>
                  )}
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
                
                {/* "X coins away" nudge for locked items */}
                {!canAfford(product) && meetsLevelRequirement(product) && (
                  <div className="mt-3 p-2 bg-slate-800/50 rounded text-center">
                    <p className="text-xs text-yellow-400">
                      ⚡ {getCoinsAway(product)} coins away from unlocking!
                    </p>
                  </div>
                )}
              </CardContent>
              <CardFooter className="p-4 pt-0">
                <Button
                  onClick={() => setSelectedProduct(product)}
                  disabled={product.stock === 0 || !canAfford(product) || !meetsLevelRequirement(product)}
                  className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
                  data-testid={`redeem-product-${product.id}`}
                >
                  {product.stock === 0 ? 'Out of Stock' :
                   !meetsLevelRequirement(product) ? `Level ${product.min_level_required} Required` :
                   !canAfford(product) ? `${getCoinsAway(product)} Coins Away` :
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
                <div className="relative">
                  <img
                    src={selectedProduct.image_url}
                    alt={selectedProduct.name}
                    className="w-24 h-24 object-cover rounded-lg bg-slate-800"
                  />
                  {selectedProduct.funded_by_brand && (
                    <Badge className="absolute -top-2 -left-2 bg-green-500 text-white text-xs">
                      <Tag className="h-3 w-3" />
                    </Badge>
                  )}
                </div>
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

              {/* First Redemption Reminder */}
              {isFirstRedemption && (
                <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                  <div className="flex items-start gap-2">
                    <Shield className="h-4 w-4 text-blue-400 mt-0.5" />
                    <p className="text-xs text-slate-300">
                      <span className="font-medium">First redemption!</span> FREE11 Coins are brand-funded reward tokens. No cash. No betting. Enjoy your reward!
                    </p>
                  </div>
                </div>
              )}
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

      {/* Voucher Delivery Success Dialog - Delight Moment */}
      <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
        <DialogContent className="bg-gradient-to-br from-slate-900 via-slate-900 to-green-900/20 border-green-500/30" data-testid="voucher-success-dialog">
          <div className="text-center py-6">
            {/* Success Icon with Animation */}
            <div className="relative inline-block mb-6">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mx-auto animate-bounce">
                <Gift className="h-10 w-10 text-white" />
              </div>
              <div className="absolute -top-1 -right-1">
                <Sparkles className="h-6 w-6 text-yellow-400 animate-pulse" />
              </div>
            </div>

            {/* Main Headline */}
            <h2 className="text-3xl font-black text-white mb-2" data-testid="success-headline">
              Unlocked! Your reward is ready 🎉
            </h2>

            {/* Sub-copy - Skill Acknowledgment */}
            <p className="text-lg text-green-400 font-medium mb-6" data-testid="success-subcopy">
              You earned this through skill. Enjoy!
            </p>

            {/* Product Info */}
            {lastRedeemedProduct && (
              <div className="bg-slate-800/50 rounded-xl p-4 mb-6 inline-block">
                <div className="flex items-center gap-4">
                  <img
                    src={lastRedeemedProduct.image_url}
                    alt={lastRedeemedProduct.name}
                    className="w-16 h-16 object-cover rounded-lg"
                  />
                  <div className="text-left">
                    <p className="text-white font-bold">{lastRedeemedProduct.name}</p>
                    <p className="text-sm text-slate-400">{lastRedeemedProduct.brand}</p>
                    <Badge className="mt-1 bg-green-500/20 text-green-400 text-xs">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Delivery in progress
                    </Badge>
                  </div>
                </div>
              </div>
            )}

            {/* CTA */}
            <Button
              onClick={() => setShowSuccessDialog(false)}
              className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold px-8"
              data-testid="success-close-btn"
            >
              Continue Shopping
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Shop;
