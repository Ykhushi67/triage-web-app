import { AlertTriangle, Zap } from 'lucide-react';
import { useSurge } from '../../context/SurgeContext';
import { deactivateSurge } from '../../api/surge';
import { useState } from 'react';
import './SurgeBanner.css';

export default function SurgeBanner() {
  const { surgeState, refresh } = useSurge();
  const [deactivating, setDeactivating] = useState(false);

  if (!surgeState.is_surge) return null;

  const handleDeactivate = async () => {
    setDeactivating(true);
    try {
      await deactivateSurge({ reason: 'Normal load restored' });
      await refresh();
    } catch (_) {} finally {
      setDeactivating(false);
    }
  };

  return (
    <div className="surge-banner">
      <div className="surge-banner-inner">
        <span className="surge-banner-icon"><AlertTriangle size={16} /></span>
        <span className="surge-banner-text">
          <strong>SURGE MODE ACTIVE</strong>
          {surgeState.surge_reason && <span> — {surgeState.surge_reason}</span>}
          <span className="surge-banner-stats">
            {surgeState.queue_size} patients · {surgeState.critical_count} critical · Avg wait {Math.round(surgeState.avg_wait_min)}m
          </span>
        </span>
        <button className="surge-banner-deactivate" onClick={handleDeactivate} disabled={deactivating}>
          <Zap size={14} />
          {deactivating ? 'Deactivating…' : 'Return to Normal Mode'}
        </button>
      </div>
    </div>
  );
}
