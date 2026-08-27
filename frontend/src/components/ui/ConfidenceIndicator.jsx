import React from 'react';
import { AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import './ConfidenceIndicator.css';

export default function ConfidenceIndicator({ confidence, confidencePct, missingCount = 0, uncertaintyFlags = [] }) {
  const pct = confidencePct !== undefined ? confidencePct : Math.round((confidence || 0) * 100);
  
  let statusText = 'HIGH CONFIDENCE';
  let statusClass = 'confidence-high';
  let StatusIcon = CheckCircle2;

  if (pct < 72 || missingCount > 0 || uncertaintyFlags.length > 0) {
    if (pct < 60 || missingCount >= 3) {
      statusText = 'HIGH UNCERTAINTY — CLINICIAN REVIEW REQUIRED';
      statusClass = 'confidence-low';
      StatusIcon = AlertCircle;
    } else {
      statusText = 'MODERATE UNCERTAINTY';
      statusClass = 'confidence-med';
      StatusIcon = AlertTriangle;
    }
  }

  return (
    <div className={`confidence-indicator-card ${statusClass}`}>
      <div className="confidence-header">
        <div className="confidence-label">
          <StatusIcon size={16} />
          <span>AI Model Confidence</span>
        </div>
        <div className="confidence-value">{pct}%</div>
      </div>

      <div className="confidence-bar-bg">
        <div 
          className="confidence-bar-fill" 
          style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
        />
      </div>

      <div className="confidence-status-badge">
        {statusText}
      </div>

      {uncertaintyFlags && uncertaintyFlags.length > 0 && (
        <div className="confidence-missing-flags">
          <div className="flags-title">Clinical Information Incomplete:</div>
          <ul className="flags-list">
            {uncertaintyFlags.map((flag, idx) => (
              <li key={idx}>• {flag}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
