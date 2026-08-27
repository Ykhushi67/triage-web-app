import React from 'react';
import { Clock, User, Cpu, AlertTriangle, CheckCircle, ArrowUpRight, Activity } from 'lucide-react';
import './Timeline.css';

export default function Timeline({ events = [] }) {
  if (!events || events.length === 0) {
    return <div className="text-sm text-muted">No chronological events logged yet.</div>;
  }

  const getEventIcon = (action) => {
    switch (action) {
      case 'AI_TRIAGE_GENERATED': return { icon: Cpu, color: 'icon-purple' };
      case 'CLINICIAN_ACCEPTED': return { icon: CheckCircle, color: 'icon-green' };
      case 'CLINICIAN_OVERRIDDEN': return { icon: ArrowUpRight, color: 'icon-amber' };
      case 'DETERIORATION_FLAGGED': return { icon: AlertTriangle, color: 'icon-red' };
      case 'VITALS_REASSESSED': return { icon: Activity, color: 'icon-blue' };
      default: return { icon: User, color: 'icon-gray' };
    }
  };

  const fmtTime = (ts) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    } catch {
      return ts;
    }
  };

  return (
    <div className="timeline-container">
      {events.map((evt, idx) => {
        const { icon: EventIcon, color } = getEventIcon(evt.action);
        return (
          <div className="timeline-item" key={idx}>
            <div className="timeline-left">
              <div className={`timeline-icon-dot ${color}`}>
                <EventIcon size={14} />
              </div>
              {idx < events.length - 1 && <div className="timeline-line" />}
            </div>
            <div className="timeline-content">
              <div className="timeline-meta">
                <span className="timeline-time">{fmtTime(evt.timestamp)}</span>
                <span className="timeline-actor">{evt.actor_role || 'SYSTEM'}</span>
              </div>
              <div className="timeline-title">{evt.action?.replace(/_/g, ' ')}</div>
              {evt.new_value && <div className="timeline-value">{evt.new_value}</div>}
              {evt.reason && <div className="timeline-reason">Reason: {evt.reason}</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
