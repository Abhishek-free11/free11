import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, X, Mic, MicOff, ArrowRight } from 'lucide-react';

const SEARCH_ITEMS = [
  { label: 'Match Centre', path: '/match-centre', tags: 'matches live upcoming cricket ipl' },
  { label: 'Predictions', path: '/predict', tags: 'predict ball over runs wicket boundary' },
  { label: 'Card Games', path: '/games', tags: 'rummy teen patti poker games play' },
  { label: 'Earn Coins', path: '/earn', tags: 'earn coins quiz spin scratch watch ad tasks boosters' },
  { label: 'Wallet', path: '/ledger', tags: 'wallet balance coins transactions ledger' },
  { label: 'FREE Bucks', path: '/freebucks', tags: 'free bucks buy purchase payment premium' },
  { label: 'Power-Ups', path: '/cards', tags: 'power ups cards double triple shield booster' },
  { label: 'Invite Friends', path: '/referrals', tags: 'invite referral friends share code' },
  { label: 'Profile', path: '/profile', tags: 'profile account settings name email' },
  { label: 'Leaderboards', path: '/leaderboards', tags: 'leaderboard rank top players' },
  { label: 'Clans', path: '/clans', tags: 'clan team group community' },
  { label: 'Free Shop', path: '/shop', tags: 'shop redeem rewards voucher gift' },
  { label: 'Support', path: '/support', tags: 'help support tickets chat faq' },
  { label: 'FAQ', path: '/faq', tags: 'faq questions answers help' },
  { label: 'Fantasy Team Builder', path: '/match-centre', tags: 'fantasy team builder dream11 players captain' },
  { label: 'Dashboard', path: '/dashboard', tags: 'dashboard home stats progress' },
];

export default function AppSearch({ isOpen, onClose }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [listening, setListening] = useState(false);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
    if (!isOpen) {
      setQuery('');
      setResults([]);
      stopListening();
    }
  }, [isOpen]);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const q = query.toLowerCase();
    const filtered = SEARCH_ITEMS.filter(
      item => item.label.toLowerCase().includes(q) || item.tags.includes(q)
    );
    setResults(filtered);
  }, [query]);

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0].transcript)
        .join('');
      setQuery(transcript);
    };

    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setListening(false);
  };

  const handleSelect = (item) => {
    navigate(item.path);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-black/90 backdrop-blur-sm" data-testid="app-search-overlay" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="max-w-lg mx-auto px-4 pt-4 safe-area-top">
        {/* Search Input */}
        <div className="flex items-center gap-2 bg-slate-800 rounded-2xl px-4 py-3 border border-slate-700">
          <Search className="w-5 h-5 text-gray-400 flex-shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search matches, games, features..."
            className="flex-1 bg-transparent text-white text-sm outline-none placeholder:text-gray-500"
            data-testid="search-input"
          />
          {query && (
            <button onClick={() => setQuery('')} className="text-gray-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={listening ? stopListening : startListening}
            className={`p-1.5 rounded-full transition-all ${listening ? 'bg-red-500/20 text-red-400 animate-pulse' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
            data-testid="voice-search-btn"
          >
            {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-sm font-medium ml-1">
            Cancel
          </button>
        </div>

        {/* Listening indicator */}
        {listening && (
          <div className="mt-3 text-center">
            <div className="flex items-center justify-center gap-1">
              <div className="w-1 h-4 bg-red-400 rounded-full animate-pulse" />
              <div className="w-1 h-6 bg-red-400 rounded-full animate-pulse" style={{ animationDelay: '0.1s' }} />
              <div className="w-1 h-3 bg-red-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
              <div className="w-1 h-5 bg-red-400 rounded-full animate-pulse" style={{ animationDelay: '0.3s' }} />
              <div className="w-1 h-4 bg-red-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
            </div>
            <p className="text-xs text-red-400 mt-1">Listening...</p>
          </div>
        )}

        {/* Results */}
        <div className="mt-3 space-y-1 max-h-[70vh] overflow-y-auto">
          {results.length > 0 ? (
            results.map((item) => (
              <button
                key={item.path + item.label}
                onClick={() => handleSelect(item)}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                data-testid={`search-result-${item.path.replace(/\//g, '-')}`}
              >
                <span className="text-white text-sm font-medium">{item.label}</span>
                <ArrowRight className="w-4 h-4 text-gray-500" />
              </button>
            ))
          ) : query.trim() ? (
            <div className="text-center py-8 text-gray-500 text-sm">No results for "{query}"</div>
          ) : (
            <div className="space-y-1">
              <p className="text-xs text-gray-500 px-1 mb-2">Quick Access</p>
              {SEARCH_ITEMS.slice(0, 8).map((item) => (
                <button
                  key={item.path}
                  onClick={() => handleSelect(item)}
                  className="w-full flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                >
                  <span className="text-gray-300 text-sm">{item.label}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-gray-600" />
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
