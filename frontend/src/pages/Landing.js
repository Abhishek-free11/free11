import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Coins, Trophy, Gift, Zap, Users, TrendingUp } from 'lucide-react';
import LanguageSelector from '../components/LanguageSelector';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 pb-20 md:pb-0 via-slate-900 to-slate-950">
      {/* Navigation */}
      <nav className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3" data-testid="logo">
            <img 
              src="/logo.png" 
              alt="FREE11 Logo" 
              className="h-12 w-auto"
            />
          </div>
          <div className="flex gap-3 items-center">
            <LanguageSelector variant="ghost" />
            <Button variant="ghost" onClick={() => navigate('/login')} className="text-slate-200 hover:text-white text-sm sm:text-base" data-testid="login-btn">
              Login
            </Button>
            <Button onClick={() => navigate('/register')} className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold text-sm sm:text-base" data-testid="register-btn">
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-12 sm:py-20 text-center" data-testid="hero-section">
        <div className="max-w-4xl mx-auto space-y-6 sm:space-y-8">
          <div className="inline-block">
            <div className="bg-gradient-to-r from-yellow-500/20 to-amber-600/20 border border-yellow-500/30 rounded-full px-4 sm:px-6 py-2 mb-4 sm:mb-6">
              <span className="text-yellow-400 font-semibold text-sm sm:text-base">Closed Beta is Live 🏏</span>
            </div>
          </div>
          <h1 className="text-4xl sm:text-6xl md:text-7xl font-black text-white leading-tight">
            Make the right calls.
            <span className="block bg-gradient-to-r from-yellow-400 via-amber-500 to-yellow-600 bg-clip-text text-transparent">
              Get real products.
            </span>
          </h1>
          <p className="text-base sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed px-4">
            Call ball-by-ball outcomes during cricket matches. Earn FREE11 Coins for correct calls. Use coins for vouchers, recharges, and more.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-center pt-4 sm:pt-6 px-4">
            <Button size="lg" onClick={() => navigate('/register')} className="w-full sm:w-auto bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold text-base sm:text-lg px-8 py-5 sm:py-6" data-testid="hero-cta-btn">
              Join Beta
              <Coins className="ml-2 h-5 w-5" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate('/login')} className="w-full sm:w-auto border-slate-700 text-slate-200 hover:bg-slate-800 text-base sm:text-lg px-8 py-5 sm:py-6">
              Sign In
            </Button>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-12 sm:py-20" data-testid="features-section">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
          <Card className="bg-slate-900/50 border-slate-800 p-6 sm:p-8 hover:border-yellow-500/50 transition-all">
            <div className="bg-gradient-to-br from-yellow-500/20 to-amber-600/20 w-12 h-12 sm:w-14 sm:h-14 rounded-lg flex items-center justify-center mb-4">
              <Zap className="h-6 w-6 sm:h-7 sm:w-7 text-yellow-400" />
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Call the Action</h3>
            <p className="text-slate-400 text-sm sm:text-base">Make ball-by-ball calls during live cricket matches. Get coins for correct calls.</p>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 p-6 sm:p-8 hover:border-red-500/50 transition-all">
            <div className="bg-gradient-to-br from-red-500/20 to-pink-600/20 w-12 h-12 sm:w-14 sm:h-14 rounded-lg flex items-center justify-center mb-4">
              <Gift className="h-6 w-6 sm:h-7 sm:w-7 text-red-400" />
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Get Real Products</h3>
            <p className="text-slate-400 text-sm sm:text-base">Use coins for Swiggy, Amazon, Netflix vouchers and more. No cash. No betting.</p>
          </Card>

          <Card className="bg-slate-900/50 border-slate-800 p-6 sm:p-8 hover:border-blue-500/50 transition-all">
            <div className="bg-gradient-to-br from-blue-500/20 to-cyan-600/20 w-12 h-12 sm:w-14 sm:h-14 rounded-lg flex items-center justify-center mb-4">
              <Trophy className="h-6 w-6 sm:h-7 sm:w-7 text-blue-400" />
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">Skill Drives Rewards</h3>
            <p className="text-slate-400 text-sm sm:text-base">Your accuracy determines your rank. Better calls = more rewards.</p>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-4xl font-black text-center text-white mb-16">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-8">
          {[
            { step: '1', title: 'Join Beta', desc: 'Use your invite code to sign up', icon: Users, color: 'yellow' },
            { step: '2', title: 'Make Calls', desc: 'Call ball-by-ball during live matches', icon: Zap, color: 'red' },
            { step: '3', title: 'Get Coins', desc: 'Correct calls earn FREE11 Coins', icon: Gift, color: 'blue' },
            { step: '4', title: 'Get Products', desc: 'Use coins for real vouchers', icon: TrendingUp, color: 'yellow' }
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
        <Card className="bg-gradient-to-r from-yellow-600 via-amber-600 to-yellow-600 p-12 text-center border-0">
          <h2 className="text-4xl font-black text-white mb-4">Make the right calls. Get real products.</h2>
          <p className="text-xl text-white/90 mb-8">Join the IPL 2026 Beta with your invite code</p>
          <Button size="lg" onClick={() => navigate('/register')} className="bg-black hover:bg-slate-900 text-white font-bold text-lg px-10 py-6" data-testid="final-cta-btn">
            Join Beta Now
            <Coins className="ml-2 h-5 w-5" />
          </Button>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 bg-slate-950/50 backdrop-blur-sm py-8 mt-20">
        <div className="container mx-auto px-4 text-center text-slate-400">
          <p className="text-lg font-bold text-white mb-2">Skill → Coins → Real Products</p>
          <p>© 2025 FREE11.com - Your Time = Free Shopping List</p>
          <p className="text-sm mt-2">Available in English, हिंदी, and 6+ Indian Languages</p>
          <div className="mt-4">
            <Button 
              variant="link" 
              onClick={() => navigate('/faq')} 
              className="text-slate-400 hover:text-yellow-400"
              data-testid="footer-faq-link"
            >
              FAQ & Help
            </Button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
