import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { AuthProvider, useAuth } from './context/AuthContext';
import { trackButtonClick } from './utils/analytics';
import { Download } from 'lucide-react';
import PWAInstallPrompt from './components/PWAInstallPrompt';

// Scroll to top on every route change
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}
// Critical path — load eagerly
// Landing page intentionally not shown to unauthenticated users — they go directly to /login
// const Landing = lazy(() => import('./pages/Landing')); // kept as lazy if needed in future
import Login from './pages/Login';
import Register from './pages/Register';
// Heavy pages — lazy loaded for performance
const Dashboard = lazy(() => import('./pages/Dashboard'));
const EarnCoins = lazy(() => import('./pages/EarnCoins'));
const Shop = lazy(() => import('./pages/Shop'));
const MyOrders = lazy(() => import('./pages/MyOrders'));
const Profile = lazy(() => import('./pages/Profile'));
const Admin = lazy(() => import('./pages/Admin'));
const FAQ = lazy(() => import('./pages/FAQ'));
const Clans = lazy(() => import('./pages/Clans'));
const Leaderboards = lazy(() => import('./pages/Leaderboards'));
const Support = lazy(() => import('./pages/Support'));
const BrandPortal = lazy(() => import('./pages/BrandPortal'));
const PrivateLeagues = lazy(() => import('./pages/PrivateLeagues'));
const CardGames = lazy(() => import('./pages/CardGames'));
const GameLobby = lazy(() => import('./pages/GameLobby'));
const SolitairePage = lazy(() => import('./pages/SolitairePage'));
const TeenPattiGame = lazy(() => import('./pages/TeenPattiGame'));
const RummyGame = lazy(() => import('./pages/RummyGame'));
const PokerGame = lazy(() => import('./pages/PokerGame'));
const GameRoom = lazy(() => import('./pages/GameRoom'));
const InviteFriends = lazy(() => import('./pages/InviteFriends'));
const AboutUs = lazy(() => import('./pages/AboutUs'));
const TermsAndConditions = lazy(() => import('./pages/TermsAndConditions'));
const PrivacyPolicy = lazy(() => import('./pages/PrivacyPolicy'));
const CommunityGuidelines = lazy(() => import('./pages/CommunityGuidelines'));
const LiveMatch = lazy(() => import('./pages/LiveMatch'));
const Ledger = lazy(() => import('./pages/Ledger'));
const Cards = lazy(() => import('./pages/Cards'));
const RewardedAds = lazy(() => import('./pages/RewardedAds'));
const Referrals = lazy(() => import('./pages/Referrals'));
const ContestHub = lazy(() => import('./pages/ContestHub'));
const AdminV2 = lazy(() => import('./pages/AdminV2'));
const AdminAnalytics = lazy(() => import('./pages/AdminAnalytics'));
const TeamBuilder = lazy(() => import('./pages/TeamBuilder'));
const MatchCentre = lazy(() => import('./pages/MatchCentre'));
const FreeBucks = lazy(() => import('./pages/FreeBucks'));
const Wallet = lazy(() => import('./pages/Wallet'));
const Predict = lazy(() => import('./pages/Predict'));
const ResponsiblePlay = lazy(() => import('./pages/ResponsiblePlay'));
const RefundPolicy = lazy(() => import('./pages/RefundPolicy'));
const SponsoredPools = lazy(() => import('./pages/SponsoredPools'));
const Disclaimer = lazy(() => import('./pages/Disclaimer'));
const WalletExplainer = lazy(() => import('./pages/WalletExplainer'));
const Blog = lazy(() => import('./pages/Blog'));
const GameSEO = lazy(() => import('./pages/GameSEO'));
import { I18nProvider } from './context/I18nContext';
import SiteFooter from './components/SiteFooter';
import { toast } from 'sonner';
import './App.css';

const API = process.env.REACT_APP_BACKEND_URL;

// Section 12 — Google OAuth AuthCallback
// Exchanges session_id from Emergent Auth for our JWT token
function AuthCallback() {
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();
  const hasProcessed = React.useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const match = hash.match(/session_id=([^&]+)/);
    if (!match) { 
      console.error('[OAuth] No session_id found in URL hash');
      navigate('/login'); 
      return; 
    }
    const sessionId = match[1];
    console.log('[OAuth] Processing session_id:', sessionId.slice(0, 10) + '...');

    (async () => {
      try {
        const res = await fetch(`${API}/api/auth/google-oauth?session_id=${encodeURIComponent(sessionId)}`, { method: 'POST' });
        console.log('[OAuth] Backend response status:', res.status);
        if (!res.ok) {
          const errorData = await res.json().catch(() => ({}));
          console.error('[OAuth] Backend error:', errorData);
          throw new Error(errorData?.detail || 'OAuth failed');
        }
        const data = await res.json();
        await loginWithToken(data.token);
        toast.success(`Welcome, ${data.user.name?.split(' ')[0] || 'Champion'}!`);
        navigate('/dashboard', { replace: true });
      } catch (err) {
        console.error('[OAuth] Error:', err.message);
        toast.error('Google sign-in failed. Please try again.');
        navigate('/login', { replace: true });
      }
    })();
  }, [navigate, loginWithToken]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F1115]">
      <div className="text-center">
        <div className="h-10 w-10 rounded-full border-2 animate-spin mx-auto mb-3" style={{ borderColor: '#C6A052', borderTopColor: 'transparent' }} />
        <p className="text-sm" style={{ color: '#8A9096' }}>Signing you in with Google...</p>
      </div>
    </div>
  );
}

