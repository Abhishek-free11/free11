import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  UserPlus, Gift, Copy, Share2, Check, Users, 
  Coins, ChevronRight, MessageCircle, Send
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const InviteFriends = () => {
  const { user } = useAuth();
  const [inviteStats, setInviteStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  // Generate user's unique referral link
  const baseUrl = window.location.origin;
  const referralCode = user?.id?.substring(0, 8)?.toUpperCase() || 'FREE11';
  const referralLink = `${baseUrl}/register?ref=${referralCode}`;
  
  // Invite message
  const inviteMessage = `🎯 Join FREE11 - India's first Consumption OS!

Make cricket predictions, earn coins, get REAL products!

✅ No money needed - 100% free
✅ Real vouchers & products
✅ Fun mini-games

Join using my link and we BOTH get bonus coins! 🪙

${referralLink}`;

  useEffect(() => {
    fetchInviteStats();
  }, []);

  const fetchInviteStats = async () => {
    try {
      // This would fetch user's referral stats in production
      // For now, using placeholder data
      setInviteStats({
        totalInvites: 0,
        successfulInvites: 0,
        coinsEarned: 0,
        pendingRewards: 0
      });
    } catch (error) {
      console.error('Failed to fetch invite stats:', error);
    } finally {
      setLoading(false);
    }
  };

  // Copy referral link
  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(referralLink);
      setCopied(true);
      toast.success('Referral link copied!');
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error('Failed to copy link');
    }
  };

  // Share via WhatsApp
  const shareViaWhatsApp = () => {
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(inviteMessage)}`;
    window.open(whatsappUrl, '_blank');
  };

  // Share via Telegram
  const shareViaTelegram = () => {
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(referralLink)}&text=${encodeURIComponent(inviteMessage)}`;
    window.open(telegramUrl, '_blank');
  };

  // Share via native share API
  const shareNative = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Join FREE11 - Get Free Products!',
          text: inviteMessage,
          url: referralLink
        });
        toast.success('Shared successfully!');
      } catch (err) {
        if (err.name !== 'AbortError') {
          copyLink(); // Fallback to copy
        }
      }
    } else {
      copyLink(); // Fallback to copy
    }
  };

  // Share via SMS
  const shareViaSMS = () => {
    const smsUrl = `sms:?body=${encodeURIComponent(inviteMessage)}`;
    window.location.href = smsUrl;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800 pb-28 md:pb-4">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 px-4 py-8">
        <div className="max-w-lg mx-auto text-center">
          <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <UserPlus className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Invite Friends</h1>
          <p className="text-green-100">Share FREE11 and earn rewards together!</p>
        </div>
      </div>

      <div className="max-w-lg mx-auto px-4 -mt-4">
        {/* Referral Rewards Card */}
        <Card className="bg-gradient-to-br from-yellow-500/20 to-amber-500/10 border-yellow-500/30 mb-6">
          <CardContent className="p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-yellow-500/20 rounded-xl flex items-center justify-center">
                <Gift className="h-6 w-6 text-yellow-400" />
              </div>
              <div>
                <h3 className="font-bold text-white">Referral Rewards</h3>
                <p className="text-sm text-slate-300">Both you and your friend get coins!</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-yellow-400">50</p>
                <p className="text-xs text-slate-400">You Earn</p>
              </div>
              <div className="bg-slate-800/50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-green-400">50</p>
                <p className="text-xs text-slate-400">Friend Gets</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Your Referral Link */}
        <Card className="bg-slate-800/50 border-slate-700 mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-white flex items-center gap-2">
              <Share2 className="h-5 w-5 text-blue-400" />
              Your Referral Link
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mb-4">
              <Input
                value={referralLink}
                readOnly
                className="bg-slate-900/50 border-slate-600 text-white font-mono text-sm"
                data-testid="referral-link-input"
              />
              <Button
                onClick={copyLink}
                variant="outline"
                className={`border-slate-600 min-w-[44px] ${copied ? 'bg-green-500/20 border-green-500' : ''}`}
                data-testid="copy-referral-btn"
              >
                {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
            
            <p className="text-xs text-slate-400 mb-4">
              Your unique code: <span className="font-mono font-bold text-yellow-400">{referralCode}</span>
            </p>
          </CardContent>
        </Card>

        {/* Share Options */}
        <Card className="bg-slate-800/50 border-slate-700 mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-white">Share Via</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {/* WhatsApp - Primary */}
            <Button
              onClick={shareViaWhatsApp}
              className="w-full h-14 bg-green-600 hover:bg-green-700 justify-start gap-4"
              data-testid="share-whatsapp-btn"
            >
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                </svg>
              </div>
              <div className="text-left flex-1">
                <p className="font-bold">WhatsApp</p>
                <p className="text-xs text-green-200">Share with contacts</p>
              </div>
              <ChevronRight className="h-5 w-5 opacity-50" />
            </Button>

            {/* Telegram */}
            <Button
              onClick={shareViaTelegram}
              className="w-full h-14 bg-blue-500 hover:bg-blue-600 justify-start gap-4"
              data-testid="share-telegram-btn"
            >
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                <Send className="h-5 w-5" />
              </div>
              <div className="text-left flex-1">
                <p className="font-bold">Telegram</p>
                <p className="text-xs text-blue-200">Share with friends</p>
              </div>
              <ChevronRight className="h-5 w-5 opacity-50" />
            </Button>

            {/* SMS */}
            <Button
              onClick={shareViaSMS}
              className="w-full h-14 bg-slate-600 hover:bg-slate-500 justify-start gap-4"
              data-testid="share-sms-btn"
            >
              <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                <MessageCircle className="h-5 w-5" />
              </div>
              <div className="text-left flex-1">
                <p className="font-bold">SMS</p>
                <p className="text-xs text-slate-300">Send text message</p>
              </div>
              <ChevronRight className="h-5 w-5 opacity-50" />
            </Button>

            {/* More Options */}
            <Button
              onClick={shareNative}
              variant="outline"
              className="w-full h-14 border-slate-600 justify-start gap-4"
              data-testid="share-more-btn"
            >
              <div className="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center">
                <Share2 className="h-5 w-5 text-slate-300" />
              </div>
              <div className="text-left flex-1">
                <p className="font-bold text-white">More Options</p>
                <p className="text-xs text-slate-400">Other apps</p>
              </div>
              <ChevronRight className="h-5 w-5 opacity-50" />
            </Button>
          </CardContent>
        </Card>

        {/* Stats Card */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg text-white flex items-center gap-2">
              <Users className="h-5 w-5 text-purple-400" />
              Your Referral Stats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-900/50 rounded-lg p-4 text-center">
                <p className="text-3xl font-bold text-white">{inviteStats?.successfulInvites || 0}</p>
                <p className="text-xs text-slate-400">Friends Joined</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4 text-center">
                <div className="flex items-center justify-center gap-1">
                  <Coins className="h-5 w-5 text-yellow-400" />
                  <p className="text-3xl font-bold text-yellow-400">{inviteStats?.coinsEarned || 0}</p>
                </div>
                <p className="text-xs text-slate-400">Coins Earned</p>
              </div>
            </div>
            
            {inviteStats?.pendingRewards > 0 && (
              <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <p className="text-sm text-yellow-400">
                  🎉 {inviteStats.pendingRewards} pending referral rewards!
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* How It Works */}
        <div className="mt-6 p-4">
          <h3 className="text-sm font-bold text-white mb-4">How It Works</h3>
          <div className="space-y-3">
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-yellow-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-yellow-400 font-bold text-sm">1</span>
              </div>
              <div>
                <p className="text-sm text-white font-medium">Share your link</p>
                <p className="text-xs text-slate-400">Send via WhatsApp, SMS, or any app</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-green-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-green-400 font-bold text-sm">2</span>
              </div>
              <div>
                <p className="text-sm text-white font-medium">Friend joins FREE11</p>
                <p className="text-xs text-slate-400">They sign up using your referral link</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <span className="text-purple-400 font-bold text-sm">3</span>
              </div>
              <div>
                <p className="text-sm text-white font-medium">Both earn coins!</p>
                <p className="text-xs text-slate-400">You get 50 coins, friend gets 50 coins</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InviteFriends;
