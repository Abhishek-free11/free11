import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  Spade, Heart, Diamond, Club, Users, Trophy, Coins, 
  Play, Plus, ChevronRight, Crown, Star, Zap, Copy
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';

// Game configurations with icons
const GAME_INFO = {
  rummy: {
    name: 'Rummy',
    description: 'Classic 13-card Indian Rummy',
    icon: Spade,
    color: 'from-red-500 to-pink-600',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    rewards: { win: 50, second: 20, participate: 5 }
  },
  teen_patti: {
    name: 'Teen Patti',
    description: '3-card Indian poker game',
    icon: Heart,
    color: 'from-purple-500 to-indigo-600',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    rewards: { win: 40, second: 15, participate: 5 }
  },
  poker: {
    name: 'Poker',
    description: 'Texas Hold\'em style',
    icon: Diamond,
    color: 'from-green-500 to-emerald-600',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
    rewards: { win: 60, second: 25, participate: 5 }
  }
};

const CardGames = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user, updateUser } = useAuth();
  const [selectedGame, setSelectedGame] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [myRooms, setMyRooms] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [showJoinCode, setShowJoinCode] = useState(false);
  const [joinCode, setJoinCode] = useState('');

  // Handle invite link with ?join= parameter
  useEffect(() => {
    const joinCodeFromUrl = searchParams.get('join');
    if (joinCodeFromUrl) {
      // Auto-populate and open join dialog
      setJoinCode(joinCodeFromUrl);
      setShowJoinCode(true);
      toast.info('Enter the room to join your friend\'s game!');
    }
  }, [searchParams]);

  useEffect(() => {
    fetchMyRooms();
  }, []);

  useEffect(() => {
    if (selectedGame) {
      fetchRooms(selectedGame);
      fetchStats(selectedGame);
    }
  }, [selectedGame]);

  const fetchMyRooms = async () => {
    try {
      const response = await api.get('/games/my-rooms');
      setMyRooms(response.data.rooms);
    } catch (error) {
      console.error('Error fetching my rooms:', error);
    }
  };

  const fetchRooms = async (gameType) => {
    try {
      setLoading(true);
      const response = await api.get(`/games/${gameType}/rooms`);
      setRooms(response.data.rooms);
    } catch (error) {
      console.error('Error fetching rooms:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async (gameType) => {
    try {
      const response = await api.get(`/games/${gameType}/stats/my`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleQuickPlay = async (gameType) => {
    try {
      setLoading(true);
      const response = await api.post(`/games/${gameType}/quick-play`);
      toast.success(response.data.message);
      navigate(`/games/${gameType}/room/${response.data.room.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start game');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRoom = async (gameType, isPrivate = false) => {
    try {
      const response = await api.post(`/games/${gameType}/rooms/create`, {
        game_type: gameType,
        name: `${GAME_INFO[gameType].name} Room`,
        max_players: 4,
        is_private: isPrivate
      });
      
      if (isPrivate && response.data.room_code) {
        toast.success(`Room created! Code: ${response.data.room_code}`);
        navigator.clipboard.writeText(response.data.room_code);
      } else {
        toast.success('Room created!');
      }
      
      navigate(`/games/${gameType}/room/${response.data.room.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create room');
    }
  };

  const handleJoinByCode = async () => {
    if (!joinCode.trim()) {
      toast.error('Please enter a room code');
      return;
    }
    
    try {
      const response = await api.post('/games/rooms/join-by-code', null, {
        params: { code: joinCode.toUpperCase() }
      });
      toast.success(response.data.message);
      const room = response.data.room;
      navigate(`/games/${room.game_type}/room/${room.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid room code');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 pb-20 md:pb-0">
      <Navbar />
      
      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-6 max-w-6xl">
        {/* Header */}
        <div className="mb-4 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2 sm:gap-3">
            <Club className="h-6 w-6 sm:h-8 sm:w-8 text-yellow-400" />
            Card Games
          </h1>
          <p className="text-slate-300 mt-1 sm:mt-2 text-sm sm:text-base">
            Play classic card games and earn coins. FREE to play!
          </p>
        </div>

        {/* Join by Code */}
        {showJoinCode ? (
          <Card className="bg-slate-800/70 border-slate-700 mb-6">
            <CardContent className="p-4 flex gap-3">
              <Input
                placeholder="Enter room code"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                className="bg-slate-800 border-slate-700 text-white"
                maxLength={6}
              />
              <Button onClick={handleJoinByCode} className="bg-green-500 hover:bg-green-600">
                Join
              </Button>
              <Button variant="outline" onClick={() => setShowJoinCode(false)}>
                Cancel
              </Button>
            </CardContent>
          </Card>
        ) : (
          <Button 
            variant="outline" 
            onClick={() => setShowJoinCode(true)}
            className="mb-6"
          >
            <Plus className="h-4 w-4 mr-2" />
            Join Private Room
          </Button>
        )}

        {/* Active Rooms */}
        {myRooms.length > 0 && (
          <Card className="bg-yellow-500/10 border-yellow-500/30 mb-6">
            <CardHeader className="pb-2">
              <CardTitle className="text-yellow-400 text-lg">Your Active Games</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {myRooms.map((room) => (
                <Button
                  key={room.id}
                  variant="outline"
                  className="w-full justify-between border-yellow-500/30 hover:bg-yellow-500/10"
                  onClick={() => navigate(`/games/${room.game_type}/room/${room.id}`)}
                >
                  <span className="flex items-center gap-2">
                    {React.createElement(GAME_INFO[room.game_type]?.icon || Spade, { className: "h-4 w-4" })}
                    {room.name}
                    <Badge variant="outline" className="text-xs">
                      {room.status === 'waiting' ? 'Waiting' : 'In Progress'}
                    </Badge>
                  </span>
                  <span className="flex items-center gap-2 text-slate-300">
                    <Users className="h-4 w-4" />
                    {room.player_ids?.length || 1}/{room.max_players}
                  </span>
                </Button>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Game Selection */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6 sm:mb-8">
          {Object.entries(GAME_INFO).map(([gameType, info]) => {
            const Icon = info.icon;
            const isSelected = selectedGame === gameType;
            
            return (
              <Card 
                key={gameType}
                className={`cursor-pointer transition-all ${info.bgColor} ${info.borderColor} ${
                  isSelected ? 'ring-2 ring-yellow-400' : ''
                }`}
                onClick={() => setSelectedGame(gameType)}
              >
                <CardContent className="p-4 sm:p-6 text-center">
                  <div className={`w-12 h-12 sm:w-16 sm:h-16 mx-auto rounded-full bg-gradient-to-br ${info.color} flex items-center justify-center mb-3 sm:mb-4`}>
                    <Icon className="h-6 w-6 sm:h-8 sm:w-8 text-white" />
                  </div>
                  <h3 className="text-lg sm:text-xl font-bold text-white mb-1 sm:mb-2">{info.name}</h3>
                  <p className="text-slate-300 text-xs sm:text-sm mb-3 sm:mb-4">{info.description}</p>
                  <div className="flex justify-center gap-2">
                    <Badge className="bg-green-500/20 text-green-400">FREE Entry</Badge>
                    <Badge className="bg-yellow-500/20 text-yellow-400">
                      <Coins className="h-3 w-3 mr-1" />
                      Win {info.rewards.win}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Selected Game Actions */}
        {selectedGame && (
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Button
                onClick={() => handleQuickPlay(selectedGame)}
                disabled={loading}
                className={`h-16 bg-gradient-to-r ${GAME_INFO[selectedGame].color} text-white font-bold`}
              >
                <Zap className="h-5 w-5 mr-2" />
                Quick Play
              </Button>
              <Button
                onClick={() => handleCreateRoom(selectedGame, false)}
                variant="outline"
                className="h-16"
              >
                <Plus className="h-5 w-5 mr-2" />
                Create Public Room
              </Button>
              <Button
                onClick={() => handleCreateRoom(selectedGame, true)}
                variant="outline"
                className="h-16"
              >
                <Users className="h-5 w-5 mr-2" />
                Create Private Room
              </Button>
            </div>

            {/* My Stats */}
            <Card className="bg-slate-800/70 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-400" />
                  Your {GAME_INFO[selectedGame].name} Stats
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-white">{stats.games_played || 0}</p>
                    <p className="text-sm text-slate-300">Games Played</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-400">{stats.games_won || 0}</p>
                    <p className="text-sm text-slate-300">Games Won</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-yellow-400">{stats.win_rate || 0}%</p>
                    <p className="text-sm text-slate-300">Win Rate</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-purple-400">{stats.total_coins_earned || 0}</p>
                    <p className="text-sm text-slate-300">Coins Earned</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Available Rooms */}
            <Card className="bg-slate-800/70 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Users className="h-5 w-5 text-blue-400" />
                  Available Rooms
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin h-8 w-8 border-2 border-yellow-400 border-t-transparent rounded-full mx-auto" />
                  </div>
                ) : rooms.length === 0 ? (
                  <div className="text-center py-8 text-slate-300">
                    <p>No rooms available. Create one or use Quick Play!</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {rooms.map((room) => (
                      <Button
                        key={room.id}
                        variant="outline"
                        className="w-full justify-between"
                        onClick={() => navigate(`/games/${selectedGame}/room/${room.id}`)}
                      >
                        <span>{room.name}</span>
                        <span className="flex items-center gap-2 text-slate-300">
                          <Users className="h-4 w-4" />
                          {room.current_players}/{room.max_players}
                          <ChevronRight className="h-4 w-4" />
                        </span>
                      </Button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Rewards Info */}
            <Card className="bg-slate-800/70 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Coins className="h-5 w-5 text-yellow-400" />
                  Coin Rewards
                </CardTitle>
                <CardDescription className="text-slate-300">
                  All games are FREE to play. Earn coins by participating!
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-yellow-500/10 rounded-lg p-4 text-center">
                    <Crown className="h-6 w-6 text-yellow-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-yellow-400">
                      {GAME_INFO[selectedGame].rewards.win}
                    </p>
                    <p className="text-sm text-slate-300">1st Place</p>
                  </div>
                  <div className="bg-slate-500/10 rounded-lg p-4 text-center">
                    <Star className="h-6 w-6 text-slate-300 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-slate-300">
                      {GAME_INFO[selectedGame].rewards.second}
                    </p>
                    <p className="text-sm text-slate-300">2nd Place</p>
                  </div>
                  <div className="bg-green-500/10 rounded-lg p-4 text-center">
                    <Play className="h-6 w-6 text-green-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-green-400">
                      {GAME_INFO[selectedGame].rewards.participate}
                    </p>
                    <p className="text-sm text-slate-300">Participate</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* How It Works */}
        {!selectedGame && (
          <Card className="bg-slate-800/70 border-slate-700">
            <CardHeader>
              <CardTitle className="text-white">How It Works</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-yellow-400 font-bold">1</span>
                </div>
                <div>
                  <h4 className="font-semibold text-white">Select a Game</h4>
                  <p className="text-slate-300 text-sm">Choose from Rummy, Teen Patti, or Poker</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-yellow-400 font-bold">2</span>
                </div>
                <div>
                  <h4 className="font-semibold text-white">Join or Create a Room</h4>
                  <p className="text-slate-300 text-sm">Play with random players or invite friends</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-yellow-400 font-bold">3</span>
                </div>
                <div>
                  <h4 className="font-semibold text-white">Play & Earn</h4>
                  <p className="text-slate-300 text-sm">Win coins based on your performance - no buy-ins!</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default CardGames;
