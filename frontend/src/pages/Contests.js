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
  Calendar, MapPin, Filter, Crown, Target, ArrowRight, Loader2,
  BookOpen, Flame
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

// T20 Season countdown for empty state
function T20EmptyState({ navigate }) {
  const [timeLeft, setTimeLeft] = React.useState({});
  React.useEffect(() => {
    const target = new Date('2026-03-26T18:00:00+05:30');
    const tick = () => {
      const diff = target - Date.now();
      if (diff <= 0) return setTimeLeft({ days: 0, hours: 0, mins: 0 });
      setTimeLeft({
        days: Math.floor(diff / 86400000),
        hours: Math.floor((diff % 86400000) / 3600000),
        mins: Math.floor((diff % 3600000) / 60000),
      });
    };
    tick();
    const id = setInterval(tick, 30000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="py-6 px-1 animate-fadeIn">
      {/* T20 countdown */}
      <div className="rounded-2xl p-4 mb-4 text-center"
        style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.08), rgba(198,160,82,0.03))', border: '1px solid rgba(198,160,82,0.2)' }}>
        <p className="text-xs font-bold tracking-widest mb-2" style={{ color: '#C6A052' }}>T20 SEASON 2026</p>
        <div className="flex justify-center gap-3 mb-2">
          {[['days', timeLeft.days], ['hrs', timeLeft.hours], ['min', timeLeft.mins]].map(([label, val]) => (
            <div key={label} className="text-center">
              <div className="text-3xl font-black text-white" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>
                {String(val ?? '--').padStart(2, '0')}
              </div>
              <div className="text-[9px] uppercase tracking-widest" style={{ color: '#8A9096' }}>{label}</div>
            </div>
          ))}
        </div>
        <p className="text-xs" style={{ color: '#8A9096' }}>Live ball-by-ball predictions start March 26</p>
      </div>

      {/* Action cards */}
      <p className="text-xs font-bold tracking-widest mb-3" style={{ color: '#8A9096' }}>WHILE YOU WAIT — EARN COINS</p>
      <div className="space-y-2">
        <button onClick={() => navigate('/earn')}
          className="w-full flex items-center gap-3 p-3.5 rounded-xl text-left transition-all active:scale-98"
          style={{ background: 'rgba(74,222,128,0.06)', border: '1px solid rgba(74,222,128,0.15)' }}>
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(74,222,128,0.1)' }}>
            <Zap className="h-4 w-4 text-green-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-white">Daily Puzzle</p>
            <p className="text-xs" style={{ color: '#8A9096' }}>Answer today's cricket question · Earn up to 15 coins</p>
          </div>
          <ChevronRight className="h-4 w-4" style={{ color: '#8A9096' }} />
        </button>
        <button onClick={() => navigate('/earn')}
          className="w-full flex items-center gap-3 p-3.5 rounded-xl text-left transition-all active:scale-98"
          style={{ background: 'rgba(198,160,82,0.06)', border: '1px solid rgba(198,160,82,0.15)' }}>
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(198,160,82,0.1)' }}>
            <Flame className="h-4 w-4" style={{ color: '#C6A052' }} />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-white">Daily Check-in Streak</p>
            <p className="text-xs" style={{ color: '#8A9096' }}>Log in every day · streak bonuses up to 75 coins</p>
          </div>
          <ChevronRight className="h-4 w-4" style={{ color: '#8A9096' }} />
        </button>
        <button onClick={() => navigate('/leaderboards')}
          className="w-full flex items-center gap-3 p-3.5 rounded-xl text-left transition-all active:scale-98"
          style={{ background: 'rgba(168,85,247,0.06)', border: '1px solid rgba(168,85,247,0.15)' }}>
          <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
            style={{ background: 'rgba(168,85,247,0.1)' }}>
            <Trophy className="h-4 w-4 text-purple-400" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-bold text-white">See the Leaderboard</p>
            <p className="text-xs" style={{ color: '#8A9096' }}>Top predictors win extra coin bonuses at season end</p>
          </div>
          <ChevronRight className="h-4 w-4" style={{ color: '#8A9096' }} />
        </button>
      </div>
    </div>
  );
}

// Default contests for each match
const generateContests = (matchId) => [
  { id: `${matchId}_mega`, name: 'Mega Contest', entry: 0, prize_pool: 5000, spots: 1000, filled: Math.floor(Math.random() * 500), winner_coins: 500 },
  { id: `${matchId}_h2h`, name: 'Head to Head', entry: 0, prize_pool: 100, spots: 2, filled: 1, winner_coins: 100 },
  { id: `${matchId}_practice`, name: 'Practice Contest', entry: 0, prize_pool: 200, spots: 100, filled: Math.floor(Math.random() * 50), winner_coins: 50 },
];

