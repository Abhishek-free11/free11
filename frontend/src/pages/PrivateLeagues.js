import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Users, Trophy, Plus, Copy, Share2, Crown, 
  ChevronRight, Medal, LogOut, Settings
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

const PrivateLeagues = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const [leagues, setLeagues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [joinCode, setJoinCode] = useState('');
  
  // Create league form
  const [newLeagueName, setNewLeagueName] = useState('');
  const [newLeagueMaxMembers, setNewLeagueMaxMembers] = useState(20);
  const [newLeagueScoringType, setNewLeagueScoringType] = useState('accuracy');

  useEffect(() => {
    fetchLeagues();
  }, []);

  const fetchLeagues = async () => {
    try {
      setLoading(true);
      const response = await api.get('/leagues/my');
      setLeagues(response.data.leagues);
    } catch (error) {
      console.error('Error fetching leagues:', error);
      toast.error('Failed to load leagues');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLeague = async () => {
    if (!newLeagueName.trim()) {
      toast.error('Please enter a league name');
      return;
    }
    
    try {
      const response = await api.post('/leagues/create', {
        name: newLeagueName,
        max_members: newLeagueMaxMembers,
        scoring_type: newLeagueScoringType
      });
      
      toast.success('League created!');
      setShowCreate(false);
      setNewLeagueName('');
      fetchLeagues();
      
      // Copy code to clipboard
      navigator.clipboard.writeText(response.data.join_code);
      toast.success(`Join code copied: ${response.data.join_code}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create league');
    }
  };

  const handleJoinLeague = async () => {
    if (!joinCode.trim()) {
      toast.error('Please enter a league code');
      return;
    }
    
    try {
      const response = await api.post('/leagues/join', {
        code: joinCode.toUpperCase()
      });
      
      toast.success(response.data.message);
      setShowJoin(false);
      setJoinCode('');
      fetchLeagues();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to join league');
    }
  };

  const copyLeagueCode = (code) => {
    navigator.clipboard.writeText(code);
    toast.success('League code copied!');
  };

  const handleLeaveLeague = async (leagueId, leagueName) => {
    if (!window.confirm(`Are you sure you want to leave "${leagueName}"?`)) {
      return;
    }
    
    try {
      await api.post(`/leagues/${leagueId}/leave`);
      toast.success('Left the league');
      fetchLeagues();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to leave league');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-yellow-400 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/50 to-blue-900/50 border-b border-slate-700">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Trophy className="h-6 w-6 text-yellow-400" />
            Private Leagues
          </h1>
          <p className="text-slate-300 mt-1">
            Compete with friends in your own leagues
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-4 space-y-4">
        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button 
            onClick={() => setShowCreate(true)}
            className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black"
            data-testid="create-league-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create League
          </Button>
          <Button 
            onClick={() => setShowJoin(true)}
            variant="outline"
            className="flex-1"
            data-testid="join-league-btn"
          >
            <Users className="h-4 w-4 mr-2" />
            Join League
          </Button>
        </div>

        {/* Create League Modal */}
        {showCreate && (
          <Card className="bg-slate-900/80 border-slate-700">
            <CardHeader>
              <CardTitle className="text-lg">Create New League</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-slate-300">League Name</Label>
                <Input
                  placeholder="My Fantasy League"
                  value={newLeagueName}
                  onChange={(e) => setNewLeagueName(e.target.value)}
                  className="bg-slate-800 border-slate-700 text-white mt-1"
                  data-testid="league-name-input"
                />
              </div>
              <div>
                <Label className="text-slate-300">Max Members</Label>
                <select
                  value={newLeagueMaxMembers}
                  onChange={(e) => setNewLeagueMaxMembers(Number(e.target.value))}
                  className="w-full h-10 rounded-md bg-slate-800 border border-slate-700 px-3 text-white mt-1"
                >
                  <option value={10}>10 members</option>
                  <option value={20}>20 members</option>
                  <option value={50}>50 members</option>
                  <option value={100}>100 members</option>
                </select>
              </div>
              <div>
                <Label className="text-slate-300">Scoring Type</Label>
                <select
                  value={newLeagueScoringType}
                  onChange={(e) => setNewLeagueScoringType(e.target.value)}
                  className="w-full h-10 rounded-md bg-slate-800 border border-slate-700 px-3 text-white mt-1"
                >
                  <option value="accuracy">Accuracy %</option>
                  <option value="total_predictions">Total Predictions</option>
                  <option value="streak">Best Streak</option>
                </select>
              </div>
              <div className="flex gap-2">
                <Button 
                  onClick={handleCreateLeague}
                  className="flex-1 bg-yellow-500 hover:bg-yellow-600 text-black"
                >
                  Create
                </Button>
                <Button 
                  onClick={() => setShowCreate(false)}
                  variant="outline"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Join League Modal */}
        {showJoin && (
          <Card className="bg-slate-900/80 border-slate-700">
            <CardHeader>
              <CardTitle className="text-lg">Join a League</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-slate-300">League Code</Label>
                <Input
                  placeholder="ABCD1234"
                  value={joinCode}
                  onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                  className="bg-slate-800 border-slate-700 text-white mt-1"
                  maxLength={8}
                  data-testid="join-code-input"
                />
              </div>
              <div className="flex gap-2">
                <Button 
                  onClick={handleJoinLeague}
                  className="flex-1 bg-green-500 hover:bg-green-600"
                >
                  Join
                </Button>
                <Button 
                  onClick={() => setShowJoin(false)}
                  variant="outline"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* League List */}
        {leagues.length === 0 ? (
          <Card className="bg-slate-800/70 border-slate-700">
            <CardContent className="p-8 text-center">
              <Trophy className="h-12 w-12 mx-auto text-slate-600 mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Leagues Yet</h3>
              <p className="text-slate-300 mb-4">
                Create a league and invite your friends to compete!
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {leagues.map((league) => (
              <Card 
                key={league.id}
                className="bg-slate-800/70 border-slate-700 hover:border-slate-700 transition-all cursor-pointer"
                onClick={() => navigate(`/leagues/${league.id}`)}
                data-testid={`league-card-${league.id}`}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
                        <Trophy className="h-6 w-6 text-white" />
                      </div>
                      <div>
                        <h3 className="font-bold flex items-center gap-2">
                          {league.name}
                          {league.is_admin && (
                            <Crown className="h-4 w-4 text-yellow-400" />
                          )}
                        </h3>
                        <div className="flex items-center gap-3 text-sm text-slate-300">
                          <span className="flex items-center gap-1">
                            <Users className="h-3 w-3" />
                            {league.member_count}/{league.max_members}
                          </span>
                          <Badge variant="outline" className="text-xs">
                            {league.scoring_type}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          copyLeagueCode(league.code);
                        }}
                        data-testid={`copy-code-${league.id}`}
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                      <ChevronRight className="h-5 w-5 text-slate-500" />
                    </div>
                  </div>
                  
                  {league.my_stats && (
                    <div className="mt-3 pt-3 border-t border-slate-700 flex items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Medal className="h-4 w-4 text-yellow-400" />
                        <span>Rank #{league.my_stats.rank || '-'}</span>
                      </div>
                      <div className="text-slate-300">
                        {league.my_stats.accuracy?.toFixed(1) || 0}% accuracy
                      </div>
                      <div className="text-slate-300">
                        {league.my_stats.total_predictions || 0} predictions
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PrivateLeagues;
