import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { Input } from '@/components/ui/input';
import { Eye, EyeOff, Loader2, Fingerprint, X, Phone, Mail } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import { createRecaptchaVerifier, sendPhoneOTP, confirmPhoneOTP, clearRecaptchaVerifier } from '../firebase';
import {
  isBiometricEnabled,
  getBiometricToken,
  getBiometricEmail,
  getBiometricName,
  enableBiometric,
  disableBiometric,
} from '../utils/biometric';

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

  // Login mode: 'password' | 'phone'
  const [loginMode, setLoginMode] = useState('password');

  // Phone OTP state
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneStage, setPhoneStage] = useState('number'); // 'number' | 'verifying'
  const [phoneLoading, setPhoneLoading] = useState(false);
  const [phoneResendTimer, setPhoneResendTimer] = useState(0);
  const confirmationResultRef = useRef(null);
  const recaptchaRef = useRef(null);
  const phoneTimerRef = useRef(null);

  // Phone OTP — DOB gate for new users, then email capture
  const [phoneDob, setPhoneDob] = useState('');
  const [phoneDobError, setPhoneDobError] = useState('');
  const [showDobGate, setShowDobGate] = useState(false);
  const [pendingFirebaseToken, setPendingFirebaseToken] = useState(null);

  // After phone OTP — collect email for new users
  const [showEmailCapture, setShowEmailCapture] = useState(false);
  const [captureEmail, setCaptureEmail] = useState('');
  const [captureEmailLoading, setCaptureEmailLoading] = useState(false);

  useEffect(() => {
    if (user) navigate('/match-centre', { replace: true });
    // Show biometric button if previously enabled
    setBiometricAvailable(isBiometricEnabled());
    // Cleanup recaptcha on unmount
    return () => { clearRecaptchaVerifier(); };
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

  // ── Phone OTP handlers ──────────────────────────────────────────────
  const startPhoneResendTimer = () => {
    setPhoneResendTimer(30);
    phoneTimerRef.current = setInterval(() => {
      setPhoneResendTimer(t => { if (t <= 1) { clearInterval(phoneTimerRef.current); return 0; } return t - 1; });
    }, 1000);
  };

  const sendPhoneOTPHandler = async () => {
    const phone = phoneNumber.trim();
    if (!phone || phone.length < 10) { toast.error('Enter a valid phone number'); return; }
    const e164 = phone.startsWith('+') ? phone : `+91${phone.replace(/\D/g, '')}`;
    setPhoneLoading(true);
    try {
      // Always create a fresh verifier — reusing a stale one causes "already rendered" error
      recaptchaRef.current = await createRecaptchaVerifier('recaptcha-container');
      const confirmation = await sendPhoneOTP(e164, recaptchaRef.current);
      confirmationResultRef.current = confirmation;
      setPhoneStage('verifying');
      startPhoneResendTimer();

      // Try Web OTP API for silent auto-detection
      if ('OTPCredential' in window) {
        const ac = new AbortController();
        setTimeout(() => ac.abort(), 60000); // 60s timeout
        navigator.credentials.get({ otp: { transport: ['sms'] }, signal: ac.signal })
          .then(async (otpCred) => {
            if (otpCred?.code) await verifyPhoneCode(otpCred.code);
          })
          .catch(() => {}); // silent fail — user types manually
      }
    } catch (err) {
      const code = err?.code || '';
      if (code === 'auth/network-request-failed') {
        toast.error('Network error — check your internet connection and try again.');
      } else if (code === 'auth/too-many-requests') {
        toast.error('Too many attempts. Please wait a few minutes and try again.');
      } else if (code === 'auth/invalid-phone-number') {
        toast.error('Invalid phone number. Please enter a valid 10-digit Indian number.');
      } else {
        toast.error(err?.message || 'Failed to send OTP. Please try again.');
      }
      clearRecaptchaVerifier();
      recaptchaRef.current = null;
    }
    setPhoneLoading(false);
  };

  const verifyPhoneCode = async (code, dob = null) => {
    if (!confirmationResultRef.current) return;
    setPhoneLoading(true);
    try {
      const idToken = await confirmPhoneOTP(confirmationResultRef.current, code);
      // First attempt without DOB — backend will tell us if DOB is required
      const resp = await api.post('/auth/phone-verify', {
        firebase_id_token: idToken,
        date_of_birth: dob || undefined,
      });
      const { access_token, user: userData, is_new_user } = resp.data;
      loginWithToken(access_token, userData);
      if (is_new_user && !userData?.email) {
        setShowEmailCapture(true);
      } else {
        toast.success('Welcome back to FREE11!');
        navigate('/match-centre');
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      // Backend requires DOB for new user
      if (detail?.error === 'dob_required' || detail?.error === 'age_restricted') {
        const idToken = await confirmPhoneOTP(confirmationResultRef.current, code).catch(() => null);
        if (idToken) setPendingFirebaseToken(idToken);
        if (detail?.error === 'age_restricted') {
          toast.error(detail.message || 'You must be 18+ to use FREE11.');
        } else {
          setShowDobGate(true);
        }
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Incorrect OTP. Please try again.');
      }
    }
    setPhoneLoading(false);
  };

  const handleDobSubmit = async () => {
    if (!phoneDob) { setPhoneDobError('Please enter your date of birth.'); return; }
    const dob = new Date(phoneDob);
    const today = new Date();
    let age = today.getFullYear() - dob.getFullYear();
    const m = today.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;
    if (age < 18) { setPhoneDobError('You must be 18 or older to use FREE11.'); return; }
    if (age > 120) { setPhoneDobError('Please enter a valid date of birth.'); return; }
    setPhoneDobError('');
    if (!pendingFirebaseToken) return;
    setPhoneLoading(true);
    try {
      const resp = await api.post('/auth/phone-verify', {
        firebase_id_token: pendingFirebaseToken,
        date_of_birth: phoneDob,
      });
      const { access_token, user: userData, is_new_user } = resp.data;
      loginWithToken(access_token, userData);
      setShowDobGate(false);
      if (is_new_user && !userData?.email) {
        setShowEmailCapture(true);
      } else {
        toast.success('Welcome to FREE11!');
        navigate('/match-centre');
      }
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (detail?.error === 'age_restricted') {
        setPhoneDobError(detail.message || 'You must be 18+ to use FREE11.');
      } else {
        toast.error(typeof detail === 'string' ? detail : 'Registration failed. Please try again.');
      }
    }
    setPhoneLoading(false);
  };

  const handleEmailCapture = async (skip = false) => {
    if (skip) { navigate('/match-centre'); return; }
    if (!captureEmail.trim()) return;
    setCaptureEmailLoading(true);
    try {
      await api.post('/auth/update-contact', { email: captureEmail.trim().toLowerCase() });
      toast.success('Email saved! Welcome to FREE11!');
      navigate('/match-centre');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Could not save email. You can add it later in Settings.');
      navigate('/match-centre');
    }
    setCaptureEmailLoading(false);
  };

  const handlePhoneOtpInput = (val) => {
    const digits = val.replace(/\D/g, '').slice(0, 6);
    if (digits.length === 6) verifyPhoneCode(digits);
  };

  return (
    <div className="min-h-screen bg-[#0F1115] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Broadcast grid */}
      <div className="absolute inset-0 bg-broadcast-grid opacity-100 pointer-events-none" />
      {/* Gold glow orb */}
      <div className="absolute pointer-events-none"
        style={{ top: '-10%', left: '50%', transform: 'translateX(-50%)', width: '80vw', height: '40vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.08) 0%, transparent 70%)' }}
      />

      {/* ── DOB Gate Modal (new phone users — 18+ check) ── */}
      {showDobGate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.9)', backdropFilter: 'blur(8px)' }}>
          <div className="w-full max-w-xs rounded-2xl p-6 text-center animate-slide-up"
            style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.25)' }}>
            <div className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.15), rgba(224,184,79,0.1))', border: '1px solid rgba(198,160,82,0.3)' }}>
              <span className="text-2xl font-black" style={{ color: '#C6A052' }}>18+</span>
            </div>
            <h3 className="font-heading text-xl tracking-wider text-white mb-1">AGE VERIFICATION</h3>
            <p className="text-xs mb-5" style={{ color: '#8A9096' }}>
              FREE11 is for adults only. Please confirm your date of birth.
            </p>
            <input
              type="date"
              value={phoneDob}
              onChange={e => { setPhoneDob(e.target.value); setPhoneDobError(''); }}
              max={new Date(new Date().setFullYear(new Date().getFullYear() - 18)).toISOString().split('T')[0]}
              className="w-full h-11 px-4 rounded-xl text-sm text-white outline-none mb-1"
              style={{ background: '#0F1115', border: `1px solid ${phoneDobError ? '#ef4444' : 'rgba(198,160,82,0.2)'}`, colorScheme: 'dark' }}
              data-testid="phone-dob-input" />
            {phoneDobError && <p className="text-xs mb-2" style={{ color: '#ef4444' }}>{phoneDobError}</p>}
            <button onClick={handleDobSubmit} disabled={!phoneDob || phoneLoading}
              className="w-full h-11 rounded-xl font-bold text-sm mt-3 disabled:opacity-40 transition-all"
              style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
              data-testid="confirm-dob-btn">
              {phoneLoading ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : 'Confirm Age & Continue'}
            </button>
          </div>
        </div>
      )}

      {/* ── Email Capture Modal (new phone users) ── */}
      {showEmailCapture && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(0,0,0,0.9)', backdropFilter: 'blur(8px)' }}>
          <div className="w-full max-w-xs rounded-2xl p-6 text-center animate-slide-up"
            style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.25)' }}>
            <div className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.15), rgba(224,184,79,0.1))', border: '1px solid rgba(198,160,82,0.3)' }}>
              <Mail className="w-7 h-7" style={{ color: '#C6A052' }} />
            </div>
            <h3 className="font-heading text-xl tracking-wider text-white mb-1">ADD YOUR EMAIL</h3>
            <p className="text-xs mb-5" style={{ color: '#8A9096' }}>
              Secure your account and receive important updates. You can skip this for now.
            </p>
            <Input
              type="email" placeholder="you@example.com"
              value={captureEmail} onChange={e => setCaptureEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleEmailCapture(false)}
              className="h-11 text-white placeholder:text-slate-600 border mb-3"
              style={{ background: '#0F1115', borderColor: 'rgba(198,160,82,0.2)' }}
              data-testid="capture-email-input" autoFocus />
            <button onClick={() => handleEmailCapture(false)} disabled={!captureEmail.trim() || captureEmailLoading}
              className="w-full h-11 rounded-xl font-bold text-sm mb-2 disabled:opacity-40 transition-all"
              style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
              data-testid="save-email-btn">
              {captureEmailLoading ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : 'Save Email'}
            </button>
            <button onClick={() => handleEmailCapture(true)}
              className="w-full h-9 text-xs transition-colors" style={{ color: '#8A9096' }}
              data-testid="skip-email-btn">
              Skip for now
            </button>
          </div>
        </div>
      )}

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

          {/* Mode toggle tabs — EMAIL and PHONE only */}
          <div className="flex gap-1 mb-6 p-1 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
            <button onClick={() => setLoginMode('password')}
              className="flex-1 py-2.5 rounded-lg text-sm font-bold tracking-wider transition-all"
              style={loginMode === 'password' ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' } : { color: '#8A9096' }}
              data-testid="mode-password-tab">EMAIL</button>
            <button onClick={() => { setLoginMode('phone'); setPhoneStage('number'); setPhoneNumber(''); clearRecaptchaVerifier(); recaptchaRef.current = null; }}
              className="flex-1 py-2.5 rounded-lg text-sm font-bold tracking-wider transition-all"
              style={loginMode === 'phone' ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' } : { color: '#8A9096' }}
              data-testid="mode-phone-tab">PHONE</button>
          </div>

          {/* Invisible reCAPTCHA container */}
          <div id="recaptcha-container" />

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
          ) : loginMode === 'phone' ? (
            /* ── Phone OTP mode ── */
            <div data-testid="phone-login-section">
              <p className="text-xs mb-5" style={{ color: '#8A9096' }}>
                Enter your mobile number — OTP will be sent automatically.
              </p>
              {phoneStage === 'number' ? (
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#8A9096' }}>Mobile Number</label>
                    <div className="flex gap-2">
                      <div className="flex items-center px-3 rounded-lg border text-white text-sm font-medium"
                        style={{ background: '#0F1115', borderColor: 'rgba(198,160,82,0.2)', minWidth: '54px' }}>
                        +91
                      </div>
                      <Input
                        type="tel" inputMode="numeric" placeholder="9876543210"
                        value={phoneNumber} onChange={e => setPhoneNumber(e.target.value.replace(/\D/g, '').slice(0, 10))}
                        onKeyDown={e => e.key === 'Enter' && sendPhoneOTPHandler()}
                        className="h-11 text-white placeholder:text-slate-600 border flex-1"
                        style={{ background: '#0F1115', borderColor: 'rgba(198,160,82,0.2)' }}
                        autoComplete="tel" data-testid="phone-input" />
                    </div>
                  </div>
                  <button onClick={sendPhoneOTPHandler} disabled={phoneLoading || phoneNumber.length < 10}
                    className="w-full h-12 rounded-xl font-heading text-xl tracking-widest transition-all disabled:opacity-50"
                    style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
                    data-testid="send-phone-otp-btn">
                    {phoneLoading ? <span className="flex items-center justify-center gap-2"><Loader2 className="h-5 w-5 animate-spin" /> Sending...</span> : 'Send OTP'}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="text-center mb-2">
                    <Phone className="h-8 w-8 mx-auto mb-2" style={{ color: '#C6A052' }} />
                    <p className="text-sm text-white font-medium">OTP sent to +91 {phoneNumber}</p>
                    <p className="text-xs mt-1" style={{ color: '#8A9096' }}>Verifying automatically from your SMS…</p>
                  </div>
                  <Input
                    type="text" inputMode="numeric" placeholder="------"
                    maxLength={6} autoComplete="one-time-code"
                    onChange={e => handlePhoneOtpInput(e.target.value)}
                    className="h-14 text-center text-2xl font-mono text-white tracking-[0.5em] border"
                    style={{ background: '#0F1115', borderColor: 'rgba(198,160,82,0.2)' }}
                    autoFocus data-testid="phone-otp-input" />
                  {phoneLoading && (
                    <div className="flex items-center justify-center gap-2 text-sm" style={{ color: '#C6A052' }}>
                      <Loader2 className="h-4 w-4 animate-spin" /> Verifying…
                    </div>
                  )}
                  <div className="text-center">
                    {phoneResendTimer > 0 ? (
                      <p className="text-xs" style={{ color: '#8A9096' }}>Resend in {phoneResendTimer}s</p>
                    ) : (
                      <button onClick={() => { setPhoneStage('number'); clearRecaptchaVerifier(); recaptchaRef.current = null; }}
                        className="text-xs font-semibold" style={{ color: '#C6A052' }} data-testid="change-phone-btn">
                        Change number / Resend
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : null}

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
