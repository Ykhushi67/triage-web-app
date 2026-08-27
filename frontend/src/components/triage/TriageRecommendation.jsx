import React from 'react';
import { PriorityBadge } from '../ui/Badges';
import ConfidenceIndicator from '../ui/ConfidenceIndicator';
import { VitalsGrid } from '../ui/VitalCard';
import { AlertTriangle, CheckCircle, ShieldAlert, Cpu, Building } from 'lucide-react';
import './TriageRecommendation.css';

export default function TriageRecommendation({ 
  result, 
  onAccept, 
  onOverride, 
  acceptLoading = false,
  showActions = true 
}) {
  if (!result) return null;

  const {
    triage_level,
    triage_label,
    priority_score,
    confidence,
    confidence_pct,
    recommended_department,
    department_probabilities = {},
    safety_flags = [],
    key_factors = [],
    uncertainty_flags = [],
    missing_vitals_count = 0,
    requires_clinician_review = false,
    vitals_normalized,
  } = result;

  const isLevel1 = triage_level === 1;

  return (
    <div className="triage-recommendation-card">
      <div className="triage-rec-header">
        <div className="flex items-center gap-2">
          <Cpu size={18} className="text-purple" />
          <span className="text-sm font-semibold text-secondary uppercase tracking-wider">
            AI Triage Recommendation (Clinical Decision Support)
          </span>
        </div>
        {requires_clinician_review && (
          <span className="badge badge-critical">
            <ShieldAlert size={12} /> MANDATORY REVIEW REQUIRED
          </span>
        )}
      </div>

      <div className={`triage-level-banner ${isLevel1 ? 'banner-critical' : triage_level === 2 ? 'banner-moderate' : 'banner-stable'}`}>
        <div className="banner-level-badge">
          <PriorityBadge level={triage_level} label={triage_label} size="lg" />
        </div>
        <div className="banner-score-box">
          <span className="banner-score-title">Priority Score</span>
          <span className="banner-score-val">{priority_score !== undefined ? Number(priority_score).toFixed(1) : '—'} <small>/ 10</small></span>
        </div>
        {recommended_department && (
          <div className="banner-dept-box">
            <span className="banner-dept-title"><Building size={12} /> Recommended Dept</span>
            <span className="banner-dept-val">{recommended_department}</span>
          </div>
        )}
      </div>

      <ConfidenceIndicator 
        confidence={confidence}
        confidencePct={confidence_pct}
        missingCount={missing_vitals_count}
        uncertaintyFlags={uncertainty_flags}
      />

      {safety_flags && safety_flags.length > 0 && (
        <div className="safety-flags-section">
          <div className="flags-header">
            <AlertTriangle size={16} />
            <span>Safety Rule Hard Floors Enforced:</span>
          </div>
          <ul className="safety-flags-list">
            {safety_flags.map((sf, idx) => (
              <li key={idx}>• {sf}</li>
            ))}
          </ul>
        </div>
      )}

      {key_factors && key_factors.length > 0 && (
        <div className="key-factors-section">
          <div className="factors-title">Clinical Explainability (Key Contributing Factors):</div>
          <ul className="factors-list">
            {key_factors.map((factor, idx) => (
              <li key={idx}>• {factor}</li>
            ))}
          </ul>
        </div>
      )}

      {vitals_normalized && (
        <div className="rec-vitals-section">
          <div className="text-xs font-semibold text-secondary uppercase tracking-wider mb-1">
            Normalized Vitals for Clinical Review:
          </div>
          <VitalsGrid vitals={vitals_normalized} />
        </div>
      )}

      {showActions && (
        <div className="triage-actions-bar">
          <button 
            className="btn btn-success btn-lg" 
            onClick={onAccept}
            disabled={acceptLoading}
          >
            <CheckCircle size={18} />
            <span>{acceptLoading ? 'Confirming…' : 'ACCEPT AI RECOMMENDATION'}</span>
          </button>
          <button 
            className="btn btn-warning btn-lg" 
            onClick={onOverride}
          >
            <span>OVERRIDE RECOMMENDATION</span>
          </button>
        </div>
      )}
    </div>
  );
}
