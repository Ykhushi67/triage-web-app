import React from 'react';
import { ShieldCheck, Cpu, User, Activity, AlertTriangle, ArrowUpRight, CheckCircle } from 'lucide-react';
import './AuditTable.css';

export default function AuditTable({ logs = [], loading = false }) {
  if (loading) {
    return <div className="text-sm text-muted text-center py-6">Loading audit events…</div>;
  }

  if (!logs || logs.length === 0) {
    return <div className="text-sm text-muted text-center py-6">No audit records found.</div>;
  }

  const getActionBadge = (action) => {
    switch (action) {
      case 'AI_TRIAGE_GENERATED':
        return <span className="badge badge-purple"><Cpu size={11} /> AI GENERATED</span>;
      case 'CLINICIAN_ACCEPTED':
        return <span className="badge badge-stable"><CheckCircle size={11} /> ACCEPTED</span>;
      case 'CLINICIAN_OVERRIDDEN':
        return <span className="badge badge-moderate"><ArrowUpRight size={11} /> OVERRIDDEN</span>;
      case 'DETERIORATION_FLAGGED':
        return <span className="badge badge-critical"><AlertTriangle size={11} /> DETERIORATION</span>;
      case 'VITALS_REASSESSED':
        return <span className="badge badge-info"><Activity size={11} /> REASSESSED</span>;
      case 'SURGE_AUTO_DETECTED':
      case 'SURGE_MANUAL_ACTIVATED':
        return <span className="badge badge-critical">SURGE ACTIVATED</span>;
      case 'SURGE_DEACTIVATED':
        return <span className="badge badge-neutral">SURGE ENDED</span>;
      default:
        return <span className="badge badge-neutral">{action}</span>;
    }
  };

  const fmtTimestamp = (ts) => {
    if (!ts) return '—';
    try {
      const d = new Date(ts);
      return d.toLocaleString('en-IN', {
        day: '2-digit', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit',
        hour12: false
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className="table-wrapper">
      <table className="data-table audit-data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Patient ID (Pseudonymized)</th>
            <th>Actor / Role</th>
            <th>Action Type</th>
            <th>Previous Value</th>
            <th>New Value</th>
            <th>Clinical Reason / Details</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.audit_id}>
              <td>
                <span className="audit-time">{fmtTimestamp(log.timestamp)}</span>
              </td>
              <td>
                <span className="audit-patient-id">{log.patient_id || '—'}</span>
              </td>
              <td>
                <div className="flex items-center gap-1">
                  {log.actor_role === 'SYSTEM' ? <Cpu size={12} className="text-purple" /> : <User size={12} className="text-muted" />}
                  <span className="audit-role">{log.actor_role || 'SYSTEM'}</span>
                </div>
              </td>
              <td>{getActionBadge(log.action)}</td>
              <td>
                <span className="audit-val-old">{log.previous_value || '—'}</span>
              </td>
              <td>
                <span className="audit-val-new">{log.new_value || '—'}</span>
              </td>
              <td>
                <span className="audit-reason" title={log.reason}>
                  {log.reason || '—'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
