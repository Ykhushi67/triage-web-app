import React from 'react';
import { PriorityBadge, StatusBadge } from '../ui/Badges';
import { Clock, AlertTriangle, ChevronRight, UserCheck, UserX } from 'lucide-react';
import './PatientTable.css';

export default function PatientTable({ queue = [], onSelectPatient, onReassess, compact = false }) {
  if (!queue || queue.length === 0) {
    return <div className="text-sm text-muted text-center py-6">No patients currently in queue.</div>;
  }

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>Rank / Priority</th>
            <th>Patient ID & Name</th>
            {!compact && <th>Dept</th>}
            {!compact && <th>Chief Complaint</th>}
            <th>Wait Time</th>
            {!compact && <th>AI Conf</th>}
            <th>Status / Alerts</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {queue.map((p, idx) => {
            const isCritical = p.triage_level === 1;
            return (
              <tr 
                key={p.encounter_id || idx} 
                onClick={() => onSelectPatient(p)}
                className={isCritical ? 'row-critical' : p.is_deteriorating ? 'row-deteriorating' : ''}
              >
                <td>
                  <div className="flex items-center gap-2">
                    <span className="rank-num">#{idx + 1}</span>
                    <PriorityBadge level={p.triage_level} label={p.triage_label} />
                  </div>
                </td>
                <td>
                  <div className="patient-name-cell">
                    <span className="font-semibold text-primary">{p.patient_name}</span>
                    <div className="patient-sub-meta">
                      <span>{p.patient_id}</span>
                      {p.age && <span>• {p.age}y</span>}
                      {p.sex && <span>• {p.sex}</span>}
                      {p.history_badge === 'Returning' ? (
                        <span className="history-mini-badge returning" title="Returning Patient"><UserCheck size={11} /> Returning</span>
                      ) : (
                        <span className="history-mini-badge first-time" title="First-time Patient"><UserX size={11} /> First</span>
                      )}
                    </div>
                  </div>
                </td>
                {!compact && (
                  <td>
                    <span className="dept-tag">{p.department || 'General'}</span>
                  </td>
                )}
                {!compact && (
                  <td>
                    <span className="complaint-truncate" title={p.chief_complaint}>
                      {p.chief_complaint || '—'}
                    </span>
                  </td>
                )}
                <td>
                  <div className="flex items-center gap-1 text-sm font-medium">
                    <Clock size={13} className="text-muted" />
                    <span>{p.waiting_minutes}m</span>
                  </div>
                </td>
                {!compact && (
                  <td>
                    <span className="text-sm font-semibold">
                      {p.confidence_pct ? `${p.confidence_pct}%` : '—'}
                    </span>
                  </td>
                )}
                <td>
                  <div className="flex items-center gap-1 flex-wrap">
                    {p.is_deteriorating && (
                      <span className="badge badge-critical animate-pulse" title="SpO2 / HR deterioration detected">
                        <AlertTriangle size={11} /> DETERIORATING
                      </span>
                    )}
                    {p.requires_reassessment && (
                      <span className="badge badge-moderate" title="Reassessment due">
                        REASSESS
                      </span>
                    )}
                    {p.is_overridden && (
                      <span className="badge badge-info" title="Clinician overrode AI score">
                        OVERRIDDEN
                      </span>
                    )}
                    {!p.is_deteriorating && !p.requires_reassessment && !p.is_overridden && (
                      <StatusBadge status={p.status} />
                    )}
                  </div>
                </td>
                <td>
                  <div className="flex items-center gap-2">
                    <button 
                      className="btn btn-sm btn-secondary" 
                      onClick={(e) => { e.stopPropagation(); onSelectPatient(p); }}
                    >
                      <span>Review</span>
                      <ChevronRight size={13} />
                    </button>
                    {onReassess && p.requires_reassessment && (
                      <button 
                        className="btn btn-sm btn-warning"
                        onClick={(e) => { e.stopPropagation(); onReassess(p); }}
                      >
                        Reassess
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
