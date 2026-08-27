import React from 'react';
import { PriorityBadge } from '../ui/Badges';
import { Clock, AlertTriangle, ArrowRight, User } from 'lucide-react';
import './PatientCard.css';

export default function PatientCard({ patient, onReview }) {
  if (!patient) return null;

  const {
    patient_id,
    patient_name,
    triage_level,
    triage_label,
    priority_score,
    waiting_minutes,
    confidence_pct,
    chief_complaint,
    is_deteriorating,
    requires_reassessment,
    safety_flags = [],
    is_overridden,
  } = patient;

  const isCritical = triage_level === 1;

  return (
    <div className={`patient-card ${isCritical ? 'patient-card-critical' : ''} ${is_deteriorating ? 'patient-card-deteriorating' : ''}`}>
      <div className="patient-card-top">
        <div className="patient-id-badge">
          <User size={13} />
          <span>{patient_id || 'PID-****'}</span>
        </div>
        <PriorityBadge level={triage_level} label={triage_label} />
      </div>

      <div className="patient-card-name-row">
        <h4 className="patient-card-name">{patient_name}</h4>
        <div className="patient-wait-badge">
          <Clock size={12} />
          <span>{waiting_minutes}m wait</span>
        </div>
      </div>

      {chief_complaint && (
        <div className="patient-complaint text-sm">
          "{chief_complaint}"
        </div>
      )}

      {safety_flags && safety_flags.length > 0 && (
        <div className="patient-card-flag">
          <AlertTriangle size={13} />
          <span>{safety_flags[0]}</span>
        </div>
      )}

      <div className="patient-card-metrics">
        <div className="metric-item">
          <span className="metric-label">Score</span>
          <span className="metric-val">{priority_score?.toFixed(1)}/10</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">AI Conf</span>
          <span className="metric-val">{confidence_pct || 0}%</span>
        </div>
        {is_deteriorating && (
          <span className="badge badge-critical">DETERIORATING</span>
        )}
        {requires_reassessment && (
          <span className="badge badge-moderate">REASSESS</span>
        )}
        {is_overridden && (
          <span className="badge badge-info">OVERRIDDEN</span>
        )}
      </div>

      <div className="patient-card-footer">
        <button className="btn btn-sm btn-primary w-full" onClick={() => onReview(patient)}>
          <span>REVIEW PATIENT</span>
          <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
