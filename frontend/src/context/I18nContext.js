import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

import en from '../locales/en.json';
import hi from '../locales/hi.json';
import bn from '../locales/bn.json';
import mr from '../locales/mr.json';
import ta from '../locales/ta.json';
import te from '../locales/te.json';
import kn from '../locales/kn.json';
import ml from '../locales/ml.json';

const TRANSLATIONS = { en, hi, bn, mr, ta, te, kn, ml };

export const LANGUAGES = [
  { code: 'en', name: 'English', native: 'English' },
  { code: 'hi', name: 'Hindi', native: 'हिन्दी' },
  { code: 'bn', name: 'Bengali', native: 'বাংলা' },
  { code: 'mr', name: 'Marathi', native: 'मराठी' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు' },
  { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ' },
  { code: 'ml', name: 'Malayalam', native: 'മലയാളം' },
];

const FONT_FAMILIES = {
  en: "'Noto Sans', sans-serif",
  hi: "'Noto Sans Devanagari', 'Noto Sans', sans-serif",
  bn: "'Noto Sans Bengali', 'Noto Sans', sans-serif",
  mr: "'Noto Sans Devanagari', 'Noto Sans', sans-serif",
  ta: "'Noto Sans Tamil', 'Noto Sans', sans-serif",
  te: "'Noto Sans Telugu', 'Noto Sans', sans-serif",
  kn: "'Noto Sans Kannada', 'Noto Sans', sans-serif",
  ml: "'Noto Sans Malayalam', 'Noto Sans', sans-serif",
};

const I18nContext = createContext();

function getNestedValue(obj, path) {
  return path.split('.').reduce((o, k) => (o && o[k] !== undefined ? o[k] : null), obj);
}

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('free11_lang') || 'en');

  useEffect(() => {
    localStorage.setItem('free11_lang', lang);
    document.documentElement.lang = lang;
    document.body.style.fontFamily = FONT_FAMILIES[lang] || FONT_FAMILIES.en;
  }, [lang]);

  const t = useCallback((key, fallback) => {
    const val = getNestedValue(TRANSLATIONS[lang], key);
    if (val !== null) return val;
    const enVal = getNestedValue(TRANSLATIONS.en, key);
    if (enVal !== null) return enVal;
    return fallback || key;
  }, [lang]);

  const changeLang = useCallback((code) => {
    if (TRANSLATIONS[code]) setLang(code);
  }, []);

  return (
    <I18nContext.Provider value={{ lang, t, changeLang, languages: LANGUAGES }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
}
