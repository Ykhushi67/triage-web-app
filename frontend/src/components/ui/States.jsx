import React from 'react';
import { Loader2, Inbox, AlertTriangle, RefreshCw } from 'lucide-react';

export function LoadingState({ message = 'Loading triage data…' }) {
  return (
    <div className="card card-body flex flex-col items-center justify-center" style={{ minHeight: '200px', gap: 'var(--space-3)' }}>
      <Loader2 size={28} className="text-purple" style={{ animation: 'spin 1s linear infinite' }} />
      <span className="text-sm font-medium text-secondary">{message}</span>
    </div>
  );
}

export function EmptyState({ title = 'No records found', message = 'No matching patient records in the current queue.', actionLabel, onAction }) {
  return (
    <div className="card card-body flex flex-col items-center justify-center text-center" style={{ minHeight: '220px', gap: 'var(--space-3)' }}>
      <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        <Inbox size={24} />
      </div>
      <div>
        <div className="text-md font-semibold text-primary">{title}</div>
        <div className="text-sm text-secondary mt-1">{message}</div>
      </div>
      {actionLabel && onAction && (
        <button className="btn btn-sm btn-secondary mt-2" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  );
}

export function ErrorState({ title = 'Unable to load data', message = 'Failed to communicate with the hospital backend service.', onRetry }) {
  return (
    <div className="card card-body flex flex-col items-center justify-center text-center" style={{ minHeight: '220px', gap: 'var(--space-3)', borderColor: 'var(--color-critical-border)', background: 'var(--color-critical-bg)' }}>
      <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: '#FEE2E2', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-critical)' }}>
        <AlertTriangle size={24} />
      </div>
      <div>
        <div className="text-md font-semibold text-critical">{title}</div>
        <div className="text-sm text-secondary mt-1">{message}</div>
      </div>
      {onRetry && (
        <button className="btn btn-sm btn-secondary mt-2" onClick={onRetry} style={{ background: '#fff' }}>
          <RefreshCw size={14} />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
