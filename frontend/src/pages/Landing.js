import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '../context/I18nContext';
import { Button } from '@/components/ui/button';
import LanguageSelector from '../components/LanguageSelector';
import {
  Zap, Gamepad2, CheckCircle2, Trophy, Gift, Coins,
  TrendingUp, Users, ChevronRight, Star, Download, X,
  IndianRupee, ShoppingBag, Flame
} from 'lucide-react';
import SkillDisclaimerModal from '../components/SkillDisclaimerModal';
import LiveActivityTicker from '../components/LiveActivityTicker';
import { motion, AnimatePresence } from 'framer-motion';

const FEATURES = [
  {
    key: 'feature1',
    icon: Zap,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/20 hover:border-yellow-500/50',
    link: '/match-centre',
    glow: 'hover:shadow-yellow-500/10',
  },
  {
    key: 'feature2',
    icon: Gamepad2,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20 hover:border-purple-500/50',
    link: '/card-games',
    glow: 'hover:shadow-purple-500/10',
  },
  {
    key: 'feature3',
    icon: CheckCircle2,
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20 hover:border-green-500/50',
    link: '/earn',
    glow: 'hover:shadow-green-500/10',
  },
  {
    key: 'feature4',
    icon: Trophy,
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/20 hover:border-orange-500/50',
    link: '/leaderboards',
    glow: 'hover:shadow-orange-500/10',
  },
  {
    key: 'feature5',
    icon: Gift,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/20 hover:border-red-500/50',
    link: '/shop',
    glow: 'hover:shadow-red-500/10',
  },
  {
    key: 'feature6',
    icon: Coins,
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/20 hover:border-emerald-500/50',
    link: '/freebucks',
    glow: 'hover:shadow-emerald-500/10',
    badge: 'Premium',
  },
];

const HOW_STEPS = [
  { num: '01', icon: Users, color: 'text-yellow-400', bg: 'bg-yellow-500/10', titleKey: 'step1_title', descKey: 'step1_desc' },
  { num: '02', icon: Zap, color: 'text-purple-400', bg: 'bg-purple-500/10', titleKey: 'step2_title', descKey: 'step2_desc' },
  { num: '03', icon: Star, color: 'text-green-400', bg: 'bg-green-500/10', titleKey: 'step3_title', descKey: 'step3_desc' },
  { num: '04', icon: Gift, color: 'text-red-400', bg: 'bg-red-500/10', titleKey: 'step4_title', descKey: 'step4_desc' },
];

