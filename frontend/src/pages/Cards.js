import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../utils/api';
import { toast } from 'sonner';
import Navbar from '../components/Navbar';
import { ArrowLeft, Shield, Zap, Star, Clock } from 'lucide-react';

export default function Cards() {
  const navigate = useNavigate();
  const [inventory, setInventory] = useState([]);
  const [cardTypes, setCardTypes] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [invRes, typesRes] = await Promise.all([
        api.v2GetCardInventory(),
        api.v2GetCardTypes(),
      ]);
      setInventory(invRes.data);
      setCardTypes(typesRes.data);
    } catch {
      toast.error('Failed to load cards');
    }
    setLoading(false);
  };

  const rarityColors = {
    common: 'from-gray-600/30 to-gray-700/20 border-gray-500/30',
    rare: 'from-blue-600/30 to-blue-700/20 border-blue-500/30',
    epic: 'from-purple-600/30 to-purple-700/20 border-purple-500/30',
  };
  const rarityGlow = {
    common: '',
    rare: 'shadow-blue-500/10 shadow-lg',
    epic: 'shadow-purple-500/10 shadow-lg',
  };

  return (
    <div className="min-h-screen bg-[#0a0e17] text-white pb-28 md:pb-4" data-testid="cards-page">
      <Navbar />
      {/* Header */}
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)} data-testid="back-button">
          <ArrowLeft className="w-5 h-5 text-gray-400" />
        </button>
        <h1 className="text-lg font-bold">Power-Ups</h1>
        <span className="ml-auto bg-emerald-500/20 text-emerald-400 text-xs px-2 py-0.5 rounded-full" data-testid="card-count">
          {inventory.length} cards
        </span>
      </div>

      {/* Card Types Info */}
      <div className="px-4 pt-4">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">Available Card Types</h3>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(cardTypes).map(([key, card]) => (
            <div
              key={key}
              className={`p-3 rounded-xl bg-gradient-to-br ${rarityColors[card.rarity] || rarityColors.common} border ${rarityGlow[card.rarity] || ''}`}
              data-testid={`card-type-${key}`}
            >
              <div className="flex items-center gap-1.5 mb-1">
                {card.effect === 'multiply_reward' ? <Zap className="w-3.5 h-3.5 text-yellow-400" /> :
                 card.effect === 'protect_streak' ? <Shield className="w-3.5 h-3.5 text-blue-400" /> :
                 <Star className="w-3.5 h-3.5 text-purple-400" />}
                <span className="text-xs font-bold">{card.name}</span>
              </div>
              <p className="text-[10px] text-gray-400 leading-tight">{card.description}</p>
              <div className="mt-1.5">
                <span className={`text-[10px] px-1.5 py-0.5 rounded capitalize ${
                  card.rarity === 'epic' ? 'bg-purple-500/20 text-purple-300' :
                  card.rarity === 'rare' ? 'bg-blue-500/20 text-blue-300' :
                  'bg-gray-500/20 text-gray-300'
                }`}>{card.rarity}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* My Inventory */}
      <div className="px-4 mt-6 pb-6" data-testid="card-inventory">
        <h3 className="text-sm font-semibold text-gray-400 mb-3">My Inventory</h3>
        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading...</div>
        ) : inventory.length === 0 ? (
          <div className="bg-white/5 rounded-xl p-6 text-center">
            <Shield className="w-10 h-10 text-gray-600 mx-auto mb-2" />
            <div className="text-sm text-gray-400">No cards yet</div>
            <p className="text-xs text-gray-600 mt-1">Earn cards through predictions and rewards!</p>
          </div>
        ) : (
          <div className="space-y-2">
            {inventory.map(card => (
              <div key={card.id} className={`p-3 rounded-xl bg-gradient-to-r ${rarityColors[card.rarity] || rarityColors.common} border flex items-center gap-3`} data-testid={`card-${card.id}`}>
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  card.effect === 'multiply_reward' ? 'bg-yellow-500/20' : 'bg-blue-500/20'
                }`}>
                  {card.multiplier > 1 ? <span className="text-lg font-black text-yellow-400">{card.multiplier}x</span> :
                   <Shield className="w-5 h-5 text-blue-400" />}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium">{card.name}</div>
                  <div className="text-xs text-gray-500">{card.description}</div>
                </div>
                <div className="text-right">
                  <Clock className="w-3 h-3 text-gray-500 inline" />
                  <span className="text-[10px] text-gray-500 ml-1">
                    {Math.ceil((new Date(card.expires_at) - new Date()) / (1000 * 60 * 60 * 24))}d
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
