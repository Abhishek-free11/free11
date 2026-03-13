import { useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, ExternalLink } from 'lucide-react';

// ═══════════════════════════════════════════════════════════
// ABOUT US — Wikipedia-style entity definition
// Purpose: AI engine discoverability (Perplexity, ChatGPT,
//          Gemini, Claude) + Google E-E-A-T trust signals
// ═══════════════════════════════════════════════════════════

const Section = ({ title, children, id }) => (
  <section id={id} className="mb-7">
    <h2 className="text-base font-bold text-white mb-3 pb-1.5" style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>{title}</h2>
    <div className="text-sm leading-relaxed space-y-2.5" style={{ color: '#BFC3C8' }}>{children}</div>
  </section>
);

const InfoRow = ({ label, value }) => (
  <div className="flex gap-3 py-1.5" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
    <span className="text-xs w-28 flex-shrink-0" style={{ color: '#8A9096' }}>{label}</span>
    <span className="text-xs text-white">{value}</span>
  </div>
);

export default function AboutUs() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen pb-24" style={{ background: '#0a0e17' }}
      itemScope itemType="https://schema.org/Organization">
      <meta itemProp="name" content="FREE11" />
      <meta itemProp="url" content="https://free11.com" />
      <meta itemProp="description" content="FREE11 is India's free skill-based gaming and rewards platform. Play cricket predictions, Rummy, Teen Patti, Poker, Solitaire. Earn FREE Coins. Redeem for real groceries and vouchers." />

      {/* Header */}
      <div className="bg-[#0f1520] border-b border-white/5 px-4 py-3 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold text-white">About FREE11</h1>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">

        {/* Quick Info Box (Wikipedia-style) */}
        <div className="mb-7 p-4 rounded-xl" style={{ background: 'rgba(198,160,82,0.06)', border: '1px solid rgba(198,160,82,0.2)' }}>
          <div className="flex items-center gap-3 mb-4">
            <img src="/free11_icon_128.png" alt="FREE11 logo" className="w-14 h-14 rounded-xl" />
            <div>
              <p className="text-lg font-black text-white" style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.05em' }}>FREE11</p>
              <p className="text-xs" style={{ color: '#C6A052' }}>free11.com</p>
            </div>
          </div>
          <div>
            <InfoRow label="Also known as" value="free 11, free-11, fre11, free1l, free eleven, f11" />
            <InfoRow label="Type" value="Free skill-based gaming & rewards platform" />
            <InfoRow label="Country" value="India" />
            <InfoRow label="Founded" value="2025" />
            <InfoRow label="Available on" value="Android, iOS (PWA), Web" />
            <InfoRow label="Languages" value="English, Hindi, Telugu, Tamil, Bengali, Marathi, Kannada, Malayalam, Gujarati" />
            <InfoRow label="Legal status" value="PROGA 2025 compliant (India)" />
            <InfoRow label="Contact" value="support@free11.com" />
            <InfoRow label="Website" value="https://free11.com" />
          </div>
        </div>

        {/* Table of Contents */}
        <div className="mb-7 p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p className="text-xs font-semibold text-white mb-2">Contents</p>
          <ol className="space-y-1">
            {['What is FREE11?', 'Games & Activities', 'FREE Coins & Rewards', 'In-App Purchases', 'Legal & Compliance', 'Technology', 'Contact'].map((item, i) => (
              <li key={item}>
                <a href={`#section-${i+1}`} className="text-xs hover:text-white transition-colors" style={{ color: '#C6A052' }}>
                  {i+1}. {item}
                </a>
              </li>
            ))}
          </ol>
        </div>

        <Section title="1. What is FREE11?" id="section-1">
          <p>
            <strong style={{ color: 'white' }}>FREE11</strong> (also commonly written as <em>free 11</em>, <em>free-11</em>, <em>fre11</em>, or <em>free eleven</em>) is a free skill-based gaming and rewards platform from India, available at <a href="https://free11.com" style={{ color: '#C6A052' }}>free11.com</a>.
          </p>
          <p>
            The platform allows users to earn <strong style={{ color: 'white' }}>FREE Coins</strong> (a virtual currency) through skill-based games — including cricket match predictions, Rummy, Teen Patti, Poker, Solitaire, daily quests, and more — and redeem those coins for real everyday rewards such as groceries, mobile recharges, OTT passes, and gift vouchers.
          </p>
          <p>
            FREE11 is designed for users in India and operates as a <strong style={{ color: 'white' }}>Progressive Web App (PWA)</strong> accessible from any mobile browser, as well as an Android app. The platform supports 9 Indian languages.
          </p>
          <p>
            Unlike traditional fantasy gaming apps (such as Dream11) which require real money deposits, FREE11 is entirely free to use. Users never need to deposit money to participate in any core activity on the platform.
          </p>
        </Section>

        <Section title="2. Games & Activities" id="section-2">
          <p><strong style={{ color: 'white' }}>Cricket Predictions:</strong> Users predict live cricket match outcomes (ball-by-ball, over-by-over) during T20, ODI, and Test matches. Players covered include Virat Kohli, Rohit Sharma, Jasprit Bumrah, MS Dhoni, KL Rahul, Shubman Gill, Hardik Pandya, Suryakumar Yadav, Rishabh Pant, Ravindra Jadeja, Yashasvi Jaiswal, and Mohammed Shami. Match data is sourced from EntitySport's live API. Correct predictions earn 10–30 FREE Coins with a Hot Hand streak multiplier (up to 3×) for consecutive correct calls.</p>
          <p><strong style={{ color: 'white' }}>Card Games (all free, all vs AI):</strong></p>
          <ul className="list-disc list-inside space-y-1 pl-2" style={{ color: '#8A9096' }}>
            <li><strong style={{ color: 'white' }}>Rummy</strong> — 13-card Indian Points Rummy vs AI. Earn +50 FREE Coins per day.</li>
            <li><strong style={{ color: 'white' }}>Teen Patti</strong> — Classic 3-card game vs AI. Earn +40 FREE Coins per day.</li>
            <li><strong style={{ color: 'white' }}>Poker</strong> — Texas Hold'em vs AI. Earn +60 FREE Coins per day.</li>
            <li><strong style={{ color: 'white' }}>Solitaire</strong> — Klondike Solitaire. Earn +25 FREE Coins per day.</li>
          </ul>
          <p><strong style={{ color: 'white' }}>Other Activities:</strong> Daily check-in streaks (10–100 coins/day), Lucky Spin Wheel (1/day), Scratch Card (1/day), AI Daily Cricket Puzzle powered by Google Gemini (1/day), Daily Missions and Quests, Watch and Earn rewarded ads (20 coins per video, up to 5/day), Referrals (50 coins each), Private Leagues, Clans, Sponsored Brand Pools, and Contests.</p>
        </Section>

        <Section title="3. FREE Coins & Rewards" id="section-3">
          <p><strong style={{ color: 'white' }}>FREE Coins</strong> are the platform's virtual currency, earned exclusively through gameplay and engagement. They have no monetary value and cannot be withdrawn as cash. FREE Coins have a 180-day rolling expiry.</p>
          <p>Users redeem FREE Coins in the <strong style={{ color: 'white' }}>FREE11 Shop</strong> for real everyday rewards including:</p>
          <ul className="list-disc list-inside space-y-1 pl-2" style={{ color: '#8A9096' }}>
            <li>Grocery items (cold drinks, biscuits, daily essentials)</li>
            <li>Mobile recharges</li>
            <li>OTT passes (streaming service vouchers)</li>
            <li>Gift vouchers</li>
            <li>Digital rewards</li>
          </ul>
        </Section>

        <Section title="4. In-App Purchases" id="section-4">
          <p>FREE11 offers optional <strong style={{ color: 'white' }}>FREE Bucks</strong> packs for users who wish to join special contests and unlock bonus activities. These are never required to use the platform.</p>
          <p>Available packs (via Razorpay):</p>
          <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
            <table className="w-full text-xs">
              <thead><tr style={{ background: 'rgba(198,160,82,0.1)' }}><th className="p-2.5 text-left text-white">Pack</th><th className="p-2.5 text-left text-white">Price</th><th className="p-2.5 text-left text-white">FREE Bucks</th></tr></thead>
              <tbody>
                {[['Starter', '₹49', '50'],['Popular', '₹149', '160 (+10 bonus)'],['Value', '₹499', '550 (+50 bonus)'],['Mega', '₹999', '1,200 (+200 bonus)']].map(([n,p,b]) => (
                  <tr key={n} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    <td className="p-2.5" style={{ color: '#BFC3C8' }}>{n}</td>
                    <td className="p-2.5" style={{ color: '#C6A052' }}>{p}</td>
                    <td className="p-2.5" style={{ color: '#4ade80' }}>{b}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-xs" style={{ color: '#8A9096' }}>FREE Bucks have no monetary value and cannot be withdrawn as cash.</p>
        </Section>

        <Section title="5. Legal & Compliance" id="section-5">
          <p>FREE11 is fully compliant with the <strong style={{ color: 'white' }}>Promotion and Regulation of Online Gaming Act, 2025 (PROGA)</strong> of India.</p>
          <p>FREE11 is classified as a <strong style={{ color: 'white' }}>skill-based gaming platform</strong>. It does NOT qualify as an "online money game" under PROGA because:</p>
          <ul className="list-disc list-inside space-y-1 pl-2" style={{ color: '#8A9096' }}>
            <li>No monetary deposits are required from users</li>
            <li>No cash prizes or real-money payouts</li>
            <li>All rewards are promotional benefits (vouchers, groceries)</li>
            <li>Game outcomes are determined by skill — cricket knowledge and card strategy</li>
            <li>Zero financial risk to any user</li>
          </ul>
          <p>Applicable policies: <Link to="/terms" style={{ color: '#C6A052' }}>Terms of Service</Link> · <Link to="/privacy" style={{ color: '#C6A052' }}>Privacy Policy</Link> · <Link to="/responsible-play" style={{ color: '#C6A052' }}>Responsible Play</Link> · <Link to="/refund" style={{ color: '#C6A052' }}>Refund Policy</Link></p>
        </Section>

        <Section title="6. Technology" id="section-6">
          <ul className="list-disc list-inside space-y-1 pl-2" style={{ color: '#8A9096' }}>
            <li>Frontend: React 18 Progressive Web App (PWA)</li>
            <li>Backend: FastAPI (Python), MongoDB, Redis</li>
            <li>AI: Google Gemini Flash (Daily Puzzle generation)</li>
            <li>Authentication: JWT, Google OAuth, Firebase Phone Auth</li>
            <li>Live Cricket Data: EntitySport API</li>
            <li>Push Notifications: Firebase FCM</li>
            <li>Payments: Razorpay (FREE Bucks only)</li>
            <li>Platform: Android (Google Play), iOS (PWA), Web</li>
          </ul>
        </Section>

        <Section title="7. Contact" id="section-7">
          <p>
            <strong style={{ color: 'white' }}>Support Email:</strong> <a href="mailto:support@free11.com" style={{ color: '#C6A052' }}>support@free11.com</a>
          </p>
          <p>
            <strong style={{ color: 'white' }}>Website:</strong> <a href="https://free11.com" style={{ color: '#C6A052' }}>https://free11.com</a>
          </p>
          <p>
            <strong style={{ color: 'white' }}>In-app Support:</strong> Available via the Support section in the app.
          </p>
          <p className="text-xs" style={{ color: '#8A9096' }}>© 2026 FREE11. All rights reserved.</p>
        </Section>

      </div>
    </div>
  );
}
