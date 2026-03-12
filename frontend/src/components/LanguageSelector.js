import React from 'react';
import { useI18n } from '../context/I18nContext';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Globe } from 'lucide-react';

const LanguageSelector = () => {
  const { lang, changeLang, languages } = useI18n();
  const current = languages.find(l => l.code === lang) || languages[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="h-8 w-8 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition-all" data-testid="lang-selector">
          <Globe className="h-4 w-4 text-gray-300" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="bg-slate-900 border-slate-800 min-w-[160px]" align="end">
        {languages.map(l => (
          <DropdownMenuItem
            key={l.code}
            onClick={() => changeLang(l.code)}
            className={`cursor-pointer ${lang === l.code ? 'text-yellow-400 font-bold' : 'text-slate-200'}`}
          >
            <span className="mr-2">{l.native}</span>
            {lang === l.code && <span className="ml-auto text-xs text-yellow-400">&#10003;</span>}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default LanguageSelector;
