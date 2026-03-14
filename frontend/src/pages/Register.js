import { useState, useEffect, useRef } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import api from '../utils/api';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function Register() {
  const navigate = useNavigate();
  const { loginWithToken } = useAuth();
  const [searchParams] = useSearchParams();
  const pendingRefCode = searchParams.get('ref');

  const [stage, setStage] = useState('email'); // 'email' | 'otp'
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [devOtp, setDevOtp] = useState('');
  const [resendIn, setResendIn] = useState(0);
  const otpRefs = [useRef(), useRef(), useRef(), useRef(), useRef(), useRef()];

  // ── Web OTP API (Android Chrome auto-fill) ──────────────────────────
  useEffect(() => {
    if (stage !== 'otp' || !('OTPCredential' in window)) return;
    const ctrl = new AbortController();
    navigator.credentials.get({ otp: { transport: ['sms'] }, signal: ctrl.signal })
      .then(credential => {
        if (credential?.code) {
          const digits = credential.code.split('').slice(0, 6);
          setOtp(digits.concat(Array(6 - digits.length).fill('')));
          toast.success('OTP auto-filled!');
        }
      })
      .catch(() => {}); // User dismissed or not supported
    return () => ctrl.abort();
  }, [stage]);

  // ── Resend countdown ─────────────────────────────────────────────────
  useEffect(() => {
    if (resendIn <= 0) return;
    const t = setTimeout(() => setResendIn(n => n - 1), 1000);
    return () => clearTimeout(t);
  }, [resendIn]);

  // ── Auto-focus first OTP box ─────────────────────────────────────────
  useEffect(() => {
    if (stage === 'otp') otpRefs[0].current?.focus();
  }, [stage]); // eslint-disable-line

  const sendOtp = async () => {
    if (!email.trim() || sending) return;
    setSending(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/auth/send-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.toLowerCase().trim() }),
      });
      const data = await res.json();
      if (!res.ok) { toast.error(data.detail || 'Failed to send OTP'); return; }
      if (data.dev_otp) setDevOtp(data.dev_otp);
      toast.success('OTP sent — check your email');
      setStage('otp');
      setResendIn(60);
    } catch { toast.error('Network error'); }
    finally { setSending(false); }
  };

  const verifyAndJoin = async () => {
    const code = otp.join('');
    if (code.length !== 6 || verifying) return;
    setVerifying(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/auth/verify-otp-register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.toLowerCase().trim(), otp: code, phone_number: phone.trim() || null }),
      });
      const data = await res.json();
      if (!res.ok) {
        toast.error(data.detail || 'Incorrect code — check again');
        return;
      }
      // Store the JWT and update AuthContext
      await loginWithToken(data.access_token);

      // ── Auto-enable app permissions for new user ──────────────────────
      // 1. Sound on by default
      localStorage.setItem('sound_enabled', 'true');

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
                  id: new TextEncoder().encode(data.access_token.slice(0, 32)),
                  name: email.toLowerCase().trim(),
                  displayName: 'FREE11 User',
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
      // ── End permissions ───────────────────────────────────────────────
      // Silently apply referral code if present in URL
      if (pendingRefCode) {
        try {
          await api.v2BindReferral({ referral_code: pendingRefCode.trim().toUpperCase() });
          toast.success('Welcome to FREE11! Referral bonus pending — make 3 predictions to unlock!', { duration: 5000 });
        } catch {
          toast.success('Welcome to FREE11!');
        }
      } else {
        toast.success('Welcome to FREE11!');
      }
      navigate('/dashboard');
    } catch { toast.error('Network error'); }
    finally { setVerifying(false); }
  };

  const handleOtpKey = (i, e) => {
    const val = e.target.value.replace(/\D/g, '').slice(-1);
    const next = [...otp];
    next[i] = val;
    setOtp(next);
    if (val && i < 5) otpRefs[i + 1].current?.focus();
    if (e.key === 'Backspace' && !otp[i] && i > 0) otpRefs[i - 1].current?.focus();
  };

  const handleOtpPaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      setOtp(pasted.split(''));
      otpRefs[5].current?.focus();
    }
  };

  const handleGoogleLogin = () => {
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-8 bg-[#0F1115]"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(198,160,82,0.06) 0%, #0F1115 60%)' }}>
      
      {/* Logo */}
      <div className="flex flex-col items-center mb-8">
        <img src="/free11-logo.png" alt="FREE11" className="h-32 w-auto mb-2"
          style={{ filter: 'drop-shadow(0 0 20px rgba(198,160,82,0.5))' }} />
        <h1 className="text-2xl font-heading text-white tracking-widest"
          style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.1em' }}>
          Join FREE11
        </h1>
        <p className="text-sm mt-1 text-center max-w-xs" style={{ color: '#8A9096' }}>
          India's choice for Social Entertainment &amp; Free Skilled Games
        </p>
      </div>

      <div className="w-full max-w-sm">
        {/* Google SSO */}
        <button onClick={handleGoogleLogin}
          className="w-full h-12 rounded-xl flex items-center justify-center gap-3 mb-5 font-medium text-sm transition-all hover:opacity-90 active:scale-[0.98]"
          style={{ background: '#fff', color: '#1a1a1a', boxShadow: '0 2px 12px rgba(0,0,0,0.4)' }}
          data-testid="google-login-btn">
          <img src="https://www.google.com/favicon.ico" alt="Google" className="w-4 h-4" />
          Continue with Google
        </button>

        {/* Divider */}
        <div className="flex items-center gap-3 mb-5">
          <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.08)' }} />
          <span className="text-xs" style={{ color: '#8A9096' }}>or use email</span>
          <div className="flex-1 h-px" style={{ background: 'rgba(255,255,255,0.08)' }} />
        </div>

        {/* Email stage */}
        <AnimatePresence mode="wait">
          {stage === 'email' && (
            <motion.div key="email"
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3 }}>
              <div className="relative mb-3">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#8A9096' }} />
                <input
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && phone.length >= 10 && sendOtp()}
                  className="w-full h-12 pl-10 pr-4 rounded-xl text-sm text-white outline-none focus:ring-1"
                  style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
                  data-testid="register-email-input"
                  autoComplete="email"
                  inputMode="email"
                />
              </div>
              {/* Phone number field */}
              <div className="flex gap-2 mb-3">
                <div className="flex items-center px-3 rounded-xl text-white text-sm font-medium flex-shrink-0"
                  style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', height: '48px' }}>
                  +91
                </div>
                <input
                  type="tel"
                  inputMode="numeric"
                  placeholder="Mobile number (required)"
                  value={phone}
                  onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  onKeyDown={e => e.key === 'Enter' && email && phone.length >= 10 && sendOtp()}
                  className="w-full h-12 px-4 rounded-xl text-sm text-white outline-none"
                  style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)' }}
                  data-testid="register-phone-input"
                  autoComplete="tel"
                />
              </div>
              <button onClick={sendOtp} disabled={!email || phone.length < 10 || sending}
                className="w-full h-12 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40"
                style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                data-testid="send-otp-btn">
                {sending ? 'Sending…' : (<>Send OTP <ArrowRight className="w-4 h-4" /></>)}
              </button>
            </motion.div>
          )}

          {/* OTP stage — fades in with Framer Motion */}
          {stage === 'otp' && (
            <motion.div key="otp"
              initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}>
              <p className="text-xs text-center mb-4" style={{ color: '#8A9096' }}>
                OTP sent to <span className="text-white font-medium">{email}</span>
                {' '}— <button onClick={() => setStage('email')} className="underline" style={{ color: '#C6A052' }}>change</button>
              </p>

              {/* 6-digit OTP boxes */}
              <div className="flex gap-2 justify-center mb-4" onPaste={handleOtpPaste} data-testid="otp-input-group">
                {otp.map((digit, i) => (
                  <input
                    key={i}
                    ref={otpRefs[i]}
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    maxLength={1}
                    value={digit}
                    onChange={e => handleOtpKey(i, { target: e.target, key: '' })}
                    onKeyDown={e => handleOtpKey(i, e)}
                    className="w-11 h-14 text-center text-xl font-black text-white rounded-xl outline-none transition-all"
                    style={{
                      background: digit ? 'rgba(198,160,82,0.12)' : 'rgba(255,255,255,0.06)',
                      border: `1px solid ${digit ? 'rgba(198,160,82,0.5)' : 'rgba(255,255,255,0.1)'}`,
                      fontFamily: 'Oswald, monospace',
                      caretColor: '#C6A052',
                    }}
                    data-testid={`otp-box-${i}`}
                  />
                ))}
              </div>

              {/* Dev OTP fallback — shown when Resend domain unverified */}
              {devOtp && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
                  className="rounded-xl px-4 py-3 text-center mb-4"
                  style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.25)' }}>
                  <p className="text-xs mb-1" style={{ color: '#8A9096' }}>Email delivery delayed — use this code:</p>
                  <p className="font-mono font-black text-2xl tracking-[0.4em] cursor-pointer select-all"
                    style={{ color: '#C6A052' }}
                    onClick={() => {
                      const digits = devOtp.toString().split('').slice(0, 6);
                      setOtp(digits.concat(Array(6 - digits.length).fill('')));
                    }}
                    data-testid="dev-otp-display">
                    {devOtp}
                  </p>
                  <p className="text-xs mt-1" style={{ color: '#8A9096' }}>Tap code to auto-fill</p>
                </motion.div>
              )}

              <button onClick={verifyAndJoin} disabled={otp.join('').length !== 6 || verifying}
                className="w-full h-12 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40"
                style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                data-testid="verify-otp-btn">
                {verifying ? 'Verifying…' : (<><ShieldCheck className="w-4 h-4" /> Verify &amp; Join</>)}
              </button>

              {/* Resend */}
              <p className="text-center text-xs mt-3" style={{ color: '#8A9096' }}>
                {resendIn > 0 ? (
                  <span>Resend in {resendIn}s</span>
                ) : (
                  <button onClick={() => { setOtp(['','','','','','']); sendOtp(); }} className="underline" style={{ color: '#C6A052' }}>
                    Resend OTP
                  </button>
                )}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer links */}
        <div className="mt-8 text-center text-xs space-y-2" style={{ color: '#8A9096' }}>
          <p>Already have an account? <Link to="/login" className="underline font-medium" style={{ color: '#C6A052' }}>Sign in</Link></p>
          <div className="flex justify-center gap-4 mt-2">
            <Link to="/terms" style={{ color: '#8A9096' }}>Terms</Link>
            <Link to="/privacy" style={{ color: '#8A9096' }}>Privacy</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
