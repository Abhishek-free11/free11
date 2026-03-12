import { useNavigate, useLocation } from 'react-router-dom';
import { useI18n } from '../context/I18nContext';

const FOOTER_LINKS = [
  { key: 'about', path: '/about' },
  { key: 'terms', path: '/terms' },
  { key: 'privacy', path: '/privacy' },
  { key: 'refund', path: '/refund' },
  { key: 'responsible_play', path: '/responsible-play' },
  { key: 'guidelines', path: '/guidelines' },
  { key: 'disclaimer', path: '/disclaimer' },
  { key: 'wallet_info', path: '/wallet-info' },
  { key: 'faq', path: '/faq' },
  { key: 'support', path: '/support' },
];

const HIDDEN_ON = ['/login', '/register', '/'];

export default function SiteFooter() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useI18n();

  if (HIDDEN_ON.includes(location.pathname)) return null;

  return (
    <footer className="bg-[#060910] border-t border-white/5 px-4 py-6 mt-4 mb-20 md:mb-0" data-testid="site-footer">
      <div className="max-w-2xl mx-auto">
        {/* Links */}
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 justify-center mb-4">
          {FOOTER_LINKS.map(l => (
            <button key={l.path} onClick={() => navigate(l.path)} className="text-[11px] text-gray-500 hover:text-gray-300 transition-colors">
              {t(`footer_links.${l.key}`)}
            </button>
          ))}
        </div>

        {/* Disclaimer */}
        <p className="text-[10px] text-gray-600 text-center leading-relaxed" data-testid="footer-disclaimer">
          {t('footer.disclaimer')}
        </p>

        <p className="text-[10px] text-gray-700 text-center mt-2">
          &copy; {new Date().getFullYear()} FREE11. {t('footer.rights')}
        </p>
      </div>
    </footer>
  );
}
