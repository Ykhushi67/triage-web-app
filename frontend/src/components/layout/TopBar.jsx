import { useState, useEffect } from 'react';
import { Wifi, WifiOff, Zap } from 'lucide-react';
import { useSurge } from '../../context/SurgeContext';
import { useAuth } from '../../context/AuthContext';
import { deactivateSurge } from '../../api/surge';
import './TopBar.css';

export default function TopBar() {
  const { user } = useAuth();
  const { surgeState, refresh } = useSurge();
  const [now, setNow] = useState(new Date());
  const [online, setOnline] = useState(true);
  const [deactivating, setDeactivating] = useState(false);

  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const fmtDate = (d) => d.toLocaleDateString('en-IN', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' });
  const fmtTime = (d) => d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });

  const handleReturnToNormal = async () => {
    setDeactivating(true);
    try {
      await deactivateSurge({ reason: 'Normal operational load restored' });
      await refresh();
    } catch (_) {
    } finally {
      setDeactivating(false);
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="topbar-dept">Emergency Department</div>
        <div className="topbar-datetime">
          <span>{fmtDate(now)}</span>
          <span className="topbar-time">{fmtTime(now)}</span>
        </div>
      </div>

      <div className="topbar-right">
        {surgeState.is_surge ? (
          <button 
            className="topbar-mode-surge"
            onClick={handleReturnToNormal}
            disabled={deactivating}
            title="Click to deactivate Surge Mode and return to Normal operations"
            style={{ cursor: 'pointer', border: '1px solid var(--color-critical-border)' }}
          >
            <span className="topbar-surge-dot" />
            <span>{deactivating ? 'Restoring…' : 'SURGE ACTIVE (Click to Normal)'}</span>
          </button>
        ) : (
          <div className="topbar-mode-normal">
            <span className="topbar-normal-dot" />
            NORMAL MODE
          </div>
        )}

        <div className="topbar-ai-status">
          {online ? (
            <><Wifi size={13} /> AI System Online</>
          ) : (
            <><WifiOff size={13} /> AI Offline</>
          )}
        </div>

        {user && (
          <div className="topbar-user">
            <div className="topbar-avatar">{user.name?.[0] || 'U'}</div>
            <span className="topbar-user-name">{user.name}</span>
            <span className="topbar-user-role">{user.role?.replace('_', ' ')}</span>
          </div>
        )}
      </div>
    </header>
  );
}
