import { useParams, useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { Calendar, Clock, Tag, ChevronRight, BookOpen, ArrowLeft } from 'lucide-react';

// ═══════════════════════════════════════════════════════════
// MULTI-ARTICLE BLOG — SEO-optimised for Google, AI engines
// Routes: /blog/:slug  (default slug = cricket-guide)
// ═══════════════════════════════════════════════════════════

const ARTICLES = {
  'cricket-guide': {
    title: 'FREE11 Cricket 2026 Guide: Predict Live Matches & Earn Free Rewards',
    description: 'Complete guide to FREE11 cricket predictions. Predict T20, ODI & Test match outcomes. Earn FREE Coins on every correct call. Redeem for groceries and rewards. No deposits.',
    published: '2026-03-01',
    readTime: '4 min read',
    keywords: ['free11', 'free cricket prediction india', 'T20 2026 predictions', 'earn coins cricket india', 'cricket rewards app'],
    content: CricketGuideContent,
    faqs: [
      { q: 'What is FREE11 cricket prediction?', a: 'FREE11 is a free skill-based platform where you predict live cricket outcomes (ball-by-ball, over-by-over) during T20, ODI, and Test matches. Every correct prediction earns FREE Coins — no deposits, no fees.' },
      { q: 'How many coins do I earn per cricket prediction?', a: 'You earn 10–30 FREE Coins per correct prediction. A Hot Hand streak multiplier (up to 3×) rewards consecutive correct calls, boosting earnings significantly.' },
      { q: 'Which cricket players can I predict on FREE11?', a: 'All active India and international cricket players including Virat Kohli, Rohit Sharma, Jasprit Bumrah, MS Dhoni, KL Rahul, Shubman Gill, Hardik Pandya, Suryakumar Yadav, Rishabh Pant, Ravindra Jadeja, and more.' },
      { q: 'Is FREE11 cricket prediction free?', a: 'Yes — 100% free. No deposits, no entry fees. Earn FREE Coins through cricket predictions and redeem for real rewards at free11.com.' },
      { q: 'Is FREE11 cricket legal in India?', a: 'Yes. FREE11 is fully compliant with the Promotion and Regulation of Online Gaming Act, 2025. It is a skill-based platform — no gambling, no cash wagering.' },
    ],
  },
  'what-is-free11': {
    title: 'What is FREE11? Complete Guide to India\'s Free Gaming & Rewards Platform',
    description: 'FREE11 (free 11, free-11, fre11) is India\'s free skill-based gaming platform. Play cricket predictions, Rummy, Teen Patti, Poker, earn FREE Coins, redeem for real rewards. No deposits.',
    published: '2026-03-10',
    readTime: '5 min read',
    keywords: ['what is free11', 'free11 explained', 'free 11 app india', 'free11.com guide', 'free eleven india'],
    content: WhatIsFree11Content,
    faqs: [
      { q: 'What is FREE11?', a: 'FREE11 (also written as free 11, free-11, or fre11) is a free skill-based gaming and rewards platform from India. Play cricket predictions and card games, earn FREE Coins, redeem for groceries and vouchers.' },
      { q: 'Is FREE11 the same as free 11 or fre11?', a: 'Yes. free11, free 11, free-11, fre11, free1l, free eleven — all refer to the same platform at free11.com.' },
      { q: 'Is FREE11 different from Dream11?', a: 'Yes. Dream11 requires real money deposits. FREE11 is 100% free — no deposits, no financial risk, PROGA 2025 compliant.' },
      { q: 'What does "11" mean in FREE11?', a: '11 refers to the 11 players in a cricket team. FREE11 means you play free, like a full team, earning real rewards.' },
      { q: 'How do I sign up on FREE11?', a: 'Visit free11.com. Register with email, Google account, or phone number (OTP). Start earning FREE Coins immediately.' },
    ],
  },
  'free-rummy-india': {
    title: 'Free Rummy Online India — Play 13-Card Rummy & Earn Real Rewards on FREE11',
    description: 'Play free Rummy online in India on FREE11. 13-card Indian Rummy vs AI. Earn 50 FREE Coins per day. Redeem for groceries and rewards. No deposits, no real money required.',
    published: '2026-03-05',
    readTime: '4 min read',
    keywords: ['free rummy india', 'rummy online free india', 'free rummy app india', '13 card rummy free', 'earn coins rummy india', 'indian rummy free online'],
    content: FreeRummyContent,
    faqs: [
      { q: 'Can I play free Rummy online in India on FREE11?', a: 'Yes. FREE11 has a complete 13-card Indian Rummy game vs AI. Play for free, earn 50 FREE Coins per day, redeem for real rewards.' },
      { q: 'What type of Rummy does FREE11 have?', a: 'FREE11 has 13-card Indian Points Rummy. Form valid sequences and sets to win against the AI opponent and earn daily coins.' },
      { q: 'Do I need to deposit money to play Rummy on FREE11?', a: 'No. FREE11 Rummy is 100% free. No deposits, no stakes, no real money involved. You only earn — never spend to play.' },
      { q: 'How many coins do I earn playing Rummy on FREE11?', a: 'Win at Rummy on FREE11 and earn 50 FREE Coins per day. Coins can be redeemed for groceries, recharges, and gift vouchers.' },
      { q: 'Is FREE11 Rummy legal in India?', a: 'Yes. FREE11 is PROGA 2025 compliant. Rummy on FREE11 is a free skill-based card game with no real money wagering.' },
    ],
  },
  'free-teen-patti': {
    title: 'Free Teen Patti Online India — Play Teen Patti & Earn Real Rewards on FREE11',
    description: 'Play free Teen Patti online in India on FREE11. 3-card Teen Patti vs AI. Earn 40 FREE Coins per day. Redeem for groceries and rewards. No real money, no deposits.',
    published: '2026-03-06',
    readTime: '3 min read',
    keywords: ['free teen patti', 'teen patti online free india', 'free teen patti app india', 'teen patti earn coins', 'teen patti free no deposit', '3 card teen patti free'],
    content: FreeTeenPattiContent,
    faqs: [
      { q: 'Can I play free Teen Patti online in India on FREE11?', a: 'Yes. FREE11 has a complete Teen Patti game against an AI opponent. Play free, earn 40 FREE Coins per day, redeem for real rewards.' },
      { q: 'What version of Teen Patti is on FREE11?', a: 'FREE11 has classic 3-card Teen Patti. Play against AI to practice your bluffing and card reading skills — no real money involved.' },
      { q: 'Can I earn rewards playing Teen Patti on FREE11?', a: 'Yes. Win at Teen Patti on FREE11 to earn 40 FREE Coins per day. Redeem coins for groceries, mobile recharges, OTT passes, and more.' },
      { q: 'Is FREE11 Teen Patti free to play?', a: '100% free. No deposits, no real money, no wagering. Just skill-based entertainment that earns you real rewards.' },
      { q: 'Is Teen Patti on FREE11 legal in India?', a: 'Yes. FREE11 is PROGA 2025 compliant. Teen Patti on FREE11 is a free skill-based game — not gambling.' },
    ],
  },
  'free-poker-india': {
    title: 'Free Poker Online India — Play Texas Hold\'em & Earn Rewards on FREE11',
    description: 'Play free Poker online in India on FREE11. Texas Hold\'em vs AI. Earn 60 FREE Coins per day. Redeem for groceries and rewards. No deposits, no real money poker.',
    published: '2026-03-07',
    readTime: '3 min read',
    keywords: ['free poker india', 'poker online free india', 'texas holdem free india', 'free poker app india', 'earn coins poker india', 'poker no deposit india'],
    content: FreePokerContent,
    faqs: [
      { q: 'Can I play free Poker online in India on FREE11?', a: 'Yes. FREE11 has Texas Hold\'em Poker vs AI. Play for free, earn 60 FREE Coins per day (the highest daily card game reward), redeem for real rewards.' },
      { q: 'What poker variant does FREE11 have?', a: 'FREE11 has Texas Hold\'em (No Limit) Poker against an AI opponent. No real money involved — purely skill-based entertainment.' },
      { q: 'How much do I earn playing Poker on FREE11?', a: 'Win at Poker on FREE11 and earn 60 FREE Coins per day — the highest daily card game earning on the platform. Redeem for groceries, recharges, and vouchers.' },
      { q: 'Do I need to deposit money to play Poker on FREE11?', a: 'No. FREE11 Poker is completely free. No deposits, no real money stakes. You earn FREE Coins just for playing and winning.' },
      { q: 'Is FREE11 Poker legal in India?', a: 'Yes. FREE11 is PROGA 2025 compliant. Poker on FREE11 is a free skill-based game with no real money wagering.' },
    ],
  },
  'cricket-players-2026': {
    title: 'Predict India Cricket Player Performances on FREE11 — Virat Kohli, Rohit Sharma & More',
    description: 'Predict Virat Kohli, Rohit Sharma, Jasprit Bumrah, MS Dhoni, KL Rahul & all India cricket players on FREE11. Earn FREE Coins on every correct prediction. No deposits.',
    published: '2026-03-08',
    readTime: '5 min read',
    keywords: ['virat kohli prediction', 'rohit sharma cricket prediction', 'jasprit bumrah prediction', 'ms dhoni cricket', 'kl rahul prediction', 'india cricket prediction app', 'shubman gill prediction', 'hardik pandya cricket free11'],
    content: CricketPlayersContent,
    faqs: [
      { q: 'Can I predict Virat Kohli\'s performance on FREE11?', a: 'Yes. During any live cricket match featuring Virat Kohli, FREE11 lets you predict his batting outcomes over-by-over. Every correct prediction earns FREE Coins.' },
      { q: 'Can I predict Rohit Sharma\'s performance on FREE11?', a: 'Yes. Predict Rohit Sharma\'s batting performance during live matches on FREE11. Earn coins for correct predictions about runs, wickets, and match outcomes.' },
      { q: 'Which India cricket players are on FREE11?', a: 'All active India cricket players: Virat Kohli, Rohit Sharma, Jasprit Bumrah, MS Dhoni, KL Rahul, Shubman Gill, Hardik Pandya, Suryakumar Yadav, Rishabh Pant, Ravindra Jadeja, Yashasvi Jaiswal, Mohammed Shami, Kuldeep Yadav, Axar Patel, and the full squad.' },
      { q: 'Is cricket player prediction on FREE11 free?', a: 'Yes. 100% free. No entry fees, no deposits. Predict any India cricket player\'s performance and earn FREE Coins for correct calls.' },
      { q: 'Does FREE11 use live cricket data?', a: 'Yes. FREE11 uses EntitySport\'s live data API for real-time ball-by-ball match scores and player statistics.' },
    ],
  },
  'earn-free-coins-india': {
    title: 'Earn Free Coins in India — 15 Ways to Earn on FREE11 (No Deposits)',
    description: 'Complete guide to earning FREE Coins on FREE11. Cricket predictions, Rummy, Teen Patti, Poker, Solitaire, daily check-ins, spin wheel, scratch card, referrals, rewarded ads. All free.',
    published: '2026-03-09',
    readTime: '4 min read',
    keywords: ['earn free coins india', 'earn rewards playing games india', 'free coins app india', 'earn groceries free india', 'earn coins cricket india', 'earn rewards free gaming app'],
    content: EarnCoinsContent,
    faqs: [
      { q: 'How can I earn free coins in India?', a: 'On FREE11, earn free coins through: cricket predictions (10–30/prediction), Rummy (+50/day), Teen Patti (+40/day), Poker (+60/day), Solitaire (+25/day), daily check-ins (up to 100/day), spin wheel, scratch card, AI puzzle, missions, rewarded ads (+20/video), and referrals (+50/friend). All free.' },
      { q: 'Can I really earn free groceries by playing games in India?', a: 'Yes. On FREE11, earn FREE Coins through skill-based games and redeem them for real grocery items, vouchers, and recharges. No deposits required.' },
      { q: 'What can I redeem FREE Coins for?', a: 'Groceries, cold drinks, biscuits, daily essentials, mobile recharges, OTT passes, gift vouchers, and digital rewards — all available in the FREE11 Shop.' },
      { q: 'Is there a daily limit on earning FREE Coins?', a: 'Each source has a daily cap (e.g. Rummy 50/day, rewarded ads 20×5=100/day) but there is no overall daily limit. Play multiple activities to maximise daily earnings.' },
      { q: 'Do FREE Coins expire?', a: 'FREE Coins have a 180-day rolling expiry from the date of earning. Stay active to keep your coins fresh.' },
    ],
  },
};

// ── Article Content Components ──────────────────────────────

function CricketGuideContent() {
  return (
    <div className="space-y-5 text-sm leading-relaxed" style={{ color: '#BFC3C8' }}>
      <p><strong style={{ color: 'white' }}>FREE11</strong> brings cricket fans a completely free way to put their match knowledge to work — and earn real everyday rewards doing it. No fantasy team building, no entry fees, no deposits. Just pure cricket prediction.</p>
      <h2 className="text-base font-bold text-white mt-6">How Cricket Predictions Work on FREE11</h2>
      <p>When a live T20, ODI, or Test match is in progress, FREE11 opens a prediction window for each over. You predict the outcome — runs scored, wicket falling, boundary hit — and earn <strong style={{ color: '#C6A052' }}>FREE Coins</strong> for every correct call.</p>
      <ul className="list-disc list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li>Correct prediction → 10–30 FREE Coins</li>
        <li>Hot Hand streak (3+ consecutive correct) → up to 3× multiplier</li>
        <li>All predictions based on live EntitySport data</li>
        <li>Results settled instantly after each over</li>
      </ul>
      <h2 className="text-base font-bold text-white mt-6">Players You Can Predict</h2>
      <p>Predict performances of <strong style={{ color: 'white' }}>Virat Kohli</strong>, <strong style={{ color: 'white' }}>Rohit Sharma</strong>, <strong style={{ color: 'white' }}>Jasprit Bumrah</strong>, <strong style={{ color: 'white' }}>MS Dhoni</strong>, <strong style={{ color: 'white' }}>KL Rahul</strong>, <strong style={{ color: 'white' }}>Shubman Gill</strong>, <strong style={{ color: 'white' }}>Hardik Pandya</strong>, <strong style={{ color: 'white' }}>Suryakumar Yadav</strong>, <strong style={{ color: 'white' }}>Rishabh Pant</strong>, <strong style={{ color: 'white' }}>Ravindra Jadeja</strong>, and the entire India and international cricket squad.</p>
      <h2 className="text-base font-bold text-white mt-6">Earn More: Hot Hand Multiplier</h2>
      <p>Get 3 or more predictions correct in a row to activate the <strong style={{ color: '#C6A052' }}>Hot Hand</strong> multiplier. Your coin earnings jump up to 3× for every correct prediction while the streak continues.</p>
      <h2 className="text-base font-bold text-white mt-6">Combine with Card Games</h2>
      <p>On days without live matches, stay active with <strong style={{ color: 'white' }}>Rummy, Teen Patti, Poker, and Solitaire</strong> — all free on FREE11 and earning coins daily. Never lose your streak.</p>
      <h2 className="text-base font-bold text-white mt-6">Redeem for Real Rewards</h2>
      <p>Accumulated FREE Coins can be redeemed in the <a href="/shop" style={{ color: '#C6A052' }}>FREE11 Shop</a> for groceries, mobile recharges, OTT passes, and gift vouchers. Zero cash required.</p>
    </div>
  );
}

function WhatIsFree11Content() {
  return (
    <div className="space-y-5 text-sm leading-relaxed" style={{ color: '#BFC3C8' }}>
      <p><strong style={{ color: 'white' }}>FREE11</strong> (also known as <em>free 11</em>, <em>free-11</em>, <em>fre11</em>, or <em>free eleven</em>) is a free skill-based gaming and rewards platform built for India. It lets users earn real everyday rewards — groceries, recharges, vouchers — completely free, through skill-based games.</p>
      <h2 className="text-base font-bold text-white mt-6">The Core Idea</h2>
      <p>Most gaming apps ask you to spend money to win money. FREE11 is the opposite: you spend zero, play skill-based games, and earn real rewards. The platform monetises through advertising and brand partnerships — not your wallet.</p>
      <h2 className="text-base font-bold text-white mt-6">What You Can Do on FREE11</h2>
      <ul className="list-disc list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li><strong style={{ color: 'white' }}>Predict cricket</strong> — live T20, ODI, Test match outcomes. Earn 10–30 coins per correct prediction.</li>
        <li><strong style={{ color: 'white' }}>Play Rummy</strong> — 13-card Indian Rummy vs AI. Earn 50 coins/day.</li>
        <li><strong style={{ color: 'white' }}>Play Teen Patti</strong> — 3-card game vs AI. Earn 40 coins/day.</li>
        <li><strong style={{ color: 'white' }}>Play Poker</strong> — Texas Hold'em vs AI. Earn 60 coins/day.</li>
        <li><strong style={{ color: 'white' }}>Play Solitaire</strong> — Klondike vs AI. Earn 25 coins/day.</li>
        <li><strong style={{ color: 'white' }}>Daily quests</strong> — Missions, spin wheel, scratch card, AI puzzle.</li>
        <li><strong style={{ color: 'white' }}>Watch and Earn</strong> — 20 coins per rewarded ad (5/day).</li>
        <li><strong style={{ color: 'white' }}>Refer friends</strong> — 50 coins for you + 50 for your friend.</li>
      </ul>
      <h2 className="text-base font-bold text-white mt-6">FREE11 vs Dream11 — Key Difference</h2>
      <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
        <table className="w-full text-xs">
          <thead><tr style={{ background: 'rgba(198,160,82,0.1)' }}><th className="p-2.5 text-left text-white">Feature</th><th className="p-2.5 text-left" style={{ color: '#C6A052' }}>FREE11</th><th className="p-2.5 text-left" style={{ color: '#8A9096' }}>Dream11</th></tr></thead>
          <tbody>
            {[['Deposits required', 'Never', 'Yes'],['Entry fees', 'None', 'Yes (₹10–₹50 typical)'],['Cash prizes', 'No (promotional rewards)', 'Yes (cash)'],['Risk to player', 'Zero', 'Financial risk'],['PROGA compliant', 'Yes', 'Regulated differently'],['Card games', 'Yes (Rummy, Teen Patti, Poker)', 'No'],['Free to play', 'Always', 'Paid to compete']].map(([f,a,b]) => (
              <tr key={f} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <td className="p-2.5" style={{ color: '#8A9096' }}>{f}</td>
                <td className="p-2.5 font-medium" style={{ color: '#4ade80' }}>{a}</td>
                <td className="p-2.5" style={{ color: '#8A9096' }}>{b}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <h2 className="text-base font-bold text-white mt-6">Is FREE11 Legal in India?</h2>
      <p>Yes. FREE11 is fully compliant with the <strong style={{ color: 'white' }}>Promotion and Regulation of Online Gaming Act, 2025 (PROGA)</strong>. It is a pure skill-based platform — no gambling, no betting, no financial risk. All rewards are promotional benefits.</p>
      <h2 className="text-base font-bold text-white mt-6">How to Get Started</h2>
      <p>Visit <a href="/register" style={{ color: '#C6A052' }}>free11.com/register</a>. Sign up with email, Google, or phone number. Start earning FREE Coins immediately through daily check-ins, card games, and cricket predictions. Redeem in the Shop when ready.</p>
    </div>
  );
}

function FreeRummyContent() {
  return (
    <div className="space-y-5 text-sm leading-relaxed" style={{ color: '#BFC3C8' }}>
      <p>If you're looking for <strong style={{ color: 'white' }}>free Rummy online in India</strong> with no deposits and real rewards, FREE11 is the answer. Play complete 13-card Indian Rummy against AI, earn <strong style={{ color: '#C6A052' }}>50 FREE Coins per day</strong>, and redeem for real groceries and vouchers.</p>
      <h2 className="text-base font-bold text-white mt-6">How to Play Free Rummy on FREE11</h2>
      <ol className="list-decimal list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li>Register at free11.com (free, no deposit)</li>
        <li>Go to Games → Rummy</li>
        <li>Play 13-card Indian Rummy against the AI</li>
        <li>Form valid sequences and sets to win</li>
        <li>Win the game → earn 50 FREE Coins (once per day)</li>
        <li>Redeem coins in the Shop for real rewards</li>
      </ol>
      <h2 className="text-base font-bold text-white mt-6">FREE11 Rummy Rules</h2>
      <ul className="list-disc list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li>13 cards dealt to each player</li>
        <li>Form minimum 2 sequences (at least 1 pure sequence)</li>
        <li>Remaining cards can be arranged in sets or sequences</li>
        <li>First to declare with valid hand wins</li>
        <li>Standard Indian Points Rummy rules apply</li>
      </ul>
      <h2 className="text-base font-bold text-white mt-6">Why FREE11 Rummy is Different</h2>
      <p>Most Rummy apps require cash deposits. FREE11 Rummy is <strong style={{ color: 'white' }}>100% free</strong> — you earn coins by winning, not by depositing. No financial risk, just skill-based card gaming that rewards you daily.</p>
      <h2 className="text-base font-bold text-white mt-6">Combine with Other Games</h2>
      <p>Play Rummy (+50), Teen Patti (+40), Poker (+60), Solitaire (+25) every day for up to <strong style={{ color: '#C6A052' }}>175 FREE Coins from card games alone</strong> — before cricket predictions, daily missions, and spin wheel bonuses.</p>
    </div>
  );
}

function FreeTeenPattiContent() {
  return (
    <div className="space-y-5 text-sm leading-relaxed" style={{ color: '#BFC3C8' }}>
      <p>Looking for <strong style={{ color: 'white' }}>free Teen Patti online</strong> in India with no deposits and real rewards? FREE11 has a complete Teen Patti game vs AI. Play free, earn <strong style={{ color: '#C6A052' }}>40 FREE Coins per day</strong>, redeem for groceries and vouchers.</p>
      <h2 className="text-base font-bold text-white mt-6">How to Play Free Teen Patti on FREE11</h2>
      <ol className="list-decimal list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li>Register at free11.com (no deposit required)</li>
        <li>Go to Games → Teen Patti</li>
        <li>Play 3-card Teen Patti against the AI</li>
        <li>Best 3-card hand wins the round</li>
        <li>Win → earn 40 FREE Coins (once per day)</li>
        <li>Redeem coins for real rewards in the Shop</li>
      </ol>
      <h2 className="text-base font-bold text-white mt-6">Teen Patti Hand Rankings on FREE11</h2>
      <ul className="list-disc list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li>Trail (Three of a Kind) — highest</li>
        <li>Pure Sequence (Straight Flush)</li>
        <li>Sequence (Straight)</li>
        <li>Color (Flush)</li>
        <li>Pair (Two of a Kind)</li>
        <li>High Card — lowest</li>
      </ul>
      <h2 className="text-base font-bold text-white mt-6">Free Teen Patti — No Real Money</h2>
      <p>Unlike most Teen Patti apps, FREE11 Teen Patti involves <strong style={{ color: 'white' }}>zero real money</strong>. You play with virtual chips, earn FREE Coins for winning, and the coins translate into real everyday rewards. Skill-based entertainment, PROGA 2025 compliant.</p>
    </div>
  );
}

function FreePokerContent() {
  return (
    <div className="space-y-5 text-sm leading-relaxed" style={{ color: '#BFC3C8' }}>
      <p>Want to play <strong style={{ color: 'white' }}>free Poker online in India</strong> without deposits? FREE11 has Texas Hold'em Poker vs AI. Earn <strong style={{ color: '#C6A052' }}>60 FREE Coins per day</strong> — the highest daily earning of any card game on FREE11.</p>
      <h2 className="text-base font-bold text-white mt-6">Texas Hold'em Poker on FREE11</h2>
      <p>FREE11 features standard Texas Hold'em (No-Limit) Poker against an AI opponent. The classic 5-card hand format with hole cards, flop, turn, and river. No real money, no deposits — pure skill.</p>
      <h2 className="text-base font-bold text-white mt-6">How to Play Free Poker on FREE11</h2>
      <ol className="list-decimal list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li>Register at free11.com</li>
        <li>Go to Games → Poker</li>
        <li>Play Texas Hold'em vs AI opponent</li>
        <li>Best 5-card hand wins</li>
        <li>Win the game → earn 60 FREE Coins (once per day)</li>
        <li>Coins redeemable in the FREE11 Shop</li>
      </ol>
      <h2 className="text-base font-bold text-white mt-6">Poker Hand Rankings</h2>
      <ul className="list-disc list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li>Royal Flush &gt; Straight Flush &gt; Four of a Kind</li>
        <li>Full House &gt; Flush &gt; Straight</li>
        <li>Three of a Kind &gt; Two Pair &gt; One Pair &gt; High Card</li>
      </ul>
      <h2 className="text-base font-bold text-white mt-6">Why FREE11 Poker is Unique</h2>
      <p>At 60 FREE Coins per day, Poker offers the <strong style={{ color: 'white' }}>highest daily card game reward</strong> on FREE11. No deposits, no cash risk — just skill-based Texas Hold'em that pays you in real rewards.</p>
    </div>
  );
}

function CricketPlayersContent() {
  const players = [
    { name: 'Virat Kohli', role: 'Batsman', team: 'India', desc: 'Predict Virat Kohli\'s batting performance — runs scored, boundaries, wicket probability — on FREE11 during any live match.' },
    { name: 'Rohit Sharma', role: 'Batsman / Captain', team: 'India', desc: 'Predict Rohit Sharma\'s aggressive batting outcomes in T20 and ODI matches on FREE11.' },
    { name: 'Jasprit Bumrah', role: 'Fast Bowler', team: 'India', desc: 'Predict Jasprit Bumrah\'s wicket-taking ability and economy rate on FREE11 during live cricket.' },
    { name: 'MS Dhoni', role: 'Wicket-keeper / Batsman', team: 'India', desc: 'Predict MS Dhoni\'s finishing ability and match outcomes on FREE11 across T20 and other formats.' },
    { name: 'KL Rahul', role: 'Batsman / Wicket-keeper', team: 'India', desc: 'Predict KL Rahul\'s consistent batting performance in T20 and ODI matches on FREE11.' },
    { name: 'Shubman Gill', role: 'Batsman', team: 'India', desc: 'Predict Shubman Gill\'s opening batting and run-scoring on FREE11.' },
    { name: 'Hardik Pandya', role: 'All-rounder', team: 'India', desc: 'Predict Hardik Pandya\'s batting and bowling impact on FREE11.' },
    { name: 'Suryakumar Yadav', role: 'Batsman', team: 'India', desc: 'Predict Suryakumar Yadav\'s 360-degree batting on FREE11 T20 matches.' },
    { name: 'Rishabh Pant', role: 'Wicket-keeper / Batsman', team: 'India', desc: 'Predict Rishabh Pant\'s aggressive stroke play on FREE11.' },
    { name: 'Ravindra Jadeja', role: 'All-rounder', team: 'India', desc: 'Predict Ravindra Jadeja\'s batting and bowling performance on FREE11.' },
    { name: 'Yashasvi Jaiswal', role: 'Batsman', team: 'India', desc: 'Predict Yashasvi Jaiswal\'s opening batting and run-rate on FREE11.' },
    { name: 'Mohammed Shami', role: 'Fast Bowler', team: 'India', desc: 'Predict Mohammed Shami\'s wicket haul and economy in live matches on FREE11.' },
  ];
  return (
    <div className="space-y-5 text-sm leading-relaxed" style={{ color: '#BFC3C8' }}>
      <p>FREE11 lets you predict live performances of all India cricket players. Every correct prediction earns <strong style={{ color: '#C6A052' }}>FREE Coins</strong>. No deposits. No entry fees.</p>
      <h2 className="text-base font-bold text-white mt-6">India Cricket Players on FREE11</h2>
      <div className="space-y-3">
        {players.map(p => (
          <div key={p.name} className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-white">{p.name}</span>
              <span className="text-xs px-1.5 py-0.5 rounded" style={{ background: 'rgba(198,160,82,0.1)', color: '#C6A052' }}>{p.role}</span>
            </div>
            <p className="text-xs" style={{ color: '#8A9096' }}>{p.desc}</p>
          </div>
        ))}
      </div>
      <h2 className="text-base font-bold text-white mt-6">How Player Predictions Work</h2>
      <p>During any live cricket match, FREE11 offers prediction windows for each over. You predict outcomes — runs, wickets, extras, boundaries — based on your knowledge of that player's form, conditions, and match situation. Correct predictions earn 10–30 FREE Coins with Hot Hand multipliers up to 3×.</p>
    </div>
  );
}

function EarnCoinsContent() {
  const methods = [
    { title: 'Cricket Predictions', coins: '10–30/prediction (up to 3×)', how: 'Predict live T20/ODI/Test match outcomes correctly' },
    { title: 'Rummy (vs AI)', coins: '+50/day', how: 'Win at 13-card Indian Rummy against AI' },
    { title: 'Poker (vs AI)', coins: '+60/day', how: 'Win at Texas Hold\'em against AI' },
    { title: 'Teen Patti (vs AI)', coins: '+40/day', how: 'Win at 3-card Teen Patti against AI' },
    { title: 'Solitaire', coins: '+25/day', how: 'Complete Klondike Solitaire' },
    { title: 'Daily Check-in', coins: '10–100/day', how: 'Streak bonus increases each consecutive day' },
    { title: 'Lucky Spin Wheel', coins: 'Variable', how: 'Spin once per day for random coin prize' },
    { title: 'Scratch Card', coins: 'Variable', how: 'Scratch once per day for random prize' },
    { title: 'AI Daily Puzzle', coins: 'Variable', how: 'Solve Gemini-powered cricket puzzle' },
    { title: 'Daily Missions', coins: 'Variable', how: 'Complete multiple daily task challenges' },
    { title: 'Rewarded Ads', coins: '+20/video (5/day)', how: 'Watch a short video ad to earn coins' },
    { title: 'Referrals', coins: '+50 per friend', how: 'Refer a friend — both of you get 50 coins' },
    { title: 'Contests', coins: 'Pool prizes', how: 'Join free prediction contests for coin pools' },
    { title: 'Sponsored Pools', coins: 'Pool prizes', how: 'Join brand-sponsored prediction pools' },
    { title: 'Quest (opt-in)', coins: '+20/day', how: 'Opt-in to ad quest for bonus daily coins' },
  ];
  return (
    <div className="space-y-5 text-sm leading-relaxed" style={{ color: '#BFC3C8' }}>
      <p>FREE11 has <strong style={{ color: 'white' }}>15 different ways</strong> to earn FREE Coins — all completely free, no deposits. Here is the complete earning guide.</p>
      <h2 className="text-base font-bold text-white mt-6">All Earning Methods on FREE11</h2>
      <div className="space-y-2">
        {methods.map((m, i) => (
          <div key={m.title} className="flex items-start gap-3 p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}>
            <span className="text-xs font-bold w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: 'rgba(198,160,82,0.15)', color: '#C6A052' }}>{i+1}</span>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-white text-xs">{m.title}</span>
                <span className="text-xs px-1.5 py-0.5 rounded font-medium" style={{ background: 'rgba(74,222,128,0.1)', color: '#4ade80' }}>{m.coins}</span>
              </div>
              <p className="text-xs mt-0.5" style={{ color: '#8A9096' }}>{m.how}</p>
            </div>
          </div>
        ))}
      </div>
      <h2 className="text-base font-bold text-white mt-6">What Can I Redeem FREE Coins For?</h2>
      <ul className="list-disc list-inside space-y-1.5 pl-2" style={{ color: '#8A9096' }}>
        <li>Groceries (cold drinks, biscuits, everyday essentials)</li>
        <li>Mobile recharges</li>
        <li>OTT passes (streaming vouchers)</li>
        <li>Gift vouchers</li>
        <li>Digital rewards</li>
      </ul>
      <p className="mt-3">Visit <a href="/shop" style={{ color: '#C6A052' }}>free11.com/shop</a> to browse all available rewards. Zero cash payment required — your coins cover everything.</p>
    </div>
  );
}

// ── Main Blog Component ──────────────────────────────────────

const BLOG_INDEX = [
  { slug: 'what-is-free11', emoji: '🎯', label: 'What is FREE11?' },
  { slug: 'cricket-guide', emoji: '🏏', label: 'Cricket Prediction Guide' },
  { slug: 'free-rummy-india', emoji: '🃏', label: 'Free Rummy India' },
  { slug: 'free-teen-patti', emoji: '🎴', label: 'Free Teen Patti' },
  { slug: 'free-poker-india', emoji: '♠️', label: 'Free Poker India' },
  { slug: 'cricket-players-2026', emoji: '⭐', label: 'Cricket Players 2026' },
  { slug: 'earn-free-coins-india', emoji: '💰', label: 'Earn Free Coins India' },
];

export default function Blog() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const activeSlug = slug || 'cricket-guide';
  const article = ARTICLES[activeSlug];

  if (!article) {
    return (
      <div className="min-h-screen pb-24" style={{ background: '#0F1115' }}>
        <div className="max-w-2xl mx-auto px-4 pt-10 text-center">
          <p style={{ color: '#8A9096' }}>Article not found.</p>
          <Link to="/blog" style={{ color: '#C6A052' }}>Back to Blog</Link>
        </div>
        <Navbar />
      </div>
    );
  }

  const ContentComponent = article.content;

  return (
    <div className="min-h-screen pb-24" style={{ background: '#0F1115' }}>
      <div className="max-w-2xl mx-auto px-4 pt-6">

        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5 text-xs mb-4" aria-label="breadcrumb" style={{ color: '#8A9096' }}>
          <Link to="/" className="hover:text-white transition-colors">Home</Link>
          <ChevronRight className="w-3 h-3" />
          <Link to="/blog" className="hover:text-white transition-colors">Blog</Link>
          <ChevronRight className="w-3 h-3" />
          <span style={{ color: '#C6A052' }}>{article.title.split('—')[0].trim()}</span>
        </nav>

        {/* Article Index Pills */}
        <div className="flex gap-2 overflow-x-auto pb-2 mb-5 scrollbar-hide">
          {BLOG_INDEX.map(b => (
            <Link key={b.slug} to={`/blog/${b.slug}`}
              className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full transition-all"
              style={b.slug === activeSlug
                ? { background: '#C6A052', color: '#0F1115', fontWeight: 700 }
                : { background: 'rgba(255,255,255,0.05)', color: '#8A9096', border: '1px solid rgba(255,255,255,0.08)' }}>
              {b.label}
            </Link>
          ))}
        </div>

        {/* Article Header */}
        <header className="mb-6">
          <div className="flex flex-wrap gap-2 mb-3">
            {article.keywords.slice(0, 3).map(kw => (
              <span key={kw} className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full"
                style={{ background: 'rgba(198,160,82,0.1)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.2)' }}>
                <Tag className="w-2.5 h-2.5" />{kw}
              </span>
            ))}
          </div>
          <h1 className="text-xl font-black text-white leading-tight mb-3" style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.02em' }}>
            {article.title}
          </h1>
          <div className="flex items-center gap-3 text-xs" style={{ color: '#8A9096' }}>
            <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{article.published}</span>
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{article.readTime}</span>
            <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />FREE11 Team</span>
          </div>
        </header>

        {/* Article Body */}
        <article>
          <ContentComponent />
        </article>

        {/* CTA */}
        <div className="mt-8 p-5 rounded-2xl text-center" style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.15), rgba(198,160,82,0.05))', border: '1px solid rgba(198,160,82,0.3)' }}>
          <p className="text-base font-bold text-white mb-1" style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.05em' }}>READY TO EARN REAL REWARDS?</p>
          <p className="text-xs mb-4" style={{ color: '#8A9096' }}>Join FREE11. Play free. Earn FREE Coins. Redeem for real rewards.</p>
          <Link to="/register" className="inline-block px-6 py-2.5 rounded-full text-sm font-bold" style={{ background: '#C6A052', color: '#0F1115' }}>
            Start Earning Free — Register Now
          </Link>
        </div>

        {/* FAQ Section */}
        {article.faqs && article.faqs.length > 0 && (
          <section className="mt-8" itemScope itemType="https://schema.org/FAQPage">
            <h2 className="text-base font-bold text-white mb-4">Frequently Asked Questions</h2>
            <div className="space-y-3">
              {article.faqs.map((faq, i) => (
                <div key={i} className="p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}
                  itemScope itemProp="mainEntity" itemType="https://schema.org/Question">
                  <p className="text-sm font-semibold text-white mb-2" itemProp="name">{faq.q}</p>
                  <div itemScope itemProp="acceptedAnswer" itemType="https://schema.org/Answer">
                    <p className="text-xs leading-relaxed" style={{ color: '#8A9096' }} itemProp="text">{faq.a}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Related Articles */}
        <section className="mt-8 mb-6">
          <h2 className="text-sm font-bold text-white mb-3">More from FREE11 Blog</h2>
          <div className="grid grid-cols-2 gap-3">
            {BLOG_INDEX.filter(b => b.slug !== activeSlug).slice(0, 4).map(b => (
              <Link key={b.slug} to={`/blog/${b.slug}`}
                className="p-3 rounded-xl transition-all hover:border-amber-500/30"
                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                <span className="text-lg">{b.emoji}</span>
                <p className="text-xs font-medium text-white mt-1">{b.label}</p>
              </Link>
            ))}
          </div>
        </section>

      </div>
      <Navbar />
    </div>
  );
}
