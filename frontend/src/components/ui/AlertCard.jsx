import React from 'react';
import { AlertCircle, Clock, TrendingDown, ArrowRight } from 'lucide-react';
import './AlertCard.css';

export function AlertCard({ 
  type = 'CRITICAL', 
  title, 
  subtitle, 
  details, 
  actionLabel = 'Review', 
  onAction,
  icon: CustomIcon
}) {
  let Icon = AlertCircle;
  let typeClass = 'alert-critical';

  if (type === 'DETERIORATING' || type === 'ACUTE_DETERIORATION') {
    Icon = TrendingDown;
    typeClass = 'alert-critical alert-pulse';
  } else if (type === 'REASSESSMENT' || type === 'REASSESSMENT_OVERDUE') {
    Icon = Clock;
    typeClass = 'alert-warning';
  } else if (type === 'LOW_CONFIDENCE') {
    Icon = AlertCircle;
    typeClass = 'alert-info';
  }

  if (CustomIcon) Icon = CustomIcon;

  return (
    <div className={`alert-card ${typeClass}`}>
      <div className="alert-icon-col">
        <Icon size={20} />
      </div>
      <div className="alert-content-col">
        <div className="alert-card-title">{title}</div>
        {subtitle && <div className="alert-card-subtitle">{subtitle}</div>}
        {details && <div className="alert-card-details">{details}</div>}
      </div>
      {onAction && (
        <button className="btn btn-sm alert-action-btn" onClick={onAction}>
          <span>{actionLabel}</span>
          <ArrowRight size={14} />
        </button>
      )}
    </div>
  );
}
