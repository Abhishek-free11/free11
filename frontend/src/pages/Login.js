import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { Input } from '@/components/ui/input';
import { Eye, EyeOff, Loader2, Fingerprint, X, Mail, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import {
  isBiometricEnabled,
  getBiometricToken,
  getBiometricEmail,
  getBiometricName,
  enableBiometric,
  disableBiometric,
} from '../utils/biometric';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Login = () => {
  const navigate = useNavigate();
  const { user, login, loginWithToken } = useAuth();
  const { t } = useI18n();

  // Password mode state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [biometricLoading, setBiometricLoading] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [showEnableBiometric, setShowEnableBiometric] = useState(false);
  const [pendingLoginData, setPendingLoginData] = useState(null);

  // OTP magic-link mode state
  const [loginMode, setLoginMode] = useState('password'); // 'password' | 'otp'
  const [otpEmail, setOtpEmail] = useState('');
  const [otpStage, setOtpStage] = useState('email'); // 'email' | 'code'
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [otpLoading, setOtpLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);
  const [devOtp, setDevOtp] = useState('');
  const otpRefs = useRef([]);
  const timerRef = useRef(null);

  useEffect(() => {
    if (user) navigate('/match-centre', { replace: true });
    // Show biometric button if previously enabled
    setBiometricAvailable(isBiometricEnabled());
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      // Token is stored in localStorage by AuthContext.login
      const storedToken = localStorage.getItem('token');
      if (!isBiometricEnabled() && storedToken) {
        // Offer biometric setup for next time
        setPendingLoginData({ email, token: storedToken });
        setShowEnableBiometric(true);
      } else {
        toast.success(t('auth.welcome_back'));
        navigate('/match-centre');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || t('auth.login_failed'));
    } finally {
      setLoading(false);
    }
  };

  const handleBiometricLogin = async () => {
    setBiometricLoading(true);
    try {
      const token = await getBiometricToken();
      if (!token) {
        toast.error('Biometric authentication cancelled');
        setBiometricLoading(false);
        return;
      }
      // Set token in localStorage so api.getMe() can pick it up
      localStorage.setItem('token', token);
      const { data } = await api.getMe();
      if (data?.id) {
        // Valid — hard reload to reinitialise AuthContext with the restored token
        window.location.href = '/match-centre';
      } else {
        throw new Error('expired');
      }
    } catch {
      localStorage.removeItem('token');
      toast.error('Session expired. Please log in again.');
      disableBiometric();
      setBiometricAvailable(false);
    }
    setBiometricLoading(false);
  };

  const handleEnableBiometric = async () => {
    if (!pendingLoginData) return;
    try {
      await enableBiometric(pendingLoginData.email, pendingLoginData.token, pendingLoginData.name);
      toast.success('Biometric login enabled!');
    } catch {
      toast.error('Could not enable biometric');
    }
    setShowEnableBiometric(false);
    setPendingLoginData(null);
    toast.success(t('auth.welcome_back'));
    navigate('/match-centre');
  };

  const handleSkipBiometric = () => {
    setShowEnableBiometric(false);
    setPendingLoginData(null);
    toast.success(t('auth.welcome_back'));
    navigate('/match-centre');
  };

  // ── OTP Magic-link helpers ──
  const startResendTimer = () => {
    setResendTimer(30);
    timerRef.current = setInterval(() => {
      setResendTimer(s => { if (s <= 1) { clearInterval(timerRef.current); return 0; } return s - 1; });
    }, 1000);
  };

  const sendOtp = async () => {
    if (!otpEmail.trim()) { toast.error('Enter your email first'); return; }
    setOtpLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/auth/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: otpEmail.toLowerCase().trim() }),
      });
      if (res.status === 429) { toast.error('Too many requests — wait a minute and try again'); setOtpLoading(false); return; }
      if (!res.ok) { toast.error('Failed to send OTP'); setOtpLoading(false); return; }
      const data = await res.json();
      if (data.dev_otp) setDevOtp(String(data.dev_otp));
      setOtpStage('code');
      setOtp(['', '', '', '', '', '']);
      startResendTimer();
      setTimeout(() => otpRefs.current[0]?.focus(), 100);
      toast.success('OTP sent to your email');
    } catch { toast.error('Failed to send OTP'); }
    setOtpLoading(false);
  };

  const handleOtpKey = (i, e) => {
    if (e.key === 'Backspace' && !otp[i] && i > 0) otpRefs.current[i - 1]?.focus();
  };

  const handleOtpChange = (i, val) => {
    const digit = val.replace(/\D/g, '').slice(-1);
    const next = [...otp];
    next[i] = digit;
    setOtp(next);
    if (digit && i < 5) otpRefs.current[i + 1]?.focus();
  };

  const verifyOtp = async () => {
    const code = otp.join('');
    if (code.length !== 6 || otpLoading) return;
    setOtpLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/auth/verify-otp-register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: otpEmail.toLowerCase().trim(), otp: code }),
      });
      if (!res.ok) {
        let detail = 'Incorrect code';
        try { detail = (await res.json()).detail || detail; } catch {}
        toast.error(detail);
        setOtpLoading(false);
        return;
      }
      const data = await res.json();
      await loginWithToken(data.access_token);
      toast.success(t('auth.welcome_back'));
      navigate('/match-centre');
    } catch { toast.error('Network error'); }
    setOtpLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0F1115] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Broadcast grid */}
      <div className="absolute inset-0 bg-broadcast-grid opacity-100 pointer-events-none" />
      {/* Gold glow orb */}
      <div className="absolute pointer-events-none"
        style={{ top: '-10%', left: '50%', transform: 'translateX(-50%)', width: '80vw', height: '40vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.08) 0%, transparent 70%)' }}
      />

      {/* ── Enable Biometric Modal ── */}
      {showEnableBiometric && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)' }}>
          <div className="w-full max-w-xs rounded-2xl p-6 text-center animate-slide-up"
            style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.2)' }}>
            <button onClick={handleSkipBiometric} className="absolute top-4 right-4 p-1" style={{ color: '#8A9096' }}>
              <X className="w-4 h-4" />
            </button>
            <div className="w-16 h-16 rounded-2xl mx-auto mb-4 flex items-center justify-center animate-coin-glow"
              style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.15), rgba(224,184,79,0.1))', border: '1px solid rgba(198,160,82,0.3)' }}>
              <Fingerprint className="w-8 h-8" style={{ color: '#C6A052' }} />
            </div>
            <h3 className="font-heading text-xl tracking-wider text-white mb-1">QUICK ACCESS</h3>
            <p className="text-sm mb-5" style={{ color: '#8A9096' }}>
              Skip the password next time. Use your fingerprint or face to sign in instantly.
            </p>
            <button onClick={handleEnableBiometric} className="btn-gold w-full h-11 rounded-xl text-sm mb-2 flex items-center justify-center gap-2"
              data-testid="enable-biometric-btn">
              <Fingerprint className="w-4 h-4" /> Enable Biometric Login
            </button>
            <button onClick={handleSkipBiometric} className="w-full h-9 text-sm transition-colors" style={{ color: '#8A9096' }}
              data-testid="skip-biometric-btn">
              Not now
            </button>
          </div>
        </div>
      )}

      <div className="w-full max-w-sm relative z-10 animate-slide-up">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="relative inline-block mb-2">
            <img src="/free11-logo.png" alt="FREE11" className="h-40 w-auto mx-auto"
              style={{ filter: 'drop-shadow(0 0 28px rgba(198,160,82,0.55))' }} />
          </div>
          <p className="text-sm mt-1 font-medium" style={{ color: '#8A9096' }}>India's choice for Social Entertainment &amp; Free Skilled Games</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-6"
          style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.18)', boxShadow: '0 24px 64px rgba(0,0,0,0.6)' }}
          data-testid="login-card">

          {/* Mode toggle tabs */}
          <div className="flex gap-1 mb-6 p-1 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
            <button onClick={() => setLoginMode('password')}
              className="flex-1 py-2 rounded-lg text-xs font-bold tracking-wider transition-all"
              style={loginMode === 'password' ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' } : { color: '#8A9096' }}
              data-testid="mode-password-tab">PASSWORD</button>
            <button onClick={() => { setLoginMode('otp'); setOtpStage('email'); setOtp(['','','','','','']); setDevOtp(''); }}
              className="flex-1 py-2 rounded-lg text-xs font-bold tracking-wider transition-all"
              style={loginMode === 'otp' ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' } : { color: '#8A9096' }}
              data-testid="mode-otp-tab">EMAIL OTP</button>
          </div>

          {loginMode === 'password' ? (
            <>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#8A9096' }}>{t('auth.email')}</label>
                  <Input type="email" placeholder={t('auth.email_placeholder')} value={email}
                    onChange={(e) => setEmail(e.target.value)} required autoComplete="email"
                    className="h-11 text-white placeholder:text-slate-600 border"
                    style={{ background: '#0F1115', borderColor: 'rgba(198,160,82,0.2)' }}
                    data-testid="email-input" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#8A9096' }}>{t('auth.password')}</label>
                  <div className="relative">
                    <Input type={showPassword ? 'text' : 'password'} placeholder="••••••••" value={password}
                      onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password"
                      className="h-11 text-white pr-10 border"
                      style={{ background: '#0F1115', borderColor: 'rgba(198,160,82,0.2)' }}
                      data-testid="password-input" />
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2" style={{ color: '#8A9096' }}>
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                <button type="submit" disabled={loading}
                  className="w-full h-12 rounded-xl font-heading text-xl tracking-widest transition-all disabled:opacity-50 ripple"
                  style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                  data-testid="submit-btn">
                  {loading ? <span className="flex items-center justify-center gap-2"><Loader2 className="h-5 w-5 animate-spin" /> Signing in...</span> : t('auth.sign_in')}
                </button>
              </form>
            </>
          ) : (
            /* ── OTP magic-link mode ── */
            <div data-testid="otp-login-section">
              <p className="text-xs mb-5" style={{ color: '#8A9096' }}>
                No password needed — we'll send a one-time code to your email.
              </p>
              {otpStage === 'email' ? (
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#8A9096' }}>Email</label>
                    <Input type="email" placeholder="you@example.com" value={otpEmail}
                      onChange={e => setOtpEmail(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && sendOtp()}
                      className="h-11 text-white placeholder:text-slate-600 border"
                      style={{ background: '#0F1115', borderColor: 'rgba(198,160,82,0.2)' }}
                      data-testid="otp-email-input" />
                  </div>
                  <button onClick={sendOtp} disabled={otpLoading || !otpEmail.trim()}
                    className="w-full h-12 rounded-xl font-heading text-lg tracking-widest flex items-center justify-center gap-2 disabled:opacity-50 transition-all"
                    style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                    data-testid="send-otp-btn">
                    {otpLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <><Mail className="h-4 w-4" /> Send OTP</>}
                  </button>
                </div>
              ) : (
                <div className="space-y-5">
                  <div>
                    <p className="text-xs mb-3" style={{ color: '#8A9096' }}>
                      Code sent to <span style={{ color: '#C6A052' }}>{otpEmail}</span>
                      <button onClick={() => setOtpStage('email')} className="ml-2 underline" style={{ color: '#8A9096' }}>Change</button>
                    </p>
                    <div className="flex gap-2 justify-between" data-testid="otp-boxes">
                      {otp.map((digit, i) => (
                        <input key={i} ref={el => otpRefs.current[i] = el}
                          type="text" inputMode="numeric" maxLength={1} value={digit}
                          onChange={e => handleOtpChange(i, e.target.value)}
                          onKeyDown={e => handleOtpKey(i, e)}
                          className="w-11 h-12 rounded-xl text-center text-lg font-bold text-white focus:outline-none"
                          style={{ background: '#0F1115', border: `1px solid ${digit ? '#C6A052' : 'rgba(255,255,255,0.12)'}` }}
                          data-testid={`otp-box-${i}`} />
                      ))}
                    </div>
                  </div>
                  <button onClick={verifyOtp} disabled={otpLoading || otp.join('').length !== 6}
                    className="w-full h-12 rounded-xl font-heading text-lg tracking-widest flex items-center justify-center gap-2 disabled:opacity-50 transition-all"
                    style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                    data-testid="verify-otp-btn">
                    {otpLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <>Verify &amp; Sign In <ArrowRight className="h-4 w-4" /></>}
                  </button>
                  {devOtp && (
                    <div className="rounded-xl px-4 py-3 text-center"
                      style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.25)' }}>
                      <p className="text-xs mb-1" style={{ color: '#8A9096' }}>Email delivery delayed — use this code:</p>
                      <p className="font-mono font-black text-2xl tracking-[0.4em] cursor-pointer select-all"
                        style={{ color: '#C6A052' }}
                        onClick={() => {
                          const digits = devOtp.split('').slice(0, 6);
                          setOtp(digits.concat(Array(6 - digits.length).fill('')));
                        }}
                        data-testid="dev-otp-display">{devOtp}</p>
                      <p className="text-xs mt-1" style={{ color: '#8A9096' }}>Tap to auto-fill</p>
                    </div>
                  )}
                  <div className="text-center">
                    {resendTimer > 0
                      ? <span className="text-xs" style={{ color: '#8A9096' }}>Resend in {resendTimer}s</span>
                      : <button onClick={sendOtp} className="text-xs underline" style={{ color: '#C6A052' }} data-testid="resend-otp-btn">Resend OTP</button>
                    }
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Biometric Login ── */}
          {biometricAvailable && (
            <div className="mt-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
                <span className="text-xs" style={{ color: '#8A9096' }}>or</span>
                <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
              </div>
              <button onClick={handleBiometricLogin} disabled={biometricLoading}
                className="w-full h-12 rounded-xl flex items-center justify-center gap-2.5 transition-all disabled:opacity-50"
                style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.25)', color: '#C6A052' }}
                data-testid="biometric-login-btn">
                {biometricLoading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span className="text-sm font-medium">Authenticating...</span>
                  </>
                ) : (
                  <>
                    <Fingerprint className="h-6 w-6" />
                    <span className="text-sm font-medium">
                      Sign in as <span className="font-bold">{getBiometricName() || getBiometricEmail()?.split('@')[0]}</span>
                    </span>
                  </>
                )}
              </button>
              <button onClick={() => { disableBiometric(); setBiometricAvailable(false); }}
                className="w-full text-center text-xs mt-2 transition-colors" style={{ color: '#8A9096' }}
                data-testid="disable-biometric-btn">
                Use different account
              </button>
            </div>
          )}

          {/* ── Google Login (Section 12) ── */}
          <div className="mt-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
              <span className="text-xs" style={{ color: '#8A9096' }}>or continue with</span>
              <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.06)' }} />
            </div>
            <button
              onClick={() => {
                // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
                const redirectUrl = window.location.origin + '/dashboard';
                window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
              }}
              className="w-full h-12 rounded-xl flex items-center justify-center gap-3 transition-all hover:scale-[1.01] active:scale-[0.99]"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.12)', color: 'white' }}
              data-testid="google-login-btn"
            >
              <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              <span className="text-sm font-medium">Continue with Google</span>
            </button>
          </div>

          <p className="mt-5 text-center text-sm" style={{ color: '#8A9096' }}>
            {t('auth.no_account')}{' '}
            <Link to="/register" className="font-semibold transition-colors hover:underline" style={{ color: '#C6A052' }}>
              {t('auth.sign_up_link')}
            </Link>
          </p>
        </div>

        <p className="text-center text-xs mt-6" style={{ color: '#8A9096' }}>
          By signing in you agree to our{' '}
          <Link to="/terms" className="underline hover:text-white transition-colors">Terms</Link>
          {' & '}
          <Link to="/privacy" className="underline hover:text-white transition-colors">Privacy Policy</Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
