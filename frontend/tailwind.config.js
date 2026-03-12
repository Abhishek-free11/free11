/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
  	extend: {
      fontFamily: {
        heading: ['"Bebas Neue"', 'sans-serif'],
        numbers: ['Oswald', 'sans-serif'],
        body: ['"Noto Sans"', 'sans-serif'],
      },
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
        // FREE11 Brand Tokens
        gold: {
          DEFAULT: '#C6A052',
          light: '#E0B84F',
          dark: '#A8863A',
          glow: 'rgba(198, 160, 82, 0.2)',
        },
        charcoal: {
          DEFAULT: '#1B1E23',
          deep: '#0F1115',
          paper: '#15181C',
        },
        silver: {
          DEFAULT: '#BFC3C8',
          muted: '#8A9096',
        },
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			}
  		},
  		keyframes: {
  			'accordion-down': {
  				from: { height: '0' },
  				to: { height: 'var(--radix-accordion-content-height)' }
  			},
  			'accordion-up': {
  				from: { height: 'var(--radix-accordion-content-height)' },
  				to: { height: '0' }
  			},
        'coin-glow': {
          '0%, 100%': { filter: 'brightness(1) drop-shadow(0 0 4px rgba(198,160,82,0.3))' },
          '50%': { filter: 'brightness(1.3) drop-shadow(0 0 10px rgba(224,184,79,0.7))' },
        },
        'score-flash': {
          '0%': { color: '#E0B84F', transform: 'scale(1.15)' },
          '100%': { color: 'inherit', transform: 'scale(1)' },
        },
        'live-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
        'slide-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'gold-shimmer': {
          '0%': { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out',
        'coin-glow': 'coin-glow 2.5s ease-in-out infinite',
        'score-flash': 'score-flash 0.5s ease-out',
        'live-pulse': 'live-pulse 1.5s ease-in-out infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'gold-shimmer': 'gold-shimmer 2.5s linear infinite',
  		},
      boxShadow: {
        'gold': '0 0 20px rgba(198, 160, 82, 0.2)',
        'gold-lg': '0 0 40px rgba(198, 160, 82, 0.35)',
        'gold-btn': '0 4px 24px rgba(198, 160, 82, 0.35)',
        'broadcast': '0 10px 40px rgba(0, 0, 0, 0.6)',
      },
  	}
  },
  plugins: [require("tailwindcss-animate")],
};
