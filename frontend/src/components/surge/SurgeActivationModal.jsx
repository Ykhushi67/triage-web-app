import React, { useState } from 'react';
import { X, AlertTriangle, Zap } from 'lucide-react';
import { activateSurge } from '../../api/surge';
import { useSurge } from '../../context/SurgeContext';

export default function SurgeActivationModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  const { refresh } = useSurge();
  const [reason, setReason] = useState('Mass Casualty Influx');
  const [detail, setDetail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleActivate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await activateSurge({ reason, reason_detail: detail || undefined });
      await refresh();
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to activate surge mode.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="flex items-center gap-2">
            <AlertTriangle size={20} className="text-critical" />
            <span className="text-lg font-bold text-critical">Activate Emergency Surge Mode</span>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={18} /></button>
        </div>

        <form onSubmit={handleActivate}>
          <div className="modal-body flex flex-col gap-4">
            <p className="text-sm text-secondary">
              Surge mode alters operational prioritization, highlights immediate action items, and flags rapid capacity bottlenecks. Clinical triage criteria remain strictly physiological.
            </p>

            <div className="form-group">
              <label className="form-label">Primary Surge Trigger Reason (Mandatory)</label>
              <select className="form-select" value={reason} onChange={(e) => setReason(e.target.value)}>
                <option value="Mass Casualty Influx">Mass Casualty Influx (Accident / Multi-victim)</option>
                <option value="Severe Capacity Overload">Severe Capacity Overload (&gt;3× Arrival Rate)</option>
                <option value="Staffing Shortage">Critical Clinical Staffing Shortage</option>
                <option value="Epidemic / Infection Wave">Epidemic / Acute Infection Outbreak Influx</option>
                <option value="Other Operational Surge">Other Operational Crisis</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Clinical Justification Details</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Enter details (e.g. Highway collision with 8 ambulances incoming, all trauma bays occupied)..."
                value={detail}
                onChange={(e) => setDetail(e.target.value)}
              />
            </div>

            {error && <div className="form-error">{error}</div>}

            <div className="text-xs text-muted">
              🛡 Activation reason is logged to the immutable hospital audit trail.
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-critical" disabled={loading}>
              <Zap size={16} />
              <span>{loading ? 'Activating…' : 'CONFIRM SURGE ACTIVATION'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