// Global click analytics — auto-tracks every button/link click across the entire app
function GlobalAnalyticsTracker() {
  useEffect(() => {
    let lastEvent = '';
    let lastTime = 0;
    const handleClick = (e) => {
      const el = e.target.closest('button, a, [data-testid], [role="button"]');
      if (!el) return;
      const label =
        el.getAttribute('data-testid') ||
        el.getAttribute('aria-label') ||
        el.getAttribute('title') ||
        el.innerText?.trim()?.slice(0, 40) ||
        el.tagName.toLowerCase();
      // Dedupe: skip if same label fired within 1s
      const now = Date.now();
      if (label === lastEvent && now - lastTime < 1000) return;
      lastEvent = label;
      lastTime = now;
      trackButtonClick(label, { tag: el.tagName.toLowerCase() });
    };
    document.addEventListener('click', handleClick, { passive: true });
    return () => document.removeEventListener('click', handleClick);
  }, []);
  return null;
}

// Permissions onboard — fires for ALL authenticated users (new + existing) who haven't been prompted yet
// Treats legacy/past users the same as new users for notifications, biometrics, and sound
function LegacyUserPermissions() {
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;
    if (localStorage.getItem('permissions_prompted') === 'true') return;

    const runPermissions = async () => {
      // 1. Sound on by default
      if (!localStorage.getItem('sound_enabled')) {
        localStorage.setItem('sound_enabled', 'true');
      }

      // 2. Push notifications
      try {
        if ('Notification' in window && Notification.permission === 'default') {
          await Notification.requestPermission();
        }
      } catch (_) {}

      // 3. Biometrics (WebAuthn platform authenticator) — best-effort
      try {
        if (window.PublicKeyCredential && !localStorage.getItem('biometric_enrolled')) {
          const supported = await PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
          if (supported) {
            const challenge = new Uint8Array(32);
            crypto.getRandomValues(challenge);
            await navigator.credentials.create({
              publicKey: {
                challenge,
                rp: { name: 'FREE11', id: window.location.hostname },
                user: {
                  id: new TextEncoder().encode((user.id || user._id || user.email || 'user').toString().slice(0, 32)),
                  name: user.email || 'user@free11.com',
                  displayName: user.name || 'FREE11 User',
                },
                pubKeyCredParams: [{ type: 'public-key', alg: -7 }, { type: 'public-key', alg: -257 }],
                authenticatorSelection: { authenticatorAttachment: 'platform', userVerification: 'preferred' },
                timeout: 30000,
              },
            });
            localStorage.setItem('biometric_enrolled', 'true');
          }
        }
      } catch (_) {}

      // Mark done — won't run again for this user on this device
      localStorage.setItem('permissions_prompted', 'true');
    };

    // Small delay so the app fully loads before prompting
    const timer = setTimeout(runPermissions, 2000);
    return () => clearTimeout(timer);
  }, [user]);

  return null;
}
// PWA Install FAB — appears as a persistent reminder after the bottom sheet has been dismissed once
// Complements PWAInstallPrompt: bottom sheet is the featured first experience, FAB is the ongoing nudge
function PWAInstallButton() {
  const [visible, setVisible] = useState(false);
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    if (localStorage.getItem('appInstalled')) return;
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) return;

    const tryShow = () => {
      if (!window.__pwaPrompt) return;
      // Only show FAB if the full bottom sheet has been dismissed at least once
      if (localStorage.getItem('pwa_prompt_dismissed_at')) {
        setVisible(true);
      }
    };

    const handler = (e) => {
      e.preventDefault();
      window.__pwaPrompt = e;
      tryShow();
    };
    window.addEventListener('beforeinstallprompt', handler);
    if (window.__pwaPrompt) tryShow();

    const installed = () => { localStorage.setItem('appInstalled', 'true'); setVisible(false); };
    window.addEventListener('appinstalled', installed);

    // Re-check every 5s in case bottom sheet was just dismissed
    const interval = setInterval(() => {
      if (!visible && window.__pwaPrompt && localStorage.getItem('pwa_prompt_dismissed_at')) {
        setVisible(true);
      }
      setPulse(p => !p);
    }, 5000);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      window.removeEventListener('appinstalled', installed);
      clearInterval(interval);
    };
  }, [visible]);

  const handleInstall = async () => {
    if (!window.__pwaPrompt) return;
    try { const { trackPWAInstall } = await import('./utils/analytics'); trackPWAInstall(); } catch (_) {}
    window.__pwaPrompt.prompt();
    const { outcome } = await window.__pwaPrompt.userChoice;
    if (outcome === 'accepted') { localStorage.setItem('appInstalled', 'true'); setVisible(false); }
  };

  if (!visible) return null;
  return (
    <button
      onClick={handleInstall}
      title="Install FREE11 App"
      data-testid="pwa-install-fab"
      aria-label="Install FREE11 App"
      style={{
        position: 'fixed',
        bottom: '80px',
        right: '16px',
        zIndex: 9997,
        width: '44px',
        height: '44px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #C6A052, #E0B84F)',
        border: 'none',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        boxShadow: pulse ? '0 0 0 6px rgba(198,160,82,0.25), 0 4px 16px rgba(0,0,0,0.5)' : '0 4px 16px rgba(0,0,0,0.5)',
        transition: 'box-shadow 0.6s ease',
      }}
    >
      <Download size={18} color="#0F1115" strokeWidth={2.5} />
    </button>
  );
}

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0F1115]">
        <div className="text-center animate-slide-up">
          <img src="/free11_icon_192.png" alt="FREE11" className="h-16 w-16 mx-auto mb-4 animate-coin-glow rounded-2xl" />
          <p className="font-heading text-3xl tracking-widest text-gold mb-3">FREE11</p>
          <div className="flex items-center justify-center gap-1.5">
            {[0,1,2].map(i => (
              <div key={i} className="h-1.5 w-1.5 rounded-full bg-gold animate-live-pulse"
                style={{ animationDelay: `${i * 0.2}s`, background: '#C6A052' }} />
            ))}
          </div>
        </div>
      </div>
    );
  }
  return user ? children : <Navigate to="/login" />;
};

