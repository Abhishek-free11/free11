import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import Navbar from '../components/Navbar';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Coins, Lock, Gift, CheckCircle, Sparkles, Tag, Target, ShoppingBag, Share2, QrCode, Zap, ExternalLink, Loader2, TrendingUp, Package, Phone, Smartphone, Wifi } from 'lucide-react';
import SkillDisclaimerModal from '../components/SkillDisclaimerModal';
import ShareCard from '../components/ShareCard';
import { AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import api from '../utils/api';
import { playCelebrationSound } from '../utils/sounds';
import confetti from 'canvas-confetti';

const Shop = () => {
  const { user, updateUser } = useAuth();
  const { t } = useI18n();
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [deliveryMobile, setDeliveryMobile] = useState('');
  const [loading, setLoading] = useState(false);
  const [isFirstRedemption, setIsFirstRedemption] = useState(true);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [lastRedeemedProduct, setLastRedeemedProduct] = useState(null);
  const [lastVoucherCode] = useState(() => `FREE11-${Math.random().toString(36).slice(2, 8).toUpperCase()}`);
  const [pinnedProductId, setPinnedProductId] = useState(null);
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [showShareCard, setShowShareCard] = useState(false);

  // Smart Commerce Router state
  const [routerDeals, setRouterDeals] = useState([]);
  const [routerDealsLoading, setRouterDealsLoading] = useState(false);
  const [selectedDeal, setSelectedDeal] = useState(null);   // router deal clicked
  const [teaseData, setTeaseData] = useState(null);         // /router/tease response
  const [teaseLoading, setTeaseLoading] = useState(false);
  const [routerSettleLoading, setRouterSettleLoading] = useState(false);
  const [routerResult, setRouterResult] = useState(null);   // /router/settle response
  const [showRouterSuccess, setShowRouterSuccess] = useState(false);
  const [routerDealCategory, setRouterDealCategory] = useState('all');
  // Airtime / Mobile Recharge state
  const [airtimeCatalog, setAirtimeCatalog]       = useState([]);
  const [selectedCarrier, setSelectedCarrier]       = useState(null);
  const [selectedPlan, setSelectedPlan]             = useState(null);
  const [rechargePhone, setRechargePhone]           = useState('');
  const [rechargeLoading, setRechargeLoading]       = useState(false);
  const [showRechargeDialog, setShowRechargeDialog] = useState(false);
  const [rechargeSuccess, setRechargeSuccess]       = useState(null);

  const BACKEND = process.env.REACT_APP_BACKEND_URL;

  const categories = [
    { value: 'all', label: 'All' },
    { value: 'rations', label: 'Rations' },
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
    fetchRouterDeals();
    fetchAirtimeCatalog();
    checkFirstRedemption();
    api.v2GetWishlist().then(r => setPinnedProductId(r.data?.product?.id || null)).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedCategory === 'all') setFilteredProducts(products);
    else setFilteredProducts(products.filter(p => p.category === selectedCategory));
  }, [selectedCategory, products]);

  const fetchProducts = async () => {
    try {
      const response = await api.getProducts();
      // Handle paginated response {products: [], total: N} or legacy flat array
      const raw = response.data;
      const list = Array.isArray(raw) ? raw : (raw?.products || []);
      const sorted = list.sort((a, b) => a.coin_price - b.coin_price);
      setProducts(sorted);
      setFilteredProducts(sorted);
    } catch {}
  };

  const fetchRouterDeals = async () => {
    setRouterDealsLoading(true);
    try {
      const res = await api.v2RouterSkus();
      setRouterDeals(res.data || []);
    } catch {} finally { setRouterDealsLoading(false); }
  };

  const fetchAirtimeCatalog = async () => {
    try {
      const token = localStorage.getItem('free11_token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/airtime/catalog`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setAirtimeCatalog(data.catalog || []);
    } catch {}
  };

  const handleRecharge = async () => {
    if (!selectedPlan || !rechargePhone.trim()) return;
    setRechargeLoading(true);
    try {
      const token = localStorage.getItem('free11_token');
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/airtime/recharge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ plan_id: selectedPlan.id, phone: rechargePhone.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Recharge failed');
      setRechargeSuccess(data);
      setShowRechargeDialog(false);
      playCelebrationSound();
      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 }, colors: ['#C6A052', '#4ade80', '#3B82F6'] });
      toast.success(data.mock
        ? 'Recharge queued! Will be delivered once our provider activates.'
        : `₹${data.inr_amount} recharge sent to ${data.phone}!`,
        { duration: 6000 });
      if (data.coins_used) updateUser({ coins_balance: (user?.coins_balance || 0) - data.coins_used });
    } catch (e) {
      toast.error(e.message || 'Recharge failed');
    } finally { setRechargeLoading(false); }
  };

  const handleDealClick = async (deal) => {
    setSelectedDeal(deal);
    setTeaseLoading(true);
    setTeaseData(null);
    setRouterResult(null);
    try {
      const res = await api.v2RouterTease(deal.sku, geoState);
      setTeaseData(res.data);
    } catch { toast.error('Could not load deal preview'); setSelectedDeal(null); }
    finally { setTeaseLoading(false); }
  };

  const handleRouterSettle = async () => {
    if (!selectedDeal || !teaseData?.best) return;
    setRouterSettleLoading(true);
    const coinCost = teaseData.best.coin_price;
    if ((user?.coins_balance || 0) < coinCost) {
      toast.error(`Need ${coinCost} coins, you have ${user?.coins_balance || 0}`);
      setRouterSettleLoading(false);
      return;
    }
    try {
      const res = await api.v2RouterSettle({ sku: selectedDeal.sku, coins_used: coinCost, geo_state: geoState });
      const result = res.data;
      setRouterResult(result);
      updateUser({ coins_balance: result.new_balance });

      if (result.status === 'redirect') {
        window.open(result.redirect_url, '_blank', 'noopener,noreferrer');
        setSelectedDeal(null);
        toast.success(`Opening ${teaseData.best.provider_name} in a new tab`, { duration: 4000 });
      } else if (result.status === 'delivered') {
        setSelectedDeal(null);
        playCelebrationSound();
        confetti({ particleCount: 120, spread: 70, origin: { y: 0.6 }, colors: ['#C6A052', '#E0B84F', '#4ade80'] });
        setShowRouterSuccess(true);
      } else if (result.status === 'placed') {
        setSelectedDeal(null);
        toast.success(`Order placed! Track via order ID: ${result.order_id}`, { duration: 6000 });
        playCelebrationSound();
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Redemption failed. Try again.');
    } finally { setRouterSettleLoading(false); }
  };

  const checkFirstRedemption = async () => {
    try {
      const response = await api.getRedemptions();
      setIsFirstRedemption(response.data.length === 0);
    } catch {}
  };

  const handleRedeem = async () => {
    if (!deliveryMobile.trim() || deliveryMobile.length < 10) {
      toast.error(t('shop_page.valid_mobile'));
      return;
    }
    setLoading(true);
    try {
      const response = await api.createRedemption({ product_id: selectedProduct.id, delivery_mobile: deliveryMobile });
      setLastRedeemedProduct(selectedProduct);
      setSelectedProduct(null);
      setDeliveryMobile('');
      updateUser({ coins_balance: response.data.new_balance });
      playCelebrationSound();
      confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 }, colors: ['#C6A052', '#E0B84F', '#4ade80'] });
      setShowSuccessDialog(true);
      setIsFirstRedemption(false);
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Redemption failed');
    } finally { setLoading(false); }
  };

  const canAfford = (product) => (user?.coins_balance || 0) >= product.coin_price;
  const meetsLevel = (product) => (user?.level || 1) >= (product.min_level_required || 1);
  const coinsAway = (product) => Math.max(0, product.coin_price - (user?.coins_balance || 0));

  return (
    <div className="min-h-screen bg-[#0F1115] pb-28 md:pb-6" data-testid="shop-page">
      <div className="fixed pointer-events-none" style={{ top: 0, left: '50%', transform: 'translateX(-50%)', width: '70vw', height: '30vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.04) 0%, transparent 70%)', zIndex: 0 }} />
      <Navbar />

      <div className="relative z-10 max-w-screen-xl mx-auto px-3 sm:px-4 py-4">
        {/* Header */}
        <div className="mb-5 animate-slide-up">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="font-heading text-3xl sm:text-4xl tracking-widest text-white mb-1">
                FREE <span style={{ color: '#C6A052' }}>SHOP</span>
              </h1>
              <p className="text-sm" style={{ color: '#8A9096' }}>{t('shop_page.subtitle')}</p>
            </div>
            <button
              onClick={() => setShowDisclaimer(true)}
              className="flex items-center gap-1 text-xs px-2 py-1 rounded-full mt-1"
              style={{ background: 'rgba(74,222,128,0.08)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.2)' }}
              data-testid="shop-skill-badge"
            >
              <span className="text-[9px]">🛡</span> Skill-Based
            </button>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <Coins className="h-4 w-4" style={{ color: '#C6A052' }} />
            <span className="font-numbers text-xl font-black text-white">{user?.coins_balance || 0}</span>
            <span className="text-xs" style={{ color: '#8A9096' }}>coins available</span>
            {user?.coins_balance > 0 && (() => {
              const affordable = products.filter(p => (user?.coins_balance || 0) >= p.coin_price);
              return affordable.length > 0 ? (
                <span className="ml-1 text-xs px-2 py-0.5 rounded-full font-medium"
                  style={{ background: 'rgba(74,222,128,0.12)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.2)' }}>
                  You can redeem {affordable.length} item{affordable.length > 1 ? 's' : ''} now
                </span>
              ) : null;
            })()}
          </div>
        </div>

        {showDisclaimer && <SkillDisclaimerModal isOpen={showDisclaimer} onClose={() => setShowDisclaimer(false)} />}
        <AnimatePresence>
          {showShareCard && (
            <ShareCard
              type="redemption"
              data={{ productName: lastRedeemedProduct?.name, coinsUsed: lastRedeemedProduct?.coin_price, imageUrl: lastRedeemedProduct?.image_url }}
              onClose={() => setShowShareCard(false)}
            />
          )}
        </AnimatePresence>

        {/* ── Smart Deals Router Section ─────────────────────────────── */}
        {/* ── MOBILE RECHARGE SECTION ─────────────────────────────── */}
        <div className="mb-6 animate-slide-up" style={{ animationDelay: '0.05s' }}>
          <div className="flex items-center gap-2 mb-3">
            <Smartphone className="h-4 w-4" style={{ color: '#C6A052' }} />
            <span className="font-heading text-sm tracking-widest text-white">MOBILE RECHARGE</span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase"
              style={{ background: 'rgba(74,222,128,0.12)', color: '#4ade80', letterSpacing: '0.08em' }}>
              LIVE
            </span>
          </div>

          {/* Carrier selector */}
          <div className="grid grid-cols-2 gap-2 mb-3" data-testid="carrier-grid">
            {airtimeCatalog.map(carrier => (
              <button key={carrier.carrier}
                data-testid={`carrier-${carrier.carrier}`}
                onClick={() => setSelectedCarrier(selectedCarrier?.carrier === carrier.carrier ? null : carrier)}
                className="flex items-center gap-2.5 p-3 rounded-xl transition-all text-left"
                style={{
                  background: selectedCarrier?.carrier === carrier.carrier ? 'rgba(198,160,82,0.15)' : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${selectedCarrier?.carrier === carrier.carrier ? 'rgba(198,160,82,0.4)' : 'rgba(255,255,255,0.07)'}`,
                }}>
                <Wifi className="h-5 w-5 flex-shrink-0" style={{ color: carrier.color || '#C6A052' }} />
                <div>
                  <p className="text-xs font-semibold text-white leading-tight">{carrier.name}</p>
                  <p className="text-[10px]" style={{ color: '#8A9096' }}>{carrier.plans?.length} plans</p>
                </div>
              </button>
            ))}
          </div>

          {/* Plans for selected carrier */}
          {selectedCarrier && (
            <div className="space-y-2" data-testid="recharge-plans">
              {selectedCarrier.plans.map(plan => {
                const canAfford = (user?.coins_balance || 0) >= plan.coins;
                return (
                  <button key={plan.id}
                    data-testid={`plan-${plan.id}`}
                    onClick={() => { if (canAfford) { setSelectedPlan(plan); setShowRechargeDialog(true); } else toast.error(`Need ${plan.coins} coins`); }}
                    className="w-full flex items-center justify-between p-3 rounded-xl transition-all"
                    style={{
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid rgba(255,255,255,0.07)',
                      opacity: canAfford ? 1 : 0.5,
                    }}>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0"
                        style={{ background: 'rgba(198,160,82,0.1)' }}>
                        <span className="font-heading text-gold text-sm">₹{plan.inr}</span>
                      </div>
                      <div className="text-left">
                        <p className="text-xs font-semibold text-white">{plan.desc}</p>
                        <p className="text-[10px]" style={{ color: '#8A9096' }}>{plan.validity} • {plan.data}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <Coins className="h-3.5 w-3.5" style={{ color: '#C6A052' }} />
                      <span className="font-numbers text-xs font-bold" style={{ color: canAfford ? '#C6A052' : '#8A9096' }}>{plan.coins.toLocaleString()}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Recharge confirmation dialog */}
        <Dialog open={showRechargeDialog} onOpenChange={setShowRechargeDialog}>
          <DialogContent style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.2)' }}>
            <DialogHeader>
              <DialogTitle className="text-white flex items-center gap-2">
                <Smartphone className="h-5 w-5" style={{ color: '#C6A052' }} />
                Confirm Recharge
              </DialogTitle>
              <DialogDescription style={{ color: '#8A9096' }}>
                {selectedPlan && `${selectedCarrier?.name} ₹${selectedPlan.inr} — ${selectedPlan.desc}`}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div>
                <Label className="text-white text-sm mb-1.5 block">Mobile Number</Label>
                <Input
                  data-testid="recharge-phone-input"
                  type="tel"
                  placeholder="10-digit mobile number"
                  value={rechargePhone}
                  onChange={e => setRechargePhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  className="text-white"
                  style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
                  maxLength={10}
                />
              </div>
              {selectedPlan && (
                <div className="p-3 rounded-lg" style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.15)' }}>
                  <div className="flex justify-between text-sm">
                    <span style={{ color: '#8A9096' }}>Recharge Amount</span>
                    <span className="text-white font-semibold">₹{selectedPlan.inr}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span style={{ color: '#8A9096' }}>Coins to deduct</span>
                    <span className="font-numbers font-bold" style={{ color: '#C6A052' }}>{selectedPlan.coins.toLocaleString()} coins</span>
                  </div>
                </div>
              )}
            </div>
            <DialogFooter className="gap-2">
              <button onClick={() => setShowRechargeDialog(false)} className="px-4 py-2 rounded-lg text-sm" style={{ background: 'rgba(255,255,255,0.06)', color: '#8A9096' }}>
                Cancel
              </button>
              <button
                data-testid="confirm-recharge-btn"
                onClick={handleRecharge}
                disabled={rechargeLoading || rechargePhone.length !== 10}
                className="px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2"
                style={{ background: 'linear-gradient(135deg,#C6A052,#E0B84F)', color: '#0F1115', opacity: rechargeLoading || rechargePhone.length !== 10 ? 0.6 : 1 }}>
                {rechargeLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Smartphone className="h-4 w-4" />}
                {rechargeLoading ? 'Processing...' : 'Confirm Recharge'}
              </button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* ── SMART DEALS SECTION ─────────────────────────────────── */}
        <div className="mb-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4" style={{ color: '#C6A052' }} />
              <span className="font-heading text-sm tracking-widest text-white">SMART DEALS</span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase"
                style={{ background: 'rgba(198,160,82,0.15)', color: '#C6A052', letterSpacing: '0.08em' }}>
                AUTO-ROUTED
              </span>
            </div>
            <span className="text-xs" style={{ color: '#8A9096' }}>{routerDeals.length} deals</span>
          </div>

          {/* Category pills for router deals */}
          <div className="flex gap-1.5 mb-3 overflow-x-auto no-scrollbar pb-1">
            {['all', 'groceries', 'vouchers', 'food', 'electronics', 'fashion', 'lifestyle', 'recharge'].map(cat => (
              <button key={cat} onClick={() => setRouterDealCategory(cat)}
                className="px-3 py-1 rounded-full text-[10px] font-medium whitespace-nowrap shrink-0 transition-all"
                style={routerDealCategory === cat
                  ? { background: 'rgba(198,160,82,0.25)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.4)' }
                  : { background: 'rgba(255,255,255,0.03)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.06)' }}>
                {cat === 'all' ? 'All Deals' : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>

          {routerDealsLoading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="h-5 w-5 animate-spin" style={{ color: '#C6A052' }} />
            </div>
          ) : (
            <div className="overflow-x-auto -mx-3 px-3 no-scrollbar" data-testid="smart-deals-section">
              <div className="flex gap-3" style={{ width: 'max-content' }}>
                {routerDeals
                  .filter(d => routerDealCategory === 'all' || d.category === routerDealCategory)
                  .map((deal) => {
                    const canAffordDeal = (user?.coins_balance || 0) >= deal.coins;
                    const providerColors = {
                      ondc: { bg: 'rgba(74,222,128,0.1)', color: '#4ade80', border: 'rgba(74,222,128,0.2)' },
                      xoxoday: { bg: 'rgba(168,85,247,0.1)', color: '#a855f7', border: 'rgba(168,85,247,0.2)' },
                      amazon: { bg: 'rgba(251,191,36,0.1)', color: '#fbbf24', border: 'rgba(251,191,36,0.2)' },
                      flipkart: { bg: 'rgba(96,165,250,0.1)', color: '#60a5fa', border: 'rgba(96,165,250,0.2)' },
                    };
                    const pc = providerColors[deal.provider] || providerColors.ondc;
                    const etaLabel = deal.provider === 'ondc' ? '~45 min' : 'Instant';
                    const valueRatio = deal.display_price ? Math.round(deal.display_price / deal.coins * 100) : null;

                    return (
                      <div key={deal.sku} className="shrink-0 rounded-2xl overflow-hidden flex flex-col"
                        style={{ width: 160, background: '#1B1E23', border: '1px solid rgba(255,255,255,0.06)' }}
                        data-testid={`router-deal-${deal.sku}`}>

                        {/* Image */}
                        <div className="relative" style={{ height: 100, background: '#141720', overflow: 'hidden' }}>
                          {deal.image ? (
                            <img src={deal.image} alt={deal.name} className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center">
                              <Gift className="h-8 w-8" style={{ color: '#2A2D33' }} />
                            </div>
                          )}
                          {/* Provider badge */}
                          <span className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded text-[9px] font-bold uppercase"
                            style={{ background: pc.bg, color: pc.color, border: `1px solid ${pc.border}` }}>
                            {deal.provider.toUpperCase()}
                          </span>
                          {/* ETA badge */}
                          <span className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded text-[9px] font-medium"
                            style={{ background: 'rgba(0,0,0,0.7)', color: '#e2e8f0' }}>
                            {etaLabel}
                          </span>
                        </div>

                        {/* Info */}
                        <div className="p-2.5 flex-1 flex flex-col gap-1.5">
                          <p className="text-xs font-bold text-white line-clamp-2 leading-tight">{deal.name}</p>
                          <div className="flex items-center justify-between">
                            <span className="flex items-center gap-0.5 text-xs font-black" style={{ color: '#C6A052' }}>
                              <Coins className="h-3 w-3" /> {deal.coins}
                            </span>
                            {deal.display_price && (
                              <span className="text-[9px] font-medium" style={{ color: '#8A9096' }}>
                                ₹{deal.display_price}
                              </span>
                            )}
                          </div>
                          {valueRatio && valueRatio >= 80 && (
                            <div className="flex items-center gap-0.5">
                              <TrendingUp className="h-2.5 w-2.5" style={{ color: '#4ade80' }} />
                              <span className="text-[9px]" style={{ color: '#4ade80' }}>
                                {valueRatio}% value
                              </span>
                            </div>
                          )}
                          <button
                            onClick={() => handleDealClick(deal)}
                            disabled={!canAffordDeal}
                            className="w-full h-7 rounded-lg text-[10px] font-bold mt-auto transition-all disabled:opacity-40"
                            style={canAffordDeal
                              ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }
                              : { background: 'rgba(255,255,255,0.04)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.08)' }}
                            data-testid={`router-redeem-${deal.sku}`}>
                            {canAffordDeal ? 'Redeem' : `${deal.coins - (user?.coins_balance || 0)} more`}
                          </button>
                        </div>
                      </div>
                    );
                  })}
              </div>
              {routerDeals.filter(d => routerDealCategory === 'all' || d.category === routerDealCategory).length === 0 && (
                <p className="text-xs text-center py-4" style={{ color: '#8A9096' }}>No deals in this category</p>
              )}
            </div>
          )}

          <div className="mt-2 flex items-center gap-1.5">
            <div className="h-px flex-1" style={{ background: 'rgba(255,255,255,0.05)' }} />
            <span className="text-[9px] uppercase tracking-widest" style={{ color: '#3A3D43' }}>Existing Catalogue</span>
            <div className="h-px flex-1" style={{ background: 'rgba(255,255,255,0.05)' }} />
          </div>
        </div>

        {/* Category tabs */}
        <div className="mb-5 overflow-x-auto -mx-3 px-3 scrollbar-hide">
          <div className="flex gap-2 w-max">
            {categories.map((cat) => (
              <button key={cat.value} onClick={() => setSelectedCategory(cat.value)}
                className="px-4 py-1.5 rounded-full text-xs font-heading tracking-wider whitespace-nowrap transition-all"
                style={selectedCategory === cat.value
                  ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115', fontWeight: 700 }
                  : { background: 'rgba(255,255,255,0.04)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.08)' }}
                data-testid={`category-${cat.value}`}>
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Products Grid */}
        {filteredProducts.length === 0 ? (
          <div className="text-center py-16">
            <ShoppingBag className="h-16 w-16 mx-auto mb-4" style={{ color: '#2A2D33' }} />
            <h3 className="text-lg font-bold text-white mb-2">{t('shop_page.no_products')}</h3>
            <p className="text-sm" style={{ color: '#8A9096' }}>{t('shop_page.try_category')}</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
            {filteredProducts.map((product) => (
              <div key={product.id}
                className={`card-broadcast overflow-hidden hover-lift flex flex-col transition-all ${!meetsLevel(product) ? 'opacity-50' : ''}`}
                data-testid={`product-${product.id}`}>
                {/* Image */}
                <div className="aspect-square relative overflow-hidden" style={{ background: '#1B1E23' }}>
                  <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
                  {product.funded_by_brand && (
                    <span className="absolute top-2 left-2 px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1"
                      style={{ background: 'rgba(74,222,128,0.9)', color: '#fff' }}>
                      <Tag className="h-2.5 w-2.5" /> {t('shop_page.brand_funded')}
                    </span>
                  )}
                  {product.is_limited_drop && (
                    <span className="absolute top-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold animate-live-pulse"
                      style={{ background: 'rgba(239,68,68,0.9)', color: '#fff' }}>
                      {t('shop_page.limited_drop')}
                    </span>
                  )}
                  {!meetsLevel(product) && (
                    <div className="absolute inset-0 flex items-center justify-center" style={{ background: 'rgba(15,17,21,0.85)' }}>
                      <div className="text-center">
                        <Lock className="h-8 w-8 mx-auto mb-1" style={{ color: '#8A9096' }} />
                        <p className="text-xs" style={{ color: '#BFC3C8' }}>Lv {product.min_level_required}+</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="p-3 flex-1 flex flex-col">
                  <div className="flex items-start justify-between mb-1">
                    <h3 className="text-sm font-bold text-white line-clamp-1 flex-1">{product.name}</h3>
                  </div>
                  <p className="text-[10px] mb-1" style={{ color: '#8A9096' }}>{product.brand}</p>
                  <p className="text-xs line-clamp-2 mb-3 flex-1" style={{ color: '#8A9096' }}>{product.description}</p>

                  {/* Price + stock + ₹ value */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5">
                      <span className="coin-indicator flex items-center gap-1 px-2 py-0.5 text-xs font-bold">
                        <Coins className="h-3 w-3" /> {product.coin_price}
                      </span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded-full font-medium"
                        style={{ background: 'rgba(74,222,128,0.1)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.15)' }}>
                        ≈ ₹{Math.round(product.coin_price * 0.8)}
                      </span>
                    </div>
                    <span className="text-[10px]" style={{ color: '#8A9096' }}>
                      {product.stock < 20 && product.stock > 0 ? (
                        <span style={{ color: '#f97316' }}>Only {product.stock} left!</span>
                      ) : `${product.stock} in stock`}
                    </span>
                  </div>

                  {!canAfford(product) && meetsLevel(product) && (
                    <div className="mb-2 px-2 py-1.5 rounded-lg text-center text-[10px]"
                      style={{ background: 'rgba(198,160,82,0.08)', color: '#C6A052' }}>
                      {coinsAway(product)} coins away!
                    </div>
                  )}

                  <button
                    onClick={() => setSelectedProduct(product)}
                    disabled={product.stock === 0 || !canAfford(product) || !meetsLevel(product)}
                    className="btn-gold w-full h-9 rounded-lg text-xs disabled:opacity-40 ripple"
                    data-testid={`redeem-product-${product.id}`}>
                    {product.stock === 0 ? t('shop_page.out_of_stock') :
                     !meetsLevel(product) ? `Lv ${product.min_level_required} required` :
                     !canAfford(product) ? `${coinsAway(product)} ${t('shop_page.coins_away')}` :
                     t('shop_page.redeem_now')}
                  </button>

                  {!canAfford(product) && meetsLevel(product) && product.stock > 0 && (
                    <button
                      className="w-full h-8 rounded-lg text-xs mt-1.5 transition-all"
                      style={pinnedProductId === product.id
                        ? { background: 'rgba(198,160,82,0.1)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.3)' }
                        : { background: 'transparent', color: '#8A9096', border: '1px solid rgba(255,255,255,0.08)' }}
                      data-testid={`set-goal-${product.id}`}
                      onClick={async () => {
                        if (pinnedProductId === product.id) {
                          await api.v2UnpinWishlist().catch(() => {});
                          setPinnedProductId(null);
                          toast.success('Goal cleared');
                        } else {
                          await api.v2PinWishlist(product.id).catch(() => {});
                          setPinnedProductId(product.id);
                          toast.success(`Goal set: ${product.name}`);
                        }
                      }}>
                      <Target className="h-3 w-3 inline mr-1" />
                      {pinnedProductId === product.id ? 'Goal set ✓' : 'Set as Goal'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Redemption Dialog */}
      <Dialog open={!!selectedProduct} onOpenChange={() => setSelectedProduct(null)}>
        <DialogContent className="max-w-sm mx-4" style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.2)' }} data-testid="redemption-dialog">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Gift className="h-5 w-5" style={{ color: '#C6A052' }} /> Confirm Redemption
            </DialogTitle>
            <DialogDescription style={{ color: '#8A9096' }}>{t('shop_page.voucher_delivery')}</DialogDescription>
          </DialogHeader>

          {selectedProduct && (
            <div className="space-y-4">
              <div className="flex gap-3">
                <img src={selectedProduct.image_url} alt={selectedProduct.name}
                  className="w-20 h-20 object-cover rounded-xl flex-shrink-0"
                  style={{ background: '#0F1115' }} />
                <div>
                  <h3 className="font-bold text-white">{selectedProduct.name}</h3>
                  <p className="text-sm" style={{ color: '#8A9096' }}>{selectedProduct.brand}</p>
                  <span className="coin-indicator inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold mt-1">
                    <Coins className="h-3 w-3" /> {selectedProduct.coin_price} coins
                  </span>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label className="text-xs uppercase tracking-wider" style={{ color: '#8A9096' }}>Mobile Number</Label>
                <Input type="tel" placeholder="+91 9876543210" value={deliveryMobile}
                  onChange={(e) => setDeliveryMobile(e.target.value.replace(/[^\d+]/g, '').slice(0, 13))}
                  className="h-11 text-white border"
                  style={{ background: '#0F1115', borderColor: 'rgba(198,160,82,0.2)', color: '#fff' }}
                  data-testid="delivery-mobile-input" />
              </div>

              <div className="p-3 rounded-xl space-y-2 text-sm" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <div className="flex justify-between">
                  <span style={{ color: '#8A9096' }}>Balance</span>
                  <span className="font-bold text-white">{user?.coins_balance}</span>
                </div>
                <div className="flex justify-between">
                  <span style={{ color: '#8A9096' }}>Cost</span>
                  <span className="font-bold" style={{ color: '#f87171' }}>-{selectedProduct.coin_price}</span>
                </div>
                <div className="flex justify-between border-t pt-2" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                  <span className="font-bold text-white">New Balance</span>
                  <span className="font-bold text-white">{user?.coins_balance - selectedProduct.coin_price}</span>
                </div>
              </div>
            </div>
          )}

          <DialogFooter className="gap-2">
            <button onClick={() => setSelectedProduct(null)} className="btn-outline-gold px-4 h-10 rounded-lg text-sm flex-1">
              Cancel
            </button>
            <button onClick={handleRedeem} disabled={loading} className="btn-gold px-4 h-10 rounded-lg text-sm flex-1 disabled:opacity-50"
              data-testid="confirm-redemption-btn">
              {loading ? 'Processing...' : 'Confirm'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Success Dialog */}
      <Dialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog}>
        <DialogContent className="max-w-sm mx-4 text-center" style={{ background: '#1B1E23', border: '1px solid rgba(74,222,128,0.3)' }} data-testid="voucher-success-dialog">
          <div className="py-4">
            <div className="relative inline-block mb-4">
              <div className="w-20 h-20 rounded-full mx-auto flex items-center justify-center"
                style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)' }}>
                {lastRedeemedProduct?.image_url ? (
                  <img src={lastRedeemedProduct.image_url} alt="" className="w-full h-full object-cover rounded-full" />
                ) : (
                  <Gift className="h-10 w-10 text-white" />
                )}
              </div>
              <Sparkles className="h-6 w-6 absolute -top-1 -right-1 animate-live-pulse" style={{ color: '#C6A052' }} />
            </div>
            <h2 className="text-2xl font-heading tracking-wider text-white mb-1" data-testid="success-headline">
              REWARD UNLOCKED!
            </h2>
            {lastRedeemedProduct && (
              <p className="text-lg font-black mb-0.5" style={{ color: '#4ade80', fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.05em' }}>
                {lastRedeemedProduct.name}
              </p>
            )}
            {lastRedeemedProduct?.coin_price && (
              <p className="text-sm font-medium mb-3" style={{ color: '#C6A052' }}>
                Saved ≈ ₹{Math.round(lastRedeemedProduct.coin_price * 0.8)} · {lastRedeemedProduct.coin_price} coins redeemed
              </p>
            )}
            <p className="text-xs mb-4" style={{ color: '#8A9096' }}>
              Earned through skill. Online Gaming Act, 2025 compliant — no stakes.
            </p>

            {/* QR Code */}
            <div className="flex flex-col items-center mb-4 p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
              <div className="flex items-center gap-2 mb-2">
                <QrCode className="w-4 h-4" style={{ color: '#C6A052' }} />
                <span className="text-xs font-bold" style={{ color: '#C6A052' }}>YOUR VOUCHER CODE</span>
              </div>
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${lastVoucherCode}&bgcolor=1B1E23&color=C6A052`}
                alt="QR Code"
                className="rounded-lg mb-2"
                style={{ width: 100, height: 100 }}
                data-testid="voucher-qr-code"
              />
              <p className="text-xs font-mono font-bold text-white tracking-widest">{lastVoucherCode}</p>
              <p className="text-xs mt-1" style={{ color: '#8A9096' }}>Also sent to your registered mobile</p>
            </div>

            {lastRedeemedProduct && (
              <div className="flex items-center gap-3 p-3 rounded-xl mb-4"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <img src={lastRedeemedProduct.image_url} alt={lastRedeemedProduct.name}
                  className="w-12 h-12 object-cover rounded-lg flex-shrink-0" />
                <div className="text-left">
                  <p className="text-sm font-bold text-white">{lastRedeemedProduct.name}</p>
                  <span className="text-[10px] px-2 py-0.5 rounded-full inline-flex items-center gap-1 mt-0.5"
                    style={{ background: 'rgba(74,222,128,0.15)', color: '#4ade80' }}>
                    <CheckCircle className="h-3 w-3" /> Delivery in progress
                  </span>
                </div>
              </div>
            )}

              <div className="flex gap-2">
              <button
                onClick={() => {
                  if (navigator.share) {
                    navigator.share({ title: 'FREE11 Reward', text: `I just redeemed ${lastRedeemedProduct?.name || 'a reward'} using coins I earned through cricket predictions on FREE11! Join the fun — no cash needed.`, url: window.location.origin });
                  } else {
                    navigator.clipboard.writeText(`I earned a FREE reward on FREE11 — ${lastRedeemedProduct?.name || 'check it out'}! ${window.location.origin}`);
                    toast.success('Share link copied!');
                  }
                }}
                className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-sm font-medium transition-all"
                style={{ background: 'rgba(198,160,82,0.12)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.25)' }}
                data-testid="success-share-btn"
              >
                <Share2 className="w-4 h-4" /> Share
              </button>
              <button onClick={() => { setShowSuccessDialog(false); setTimeout(() => setShowShareCard(true), 300); }} className="btn-gold flex-1 py-2.5 rounded-xl text-sm"
                data-testid="success-close-btn">
                Continue
              </button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
      {/* ── Router: Tease / Confirm Modal ─────────────────────────── */}
      <Dialog open={!!selectedDeal} onOpenChange={() => { setSelectedDeal(null); setTeaseData(null); }}>
        <DialogContent className="max-w-sm mx-4" style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.2)' }} data-testid="router-tease-modal">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Zap className="h-5 w-5" style={{ color: '#C6A052' }} /> Best Deal Found
            </DialogTitle>
            <DialogDescription style={{ color: '#8A9096' }}>Auto-routed to the best provider for your location</DialogDescription>
          </DialogHeader>

          {teaseLoading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-8 w-8 animate-spin" style={{ color: '#C6A052' }} />
            </div>
          ) : teaseData?.best ? (
            <div className="space-y-4">
              {/* Best provider card */}
              <div className="rounded-xl p-4 space-y-3" style={{ background: 'rgba(198,160,82,0.05)', border: '1px solid rgba(198,160,82,0.2)' }}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-wider mb-0.5" style={{ color: '#8A9096' }}>Best Option</p>
                    <p className="font-bold text-white">{teaseData.best.provider_name}</p>
                  </div>
                  <span className="px-2 py-1 rounded-full text-xs font-bold"
                    style={{ background: 'rgba(74,222,128,0.15)', color: '#4ade80' }}>
                    {teaseData.best.value_note}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg p-2" style={{ background: 'rgba(0,0,0,0.3)' }}>
                    <p className="font-black text-white font-numbers">{teaseData.best.coin_price}</p>
                    <p className="text-[9px] uppercase" style={{ color: '#8A9096' }}>COINS</p>
                  </div>
                  <div className="rounded-lg p-2" style={{ background: 'rgba(0,0,0,0.3)' }}>
                    <p className="font-black text-white">₹{teaseData.best.real_price}</p>
                    <p className="text-[9px] uppercase" style={{ color: '#8A9096' }}>VALUE</p>
                  </div>
                  <div className="rounded-lg p-2" style={{ background: 'rgba(0,0,0,0.3)' }}>
                    <p className="font-black text-white">{teaseData.best.eta_label}</p>
                    <p className="text-[9px] uppercase" style={{ color: '#8A9096' }}>ETA</p>
                  </div>
                </div>
                <div className="text-xs pt-2 border-t flex justify-between" style={{ borderColor: 'rgba(255,255,255,0.06)', color: '#8A9096' }}>
                  <span>Your balance</span>
                  <span className="text-white">{user?.coins_balance} → {Math.max(0, (user?.coins_balance || 0) - teaseData.best.coin_price)}</span>
                </div>
              </div>

              {/* Other options */}
              {teaseData.options?.length > 1 && (
                <div className="space-y-1.5">
                  <p className="text-[10px] uppercase tracking-wider" style={{ color: '#8A9096' }}>Other options</p>
                  {teaseData.options.slice(1).map(opt => (
                    <div key={opt.provider_id} className="flex items-center justify-between px-3 py-2 rounded-lg text-xs"
                      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
                      <span style={{ color: '#8A9096' }}>{opt.provider_name}</span>
                      <span style={{ color: '#8A9096' }}>{opt.coin_price} coins · {opt.eta_label}</span>
                    </div>
                  ))}
                </div>
              )}

              {teaseData.best.provider_id === 'amazon' || teaseData.best.provider_id === 'flipkart' ? (
                <p className="text-[10px] text-center" style={{ color: '#8A9096' }}>
                  You'll be redirected to {teaseData.best.provider_name}. FREE11 earns a small affiliate commission.
                </p>
              ) : null}
            </div>
          ) : teaseData?.status === 'not_found' ? (
            <div className="text-center py-6">
              <Package className="h-10 w-10 mx-auto mb-2" style={{ color: '#3A3D43' }} />
              <p className="text-sm" style={{ color: '#8A9096' }}>No providers available for this item</p>
            </div>
          ) : null}

          <DialogFooter className="gap-2">
            <button onClick={() => { setSelectedDeal(null); setTeaseData(null); }}
              className="btn-outline-gold px-4 h-10 rounded-lg text-sm flex-1"
              data-testid="router-tease-cancel">
              Cancel
            </button>
            <button onClick={handleRouterSettle}
              disabled={!teaseData?.best || routerSettleLoading || teaseLoading}
              className="btn-gold px-4 h-10 rounded-lg text-sm flex-1 disabled:opacity-50 flex items-center justify-center gap-1.5"
              data-testid="router-tease-confirm">
              {routerSettleLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : teaseData?.best?.provider_id === 'amazon' || teaseData?.best?.provider_id === 'flipkart' ? (
                <><ExternalLink className="h-4 w-4" /> Open Store</>
              ) : (
                'Confirm'
              )}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Router: Voucher Success Dialog ────────────────────────────── */}
      <Dialog open={showRouterSuccess} onOpenChange={setShowRouterSuccess}>
        <DialogContent className="max-w-sm mx-4 text-center" style={{ background: '#1B1E23', border: '1px solid rgba(74,222,128,0.3)' }} data-testid="router-success-dialog">
          <div className="py-4">
            <div className="relative inline-block mb-4">
              <div className="w-20 h-20 rounded-full mx-auto flex items-center justify-center animate-bounce"
                style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)' }}>
                <Gift className="h-10 w-10 text-white" />
              </div>
              <Sparkles className="h-6 w-6 absolute -top-1 -right-1 animate-live-pulse" style={{ color: '#C6A052' }} />
            </div>
            <h2 className="text-2xl font-heading tracking-wider text-white mb-1">VOUCHER UNLOCKED!</h2>
            <p className="font-medium mb-4 text-sm" style={{ color: '#4ade80' }}>
              Earned through skill — no stakes, no cash.
            </p>

            {routerResult?.voucher_code && (
              <div className="flex flex-col items-center mb-4 p-3 rounded-xl"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                <div className="flex items-center gap-2 mb-2">
                  <QrCode className="w-4 h-4" style={{ color: '#C6A052' }} />
                  <span className="text-xs font-bold" style={{ color: '#C6A052' }}>VOUCHER CODE</span>
                </div>
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${routerResult.voucher_code}&bgcolor=1B1E23&color=C6A052`}
                  alt="QR Code" className="rounded-lg mb-2" style={{ width: 100, height: 100 }}
                  data-testid="router-voucher-qr" />
                <p className="text-xs font-mono font-bold text-white tracking-widest" data-testid="router-voucher-code">
                  {routerResult.voucher_code}
                </p>
                <p className="text-xs mt-1" style={{ color: '#8A9096' }}>
                  {routerResult.instructions || 'Use this code at checkout'}
                </p>
              </div>
            )}

            <button onClick={() => setShowRouterSuccess(false)} className="btn-gold w-full py-2.5 rounded-xl text-sm"
              data-testid="router-success-close">
              Done
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Shop;
