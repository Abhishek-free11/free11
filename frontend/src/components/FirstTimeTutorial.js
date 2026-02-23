import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Target, Coins, Gift, Trophy, ChevronRight, ChevronLeft, X } from 'lucide-react';

const TUTORIAL_SCREENS = [
  {
    id: 1,
    icon: Target,
    iconColor: 'text-red-400',
    iconBg: 'bg-red-500/20',
    title: 'Predict cricket.',
    subtitle: "That's how you earn coins.",
    description: 'Make ball-by-ball predictions during live matches. Your accuracy determines your rewards.',
  },
  {
    id: 2,
    icon: Coins,
    iconColor: 'text-yellow-400',
    iconBg: 'bg-yellow-500/20',
    title: 'Coins unlock real products.',
    subtitle: 'No cash. No betting.',
    description: 'FREE11 Coins are reward tokens you earn through skill. Redeem them for vouchers, recharges, and more.',
  },
  {
    id: 3,
    icon: Gift,
    iconColor: 'text-green-400',
    iconBg: 'bg-green-500/20',
    title: 'Redeem vouchers instantly',
    subtitle: 'for real products.',
    description: 'All rewards are brand-funded. Get Amazon, Swiggy, Netflix vouchers and more delivered to you.',
  },
  {
    id: 4,
    icon: Trophy,
    iconColor: 'text-purple-400',
    iconBg: 'bg-purple-500/20',
    title: 'Skill drives rewards.',
    subtitle: 'Boosters just help you earn faster.',
    description: 'Your prediction accuracy determines your rank. Ads and mini-games are optional ways to earn bonus coins.',
  },
];

const FirstTimeTutorial = ({ onComplete, onSkip }) => {
  const [currentScreen, setCurrentScreen] = useState(0);

  const handleNext = () => {
    if (currentScreen < TUTORIAL_SCREENS.length - 1) {
      setCurrentScreen(currentScreen + 1);
    } else {
      onComplete();
    }
  };

  const handlePrev = () => {
    if (currentScreen > 0) {
      setCurrentScreen(currentScreen - 1);
    }
  };

  const screen = TUTORIAL_SCREENS[currentScreen];
  const Icon = screen.icon;
  const isLastScreen = currentScreen === TUTORIAL_SCREENS.length - 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm" data-testid="first-time-tutorial">
      <div className="relative w-full max-w-md mx-4">
        {/* Skip button */}
        <button
          onClick={onSkip}
          className="absolute -top-12 right-0 text-slate-400 hover:text-white transition-colors flex items-center gap-1 text-sm"
          data-testid="tutorial-skip-btn"
        >
          Skip
          <X className="h-4 w-4" />
        </button>

        {/* Tutorial Card */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl">
          {/* Progress dots */}
          <div className="flex justify-center gap-2 mb-8">
            {TUTORIAL_SCREENS.map((_, index) => (
              <div
                key={index}
                className={`h-2 rounded-full transition-all duration-300 ${
                  index === currentScreen
                    ? 'w-8 bg-yellow-400'
                    : index < currentScreen
                    ? 'w-2 bg-yellow-400/50'
                    : 'w-2 bg-slate-600'
                }`}
              />
            ))}
          </div>

          {/* Icon */}
          <div className={`w-20 h-20 rounded-2xl ${screen.iconBg} flex items-center justify-center mx-auto mb-6`}>
            <Icon className={`h-10 w-10 ${screen.iconColor}`} />
          </div>

          {/* Content */}
          <div className="text-center mb-8">
            <h2 className="text-2xl font-black text-white mb-1">{screen.title}</h2>
            <h3 className="text-xl font-bold text-yellow-400 mb-4">{screen.subtitle}</h3>
            <p className="text-slate-400 text-sm leading-relaxed">{screen.description}</p>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={handlePrev}
              disabled={currentScreen === 0}
              className={`text-slate-400 hover:text-white ${currentScreen === 0 ? 'invisible' : ''}`}
            >
              <ChevronLeft className="h-5 w-5 mr-1" />
              Back
            </Button>

            <span className="text-sm text-slate-500">
              {currentScreen + 1} of {TUTORIAL_SCREENS.length}
            </span>

            <Button
              onClick={handleNext}
              className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
              data-testid="tutorial-next-btn"
            >
              {isLastScreen ? "Let's Go!" : 'Next'}
              {!isLastScreen && <ChevronRight className="h-5 w-5 ml-1" />}
            </Button>
          </div>
        </div>

        {/* Replay hint */}
        <p className="text-center text-slate-500 text-xs mt-4">
          You can replay this tutorial anytime from Profile → Help
        </p>
      </div>
    </div>
  );
};

export default FirstTimeTutorial;
