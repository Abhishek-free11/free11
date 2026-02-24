import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  Spade, Heart, Diamond, Club, Users, Trophy, Coins, 
  Play, ArrowLeft, Crown, Copy, Send, Eye, EyeOff,
  HandMetal, XCircle, Check, RefreshCw, MessageSquare,
  Share2, UserPlus, Link2
} from 'lucide-react';
import { toast } from 'sonner';
import api from '../utils/api';
import confetti from 'canvas-confetti';

const GAME_INFO = {
  rummy: { name: 'Rummy', icon: Spade, color: 'from-red-500 to-pink-600', bgColor: 'bg-red-500' },
  teen_patti: { name: 'Teen Patti', icon: Heart, color: 'from-purple-500 to-indigo-600', bgColor: 'bg-purple-500' },
  poker: { name: 'Poker', icon: Diamond, color: 'from-green-500 to-emerald-600', bgColor: 'bg-green-500' }
};

// Card component for displaying playing cards
const PlayingCard = ({ card, hidden = false, selected = false, onClick, small = false }) => {
  const suitSymbols = {
    hearts: '♥',
    diamonds: '♦',
    clubs: '♣',
    spades: '♠'
  };
  
  const suitColors = {
    hearts: 'text-red-500',
    diamonds: 'text-red-500',
    clubs: 'text-slate-900',
    spades: 'text-slate-900'
  };
  
  if (hidden || card?.hidden) {
    return (
      <div 
        className={`${small ? 'w-10 h-14' : 'w-16 h-22'} bg-gradient-to-br from-blue-600 to-blue-800 rounded-lg border-2 border-blue-400 flex items-center justify-center shadow-lg`}
        onClick={onClick}
      >
        <div className="text-blue-300 text-xl font-bold">?</div>
      </div>
    );
  }
  
  return (
    <div 
      className={`${small ? 'w-10 h-14' : 'w-16 h-22'} bg-white rounded-lg border-2 ${selected ? 'border-yellow-400 ring-2 ring-yellow-400' : 'border-slate-300'} flex flex-col items-center justify-center shadow-lg cursor-pointer hover:scale-105 transition-transform`}
      onClick={onClick}
    >
      <span className={`${small ? 'text-sm' : 'text-lg'} font-bold ${suitColors[card?.suit] || 'text-slate-900'}`}>
        {card?.rank || '?'}
      </span>
      <span className={`${small ? 'text-lg' : 'text-2xl'} ${suitColors[card?.suit] || 'text-slate-900'}`}>
        {suitSymbols[card?.suit] || '?'}
      </span>
    </div>
  );
};

