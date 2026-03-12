import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Flame, Trophy, Clock } from 'lucide-react';

const IPL_SLIDES = [
  {
    id: 1,
    badge: 'T20 2026',
    title: 'Cricket Season is HERE',
    subtitle: 'Predict every over. Earn Free Coins.',
    cta: 'Start Predicting',
    ctaPath: '/predict',
    bg: 'linear-gradient(135deg, #0f1115 0%, #1a0a00 50%, #0f1115 100%)',
    accentColor: '#C6A052',
    icon: Flame,
    sponsor: 'Official Sponsor',
    sponsorBg: 'rgba(198,160,82,0.15)',
  },
  {
    id: 2,
    badge: 'MEGA CONTEST',
    title: 'Win 2000 Coins',
    subtitle: 'Top 10 predictors share the prize pool.',
    cta: 'Join Contest',
    ctaPath: '/match-centre',
    bg: 'linear-gradient(135deg, #0f1115 0%, #001a1a 50%, #0f1115 100%)',
    accentColor: '#4ade80',
    icon: Trophy,
    sponsor: 'Brand Partner',
    sponsorBg: 'rgba(74,222,128,0.1)',
  },
  {
    id: 3,
    badge: 'SPONSORED POOL',
    title: 'Champions Pool',
    subtitle: 'Brand-funded prize pool. Predict & win groceries!',
    cta: 'View Pool',
    ctaPath: '/sponsored',
    bg: 'linear-gradient(135deg, #0f1115 0%, #1a1000 50%, #0f1115 100%)',
    accentColor: '#E0B84F',
    icon: Trophy,
    sponsor: 'Brand Partner',
    sponsorBg: 'rgba(224,184,79,0.1)',
  },
  {
    id: 4,
    badge: 'SMART DEALS',
    title: 'Earn → Redeem Groceries',
    subtitle: 'Cold drinks, biscuits, atta — via ONDC. No cash.',
    cta: 'Browse Shop',
    ctaPath: '/shop',
    bg: 'linear-gradient(135deg, #0f1115 0%, #001a0a 50%, #0f1115 100%)',
    accentColor: '#4ade80',
    icon: Flame,
    sponsor: 'ONDC Network',
    sponsorBg: 'rgba(74,222,128,0.08)',
  },
];

export default function IPLCarousel() {
  const navigate = useNavigate();
  const [active, setActive] = useState(0);
  const timerRef = useRef(null);

  const startTimer = () => {
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setActive(prev => (prev + 1) % IPL_SLIDES.length);
    }, 4000);
  };

  useEffect(() => {
    startTimer();
    return () => clearInterval(timerRef.current);
  }, []);

  const go = (dir) => {
    setActive(prev => (prev + dir + IPL_SLIDES.length) % IPL_SLIDES.length);
    startTimer();
  };

  const slide = IPL_SLIDES[active];
  const Icon = slide.icon;

  return (
    <div
      className="relative rounded-2xl overflow-hidden mb-4"
      style={{ background: slide.bg, border: '1px solid rgba(198,160,82,0.18)', minHeight: '160px', transition: 'background 0.5s ease' }}
      data-testid="ipl-carousel"
    >
      {/* Sponsor badge */}
      <div className="absolute top-3 right-3 z-10">
        <span
          className="text-xs px-2 py-0.5 rounded-full font-medium"
          style={{ background: slide.sponsorBg, color: slide.accentColor, border: `1px solid ${slide.accentColor}40` }}
        >
          {slide.sponsor}
        </span>
      </div>

      <div className="p-4 pr-12">
        {/* Badge */}
        <div className="flex items-center gap-2 mb-2">
          <div
            className="w-6 h-6 rounded-md flex items-center justify-center"
            style={{ background: `${slide.accentColor}20` }}
          >
            <Icon className="w-3 h-3" style={{ color: slide.accentColor }} />
          </div>
          <span
            className="text-xs font-bold tracking-wider"
            style={{ color: slide.accentColor, fontFamily: 'Bebas Neue, sans-serif' }}
          >
            {slide.badge}
          </span>
        </div>

        {/* Title */}
        <h2
          className="text-2xl font-bold text-white mb-1 leading-tight"
          style={{ fontFamily: 'Bebas Neue, sans-serif', letterSpacing: '0.03em' }}
        >
          {slide.title}
        </h2>
        <p className="text-xs mb-4" style={{ color: '#BFC3C8' }}>{slide.subtitle}</p>

        {/* CTA */}
        <button
          onClick={() => navigate(slide.ctaPath)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold transition-all hover:scale-105 active:scale-95"
          style={{ background: slide.accentColor, color: '#0F1115' }}
          data-testid={`ipl-carousel-cta-${slide.id}`}
        >
          {slide.cta}
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Nav arrows */}
      <button
        onClick={() => go(-1)}
        className="absolute left-2 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full flex items-center justify-center"
        style={{ background: 'rgba(0,0,0,0.5)' }}
        data-testid="ipl-carousel-prev"
      >
        <ChevronLeft className="w-3.5 h-3.5 text-white" />
      </button>
      <button
        onClick={() => go(1)}
        className="absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full flex items-center justify-center"
        style={{ background: 'rgba(0,0,0,0.5)' }}
        data-testid="ipl-carousel-next"
      >
        <ChevronRight className="w-3.5 h-3.5 text-white" />
      </button>

      {/* Dots */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
        {IPL_SLIDES.map((_, i) => (
          <button
            key={i}
            onClick={() => { setActive(i); startTimer(); }}
            className="rounded-full transition-all"
            style={{
              width: i === active ? '16px' : '6px',
              height: '6px',
              background: i === active ? slide.accentColor : 'rgba(255,255,255,0.3)',
            }}
          />
        ))}
      </div>

    </div>
  );
}
