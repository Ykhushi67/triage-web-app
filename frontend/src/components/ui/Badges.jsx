/* PriorityBadge */
export function PriorityBadge({ level, label, size = 'md' }) {
  const map = {
    1: { cls: 'badge-critical', text: label || 'CRITICAL', icon: '🔴' },
    2: { cls: 'badge-moderate', text: label || 'MODERATE', icon: '🟡' },
    3: { cls: 'badge-stable',   text: label || 'STABLE',   icon: '🟢' },
  };
  const { cls, text, icon } = map[level] || { cls: 'badge-neutral', text: 'UNKNOWN', icon: '⚪' };

  return (
    <span className={`badge ${cls} ${size === 'lg' ? 'badge-lg' : ''}`}>
      {icon} {text}
    </span>
  );
}

/* StatusBadge */
export function StatusBadge({ status, label }) {
  const statusMap = {
    WAITING: 'badge-moderate',
    UNDER_REVIEW: 'badge-info',
    COMPLETED: 'badge-stable',
    ESCALATED: 'badge-critical',
    DISCHARGED: 'badge-neutral',
  };
  return (
    <span className={`badge ${statusMap[status] || 'badge-neutral'}`}>
      {label || status}
    </span>
  );
}
