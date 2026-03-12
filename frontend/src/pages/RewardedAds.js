import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import { ArrowLeft, Play, Coins, Clock, CheckCircle, Tv, Zap, Shield } from 'lucide-react';

/**
 * Detects if the user is inside the FREE11 Android TWA wrapper.
 * TWA apps add "wv" (WebView) or keep a recognizable UA pattern.
 */
function isAndroidTWA() {
  const ua = navigator.userAgent || '';
  return /Android/i.test(ua) && (/wv\)/.test(ua) || /free11/i.test(ua));
}

/**
 * Builds the intent URI that Android Chrome resolves to open RewardedAdActivity.
 * Passes the JWT token so the Activity can call the backend after the ad completes.
 */
function buildAdIntent(token) {
  const encoded = encodeURIComponent(token || '');
  return `intent://rewarded-ad?token=${encoded}#Intent;scheme=free11;package=com.free11.app;end`;
}

export default function RewardedAds() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, updateUser } = useAuth();
  const [adStatus, setAdStatus] = useState(null);
  const [watching, setWatching] = useState(false);
  const [currentAdId, setCurrentAdId] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef(null);
  const admobCallbackRan = useRef(false);

  const loadStatus = useCallback(async () => {
    try {
      const { data } = await api.v2GetAdStatus();
      setAdStatus(data);
    } catch {}
  }, []);

  useEffect(() => {
    loadStatus();
    return () => clearInterval(timerRef.current);
  }, [loadStatus]);

  // ── Handle return from Android AdMob ad ──────────────────────────────
  useEffect(() => {
    const admobComplete = searchParams.get('admob_complete');
    const admobFailed = searchParams.get('admob_failed');

    if (admobComplete === '1') {
      if (admobCallbackRan.current) return; // React StrictMode guard
      admobCallbackRan.current = true;
      handleAdMobCallback();
    } else if (admobFailed === '1') {
      toast.error('Ad was dismissed early. Watch the full ad to earn coins!');
      navigate('/watch-earn', { replace: true });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAdMobCallback = async () => {
    setLoading(true);
    try {
      const { data } = await api.v2ClaimAdMobReward({ reward_type: 'ad_watch' });
      toast.success(`+${data.reward_coins} Coins earned! Great watch!`);
      // Update navbar balance immediately
      updateUser({ coins_balance: (user?.coins_balance || 0) + data.reward_coins });
      await loadStatus();
    } catch (e) {
      const msg = e.response?.data?.detail || '';
      if (msg.includes('Daily ad limit')) {
        toast.info('Daily ad limit reached (5/day). Come back tomorrow!');
      } else {
        toast.success('Ad reward processed!');
      }
      await loadStatus();
    }
    setLoading(false);
    navigate('/watch-earn', { replace: true });
  };

  // ── Android TWA: trigger native AdMob ad ─────────────────────────────
  const launchAndroidAd = () => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token') || '';
    window.location.href = buildAdIntent(token);
  };

  // ── Web fallback: mock ad simulation ─────────────────────────────────
  const startWatchingWeb = async () => {
    try {
      const { data } = await api.v2StartAd();
      if (data.error) {
        toast.error(data.error === 'daily_limit_reached' ? 'Daily limit reached!' : data.error);
        return;
      }
      setCurrentAdId(data.ad_id);
      setCountdown(data.duration_seconds);
      setWatching(true);

      timerRef.current = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) { clearInterval(timerRef.current); return 0; }
          return prev - 1;
        });
      }, 1000);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to start ad');
    }
  };

  const claimWebReward = async () => {
    try {
      const { data } = await api.v2CompleteAd(currentAdId);
      toast.success(`+${data.reward_coins} Coins earned!`);
      setWatching(false);
      setCurrentAdId(null);
      await loadStatus();
    } catch {
      toast.error('Failed to claim reward');
    }
  };

  const handleWatchButton = () => {
    if (isAndroidTWA()) {
      launchAndroidAd();
    } else {
      startWatchingWeb();
    }
  };

  const onAndroid = isAndroidTWA();
  const rewardCoins = onAndroid ? 20 : (adStatus?.reward_per_ad || 10);
  const canWatch = adStatus?.remaining_today > 0 && !watching;

  return (
    <div className="min-h-screen text-white pb-28 md:pb-6" style={{ background: '#0F1115' }}
      data-testid="rewarded-ads-page">
      <Navbar />
      <div className="max-w-lg mx-auto px-4 pt-4">

        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <button onClick={() => navigate(-1)}
            className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)' }}
            data-testid="back-button">
            <ArrowLeft className="w-4 h-4 text-white" />
          </button>
          <div>
            <h1 className="font-heading text-xl text-white tracking-wide">Watch & Earn</h1>
            <p className="text-xs" style={{ color: '#8A9096' }}>Watch short ads, earn real coins</p>
          </div>
        </div>

        {/* Status Card */}
        {adStatus && (
          <div className="rounded-2xl p-5 mb-4"
            style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.2)' }}
            data-testid="ad-status-card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs mb-1" style={{ color: '#8A9096' }}>Reward per ad</p>
                <div className="flex items-center gap-1.5">
                  <Coins className="w-5 h-5" style={{ color: '#C6A052' }} />
                  <span className="text-3xl font-black font-numbers" style={{ color: '#C6A052' }}>
                    {rewardCoins}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs mb-1" style={{ color: '#8A9096' }}>Today's progress</p>
                <p className="text-2xl font-black font-numbers text-white">
                  {adStatus.watched_today}<span className="text-base font-normal text-gray-500">/{adStatus.daily_limit}</span>
                </p>
                <p className="text-xs mt-0.5" style={{ color: adStatus.remaining_today > 0 ? '#4ade80' : '#8A9096' }}>
                  {adStatus.remaining_today} remaining
                </p>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mt-3 h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <div className="h-1.5 rounded-full transition-all"
                style={{
                  width: `${(adStatus.watched_today / adStatus.daily_limit) * 100}%`,
                  background: 'linear-gradient(90deg, #C6A052, #e8c87a)',
                }} />
            </div>
          </div>
        )}

        {/* Main Ad Player / CTA */}
        <div className="rounded-2xl overflow-hidden mb-4"
          style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
          data-testid="ad-player">

          {watching && !onAndroid ? (
            /* Web mock ad player */
            <div className="p-8 text-center">
              <div className="w-full h-36 rounded-xl flex items-center justify-center mb-5"
                style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.12), rgba(6,78,59,0.2))', border: '1px solid rgba(16,185,129,0.15)' }}>
                <div className="text-center">
                  <Tv className="w-10 h-10 mx-auto mb-2" style={{ color: 'rgba(255,255,255,0.2)' }} />
                  <p className="text-xs" style={{ color: '#8A9096' }}>Simulated Ad (Web Preview)</p>
                </div>
              </div>
              {countdown > 0 ? (
                <div>
                  <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3 relative"
                    style={{ border: '3px solid rgba(16,185,129,0.2)' }}>
                    <svg className="absolute inset-0 w-16 h-16 -rotate-90">
                      <circle cx="32" cy="32" r="28" fill="none" stroke="#10b981" strokeWidth="3"
                        strokeDasharray={`${(1 - countdown / 10) * 176} 176`} />
                    </svg>
                    <span className="text-xl font-black text-emerald-400 font-numbers">{countdown}</span>
                  </div>
                  <p className="text-sm flex items-center justify-center gap-1.5" style={{ color: '#8A9096' }}>
                    <Clock className="w-4 h-4" /> Watching ad...
                  </p>
                </div>
              ) : (
                <button onClick={claimWebReward}
                  className="px-8 py-3 rounded-xl font-bold flex items-center gap-2 mx-auto transition-all active:scale-95"
                  style={{ background: 'linear-gradient(135deg, #C6A052, #d4aa5a)', color: '#0F1115' }}
                  data-testid="claim-reward-btn">
                  <CheckCircle className="w-5 h-5" /> Claim {adStatus?.reward_per_ad || 10} Coins
                </button>
              )}
            </div>
          ) : (
            /* Watch Ad CTA */
            <div className="p-8 text-center">
              <div className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                style={{ background: 'rgba(198,160,82,0.12)', border: '1px solid rgba(198,160,82,0.25)' }}>
                <Play className="w-8 h-8" style={{ color: '#C6A052' }} />
              </div>
              <h3 className="text-lg font-bold mb-1.5 text-white">
                {onAndroid ? 'Watch Ad — Earn 20 Coins' : 'Watch an Ad'}
              </h3>
              <p className="text-sm mb-5" style={{ color: '#8A9096' }}>
                {onAndroid
                  ? 'A short Google ad will play. Earn coins instantly when it completes!'
                  : `Watch a short ad and earn ${adStatus?.reward_per_ad || 10} coins instantly!`
                }
              </p>
              {canWatch ? (
                <button onClick={handleWatchButton} disabled={loading}
                  className="px-8 py-3 rounded-xl font-bold transition-all active:scale-95 disabled:opacity-50"
                  style={{ background: 'linear-gradient(135deg, #C6A052, #d4aa5a)', color: '#0F1115' }}
                  data-testid="watch-ad-btn">
                  {loading ? 'Processing...' : `Watch Ad → Earn ${rewardCoins} Coins`}
                </button>
              ) : (
                <div className="text-sm px-4 py-3 rounded-xl"
                  style={{ background: 'rgba(255,255,255,0.04)', color: '#8A9096' }}>
                  Daily limit reached (5/5). Come back tomorrow!
                </div>
              )}
            </div>
          )}
        </div>

        {/* Info tiles */}
        <div className="grid grid-cols-3 gap-2">
          {[
            { icon: Zap, label: 'Instant', desc: 'Coins credited right away' },
            { icon: Shield, label: 'Safe', desc: 'Google-verified ads only' },
            { icon: Coins, label: '5x / day', desc: 'Up to 100 coins daily' },
          ].map(({ icon: Icon, label, desc }) => (
            <div key={label} className="rounded-xl p-3 text-center"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <Icon className="w-4 h-4 mx-auto mb-1.5" style={{ color: '#C6A052' }} />
              <p className="text-xs font-bold text-white">{label}</p>
              <p className="text-[10px] mt-0.5" style={{ color: '#8A9096' }}>{desc}</p>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