// Player seat component
const PlayerSeat = ({ player, isCurrentTurn, isMe, isFolded, hasSeen, gameType, cards }) => {
  return (
    <div className={`relative p-3 rounded-xl transition-all ${
      isCurrentTurn ? 'bg-yellow-500/20 ring-2 ring-yellow-400' : 'bg-slate-800/50'
    } ${isFolded ? 'opacity-50' : ''}`}>
      <div className="flex items-center gap-3">
        <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${
          isMe ? 'from-yellow-400 to-amber-500' : 'from-slate-500 to-slate-600'
        } flex items-center justify-center`}>
          {player.isHost ? (
            <Crown className="h-5 w-5 text-white" />
          ) : (
            <span className="text-white font-bold text-sm">{player.name?.[0]?.toUpperCase() || 'P'}</span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-white truncate">{player.name}</p>
          <div className="flex gap-1 mt-1">
            {isMe && <Badge className="bg-blue-500/30 text-blue-300 text-xs">You</Badge>}
            {player.isHost && <Badge className="bg-yellow-500/30 text-yellow-300 text-xs">Host</Badge>}
            {hasSeen && gameType === 'teen_patti' && (
              <Badge className="bg-green-500/30 text-green-300 text-xs">
                <Eye className="h-3 w-3 mr-1" />Seen
              </Badge>
            )}
            {isFolded && <Badge className="bg-red-500/30 text-red-300 text-xs">Folded</Badge>}
          </div>
        </div>
      </div>
      
      {/* Player's cards (if visible) */}
      {cards && cards.length > 0 && (
        <div className="flex gap-1 mt-2 justify-center">
          {cards.map((card, idx) => (
            <PlayingCard key={idx} card={card} hidden={card?.hidden} small />
          ))}
        </div>
      )}
    </div>
  );
};

const GameRoom = () => {
  const navigate = useNavigate();
  const { gameType, roomId } = useParams();
  const { user, updateUser } = useAuth();
  
  // WebSocket state
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  
  // Game state
  const [connected, setConnected] = useState(false);
  const [room, setRoom] = useState(null);
  const [players, setPlayers] = useState([]);
  const [gameState, setGameState] = useState(null);
  const [gameResult, setGameResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [selectedCards, setSelectedCards] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [showChat, setShowChat] = useState(false);
  
  const gameInfo = GAME_INFO[gameType] || GAME_INFO.rummy;
  const Icon = gameInfo.icon;
  
  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    
    const backendUrl = process.env.REACT_APP_BACKEND_URL || '';
    const wsUrl = backendUrl.replace('https://', 'wss://').replace('http://', 'ws://');
    const token = localStorage.getItem('token');
    
    const wsEndpoint = `${wsUrl}/api/games/ws/${roomId}?token=${token}&player_id=${user?.id}&player_name=${encodeURIComponent(user?.name || 'Player')}`;
    
    ws.current = new WebSocket(wsEndpoint);
    
    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      setLoading(false);
    };
    
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };
    
    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      
      // Attempt to reconnect after 3 seconds
      reconnectTimeout.current = setTimeout(() => {
        if (document.visibilityState === 'visible') {
          connectWebSocket();
        }
      }, 3000);
    };
    
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [roomId, user?.id, user?.name]);
  
  // Handle incoming WebSocket messages
  const handleWebSocketMessage = (data) => {
    console.log('WS Message:', data.type, data);
    
    switch (data.type) {
      case 'connected':
        setRoom({
          id: data.room_id,
          game_type: data.game_type,
          host_id: data.is_host ? user?.id : null,
          status: data.status
        });
        setPlayers(data.players.map(p => ({
          ...p,
          isHost: p.id === data.players[0]?.id,
          isMe: p.id === user?.id
        })));
        break;
        
      case 'player_joined':
        setPlayers(prev => {
          if (prev.find(p => p.id === data.player_id)) return prev;
          return [...prev, {
            id: data.player_id,
            name: data.player_name,
            isMe: data.player_id === user?.id
          }];
        });
        toast.info(`${data.player_name} joined the game`);
        break;
        
      case 'player_left':
        setPlayers(prev => prev.filter(p => p.id !== data.player_id));
        toast.info(`${data.player_name} left the game`);
        break;
        
      case 'game_started':
        setRoom(prev => ({ ...prev, status: 'playing' }));
        toast.success('Game started!');
        break;
        
      case 'game_state':
        setGameState(data);
        break;
        
      case 'player_action':
        // Show action toast
        if (data.player_id !== user?.id) {
          const actionText = {
            fold: 'folded',
            call: `called ${data.amount}`,
            raise: `raised to ${data.amount}`,
            check: 'checked',
            seen: 'saw their cards',
            show: 'requested show',
            draw_deck: 'drew from deck',
            draw_discard: 'picked from discard',
            discard: 'discarded a card',
            declare: 'declared!'
          };
          toast.info(`${data.player_name} ${actionText[data.action] || data.action}`);
        }
        break;
        
      case 'game_complete':
        setGameResult(data);
        setRoom(prev => ({ ...prev, status: 'completed' }));
        
        // Check if user won
        const myReward = data.rewards?.find(r => r.user_id === user?.id);
        if (myReward) {
          if (myReward.rank === 1) {
            confetti({
              particleCount: 150,
              spread: 70,
              origin: { y: 0.6 },
              colors: ['#fbbf24', '#f59e0b', '#d97706']
            });
            toast.success(`🏆 You won! +${myReward.coins} coins!`);
          } else {
            toast.info(`You placed #${myReward.rank}. +${myReward.coins} coins`);
          }
          updateUser({ coins_balance: (user?.coins_balance || 0) + myReward.coins });
        }
        break;
        
      case 'chat':
        setChatMessages(prev => [...prev.slice(-50), {
          player_id: data.player_id,
          player_name: data.player_name,
          message: data.message,
          isMe: data.player_id === user?.id
        }]);
        break;
        
      case 'error':
        toast.error(data.message || 'An error occurred');
        break;
        
      default:
        console.log('Unknown message type:', data.type);
    }
  };
  
  // Send WebSocket message
  const sendMessage = (message) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      toast.error('Connection lost. Reconnecting...');
      connectWebSocket();
    }
  };
  
  // Game actions
  const startGame = () => {
    setStarting(true);
    sendMessage({ type: 'start_game' });
    setTimeout(() => setStarting(false), 1000);
  };
  
  const performAction = (action, extra = {}) => {
    sendMessage({ type: 'action', action, ...extra });
  };
  
  const sendChat = () => {
    if (!chatInput.trim()) return;
    sendMessage({ type: 'chat', message: chatInput.trim() });
    setChatInput('');
  };
  
  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connectWebSocket]);
  
  // Fetch room data on mount (for initial state)
  useEffect(() => {
    const fetchRoomData = async () => {
      try {
        const response = await api.get(`/games/${gameType}/rooms/${roomId}/state`);
        if (response.data.room) {
          setRoom(response.data.room);
        }
      } catch (error) {
        console.error('Error fetching room:', error);
      }
    };
    
    fetchRoomData();
  }, [gameType, roomId]);
  
  // Copy room code
  const copyRoomCode = () => {
    if (room?.room_code) {
      navigator.clipboard.writeText(room.room_code);
      toast.success('Room code copied!');
    }
  };
  
  // Generate invite link
  const getInviteLink = () => {
    const baseUrl = window.location.origin;
    const code = room?.room_code || roomId;
    return `${baseUrl}/games?join=${code}`;
  };
  
  // Share invite link
  const shareInvite = async () => {
    const inviteLink = getInviteLink();
    const gameName = gameInfo.name;
    const shareText = `Join my ${gameName} game on FREE11! 🎴\n\n${room?.room_code ? `Room Code: ${room.room_code}\n` : ''}Click to join: ${inviteLink}`;
    
    // Try native share API first (mobile)
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Join ${gameName} on FREE11`,
          text: shareText,
          url: inviteLink
        });
        toast.success('Invite shared!');
        return;
      } catch (err) {
        // User cancelled or share failed, fall back to clipboard
        if (err.name !== 'AbortError') {
          console.log('Share failed, copying to clipboard');
        }
      }
    }
    
    // Fallback: copy to clipboard
    try {
      await navigator.clipboard.writeText(shareText);
      toast.success('Invite link copied! Share it with your friends.');
    } catch (err) {
      toast.error('Failed to copy invite link');
    }
  };
  
  // Copy just the invite link
  const copyInviteLink = () => {
    const inviteLink = getInviteLink();
    navigator.clipboard.writeText(inviteLink);
    toast.success('Invite link copied!');
  };
  
  // Determine if it's user's turn
  const isMyTurn = gameState?.current_player === user?.id;
  const myHand = gameState?.hands?.[user?.id] || [];
  const canCheck = gameType === 'poker' && gameState?.current_bet === (gameState?.player_bets?.[user?.id] || 0);
  
  if (loading && !connected) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-yellow-400 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400">Connecting to game...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className={`bg-gradient-to-r ${gameInfo.color} py-4`}>
        <div className="container mx-auto px-4 max-w-5xl">
          <div className="flex items-center justify-between">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/games')}
              className="text-white hover:bg-white/20"
              data-testid="back-button"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <div className="text-center">
              <h1 className="text-xl font-bold flex items-center justify-center gap-2">
                <Icon className="h-5 w-5" />
                {gameInfo.name}
              </h1>
              <Badge className={`mt-1 ${connected ? 'bg-green-500/30 text-green-300' : 'bg-red-500/30 text-red-300'}`}>
                {connected ? 'Connected' : 'Reconnecting...'}
              </Badge>
            </div>
            <Button
              variant="ghost"
              onClick={() => setShowChat(!showChat)}
              className="text-white hover:bg-white/20"
              data-testid="chat-toggle"
            >
              <MessageSquare className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
      
      <div className="container mx-auto px-4 py-4 max-w-5xl">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Main Game Area */}
          <div className="lg:col-span-2 space-y-4">
            {/* Room Code (if private) */}
            {room?.room_code && (
              <Card className="bg-yellow-500/10 border-yellow-500/30">
                <CardContent className="p-3 flex items-center justify-between">
                  <div>
                    <p className="text-xs text-slate-400">Room Code</p>
                    <p className="text-xl font-bold text-yellow-400">{room.room_code}</p>
                  </div>
                  <Button onClick={copyRoomCode} variant="outline" size="sm" className="border-yellow-500/50">
                    <Copy className="h-4 w-4 mr-1" />
                    Copy
                  </Button>
                </CardContent>
              </Card>
            )}
            
            {/* Game Table */}
            {gameState && !gameResult ? (
              <Card className="bg-slate-900/80 border-slate-700">
                <CardContent className="p-4">
                  {/* Game Info */}
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <p className="text-sm text-slate-400">
                        {gameType === 'poker' && `Phase: ${gameState.phase?.toUpperCase()}`}
                        {gameType === 'teen_patti' && `Bet: ${gameState.current_bet}`}
                        {gameType === 'rummy' && `Deck: ${gameState.deck_size} cards`}
                      </p>
                    </div>
                    <Badge className="bg-yellow-500/20 text-yellow-400 text-lg px-3 py-1">
                      <Coins className="h-4 w-4 mr-1" />
                      Pot: {gameState.pot || 0}
                    </Badge>
                  </div>
                  
                  {/* Community Cards (Poker) */}
                  {gameType === 'poker' && gameState.community_cards?.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs text-slate-400 mb-2">Community Cards</p>
                      <div className="flex gap-2 justify-center">
                        {gameState.community_cards.map((card, idx) => (
                          <PlayingCard key={idx} card={card} />
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Discard Pile (Rummy) */}
                  {gameType === 'rummy' && (
                    <div className="flex justify-center gap-8 mb-4">
                      <div className="text-center">
                        <p className="text-xs text-slate-400 mb-2">Draw Pile</p>
                        <PlayingCard hidden />
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-slate-400 mb-2">Discard</p>
                        {gameState.discard_top ? (
                          <PlayingCard card={gameState.discard_top} />
                        ) : (
                          <div className="w-16 h-22 border-2 border-dashed border-slate-600 rounded-lg" />
                        )}
                      </div>
                    </div>
                  )}
                  
                  {/* Current Turn Indicator */}
                  {gameState.current_player && (
                    <div className={`text-center py-2 px-4 rounded-lg mb-4 ${
                      isMyTurn ? 'bg-yellow-500/20 text-yellow-400' : 'bg-slate-700/50 text-slate-400'
                    }`}>
                      {isMyTurn ? "🎯 Your Turn!" : `Waiting for ${gameState.player_names?.[gameState.current_player] || 'opponent'}...`}
                    </div>
                  )}
                  
                  {/* My Hand */}
                  <div className="mb-4">
                    <p className="text-sm text-slate-400 mb-2">Your Hand</p>
                    <div className="flex gap-2 justify-center flex-wrap">
                      {myHand.map((card, idx) => (
                        <PlayingCard 
                          key={idx} 
                          card={card} 
                          hidden={card?.hidden}
                          selected={selectedCards.includes(idx)}
                          onClick={() => {
                            if (gameType === 'rummy') {
                              setSelectedCards(prev => 
                                prev.includes(idx) 
                                  ? prev.filter(i => i !== idx)
                                  : [...prev, idx]
                              );
                            }
                          }}
                        />
                      ))}
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  {isMyTurn && (
                    <div className="flex flex-wrap gap-2 justify-center">
                      {/* Teen Patti Actions */}
                      {gameType === 'teen_patti' && (
                        <>
                          {!gameState.seen_players?.includes(user?.id) && (
                            <Button
                              onClick={() => performAction('see')}
                              className="bg-blue-500 hover:bg-blue-600"
                              data-testid="see-cards-btn"
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              See Cards
                            </Button>
                          )}
                          <Button
                            onClick={() => performAction('call')}
                            className="bg-green-500 hover:bg-green-600"
                            data-testid="call-btn"
                          >
                            <Check className="h-4 w-4 mr-2" />
                            Call ({gameState.seen_players?.includes(user?.id) ? gameState.current_bet : Math.floor(gameState.current_bet / 2)})
                          </Button>
                          <Button
                            onClick={() => performAction('raise', { amount: gameState.current_bet * 2 })}
                            className="bg-yellow-500 hover:bg-yellow-600"
                            data-testid="raise-btn"
                          >
                            Raise
                          </Button>
                          {gameState.active_players?.length === 2 && (
                            <Button
                              onClick={() => performAction('show')}
                              className="bg-purple-500 hover:bg-purple-600"
                              data-testid="show-btn"
                            >
                              <HandMetal className="h-4 w-4 mr-2" />
                              Show
                            </Button>
                          )}
                          <Button
                            onClick={() => performAction('fold')}
                            variant="outline"
                            className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                            data-testid="fold-btn"
                          >
                            <XCircle className="h-4 w-4 mr-2" />
                            Fold
                          </Button>
                        </>
                      )}
                      
                      {/* Poker Actions */}
                      {gameType === 'poker' && (
                        <>
                          {canCheck && (
                            <Button
                              onClick={() => performAction('check')}
                              className="bg-blue-500 hover:bg-blue-600"
                              data-testid="check-btn"
                            >
                              <Check className="h-4 w-4 mr-2" />
                              Check
                            </Button>
                          )}
                          {!canCheck && (
                            <Button
                              onClick={() => performAction('call')}
                              className="bg-green-500 hover:bg-green-600"
                              data-testid="call-btn"
                            >
                              <Check className="h-4 w-4 mr-2" />
                              Call
                            </Button>
                          )}
                          <Button
                            onClick={() => performAction('raise', { amount: 20 })}
                            className="bg-yellow-500 hover:bg-yellow-600"
                            data-testid="raise-btn"
                          >
                            Raise
                          </Button>
                          <Button
                            onClick={() => performAction('fold')}
                            variant="outline"
                            className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                            data-testid="fold-btn"
                          >
                            <XCircle className="h-4 w-4 mr-2" />
                            Fold
                          </Button>
                        </>
                      )}
                      
                      {/* Rummy Actions */}
                      {gameType === 'rummy' && (
                        <>
                          {!gameState.has_drawn?.[user?.id] && (
                            <>
                              <Button
                                onClick={() => performAction('draw_deck')}
                                className="bg-blue-500 hover:bg-blue-600"
                                data-testid="draw-deck-btn"
                              >
                                Draw from Deck
                              </Button>
                              {gameState.discard_top && (
                                <Button
                                  onClick={() => performAction('draw_discard')}
                                  className="bg-green-500 hover:bg-green-600"
                                  data-testid="draw-discard-btn"
                                >
                                  Pick Discard
                                </Button>
                              )}
                            </>
                          )}
                          {gameState.has_drawn?.[user?.id] && selectedCards.length === 1 && (
                            <Button
                              onClick={() => {
                                performAction('discard', { card_index: selectedCards[0] });
                                setSelectedCards([]);
                              }}
                              className="bg-orange-500 hover:bg-orange-600"
                              data-testid="discard-btn"
                            >
                              Discard Selected
                            </Button>
                          )}
                          {gameState.has_drawn?.[user?.id] && myHand.length === 14 && (
                            <Button
                              onClick={() => performAction('declare', { melds: [] })}
                              className="bg-purple-500 hover:bg-purple-600"
                              data-testid="declare-btn"
                            >
                              Declare
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ) : gameResult ? (
              /* Game Results */
              <Card className="bg-slate-900/80 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-yellow-400">
                    <Trophy className="h-6 w-6" />
                    Game Results
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center mb-6">
                    <p className="text-lg text-slate-400">Winner</p>
                    <p className="text-3xl font-bold text-yellow-400">{gameResult.winner_name}</p>
                    {gameResult.hand_name && (
                      <Badge className="mt-2 bg-purple-500/20 text-purple-300">
                        {gameResult.hand_name}
                      </Badge>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    {gameResult.rewards?.map((result, index) => (
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
                          <span className="font-medium">
                            {result.user_id === user?.id ? 'You' : result.name}
                          </span>
                        </div>
                        <Badge className="bg-yellow-500/20 text-yellow-400">
                          <Coins className="h-3 w-3 mr-1" />
                          +{result.coins}
                        </Badge>
                      </div>
                    ))}
                  </div>
                  
                  <Button 
                    onClick={() => navigate('/games')}
                    className={`w-full mt-6 bg-gradient-to-r ${gameInfo.color}`}
                    data-testid="play-again-btn"
                  >
                    Play Again
                  </Button>
                </CardContent>
              </Card>
            ) : (
              /* Waiting Room */
              <Card className="bg-slate-900/80 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-blue-400" />
                    Waiting for Players
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-400 mb-4">
                    {players.length} / {room?.max_players || 4} players joined
                  </p>
                  
                  {/* Start Game Button (Host only) */}
                  {room?.host_id === user?.id && (
                    <Button
                      onClick={startGame}
                      disabled={players.length < 2 || starting}
                      className={`w-full h-12 bg-gradient-to-r ${gameInfo.color} text-white font-bold mb-4`}
                      data-testid="start-game-btn"
                    >
                      {starting ? (
                        <RefreshCw className="h-5 w-5 mr-2 animate-spin" />
                      ) : (
                        <Play className="h-5 w-5 mr-2" />
                      )}
                      {players.length < 2 ? 'Need at least 2 players' : 'Start Game'}
                    </Button>
                  )}
                  
                  {/* Invite Friends Section */}
                  <div className="bg-slate-800/50 rounded-lg p-4 mb-4">
                    <h4 className="text-sm font-medium text-white mb-3 flex items-center gap-2">
                      <UserPlus className="h-4 w-4 text-green-400" />
                      Invite Friends
                    </h4>
                    <p className="text-xs text-slate-400 mb-3">
                      Share the invite link to bring friends directly into this game!
                    </p>
                    <div className="flex gap-2">
                      <Button
                        onClick={shareInvite}
                        className="flex-1 bg-green-500 hover:bg-green-600"
                        data-testid="share-invite-btn"
                      >
                        <Share2 className="h-4 w-4 mr-2" />
                        Share Invite
                      </Button>
                      <Button
                        onClick={copyInviteLink}
                        variant="outline"
                        className="border-slate-600"
                        data-testid="copy-link-btn"
                      >
                        <Link2 className="h-4 w-4" />
                      </Button>
                    </div>
                    {room?.room_code && (
                      <div className="mt-3 flex items-center justify-between bg-slate-900/50 rounded px-3 py-2">
                        <span className="text-xs text-slate-400">Code:</span>
                        <span className="font-mono font-bold text-yellow-400">{room.room_code}</span>
                        <Button
                          onClick={copyRoomCode}
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    )}
                  </div>
                  
                  {room?.host_id !== user?.id && (
                    <div className="text-center py-4">
                      <RefreshCw className="h-8 w-8 text-blue-400 mx-auto mb-2 animate-spin" />
                      <p className="text-slate-400">Waiting for host to start...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
          
          {/* Sidebar - Players & Chat */}
          <div className="space-y-4">
            {/* Players List */}
            <Card className="bg-slate-900/80 border-slate-700">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Users className="h-4 w-4 text-blue-400" />
                  Players ({players.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {players.map((player) => (
                  <PlayerSeat
                    key={player.id}
                    player={player}
                    isCurrentTurn={gameState?.current_player === player.id}
                    isMe={player.id === user?.id}
                    isFolded={gameState?.folded_players?.includes(player.id)}
                    hasSeen={gameState?.seen_players?.includes(player.id)}
                    gameType={gameType}
                    cards={gameState?.hands?.[player.id]}
                  />
                ))}
                
                {/* Empty slots */}
                {Array.from({ length: (room?.max_players || 4) - players.length }).map((_, i) => (
                  <div 
                    key={`empty-${i}`} 
                    className="p-3 rounded-xl border-2 border-dashed border-slate-700 text-center text-slate-600"
                  >
                    Waiting...
                  </div>
                ))}
              </CardContent>
            </Card>
            
            {/* Chat */}
            {showChat && (
              <Card className="bg-slate-900/80 border-slate-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Chat</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-48 overflow-y-auto mb-2 space-y-1">
                    {chatMessages.length === 0 ? (
                      <p className="text-slate-500 text-sm text-center py-4">No messages yet</p>
                    ) : (
                      chatMessages.map((msg, idx) => (
                        <div key={idx} className={`text-sm ${msg.isMe ? 'text-yellow-400' : 'text-slate-300'}`}>
                          <span className="font-medium">{msg.isMe ? 'You' : msg.player_name}:</span>{' '}
                          {msg.message}
                        </div>
                      ))
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Input
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="Type a message..."
                      className="bg-slate-800 border-slate-700 text-sm"
                      onKeyPress={(e) => e.key === 'Enter' && sendChat()}
                      data-testid="chat-input"
                    />
                    <Button onClick={sendChat} size="sm" data-testid="send-chat-btn">
                      <Send className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameRoom;
