import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Package, Coins, Clock, CheckCircle, Truck } from 'lucide-react';
import api from '../utils/api';

const MyOrders = () => {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await api.getRedemptions();
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4" />;
      case 'confirmed': return <CheckCircle className="h-4 w-4" />;
      case 'shipped': return <Truck className="h-4 w-4" />;
      case 'delivered': return <Package className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-500/20 text-yellow-400';
      case 'confirmed': return 'bg-blue-500/20 text-blue-400';
      case 'shipped': return 'bg-purple-500/20 text-purple-400';
      case 'delivered': return 'bg-green-500/20 text-green-400';
      default: return 'bg-slate-500/20 text-slate-400';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 pb-20 md:pb-0 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl" data-testid="orders-page">
        <div className="mb-8">
          <h1 className="text-4xl font-black text-white mb-2">My Orders 📦</h1>
          <p className="text-slate-400">Track your redemptions and deliveries</p>
        </div>

        {orders.length > 0 ? (
          <div className="space-y-4">
            {orders.map((order) => (
              <Card key={order.id} className="bg-slate-900/50 border-slate-800" data-testid={`order-${order.id}`}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-white flex items-center gap-2">
                        {order.product_name}
                      </CardTitle>
                      <CardDescription className="text-slate-400">
                        Order ID: {order.id.slice(0, 8)}...
                      </CardDescription>
                    </div>
                    <Badge className={getStatusColor(order.status)}>
                      {getStatusIcon(order.status)}
                      <span className="ml-1 capitalize">{order.status}</span>
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-slate-400">Order Date</p>
                      <p className="text-white font-medium">
                        {new Date(order.order_date).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400">Coins Spent</p>
                      <p className="text-yellow-400 font-bold flex items-center gap-1">
                        <Coins className="h-4 w-4" />
                        {order.coins_spent}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-400">Delivery Address</p>
                      <p className="text-white font-medium line-clamp-1">
                        {order.delivery_address || 'Not provided'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Package className="h-20 w-20 text-slate-700 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-slate-400 mb-2">No orders yet</h3>
            <p className="text-slate-500">Start shopping and redeem your coins!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MyOrders;