import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const api = {
  // Generic methods
  get: (endpoint) => axios.get(`${API}${endpoint}`, { headers: getAuthHeader() }),
  post: (endpoint, data) => axios.post(`${API}${endpoint}`, data, { headers: getAuthHeader() }),
  
  // Auth
  login: (data) => axios.post(`${API}/auth/login`, data),
  register: (data) => axios.post(`${API}/auth/register`, data),
  getMe: () => axios.get(`${API}/auth/me`, { headers: getAuthHeader() }),

  // Coins
  getBalance: () => axios.get(`${API}/coins/balance`, { headers: getAuthHeader() }),
  getTransactions: () => axios.get(`${API}/coins/transactions`, { headers: getAuthHeader() }),
  dailyCheckin: () => axios.post(`${API}/coins/checkin`, {}, { headers: getAuthHeader() }),

  // Games
  playQuiz: (answers) => axios.post(`${API}/games/quiz`, { answers }, { headers: getAuthHeader() }),
  spinWheel: () => axios.post(`${API}/games/spin`, {}, { headers: getAuthHeader() }),
  scratchCard: () => axios.post(`${API}/games/scratch`, {}, { headers: getAuthHeader() }),

  // Tasks
  getTasks: () => axios.get(`${API}/tasks`, { headers: getAuthHeader() }),
  completeTask: (taskId) => axios.post(`${API}/tasks/complete`, { task_id: taskId }, { headers: getAuthHeader() }),

  // Products
  getProducts: (category) => axios.get(`${API}/products${category ? `?category=${category}` : ''}`),
  getProduct: (id) => axios.get(`${API}/products/${id}`),
  createProduct: (data) => axios.post(`${API}/products`, data, { headers: getAuthHeader() }),

  // Redemptions
  createRedemption: (data) => axios.post(`${API}/redemptions`, data, { headers: getAuthHeader() }),
  getRedemptions: () => axios.get(`${API}/redemptions`, { headers: getAuthHeader() }),
  getAllRedemptions: () => axios.get(`${API}/redemptions/all`, { headers: getAuthHeader() }),

  // User
  getUserStats: () => axios.get(`${API}/user/stats`, { headers: getAuthHeader() }),
  getDemandProgress: () => axios.get(`${API}/user/demand-progress`, { headers: getAuthHeader() }),
  getUserBadges: () => axios.get(`${API}/user/badges`, { headers: getAuthHeader() }),
  getLeaderboard: () => axios.get(`${API}/leaderboard`),
  
  // Beta
  getBetaStatus: () => axios.get(`${API}/beta/status`),
  validateInvite: (code) => axios.post(`${API}/beta/validate-invite`, { code }),
  
  // Tutorial
  getTutorialStatus: () => axios.get(`${API}/user/tutorial-status`, { headers: getAuthHeader() }),
  completeTutorial: () => axios.post(`${API}/user/complete-tutorial`, {}, { headers: getAuthHeader() }),
  resetTutorial: () => axios.post(`${API}/user/reset-tutorial`, {}, { headers: getAuthHeader() }),

  // Admin
  getAnalytics: () => axios.get(`${API}/admin/analytics`, { headers: getAuthHeader() }),
  getBrandRoas: () => axios.get(`${API}/admin/brand-roas`, { headers: getAuthHeader() }),

  // FAQ
  getFAQ: () => axios.get(`${API}/faq`),

  // ==================== CLANS APIs ====================
  createClan: (data) => axios.post(`${API}/clans/create`, data, { headers: getAuthHeader() }),
  listClans: (sortBy = 'accuracy') => axios.get(`${API}/clans/list?sort_by=${sortBy}`),
  getMyClan: () => axios.get(`${API}/clans/my`, { headers: getAuthHeader() }),
  getClan: (clanId) => axios.get(`${API}/clans/${clanId}`),
  joinClan: (clanId) => axios.post(`${API}/clans/join`, { clan_id: clanId }, { headers: getAuthHeader() }),
  leaveClan: () => axios.post(`${API}/clans/leave`, {}, { headers: getAuthHeader() }),
  getClanLeaderboard: () => axios.get(`${API}/clans/leaderboard/clans`),
  getClanMemberLeaderboard: (clanId) => axios.get(`${API}/clans/leaderboard/members/${clanId}`),
  getClanChallenges: () => axios.get(`${API}/clans/challenges/available`, { headers: getAuthHeader() }),
  participateInChallenge: (challengeId) => axios.post(`${API}/clans/challenges/participate/${challengeId}`, {}, { headers: getAuthHeader() }),

  // ==================== LEADERBOARDS APIs ====================
  getGlobalLeaderboard: (limit = 50) => axios.get(`${API}/leaderboards/global?limit=${limit}`),
  getWeeklyLeaderboard: (limit = 50) => axios.get(`${API}/leaderboards/weekly?limit=${limit}`),
  getStreakLeaderboard: (limit = 50) => axios.get(`${API}/leaderboards/streak?limit=${limit}`),
  getPublicProfile: (userId) => axios.get(`${API}/leaderboards/profile/${userId}`),
  getActivityFeed: () => axios.get(`${API}/leaderboards/activity-feed`, { headers: getAuthHeader() }),
  
  // Duels
  getMyDuels: () => axios.get(`${API}/leaderboards/duels/my`, { headers: getAuthHeader() }),
  createDuel: (challengedId, matchId = null) => axios.post(`${API}/leaderboards/duels/challenge`, { challenged_id: challengedId, match_id: matchId }, { headers: getAuthHeader() }),
  acceptDuel: (duelId) => axios.post(`${API}/leaderboards/duels/${duelId}/accept`, {}, { headers: getAuthHeader() }),
  declineDuel: (duelId) => axios.post(`${API}/leaderboards/duels/${duelId}/decline`, {}, { headers: getAuthHeader() }),

  // ==================== CRICKET APIs ====================
  // Matches
  getMatches: (status) => axios.get(`${API}/cricket/matches${status ? `?status=${status}` : ''}`),
  getLiveMatches: () => axios.get(`${API}/cricket/matches/live`),
  getMatch: (matchId) => axios.get(`${API}/cricket/matches/${matchId}`),
  
  // Predictions
  predictBall: (data) => axios.post(`${API}/cricket/predict/ball`, data, { headers: getAuthHeader() }),
  predictMatch: (data) => axios.post(`${API}/cricket/predict/match`, data, { headers: getAuthHeader() }),
  getMyPredictions: (matchId) => axios.get(`${API}/cricket/predictions/my${matchId ? `?match_id=${matchId}` : ''}`, { headers: getAuthHeader() }),
  getCricketLeaderboard: () => axios.get(`${API}/cricket/leaderboard`),

  // ==================== ADS APIs ====================
  getAdConfig: () => axios.get(`${API}/ads/config`),
  getAdStatus: () => axios.get(`${API}/ads/status`, { headers: getAuthHeader() }),
  claimAdReward: (data) => axios.post(`${API}/ads/reward`, data, { headers: getAuthHeader() }),
  getAdHistory: () => axios.get(`${API}/ads/history`, { headers: getAuthHeader() }),

  // ==================== SUPPORT APIs ====================
  // Chatbot
  sendChatMessage: (message) => axios.post(`${API}/support/chat`, { message }, { headers: getAuthHeader() }),
  getChatSuggestions: () => axios.get(`${API}/support/chat/suggestions`),
  
  // Tickets
  createTicket: (data) => axios.post(`${API}/support/tickets`, data, { headers: getAuthHeader() }),
  getMyTickets: (status) => axios.get(`${API}/support/tickets${status ? `?status=${status}` : ''}`, { headers: getAuthHeader() }),
  getTicket: (ticketId) => axios.get(`${API}/support/tickets/${ticketId}`, { headers: getAuthHeader() }),
  replyToTicket: (ticketId, message) => axios.post(`${API}/support/tickets/${ticketId}/reply?message=${encodeURIComponent(message)}`, {}, { headers: getAuthHeader() }),

  // ==================== FULFILLMENT APIs ====================
  getFulfillmentStatus: (orderId) => axios.get(`${API}/fulfillment/status/${orderId}`, { headers: getAuthHeader() }),
  getMyVouchers: (status) => axios.get(`${API}/fulfillment/my-vouchers${status ? `?status=${status}` : ''}`, { headers: getAuthHeader() }),
  retryFulfillment: (fulfillmentId) => axios.post(`${API}/fulfillment/retry/${fulfillmentId}`, {}, { headers: getAuthHeader() }),

  // ==================== GIFT CARD APIs ====================
  getAvailableGiftCards: (brand) => axios.get(`${API}/gift-cards/available${brand ? `?brand=${brand}` : ''}`, { headers: getAuthHeader() }),
  redeemGiftCard: (brand, value) => axios.post(`${API}/gift-cards/redeem?brand=${brand}&value=${value}`, {}, { headers: getAuthHeader() }),
  getMyGiftCardRedemptions: () => axios.get(`${API}/gift-cards/my-redemptions`, { headers: getAuthHeader() }),
  
  // Admin Gift Cards
  uploadSingleGiftCard: (data) => axios.post(`${API}/gift-cards/admin/upload-single`, data, { headers: getAuthHeader() }),
  uploadBulkGiftCards: (formData) => axios.post(`${API}/gift-cards/admin/upload-bulk`, formData, { 
    headers: { ...getAuthHeader(), 'Content-Type': 'multipart/form-data' }
  }),
  getGiftCardInventory: (brand, status) => {
    let url = `${API}/gift-cards/admin/inventory`;
    const params = [];
    if (brand) params.push(`brand=${brand}`);
    if (status) params.push(`status=${status}`);
    if (params.length) url += `?${params.join('&')}`;
    return axios.get(url, { headers: getAuthHeader() });
  },

  // ==================== V2 ENGINE APIs ====================
  // Contests V2
  v2CreateContest: (data) => axios.post(`${API}/v2/contests/create`, data, { headers: getAuthHeader() }),
  v2JoinContest: (data) => axios.post(`${API}/v2/contests/join`, data, { headers: getAuthHeader() }),
  v2JoinByCode: (data) => axios.post(`${API}/v2/contests/join-code`, data, { headers: getAuthHeader() }),
  v2GetMatchContests: (matchId, type) => axios.get(`${API}/v2/contests/match/${matchId}${type ? `?contest_type=${type}` : ''}`),
  v2GetContest: (id) => axios.get(`${API}/v2/contests/${id}`),
  v2GetContestLeaderboard: (id) => axios.get(`${API}/v2/contests/${id}/leaderboard`, { headers: getAuthHeader() }),
  v2GetMyContests: () => axios.get(`${API}/v2/contests/user/my`, { headers: getAuthHeader() }),
  v2SeedContests: (matchId) => axios.post(`${API}/v2/contests/seed/${matchId}`, {}, { headers: getAuthHeader() }),
  v2FinalizeContest: (contestId) => axios.post(`${API}/v2/contests/${contestId}/finalize`, {}, { headers: getAuthHeader() }),

  // Predictions V2
  v2SubmitPrediction: (data) => axios.post(`${API}/v2/predictions/submit`, data, { headers: getAuthHeader() }),
  v2GetMyPredictions: (matchId) => axios.get(`${API}/v2/predictions/my${matchId ? `?match_id=${matchId}` : ''}`, { headers: getAuthHeader() }),
  v2GetPredictionStats: () => axios.get(`${API}/v2/predictions/stats`, { headers: getAuthHeader() }),
  v2GetPredictionTypes: () => axios.get(`${API}/v2/predictions/types`),

  // Cards V2
  v2GetCardInventory: () => axios.get(`${API}/v2/cards/inventory`, { headers: getAuthHeader() }),
  v2GetCardTypes: () => axios.get(`${API}/v2/cards/types`),
  v2ActivateCard: (data) => axios.post(`${API}/v2/cards/activate`, data, { headers: getAuthHeader() }),

  // Ledger V2
  v2GetLedgerBalance: () => axios.get(`${API}/v2/ledger/balance`, { headers: getAuthHeader() }),
  v2GetLedgerHistory: (limit, offset) => axios.get(`${API}/v2/ledger/history?limit=${limit || 50}&offset=${offset || 0}`, { headers: getAuthHeader() }),
  v2ReconcileLedger: () => axios.post(`${API}/v2/ledger/reconcile`, {}, { headers: getAuthHeader() }),

  // Redemption V2
  v2Redeem: (data) => axios.post(`${API}/v2/redeem`, data, { headers: getAuthHeader() }),
  v2GetVoucherStatus: (id) => axios.get(`${API}/v2/redeem/status/${id}`, { headers: getAuthHeader() }),
  v2GetMyVouchers: () => axios.get(`${API}/v2/redeem/my`, { headers: getAuthHeader() }),

  // Ads V2
  v2GetAdStatus: () => axios.get(`${API}/v2/ads/status`, { headers: getAuthHeader() }),
  v2StartAd: () => axios.post(`${API}/v2/ads/start`, {}, { headers: getAuthHeader() }),
  v2CompleteAd: (adId) => axios.post(`${API}/v2/ads/complete`, { ad_id: adId }, { headers: getAuthHeader() }),

  // Referral V2
  v2GetReferralCode: () => axios.get(`${API}/v2/referral/code`, { headers: getAuthHeader() }),
  v2GetReferralStats: () => axios.get(`${API}/v2/referral/stats`, { headers: getAuthHeader() }),
  v2BindReferral: (data) => axios.post(`${API}/v2/referral/bind`, data, { headers: getAuthHeader() }),

  // Match State V2
  v2GetMatchState: (matchId) => axios.get(`${API}/v2/match/${matchId}/state`),
  v2GetLiveMatches: () => axios.get(`${API}/v2/matches/live`),
  v2GetAllMatches: (status, limit) => axios.get(`${API}/v2/matches/all?${status ? `status=${status}&` : ''}limit=${limit || 20}`),

  // Admin V2
  v2AdminKillMatch: (data) => axios.post(`${API}/admin/v2/match/kill`, data, { headers: getAuthHeader() }),
  v2AdminFreezeMatch: (data) => axios.post(`${API}/admin/v2/match/freeze`, data, { headers: getAuthHeader() }),
  v2AdminCreateTestMatch: () => axios.post(`${API}/admin/v2/match/test/create`, {}, { headers: getAuthHeader() }),
  v2AdminAdvanceTestMatch: (data) => axios.post(`${API}/admin/v2/match/test/advance`, data, { headers: getAuthHeader() }),
  v2AdminVoidContest: (data) => axios.post(`${API}/admin/v2/contest/void`, data, { headers: getAuthHeader() }),
  v2AdminVoidPredictions: (data) => axios.post(`${API}/admin/v2/predictions/void`, data, { headers: getAuthHeader() }),
  v2AdminResolveOver: (data) => axios.post(`${API}/admin/v2/predictions/resolve-over`, data, { headers: getAuthHeader() }),
  v2AdminFreezeWallet: (data) => axios.post(`${API}/admin/v2/wallet/freeze`, data, { headers: getAuthHeader() }),
  v2AdminAdjustCoins: (data) => axios.post(`${API}/admin/v2/wallet/adjust`, data, { headers: getAuthHeader() }),
  v2AdminSetFeatureFlag: (data) => axios.post(`${API}/admin/v2/feature-flag`, data, { headers: getAuthHeader() }),
  v2AdminGetFeatureFlags: () => axios.get(`${API}/admin/v2/feature-flags`, { headers: getAuthHeader() }),
  v2AdminToggleTestMode: () => axios.post(`${API}/admin/v2/toggle-test-mode`, {}, { headers: getAuthHeader() }),
  v2AdminReconcileAll: () => axios.post(`${API}/admin/v2/ledger/reconcile-all`, {}, { headers: getAuthHeader() }),
  v2AdminGetActionLog: (limit) => axios.get(`${API}/admin/v2/action-log?limit=${limit || 50}`, { headers: getAuthHeader() }),
  v2AdminForceCompleteVoucher: (data) => axios.post(`${API}/admin/v2/voucher/force-complete`, data, { headers: getAuthHeader() }),
  v2AdminForceFailVoucher: (data) => axios.post(`${API}/admin/v2/voucher/force-fail`, data, { headers: getAuthHeader() }),

  // EntitySport Real Data
  v2EsGetMatches: (status, perPage) => axios.get(`${API}/v2/es/matches?status=${status || 3}&per_page=${perPage || 20}`),
  v2EsGetMatchInfo: (matchId) => axios.get(`${API}/v2/es/match/${matchId}/info`),
  v2EsGetMatchLive: (matchId) => axios.get(`${API}/v2/es/match/${matchId}/live`),
  v2EsGetScorecard: (matchId) => axios.get(`${API}/v2/es/match/${matchId}/scorecard`),
  v2EsGetSquads: (matchId) => axios.get(`${API}/v2/es/match/${matchId}/squads`),
  v2EsSync: () => axios.post(`${API}/v2/es/sync`, {}, { headers: getAuthHeader() }),
  v2EsGetCompetitions: () => axios.get(`${API}/v2/es/competitions`),

  // Fantasy V2
  v2CreateFantasyTeam: (data) => axios.post(`${API}/v2/fantasy/create-team`, data, { headers: getAuthHeader() }),
  v2GetMyFantasyTeams: (matchId) => axios.get(`${API}/v2/fantasy/my-teams${matchId ? `?match_id=${matchId}` : ''}`, { headers: getAuthHeader() }),
  v2GetFantasyTeam: (teamId) => axios.get(`${API}/v2/fantasy/team/${teamId}`),
  v2GetFantasyRankings: (matchId) => axios.get(`${API}/v2/fantasy/rankings/${matchId}`),
  v2CompareTeams: (data) => axios.post(`${API}/v2/fantasy/compare`, data, { headers: getAuthHeader() }),
  v2GetPointsSystem: () => axios.get(`${API}/v2/fantasy/points-system`),

  // FREE Bucks
  v2GetFreeBucksBalance: () => axios.get(`${API}/v2/freebucks/balance`, { headers: getAuthHeader() }),
  v2GetFreeBucksHistory: (limit) => axios.get(`${API}/v2/freebucks/history?limit=${limit || 50}`, { headers: getAuthHeader() }),
  v2GetFreeBucksPackages: () => axios.get(`${API}/v2/freebucks/packages`),

  // Payments
  v2GetWalletHistory: () => axios.get(`${API}/v2/payments/history`, { headers: getAuthHeader() }),
  v2ClaimAdMobReward: (data) => axios.post(`${API}/v2/ads/reward`, data, { headers: getAuthHeader() }),
  v2GetPaymentPackages: () => axios.get(`${API}/payments/packages`),
  v2CreateCheckout: (data) => axios.post(`${API}/payments/checkout`, data, { headers: getAuthHeader() }),
  v2GetPaymentStatus: (sessionId) => axios.get(`${API}/payments/status/${sessionId}`),

  // Feature Gating
  v2GetGatedFeatures: () => axios.get(`${API}/v2/features/gated`),
  v2CheckFeature: (feature) => axios.get(`${API}/v2/features/check/${feature}`, { headers: getAuthHeader() }),
  v2UseFeature: (data) => axios.post(`${API}/v2/features/use`, data, { headers: getAuthHeader() }),

  // Notifications
  v2GetNotifications: (limit, unreadOnly) => axios.get(`${API}/v2/notifications?limit=${limit || 50}&unread_only=${unreadOnly || false}`, { headers: getAuthHeader() }),
  v2MarkNotifRead: (id) => axios.post(`${API}/v2/notifications/${id}/read`, {}, { headers: getAuthHeader() }),
  v2MarkAllNotifsRead: () => axios.post(`${API}/v2/notifications/read-all`, {}, { headers: getAuthHeader() }),

  // Analytics (admin)
  v2GetAnalyticsDashboard: () => axios.get(`${API}/v2/analytics/dashboard`, { headers: getAuthHeader() }),
  v2GetCacheStats: () => axios.get(`${API}/v2/cache/stats`, { headers: getAuthHeader() }),

  // Health
  v2Health: () => axios.get(`${API}/health`),

  // OTP Email Verification
  sendOtp: (email) => axios.post(`${API}/auth/send-otp`, { email }),
  verifyOtp: (email, otp) => axios.post(`${API}/auth/verify-otp`, { email, otp }),
  getEmailStatus: () => axios.get(`${API}/auth/email-status`, { headers: getAuthHeader() }),
  resendVerification: () => axios.post(`${API}/auth/resend-verification`, {}, { headers: getAuthHeader() }),

  // FCM Push Notifications
  registerPushToken: (token, deviceType) => axios.post(`${API}/push/register`, { token, device_type: deviceType }, { headers: getAuthHeader() }),
  v2RegisterPushToken: (deviceToken, deviceType) => axios.post(`${API}/v2/push/register`, { device_token: deviceToken, device_type: deviceType }, { headers: getAuthHeader() }),
  unregisterPushToken: (token, deviceType) => axios.post(`${API}/push/unregister`, { token, device_type: deviceType }, { headers: getAuthHeader() }),
  getPushPreferences: () => axios.get(`${API}/push/preferences`, { headers: getAuthHeader() }),
  updatePushPreferences: (prefs) => axios.post(`${API}/push/preferences`, prefs, { headers: getAuthHeader() }),

  // Fraud (admin)
  v2GetFlaggedUsers: () => axios.get(`${API}/admin/v2/fraud/flagged`, { headers: getAuthHeader() }),
  v2FlagUser: (data) => axios.post(`${API}/admin/v2/fraud/flag`, data, { headers: getAuthHeader() }),
  v2BanUser: (data) => axios.post(`${API}/admin/v2/fraud/ban`, data, { headers: getAuthHeader() }),
  v2UnbanUser: (data) => axios.post(`${API}/admin/v2/fraud/unban`, data, { headers: getAuthHeader() }),

  // Engagement: Progression
  getProgression: () => axios.get(`${API}/v2/engage/progression`, { headers: getAuthHeader() }),
  getTiers: () => axios.get(`${API}/v2/engage/tiers`),

  // Engagement: Missions
  getDailyMissions: () => axios.get(`${API}/v2/engage/missions`, { headers: getAuthHeader() }),
  claimMission: (missionId) => axios.post(`${API}/v2/engage/missions/claim`, { mission_id: missionId }, { headers: getAuthHeader() }),

  // Engagement: Streak
  getStreak: () => axios.get(`${API}/v2/engage/streak`, { headers: getAuthHeader() }),
  streakCheckin: () => axios.post(`${API}/v2/engage/streak/checkin`, {}, { headers: getAuthHeader() }),

  // Engagement: Spin Wheel
  getSpinStatus: () => axios.get(`${API}/v2/engage/spin/status`, { headers: getAuthHeader() }),
  doSpin: () => axios.post(`${API}/v2/engage/spin`, {}, { headers: getAuthHeader() }),
  getSpinHistory: () => axios.get(`${API}/v2/engage/spin/history`, { headers: getAuthHeader() }),

  // Engagement: Leaderboards
  getEngageLeaderboard: (period) => axios.get(`${API}/v2/engage/leaderboard/${period}`),

  // Engagement: Economy
  getEconomyStatus: () => axios.get(`${API}/v2/engage/economy/status`, { headers: getAuthHeader() }),
  getEconomyStats: () => axios.get(`${API}/v2/engage/economy/stats`, { headers: getAuthHeader() }),

  // Engagement: Store Tiers
  getStoreTiers: () => axios.get(`${API}/v2/engage/store/tiers`, { headers: getAuthHeader() }),

  // Engagement: Surprise Rewards
  checkSurprise: (trigger) => axios.post(`${API}/v2/engage/surprise/${trigger}`, {}, { headers: getAuthHeader() }),

  // Vouchers (Xoxoday)
  getVoucherCatalog: (category) => axios.get(`${API}/v2/vouchers/catalog${category ? `?category=${category}` : ''}`),
  getVoucherStatus: () => axios.get(`${API}/v2/vouchers/status`),
  redeemVoucher: (data) => axios.post(`${API}/v2/vouchers/redeem`, data, { headers: getAuthHeader() }),

  // Feature 1: Wish List Progress Tracker
  v2GetWishlist: () => axios.get(`${API}/v2/wishlist`, { headers: getAuthHeader() }),
  v2PinWishlist: (product_id) => axios.post(`${API}/v2/wishlist/pin`, { product_id }, { headers: getAuthHeader() }),
  v2UnpinWishlist: () => axios.delete(`${API}/v2/wishlist/unpin`, { headers: getAuthHeader() }),

  // Feature 2: Hot Hand Streak
  v2GetPredictionStreak: () => axios.get(`${API}/v2/predictions/streak`, { headers: getAuthHeader() }),

  // Feature 3: Live Crowd Meter
  v2GetCrowdMeter: (matchId) => axios.get(`${API}/v2/crowd-meter/${matchId}`),

  // Feature 4: Daily Cricket Puzzle
  v2GetTodayPuzzle: () => axios.get(`${API}/v2/puzzle/today`, { headers: getAuthHeader() }),
  v2AnswerPuzzle: (answer) => axios.post(`${API}/v2/puzzle/answer`, { answer }, { headers: getAuthHeader() }),

  // Feature 5: Weekly Report Card
  v2GetWeeklyReport: () => axios.get(`${API}/v2/report-card/weekly`, { headers: getAuthHeader() }),
  v2DismissWeeklyReport: () => axios.post(`${API}/v2/report-card/dismiss`, {}, { headers: getAuthHeader() }),

  // Quest Engine
  v2QuestStatus: () => axios.get(`${API}/v2/quest/status`, { headers: getAuthHeader() }),
  v2QuestOffer: () => axios.post(`${API}/v2/quest/offer`, {}, { headers: getAuthHeader() }),
  v2QuestClaimAd: (quest_id) => axios.post(`${API}/v2/quest/claim-ad`, { quest_id }, { headers: getAuthHeader() }),
  v2QuestRationViewed: (quest_id) => axios.post(`${API}/v2/quest/ration-viewed`, { quest_id }, { headers: getAuthHeader() }),
  v2QuestDismiss: (quest_id) => axios.post(`${API}/v2/quest/dismiss`, { quest_id }, { headers: getAuthHeader() }),
  v2QuestHistory: () => axios.get(`${API}/v2/quest/history`, { headers: getAuthHeader() }),

  // Router (Ration Rails Aggregator)
  v2RouterTease: (sku, geo_state) => axios.get(`${API}/v2/router/tease?sku=${sku || 'cola_2l'}&geo_state=${geo_state || 'MH'}`),
  v2RouterSettle: (data) => axios.post(`${API}/v2/router/settle`, data, { headers: getAuthHeader() }),
  v2RouterSkus: () => axios.get(`${API}/v2/router/skus`),

  // Sponsored Pools
  v2GetSponsoredPools: (status) => axios.get(`${API}/v2/sponsored${status ? `?status=${status}` : ''}`, { headers: getAuthHeader() }),
  v2GetSponsoredPool: (id) => axios.get(`${API}/v2/sponsored/${id}`, { headers: getAuthHeader() }),
  v2JoinSponsoredPool: (pool_id) => axios.post(`${API}/v2/sponsored/join`, { pool_id }, { headers: getAuthHeader() }),
  v2SponsoredPoolLeaderboard: (id) => axios.get(`${API}/v2/sponsored/${id}/leaderboard`, { headers: getAuthHeader() }),
  v2CreateSponsoredPool: (data) => axios.post(`${API}/v2/sponsored/create`, data, { headers: getAuthHeader() }),
  v2FinalizeSponsoredPool: (id) => axios.post(`${API}/v2/sponsored/${id}/finalize`, {}, { headers: getAuthHeader() }),

  // KPIs (admin)
  v2GetKPIs: () => axios.get(`${API}/v2/kpis`, { headers: getAuthHeader() }),
  v2GetCohortCsv: () => axios.get(`${API}/v2/kpis/cohort-csv`, { headers: getAuthHeader() }),
  v2GetRouterKPIs: () => axios.get(`${API}/v2/kpis/router`, { headers: getAuthHeader() }),
};

export default api;