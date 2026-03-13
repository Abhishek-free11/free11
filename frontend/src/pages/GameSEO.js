import { Link, useNavigate, useLocation } from 'react-router-dom';
import { CheckCircle, Star, Coins, Gift, ArrowRight } from 'lucide-react';

// ═══════════════════════════════════════════════════════════
// PUBLIC SEO LANDING PAGES — No auth required
// Routes: /rummy, /teen-patti, /poker, /cricket-prediction
// Purpose: High-priority SEO pages targeting game search terms
// ═══════════════════════════════════════════════════════════

const GAME_DATA = {
  rummy: {
    title: 'Free Rummy Online India',
    h1: 'Play Free Rummy Online in India — Earn Real Rewards',
    subtitle: 'FREE11 has complete 13-card Indian Rummy vs AI. Win daily. Earn 50 FREE Coins. Redeem for groceries and vouchers. No deposits ever.',
    keywords: 'free rummy india, rummy online free india, 13 card rummy free, earn coins rummy india',
    coins: '50 FREE Coins / day',
    gameType: 'rummy',
    color: '#C6A052',
    features: ['13-card Indian Points Rummy', 'Play vs AI opponent', 'Win → earn 50 FREE Coins daily', 'Redeem coins for real groceries', 'No real money, no deposits', 'PROGA 2025 compliant'],
    howToPlay: ['Register at free11.com (free, no deposit)', 'Go to Games → Rummy', 'Deal 13 cards, form valid sequences & sets', 'First to declare with a valid hand wins', 'Earn 50 FREE Coins once per day', 'Redeem coins in the FREE11 Shop'],
    faqs: [
      { q: 'Is FREE11 Rummy free to play?', a: 'Yes. 100% free. No deposits, no entry fees, no real money stakes. Play Rummy, win, earn FREE Coins.' },
      { q: 'What type of Rummy is on FREE11?', a: '13-card Indian Points Rummy vs AI. Standard rules — 2 sequences (1 pure) required to declare.' },
      { q: 'How many coins do I earn playing Rummy?', a: 'Win at Rummy on FREE11 to earn 50 FREE Coins per day. Coins are redeemable for groceries, recharges, and vouchers.' },
      { q: 'Is FREE11 Rummy legal in India?', a: 'Yes. FREE11 is PROGA 2025 compliant. Rummy on FREE11 is free skill-based entertainment — not gambling.' },
    ],
    schema: {
      '@type': 'VideoGame',
      name: 'FREE11 Rummy — Free 13-Card Indian Rummy Online India',
      alternateName: ['free rummy india', 'rummy online free india', '13 card rummy free', 'free rummy app india'],
      description: 'FREE11 Rummy is a free 13-card Indian Points Rummy game vs AI. Play online in India, earn 50 FREE Coins per day, redeem for real groceries and vouchers. No deposits required.',
      genre: ['Card Game', 'Skill Game'],
      gamePlatform: ['Android', 'iOS', 'Web Browser'],
      playMode: 'SinglePlayer',
      applicationCategory: 'GameApplication',
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'INR' },
      url: 'https://free11.com/rummy',
    },
  },
  'teen-patti': {
    title: 'Free Teen Patti Online India',
    h1: 'Play Free Teen Patti Online in India — Earn Real Rewards',
    subtitle: 'FREE11 has complete Teen Patti vs AI. Play 3-card Teen Patti free. Earn 40 FREE Coins daily. Redeem for groceries and vouchers. No deposits.',
    keywords: 'free teen patti, teen patti online free india, teen patti earn coins, free teen patti app india',
    coins: '40 FREE Coins / day',
    gameType: 'teen_patti',
    color: '#a855f7',
    features: ['Classic 3-card Teen Patti', 'Play vs AI opponent', 'Win → earn 40 FREE Coins daily', 'Redeem coins for real rewards', 'No real money, no deposits', 'PROGA 2025 compliant'],
    howToPlay: ['Register at free11.com (free)', 'Go to Games → Teen Patti', 'Play classic 3-card Teen Patti vs AI', 'Best 3-card hand wins', 'Earn 40 FREE Coins once per day', 'Redeem coins for groceries and vouchers'],
    faqs: [
      { q: 'Is FREE11 Teen Patti free?', a: 'Yes. 100% free. Play Teen Patti vs AI, win, earn FREE Coins. No deposits, no real money.' },
      { q: 'What version of Teen Patti is on FREE11?', a: 'Classic 3-card Teen Patti vs AI. Standard hand rankings: Trail > Pure Sequence > Sequence > Color > Pair > High Card.' },
      { q: 'How many coins do I earn at Teen Patti?', a: '40 FREE Coins per day for winning at Teen Patti on FREE11.' },
      { q: 'Is FREE11 Teen Patti legal?', a: 'Yes. FREE11 is PROGA 2025 compliant. Teen Patti on FREE11 is free skill-based entertainment — not gambling.' },
    ],
    schema: {
      '@type': 'VideoGame',
      name: 'FREE11 Teen Patti — Free Teen Patti Online India',
      alternateName: ['free teen patti india', 'teen patti online free', 'free teen patti app', '3 card teen patti free'],
      description: 'FREE11 Teen Patti is a free 3-card Teen Patti game vs AI. Play online in India, earn 40 FREE Coins per day, redeem for real rewards. No deposits required.',
      genre: ['Card Game', 'Skill Game'],
      gamePlatform: ['Android', 'iOS', 'Web Browser'],
      playMode: 'SinglePlayer',
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'INR' },
      url: 'https://free11.com/teen-patti',
    },
  },
  poker: {
    title: 'Free Poker Online India',
    h1: 'Play Free Poker Online in India — Texas Hold\'em & Earn Rewards',
    subtitle: 'FREE11 has Texas Hold\'em Poker vs AI. Earn 60 FREE Coins daily — the highest daily card game reward on FREE11. No deposits, no real money.',
    keywords: 'free poker india, poker online free india, texas holdem free india, earn coins poker india',
    coins: '60 FREE Coins / day',
    gameType: 'poker',
    color: '#ef4444',
    features: ['Texas Hold\'em (No-Limit) Poker', 'Play vs AI opponent', 'Win → earn 60 FREE Coins daily (highest card game reward)', 'Redeem coins for real rewards', 'No real money, no deposits', 'PROGA 2025 compliant'],
    howToPlay: ['Register at free11.com (free)', 'Go to Games → Poker', 'Play Texas Hold\'em vs AI', 'Best 5-card hand wins', 'Earn 60 FREE Coins once per day', 'Redeem coins in the FREE11 Shop'],
    faqs: [
      { q: 'Is FREE11 Poker free to play?', a: 'Yes. 100% free. Texas Hold\'em vs AI, no deposits, no real money. Earn FREE Coins for winning.' },
      { q: 'What poker game is on FREE11?', a: 'Texas Hold\'em (No-Limit) Poker vs AI. Standard 5-card hand rules with hole cards, flop, turn, and river.' },
      { q: 'How many coins do I earn at Poker?', a: '60 FREE Coins per day — the highest daily earning from any card game on FREE11.' },
      { q: 'Is FREE11 Poker legal in India?', a: 'Yes. PROGA 2025 compliant. FREE11 Poker is free skill-based card entertainment — not gambling.' },
    ],
    schema: {
      '@type': 'VideoGame',
      name: 'FREE11 Poker — Free Texas Hold\'em Poker Online India',
      alternateName: ['free poker india', 'texas holdem free india', 'poker online free india', 'free poker app india'],
      description: 'FREE11 Poker is free Texas Hold\'em vs AI. Earn 60 FREE Coins per day — the highest card game daily reward on FREE11. Redeem for real rewards. No deposits.',
      genre: ['Card Game', 'Skill Game'],
      gamePlatform: ['Android', 'iOS', 'Web Browser'],
      playMode: 'SinglePlayer',
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'INR' },
      url: 'https://free11.com/poker',
    },
  },
  'cricket-prediction': {
    title: 'Free Cricket Prediction App India',
    h1: 'Free Cricket Prediction App India — Predict Matches & Earn Rewards',
    subtitle: 'Predict Virat Kohli, Rohit Sharma, Jasprit Bumrah and all India cricket players on FREE11. Earn FREE Coins on every correct call. No deposits ever.',
    keywords: 'free cricket prediction india, cricket prediction app no deposit, earn coins cricket india, virat kohli prediction, rohit sharma prediction',
    coins: '10–30 coins × up to 3×',
    gameType: null,
    color: '#4ade80',
    features: ['Live T20, ODI & Test match predictions', 'Ball-by-ball and over-by-over', 'Hot Hand streak multiplier (up to 3×)', 'All India cricket players covered', 'EntitySport live data', 'No deposits, 100% free'],
    howToPlay: ['Register at free11.com', 'Go to Play → Match Centre', 'Select a live match', 'Predict over-by-over outcomes', 'Earn 10–30 FREE Coins per correct call', 'Activate Hot Hand for up to 3× multiplier'],
    faqs: [
      { q: 'Is FREE11 cricket prediction free?', a: 'Yes. 100% free. No deposits, no entry fees. Predict any live cricket match and earn FREE Coins.' },
      { q: 'Which cricket players can I predict?', a: 'All active India players: Virat Kohli, Rohit Sharma, Jasprit Bumrah, MS Dhoni, KL Rahul, Shubman Gill, Hardik Pandya, Suryakumar Yadav, Rishabh Pant, Ravindra Jadeja, Yashasvi Jaiswal, Mohammed Shami, and more.' },
      { q: 'How much do I earn per cricket prediction?', a: '10–30 FREE Coins per correct prediction. Hot Hand multiplier gives up to 3× for consecutive correct calls.' },
      { q: 'Is FREE11 cricket prediction legal in India?', a: 'Yes. PROGA 2025 compliant. Skill-based predictions — no gambling, no cash wagering.' },
    ],
    schema: {
      '@type': 'MobileApplication',
      name: 'FREE11 — Free Cricket Prediction App India',
      alternateName: ['free cricket prediction india', 'cricket prediction app no deposit', 'earn coins cricket india', 'free cricket app india'],
      description: 'FREE11 is a free cricket prediction app for India. Predict T20, ODI, and Test match outcomes for Virat Kohli, Rohit Sharma, and all India players. Earn FREE Coins. No deposits.',
      applicationCategory: 'SportsApplication',
      operatingSystem: 'Android, iOS, Web',
      offers: { '@type': 'Offer', price: '0', priceCurrency: 'INR' },
      url: 'https://free11.com/cricket-prediction',
    },
  },
};

