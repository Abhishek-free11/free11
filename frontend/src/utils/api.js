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
  getLeaderboard: () => axios.get(`${API}/leaderboard`),

  // Admin
  getAnalytics: () => axios.get(`${API}/admin/analytics`, { headers: getAuthHeader() }),
};

export default api;