import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { login as loginApi } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('pt_user')); } catch { return null; }
  });
  const [token, setToken] = useState(() => localStorage.getItem('pt_token'));

  const login = useCallback(async (email, password) => {
    const res = await loginApi(email, password);
    const { access_token, user: userInfo } = res.data;
    localStorage.setItem('pt_token', access_token);
    localStorage.setItem('pt_user', JSON.stringify(userInfo));
    setToken(access_token);
    setUser(userInfo);
    return userInfo;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('pt_token');
    localStorage.removeItem('pt_user');
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    const handler = () => logout();
    window.addEventListener('auth:logout', handler);
    return () => window.removeEventListener('auth:logout', handler);
  }, [logout]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
