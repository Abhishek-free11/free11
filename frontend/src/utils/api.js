import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const api = {
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
};

export default api;