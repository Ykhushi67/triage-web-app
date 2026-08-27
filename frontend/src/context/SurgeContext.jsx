import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { getSurgeStatus } from '../api/surge';
import { useAuth } from './AuthContext';

const SurgeContext = createContext(null);

export function SurgeProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [surgeState, setSurgeState] = useState({
    is_surge: false,
    operating_mode: 'NORMAL',
    surge_reason: null,
    queue_size: 0,
    critical_count: 0,
    avg_wait_min: 0,
    actions_required: [],
  });
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef(null);

  const refresh = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      setLoading(true);
      const res = await getSurgeStatus();
      setSurgeState(res.data);
    } catch (_) {
      // silently fail - backend might not be running
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      refresh();
      intervalRef.current = setInterval(refresh, 30000);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [isAuthenticated, refresh]);

  return (
    <SurgeContext.Provider value={{ surgeState, refresh, loading }}>
      {children}
    </SurgeContext.Provider>
  );
}

export const useSurge = () => {
  const ctx = useContext(SurgeContext);
  if (!ctx) throw new Error('useSurge must be used within SurgeProvider');
  return ctx;
};
