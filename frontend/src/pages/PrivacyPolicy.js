import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Shield, Eye, Lock, Trash2, Bell, CreditCard, Gamepad2, Users, Globe } from 'lucide-react';

const S = ({ title, icon: Icon, children, id }) => (
  <div className="mb-8" id={id}>
    <div className="flex items-center gap-2.5 mb-3 pb-2" style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
      {Icon && <Icon className="w-4 h-4 flex-shrink-0" style={{ color: '#C6A052' }} />}
      <h2 className="text-sm font-bold text-white">{title}</h2>
    </div>
    <div className="text-sm leading-relaxed space-y-3" style={{ color: '#BFC3C8' }}>{children}</div>
  </div>
);

const Table = ({ headers, rows }) => (
  <div className="rounded-xl overflow-hidden my-3" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
    <table className="w-full text-xs">
      <thead>
        <tr style={{ background: 'rgba(198,160,82,0.08)' }}>
          {headers.map(h => <th key={h} className="p-2.5 text-left text-white font-semibold">{h}</th>)}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
            {row.map((cell, j) => <td key={j} className="p-2.5" style={{ color: j === 0 ? '#fff' : '#8A9096' }}>{cell}</td>)}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const TOCItem = ({ num, label, anchor }) => (
  <li>
    <a href={`#${anchor}`} className="text-xs hover:text-white transition-colors" style={{ color: '#C6A052' }}>
      {num}. {label}
    </a>
  </li>
);

export default function PrivacyPolicy() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen pb-24" style={{ background: '#0a0e17' }}>
      <div className="sticky top-0 z-10 flex items-center gap-3 px-4 py-3" style={{ background: '#0f1520', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <button onClick={() => navigate(-1)}><ArrowLeft className="w-5 h-5 text-gray-400" /></button>
        <h1 className="text-lg font-bold text-white">Privacy Policy</h1>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-6">

        {/* Header */}
        <div className="mb-6 p-4 rounded-xl" style={{ background: 'rgba(198,160,82,0.06)', border: '1px solid rgba(198,160,82,0.2)' }}>
          <p className="text-xs font-bold text-white mb-1">FREE11 — Privacy Policy</p>
          <p className="text-xs" style={{ color: '#8A9096' }}>Effective Date: 1 March 2026 · Last Updated: March 2026</p>
          <p className="text-xs mt-2" style={{ color: '#8A9096' }}>
            This policy applies to all users of the FREE11 platform available at free11.com, the FREE11 Android app, and any related services. By using FREE11, you agree to the collection and use of information as described in this policy.
          </p>
          <p className="text-xs mt-2" style={{ color: '#8A9096' }}>
            FREE11 is operated in compliance with the <strong style={{ color: 'white' }}>Digital Personal Data Protection Act, 2023 (DPDP Act)</strong>, the Information Technology Act, 2000, and all applicable Indian laws.
          </p>
        </div>

        {/* Table of Contents */}
        <div className="mb-8 p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)' }}>
          <p className="text-xs font-bold text-white mb-3">Contents</p>
          <ol className="space-y-1.5 columns-2">
            <TOCItem num="1" label="Who We Are" anchor="who-we-are" />
            <TOCItem num="2" label="Data We Collect" anchor="data-collect" />
            <TOCItem num="3" label="How We Use Data" anchor="how-we-use" />
            <TOCItem num="4" label="Legal Basis" anchor="legal-basis" />
            <TOCItem num="5" label="Data Sharing" anchor="data-sharing" />
            <TOCItem num="6" label="Third-Party Services" anchor="third-parties" />
            <TOCItem num="7" label="Data Retention" anchor="retention" />
            <TOCItem num="8" label="Your Rights" anchor="your-rights" />
            <TOCItem num="9" label="Cookies & Tracking" anchor="cookies" />
            <TOCItem num="10" label="Children's Policy" anchor="children" />
            <TOCItem num="11" label="Data Security" anchor="security" />
            <TOCItem num="12" label="Changes to Policy" anchor="changes" />
            <TOCItem num="13" label="Contact Us" anchor="contact" />
          </ol>
        </div>

        {/* 1. Who We Are */}
        <S title="1. Who We Are" icon={Globe} id="who-we-are">
          <p><strong style={{ color: 'white' }}>FREE11</strong> is a free skill-based gaming and rewards platform. We operate at <strong style={{ color: 'white' }}>free11.com</strong> and via the FREE11 Android app. We are a Data Fiduciary under the Digital Personal Data Protection Act, 2023.</p>
          <p><strong style={{ color: 'white' }}>Contact:</strong> support@free11.com</p>
          <p className="text-xs" style={{ color: '#8A9096' }}>This platform is intended exclusively for users who are 18 years or older and located in India.</p>
        </S>

        {/* 2. Data We Collect */}
        <S title="2. Data We Collect" icon={Eye} id="data-collect">
          <p>We collect data across the following categories:</p>

          <p className="text-xs font-semibold text-white mt-4 mb-1">A. Personal Identity Data</p>
          <Table
            headers={['Data', 'When Collected', 'Purpose']}
            rows={[
              ['Full name', 'Registration', 'Account identity & display'],
              ['Email address', 'Registration / Google Auth', 'Login, OTP, notifications'],
              ['Phone number', 'Phone Auth (OTP)', 'SMS verification & login'],
              ['Profile photo', 'Google OAuth (if granted)', 'Profile display'],
              ['Date of birth', 'Registration / KYC', 'Age verification (18+ required)'],
              ['Google account info', 'Google Sign-In', 'Login identity'],
            ]}
          />

          <p className="text-xs font-semibold text-white mt-4 mb-1">B. Device & Technical Data</p>
          <Table
            headers={['Data', 'When Collected', 'Purpose']}
            rows={[
              ['Device fingerprint / hash', 'Every session', 'Fraud prevention, duplicate account detection'],
              ['IP address', 'Every request', 'Geo-fencing (India-only), fraud detection'],
              ['Country / region (IP-based)', 'Every session', 'Regulatory geo-restriction'],
              ['Browser, OS, device type', 'Every session', 'App compatibility & analytics'],
              ['Firebase FCM push token', 'App install / login', 'Push notifications'],
              ['PWA install status', 'Browser event', 'Feature & onboarding delivery'],
              ['Session timestamps & duration', 'Every session', 'Retention analytics, abuse detection'],
            ]}
          />

          <p className="text-xs font-semibold text-white mt-4 mb-1">C. Gameplay & Behavioural Data</p>
          <Table
            headers={['Data', 'When Collected', 'Purpose']}
            rows={[
              ['Prediction history (match, choice, result)', 'Every prediction', 'Score calculation, coin awards, leaderboard'],
              ['Card game win/loss history', 'Every game session', 'Daily coin tracking'],
              ['Check-in streak history', 'Daily check-in', 'Streak rewards'],
              ['Spin wheel & scratch card history', 'Daily activity', 'Coin tracking, abuse prevention'],
              ['Mission & quest progress', 'Missions engine', 'Reward claiming'],
              ['AI puzzle answers & scores', 'Daily puzzle', 'Performance tracking'],
              ['Ad watch history', 'Watch & Earn', 'Coin grant verification (5/day limit)'],
              ['Contest entries & results', 'Contest participation', 'Prize distribution'],
              ['Sponsored pool entries', 'Pool participation', 'Brand campaign tracking'],
              ['Referral links used / referred users', 'Referral', 'Coin payouts'],
              ['Language preference', 'Settings', 'Localisation'],
              ['Notification opt-in/out status', 'Settings', 'FCM notification delivery'],
              ['Wishlist goal selection', 'Profile', 'Personalised reward nudging'],
            ]}
          />

          <p className="text-xs font-semibold text-white mt-4 mb-1">D. Financial & Transaction Data</p>
          <Table
            headers={['Data', 'When Collected', 'Purpose']}
            rows={[
              ['FREE Coin balance & full transaction history', 'All earn/spend events', 'Ledger, support, audits'],
              ['FREE Bucks balance & purchase history', 'All purchase events', 'Purchase records'],
              ['Razorpay order ID & payment status', 'FREE Bucks purchase', 'Payment verification (no card data stored)'],
              ['Cashfree transaction records', 'Future payments', 'Payment verification'],
              ['Redemption orders & voucher codes issued', 'Shop redemption', 'Fulfillment & order history'],
            ]}
          />
          <p className="text-xs mt-1" style={{ color: '#8A9096' }}>Note: FREE11 does not store card numbers, CVV, UPI PINs, or banking credentials. All payment processing is handled by Razorpay and Cashfree on their PCI-DSS compliant infrastructure.</p>

          <p className="text-xs font-semibold text-white mt-4 mb-1">E. Social & Community Data</p>
          <Table
            headers={['Data', 'When Collected', 'Purpose']}
            rows={[
              ['Clan membership & activity', 'Clan join/create', 'Social features, clan leaderboard'],
              ['Private league participation', 'League join', 'Contest scoring'],
              ['Leaderboard ranking & username', 'All gameplay', 'Public leaderboard display'],
              ['Support tickets & communications', 'Support page', 'Issue resolution'],
            ]}
          />

          <p className="text-xs font-semibold text-white mt-4 mb-1">F. Future Data (as platform expands)</p>
          <Table
            headers={['Data', 'Trigger', 'Purpose']}
            rows={[
              ['KYC documents (Aadhaar / PAN)', 'If regulatory obligation arises', 'Identity verification for high-value redemptions'],
              ['Shipping address', 'If physical product delivery enabled', 'Grocery & physical reward delivery'],
              ['UPI ID or bank account details', 'If direct digital payouts introduced', 'Reward disbursement'],
              ['Survey & feedback responses', 'Optional user surveys', 'Product improvement'],
              ['In-app chat messages', 'If social chat feature added', 'Community moderation'],
            ]}
          />
        </S>

        {/* 3. How We Use Data */}
        <S title="3. How We Use Your Data" icon={Gamepad2} id="how-we-use">
          <ul className="space-y-2 list-disc list-inside" style={{ color: '#8A9096' }}>
            <li><strong style={{ color: 'white' }}>Account management:</strong> Register, authenticate, and manage your FREE11 account</li>
            <li><strong style={{ color: 'white' }}>Platform operation:</strong> Process predictions, card games, missions, contests, and all core features</li>
            <li><strong style={{ color: 'white' }}>Coin economy:</strong> Track earnings, spending, expiry, and maintain your ledger</li>
            <li><strong style={{ color: 'white' }}>Reward fulfilment:</strong> Process voucher and grocery redemptions via partner networks</li>
            <li><strong style={{ color: 'white' }}>Payment processing:</strong> Facilitate optional FREE Bucks purchases via Razorpay/Cashfree</li>
            <li><strong style={{ color: 'white' }}>Fraud prevention:</strong> Detect and prevent duplicate accounts, coin farming, and abuse</li>
            <li><strong style={{ color: 'white' }}>Push notifications:</strong> Send match alerts, coin updates, and feature announcements (opt-out available)</li>
            <li><strong style={{ color: 'white' }}>Email communications:</strong> Send OTPs, welcome emails, and important account updates via Resend</li>
            <li><strong style={{ color: 'white' }}>Legal compliance:</strong> Maintain records required under Indian law (DPDP Act, IT Act, PROGA 2025)</li>
            <li><strong style={{ color: 'white' }}>Analytics & improvement:</strong> Understand platform usage patterns to improve features and performance</li>
            <li><strong style={{ color: 'white' }}>Personalisation:</strong> Show relevant rewards, matches, and game recommendations based on your activity</li>
            <li><strong style={{ color: 'white' }}>Advertising:</strong> Serve AdMob banner and rewarded ads (AdMob may collect device ad identifiers per Google's policies)</li>
          </ul>
        </S>

        {/* 4. Legal Basis */}
        <S title="4. Legal Basis for Processing" icon={Shield} id="legal-basis">
          <p>Under the Digital Personal Data Protection Act, 2023 (DPDP Act), FREE11 processes personal data on the following lawful bases:</p>
          <Table
            headers={['Processing Activity', 'Legal Basis']}
            rows={[
              ['Account registration & core platform operation', 'Consent (explicit at registration)'],
              ['OTP verification & security', 'Legitimate interest / Consent'],
              ['Payment processing (FREE Bucks)', 'Performance of contract'],
              ['Fraud prevention & geo-fencing', 'Legitimate interest (legal obligation)'],
              ['Push notifications & marketing emails', 'Consent (opt-in/opt-out available)'],
              ['Analytics & platform improvement', 'Legitimate interest'],
              ['Legal record-keeping', 'Legal obligation (IT Act, PROGA 2025)'],
              ['KYC / identity verification (future)', 'Legal obligation / Consent'],
            ]}
          />
        </S>

        {/* 5. Data Sharing */}
        <S title="5. Data Sharing" icon={Users} id="data-sharing">
          <p>FREE11 does <strong style={{ color: 'white' }}>NOT sell your personal data</strong> to any third party. We share data only in these circumstances:</p>
          <ul className="space-y-2 list-disc list-inside" style={{ color: '#8A9096' }}>
            <li><strong style={{ color: 'white' }}>Service providers:</strong> Only what is necessary to deliver the service (e.g. Razorpay receives order details for payment)</li>
            <li><strong style={{ color: 'white' }}>Reward fulfilment partners:</strong> Name and delivery details shared with voucher/grocery partners only upon redemption</li>
            <li><strong style={{ color: 'white' }}>Legal obligations:</strong> If required by Indian law, court order, or government authority</li>
            <li><strong style={{ color: 'white' }}>Business transfer:</strong> In the event of a merger or acquisition, user data may be transferred with advance notice</li>
          </ul>
          <p>Your username and leaderboard rank are <strong style={{ color: 'white' }}>publicly visible</strong> on FREE11 leaderboards. Your email, phone number, and financial data are never publicly visible.</p>
        </S>

        {/* 6. Third-Party Services */}
        <S title="6. Third-Party Services" icon={Globe} id="third-parties">
          <Table
            headers={['Service', 'Provider', 'Data Shared', 'Policy']}
            rows={[
              ['Payments', 'Razorpay', 'Order amount, contact', 'razorpay.com/privacy'],
              ['Payments (future)', 'Cashfree', 'Order amount, contact', 'cashfree.com/privacy'],
              ['Push notifications', 'Firebase FCM (Google)', 'FCM token, device info', 'firebase.google.com/support/privacy'],
              ['Phone auth', 'Firebase Auth (Google)', 'Phone number', 'firebase.google.com/support/privacy'],
              ['Google Sign-In', 'Google LLC', 'Name, email, profile photo', 'policies.google.com/privacy'],
              ['Email delivery', 'Resend', 'Email address', 'resend.com/privacy'],
              ['Error monitoring', 'Sentry', 'Error logs, device info', 'sentry.io/privacy'],
              ['Advertising', 'Google AdMob', 'Device ad ID, usage signals', 'policies.google.com/privacy'],
              ['Gift cards (USD)', 'Reloadly', 'Redemption details', 'reloadly.com/privacy'],
              ['Gift cards (future)', 'Xoxoday / Woohoo', 'Redemption details', 'respective privacy policies'],
              ['AI features', 'Google Gemini', 'Puzzle query content', 'policies.google.com/privacy'],
              ['Cricket data', 'EntitySport', 'No personal data', 'entitysport.com'],
            ]}
          />
        </S>

        {/* 7. Data Retention */}
        <S title="7. Data Retention" icon={Trash2} id="retention">
          <Table
            headers={['Data Type', 'Retention Period']}
            rows={[
              ['Account & profile data', 'Until account deletion + 90 days'],
              ['FREE Coin transaction history', 'Until account deletion + 1 year'],
              ['Payment records (FREE Bucks)', '7 years (RBI / tax compliance)'],
              ['Redemption orders', '3 years (consumer protection compliance)'],
              ['Fraud prevention signals (device hash)', '2 years from last activity'],
              ['Push notification tokens', 'Until revoked or account deletion'],
              ['Session & analytics data', '12 months rolling'],
              ['Support communications', '2 years from ticket closure'],
              ['Legal compliance records', 'As required by applicable law (up to 7 years)'],
              ['FREE Coins (validity)', '180 days rolling from date of earning'],
            ]}
          />
          <p className="text-xs mt-2" style={{ color: '#8A9096' }}>When an account is deleted, personal identification data is anonymised or erased within 90 days. Financial transaction records required for legal compliance are retained in anonymised form for the legally mandated period.</p>
        </S>

        {/* 8. Your Rights */}
        <S title="8. Your Rights Under DPDP Act 2023" icon={Shield} id="your-rights">
          <p>As a Data Principal under the Digital Personal Data Protection Act, 2023, you have the following rights:</p>
          <ul className="space-y-2.5 list-disc list-inside" style={{ color: '#8A9096' }}>
            <li><strong style={{ color: 'white' }}>Right to Access:</strong> Request a copy of all personal data FREE11 holds about you</li>
            <li><strong style={{ color: 'white' }}>Right to Correction:</strong> Request correction of inaccurate or incomplete personal data</li>
            <li><strong style={{ color: 'white' }}>Right to Erasure:</strong> Request deletion of your account and personal data (subject to legal retention obligations)</li>
            <li><strong style={{ color: 'white' }}>Right to Grievance Redressal:</strong> File a complaint about how your data is being processed</li>
            <li><strong style={{ color: 'white' }}>Right to Withdraw Consent:</strong> Withdraw marketing consent at any time (does not affect core platform functionality)</li>
            <li><strong style={{ color: 'white' }}>Right to Nominate:</strong> Nominate a person to exercise your rights in the event of incapacity (as provided under DPDP Act)</li>
          </ul>
          <p className="mt-2">To exercise any of these rights, contact us at <a href="mailto:support@free11.com" style={{ color: '#C6A052' }}>support@free11.com</a>. We will respond within <strong style={{ color: 'white' }}>30 days</strong>.</p>
        </S>

        {/* 9. Cookies */}
        <S title="9. Cookies & Local Storage" icon={Eye} id="cookies">
          <p>FREE11 uses the following browser storage mechanisms:</p>
          <Table
            headers={['Type', 'Purpose', 'Can be disabled?']}
            rows={[
              ['localStorage (auth token)', 'Keep you logged in', 'Yes — clears on browser clear'],
              ['localStorage (language pref)', 'Remember your language', 'Yes'],
              ['localStorage (PWA install)', 'Track install prompt state', 'Yes'],
              ['Session cookies', 'Session management', 'Yes'],
              ['Firebase cookies', 'Authentication state', 'Disabling may break login'],
              ['AdMob cookies / device ID', 'Ad personalisation', 'Managed via device ad settings'],
            ]}
          />
          <p className="text-xs" style={{ color: '#8A9096' }}>FREE11 does not use third-party tracking cookies for advertising profiling beyond Google AdMob's own ad serving.</p>
        </S>

        {/* 10. Children */}
        <S title="10. Children's Policy" icon={Shield} id="children">
          <p><strong style={{ color: 'white' }}>FREE11 is strictly for users aged 18 and above.</strong></p>
          <p>We do not knowingly collect personal data from anyone under 18 years of age. If we become aware that a user is under 18, their account will be suspended immediately and their data deleted within 30 days.</p>
          <p>If you believe a minor has registered on FREE11, please contact us immediately at <a href="mailto:support@free11.com" style={{ color: '#C6A052' }}>support@free11.com</a>.</p>
        </S>

        {/* 11. Security */}
        <S title="11. Data Security" icon={Lock} id="security">
          <p>FREE11 implements the following security measures:</p>
          <ul className="space-y-2 list-disc list-inside" style={{ color: '#8A9096' }}>
            <li><strong style={{ color: 'white' }}>Encrypted transmission:</strong> All data in transit is encrypted via HTTPS/TLS</li>
            <li><strong style={{ color: 'white' }}>Authentication:</strong> JWT tokens, OTP verification, Google OAuth, Firebase Phone Auth</li>
            <li><strong style={{ color: 'white' }}>Fraud engine:</strong> Device fingerprinting and duplicate account detection</li>
            <li><strong style={{ color: 'white' }}>API rate limiting:</strong> Protection against abuse and brute force attacks</li>
            <li><strong style={{ color: 'white' }}>Geo-fencing:</strong> India-only access enforced at API level</li>
            <li><strong style={{ color: 'white' }}>Access controls:</strong> Admin access restricted with separate authentication</li>
            <li><strong style={{ color: 'white' }}>Error monitoring:</strong> Sentry used to detect and resolve security issues proactively</li>
            <li><strong style={{ color: 'white' }}>Payment security:</strong> No card/banking data stored; all payments via PCI-DSS certified providers</li>
          </ul>
          <p className="text-xs mt-2" style={{ color: '#8A9096' }}>In the event of a data breach that is likely to result in risk to your rights, FREE11 will notify affected users and the Data Protection Board of India within the timeframe specified by the DPDP Act.</p>
        </S>

        {/* 12. Changes */}
        <S title="12. Changes to This Policy" icon={Bell} id="changes">
          <p>FREE11 may update this Privacy Policy periodically to reflect changes in our data practices, features, or applicable law. When material changes are made:</p>
          <ul className="space-y-1 list-disc list-inside" style={{ color: '#8A9096' }}>
            <li>We will update the "Last Updated" date at the top of this page</li>
            <li>For significant changes, we will notify you via email or in-app notification</li>
            <li>Continued use of FREE11 after the effective date constitutes acceptance</li>
          </ul>
        </S>

        {/* 13. Contact */}
        <S title="13. Contact & Grievance Officer" icon={Users} id="contact">
          <p>For any privacy-related queries, requests, or complaints:</p>
          <div className="p-4 rounded-xl mt-2" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <p className="text-xs font-bold text-white mb-2">Data Grievance Officer — FREE11</p>
            <p className="text-xs" style={{ color: '#8A9096' }}>Email: <a href="mailto:support@free11.com" style={{ color: '#C6A052' }}>support@free11.com</a></p>
            <p className="text-xs" style={{ color: '#8A9096' }}>Website: <a href="https://free11.com" style={{ color: '#C6A052' }}>https://free11.com</a></p>
            <p className="text-xs mt-2" style={{ color: '#8A9096' }}>Response time: Within 30 days of receiving your request.</p>
            <p className="text-xs mt-2" style={{ color: '#8A9096' }}>You also have the right to lodge a complaint with the <strong style={{ color: 'white' }}>Data Protection Board of India</strong> if you believe your rights under the DPDP Act have been violated.</p>
          </div>
        </S>

        <p className="text-xs text-center mt-4" style={{ color: '#8A9096' }}>© 2026 FREE11. All rights reserved.</p>
      </div>
    </div>
  );
}
