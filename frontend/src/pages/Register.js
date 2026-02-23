import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Coins, Ticket, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

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
    
    if (betaRequired && !inviteValid) {
      toast.error('Valid invite code required for beta access');
      return;
    }
    
    setLoading(true);

    try {
      await register(email, name, password, inviteCode || null);
      toast.success('🎉 Welcome! You got 50 FREE coins!');
      navigate('/');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-slate-900/50 border-slate-800" data-testid="register-card">
        <CardHeader className="space-y-4 text-center">
          <div className="flex items-center justify-center gap-3">
            <img 
              src="/app-icon.png" 
              alt="FREE11" 
              className="h-16 w-16 rounded-xl"
            />
          </div>
          <CardTitle className="text-2xl text-white">Join FREE11</CardTitle>
          <CardDescription className="text-slate-400">Create your account and get 50 welcome coins</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-slate-200">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="Your Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="bg-slate-800 border-slate-700 text-white"
                data-testid="name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-200">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="bg-slate-800 border-slate-700 text-white"
                data-testid="email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-200">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                className="bg-slate-800 border-slate-700 text-white"
                data-testid="password-input"
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
              disabled={loading}
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