const ContestCard = ({ contest, onJoin, matchStatus }) => {
  const fillPercentage = (contest.filled / contest.spots) * 100;
  const isCompleted = matchStatus === 'completed';
  
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
          <span className="text-slate-300">{contest.filled} joined</span>
          <span className="text-slate-500">{contest.spots - contest.filled} spots left</span>
        </div>
      </div>
      
      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-xs text-slate-300">
          <span className="flex items-center gap-1">
            <Trophy className="h-3 w-3 text-yellow-400" />
            Win {contest.winner_coins} coins
          </span>
          <span className="flex items-center gap-1">
            <Users className="h-3 w-3" />
            {contest.spots} spots
          </span>
        </div>
        {isCompleted ? (
          <Button 
            size="sm" 
            className="bg-slate-600 text-slate-300 cursor-not-allowed"
            disabled
          >
            Match Ended
          </Button>
        ) : (
          <Button 
            size="sm" 
            className="bg-green-500 hover:bg-green-600 text-white font-bold"
            onClick={() => onJoin(contest)}
          >
            Join Free
          </Button>
        )}
      </div>
    </div>
  );
};

const MatchCard = ({ match, onSelect }) => {
  const startTime = new Date(match.start_time);
  const now = new Date();
  const hoursLeft = Math.max(0, Math.floor((startTime - now) / (1000 * 60 * 60)));
  const minutesLeft = Math.max(0, Math.floor(((startTime - now) % (1000 * 60 * 60)) / (1000 * 60)));
  
  // Check if this is mock data
  const isMock = match.is_mock || match.source === 'mock_data';
  
  // Check if ICC World Cup
  const isICCWorldCup = match.is_icc_worldcup || (match.series && match.series.toLowerCase().includes('world cup'));
  const isIPL = match.is_ipl || (match.series && match.series.toLowerCase().includes('ipl'));
  
  // Team colors mapping
  const teamColors = {
    'CSK': 'from-yellow-500 to-yellow-600',
    'MI': 'from-blue-500 to-blue-700',
    'RCB': 'from-red-600 to-red-800',
    'DC': 'from-blue-400 to-blue-600',
    'KKR': 'from-purple-600 to-purple-800',
    'RR': 'from-pink-500 to-pink-700',
    'SRH': 'from-orange-500 to-orange-700',
    'GT': 'from-cyan-500 to-cyan-700',
    'PBKS': 'from-red-500 to-red-600',
    'LSG': 'from-teal-500 to-teal-700',
    'IND': 'from-blue-600 to-blue-800',
    'AUS': 'from-yellow-500 to-yellow-700',
    'ENG': 'from-red-500 to-blue-700',
    'SA': 'from-green-600 to-green-800',
    'PAK': 'from-green-500 to-green-700',
    'WI': 'from-red-600 to-yellow-600',
    'NZ': 'from-slate-700 to-slate-900',
    'SL': 'from-blue-700 to-yellow-600',
  };
  
  return (
    <div 
      className={`bg-gradient-to-b from-slate-800/90 to-slate-900/90 rounded-2xl overflow-hidden cursor-pointer card-tap hover-lift ${isICCWorldCup ? 'ring-2 ring-yellow-500/50' : ''}`}
      onClick={() => onSelect(match)}
    >
      {/* ICC World Cup Banner */}
      {isICCWorldCup && !isMock && (
        <div className="bg-gradient-to-r from-yellow-600/30 to-orange-600/30 border-b border-yellow-500/30 px-4 py-1.5">
          <span className="text-xs text-yellow-400 font-bold">🏆 ICC Men's T20 World Cup 2026</span>
        </div>
      )}
      
      {/* T20 Season Banner */}
      {isIPL && !isICCWorldCup && !isMock && (
        <div className="bg-gradient-to-r from-purple-600/30 to-blue-600/30 border-b border-purple-500/30 px-4 py-1.5">
          <span className="text-xs text-purple-400 font-bold">🏏 T20 Season 2026</span>
        </div>
      )}
      
      {/* Mock Data Banner */}
      {isMock && (
        <div className="bg-amber-500/20 border-b border-amber-500/30 px-4 py-1.5">
          <span className="text-xs text-amber-400 font-medium">⚠️ DEMO DATA - For testing only</span>
        </div>
      )}
      
      {/* Match Header */}
      <div className="px-4 py-2 flex items-center justify-between border-b border-slate-700/50">
        <span className="text-xs text-slate-400 font-medium truncate max-w-[60%]">{match.series}</span>
        {/* Only show LIVE badge for real live matches, NOT mock data */}
        {match.status === 'live' && !isMock ? (
          <div className="flex items-center gap-1.5 bg-red-500/20 rounded-full px-2 py-0.5 animate-pulse">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span className="text-xs text-red-400 font-bold">LIVE</span>
          </div>
        ) : match.status === 'completed' ? (
          <Badge className="bg-slate-600/50 text-slate-300 text-xs">Completed</Badge>
        ) : (
          <div className="flex items-center gap-1.5 bg-slate-700/50 rounded-full px-2 py-0.5">
            <Clock className="h-3 w-3 text-yellow-400" />
            <span className="text-xs text-yellow-400 font-bold">
              {hoursLeft > 0 ? `${hoursLeft}h : ${minutesLeft}m` : `${minutesLeft}m`}
            </span>
          </div>
        )}
      </div>
      
      {/* Teams Section */}
      <div className="px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Team 1 */}
          <div className="flex items-center gap-3 flex-1">
            <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${teamColors[match.team1_short] || 'from-slate-500 to-slate-700'} flex items-center justify-center shadow-lg`}>
              <span className="text-lg font-black text-white drop-shadow-md">{match.team1_short?.[0] || '?'}</span>
            </div>
            <div>
              <p className="font-bold text-white text-base">{match.team1_short || 'TBD'}</p>
              <p className="text-xs text-slate-400 truncate max-w-[70px]">{match.team1}</p>
              {match.team1_score && (
                <p className="text-xs text-green-400 font-bold mt-1">{match.team1_score}</p>
              )}
            </div>
          </div>
          
          {/* VS Badge */}
          <div className="px-3">
            <span className="text-slate-500 font-medium text-sm">v</span>
          </div>
          
          {/* Team 2 */}
          <div className="flex items-center gap-3 flex-1 justify-end">
            <div className="text-right">
              <p className="font-bold text-white text-base">{match.team2_short || 'TBD'}</p>
              <p className="text-xs text-slate-400 truncate max-w-[70px]">{match.team2}</p>
              {match.team2_score && (
                <p className="text-xs text-green-400 font-bold mt-1">{match.team2_score}</p>
              )}
            </div>
            <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${teamColors[match.team2_short] || 'from-slate-500 to-slate-700'} flex items-center justify-center shadow-lg`}>
              <span className="text-lg font-black text-white drop-shadow-md">{match.team2_short?.[0] || '?'}</span>
            </div>
          </div>
        </div>
        
        {/* Status Text for live/completed matches */}
        {match.status_text && (
          <p className="text-xs text-center text-slate-400 mt-3 truncate">{match.status_text}</p>
        )}
      </div>
      
      {/* Bottom Action - Different for Live/Upcoming vs Completed */}
      <div className="bg-slate-900/80 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Trophy className="h-4 w-4 text-yellow-400" />
          <span className="text-white text-sm">{match.contests.length} Contests</span>
        </div>
        {match.status === 'completed' ? (
          <button className="bg-slate-600 hover:bg-slate-500 text-white font-bold text-sm px-5 py-2 rounded-full flex items-center gap-1 transition-all">
            View Results <ArrowRight className="h-4 w-4" />
          </button>
        ) : (
          <button className="bg-green-500 hover:bg-green-600 text-white font-bold text-sm px-5 py-2 rounded-full flex items-center gap-1 shadow-lg shadow-green-500/30 transition-all animate-pulseGlow ripple">
            Join <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
};

const Contests = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [matches, setMatches] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [activeTab, setActiveTab] = useState('live');
  const [loading, setLoading] = useState(true);
  const [dataSource, setDataSource] = useState('loading');
  const [apiNotice, setApiNotice] = useState(null);
  const [isMockData, setIsMockData] = useState(false);
  const [userParticipatedMatches, setUserParticipatedMatches] = useState([]);

  // Fetch user's participated matches (for filtering completed)
  useEffect(() => {
    const fetchUserParticipation = async () => {
      try {
        // Fetch user's predictions/participations
        const res = await api.get('/predictions/my');
        if (res.data && res.data.match_predictions) {
          const matchIds = res.data.match_predictions.map(p => p.match_id);
          setUserParticipatedMatches(matchIds);
        }
      } catch (err) {
        // User may not have any participations yet
        setUserParticipatedMatches([]);
      }
    };
    fetchUserParticipation();
  }, []);

  // Fetch REAL live matches from API - NO DATABASE FALLBACK
  useEffect(() => {
    const fetchLiveMatches = async () => {
      setLoading(true);
      try {
        const response = await api.get('/cricket/live');
        const liveData = response.data;
        
        // Set data source info
        setDataSource(liveData.source || 'unknown');
        setApiNotice(liveData.notice);
        
        // Check if mock data
        const mockCheck = liveData.is_mock || liveData.source === 'mock_data';
        setIsMockData(mockCheck);
        
        if (liveData.matches && liveData.matches.length > 0) {
          // Transform API data - keep exactly as returned
          const transformedMatches = liveData.matches.map(match => ({
            id: match.id,
            team1: match.team1,
            team1_short: match.team1_short,
            team2: match.team2,
            team2_short: match.team2_short,
            series: match.series || 'Cricket Match',
            venue: match.venue || 'TBD',
            start_time: match.start_time || new Date().toISOString(),
            status: match.status,
            status_text: match.status_text,
            team1_score: match.team1_score,
            team2_score: match.team2_score,
            is_mock: match.is_mock,
            is_icc_worldcup: match.is_icc_worldcup,
            is_ipl: match.is_ipl,
            source: match.source,
            priority: match.priority,
            contests: generateContests(match.id),
          }));
          
          setMatches(transformedMatches);
          
          // Show appropriate toast based on actual source
          if (mockCheck) {
            toast.warning('Demo mode - Live APIs unavailable');
          } else if (liveData.source === 'cricketdata_api') {
            toast.success(`${transformedMatches.length} live matches loaded!`);
          }
        } else {
          setMatches([]);
        }
      } catch (error) {
        console.error('Error fetching matches:', error);
        toast.error('Failed to load matches');
        setMatches([]);
        setIsMockData(true);
      } finally {
        setLoading(false);
      }
    };

    fetchLiveMatches();
    const interval = setInterval(fetchLiveMatches, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleJoinContest = (contest) => {
    // Navigate to V2 contest hub for this match
    if (selectedMatch) {
      navigate(`/contest-hub/${selectedMatch.id}`);
    }
  };

  const handleMatchSelect = (match) => {
    // For live matches, go directly to the live match prediction page
    if (match.status === 'live') {
      navigate(`/match/${match.id}`);
    } else {
      setSelectedMatch(match);
    }
  };

  const handleBackToMatches = () => {
    setSelectedMatch(null);
  };

  return (
    <div className="min-h-screen bg-black pb-28 md:pb-4">
      <Navbar />
      
      <div className="container mx-auto px-3 sm:px-4 py-4 max-w-2xl animate-fadeIn">
        {/* Header - Dream11 Style */}
        {!selectedMatch && (
          <div className="mb-5 animate-slideUp">
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <img src="/icon-48x48.png" alt="" className="h-6 w-6 rounded-lg" />
              {activeTab === 'live' ? 'Live Matches' : activeTab === 'completed' ? 'My Matches' : 'Upcoming Matches'}
            </h1>
            {!loading && (
              <p className="text-xs text-slate-400 mt-1">
                {(() => {
                  const filteredCount = activeTab === 'completed' 
                    ? matches.filter(m => m.status === 'completed' && userParticipatedMatches.includes(m.id)).length
                    : matches.filter(m => m.status === activeTab).length;
                  const isRealData = dataSource === 'cricketdata_api' || dataSource === 'cached_stale';
                  const dataLabel = isMockData ? 'Demo data' : isRealData ? 'Real-time data' : 'Loading...';
                  return `${filteredCount} ${filteredCount === 1 ? 'match' : 'matches'} • ${dataLabel}`;
                })()}
              </p>
            )}
            {/* Mock Data Warning Banner - only show if actually mock */}
            {isMockData && (
              <div className="mt-2 bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2">
                <p className="text-xs text-amber-400 font-medium">⚠️ DEMO MODE: Live APIs unavailable</p>
              </div>
            )}
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
            {/* Tabs - Dream11 Style */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-5">
              <TabsList className="bg-slate-900 border border-slate-800 w-full rounded-full p-1 h-auto">
                <TabsTrigger 
                  value="upcoming" 
                  className="flex-1 rounded-full py-2 text-sm data-[state=active]:bg-white data-[state=active]:text-black font-medium"
                >
                  Upcoming
                </TabsTrigger>
                <TabsTrigger 
                  value="live" 
                  className="flex-1 rounded-full py-2 text-sm data-[state=active]:bg-green-500 data-[state=active]:text-white font-medium"
                >
                  🔴 Live
                </TabsTrigger>
                <TabsTrigger 
                  value="completed" 
                  className="flex-1 rounded-full py-2 text-sm data-[state=active]:bg-slate-700 data-[state=active]:text-white font-medium"
                >
                  Completed
                </TabsTrigger>
              </TabsList>
            </Tabs>
            
            {/* Featured Contest Banner - Dream11 Style */}
            <div className="bg-gradient-to-r from-emerald-600/90 to-green-700/90 rounded-2xl p-4 mb-5 shadow-lg shadow-green-500/20">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-white/20 rounded-xl">
                  <Star className="h-6 w-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-white text-lg">Mega Contest</h3>
                  <p className="text-green-100 text-sm">🏆 5000 coins prize pool • FREE entry</p>
                </div>
                <span className="bg-yellow-400 text-black font-bold text-xs px-3 py-1 rounded-full">HOT</span>
              </div>
            </div>
            
            {/* Match List with staggered animation */}
            <div className="space-y-3 stagger-children">
              {loading ? (
                <div className="text-center py-12">
                  <Loader2 className="h-8 w-8 text-yellow-400 mx-auto mb-3 animate-spin" />
                  <p className="text-slate-400">Loading live matches...</p>
                </div>
              ) : (
                matches
                  .filter(match => {
                    if (activeTab === 'live') return match.status === 'live';
                    if (activeTab === 'upcoming') return match.status === 'upcoming';
                    // For completed: ONLY show matches user participated in
                    if (activeTab === 'completed') {
                      return match.status === 'completed' && userParticipatedMatches.includes(match.id);
                    }
                    return false;
                  })
                  // Sort: ICC World Cup first, then IPL, then others
                  .sort((a, b) => (a.priority || 10) - (b.priority || 10))
                  .map((match) => (
                    <MatchCard 
                      key={match.id} 
                      match={match} 
                      onSelect={handleMatchSelect}
                    />
                  ))
              )}
            </div>
            
            {!loading && matches.filter(match => {
              if (activeTab === 'live') return match.status === 'live';
              if (activeTab === 'upcoming') return match.status === 'upcoming';
              if (activeTab === 'completed') {
                return match.status === 'completed' && userParticipatedMatches.includes(match.id);
              }
              return false;
            }).length === 0 && (
              <div className="animate-fadeIn">
                {activeTab === 'live' ? (
                  <T20EmptyState navigate={navigate} />
                ) : activeTab === 'completed' ? (
                  <div className="text-center py-10">
                    <Trophy className="h-10 w-10 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-300 text-sm">You haven't participated in any matches yet</p>
                    <p className="text-slate-500 text-xs mt-1">Join live matches to see your history here</p>
                  </div>
                ) : (
                  <T20EmptyState navigate={navigate} />
                )}
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
                  {selectedMatch.status === 'completed' ? (
                    <Badge className="bg-slate-600 text-slate-300 text-xs">Match Ended</Badge>
                  ) : selectedMatch.status === 'live' ? (
                    <div className="flex items-center gap-1 text-xs text-red-400">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                      LIVE
                    </div>
                  ) : (
                    <div className="flex items-center gap-1 text-xs text-yellow-400">
                      <Clock className="h-3 w-3" />
                      Starting Soon
                    </div>
                  )}
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
                
                <div className="flex items-center justify-center gap-1 text-xs text-slate-300">
                  <MapPin className="h-3 w-3" />
                  {selectedMatch.venue}
                </div>
              </CardContent>
            </Card>
            
            {/* Create Team CTA - Only for upcoming/live matches */}
            {selectedMatch.status !== 'completed' && (
              <Card className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border-green-500/30 mb-4">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-white">Create Your Team</h3>
                      <p className="text-slate-300 text-sm">Pick 11 players and compete</p>
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
            )}
            
            {/* Match Ended Notice */}
            {selectedMatch.status === 'completed' && (
              <Card className="bg-slate-700/30 border-slate-600 mb-4">
                <CardContent className="p-4 text-center">
                  <p className="text-slate-300">This match has ended. Team creation is closed.</p>
                  {selectedMatch.team1_score && (
                    <p className="text-green-400 font-bold mt-2">
                      Final: {selectedMatch.team1_short} {selectedMatch.team1_score} vs {selectedMatch.team2_short} {selectedMatch.team2_score}
                    </p>
                  )}
                </CardContent>
              </Card>
            )}
            
            {/* Contests List */}
            <h3 className="text-white font-bold mb-3">Available Contests</h3>
            <div className="space-y-3">
              {selectedMatch.contests.map((contest) => (
                <ContestCard 
                  key={contest.id} 
                  contest={contest} 
                  onJoin={handleJoinContest}
                  matchStatus={selectedMatch.status}
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
