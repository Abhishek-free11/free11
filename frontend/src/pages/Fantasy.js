import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Users, Trophy, Star, ChevronRight, Check, X, 
  ArrowLeft, Info, Coins, Target, Crown
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

// Role icons and colors
const ROLE_CONFIG = {
  WK: { label: 'Wicket Keeper', color: 'bg-yellow-500', min: 1, max: 4 },
  BAT: { label: 'Batsman', color: 'bg-blue-500', min: 3, max: 6 },
  ALL: { label: 'All-Rounder', color: 'bg-green-500', min: 1, max: 4 },
  BOWL: { label: 'Bowler', color: 'bg-purple-500', min: 3, max: 6 }
};

const Fantasy = () => {
  const navigate = useNavigate();
  const { matchId } = useParams();
  const { user } = useAuth();
  
  const [players, setPlayers] = useState([]);
  const [playersByRole, setPlayersByRole] = useState({});
  const [contests, setContests] = useState([]);
  const [selectedPlayers, setSelectedPlayers] = useState([]);
  const [captain, setCaptain] = useState(null);
  const [viceCaptain, setViceCaptain] = useState(null);
  const [totalCredits, setTotalCredits] = useState(0);
  const [constraints, setConstraints] = useState({});
  const [loading, setLoading] = useState(true);
  const [step, setStep] = useState('select'); // select, captain, contest
  const [selectedContest, setSelectedContest] = useState(null);
  const [match, setMatch] = useState(null);

  useEffect(() => {
    fetchMatchData();
  }, [matchId]);

  const fetchMatchData = async () => {
    try {
      setLoading(true);
      
      // Fetch players
      const playersRes = await api.get(`/fantasy/matches/${matchId}/players`);
      setPlayers(playersRes.data.players);
      setPlayersByRole(playersRes.data.by_role);
      setConstraints(playersRes.data.constraints);
      
      // Fetch contests
      const contestsRes = await api.get(`/fantasy/matches/${matchId}/contests`);
      setContests(contestsRes.data.contests);
      
      // Fetch match details
      const matchRes = await api.get(`/cricket/matches/${matchId}`);
      setMatch(matchRes.data);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load match data');
    } finally {
      setLoading(false);
    }
  };

  const togglePlayer = (player) => {
    const isSelected = selectedPlayers.some(p => p.id === player.id);
    
    if (isSelected) {
      setSelectedPlayers(selectedPlayers.filter(p => p.id !== player.id));
      if (captain?.id === player.id) setCaptain(null);
      if (viceCaptain?.id === player.id) setViceCaptain(null);
    } else {
      // Check constraints
      if (selectedPlayers.length >= 11) {
        toast.error('Maximum 11 players allowed');
        return;
      }
      
      const newCredits = totalCredits + player.credits;
      if (newCredits > 100) {
        toast.error('Credit limit exceeded');
        return;
      }
      
      // Check role limits
      const roleCount = selectedPlayers.filter(p => p.role === player.role).length;
      const roleConfig = ROLE_CONFIG[player.role];
      if (roleCount >= roleConfig.max) {
        toast.error(`Maximum ${roleConfig.max} ${roleConfig.label}s allowed`);
        return;
      }
      
      // Check team limit
      const teamCount = selectedPlayers.filter(p => p.team_short === player.team_short).length;
      if (teamCount >= 7) {
        toast.error('Maximum 7 players from one team');
        return;
      }
      
      setSelectedPlayers([...selectedPlayers, player]);
    }
  };

  useEffect(() => {
    const credits = selectedPlayers.reduce((sum, p) => sum + p.credits, 0);
    setTotalCredits(credits);
  }, [selectedPlayers]);

  const canProceedToCapitan = () => {
    if (selectedPlayers.length !== 11) return false;
    
    const roleCounts = { WK: 0, BAT: 0, ALL: 0, BOWL: 0 };
    selectedPlayers.forEach(p => roleCounts[p.role]++);
    
    for (const [role, config] of Object.entries(ROLE_CONFIG)) {
      if (roleCounts[role] < config.min || roleCounts[role] > config.max) {
        return false;
      }
    }
    return true;
  };

  const handleCreateTeam = async () => {
    if (!captain || !viceCaptain) {
      toast.error('Please select Captain and Vice-Captain');
      return;
    }
    
    if (!selectedContest) {
      toast.error('Please select a contest');
      return;
    }
    
    try {
      const response = await api.post('/fantasy/teams/create', {
        match_id: matchId,
        contest_id: selectedContest.id,
        player_ids: selectedPlayers.map(p => p.id),
        captain_id: captain.id,
        vice_captain_id: viceCaptain.id
      });
      
      toast.success('Team created successfully! 🎉');
      navigate('/contests');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create team');
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
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 text-white pb-20 md:pb-0">
      {/* Header */}
      <div className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur border-b border-slate-700">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => step === 'select' ? navigate(-1) : setStep('select')}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          
          <div className="text-center">
            <p className="text-sm text-slate-300">
              {match?.team1_short} vs {match?.team2_short}
            </p>
            <p className="text-xs text-slate-500">{match?.venue}</p>
          </div>
          
          <div className="text-right">
            <p className="text-sm font-bold text-yellow-400">{selectedPlayers.length}/11</p>
            <p className="text-xs text-slate-300">{totalCredits.toFixed(1)}/100 cr</p>
          </div>
        </div>
        
        {/* Progress Steps */}
        <div className="max-w-4xl mx-auto px-4 py-2 flex items-center gap-2">
          {['select', 'captain', 'contest'].map((s, i) => (
            <React.Fragment key={s}>
              <div 
                className={`flex-1 h-1 rounded ${
                  step === s ? 'bg-yellow-400' : 
                  ['select', 'captain', 'contest'].indexOf(step) > i ? 'bg-green-500' : 'bg-slate-700'
                }`}
              />
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step: Player Selection */}
      {step === 'select' && (
        <div className="max-w-4xl mx-auto px-4 py-4 space-y-4">
          {/* Role Tabs */}
          <div className="flex gap-2 overflow-x-auto pb-2">
            {Object.entries(ROLE_CONFIG).map(([role, config]) => {
              const count = selectedPlayers.filter(p => p.role === role).length;
              return (
                <Badge 
                  key={role}
                  variant="outline"
                  className={`${config.color} bg-opacity-20 text-white whitespace-nowrap`}
                >
                  {config.label} ({count}/{config.min}-{config.max})
                </Badge>
              );
            })}
          </div>

          {/* Players Grid */}
          {Object.entries(playersByRole).map(([role, rolePlayers]) => (
            <div key={role} className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${ROLE_CONFIG[role].color}`} />
                {ROLE_CONFIG[role].label}s
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {rolePlayers.map((player) => {
                  const isSelected = selectedPlayers.some(p => p.id === player.id);
                  return (
                    <Card 
                      key={player.id}
                      className={`cursor-pointer transition-all ${
                        isSelected 
                          ? 'bg-yellow-500/20 border-yellow-500' 
                          : 'bg-slate-800/70 border-slate-700 hover:border-slate-600'
                      }`}
                      onClick={() => togglePlayer(player)}
                      data-testid={`player-card-${player.id}`}
                    >
                      <CardContent className="p-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full ${ROLE_CONFIG[role].color} flex items-center justify-center text-white font-bold`}>
                            {player.name.charAt(0)}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{player.name}</p>
                            <p className="text-xs text-slate-300">{player.team_short}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className="text-xs">
                            {player.credits} cr
                          </Badge>
                          {isSelected && (
                            <Check className="h-5 w-5 text-yellow-400" />
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Continue Button */}
          <div className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur border-t border-slate-700 p-4">
            <div className="max-w-4xl mx-auto">
              <Button 
                className="w-full bg-yellow-500 hover:bg-yellow-600 text-black"
                disabled={!canProceedToCapitan()}
                onClick={() => setStep('captain')}
                data-testid="proceed-to-captain-btn"
              >
                Select Captain & Vice-Captain
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Step: Captain Selection */}
      {step === 'captain' && (
        <div className="max-w-4xl mx-auto px-4 py-4 space-y-4">
          <Card className="bg-slate-800/70 border-slate-700">
            <CardContent className="p-4 text-center">
              <p className="text-sm text-slate-300">
                Captain gets <span className="text-yellow-400 font-bold">2x</span> points, 
                Vice-Captain gets <span className="text-yellow-400 font-bold">1.5x</span> points
              </p>
            </CardContent>
          </Card>

          <div className="space-y-2">
            {selectedPlayers.map((player) => {
              const isCaptain = captain?.id === player.id;
              const isViceCaptain = viceCaptain?.id === player.id;
              
              return (
                <Card 
                  key={player.id}
                  className={`bg-slate-800/70 border-slate-700 ${
                    isCaptain ? 'border-yellow-500' : isViceCaptain ? 'border-blue-500' : ''
                  }`}
                >
                  <CardContent className="p-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full ${ROLE_CONFIG[player.role].color} flex items-center justify-center text-white font-bold`}>
                        {player.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium text-sm">{player.name}</p>
                        <p className="text-xs text-slate-300">{player.team_short} • {player.role}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant={isCaptain ? "default" : "outline"}
                        className={isCaptain ? "bg-yellow-500 text-black" : ""}
                        onClick={() => {
                          if (isViceCaptain) setViceCaptain(null);
                          setCaptain(isCaptain ? null : player);
                        }}
                        data-testid={`captain-btn-${player.id}`}
                      >
                        <Crown className="h-4 w-4 mr-1" />
                        C
                      </Button>
                      <Button
                        size="sm"
                        variant={isViceCaptain ? "default" : "outline"}
                        className={isViceCaptain ? "bg-blue-500" : ""}
                        onClick={() => {
                          if (isCaptain) setCaptain(null);
                          setViceCaptain(isViceCaptain ? null : player);
                        }}
                        data-testid={`vc-btn-${player.id}`}
                      >
                        VC
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Continue Button */}
          <div className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur border-t border-slate-700 p-4">
            <div className="max-w-4xl mx-auto">
              <Button 
                className="w-full bg-yellow-500 hover:bg-yellow-600 text-black"
                disabled={!captain || !viceCaptain}
                onClick={() => setStep('contest')}
                data-testid="proceed-to-contest-btn"
              >
                Select Contest
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Step: Contest Selection */}
      {step === 'contest' && (
        <div className="max-w-4xl mx-auto px-4 py-4 space-y-4 pb-24">
          <h2 className="text-lg font-bold">Select a Contest</h2>
          
          {contests.map((contest) => (
            <Card 
              key={contest.id}
              className={`cursor-pointer transition-all ${
                selectedContest?.id === contest.id 
                  ? 'bg-yellow-500/20 border-yellow-500' 
                  : 'bg-slate-800/70 border-slate-700 hover:border-slate-600'
              }`}
              onClick={() => setSelectedContest(contest)}
              data-testid={`contest-card-${contest.id}`}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-bold">{contest.name}</h3>
                    <Badge variant="outline" className="mt-1 text-xs">
                      {contest.contest_type}
                    </Badge>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-yellow-400">
                      <Coins className="h-4 w-4 inline mr-1" />
                      {contest.prize_pool_coins}
                    </p>
                    <p className="text-xs text-slate-300">Prize Pool</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-4">
                    <span className="text-slate-300">
                      <Users className="h-4 w-4 inline mr-1" />
                      {contest.current_entries}/{contest.max_entries}
                    </span>
                    <span className="text-green-400">FREE Entry</span>
                  </div>
                  {selectedContest?.id === contest.id && (
                    <Check className="h-5 w-5 text-yellow-400" />
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Submit Button */}
          <div className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur border-t border-slate-700 p-4">
            <div className="max-w-4xl mx-auto">
              <Button 
                className="w-full bg-green-500 hover:bg-green-600 text-white"
                disabled={!selectedContest}
                onClick={handleCreateTeam}
                data-testid="create-team-btn"
              >
                <Trophy className="h-4 w-4 mr-2" />
                Create Team & Join Contest
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Fantasy;