export default function GameSEO() {
  const location = useLocation();
  const navigate = useNavigate();
  const pathToGame = { '/rummy': 'rummy', '/teen-patti': 'teen-patti', '/poker': 'poker', '/cricket-prediction': 'cricket-prediction' };
  const game = pathToGame[location.pathname];
  const data = GAME_DATA[game];

  if (!data) {
    navigate('/games');
    return null;
  }

  const playRoute = data.gameType ? `/games/${data.gameType}/play` : '/predict';

  return (
    <div className="min-h-screen pb-24" style={{ background: '#0F1115' }}>
      {/* JSON-LD Schema */}
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({ '@context': 'https://schema.org', ...data.schema }) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        mainEntity: data.faqs.map(f => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } }))
      }) }} />

      <div className="max-w-2xl mx-auto px-4 pt-6">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5 text-xs mb-5" style={{ color: '#8A9096' }}>
          <Link to="/" className="hover:text-white">Home</Link>
          <span>/</span>
          <Link to="/games" className="hover:text-white">Games</Link>
          <span>/</span>
          <span style={{ color: data.color }}>{data.title}</span>
        </nav>

        {/* Hero */}
        <div className="mb-8 p-6 rounded-2xl text-center" style={{ background: `linear-gradient(135deg, rgba(${data.color === '#C6A052' ? '198,160,82' : data.color === '#a855f7' ? '168,85,247' : data.color === '#ef4444' ? '239,68,68' : '74,222,128'},0.1), rgba(15,17,21,0.8))`, border: `1px solid ${data.color}33` }}>
          <div className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-full mb-4" style={{ background: `${data.color}20`, color: data.color, border: `1px solid ${data.color}40` }}>
            <Star className="w-3 h-3" />
            <span>FREE TO PLAY — NO DEPOSITS</span>
          </div>
          <h1 className="text-2xl font-black text-white mb-3 leading-tight" style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.03em' }}>
            {data.h1}
          </h1>
          <p className="text-sm mb-5" style={{ color: '#8A9096' }}>{data.subtitle}</p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link to="/register" className="px-6 py-2.5 rounded-full text-sm font-bold flex items-center gap-2" style={{ background: data.color, color: '#0F1115' }}>
              Play Free Now <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to={playRoute} className="px-5 py-2.5 rounded-full text-sm font-medium" style={{ border: `1px solid ${data.color}50`, color: data.color }}>
              Open Game
            </Link>
          </div>
        </div>

        {/* Daily Coins Badge */}
        <div className="flex items-center gap-3 p-4 rounded-xl mb-6" style={{ background: 'rgba(198,160,82,0.08)', border: '1px solid rgba(198,160,82,0.2)' }}>
          <Coins className="w-6 h-6 flex-shrink-0" style={{ color: '#C6A052' }} />
          <div>
            <p className="text-sm font-bold text-white">Daily Earn: <span style={{ color: '#C6A052' }}>{data.coins}</span></p>
            <p className="text-xs" style={{ color: '#8A9096' }}>Win the game once per day. Coins redeem for real groceries and rewards.</p>
          </div>
        </div>

        {/* Features */}
        <section className="mb-8">
          <h2 className="text-base font-bold text-white mb-4">{data.title} on FREE11 — Key Features</h2>
          <div className="space-y-2">
            {data.features.map(f => (
              <div key={f} className="flex items-start gap-3">
                <CheckCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#4ade80' }} />
                <p className="text-sm" style={{ color: '#BFC3C8' }}>{f}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How to Play */}
        <section className="mb-8">
          <h2 className="text-base font-bold text-white mb-4">How to Play {data.title} on FREE11</h2>
          <div className="space-y-3">
            {data.howToPlay.map((step, i) => (
              <div key={i} className="flex items-start gap-3 p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
                <span className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0" style={{ background: `${data.color}20`, color: data.color }}>{i + 1}</span>
                <p className="text-sm" style={{ color: '#BFC3C8' }}>{step}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Rewards */}
        <section className="mb-8 p-4 rounded-xl" style={{ background: 'rgba(74,222,128,0.05)', border: '1px solid rgba(74,222,128,0.15)' }}>
          <div className="flex items-center gap-2 mb-3">
            <Gift className="w-5 h-5" style={{ color: '#4ade80' }} />
            <h2 className="text-sm font-bold text-white">Redeem Coins for Real Rewards</h2>
          </div>
          <p className="text-xs mb-3" style={{ color: '#8A9096' }}>Every FREE Coin earned from {data.title} can be redeemed in the FREE11 Shop for:</p>
          <div className="grid grid-cols-2 gap-2">
            {['Groceries & daily essentials', 'Mobile recharges', 'OTT passes', 'Gift vouchers'].map(r => (
              <div key={r} className="flex items-center gap-1.5 text-xs" style={{ color: '#BFC3C8' }}>
                <span style={{ color: '#4ade80' }}>✓</span> {r}
              </div>
            ))}
          </div>
        </section>

        {/* FAQ */}
        <section className="mb-8" itemScope itemType="https://schema.org/FAQPage">
          <h2 className="text-base font-bold text-white mb-4">Frequently Asked Questions</h2>
          <div className="space-y-3">
            {data.faqs.map((faq, i) => (
              <div key={i} className="p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                itemScope itemProp="mainEntity" itemType="https://schema.org/Question">
                <p className="text-sm font-semibold text-white mb-1.5" itemProp="name">{faq.q}</p>
                <div itemScope itemProp="acceptedAnswer" itemType="https://schema.org/Answer">
                  <p className="text-xs leading-relaxed" style={{ color: '#8A9096' }} itemProp="text">{faq.a}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Other Games CTA */}
        <section className="mb-6">
          <h2 className="text-sm font-bold text-white mb-3">More Free Games on FREE11</h2>
          <div className="grid grid-cols-2 gap-3">
            {[
              { path: '/rummy', label: 'Free Rummy', coins: '+50/day', color: '#C6A052' },
              { path: '/teen-patti', label: 'Free Teen Patti', coins: '+40/day', color: '#a855f7' },
              { path: '/poker', label: 'Free Poker', coins: '+60/day', color: '#ef4444' },
              { path: '/cricket-prediction', label: 'Cricket Prediction', coins: 'Up to 3×', color: '#4ade80' },
            ].filter(g => location.pathname !== g.path).slice(0, 3).map(g => (
              <Link key={g.path} to={g.path} className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <p className="text-xs font-semibold text-white">{g.label}</p>
                <p className="text-xs mt-0.5" style={{ color: g.color }}>{g.coins}</p>
              </Link>
            ))}
          </div>
        </section>

        {/* Final CTA */}
        <div className="p-5 rounded-2xl text-center mb-8" style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.15), rgba(198,160,82,0.05))', border: '1px solid rgba(198,160,82,0.3)' }}>
          <p className="text-base font-bold text-white mb-1" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>JOIN FREE11 — START EARNING TODAY</p>
          <p className="text-xs mb-4" style={{ color: '#8A9096' }}>Free to register. Free to play. Real rewards.</p>
          <Link to="/register" className="inline-block px-6 py-2.5 rounded-full text-sm font-bold" style={{ background: '#C6A052', color: '#0F1115' }}>
            Register Free — No Deposits
          </Link>
        </div>
      </div>
    </div>
  );
}
