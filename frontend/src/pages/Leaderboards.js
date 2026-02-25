import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { 
  Trophy, Target, Flame, Crown, Medal, 
  Users, TrendingUp, Swords, Calendar, Award,
  ChevronRight, Eye
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const Leaderboards = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [globalLeaderboard, setGlobalLeaderboard] = useState([]);
  const [weeklyLeaderboard, setWeeklyLeaderboard] = useState([]);
  const [streakLeaderboard, setStreakLeaderboard] = useState([]);
  const [myDuels, setMyDuels] = useState(null);
  const [activityFeed, setActivityFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [profileDialogOpen, setProfileDialogOpen] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

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
    } catch (error) {
      console.error('Error fetching leaderboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewProfile = async (userId) => {
    try {
      const response = await api.getPublicProfile(userId);
      setSelectedProfile(response.data);
      setProfileDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load profile');
    }
  };

  const handleChallenge = async (userId) => {
    try {
      await api.createDuel(userId);
      toast.success('Duel challenge sent!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send challenge');
    }
  };

  const handleAcceptDuel = async (duelId) => {
    try {
      await api.acceptDuel(duelId);
      toast.success('Duel accepted! Game on!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to accept duel');
    }
  };

  const handleDeclineDuel = async (duelId) => {
    try {
      await api.declineDuel(duelId);
      toast.info('Duel declined');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to decline duel');
    }
  };

  const getRankBadge = (rank) => {
    if (rank === 1) return <Crown className="h-5 w-5 text-yellow-400" />;
    if (rank === 2) return <Medal className="h-5 w-5 text-slate-300" />;
    if (rank === 3) return <Medal className="h-5 w-5 text-amber-600" />;
    return null;
  };

  const LeaderboardRow = ({ entry, showChallenge = true }) => (
    <div 
      className={`flex items-center justify-between p-4 rounded-lg transition-colors cursor-pointer hover:bg-slate-800 ${
        entry.rank === 1 ? 'bg-yellow-500/10 border border-yellow-500/30' :
        entry.rank === 2 ? 'bg-slate-400/10 border border-slate-400/30' :
        entry.rank === 3 ? 'bg-amber-700/10 border border-amber-700/30' :
        'bg-slate-800/50'
      }`}
      onClick={() => viewProfile(entry.id)}
      data-testid={`leaderboard-row-${entry.id}`}
    >
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
          entry.rank === 1 ? 'bg-yellow-500 text-black' :
          entry.rank === 2 ? 'bg-slate-400 text-black' :
          entry.rank === 3 ? 'bg-amber-700 text-white' :
          'bg-slate-700 text-slate-300'
        }`}>
          {getRankBadge(entry.rank) || entry.rank}
        </div>
        <Avatar>
          <AvatarFallback 
            className="text-white font-bold"
            style={{ backgroundColor: entry.rank_color || '#64748b' }}
          >
            {entry.name?.[0]?.toUpperCase() || '?'}
          </AvatarFallback>
        </Avatar>
        <div>
          <p className="text-white font-bold">{entry.name}</p>
          <div className="flex items-center gap-2">
            <Badge 
              className="text-xs"
              style={{ 
                backgroundColor: `${entry.rank_color}20` || '#64748b20',
                color: entry.rank_color || '#94a3b8',
                border: `1px solid ${entry.rank_color}50` || '#64748b50'
              }}
            >
              {entry.rank_name || `Level ${entry.level}`}
            </Badge>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-2xl font-bold text-green-400">{entry.accuracy}%</p>
          <p className="text-xs text-slate-400">
            {entry.correct_predictions || entry.correct_this_week || 0}/{entry.total_predictions || entry.predictions_this_week || 0} correct
          </p>
        </div>
        {showChallenge && entry.id !== user?.id && (
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => {
              e.stopPropagation();
              handleChallenge(entry.id);
            }}
            className="border-red-500/50 text-red-400 hover:bg-red-500/10"
            data-testid={`challenge-btn-${entry.id}`}
          >
            <Swords className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 pb-20 md:pb-0 via-slate-900 to-slate-950">
        <Navbar />
        <div className="container mx-auto px-4 py-20 text-center">
          <div className="animate-spin h-12 w-12 border-4 border-yellow-400 border-t-transparent rounded-full mx-auto"></div>
          <p className="text-slate-400 mt-4">Loading leaderboards...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 pb-20 md:pb-0 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl" data-testid="leaderboards-page">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-black text-white mb-2 flex items-center gap-3">
            <Trophy className="h-10 w-10 text-yellow-400" />
            Leaderboards
          </h1>
          <p className="text-slate-400">Compete on SKILL - accuracy and streaks matter, not coins!</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Leaderboard Section */}
          <div className="lg:col-span-2">
            <Tabs defaultValue="global" className="space-y-6">
              <TabsList className="bg-slate-800/50 border border-slate-700">
                <TabsTrigger value="global" className="data-[state=active]:bg-yellow-500 data-[state=active]:text-black">
                  <Trophy className="h-4 w-4 mr-2" />
                  Global
                </TabsTrigger>
                <TabsTrigger value="weekly" className="data-[state=active]:bg-blue-500">
                  <Calendar className="h-4 w-4 mr-2" />
                  Weekly
                </TabsTrigger>
                <TabsTrigger value="streak" className="data-[state=active]:bg-red-500">
                  <Flame className="h-4 w-4 mr-2" />
                  Streaks
                </TabsTrigger>
              </TabsList>

              {/* Global Leaderboard */}
              <TabsContent value="global">
                <Card className="bg-slate-800/80 border-slate-800">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Trophy className="h-5 w-5 text-yellow-400" />
                      Global Rankings
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      All-time prediction accuracy (min. 5 predictions to qualify)
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-[600px] overflow-y-auto">
                      {globalLeaderboard.length === 0 ? (
                        <div className="text-center py-12">
                          <Trophy className="h-16 w-16 text-slate-700 mx-auto mb-4" />
                          <p className="text-slate-400">No rankings yet. Make predictions to climb the board!</p>
                        </div>
                      ) : (
                        globalLeaderboard.map((entry) => (
                          <LeaderboardRow key={entry.id} entry={entry} />
                        ))
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Weekly Leaderboard */}
              <TabsContent value="weekly">
                <Card className="bg-slate-800/80 border-slate-800">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Calendar className="h-5 w-5 text-blue-400" />
                      Weekly Rankings
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      This week's top predictors (resets every Monday)
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-[600px] overflow-y-auto">
                      {weeklyLeaderboard.length === 0 ? (
                        <div className="text-center py-12">
                          <Calendar className="h-16 w-16 text-slate-700 mx-auto mb-4" />
                          <p className="text-slate-400">No predictions this week yet. Be the first!</p>
                        </div>
                      ) : (
                        weeklyLeaderboard.map((entry) => (
                          <LeaderboardRow key={entry.id} entry={entry} />
                        ))
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Streak Leaderboard */}
              <TabsContent value="streak">
                <Card className="bg-slate-800/80 border-slate-800">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <Flame className="h-5 w-5 text-red-400" />
                      Streak Kings
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      Longest consecutive correct predictions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-[600px] overflow-y-auto">
                      {streakLeaderboard.length === 0 ? (
                        <div className="text-center py-12">
                          <Flame className="h-16 w-16 text-slate-700 mx-auto mb-4" />
                          <p className="text-slate-400">No streaks yet. Start predicting!</p>
                        </div>
                      ) : (
                        streakLeaderboard.map((entry) => (
                          <div 
                            key={entry.id}
                            className={`flex items-center justify-between p-4 rounded-lg cursor-pointer hover:bg-slate-800 ${
                              entry.rank <= 3 ? 'bg-red-500/10 border border-red-500/30' : 'bg-slate-800/50'
                            }`}
                            onClick={() => viewProfile(entry.id)}
                          >
                            <div className="flex items-center gap-4">
                              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                                entry.rank === 1 ? 'bg-red-500 text-white' :
                                entry.rank === 2 ? 'bg-orange-500 text-white' :
                                entry.rank === 3 ? 'bg-yellow-500 text-black' :
                                'bg-slate-700 text-slate-300'
                              }`}>
                                {entry.rank}
                              </div>
                              <div>
                                <p className="text-white font-bold">{entry.name}</p>
                                <Badge className="text-xs bg-slate-700 text-slate-300">
                                  {entry.rank_name}
                                </Badge>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Flame className="h-6 w-6 text-red-400" />
                              <span className="text-3xl font-black text-red-400">{entry.streak}</span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar - Duels & Activity */}
          <div className="space-y-6">
            {/* My Duels */}
            <Card className="bg-slate-800/80 border-slate-800" data-testid="duels-section">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Swords className="h-5 w-5 text-red-400" />
                  Prediction Duels
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Challenge friends - winner gets badges!
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Duel Stats */}
                {myDuels?.stats && (
                  <div className="grid grid-cols-3 gap-2 mb-4 p-3 bg-slate-800/50 rounded-lg">
                    <div className="text-center">
                      <p className="text-xl font-bold text-green-400">{myDuels.stats.won}</p>
                      <p className="text-xs text-slate-400">Won</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold text-blue-400">{myDuels.stats.played}</p>
                      <p className="text-xs text-slate-400">Played</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold text-yellow-400">{myDuels.stats.win_rate}%</p>
                      <p className="text-xs text-slate-400">Win Rate</p>
                    </div>
                  </div>
                )}

                {/* Pending Duels */}
                {myDuels?.pending?.length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm text-slate-400 mb-2">Incoming Challenges</p>
                    {myDuels.pending
                      .filter(d => d.challenged_id === user?.id)
                      .map((duel) => (
                      <div key={duel.id} className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg mb-2">
                        <p className="text-white font-medium">{duel.challenger_name} challenged you!</p>
                        <div className="flex gap-2 mt-2">
                          <Button 
                            size="sm" 
                            className="bg-green-500 hover:bg-green-600"
                            onClick={() => handleAcceptDuel(duel.id)}
                            data-testid={`accept-duel-${duel.id}`}
                          >
                            Accept
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline"
                            className="border-slate-600"
                            onClick={() => handleDeclineDuel(duel.id)}
                          >
                            Decline
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Active Duels */}
                {myDuels?.active?.length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm text-slate-400 mb-2">Active Duels</p>
                    {myDuels.active.map((duel) => (
                      <div key={duel.id} className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg mb-2">
                        <p className="text-white font-medium">
                          vs {duel.challenger_id === user?.id ? duel.challenged_name : duel.challenger_name}
                        </p>
                        <div className="flex justify-between text-sm mt-2">
                          <span className="text-slate-400">
                            You: {duel.challenger_id === user?.id ? duel.challenger_correct : duel.challenged_correct}/
                            {duel.challenger_id === user?.id ? duel.challenger_predictions : duel.challenged_predictions}
                          </span>
                          <span className="text-slate-400">
                            Them: {duel.challenger_id === user?.id ? duel.challenged_correct : duel.challenger_correct}/
                            {duel.challenger_id === user?.id ? duel.challenged_predictions : duel.challenger_predictions}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {(!myDuels?.pending?.length && !myDuels?.active?.length) && (
                  <div className="text-center py-4">
                    <Swords className="h-10 w-10 text-slate-700 mx-auto mb-2" />
                    <p className="text-slate-400 text-sm">No active duels. Challenge someone!</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Activity Feed */}
            <Card className="bg-slate-800/80 border-slate-800" data-testid="activity-feed">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  Activity Feed
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {activityFeed.length === 0 ? (
                    <div className="text-center py-4">
                      <TrendingUp className="h-10 w-10 text-slate-700 mx-auto mb-2" />
                      <p className="text-slate-400 text-sm">No recent activity</p>
                    </div>
                  ) : (
                    activityFeed.map((activity, idx) => (
                      <div key={idx} className="p-3 bg-slate-800/50 rounded-lg">
                        <p className="text-white text-sm font-medium">{activity.title}</p>
                        <p className="text-slate-400 text-xs">{activity.description}</p>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Profile Dialog */}
      <Dialog open={profileDialogOpen} onOpenChange={setProfileDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-800 max-w-md">
          {selectedProfile && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-4">
                  <Avatar className="h-16 w-16">
                    <AvatarFallback 
                      className="text-2xl font-bold"
                      style={{ backgroundColor: selectedProfile.rank?.color || '#64748b' }}
                    >
                      {selectedProfile.name?.[0]?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <DialogTitle className="text-white text-xl">{selectedProfile.name}</DialogTitle>
                    <Badge 
                      style={{ 
                        backgroundColor: `${selectedProfile.rank?.color}20`,
                        color: selectedProfile.rank?.color,
                        border: `1px solid ${selectedProfile.rank?.color}50`
                      }}
                    >
                      Level {selectedProfile.level} - {selectedProfile.rank?.name}
                    </Badge>
                  </div>
                </div>
              </DialogHeader>
              
              <div className="space-y-4 py-4">
                {/* Skill Stats */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-green-400">{selectedProfile.skill_stats?.accuracy}%</p>
                    <p className="text-xs text-slate-400">Accuracy</p>
                  </div>
                  <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-red-400">{selectedProfile.skill_stats?.current_streak}</p>
                    <p className="text-xs text-slate-400">Current Streak</p>
                  </div>
                  <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-400">{selectedProfile.skill_stats?.total_predictions}</p>
                    <p className="text-xs text-slate-400">Predictions</p>
                  </div>
                  <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-400">{selectedProfile.duel_stats?.win_rate}%</p>
                    <p className="text-xs text-slate-400">Duel Win Rate</p>
                  </div>
                </div>

                {/* Clan */}
                {selectedProfile.clan && (
                  <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <p className="text-sm text-slate-400">Clan</p>
                    <p className="text-white font-bold">
                      {selectedProfile.clan.logo} [{selectedProfile.clan.tag}] {selectedProfile.clan.name}
                    </p>
                  </div>
                )}

                {/* Badges */}
                {selectedProfile.badges?.length > 0 && (
                  <div>
                    <p className="text-sm text-slate-400 mb-2">Badges</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedProfile.badges.map((badge) => (
                        <Badge key={badge} className="bg-yellow-500/20 text-yellow-400 border-yellow-500/50">
                          {badge.replace(/_/g, ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <DialogFooter>
                {selectedProfile.id !== user?.id && (
                  <Button 
                    className="bg-red-500 hover:bg-red-600"
                    onClick={() => {
                      handleChallenge(selectedProfile.id);
                      setProfileDialogOpen(false);
                    }}
                  >
                    <Swords className="h-4 w-4 mr-2" />
                    Challenge to Duel
                  </Button>
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
