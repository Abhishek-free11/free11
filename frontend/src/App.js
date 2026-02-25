import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { AuthProvider, useAuth } from './context/AuthContext';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Contests from './pages/Contests';
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
import Fantasy from './pages/Fantasy';
import PrivateLeagues from './pages/PrivateLeagues';
import CardGames from './pages/CardGames';
import GameRoom from './pages/GameRoom';
import './App.css';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  // Show nothing while loading auth state
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-yellow-400 border-t-transparent rounded-full" />
      </div>
    );
  }
  
  return user ? children : <Navigate to="/login" />;
};

const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-yellow-400 border-t-transparent rounded-full" />
      </div>
    );
  }
  
  if (!user) return <Navigate to="/login" />;
  if (!user.is_admin) return <Navigate to="/contests" />;
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
            <Route path="/contests" element={<PrivateRoute><Contests /></PrivateRoute>} />
            <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/earn" element={<PrivateRoute><EarnCoins /></PrivateRoute>} />
            <Route path="/cricket" element={<PrivateRoute><Cricket /></PrivateRoute>} />
            <Route path="/fantasy/:matchId" element={<PrivateRoute><Fantasy /></PrivateRoute>} />
            <Route path="/leagues" element={<PrivateRoute><PrivateLeagues /></PrivateRoute>} />
            <Route path="/games" element={<PrivateRoute><CardGames /></PrivateRoute>} />
            <Route path="/games/:gameType/room/:roomId" element={<PrivateRoute><GameRoom /></PrivateRoute>} />
            <Route path="/shop" element={<PrivateRoute><Shop /></PrivateRoute>} />
            <Route path="/orders" element={<PrivateRoute><MyOrders /></PrivateRoute>} />
            <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
            <Route path="/admin" element={<AdminRoute><Admin /></AdminRoute>} />
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