import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Trophy, Users, Coins, Clock, ChevronRight, Zap, Star, 
  Calendar, MapPin, Filter, Crown, Target, ArrowRight
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

// Mock data for contests (to be replaced with API)
const MOCK_MATCHES = [
  {
    id: 'match1',
    team1: 'Chennai Super Kings',
    team1_short: 'CSK',
    team2: 'Mumbai Indians',
    team2_short: 'MI',
    series: 'IPL 2026',
    venue: 'M.A. Chidambaram Stadium',
    start_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(), // 2 hours from now
    status: 'upcoming',
    contests: [
      { id: 'c1', name: 'Mega Contest', entry: 0, prize_pool: 5000, spots: 1000, filled: 456, winner_coins: 500 },
      { id: 'c2', name: 'Head to Head', entry: 0, prize_pool: 100, spots: 2, filled: 1, winner_coins: 100 },
      { id: 'c3', name: 'Practice Contest', entry: 0, prize_pool: 200, spots: 100, filled: 23, winner_coins: 50 },
    ]
  },
  {
    id: 'match2',
    team1: 'Royal Challengers',
    team1_short: 'RCB',
    team2: 'Delhi Capitals',
    team2_short: 'DC',
    series: 'IPL 2026',
    venue: 'M. Chinnaswamy Stadium',
    start_time: new Date(Date.now() + 5 * 60 * 60 * 1000).toISOString(), // 5 hours from now
    status: 'upcoming',
    contests: [
      { id: 'c4', name: 'Winner Takes All', entry: 0, prize_pool: 1000, spots: 50, filled: 12, winner_coins: 200 },
      { id: 'c5', name: 'Small League', entry: 0, prize_pool: 500, spots: 20, filled: 8, winner_coins: 100 },
    ]
  },
  {
    id: 'match3',
    team1: 'Kolkata Knight Riders',
    team1_short: 'KKR',
    team2: 'Rajasthan Royals',
    team2_short: 'RR',
    series: 'IPL 2026',
    venue: 'Eden Gardens',
    start_time: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
    status: 'upcoming',
    contests: [
      { id: 'c6', name: 'Grand League', entry: 0, prize_pool: 10000, spots: 5000, filled: 1234, winner_coins: 1000 },
    ]
  },
];

const ContestCard = ({ contest, onJoin }) => {
  const fillPercentage = (contest.filled / contest.spots) * 100;
  
  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 hover:border-yellow-500/50 transition-all">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="font-bold text-white">{contest.name}</h4>
          <div className="flex items-center gap-2 mt-1">
            <Badge className="bg-green-500/20 text-green-400 text-xs">FREE Entry</Badge>
          </div>
        </div>
        <div className="text-right">
          <p className="text-yellow-400 font-bold text-lg">{contest.prize_pool}</p>
          <p className="text-slate-500 text-xs">Prize Pool</p>
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="mb-3">
        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all"
            style={{ width: `${fillPercentage}%` }}
          />
        </div>
        <div className="flex justify-between mt-1 text-xs">
          <span className="text-slate-400">{contest.filled} joined</span>
          <span className="text-slate-500">{contest.spots - contest.filled} spots left</span>
        </div>
      </div>
      
      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <Trophy className="h-3 w-3 text-yellow-400" />
            Win {contest.winner_coins} coins
          </span>
          <span className="flex items-center gap-1">
            <Users className="h-3 w-3" />
            {contest.spots} spots
          </span>
        </div>
        <Button 
          size="sm" 
          className="bg-green-500 hover:bg-green-600 text-white font-bold"
          onClick={() => onJoin(contest)}
        >
          Join Free
        </Button>
      </div>
    </div>
  );
};

