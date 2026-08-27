import React from 'react';
import { History, UserCheck, UserX, Clock, Building } from 'lucide-react';
import './HistoryPanel.css';

export default function HistoryPanel({ history }) {
  if (!history) return null;

  const { has_history, total_visits, visits = [], is_returning, history_badge } = history;

  return (
    <div className="history-panel card card-sm">
      <div className="history-header">
        <div className="history-badge-wrapper">
          {has_history ? (
            <span className="badge badge-purple history-badge-tag">
              <UserCheck size={13} />
              <span>RETURNING PATIENT ({total_visits} prior visit{total_visits === 1 ? '' : 's'})</span>
            </span>
          ) : (
            <span className="badge badge-stable history-badge-tag">
              <UserX size={13} />
              <span>FIRST-TIME PATIENT (No Prior Records)</span>
            </span>
          )}
        </div>
        <div className="history-isolation-note">
          🔒 Patient history is for clinician context only and is isolated from ML triage scoring.
        </div>
      </div>

      {has_history && visits.length > 0 && (
        <div className="history-visits-list">
          <div className="visits-title">Previous Hospital Encounters:</div>
          <div className="visits-table-wrapper">
            <table className="visits-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Department</th>
                  <th>Chief Complaint</th>
                  <th>Urgency</th>
                </tr>
              </thead>
              <tbody>
                {visits.map((v, i) => (
                  <tr key={i}>
                    <td><Clock size={12} style={{ display: 'inline', marginRight: '4px' }} />{v.visit_date}</td>
                    <td><Building size={12} style={{ display: 'inline', marginRight: '4px' }} />{v.department || '—'}</td>
                    <td>{v.chief_complaint || '—'}</td>
                    <td>
                      <span className={`badge ${v.triage_level === 1 ? 'badge-critical' : v.triage_level === 2 ? 'badge-moderate' : 'badge-stable'}`}>
                        {v.triage_label || `Level ${v.triage_level || '—'}`}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
