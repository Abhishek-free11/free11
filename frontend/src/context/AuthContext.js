import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Silently request notification permission and register FCM token.
 * Called after successful login/register.
 */
async function registerWebPushToken(authToken) {
  try {
    const { requestAndGetToken } = await import('../firebase');
    const fcmToken = await requestAndGetToken();
    if (!fcmToken) return;

    await axios.post(
      `${process.env.REACT_APP_BACKEND_URL}/api/v2/push/register`,
      { device_token: fcmToken, device_type: 'web' },
      { headers: { Authorization: `Bearer ${authToken}` } }
    );
    console.info('[FCM] Web push token registered');
  } catch (e) {
    // Non-blocking — push is optional
    console.info('[FCM] Web push registration skipped:', e.message);
  }
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const loginWithToken = async (token) => {
    setLoading(true); // hold PrivateRoute at spinner while fetchUser resolves
    localStorage.setItem('token', token);
    setToken(token);
    // fetchUser is triggered by the token useEffect
  };

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { 
      email: email.trim().toLowerCase(), 
      password: password 
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setUser(userData);
    // Register web push token silently (non-blocking)
    registerWebPushToken(access_token);
    return userData;
  };

  const register = async (email, name, password, dateOfBirth, inviteCode = null) => {
    const payload = { email, name, password, date_of_birth: dateOfBirth };
    if (inviteCode) {
      payload.invite_code = inviteCode;
    }
    const response = await axios.post(`${API}/auth/register`, payload);
    const { access_token, user: userData } = response.data;
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setUser(userData);
    // Register web push token silently (non-blocking)
    registerWebPushToken(access_token);
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const updateUser = (userData) => {
    setUser(prev => ({ ...prev, ...userData }));
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, loginWithToken, register, logout, updateUser, token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);