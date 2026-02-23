import React from 'react';
import { Button } from '@/components/ui/button';
import { Target, Gift, History, Coins, TrendingUp } from 'lucide-react';

const EMPTY_STATES = {
  dashboard: {
    icon: Target,
    iconColor: 'text-yellow-400',
    iconBg: 'bg-yellow-500/10',
    title: 'Welcome to FREE11!',
    description: 'Make your first prediction to start unlocking real products.',
    actionText: 'Start Predicting',
    actionPath: '/cricket',
  },
  predictions: {
    icon: Target,
    iconColor: 'text-blue-400',
    iconBg: 'bg-blue-500/10',
    title: 'No predictions yet',
    description: 'Start predicting to build your streak and climb the leaderboard!',
    actionText: 'Make Prediction',
    actionPath: '/cricket',
  },
  vouchers: {
    icon: Gift,
    iconColor: 'text-green-400',
    iconBg: 'bg-green-500/10',
    title: 'No vouchers yet',
    description: 'Redeemed vouchers will appear here once you unlock your first reward.',
    actionText: 'Browse Shop',
    actionPath: '/shop',
  },
  transactions: {
    icon: Coins,
    iconColor: 'text-yellow-400',
    iconBg: 'bg-yellow-500/10',
    title: 'No transactions yet',
    description: 'Your coin history will show up once you start earning.',
    actionText: 'Start Earning',
    actionPath: '/cricket',
  },
  redemptions: {
    icon: Gift,
    iconColor: 'text-purple-400',
    iconBg: 'bg-purple-500/10',
    title: 'No redemptions yet',
    description: 'Your redeemed products will appear here. Start earning coins to unlock rewards!',
    actionText: 'Browse Shop',
    actionPath: '/shop',
  },
  activity: {
    icon: TrendingUp,
    iconColor: 'text-green-400',
    iconBg: 'bg-green-500/10',
    title: 'No activity yet',
    description: 'Your recent activity will show up here once you start playing.',
    actionText: 'Get Started',
    actionPath: '/cricket',
  },
  leaderboard: {
    icon: Target,
    iconColor: 'text-yellow-400',
    iconBg: 'bg-yellow-500/10',
    title: 'Leaderboard loading...',
    description: 'Start predicting to join the leaderboard and compete with others!',
    actionText: 'Start Predicting',
    actionPath: '/cricket',
  },
};

const EmptyState = ({ type, onAction, customTitle, customDescription, customActionText, className = '' }) => {
  const config = EMPTY_STATES[type] || EMPTY_STATES.dashboard;
  const Icon = config.icon;

  const title = customTitle || config.title;
  const description = customDescription || config.description;
  const actionText = customActionText || config.actionText;

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 ${className}`} data-testid={`empty-state-${type}`}>
      {/* Icon */}
      <div className={`w-16 h-16 rounded-2xl ${config.iconBg} flex items-center justify-center mb-4`}>
        <Icon className={`h-8 w-8 ${config.iconColor}`} />
      </div>

      {/* Content */}
      <h3 className="text-lg font-bold text-white mb-2 text-center">{title}</h3>
      <p className="text-sm text-slate-400 text-center max-w-xs mb-6">{description}</p>

      {/* Action */}
      {onAction && (
        <Button
          onClick={onAction}
          className="bg-gradient-to-r from-yellow-500 to-amber-600 hover:from-yellow-600 hover:to-amber-700 text-black font-bold"
          data-testid={`empty-state-${type}-action`}
        >
          {actionText}
        </Button>
      )}
    </div>
  );
};

export default EmptyState;
