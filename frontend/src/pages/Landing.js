import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Coins, Trophy, Gift, Zap, Users, TrendingUp } from 'lucide-react';
import LanguageSelector from '../components/LanguageSelector';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Navigation */}
      <nav className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3" data-testid="logo">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 to-amber-600 blur-xl opacity-50"></div>
              <Coins className="h-10 w-10 text-yellow-400 relative" strokeWidth={2.5} />
            </div>
            <span className="text-3xl font-black bg-gradient-to-r from-yellow-400 via-red-500 to-blue-500 bg-clip-text text-transparent">
              FREE11
            </span>
          </div>
          <div className="flex gap-3 items-center">
            <LanguageSelector variant="ghost" />
            <Button variant="ghost" onClick={() => navigate('/login')} className="text-slate-200 hover:text-white" data-testid="login-btn">
              Login
            </Button>
            <Button onClick={() => navigate('/register')} className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold" data-testid="register-btn">
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center" data-testid="hero-section">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="inline-block">
            <div className="bg-gradient-to-r from-yellow-500/20 to-amber-600/20 border border-yellow-500/30 rounded-full px-6 py-2 mb-6">
              <span className="text-yellow-400 font-semibold">Nobody Will Ever Lose on FREE11 ✨</span>
            </div>
          </div>
          <h1 className="text-6xl md:text-7xl font-black text-white leading-tight">
            Your Time =
            <span className="block bg-gradient-to-r from-yellow-400 via-red-500 to-blue-500 bg-clip-text text-transparent">
              Free Shopping List
            </span>
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Everything here is free, except your time! Play games, complete tasks, earn FREE11 Coins, and redeem real products.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-6">
            <Button size="lg" onClick={() => navigate('/register')} className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold text-lg px-8 py-6" data-testid="hero-cta-btn">
              Start Earning Now
              <Coins className="ml-2 h-5 w-5" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate('/login')} className="border-slate-700 text-slate-200 hover:bg-slate-800 text-lg px-8 py-6">
              Sign In
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-20" data-testid="features-section">
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="bg-slate-900/50 border-slate-800 p-8 hover:border-yellow-500/50 transition-all">
            <div className="bg-gradient-to-br from-yellow-500/20 to-amber-600/20 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <Zap className="h-7 w-7 text-yellow-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Earn FREE11 Coins</h3>
            <p className="text-slate-400">Play skill-based games, complete daily tasks, and maintain streaks to earn coins.</p>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 p-8 hover:border-red-500/50 transition-all">
            <div className="bg-gradient-to-br from-red-500/20 to-pink-600/20 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <Gift className="h-7 w-7 text-red-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Redeem Real Products</h3>
            <p className="text-slate-400">Exchange coins for electronics, vouchers, groceries, fashion, and more.</p>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 p-8 hover:border-blue-500/50 transition-all">
            <div className="bg-gradient-to-br from-blue-500/20 to-cyan-600/20 w-14 h-14 rounded-lg flex items-center justify-center mb-4">
              <Trophy className="h-7 w-7 text-blue-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Level Up & Compete</h3>
            <p className="text-slate-400">Climb the leaderboard, unlock achievements, and earn exclusive rewards.</p>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-4xl font-black text-center text-white mb-16">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-8">
          {[
            { step: '1', title: 'Sign Up Free', desc: 'Get 50 welcome coins instantly', icon: Users, color: 'yellow' },
            { step: '2', title: 'Play & Earn', desc: 'Complete tasks and play games', icon: Zap, color: 'red' },
            { step: '3', title: 'Browse Shop', desc: 'Choose from thousands of products', icon: Gift, color: 'blue' },
            { step: '4', title: 'Redeem & Enjoy', desc: 'Get products delivered to you', icon: TrendingUp, color: 'yellow' }
          ].map((item) => (
            <div key={item.step} className="text-center space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-slate-800/50 border border-slate-700 flex items-center justify-center">
                <item.icon className="h-8 w-8 text-yellow-400" />
              </div>
              <div className="text-5xl font-black text-slate-800">{item.step}</div>
              <h3 className="text-xl font-bold text-white">{item.title}</h3>
              <p className="text-slate-400">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <Card className="bg-gradient-to-r from-yellow-600 via-red-600 to-blue-600 p-12 text-center border-0">
          <h2 className="text-4xl font-black text-white mb-4">Ready to Start Earning?</h2>
          <p className="text-xl text-white/90 mb-8">Join thousands of users transforming their time into real value</p>
          <Button size="lg" onClick={() => navigate('/register')} className="bg-black hover:bg-slate-900 text-white font-bold text-lg px-10 py-6" data-testid="final-cta-btn">
            Get Started Free
            <Coins className="ml-2 h-5 w-5" />
          </Button>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/50 backdrop-blur-sm py-8 mt-20">
        <div className="container mx-auto px-4 text-center text-slate-400">
          <p className="text-lg font-bold text-white mb-2">💯 Nobody Will Ever Lose on FREE11</p>
          <p>© 2025 FREE11.com - Your Time = Free Shopping List</p>
          <p className="text-sm mt-2">Available in English, हिंदी, and 6+ Indian Languages</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
