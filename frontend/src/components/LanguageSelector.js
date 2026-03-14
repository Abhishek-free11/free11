import React from 'react';
import { useI18n } from '../context/I18nContext';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Globe, ChevronDown, Check } from 'lucide-react';

const LanguageSelector = ({ variant = 'compact' }) => {
  const { lang, changeLang, languages } = useI18n();
  const current = languages.find(l => l.code === lang) || languages[0];

  // Compact variant - used in navbar or small spaces
  if (variant === 'compact') {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button 
            className="h-9 px-3 flex items-center gap-2 rounded-lg transition-all"
            style={{ 
              background: 'rgba(198,160,82,0.1)', 
              border: '1px solid rgba(198,160,82,0.2)'
            }}
            data-testid="lang-selector"
          >
            <Globe className="h-4 w-4" style={{ color: '#C6A052' }} />
            <span className="text-sm font-medium text-white">{current.native}</span>
            <ChevronDown className="h-3 w-3" style={{ color: '#8A9096' }} />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent 
          className="min-w-[180px]" 
          align="end"
          style={{ 
            background: '#1B1E23', 
            border: '1px solid rgba(255,255,255,0.08)',
            boxShadow: '0 10px 40px rgba(0,0,0,0.5)'
          }}
        >
          {languages.map(l => (
            <DropdownMenuItem
              key={l.code}
              onClick={() => changeLang(l.code)}
              className="cursor-pointer flex items-center justify-between py-2.5 px-3 rounded-md transition-colors"
              style={{ 
                color: lang === l.code ? '#C6A052' : '#BFC3C8',
                background: lang === l.code ? 'rgba(198,160,82,0.1)' : 'transparent'
              }}
            >
              <div className="flex items-center gap-3">
                <span className="text-base">{l.native}</span>
                <span className="text-xs" style={{ color: '#8A9096' }}>{l.name}</span>
              </div>
              {lang === l.code && <Check className="h-4 w-4" style={{ color: '#C6A052' }} />}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  // Full variant - used in profile settings
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button 
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all hover:opacity-80"
          style={{ 
            background: 'rgba(198,160,82,0.12)', 
            border: '1px solid rgba(198,160,82,0.2)'
          }}
          data-testid="lang-selector-full"
        >
          <Globe className="h-4 w-4" style={{ color: '#C6A052' }} />
          <span className="font-medium" style={{ color: '#C6A052' }}>{current.native}</span>
          <ChevronDown className="h-4 w-4" style={{ color: '#C6A052' }} />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent 
        className="min-w-[220px]" 
        align="end"
        style={{ 
          background: '#1B1E23', 
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 10px 40px rgba(0,0,0,0.5)'
        }}
      >
        <div className="px-3 py-2 border-b" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
          <p className="text-xs font-medium" style={{ color: '#8A9096' }}>Select Language</p>
        </div>
        <div className="py-1">
          {languages.map(l => (
            <DropdownMenuItem
              key={l.code}
              onClick={() => changeLang(l.code)}
              className="cursor-pointer flex items-center justify-between py-3 px-3 mx-1 rounded-lg transition-colors"
              style={{ 
                color: lang === l.code ? '#C6A052' : '#BFC3C8',
                background: lang === l.code ? 'rgba(198,160,82,0.1)' : 'transparent'
              }}
            >
              <div className="flex flex-col">
                <span className="font-medium">{l.native}</span>
                <span className="text-xs" style={{ color: '#8A9096' }}>{l.name}</span>
              </div>
              {lang === l.code && (
                <div className="flex items-center justify-center w-5 h-5 rounded-full" style={{ background: 'rgba(198,160,82,0.2)' }}>
                  <Check className="h-3 w-3" style={{ color: '#C6A052' }} />
                </div>
              )}
            </DropdownMenuItem>
          ))}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default LanguageSelector;
