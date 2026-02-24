import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { AuthProvider, useAuth } from './context/AuthContext';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import EarnCoins from './pages/EarnCoins';
import Cricket from './pages/Cricket';
import Shop from './pages/Shop';
import MyOrders from './pages/MyOrders';
import Profile from './pages/Profile';
import Admin from './pages/Admin';
import FAQ from './pages/FAQ';
import Clans from './pages/Clans';
import Leaderboards from './pages/Leaderboards';
import Support from './pages/Support';
import BrandPortal from './pages/BrandPortal';
import './App.css';

const PrivateRoute = ({ children }) => {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" />;
};

const AdminRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (!user.is_admin) return <Navigate to="/dashboard" />;
  return children;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/earn" element={<PrivateRoute><EarnCoins /></PrivateRoute>} />
            <Route path="/cricket" element={<PrivateRoute><Cricket /></PrivateRoute>} />
            <Route path="/shop" element={<PrivateRoute><Shop /></PrivateRoute>} />
            <Route path="/orders" element={<PrivateRoute><MyOrders /></PrivateRoute>} />
            <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
            <Route path="/admin" element={<PrivateRoute><Admin /></PrivateRoute>} />
            <Route path="/faq" element={<FAQ />} />
            <Route path="/clans" element={<PrivateRoute><Clans /></PrivateRoute>} />
            <Route path="/leaderboards" element={<PrivateRoute><Leaderboards /></PrivateRoute>} />
            <Route path="/support" element={<PrivateRoute><Support /></PrivateRoute>} />
            <Route path="/brand" element={<BrandPortal />} />
          </Routes>
          <Toaster position="top-center" richColors />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;