const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-[#0F1115]"><div className="animate-spin h-8 w-8 border-2 rounded-full" style={{ borderColor: '#C6A052', borderTopColor: 'transparent' }} /></div>;
  if (!user) return <Navigate to="/login" />;
  if (!user.is_admin) return <Navigate to="/match-centre" />;
  return children;
};

// Root route: redirect authenticated users to dashboard, else go straight to Login
const RootRoute = () => {
  const { user, loading } = useAuth();
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F1115]">
      <div className="text-center animate-slide-up">
        <img src="/free11_icon_192.png" alt="FREE11" className="h-16 w-16 mx-auto mb-4 animate-coin-glow rounded-2xl" />
        <p className="font-heading text-3xl tracking-widest text-gold mb-3">FREE11</p>
        <div className="flex items-center justify-center gap-1.5">
          {[0,1,2].map(i => (
            <div key={i} className="h-1.5 w-1.5 rounded-full bg-gold animate-live-pulse"
              style={{ animationDelay: `${i * 0.2}s`, background: '#C6A052' }} />
          ))}
        </div>
      </div>
    </div>
  );
  if (user) return <Navigate to="/dashboard" replace />;
  return <Navigate to="/login" replace />;
};

// Spinner used as fallback for all lazy-loaded pages
const PageSpinner = () => (
  <div className="min-h-screen flex items-center justify-center bg-[#0F1115]">
    <div className="text-center">
      <img src="/free11_icon_192.png" alt="FREE11" className="h-12 w-12 mx-auto mb-3 rounded-2xl animate-coin-glow" />
      <div className="flex items-center justify-center gap-1.5">
        {[0,1,2].map(i => (
          <div key={i} className="h-1.5 w-1.5 rounded-full animate-live-pulse"
            style={{ background: '#C6A052', animationDelay: `${i * 0.2}s` }} />
        ))}
      </div>
    </div>
  </div>
);

