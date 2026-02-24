import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Spade, Heart, Diamond, Club, Users, Trophy, Coins, 
  Play, ArrowLeft, Crown, Copy, Share2, CheckCircle
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import confetti from 'canvas-confetti';

const GAME_INFO = {
  rummy: { name: 'Rummy', icon: Spade, color: 'from-red-500 to-pink-600' },
  teen_patti: { name: 'Teen Patti', icon: Heart, color: 'from-purple-500 to-indigo-600' },
  poker: { name: 'Poker', icon: Diamond, color: 'from-green-500 to-emerald-600' }
};

const GameRoom = () => {
  const navigate = useNavigate();
  const { gameType, roomId } = useParams();
  const { user, updateUser } = useAuth();
  
  const [room, setRoom] = useState(null);
  const [players, setPlayers] = useState([]);
  const [gameResult, setGameResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  const gameInfo = GAME_INFO[gameType] || GAME_INFO.rummy;
  const Icon = gameInfo.icon;

  useEffect(() => {
    fetchRoomData();
    // Poll for updates
    const interval = setInterval(fetchRoomData, 3000);
    return () => clearInterval(interval);
  }, [roomId]);

  const fetchRoomData = async () => {
    try {
      // In a real app, we'd have a dedicated endpoint
      const roomsRes = await api.get('/games/my-rooms');
      const foundRoom = roomsRes.data.rooms.find(r => r.id === roomId);
      
      if (foundRoom) {
        setRoom(foundRoom);
        
        // Fetch player details
        const playerDetails = [];
        for (const playerId of foundRoom.player_ids || []) {
          playerDetails.push({
            id: playerId,
            name: playerId === user?.id ? user.name : `Player ${playerDetails.length + 1}`,
            isHost: playerId === foundRoom.host_id,
            isMe: playerId === user?.id
          });
        }
        setPlayers(playerDetails);
      }
    } catch (error) {
      console.error('Error fetching room:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartGame = async () => {
    try {
      setStarting(true);
      await api.post(`/games/${gameType}/rooms/${roomId}/start`);
      toast.success('Game started!');
      fetchRoomData();
      
      // Simulate game completion after delay (demo)
      setTimeout(async () => {
        try {
          const result = await api.post(`/games/${gameType}/rooms/${roomId}/complete`);
          setGameResult(result.data);
          
          // Check if user won
          const myResult = result.data.results.find(r => r.user_id === user?.id);
          if (myResult) {
            if (myResult.rank === 1) {
              confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#fbbf24', '#f59e0b', '#d97706']
              });
              toast.success(`🏆 You won! +${myResult.coins_earned} coins!`);
            } else {
              toast.info(`You placed #${myResult.rank}. +${myResult.coins_earned} coins`);
            }
            updateUser({ coins_balance: (user?.coins_balance || 0) + myResult.coins_earned });
          }
        } catch (error) {
          console.error('Error completing game:', error);
        }
      }, 5000);
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start game');
    } finally {
      setStarting(false);
    }
  };

  const copyRoomCode = () => {
    if (room?.room_code) {
      navigator.clipboard.writeText(room.room_code);
      toast.success('Room code copied!');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-yellow-400 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!room) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <Card className="bg-slate-900/50 border-slate-800 p-8 text-center">
          <p className="text-slate-400 mb-4">Room not found or game ended</p>
          <Button onClick={() => navigate('/games')}>Back to Games</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className={`bg-gradient-to-r ${gameInfo.color} py-6`}>
        <div className="container mx-auto px-4 max-w-4xl">
          <div className="flex items-center justify-between">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/games')}
              className="text-white hover:bg-white/20"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div className="text-center">
              <h1 className="text-2xl font-bold flex items-center justify-center gap-2">
                <Icon className="h-6 w-6" />
                {room.name}
              </h1>
              <Badge className="mt-1 bg-white/20">
                {room.status === 'waiting' ? 'Waiting for players' : 
                 room.status === 'playing' ? 'Game in progress' : 'Completed'}
              </Badge>
            </div>
            <div className="w-20" /> {/* Spacer */}
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6 max-w-4xl space-y-6">
        {/* Room Code (if private) */}
        {room.is_private && room.room_code && (
          <Card className="bg-yellow-500/10 border-yellow-500/30">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Room Code</p>
                <p className="text-2xl font-bold text-yellow-400">{room.room_code}</p>
              </div>
              <Button onClick={copyRoomCode} variant="outline" className="border-yellow-500/50">
                <Copy className="h-4 w-4 mr-2" />
                Copy
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Players */}
        <Card className="bg-slate-900/50 border-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-400" />
              Players ({players.length}/{room.max_players})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {players.map((player, index) => (
                <div 
                  key={player.id}
                  className={`bg-slate-800/50 rounded-lg p-4 text-center ${
                    player.isMe ? 'ring-2 ring-yellow-400' : ''
                  }`}
                >
                  <div className={`w-12 h-12 mx-auto rounded-full bg-gradient-to-br ${gameInfo.color} flex items-center justify-center mb-2`}>
                    {player.isHost ? (
                      <Crown className="h-6 w-6 text-white" />
                    ) : (
                      <span className="text-white font-bold">{index + 1}</span>
                    )}
                  </div>
                  <p className="font-medium truncate">{player.name}</p>
                  {player.isHost && (
                    <Badge className="mt-1 bg-yellow-500/20 text-yellow-400 text-xs">Host</Badge>
                  )}
                  {player.isMe && (
                    <Badge className="mt-1 bg-blue-500/20 text-blue-400 text-xs">You</Badge>
                  )}
                </div>
              ))}
              
              {/* Empty slots */}
              {Array.from({ length: room.max_players - players.length }).map((_, i) => (
                <div key={`empty-${i}`} className="bg-slate-800/30 rounded-lg p-4 text-center border-2 border-dashed border-slate-700">
                  <div className="w-12 h-12 mx-auto rounded-full bg-slate-700/50 flex items-center justify-center mb-2">
                    <Users className="h-6 w-6 text-slate-600" />
                  </div>
                  <p className="text-slate-600">Waiting...</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Game Status / Results */}
        {gameResult ? (
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-400" />
                Game Results
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {gameResult.results.map((result, index) => (
                  <div 
                    key={result.user_id}
                    className={`flex items-center justify-between p-3 rounded-lg ${
                      index === 0 ? 'bg-yellow-500/20' : 'bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className={`text-2xl font-bold ${
                        index === 0 ? 'text-yellow-400' : 'text-slate-400'
                      }`}>#{result.rank}</span>
                      <div>
                        <p className="font-medium">
                          {result.user_id === user?.id ? 'You' : `Player ${index + 1}`}
                        </p>
                        <p className="text-sm text-slate-400">{result.hand}</p>
                      </div>
                    </div>
                    <Badge className="bg-yellow-500/20 text-yellow-400">
                      <Coins className="h-3 w-3 mr-1" />
                      +{result.coins_earned}
                    </Badge>
                  </div>
                ))}
              </div>
              
              <Button 
                onClick={() => navigate('/games')}
                className="w-full mt-6 bg-gradient-to-r from-yellow-500 to-amber-600"
              >
                Play Again
              </Button>
            </CardContent>
          </Card>
        ) : room.status === 'playing' ? (
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="p-8 text-center">
              <div className="animate-pulse">
                <Icon className="h-16 w-16 mx-auto text-yellow-400 mb-4" />
                <h3 className="text-xl font-bold mb-2">Game in Progress</h3>
                <p className="text-slate-400">Simulating gameplay...</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          /* Start Game Button (host only) */
          room.host_id === user?.id && (
            <Card className="bg-slate-900/50 border-slate-800">
              <CardContent className="p-6">
                <Button
                  onClick={handleStartGame}
                  disabled={players.length < 2 || starting}
                  className={`w-full h-14 bg-gradient-to-r ${gameInfo.color} text-white font-bold text-lg`}
                >
                  {starting ? (
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full mr-2" />
                  ) : (
                    <Play className="h-5 w-5 mr-2" />
                  )}
                  {players.length < 2 ? 'Need at least 2 players' : 'Start Game'}
                </Button>
                
                {players.length < 2 && (
                  <p className="text-center text-slate-400 mt-3 text-sm">
                    Share the room code with friends to invite them!
                  </p>
                )}
              </CardContent>
            </Card>
          )
        )}

        {/* Waiting Message (non-host) */}
        {room.status === 'waiting' && room.host_id !== user?.id && (
          <Card className="bg-slate-900/50 border-slate-800">
            <CardContent className="p-8 text-center">
              <div className="animate-pulse">
                <Users className="h-12 w-12 mx-auto text-blue-400 mb-4" />
                <p className="text-slate-400">Waiting for host to start the game...</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default GameRoom;