const MatchCard = ({ match, onSelect }) => {
  const startTime = new Date(match.start_time);
  const now = new Date();
  const hoursLeft = Math.max(0, Math.floor((startTime - now) / (1000 * 60 * 60)));
  const minutesLeft = Math.max(0, Math.floor(((startTime - now) % (1000 * 60 * 60)) / (1000 * 60)));
  
  return (
    <Card 
      className="bg-slate-800/80 border-slate-700 hover:border-yellow-500/50 transition-all cursor-pointer overflow-hidden"
      onClick={() => onSelect(match)}
    >
      {/* Match Header */}
      <div className="bg-gradient-to-r from-slate-900/80 to-slate-800/80 px-4 py-2 flex items-center justify-between">
        <Badge className="bg-slate-700 text-slate-300 text-xs">{match.series}</Badge>
        <div className="flex items-center gap-1 text-xs">
          <Clock className="h-3 w-3 text-red-400" />
          <span className="text-red-400 font-medium">
            {hoursLeft > 0 ? `${hoursLeft}h ${minutesLeft}m` : `${minutesLeft}m`}
          </span>
        </div>
      </div>
      
      <CardContent className="p-4">
        {/* Teams */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3 flex-1">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-yellow-500 to-amber-600 flex items-center justify-center text-lg font-black text-black">
              {match.team1_short[0]}
            </div>
            <div>
              <p className="font-bold text-white">{match.team1_short}</p>
              <p className="text-xs text-slate-400 truncate max-w-[80px]">{match.team1}</p>
            </div>
          </div>
          
          <div className="px-3">
            <span className="text-slate-600 font-bold text-sm">VS</span>
          </div>
          
          <div className="flex items-center gap-3 flex-1 justify-end">
            <div className="text-right">
              <p className="font-bold text-white">{match.team2_short}</p>
              <p className="text-xs text-slate-400 truncate max-w-[80px]">{match.team2}</p>
            </div>
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-lg font-black text-white">
              {match.team2_short[0]}
            </div>
          </div>
        </div>
        
        {/* Contest count */}
        <div className="flex items-center justify-between bg-slate-900/50 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <Trophy className="h-4 w-4 text-yellow-400" />
            <span className="text-white text-sm font-medium">{match.contests.length} Contests</span>
          </div>
          <Button size="sm" className="bg-yellow-500 hover:bg-yellow-600 text-black font-bold gap-1">
            Join <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

const Contests = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [matches, setMatches] = useState(MOCK_MATCHES);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [activeTab, setActiveTab] = useState('upcoming');
  const [loading, setLoading] = useState(false);

  const handleJoinContest = (contest) => {
    // Navigate to team creation for this contest
    if (selectedMatch) {
      navigate(`/fantasy/${selectedMatch.id}?contest=${contest.id}`);
    }
  };

  const handleMatchSelect = (match) => {
    setSelectedMatch(match);
  };

  const handleBackToMatches = () => {
    setSelectedMatch(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 pb-20 md:pb-0">
      <Navbar />
      
      <div className="container mx-auto px-3 sm:px-4 py-4 max-w-2xl">
        {/* Header */}
        {!selectedMatch && (
          <div className="mb-4">
            <h1 className="text-2xl font-black text-white flex items-center gap-2">
              <Trophy className="h-7 w-7 text-yellow-400" />
              Contests
            </h1>
            <p className="text-slate-400 text-sm mt-1">Join fantasy contests and win coins!</p>
          </div>
        )}
        
        {/* Back button when match selected */}
        {selectedMatch && (
          <Button 
            variant="ghost" 
            onClick={handleBackToMatches}
            className="mb-4 text-slate-400 hover:text-white"
          >
            ← Back to Matches
          </Button>
        )}
        
        {!selectedMatch ? (
          <>
            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-4">
              <TabsList className="bg-slate-800 border border-slate-700 w-full">
                <TabsTrigger 
                  value="upcoming" 
                  className="flex-1 data-[state=active]:bg-yellow-500/20 data-[state=active]:text-yellow-400"
                >
                  Upcoming
                </TabsTrigger>
                <TabsTrigger 
                  value="live" 
                  className="flex-1 data-[state=active]:bg-red-500/20 data-[state=active]:text-red-400"
                >
                  Live
                </TabsTrigger>
                <TabsTrigger 
                  value="completed" 
                  className="flex-1 data-[state=active]:bg-slate-500/20 data-[state=active]:text-slate-300"
                >
                  Completed
                </TabsTrigger>
              </TabsList>
            </Tabs>
            
            {/* Featured Contest Banner */}
            <Card className="bg-gradient-to-r from-yellow-500/20 via-orange-500/20 to-red-500/20 border-yellow-500/30 mb-4">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-yellow-500/20 rounded-xl">
                    <Star className="h-6 w-6 text-yellow-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-bold text-white">Mega Contest</h3>
                    <p className="text-slate-400 text-sm">5000 coins prize pool • FREE entry</p>
                  </div>
                  <Badge className="bg-yellow-500 text-black font-bold">HOT</Badge>
                </div>
              </CardContent>
            </Card>
            
            {/* Match List */}
            <div className="space-y-3">
              {matches.map((match) => (
                <MatchCard 
                  key={match.id} 
                  match={match} 
                  onSelect={handleMatchSelect}
                />
              ))}
            </div>
            
            {matches.length === 0 && (
              <div className="text-center py-12">
                <Trophy className="h-12 w-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-400">No matches available</p>
              </div>
            )}
          </>
        ) : (
          /* Match Detail with Contests */
          <div>
            {/* Match Info Header */}
            <Card className="bg-slate-800/80 border-slate-700 mb-4">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <Badge className="bg-slate-700 text-slate-300 text-xs">{selectedMatch.series}</Badge>
                  <div className="flex items-center gap-1 text-xs text-red-400">
                    <Clock className="h-3 w-3" />
                    Starting Soon
                  </div>
                </div>
                
                <div className="flex items-center justify-between py-3">
                  <div className="text-center flex-1">
                    <div className="w-14 h-14 mx-auto rounded-full bg-gradient-to-br from-yellow-500 to-amber-600 flex items-center justify-center text-xl font-black text-black mb-2">
                      {selectedMatch.team1_short[0]}
                    </div>
                    <p className="font-bold text-white">{selectedMatch.team1_short}</p>
                  </div>
                  
                  <div className="text-2xl font-black text-slate-600">VS</div>
                  
                  <div className="text-center flex-1">
                    <div className="w-14 h-14 mx-auto rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-xl font-black text-white mb-2">
                      {selectedMatch.team2_short[0]}
                    </div>
                    <p className="font-bold text-white">{selectedMatch.team2_short}</p>
                  </div>
                </div>
                
                <div className="flex items-center justify-center gap-1 text-xs text-slate-400">
                  <MapPin className="h-3 w-3" />
                  {selectedMatch.venue}
                </div>
              </CardContent>
            </Card>
            
            {/* Create Team CTA */}
            <Card className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-green-500/30 mb-4">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-white">Create Your Team</h3>
                    <p className="text-slate-400 text-sm">Pick 11 players and compete</p>
                  </div>
                  <Button 
                    className="bg-green-500 hover:bg-green-600 text-white font-bold"
                    onClick={() => navigate(`/fantasy/${selectedMatch.id}`)}
                  >
                    <Zap className="h-4 w-4 mr-1" />
                    Create Team
                  </Button>
                </div>
              </CardContent>
            </Card>
            
            {/* Contests List */}
            <h3 className="text-white font-bold mb-3">Available Contests</h3>
            <div className="space-y-3">
              {selectedMatch.contests.map((contest) => (
                <ContestCard 
                  key={contest.id} 
                  contest={contest} 
                  onJoin={handleJoinContest}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Contests;
