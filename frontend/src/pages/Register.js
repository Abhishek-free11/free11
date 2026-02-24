import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Coins, Ticket, CheckCircle, XCircle, Eye, EyeOff, Calendar, MapPin, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

// Country restriction - India only
const ALLOWED_COUNTRY = "India";

// No blocked states - all Indian states allowed
const BLOCKED_STATES = [];

const INDIAN_STATES = [
  "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
  "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli", "Daman and Diu", "Delhi",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand",
  "Karnataka", "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh", "Maharashtra",
  "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab",
  "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
  "Uttarakhand", "West Bengal"
];

const Register = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [inviteValid, setInviteValid] = useState(null);
  const [inviteChecking, setInviteChecking] = useState(false);
  const [loading, setLoading] = useState(false);
  const [betaRequired, setBetaRequired] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  
  // Age gate fields
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [ageValid, setAgeValid] = useState(null);
  
  // Geo-blocking fields
  const [state, setState] = useState('');
  const [stateBlocked, setStateBlocked] = useState(false);

  // Check if invite code is in URL
  useEffect(() => {
    const codeFromUrl = searchParams.get('invite') || searchParams.get('code');
    if (codeFromUrl) {
      setInviteCode(codeFromUrl);
      validateInviteCode(codeFromUrl);
    }
    
    // Check beta status
    const checkBetaStatus = async () => {
      try {
        const response = await api.getBetaStatus();
        setBetaRequired(response.data.require_invite_code);
      } catch (error) {
        console.error('Error checking beta status:', error);
      }
    };
    checkBetaStatus();
  }, [searchParams]);

  // Calculate age from date of birth
  const validateAge = (dob) => {
    if (!dob) {
      setAgeValid(null);
      return;
    }
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    setAgeValid(age >= 18);
  };

  // Check if state is blocked
  const checkStateBlocked = (selectedState) => {
    const blocked = BLOCKED_STATES.includes(selectedState);
    setStateBlocked(blocked);
    return blocked;
  };

  const validateInviteCode = async (code) => {
    if (!code || code.length < 5) {
      setInviteValid(null);
      return;
    }
    
    setInviteChecking(true);
    try {
      const response = await api.validateInvite(code);
      setInviteValid(response.data.valid);
    } catch (error) {
      setInviteValid(false);
    } finally {
      setInviteChecking(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Age validation (18+ still required for community platform)
    if (!ageValid) {
      toast.error('You must be 18 years or older to use FREE11');
      return;
    }
    
    if (!state) {
      toast.error('Please select your state');
      return;
    }
    
    if (betaRequired && !inviteValid) {
      toast.error('Valid invite code required for beta access');
      return;
    }
    
    setLoading(true);

    try {
      await register(email, name, password, inviteCode || null);
      toast.success('🎉 Welcome! You got 50 FREE coins!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-slate-900/50 border-slate-800 mx-4" data-testid="register-card">
        <CardHeader className="space-y-3 text-center px-4 sm:px-6">
          <div className="flex items-center justify-center gap-3">
            <img 
              src="/app-icon.png" 
              alt="FREE11" 
              className="h-12 w-12 sm:h-16 sm:w-16 rounded-xl"
            />
          </div>
          <CardTitle className="text-xl sm:text-2xl text-white">Join FREE11</CardTitle>
          <CardDescription className="text-slate-400 text-sm">Create your account and get 50 welcome coins</CardDescription>
        </CardHeader>
        <CardContent className="px-4 sm:px-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-slate-200 text-sm">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Your Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="bg-slate-800 border-slate-700 text-white h-11"
                data-testid="name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-200 text-sm">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-slate-800 border-slate-700 text-white h-11"
                data-testid="email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-200 text-sm">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="bg-slate-800 border-slate-700 text-white pr-10 h-11"
                  data-testid="password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            
            {/* Age Gate - Date of Birth */}
            <div className="space-y-2">
              <Label htmlFor="dob" className="text-slate-200 text-sm flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Date of Birth
                <span className="text-red-400 text-xs">(18+ only)</span>
              </Label>
              <Input
                id="dob"
                type="date"
                value={dateOfBirth}
                onChange={(e) => {
                  setDateOfBirth(e.target.value);
                  validateAge(e.target.value);
                }}
                required
                max={new Date(new Date().setFullYear(new Date().getFullYear() - 18)).toISOString().split('T')[0]}
                className={`bg-slate-800 border-slate-700 text-white h-11 ${
                  ageValid === true ? 'border-green-500' : 
                  ageValid === false ? 'border-red-500' : ''
                }`}
                data-testid="dob-input"
              />
              {ageValid === false && (
                <p className="text-xs text-red-400 flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  You must be 18 years or older
                </p>
              )}
            </div>
            
            {/* Geo-blocking - State Selection */}
            <div className="space-y-2">
              <Label htmlFor="state" className="text-slate-200 text-sm flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                State
              </Label>
              <select
                id="state"
                value={state}
                onChange={(e) => {
                  setState(e.target.value);
                  checkStateBlocked(e.target.value);
                }}
                required
                className={`w-full h-11 rounded-md bg-slate-800 border px-3 text-white ${
                  stateBlocked ? 'border-red-500' : 'border-slate-700'
                }`}
                data-testid="state-select"
              >
                <option value="">Select your state</option>
                {INDIAN_STATES.map((s) => (
                  <option key={s} value={s} disabled={BLOCKED_STATES.includes(s)}>
                    {s} {BLOCKED_STATES.includes(s) ? '(Not Available)' : ''}
                  </option>
                ))}
              </select>
              {stateBlocked && (
                <p className="text-xs text-red-400 flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  Fantasy sports are not available in {state}
                </p>
              )}
            </div>
            
            {/* Beta Invite Code Field */}
            {betaRequired && (
              <div className="space-y-2">
                <Label htmlFor="invite" className="text-slate-200 text-sm flex items-center gap-2">
                  <Ticket className="h-4 w-4" />
                  Invite Code
                  <span className="text-red-400 text-xs">(Required)</span>
                </Label>
                <div className="relative">
                  <Input
                    id="invite"
                    type="text"
                    placeholder="BETA01"
                    value={inviteCode}
                    onChange={(e) => {
                      const code = e.target.value.toUpperCase().replace(/\s/g, '');
                      setInviteCode(code);
                      if (code.length >= 5) {
                        validateInviteCode(code);
                      } else {
                        setInviteValid(null);
                      }
                    }}
                    className={`bg-slate-800 border-slate-700 text-white pr-10 h-11 ${
                      inviteValid === true ? 'border-green-500' : 
                      inviteValid === false ? 'border-red-500' : ''
                    }`}
                    data-testid="invite-code-input"
                  />
                  {inviteChecking && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <div className="h-4 w-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                  )}
                  {!inviteChecking && inviteValid === true && (
                    <CheckCircle className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-green-500" />
                  )}
                  {!inviteChecking && inviteValid === false && (
                    <XCircle className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-red-500" />
                  )}
                </div>
                {inviteValid === false && (
                  <p className="text-xs text-red-400">Invalid or expired invite code</p>
                )}
                {inviteValid === true && (
                  <p className="text-xs text-green-400">Valid invite code!</p>
                )}
              </div>
            )}
            
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
              disabled={loading || (betaRequired && !inviteValid)}
              data-testid="submit-btn"
            >
              {loading ? 'Creating account...' : 'Sign Up & Get 50 Coins'}
            </Button>
          </form>
          <div className="mt-6 text-center text-sm text-slate-400">
            Already have an account?{' '}
            <Link to="/login" className="text-yellow-400 hover:underline font-semibold">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Register;