const Landing = () => {
  const navigate = useNavigate();
  const { t } = useI18n();
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [installPrompt, setInstallPrompt] = useState(null);
  const [showInstallBanner, setShowInstallBanner] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      e.preventDefault();
      window.__pwaPrompt = e; // ensure global prompt is always up to date
      setInstallPrompt(e);
      if (!sessionStorage.getItem('install-banner-dismissed')) {
        setShowInstallBanner(true);
      }
    };
    window.addEventListener('beforeinstallprompt', handler);
    // Also pick up prompt if already captured before React loaded
    if (window.__pwaPrompt && !sessionStorage.getItem('install-banner-dismissed')) {
      setInstallPrompt(window.__pwaPrompt);
      setShowInstallBanner(true);
    }
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    const { outcome } = await installPrompt.userChoice;
    if (outcome === 'accepted') setShowInstallBanner(false);
    setInstallPrompt(null);
  };

  const dismissBanner = () => {
    setShowInstallBanner(false);
    sessionStorage.setItem('install-banner-dismissed', '1');
  };

  return (
    <div className="min-h-screen bg-[#0F1115] text-white overflow-x-hidden">
      {/* Broadcast grid + glow */}
      <div className="fixed inset-0 bg-broadcast-grid pointer-events-none" />
      <div className="fixed pointer-events-none" style={{ top:'-15%',left:'50%',transform:'translateX(-50%)',width:'100vw',height:'60vh',background:'radial-gradient(ellipse, rgba(198,160,82,0.07) 0%, transparent 65%)' }} />

      {/* ── PWA Install Banner ── */}
      <AnimatePresence>
        {showInstallBanner && (
          <motion.div
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 80, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 28 }}
            className="fixed bottom-0 inset-x-0 z-[100] px-4 pb-4 sm:px-6"
            data-testid="pwa-install-banner"
          >
            <div className="max-w-md mx-auto rounded-2xl p-4 flex items-center gap-3"
              style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.3)', boxShadow: '0 -4px 32px rgba(0,0,0,0.5)' }}>
              <img src="/free11_icon_192.png" alt="FREE11" className="h-12 w-12 rounded-xl shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="font-heading text-sm tracking-wider text-white">Install FREE11</p>
                <p className="text-xs mt-0.5" style={{ color: '#8A9096' }}>Add to Home Screen for the best experience</p>
              </div>
              <button
                onClick={handleInstall}
                className="shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold"
                style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                data-testid="pwa-install-btn">
                <Download className="h-3.5 w-3.5" /> Install
              </button>
              <button onClick={dismissBanner} className="shrink-0 p-1 rounded-lg" style={{ color: '#8A9096' }}
                data-testid="pwa-install-dismiss">
                <X className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Sticky Nav */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b"
        style={{ background:'rgba(15,17,21,0.92)', borderColor:'rgba(198,160,82,0.12)', backdropFilter:'blur(16px)' }}
        data-testid="landing-nav">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="flex items-center gap-2 flex-shrink-0">
            <img src="/free11_icon_192.png" alt="FREE11" className="h-8 w-8 rounded-xl animate-coin-glow" />
            <span className="font-heading text-xl tracking-widest" style={{ color:'#C6A052', letterSpacing:'0.12em' }}>FREE11</span>
          </button>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden sm:block"><LanguageSelector variant="ghost" /></div>
            <button onClick={() => navigate('/login')} className="text-sm px-3 h-8 rounded-lg transition-colors"
              style={{ color:'#BFC3C8' }} data-testid="nav-login-btn">{t('landing.login')}</button>
            <button onClick={() => navigate('/register')}
              className="btn-gold text-sm px-4 h-8 rounded-lg" data-testid="nav-register-btn">
              {t('landing.start_playing')}
            </button>
          </div>
        </div>
      </nav>

      {/* ───── HERO ───── */}
      <section className="relative pt-28 pb-16 px-4" data-testid="hero-section">
        {/* Hero stadium background image */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <img
            src="https://static.prod-images.emergentagent.com/jobs/cd09d64a-beec-4caf-8b0f-ee03c7f75011/images/f1a4d946bcfce67e7ccdeffb35325a9ffaea5fe941eac9953ab40face0b7f280.png"
            alt="Cricket Stadium"
            className="w-full h-full object-cover opacity-[0.12]"
            loading="eager"
            style={{ filter: 'blur(2px)' }}
          />
          <div className="absolute inset-0" style={{ background: 'linear-gradient(to bottom, rgba(15,17,21,0.5) 0%, rgba(15,17,21,0.95) 80%, #0F1115 100%)' }} />
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <img src="/free11-logo.png" alt="FREE11" className="h-40 sm:h-56 w-auto"
              style={{ filter:'drop-shadow(0 0 40px rgba(198,160,82,0.6))' }} />
          </div>

          {/* Platform badge */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 mb-5 text-xs"
            style={{ background:'rgba(198,160,82,0.08)', border:'1px solid rgba(198,160,82,0.2)', color:'#C6A052' }}>
            <span className="w-1.5 h-1.5 rounded-full animate-live-pulse" style={{ background:'#C6A052' }} />
            India's #1 Skill-Based Cricket Prediction Platform
          </motion.div>

          {/* H1 — exact PRD tagline */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.15 }}
            className="text-4xl sm:text-6xl md:text-7xl font-black leading-none tracking-tight mb-5"
            style={{ fontFamily:'Bebas Neue, sans-serif', letterSpacing:'0.04em' }}
            data-testid="hero-h1">
            <span className="text-white">India's choice for</span>
            <br />
            <span className="text-gold-gradient">Social Entertainment &amp; Free Skilled Games</span>
          </motion.h1>

          {/* Subparagraph — exact PRD copy */}
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: "easeOut", delay: 0.3 }}
            className="text-base sm:text-lg max-w-2xl mx-auto mb-8 px-2 leading-relaxed" style={{ color:'#BFC3C8' }}
            data-testid="hero-subpara">
            Make accurate predictions in live matches, earn <strong style={{ color:'#C6A052' }}>FREE Coins</strong> through skill, redeem for cold drinks, groceries, mobile recharges &amp; more —{' '}
            <span style={{ color:'#8A9096' }}>no money down.</span>
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut", delay: 0.45 }}
            className="flex flex-col sm:flex-row gap-3 justify-center items-stretch sm:items-center px-4 sm:px-0 mb-8">
            <button onClick={() => navigate('/register')}
              className="btn-gold h-12 px-8 rounded-xl text-base font-heading tracking-wider ripple"
              data-testid="hero-primary-btn">
              START PLAYING &rarr;
            </button>
            <button onClick={() => navigate('/earn')}
              className="btn-outline-gold h-12 px-8 rounded-xl text-base font-heading tracking-wider ripple"
              data-testid="hero-secondary-btn">
              EXPLORE GAMES
            </button>
          </motion.div>

          {/* Trust bullets */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, ease: "easeOut", delay: 0.6 }}
            className="flex flex-wrap justify-center gap-x-5 gap-y-2 text-xs" style={{ color:'#8A9096' }}>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500" />Free to play
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full" style={{ background:'#C6A052' }} />Real grocery rewards
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />100% skill-based
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400" />No deposits or risk
            </span>
          </motion.div>

          {/* Live Activity Ticker */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut", delay: 0.75 }}
            className="mt-6 max-w-sm mx-auto">
            <LiveActivityTicker />
          </motion.div>
        </div>
      </section>

      {/* ───── SOCIAL PROOF STATS BAR ───── */}
      <section className="px-4 py-5" data-testid="stats-bar">
        <div className="max-w-2xl mx-auto">
          <div className="grid grid-cols-3 gap-3">
            {[
              { value: '1.5L+', label: 'Users Joined', icon: Users, color: '#C6A052' },
              { value: '₹8.2L+', label: 'Rewards Earned', icon: IndianRupee, color: '#4ade80' },
              { value: '73%', label: 'Avg Accuracy', icon: Trophy, color: '#a855f7' },
            ].map(({ value, label, icon: Icon, color }) => (
              <div key={label} className="rounded-2xl p-3 text-center"
                style={{ background: 'rgba(255,255,255,0.025)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <Icon className="h-4 w-4 mx-auto mb-1.5" style={{ color }} />
                <div className="text-lg font-black text-white" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>{value}</div>
                <div className="text-[10px] mt-0.5" style={{ color: '#8A9096' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ───── 6-FEATURE GRID ───── */}
      <section className="px-4 py-12 sm:py-20" data-testid="features-section">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10 sm:mb-14">
            <h2 className="text-2xl sm:text-4xl font-black text-white mb-3">
              {t('landing.platform_title')}
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              {t('landing.platform_subtitle')}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-5" data-testid="feature-grid">
            {FEATURES.map((f) => (
              <button
                key={f.key}
                onClick={() => navigate(f.link)}
                className={`group relative text-left p-5 sm:p-6 rounded-2xl bg-white/3 border ${f.border} transition-all duration-300 hover:shadow-xl ${f.glow} active:scale-98 w-full`}
                data-testid={`feature-card-${f.key}`}
              >
                {f.badge && (
                  <span className="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full px-2 py-0.5">
                    {f.badge}
                  </span>
                )}
                <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-xl ${f.bg} border ${f.border} flex items-center justify-center mb-4`}>
                  <f.icon className={`h-5 w-5 sm:h-6 sm:w-6 ${f.color}`} />
                </div>
                <h3 className="text-base sm:text-lg font-bold text-white mb-1.5">
                  {t(`landing.${f.key}_title`)}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {t(`landing.${f.key}_desc`)}
                </p>
                <div className={`flex items-center gap-1 mt-3 text-xs font-medium ${f.color} opacity-0 group-hover:opacity-100 transition-opacity`}>
                  Learn more <ChevronRight className="h-3 w-3" />
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* ───── HOW IT WORKS ───── */}
      <section className="px-4 py-12 sm:py-20 bg-white/2" data-testid="how-it-works-section">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10 sm:mb-14">
            <h2 className="text-2xl sm:text-4xl font-black text-white mb-2">
              {t('landing.how_it_works')}
            </h2>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {HOW_STEPS.map((step) => (
              <div key={step.num} className="text-center space-y-3">
                <div className={`w-12 h-12 sm:w-14 sm:h-14 mx-auto rounded-2xl ${step.bg} flex items-center justify-center`}>
                  <step.icon className={`h-6 w-6 sm:h-7 sm:w-7 ${step.color}`} />
                </div>
                <div className="text-3xl sm:text-4xl font-black text-white/5">{step.num}</div>
                <h3 className="text-sm sm:text-base font-bold text-white">{t(`landing.${step.titleKey}`)}</h3>
                <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">{t(`landing.${step.descKey}`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ───── FINAL CTA ───── */}
      <section className="px-4 py-16 sm:py-24" data-testid="cta-section">
        <div className="max-w-2xl mx-auto text-center">
          <div className="bg-gradient-to-br from-yellow-500/10 via-amber-500/5 to-transparent border border-yellow-500/20 rounded-3xl p-8 sm:p-12">
            <TrendingUp className="h-10 w-10 text-yellow-400 mx-auto mb-5" />
            <h2 className="text-2xl sm:text-4xl font-black text-white mb-3">
              {t('landing.cta_headline')}
            </h2>
            <p className="text-slate-300 text-sm sm:text-base mb-8">
              {t('landing.cta_desc')}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                size="lg"
                onClick={() => navigate('/register')}
                className="w-full sm:w-auto bg-yellow-500 hover:bg-yellow-400 text-black font-bold text-base px-8 py-5 h-auto shadow-xl shadow-yellow-500/20 active:scale-95"
                data-testid="cta-register-btn"
              >
                {t('landing.create_account')}
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={() => navigate('/login')}
                className="w-full sm:w-auto border-white/15 text-white hover:bg-white/5 text-base px-8 py-5 h-auto active:scale-95"
                data-testid="cta-login-btn"
              >
                {t('landing.login_btn')}
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* ───── Section 8: SEO Content Block ───── */}
      <section className="px-4 py-10 sm:py-14" style={{ background: 'rgba(255,255,255,0.02)' }} data-testid="seo-section">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-black text-white mb-4" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>
            FREE11 — India's Free Fantasy Cricket App
          </h2>
          <div className="text-sm leading-relaxed space-y-3" style={{ color: '#8A9096' }}>
            <p>
              <strong style={{ color: '#BFC3C8' }}>FREE11</strong> is India's most accessible free fantasy cricket platform — built for the T20 cricket season and beyond. Unlike traditional fantasy apps that require deposits or carry financial risk, FREE11 is completely free to play. You earn <strong style={{ color: '#C6A052' }}>FREE Coins</strong> by making accurate <strong style={{ color: '#BFC3C8' }}>skill-based cricket predictions</strong> and redeem them for real everyday essentials: cold drinks, biscuits, wheat flour, mobile recharges, and more.
            </p>
            <p>
              Every T20 cricket over becomes a micro-earning opportunity. Every correct prediction brings you closer to your next grocery redemption. Earn rewards from cricket the smart way — predictions, daily puzzles, streaks, Crowd Meter, and sponsored brand pools all generate coins.
            </p>
            <p>
              The <a href="/shop" className="underline" style={{ color: '#C6A052' }}>FREE11 Shop</a> stocks 50+ brand-funded SKUs delivered via ONDC, Zepto, and BigBasket. Start free, play skill, earn real.
            </p>
            <div className="flex flex-wrap gap-3 pt-2">
              <a href="/predict" className="text-xs px-3 py-1.5 rounded-full font-medium" style={{ background: 'rgba(198,160,82,0.1)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.25)' }}>Start Predicting Free</a>
              <a href="/shop" className="text-xs px-3 py-1.5 rounded-full font-medium" style={{ background: 'rgba(74,222,128,0.1)', color: '#4ade80', border: '1px solid rgba(74,222,128,0.25)' }}>Browse Rewards Shop</a>
              <a href="/blog/cricket-guide" className="text-xs px-3 py-1.5 rounded-full font-medium" style={{ background: 'rgba(255,255,255,0.05)', color: '#BFC3C8', border: '1px solid rgba(255,255,255,0.1)' }}>Cricket Guide 2026</a>
            </div>
          </div>
        </div>
      </section>

      {/* ───── FOOTER ───── */}
      <footer className="border-t border-white/5 bg-black/40 px-4 py-10">
        <div className="max-w-4xl mx-auto">
          {/* Disclaimer */}
          <div className="bg-white/3 border border-white/8 rounded-xl p-4 mb-8 text-center">
            <p className="text-[11px] sm:text-xs text-slate-500 leading-relaxed">
              <strong className="text-yellow-500/70">{t('landing.disclaimer_title')}</strong>{' '}
              {t('landing.disclaimer_text')}
            </p>
          </div>

          {/* Logo + tagline */}
          <div className="text-center mb-6">
            <div className="flex items-center justify-center gap-2 mb-2">
              <img src="/free11_icon_192.png" alt="FREE11" className="h-7 w-7 rounded-xl" />
              <span className="font-heading tracking-widest" style={{ color: '#C6A052', letterSpacing: '0.12em' }}>FREE11</span>
            </div>
            <p className="text-slate-500 text-xs">{t('landing.tagline_coins')}</p>
          </div>

          {/* Footer links */}
          <div className="flex flex-wrap justify-center gap-x-5 gap-y-2 mb-6">
            {[
              { key: 'about', path: '/about' },
              { key: 'terms', path: '/terms' },
              { key: 'privacy', path: '/privacy' },
              { key: 'guidelines', path: '/guidelines' },
              { key: 'faq', path: '/faq' },
              { key: 'support', path: '/support' },
              { label: 'Blog', path: '/blog' },
            ].map(l => (
              <button
                key={l.key || l.label}
                onClick={() => navigate(l.path)}
                className="text-xs text-slate-500 hover:text-slate-300 transition-colors py-1"
              >
                {l.label || t(`footer_links.${l.key}`)}
              </button>
            ))}
          </div>

          {/* Section 2 — Skill Disclaimer in footer */}
          <div className="max-w-xl mx-auto mb-4 p-3 rounded-xl text-center" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
            <button
              onClick={() => setShowDisclaimer(true)}
              className="text-xs hover:underline transition-colors"
              style={{ color: 'rgba(255,255,255,0.35)' }}
              data-testid="footer-skill-disclaimer-btn"
            >
              FREE11 is a skill-based sports prediction platform. No deposits or cash wagering. Rewards are promotional benefits only. Online Gaming Act, 2025 compliant. <span style={{ color: 'rgba(255,255,255,0.5)' }}>Learn more →</span>
            </button>
          </div>
          <SkillDisclaimerModal isOpen={showDisclaimer} onClose={() => setShowDisclaimer(false)} />

          <p className="text-center text-xs text-slate-600">
            &copy; 2026 FREE11 &mdash; {t('landing.copyright_suffix')}
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
