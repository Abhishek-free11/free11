import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import { 
  Users, Trophy, Target, Flame, Crown, Shield, 
  Plus, Search, LogOut, Award, TrendingUp 
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const Clans = () => {
  const { user, refreshUser } = useAuth();
  const navigate = useNavigate();
  const [myClan, setMyClan] = useState(null);
  const [allClans, setAllClans] = useState([]);
  const [clanLeaderboard, setClanLeaderboard] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Create clan form
  const [newClan, setNewClan] = useState({
    name: '',
    description: '',
    tag: '',
    logo_emoji: '🏏'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [myClanRes, clansRes, leaderboardRes, challengesRes] = await Promise.all([
        api.getMyClan(),
        api.listClans('accuracy'),
        api.getClanLeaderboard(),
        api.getClanChallenges()
      ]);
      
      setMyClan(myClanRes.data);
      setAllClans(clansRes.data || []);
      setClanLeaderboard(leaderboardRes.data || []);
      setChallenges(challengesRes.data?.challenges || []);
    } catch (error) {
      console.error('Error fetching clan data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateClan = async () => {
    if (!newClan.name || !newClan.tag || !newClan.description) {
      toast.error('Please fill all fields');
      return;
    }
    
    try {
      await api.createClan(newClan);
      toast.success('Clan created successfully!');
      setCreateDialogOpen(false);
      setNewClan({ name: '', description: '', tag: '', logo_emoji: '🏏' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create clan');
    }
  };

  const handleJoinClan = async (clanId) => {
    try {
      await api.joinClan(clanId);
      toast.success(
        <div>
          <p className="font-bold">Welcome to the clan! 🎉</p>
          <p className="text-sm text-slate-300 mt-1">Remember: Clans compete on SKILL (accuracy & streaks), not coins. Rise together!</p>
        </div>,
        { duration: 5000 }
      );
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to join clan');
    }
  };

  const handleLeaveClan = async () => {
    try {
      await api.leaveClan();
      toast.success('Left the clan');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to leave clan');
    }
  };

  const filteredClans = allClans.filter(clan => 
    clan.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    clan.tag.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const emojiOptions = ['🏏', '🔥', '⚡', '🎯', '🏆', '💎', '🦁', '🐯', '🦅', '🐉'];

  const getRoleColor = (role) => {
    switch(role) {
      case 'leader': return 'text-yellow-400 bg-yellow-500/20';
      case 'co-leader': return 'text-purple-400 bg-purple-500/20';
      case 'elder': return 'text-blue-400 bg-blue-500/20';
      default: return 'text-slate-400 bg-slate-500/20';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 pb-20 md:pb-0 via-slate-900 to-slate-950">
        <Navbar />
        <div className="container mx-auto px-4 py-20 text-center">
          <div className="animate-spin h-12 w-12 border-4 border-yellow-400 border-t-transparent rounded-full mx-auto"></div>
          <p className="text-slate-400 mt-4">Loading clans...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 pb-20 md:pb-0 via-slate-900 to-slate-950">
      <Navbar />
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 max-w-7xl" data-testid="clans-page">
        {/* Header */}
        <div className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-black text-white mb-2 flex items-center gap-3">
              <Users className="h-10 w-10 text-blue-400" />
              Clans
            </h1>
            <p className="text-slate-400">Join or create a clan to compete together!</p>
          </div>
          
          {!myClan?.in_clan && (
            <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
              <DialogTrigger asChild>
                <Button 
                  className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                  disabled={user?.level < 2}
                  data-testid="create-clan-btn"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create Clan
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-slate-900 border-slate-800">
                <DialogHeader>
                  <DialogTitle className="text-white">Create New Clan</DialogTitle>
                  <DialogDescription className="text-slate-400">
                    Build your cricket prediction squad!
                  </DialogDescription>
                </DialogHeader>
                
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label className="text-slate-200">Clan Name</Label>
                    <Input
                      placeholder="Mumbai Mavericks"
                      value={newClan.name}
                      onChange={(e) => setNewClan({...newClan, name: e.target.value})}
                      className="bg-slate-800 border-slate-700 text-white"
                      data-testid="clan-name-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-slate-200">Tag (2-5 characters)</Label>
                    <Input
                      placeholder="MMAV"
                      maxLength={5}
                      value={newClan.tag}
                      onChange={(e) => setNewClan({...newClan, tag: e.target.value.toUpperCase()})}
                      className="bg-slate-800 border-slate-700 text-white uppercase"
                      data-testid="clan-tag-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-slate-200">Description</Label>
                    <Input
                      placeholder="The best predictors in Mumbai!"
                      value={newClan.description}
                      onChange={(e) => setNewClan({...newClan, description: e.target.value})}
                      className="bg-slate-800 border-slate-700 text-white"
                      data-testid="clan-desc-input"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label className="text-slate-200">Clan Logo</Label>
                    <div className="flex flex-wrap gap-2">
                      {emojiOptions.map((emoji) => (
                        <Button
                          key={emoji}
                          variant={newClan.logo_emoji === emoji ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setNewClan({...newClan, logo_emoji: emoji})}
                          className={newClan.logo_emoji === emoji ? 'bg-blue-500' : 'border-slate-700'}
                        >
                          {emoji}
                        </Button>
                      ))}
                    </div>
                  </div>
                </div>
                
                <DialogFooter>
                  <Button variant="outline" onClick={() => setCreateDialogOpen(false)} className="border-slate-700">
                    Cancel
                  </Button>
                  <Button onClick={handleCreateClan} className="bg-blue-500 hover:bg-blue-600" data-testid="confirm-create-clan">
                    Create Clan
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
          
          {user?.level < 2 && !myClan?.in_clan && (
            <p className="text-sm text-amber-400">
              Reach Level 2 (Amateur) to create a clan
            </p>
          )}
        </div>

        {/* My Clan Section */}
        {myClan?.in_clan && myClan.clan && (
          <Card className="mb-8 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/30" data-testid="my-clan-card">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-5xl">{myClan.clan.logo_emoji}</div>
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50">
                        [{myClan.clan.tag}]
                      </Badge>
                      <CardTitle className="text-white text-2xl">{myClan.clan.name}</CardTitle>
                    </div>
                    <CardDescription className="text-slate-400 mt-1">
                      {myClan.clan.description}
                    </CardDescription>
                  </div>
                </div>
                
                {myClan.membership?.role !== 'leader' && (
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleLeaveClan}
                    className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                    data-testid="leave-clan-btn"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Leave
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {/* Clan Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center p-4 bg-slate-900/50 rounded-lg">
                  <Target className="h-6 w-6 text-green-400 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-green-400">{myClan.clan.clan_accuracy}%</p>
                  <p className="text-xs text-slate-400">Clan Accuracy</p>
                </div>
                <div className="text-center p-4 bg-slate-900/50 rounded-lg">
                  <Users className="h-6 w-6 text-blue-400 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-blue-400">{myClan.clan.member_count}/{myClan.clan.max_members}</p>
                  <p className="text-xs text-slate-400">Members</p>
                </div>
                <div className="text-center p-4 bg-slate-900/50 rounded-lg">
                  <Flame className="h-6 w-6 text-red-400 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-red-400">{myClan.clan.best_streak}</p>
                  <p className="text-xs text-slate-400">Best Streak</p>
                </div>
                <div className="text-center p-4 bg-slate-900/50 rounded-lg">
                  <Trophy className="h-6 w-6 text-yellow-400 mx-auto mb-2" />
                  <p className="text-2xl font-bold text-yellow-400">{myClan.clan.challenges_won}</p>
                  <p className="text-xs text-slate-400">Challenges Won</p>
                </div>
              </div>

              {/* Members List */}
              <div>
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-400" />
                  Members ({myClan.members?.length || 0})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {myClan.members?.map((member, idx) => (
                    <div 
                      key={member.user_id}
                      className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-slate-500 font-mono w-6">#{idx + 1}</span>
                        <div>
                          <p className="text-white font-medium">{member.name}</p>
                          <div className="flex items-center gap-2">
                            <Badge className={`text-xs ${getRoleColor(member.role)}`}>
                              {member.role === 'leader' && <Crown className="h-3 w-3 mr-1" />}
                              {member.role}
                            </Badge>
                            <span className="text-xs text-slate-400">Level {member.level}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-green-400 font-bold">{member.accuracy}%</p>
                        <p className="text-xs text-slate-400">{member.predictions_in_clan} predictions</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tabs for Browse/Leaderboard/Challenges */}
        <Tabs defaultValue={myClan?.in_clan ? "leaderboard" : "browse"} className="space-y-6">
          <TabsList className="bg-slate-800/50 border border-slate-700">
            {!myClan?.in_clan && (
              <TabsTrigger value="browse" className="data-[state=active]:bg-blue-500">
                Browse Clans
              </TabsTrigger>
            )}
            <TabsTrigger value="leaderboard" className="data-[state=active]:bg-blue-500">
              Clan Leaderboard
            </TabsTrigger>
            <TabsTrigger value="challenges" className="data-[state=active]:bg-blue-500">
              Challenges
            </TabsTrigger>
          </TabsList>

          {/* Browse Clans Tab */}
          {!myClan?.in_clan && (
            <TabsContent value="browse">
              <Card className="bg-slate-900/50 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Search className="h-5 w-5 text-slate-400" />
                    Find a Clan
                  </CardTitle>
                  <div className="relative">
                    <Input
                      placeholder="Search by name or tag..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="bg-slate-800 border-slate-700 text-white pl-10"
                      data-testid="clan-search-input"
                    />
                    <Search className="h-4 w-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {filteredClans.length === 0 ? (
                      <div className="text-center py-8">
                        <Users className="h-12 w-12 text-slate-700 mx-auto mb-3" />
                        <p className="text-slate-400">No clans found. Be the first to create one!</p>
                      </div>
                    ) : (
                      filteredClans.map((clan) => (
                        <div 
                          key={clan.id}
                          className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors"
                          data-testid={`clan-item-${clan.id}`}
                        >
                          <div className="flex items-center gap-4">
                            <div className="text-3xl">{clan.logo_emoji}</div>
                            <div>
                              <div className="flex items-center gap-2">
                                <Badge className="bg-slate-700 text-slate-300">[{clan.tag}]</Badge>
                                <p className="text-white font-bold">{clan.name}</p>
                              </div>
                              <p className="text-sm text-slate-400">{clan.description}</p>
                              <div className="flex items-center gap-4 mt-1 text-xs text-slate-500">
                                <span><Users className="h-3 w-3 inline mr-1" />{clan.member_count}/{clan.max_members}</span>
                                <span className="text-green-400">{clan.clan_accuracy}% accuracy</span>
                              </div>
                            </div>
                          </div>
                          <Button 
                            onClick={() => handleJoinClan(clan.id)}
                            className="bg-blue-500 hover:bg-blue-600"
                            disabled={clan.member_count >= clan.max_members}
                            data-testid={`join-clan-${clan.id}`}
                          >
                            {clan.member_count >= clan.max_members ? 'Full' : 'Join'}
                          </Button>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* Leaderboard Tab */}
          <TabsContent value="leaderboard">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-400" />
                  Clan Rankings (By Skill)
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Ranked by prediction accuracy - not coins!
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {clanLeaderboard.length === 0 ? (
                    <div className="text-center py-8">
                      <Trophy className="h-12 w-12 text-slate-700 mx-auto mb-3" />
                      <p className="text-slate-400">No clans on the leaderboard yet</p>
                    </div>
                  ) : (
                    clanLeaderboard.map((clan) => (
                      <div 
                        key={clan.id}
                        className={`flex items-center justify-between p-4 rounded-lg ${
                          clan.rank === 1 ? 'bg-yellow-500/10 border border-yellow-500/30' :
                          clan.rank === 2 ? 'bg-slate-400/10 border border-slate-400/30' :
                          clan.rank === 3 ? 'bg-amber-700/10 border border-amber-700/30' :
                          'bg-slate-800/50'
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                            clan.rank === 1 ? 'bg-yellow-500 text-black' :
                            clan.rank === 2 ? 'bg-slate-400 text-black' :
                            clan.rank === 3 ? 'bg-amber-700 text-white' :
                            'bg-slate-700 text-slate-300'
                          }`}>
                            {clan.rank}
                          </div>
                          <div className="text-2xl">{clan.logo_emoji}</div>
                          <div>
                            <div className="flex items-center gap-2">
                              <Badge className="bg-slate-700 text-slate-300">[{clan.tag}]</Badge>
                              <p className="text-white font-bold">{clan.name}</p>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                              <span><Users className="h-3 w-3 inline mr-1" />{clan.member_count}</span>
                              <span><TrendingUp className="h-3 w-3 inline mr-1" />{clan.total_predictions} predictions</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-bold text-green-400">{clan.accuracy}%</p>
                          <p className="text-xs text-slate-400">
                            <Flame className="h-3 w-3 inline mr-1 text-red-400" />
                            Best streak: {clan.best_streak}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Challenges Tab */}
          <TabsContent value="challenges">
            <Card className="bg-slate-900/50 border-slate-800">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Award className="h-5 w-5 text-purple-400" />
                  Clan Challenges
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Compete with other clans for badges and glory!
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!myClan?.in_clan ? (
                  <div className="text-center py-8">
                    <Shield className="h-12 w-12 text-slate-700 mx-auto mb-3" />
                    <p className="text-slate-400">Join a clan to participate in challenges</p>
                  </div>
                ) : challenges.length === 0 ? (
                  <div className="text-center py-8">
                    <Award className="h-12 w-12 text-slate-700 mx-auto mb-3" />
                    <p className="text-slate-400">No active challenges right now</p>
                  </div>
                ) : (
                  <div className="grid md:grid-cols-3 gap-4">
                    {challenges.map((challenge) => (
                      <Card 
                        key={challenge.id} 
                        className="bg-slate-800/50 border-slate-700 hover:border-purple-500/50 transition-colors"
                      >
                        <CardHeader className="pb-2">
                          <CardTitle className="text-white text-lg">{challenge.name}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <p className="text-slate-400 text-sm mb-3">{challenge.description}</p>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-slate-500">Target:</span>
                              <span className="text-white">{challenge.target}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Duration:</span>
                              <span className="text-white">{challenge.duration}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Reward:</span>
                              <span className="text-yellow-400">{challenge.reward}</span>
                            </div>
                          </div>
                          <Button 
                            className="w-full mt-4 bg-purple-500 hover:bg-purple-600"
                            size="sm"
                          >
                            Participate
                          </Button>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Clans;
