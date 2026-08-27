import React, { useState, useEffect } from 'react';
import { getAuditLogs } from '../api/audit';
import AuditTable from '../components/audit/AuditTable';
import { LoadingState, ErrorState } from '../components/ui/States';
import { 
  ClipboardList, ShieldCheck, Filter, RefreshCw, 
  Search, Download, FileText 
} from 'lucide-react';
import './AuditLog.css';

export default function AuditLog() {
  const [logs, setLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [actionFilter, setActionFilter] = useState('');
  const [searchPatientId, setSearchPatientId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadLogs = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getAuditLogs(0, 100, actionFilter || undefined);
      setLogs(res.data.logs || []);
      setTotal(res.data.total || 0);
    } catch (_) {
      setError('Unable to retrieve audit records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, [actionFilter]);

  const filteredLogs = logs.filter((log) => {
    if (!searchPatientId.trim()) return true;
    return log.patient_id?.toLowerCase().includes(searchPatientId.trim().toLowerCase());
  });

  const handleExportCSV = () => {
    if (filteredLogs.length === 0) return;
    const headers = ['Audit ID', 'Timestamp', 'Patient ID', 'Actor Role', 'Action', 'Old Value', 'New Value', 'Reason'];
    const rows = filteredLogs.map(l => [
      l.audit_id,
      l.timestamp,
      l.patient_id,
      l.actor_role,
      l.action,
      `"${l.previous_value || ''}"`,
      `"${l.new_value || ''}"`,
      `"${l.reason || ''}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `triage_audit_log_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="audit-log-page">
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Persistent Audit Trail & Clinical Governance</h1>
          <p className="page-subtitle">Immutable chronological log of all AI triage generations, clinician overrides, and surge transitions</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary btn-sm" onClick={handleExportCSV} disabled={filteredLogs.length === 0}>
            <Download size={14} />
            <span>Export CSV</span>
          </button>
          <button className="btn btn-secondary btn-sm" onClick={loadLogs} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Logs</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="card card-body mb-4">
        <div className="audit-filters-row">
          <div className="audit-search-box">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="form-input pl-8"
              placeholder="Search by pseudonymized Patient ID (e.g. PID-0011)..."
              value={searchPatientId}
              onChange={(e) => setSearchPatientId(e.target.value)}
            />
          </div>

          <div className="audit-select-box">
            <Filter size={16} className="filter-icon text-muted" />
            <select
              className="form-select pl-8"
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            >
              <option value="">All Action Types</option>
              <option value="AI_TRIAGE_GENERATED">AI Triage Generated</option>
              <option value="CLINICIAN_ACCEPTED">Clinician Accepted</option>
              <option value="CLINICIAN_OVERRIDDEN">Clinician Overridden</option>
              <option value="DETERIORATION_FLAGGED">Deterioration Flagged</option>
              <option value="VITALS_REASSESSED">Vitals Reassessed</option>
              <option value="SURGE_MANUAL_ACTIVATED">Surge Activated</option>
              <option value="SURGE_DEACTIVATED">Surge Deactivated</option>
            </select>
          </div>
        </div>

        <div className="dpdp-strip-note mt-3">
          <ShieldCheck size={14} className="text-stable" />
          <span>
            <strong>DPDP Act 2023 Principles Enforced:</strong> Audit records store pseudonymous IDs (`PID-****`) and clinical reason codes without identifiable personal data.
          </span>
        </div>
      </div>

      {loading ? (
        <LoadingState message="Loading immutable audit logs..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadLogs} />
      ) : (
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <span className="text-sm font-bold text-primary">
              Displaying {filteredLogs.length} of {total} Recorded Audit Events
            </span>
            <span className="text-xs text-muted">Append-only database ledger</span>
          </div>
          <AuditTable logs={filteredLogs} />
        </div>
      )}
    </div>
  );
}
