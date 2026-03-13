import { useNavigate, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { Calendar, Clock, Tag, ChevronRight, BookOpen } from 'lucide-react';

// Section 7 — SEO Blog
// Route: /blog/cricket-guide
// Keywords: free11, free fantasy cricket India, free11 T20 predictions rewards

const ARTICLE = {
  slug: 'cricket-guide',
  title: 'FREE11 Cricket 2026 Guide: Skill Predictions & Free Rewards',
  published: '2026-03-01',
  readTime: '4 min read',
  keywords: ['free11', 'free fantasy cricket India', 'T20 2026 predictions', 'free cricket rewards India'],
  faqs: [
    {
      q: 'What is FREE11?',
      a: 'FREE11 is a free fantasy cricket app for India. You predict cricket outcomes over-by-over, earn FREE Coins through skill, and redeem them for real groceries, recharges, and vouchers — no deposits or cash involved.',
    },
    {
      q: 'Is FREE11 free to play?',
      a: 'Yes — 100% free. There are no entry fees, no deposits, and no real-money wagering. FREE11 is a skill-based sports entertainment platform. You earn rewards purely through skill-based cricket predictions.',
    },
    {
      q: 'How do rewards work on FREE11?',
      a: 'You earn FREE Coins by correctly predicting match outcomes. These coins accumulate in your wallet and can be redeemed in the Shop for everyday groceries, OTT passes, mobile recharges, and more — all at zero cost to you.',
    },
    {
      q: 'Can I play FREE11 during the cricket season?',
      a: 'Absolutely! The T20 cricket season is the flagship season for FREE11. Over-by-over ball predictions during cricket matches give you maximum earning potential. We also run Sponsored Pools funded by brands exclusively during the season.',
    },
    {
      q: 'Is FREE11 legal in India?',
      a: 'YES. FREE11 is fully compliant with the Promotion and Regulation of Online Gaming Act, 2025 (PROGA). It is a pure skill-based game — no deposits, no cash prizes, only promotional benefits earned through demonstrated prediction skill.',
    },
  ],
};

export default function Blog() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen pb-24" style={{ background: '#0F1115' }}>
      <div className="max-w-2xl mx-auto px-4 pt-6">

        {/* Breadcrumb */}
        <div className="flex items-center gap-1.5 text-xs mb-4" style={{ color: '#8A9096' }}>
          <Link to="/" className="hover:text-white transition-colors">Home</Link>
          <ChevronRight className="w-3 h-3" />
          <span style={{ color: '#C6A052' }}>Blog</span>
        </div>

        {/* Article header */}
        <header className="mb-6">
          <div className="flex flex-wrap gap-2 mb-3">
            {ARTICLE.keywords.slice(0, 3).map(kw => (
              <span key={kw} className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full" style={{ background: 'rgba(198,160,82,0.1)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.2)' }}>
                <Tag className="w-2.5 h-2.5" />{kw}
              </span>
            ))}
          </div>
          <h1 className="text-3xl font-bold text-white mb-3 leading-tight" style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.02em' }}>
            {ARTICLE.title}
          </h1>
          <div className="flex items-center gap-3 text-xs" style={{ color: '#8A9096' }}>
            <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{ARTICLE.published}</span>
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{ARTICLE.readTime}</span>
            <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />FREE11 Team</span>
          </div>
        </header>

        {/* Hero image */}
        <div className="rounded-2xl overflow-hidden mb-6" style={{ border: '1px solid rgba(198,160,82,0.2)' }}>
          <img
            src="https://static.prod-images.emergentagent.com/jobs/cd09d64a-beec-4caf-8b0f-ee03c7f75011/images/f1a4d946bcfce67e7ccdeffb35325a9ffaea5fe941eac9953ab40face0b7f280.png"
            alt="T20 Cricket Season 2026 — FREE11"
            className="w-full h-48 object-cover"
            loading="lazy"
          />
          <div className="px-4 py-2" style={{ background: 'rgba(198,160,82,0.05)' }}>
            <p className="text-xs text-center" style={{ color: '#8A9096' }}>T20 Cricket Season 2026 — Play Cricket. Earn Essentials. No deposits.</p>
          </div>
        </div>

        {/* Article body */}
        <article className="prose max-w-none" style={{ color: '#BFC3C8' }}>

          <h2 className="text-xl font-bold text-white mb-3" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>
            What is FREE11 and How Does It Work?
          </h2>
          <p className="text-sm leading-relaxed mb-4">
            <strong style={{ color: '#C6A052' }}>FREE11</strong> is a free skill-based gaming platform built around cricket and card games. Unlike traditional fantasy platforms that require deposits or carry financial risk, FREE11 is entirely free to play. You earn <strong style={{ color: 'white' }}>FREE Coins</strong> by making accurate cricket predictions, then redeem those coins for real everyday products: cold drinks, biscuits, wheat flour, mobile recharges, OTT passes, and much more.
          </p>
          <p className="text-sm leading-relaxed mb-4">
            The platform is built around <strong style={{ color: 'white' }}>skill-based free fantasy cricket India</strong> gameplay. Every over of every T20 cricket match becomes an earning opportunity. Predict runs, wickets, or boundaries correctly and watch your coin balance grow in real time.
          </p>

          <h2 className="text-xl font-bold text-white mb-3 mt-6" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>
            FREE11 Cricket 2026 Predictions — How to Earn Maximum Coins
          </h2>
          <p className="text-sm leading-relaxed mb-3">
            During the T20 cricket season, FREE11 activates its full prediction engine with live over-by-over gameplay. Here's how to maximise your FREE Coin earnings:
          </p>
          <ul className="space-y-2 mb-4 pl-4">
            {[
              { title: 'Prediction Streak Bonus ("Hot Hand")', desc: 'Get 3+ correct predictions in a row to activate the Hot Hand multiplier — earn up to 3× coins per correct prediction.' },
              { title: 'Daily Check-In Streak', desc: 'Log in every day during the cricket season to compound your streak bonus. 7-day streaks unlock special reward drops.' },
              { title: 'Sponsored Pool Contests', desc: 'Join brand-funded pools. Predict best, win coins tied to real grocery and lifestyle products.' },
              { title: 'Daily AI Puzzle', desc: 'FREE11\'s Gemini-powered puzzle gives you a fresh cricket knowledge challenge daily for bonus coins.' },
              { title: 'Referral Rewards', desc: 'Invite friends to FREE11 and earn coins for every successful referral who makes their first prediction.' },
            ].map(({ title, desc }) => (
              <li key={title} className="text-sm" style={{ color: '#BFC3C8' }}>
                <strong style={{ color: '#C6A052' }}>{title}:</strong> {desc}
              </li>
            ))}
          </ul>

          <h2 className="text-xl font-bold text-white mb-3 mt-6" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>
            FREE11 Prediction Rewards — What Can You Redeem?
          </h2>
          <p className="text-sm leading-relaxed mb-3">
            The <Link to="/shop" className="underline" style={{ color: '#C6A052' }}>FREE11 Shop</Link> offers 50+ brand-funded rewards across two categories:
          </p>
          <div className="grid grid-cols-2 gap-3 mb-4">
            {[
              { cat: 'Groceries', items: 'Cola drinks · Biscuits · Wheat flour · Rice · Oil · Dal · Zepto bundles', color: '#4ade80' },
              { cat: 'Lifestyle', items: 'Mobile recharge · OTT passes · Wireless earbuds · Gift vouchers · Fashion', color: '#C6A052' },
            ].map(({ cat, items, color }) => (
              <div key={cat} className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.04)', border: `1px solid ${color}30` }}>
                <p className="text-xs font-bold mb-1" style={{ color }}>{cat}</p>
                <p className="text-xs" style={{ color: '#8A9096' }}>{items}</p>
              </div>
            ))}
          </div>
          <p className="text-sm leading-relaxed mb-4">
            All rewards are fulfilled via our partner network. Coins cover the reward cost — no additional payment needed from you.
          </p>

          <h2 className="text-xl font-bold text-white mb-3 mt-6" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>
            Is FREE11 Safe, Legal and PROGA Compliant?
          </h2>
          <p className="text-sm leading-relaxed mb-4">
            FREE11 operates exclusively under India's Promotion and Regulation of Online Gaming Act, 2025 (PROGA) framework. It is a <strong style={{ color: 'white' }}>skill-based platform</strong> — not a gambling or betting product. There are no deposits, no cash prizes, and no financial risk. All prediction outcomes are determined by your cricket knowledge and analytical skill, not chance.
          </p>

          {/* CTA */}
          <div className="rounded-2xl p-5 my-6 text-center" style={{ background: 'linear-gradient(135deg, rgba(198,160,82,0.1), rgba(198,160,82,0.05))', border: '1px solid rgba(198,160,82,0.25)' }}>
            <p className="text-lg font-bold text-white mb-1" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>PLAY FREE. EARN ESSENTIALS.</p>
            <p className="text-xs mb-3" style={{ color: '#8A9096' }}>No deposit required. Cricket Season 2026 live now.</p>
            <button
              onClick={() => navigate('/predict')}
              className="px-6 py-2.5 rounded-xl text-sm font-bold"
              style={{ background: 'linear-gradient(135deg, #C6A052, #E0B84F)', color: '#0F1115' }}
              data-testid="blog-cta-predict"
            >
              Start Predicting Free →
            </button>
          </div>
        </article>

        {/* FAQ Schema (also rendered visually) */}
        <section className="mt-6 mb-8">
          <h2 className="text-xl font-bold text-white mb-4" style={{ fontFamily: 'Bebas Neue, sans-serif' }}>
            Frequently Asked Questions
          </h2>
          <div className="space-y-3">
            {ARTICLE.faqs.map(({ q, a }) => (
              <details
                key={q}
                className="rounded-xl overflow-hidden group"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}
              >
                <summary className="flex items-center justify-between px-4 py-3 cursor-pointer text-sm font-medium text-white list-none" data-testid={`faq-${q.slice(0, 20)}`}>
                  {q}
                  <ChevronRight className="w-4 h-4 transition-transform group-open:rotate-90 flex-shrink-0 ml-2" style={{ color: '#C6A052' }} />
                </summary>
                <div className="px-4 pb-3 text-xs leading-relaxed" style={{ color: '#8A9096' }}>{a}</div>
              </details>
            ))}
          </div>
        </section>

        {/* Internal links */}
        <div className="grid grid-cols-3 gap-2 mb-8">
          {[
            { label: 'Predict Now', path: '/predict' },
            { label: 'Browse Shop', path: '/shop' },
            { label: 'Join Pools', path: '/sponsored' },
          ].map(({ label, path }) => (
            <Link key={path} to={path}
              className="text-center py-2.5 rounded-xl text-xs font-bold"
              style={{ background: 'rgba(198,160,82,0.08)', color: '#C6A052', border: '1px solid rgba(198,160,82,0.2)' }}
            >
              {label}
            </Link>
          ))}
        </div>

      </div>
      <Navbar />
    </div>
  );
}
