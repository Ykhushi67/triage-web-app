import React, { useState } from 'react';
import { X, ShieldAlert, Check } from 'lucide-react';
import './OverrideModal.css';

const REASON_CODES = [
  { code: 'PATIENT_CLINICALLY_WORSE', label: 'Patient clinically appears worse than score reflects' },
  { code: 'ADDITIONAL_INFO_AVAILABLE', label: 'Additional clinical history / ECG / lab information available' },
  { code: 'AI_UNSUITABLE', label: 'AI recommendation unsuitable for this presentation' },
  { code: 'LOCAL_CLINICAL_JUDGEMENT', label: 'Senior clinician / attending physician judgment' },
  { code: 'OTHER', label: 'Other clinical rationale (free-text explanation required)' },
];

export default function OverrideModal({ 
  isOpen, 
  onClose, 
  encounterId, 
  aiLevel = 2, 
  aiScore = 5.0, 
  onSubmit, 
  loading = false 
}) {
  if (!isOpen) return null;

  const [finalLevel, setFinalLevel] = useState(1);
  const [finalDept, setFinalDept] = useState('');
  const [reasonCode, setReasonCode] = useState('PATIENT_CLINICALLY_WORSE');
  const [reasonText, setReasonText] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!reasonCode) {
      setError('Please select a mandatory clinical override reason code.');
      return;
    }
    if (reasonCode === 'OTHER' && !reasonText.trim()) {
      setError('Please provide free-text clinical details when selecting "Other".');
      return;
    }

    setError('');
    onSubmit({
      encounter_id: encounterId,
      final_triage_level: Number(finalLevel),
      final_department: finalDept || undefined,
      reason_code: reasonCode,
      reason_free_text: reasonText.trim() || undefined,
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content override-modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="flex items-center gap-2">
            <ShieldAlert size={20} className="text-critical" />
            <span className="text-lg font-bold text-primary">Clinician Triage Override</span>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body flex flex-col gap-4">
            <div className="override-ai-baseline">
              <span className="text-xs text-muted font-semibold uppercase">AI Baseline:</span>
              <span className="badge badge-neutral">Level {aiLevel} (Score: {Number(aiScore).toFixed(1)}/10)</span>
              <span className="text-xs text-secondary ml-auto">Encounter: {encounterId}</span>
            </div>

            <div className="form-group">
              <label className="form-label">Final Clinical Urgency Level (Mandatory)</label>
              <div className="override-level-selector">
                <button
                  type="button"
                  className={`level-choice-btn ${finalLevel === 1 ? 'active-level-1' : ''}`}
                  onClick={() => setFinalLevel(1)}
                >
                  <span className="choice-badge badge-critical">🔴 Level 1</span>
                  <span className="choice-desc">CRITICAL (Immediate)</span>
                </button>
                <button
                  type="button"
                  className={`level-choice-btn ${finalLevel === 2 ? 'active-level-2' : ''}`}
                  onClick={() => setFinalLevel(2)}
                >
                  <span className="choice-badge badge-moderate">🟡 Level 2</span>
                  <span className="choice-desc">MODERATE (Urgent)</span>
                </button>
                <button
                  type="button"
                  className={`level-choice-btn ${finalLevel === 3 ? 'active-level-3' : ''}`}
                  onClick={() => setFinalLevel(3)}
                >
                  <span className="choice-badge badge-stable">🟢 Level 3</span>
                  <span className="choice-desc">LOW (Routine)</span>
                </button>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Specialty Department Assignment (Optional)</label>
              <select 
                className="form-select" 
                value={finalDept} 
                onChange={(e) => setFinalDept(e.target.value)}
              >
                <option value="">Select Department (Default: Auto)</option>
                <option value="Emergency">Emergency</option>
                <option value="Cardiology">Cardiology</option>
                <option value="Pulmonology">Pulmonology</option>
                <option value="Neurology">Neurology</option>
                <option value="Gastroenterology">Gastroenterology</option>
                <option value="Orthopedics">Orthopedics</option>
                <option value="General Medicine">General Medicine</option>
                <option value="Pediatrics">Pediatrics</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Structured Override Reason Code (Mandatory)</label>
              <select
                className="form-select"
                value={reasonCode}
                onChange={(e) => setReasonCode(e.target.value)}
              >
                {REASON_CODES.map((rc) => (
                  <option key={rc.code} value={rc.code}>{rc.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Clinical Justification & Notes</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Enter objective clinical rationale for audit trail (e.g. Diaphoretic, ST elevation on bedside ECG, acute distress)..."
                value={reasonText}
                onChange={(e) => setReasonText(e.target.value)}
              />
            </div>

            {error && <div className="form-error">{error}</div>}

            <div className="override-disclaimer">
              🛡 This action will be permanently recorded in the immutable audit trail with your Clinician ID.
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-warning" disabled={loading}>
              <Check size={16} />
              <span>{loading ? 'Recording Override…' : 'Confirm Override & Update Queue'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