// CRITICAL: Detect session_id synchronously during render (prevents race conditions with AuthProvider)
function AppRouter() {
  const location = useLocation();
  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  if (location.hash?.includes('session_id=')) return <AuthCallback />;

  return (
    <Suspense fallback={<PageSpinner />}>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<RootRoute />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/contests" element={<Navigate to="/match-centre" />} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/earn" element={<PrivateRoute><EarnCoins /></PrivateRoute>} />
        <Route path="/cricket" element={<Navigate to="/predict" />} />
        <Route path="/fantasy/:matchId" element={<Navigate to="/match-centre" />} />
        <Route path="/predict" element={<PrivateRoute><Predict /></PrivateRoute>} />
        <Route path="/leagues" element={<PrivateRoute><PrivateLeagues /></PrivateRoute>} />
        <Route path="/games" element={<PrivateRoute><CardGames /></PrivateRoute>} />
        <Route path="/games/solitaire" element={<PrivateRoute><SolitairePage /></PrivateRoute>} />
        <Route path="/games/teen_patti/play" element={<PrivateRoute><TeenPattiGame /></PrivateRoute>} />
        <Route path="/games/rummy/play" element={<PrivateRoute><RummyGame /></PrivateRoute>} />
        <Route path="/games/poker/play" element={<PrivateRoute><PokerGame /></PrivateRoute>} />
        <Route path="/games/:gameType" element={<PrivateRoute><GameLobby /></PrivateRoute>} />
        <Route path="/games/:gameType/room/:roomId" element={<PrivateRoute><GameRoom /></PrivateRoute>} />
        <Route path="/shop" element={<PrivateRoute><Shop /></PrivateRoute>} />
        <Route path="/orders" element={<PrivateRoute><MyOrders /></PrivateRoute>} />
        <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
        <Route path="/admin" element={<AdminRoute><Admin /></AdminRoute>} />
        <Route path="/faq" element={<FAQ />} />
        <Route path="/clans" element={<PrivateRoute><Clans /></PrivateRoute>} />
        <Route path="/leaderboards" element={<PrivateRoute><Leaderboards /></PrivateRoute>} />
        <Route path="/support" element={<PrivateRoute><Support /></PrivateRoute>} />
        <Route path="/invite" element={<PrivateRoute><InviteFriends /></PrivateRoute>} />
        <Route path="/brand" element={<BrandPortal />} />
        <Route path="/match/:matchId" element={<PrivateRoute><LiveMatch /></PrivateRoute>} />
        <Route path="/contest-hub/:matchId" element={<PrivateRoute><ContestHub /></PrivateRoute>} />
        <Route path="/team-builder/:matchId" element={<PrivateRoute><TeamBuilder /></PrivateRoute>} />
        <Route path="/match-centre" element={<MatchCentre />} />
        <Route path="/ledger" element={<PrivateRoute><Ledger /></PrivateRoute>} />
        <Route path="/cards" element={<PrivateRoute><Cards /></PrivateRoute>} />
        <Route path="/watch-earn" element={<PrivateRoute><RewardedAds /></PrivateRoute>} />
        <Route path="/referrals" element={<PrivateRoute><Referrals /></PrivateRoute>} />
        <Route path="/freebucks" element={<PrivateRoute><FreeBucks /></PrivateRoute>} />
        <Route path="/wallet" element={<PrivateRoute><Wallet /></PrivateRoute>} />
        <Route path="/payment/success" element={<PrivateRoute><FreeBucks /></PrivateRoute>} />
        <Route path="/payment/cancel" element={<PrivateRoute><FreeBucks /></PrivateRoute>} />
        <Route path="/admin/v2" element={<AdminRoute><AdminV2 /></AdminRoute>} />
        <Route path="/admin/analytics" element={<AdminRoute><AdminAnalytics /></AdminRoute>} />
        <Route path="/sponsored" element={<PrivateRoute><SponsoredPools /></PrivateRoute>} />
        <Route path="/blog/cricket-guide" element={<Blog />} />
        <Route path="/blog/ipl-guide" element={<Blog />} />
        <Route path="/blog/:slug" element={<Blog />} />
        <Route path="/blog" element={<Blog />} />
        {/* SEO Game Landing Pages */}
        <Route path="/rummy" element={<GameSEO />} />
        <Route path="/teen-patti" element={<GameSEO />} />
        <Route path="/poker" element={<GameSEO />} />
        <Route path="/cricket-prediction" element={<GameSEO />} />
        <Route path="/about" element={<AboutUs />} />
        <Route path="/terms" element={<TermsAndConditions />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/guidelines" element={<CommunityGuidelines />} />
        <Route path="/responsible-play" element={<ResponsiblePlay />} />
        <Route path="/refund" element={<RefundPolicy />} />
        <Route path="/disclaimer" element={<Disclaimer />} />
        <Route path="/wallet-info" element={<WalletExplainer />} />
      </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <I18nProvider>
      <AuthProvider>
        <BrowserRouter>
          <div className="App">
            <AppRouter />
            <SiteFooter />
            <PWAInstallPrompt />
            <PWAInstallButton />
            <GlobalAnalyticsTracker />
            <LegacyUserPermissions />
            <Toaster position="top-center" richColors />
          </div>
        </BrowserRouter>
      </AuthProvider>
    </I18nProvider>
  );
}

export default App;
