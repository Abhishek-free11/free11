import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import Navbar from '../components/Navbar';
import { Trophy, Target, Flame, Crown, Users, TrendingUp, Swords, Calendar, Award, ChevronRight, Share2 } from 'lucide-react';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { toast } from 'sonner';
import api from '../utils/api';
import ShareCard from '../components/ShareCard';
import { AnimatePresence } from 'framer-motion';

const Leaderboards = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useI18n();
  const [globalLeaderboard, setGlobalLeaderboard] = useState([]);
  const [weeklyLeaderboard, setWeeklyLeaderboard] = useState([]);
  const [streakLeaderboard, setStreakLeaderboard] = useState([]);
  const [myDuels, setMyDuels] = useState(null);
  const [activityFeed, setActivityFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [activeTab, setActiveTab] = useState('global');
  const [showShareCard, setShowShareCard] = useState(false);
  const [shareCardData, setShareCardData] = useState({});

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [globalRes, weeklyRes, streakRes, duelsRes, feedRes] = await Promise.all([
        api.getGlobalLeaderboard(50),
        api.getWeeklyLeaderboard(50),
        api.getStreakLeaderboard(50),
        api.getMyDuels(),
        api.getActivityFeed()
      ]);
      setGlobalLeaderboard(globalRes.data?.leaderboard || []);
      setWeeklyLeaderboard(weeklyRes.data?.leaderboard || []);
      setStreakLeaderboard(streakRes.data?.leaderboard || []);
      setMyDuels(duelsRes.data);
      setActivityFeed(feedRes.data?.activities || []);
    } catch {}
    finally { setLoading(false); }
  };

  const viewProfile = async (userId) => {
    try {
      const response = await api.getPublicProfile(userId);
      setSelectedProfile(response.data);
    } catch { toast.error('Failed to load profile'); }
  };

  const handleChallenge = async (userId) => {
    try {
      await api.createDuel(userId);
      toast.success('Duel challenge sent!');
      fetchData();
    } catch (error) { toast.error(error.response?.data?.detail || 'Failed'); }
  };

  const handleAcceptDuel = async (duelId) => {
    try { await api.acceptDuel(duelId); toast.success('Duel accepted!'); fetchData(); } catch (error) { toast.error('Failed'); }
  };

  const handleDeclineDuel = async (duelId) => {
    try { await api.declineDuel(duelId); toast.info('Declined'); fetchData(); } catch {}
  };

  const TABS = [
    { key: 'global', label: t('leaderboard_page.global_tab'), icon: Trophy },
    { key: 'weekly', label: t('leaderboard_page.weekly_tab'), icon: Calendar },
    { key: 'streak', label: t('leaderboard_page.streak_tab'), icon: Flame },
  ];

  const currentList = activeTab === 'global' ? globalLeaderboard : activeTab === 'weekly' ? weeklyLeaderboard : streakLeaderboard;

  const rankStyle = (rank) => {
    if (rank === 1) return { background: 'linear-gradient(135deg,#C6A052,#E0B84F)', color: '#0F1115' };
    if (rank === 2) return { background: '#BFC3C8', color: '#0F1115' };
    if (rank === 3) return { background: '#CD7F32', color: '#fff' };
    return { background: 'rgba(255,255,255,0.06)', color: '#8A9096' };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F1115] pb-28 md:pb-6">
        <Navbar />
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 rounded-full border-2 animate-spin" style={{ borderColor: '#C6A052', borderTopColor: 'transparent' }} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F1115] pb-28 md:pb-6" data-testid="leaderboards-page">
      <div className="fixed pointer-events-none" style={{ top: 0, left: '50%', transform: 'translateX(-50%)', width: '70vw', height: '30vh', background: 'radial-gradient(ellipse, rgba(198,160,82,0.04) 0%, transparent 70%)', zIndex: 0 }} />
      <Navbar />

      <div className="relative z-10 max-w-screen-xl mx-auto px-3 sm:px-4 py-4 space-y-4 animate-slide-up">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Trophy className="h-7 w-7 sm:h-9 sm:w-9" style={{ color: '#C6A052' }} />
          <div>
            <h1 className="font-heading text-2xl sm:text-4xl tracking-widest text-white">{t('leaderboard_page.title')}</h1>
            <p className="text-xs sm:text-sm" style={{ color: '#8A9096' }}>{t('leaderboard_page.subtitle')}</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-4">
          {/* Main leaderboard */}
          <div className="lg:col-span-2 space-y-3">
            {/* Tab bar */}
            <div className="flex gap-2">
              {TABS.map(({ key, label, icon: Icon }) => (
                <button key={key} onClick={() => setActiveTab(key)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-heading tracking-wider transition-all"
                  style={activeTab === key
                    ? { background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115', fontWeight: 700 }
                    : { background: 'rgba(255,255,255,0.04)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.06)' }}>
                  <Icon className="h-3.5 w-3.5" />
                  <span>{label}</span>
                </button>
              ))}
            </div>

            {/* Rows */}
            <div className="card-broadcast overflow-hidden">
              {currentList.length === 0 ? (
                <div className="text-center py-16">
                  <Trophy className="h-12 w-12 mx-auto mb-3" style={{ color: '#2A2D33' }} />
                  <p className="text-sm" style={{ color: '#8A9096' }}>No entries yet</p>
                </div>
              ) : (
                <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                  {currentList.map((entry) => (
                    <div key={entry.id} onClick={() => viewProfile(entry.id)}
                      className="flex items-center justify-between px-4 py-3 cursor-pointer transition-colors hover:bg-white/3"
                      style={entry.rank <= 3 ? { background: entry.rank === 1 ? 'rgba(198,160,82,0.06)' : 'transparent' } : {}}
                      data-testid={`leaderboard-row-${entry.id}`}>
                      {/* Rank */}
                      <div className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-sm font-black mr-3"
                        style={rankStyle(entry.rank)}>
                        {entry.rank === 1 ? <Crown className="h-4 w-4" /> : entry.rank}
                      </div>
                      {/* Name */}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-white truncate">{entry.name}</p>
                        <p className="text-[10px]" style={{ color: entry.rank_color || '#8A9096' }}>
                          {entry.rank_name || `Level ${entry.level}`}
                        </p>
                      </div>
                      {/* Score */}
                      <div className="text-right ml-3">
                        {activeTab === 'streak' ? (
                          <div className="flex items-center gap-1">
                            <Flame className="h-5 w-5 text-orange-400" />
                            <span className="text-2xl font-numbers font-black text-orange-400">{entry.streak}</span>
                          </div>
                        ) : (
                          <>
                            <p className="text-xl font-numbers font-black" style={{ color: '#4ade80' }}>{entry.accuracy}%</p>
                            <p className="text-[10px] hidden sm:block" style={{ color: '#8A9096' }}>
                              {entry.correct_predictions || entry.correct_this_week || 0}/{entry.total_predictions || entry.predictions_this_week || 0}
                            </p>
                          </>
                        )}
                      </div>
                      {entry.id !== user?.id && (
                        <button onClick={(e) => { e.stopPropagation(); handleChallenge(entry.id); }}
                          className="ml-3 p-2 rounded-lg transition-colors hidden sm:flex"
                          style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}
                          data-testid={`challenge-btn-${entry.id}`}>
                          <Swords className="h-4 w-4" />
                        </button>
                      )}
                      {entry.rank <= 3 && (
                        <button
                          onClick={(e) => { e.stopPropagation(); setShareCardData({ rank: entry.rank, accuracy: entry.accuracy }); setShowShareCard(true); }}
                          className="ml-2 p-2 rounded-lg transition-colors"
                          style={{ background: 'rgba(198,160,82,0.1)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.2)' }}
                          data-testid={`share-rank-${entry.rank}`}
                        >
                          <Share2 className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-4">
            {/* Duels */}
            <div className="card-broadcast p-4" data-testid="duels-section">
              <h3 className="font-medium text-white mb-3 flex items-center gap-2">
                <Swords className="h-4 w-4 text-red-400" /> {t('leaderboard_page.duels_title')}
              </h3>
              {myDuels?.stats && (
                <div className="grid grid-cols-3 gap-2 mb-3">
                  {[
                    { label: t('leaderboard_page.won'), value: myDuels.stats.won, color: '#4ade80' },
                    { label: t('leaderboard_page.played'), value: myDuels.stats.played, color: '#60a5fa' },
                    { label: t('leaderboard_page.win_rate'), value: `${myDuels.stats.win_rate}%`, color: '#C6A052' },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="text-center p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                      <p className="text-lg font-numbers font-black" style={{ color }}>{value}</p>
                      <p className="text-[10px]" style={{ color: '#8A9096' }}>{label}</p>
                    </div>
                  ))}
                </div>
              )}
              {myDuels?.pending?.filter(d => d.challenged_id === user?.id).map((duel) => (
                <div key={duel.id} className="p-3 rounded-xl mb-2" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
                  <p className="text-white text-sm font-medium">{duel.challenger_name} challenged you!</p>
                  <div className="flex gap-2 mt-2">
                    <button onClick={() => handleAcceptDuel(duel.id)} className="btn-gold px-3 h-8 rounded-lg text-xs flex-1"
                      data-testid={`accept-duel-${duel.id}`}>Accept</button>
                    <button onClick={() => handleDeclineDuel(duel.id)} className="btn-outline-gold px-3 h-8 rounded-lg text-xs flex-1">Decline</button>
                  </div>
                </div>
              ))}
              {myDuels?.active?.map((duel) => (
                <div key={duel.id} className="p-3 rounded-xl mb-2" style={{ background: 'rgba(96,165,250,0.08)', border: '1px solid rgba(96,165,250,0.2)' }}>
                  <p className="text-white text-sm font-medium">vs {duel.challenger_id === user?.id ? duel.challenged_name : duel.challenger_name}</p>
                  <div className="flex justify-between text-xs mt-1" style={{ color: '#8A9096' }}>
                    <span>You: {duel.challenger_id === user?.id ? duel.challenger_correct : duel.challenged_correct}/{duel.challenger_id === user?.id ? duel.challenger_predictions : duel.challenged_predictions}</span>
                    <span>Them: {duel.challenger_id === user?.id ? duel.challenged_correct : duel.challenger_correct}/{duel.challenger_id === user?.id ? duel.challenged_predictions : duel.challenger_predictions}</span>
                  </div>
                </div>
              ))}
              {(!myDuels?.pending?.length && !myDuels?.active?.length) && (
                <div className="text-center py-4">
                  <Swords className="h-8 w-8 mx-auto mb-2" style={{ color: '#2A2D33' }} />
                  <p className="text-sm" style={{ color: '#8A9096' }}>{t('leaderboard_page.no_duels')}</p>
                </div>
              )}
            </div>

            {/* Activity feed */}
            <div className="card-broadcast p-4" data-testid="activity-feed">
              <h3 className="font-medium text-white mb-3 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-400" /> {t('leaderboard_page.activity_title')}
              </h3>
              {activityFeed.length === 0 ? (
                <p className="text-sm text-center py-3" style={{ color: '#8A9096' }}>{t('leaderboard_page.no_activity')}</p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {activityFeed.map((activity, idx) => (
                    <div key={idx} className="p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.03)' }}>
                      <p className="text-sm text-white font-medium">{activity.title}</p>
                      <p className="text-xs" style={{ color: '#8A9096' }}>{activity.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showShareCard && (
          <ShareCard
            type="leaderboard"
            data={shareCardData}
            onClose={() => setShowShareCard(false)}
          />
        )}
      </AnimatePresence>

      {/* Profile Dialog */}
      <Dialog open={!!selectedProfile} onOpenChange={() => setSelectedProfile(null)}>
        <DialogContent className="max-w-sm mx-4" style={{ background: '#1B1E23', border: '1px solid rgba(198,160,82,0.2)' }}>
          {selectedProfile && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <Avatar className="h-14 w-14">
                    <AvatarFallback className="text-xl font-black"
                      style={{ background: `linear-gradient(135deg,${selectedProfile.rank?.color || '#C6A052'},${selectedProfile.rank?.color || '#E0B84F'})`, color: '#0F1115' }}>
                      {selectedProfile.name?.[0]?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <DialogTitle className="text-white">{selectedProfile.name}</DialogTitle>
                    <span className="text-xs px-2 py-0.5 rounded-full"
                      style={{ background: `${selectedProfile.rank?.color || '#C6A052'}20`, color: selectedProfile.rank?.color || '#C6A052', border: `1px solid ${selectedProfile.rank?.color || '#C6A052'}40` }}>
                      Lv {selectedProfile.level} — {selectedProfile.rank?.name}
                    </span>
                  </div>
                </div>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-2 py-2">
                {[
                  { label: 'Accuracy', value: `${selectedProfile.skill_stats?.accuracy}%`, color: '#4ade80' },
                  { label: 'Streak', value: selectedProfile.skill_stats?.current_streak, color: 'text-orange-400' },
                  { label: 'Predictions', value: selectedProfile.skill_stats?.total_predictions, color: '#60a5fa' },
                  { label: 'Duel W/R', value: `${selectedProfile.duel_stats?.win_rate}%`, color: '#C6A052' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="text-center p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
                    <p className="text-2xl font-numbers font-black" style={{ color }}>{value}</p>
                    <p className="text-xs" style={{ color: '#8A9096' }}>{label}</p>
                  </div>
                ))}
              </div>
              <DialogFooter>
                {selectedProfile.id !== user?.id && (
                  <button className="w-full btn-gold h-10 rounded-xl text-sm"
                    onClick={() => { handleChallenge(selectedProfile.id); setSelectedProfile(null); }}>
                    <Swords className="h-4 w-4 inline mr-2" /> {t('leaderboard_page.challenge_btn')}
                  </button>
                )}
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Leaderboards;
