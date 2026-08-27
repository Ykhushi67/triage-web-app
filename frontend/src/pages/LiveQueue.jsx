import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { getLiveQueue } from '../api/queue';
import PatientTable from '../components/patient/PatientTable';
import PatientDrawer from '../components/patient/PatientDrawer';
import { LoadingState, ErrorState } from '../components/ui/States';
import { 
  Users, Search, Filter, RefreshCw, Building, AlertTriangle, 
  ShieldAlert, Clock, UserCheck 
} from 'lucide-react';
import './LiveQueue.css';

export default function LiveQueue() {
  const [queueData, setQueueData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('ALL'); // 'ALL' | '1' | '2' | '3' | 'REASSESS' | 'DETERIORATING'
  const [departmentFilter, setDepartmentFilter] = useState('ALL'); // 'ALL' | specific department name
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getLiveQueue();
      setQueueData(res.data);
    } catch (err) {
      setError('Unable to fetch live emergency queue.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue();
    const interval = setInterval(loadQueue, 15000);
    return () => clearInterval(interval);
  }, [loadQueue]);

  const queue = queueData?.queue || [];
  const summary = queueData?.summary || { total_waiting: 0, critical_count: 0, moderate_count: 0, low_count: 0 };

  // Dynamically extract all available unique departments from the queue
  const availableDepartments = useMemo(() => {
    const set = new Set();
    queue.forEach(p => {
      if (p.department) set.add(p.department);
    });
    // Add common canonical emergency departments
    ['Emergency', 'Cardiology', 'Pulmonology', 'Neurology', 'Gastroenterology', 'Orthopedics', 'General Medicine', 'Pediatrics'].forEach(d => set.add(d));
    return Array.from(set).sort();
  }, [queue]);

  // Client-side filtering by Priority, Department, and Search query
  const filteredQueue = useMemo(() => {
    return queue.filter((p) => {
      // 1. Search Query Filter (name or patient_id)
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = p.patient_name?.toLowerCase().includes(q);
        const matchesId = p.patient_id?.toLowerCase().includes(q);
        const matchesComplaint = p.chief_complaint?.toLowerCase().includes(q);
        if (!matchesName && !matchesId && !matchesComplaint) return false;
      }

      // 2. Department Filter
      if (departmentFilter !== 'ALL') {
        const pDept = (p.department || 'General Medicine').toLowerCase();
        if (pDept !== departmentFilter.toLowerCase()) return false;
      }

      // 3. Priority Level / Status Filter
      if (priorityFilter === '1' && p.triage_level !== 1) return false;
      if (priorityFilter === '2' && p.triage_level !== 2) return false;
      if (priorityFilter === '3' && p.triage_level !== 3) return false;
      if (priorityFilter === 'REASSESS' && !p.requires_reassessment) return false;
      if (priorityFilter === 'DETERIORATING' && !p.is_deteriorating) return false;

      return true;
    });
  }, [queue, searchQuery, departmentFilter, priorityFilter]);

  const handleSelectPatient = (p) => {
    setSelectedPatient(p);
    setDrawerOpen(true);
  };

  return (
    <div className="live-queue-page">
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Live Clinical Priority Queue</h1>
          <p className="page-subtitle">Emergency Department active patient queue sorted by physiological risk and wait time</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadQueue} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Queue Summary Counter Strip */}
      <div className="queue-summary-strip mb-4">
        <div className="summary-pill">
          <span className="pill-val">{summary.total_waiting}</span>
          <span className="pill-lbl">Total Waiting</span>
        </div>
        <div className="summary-pill pill-critical">
          <span className="pill-val">🔴 {summary.critical_count}</span>
          <span className="pill-lbl">Level 1 Critical</span>
        </div>
        <div className="summary-pill pill-moderate">
          <span className="pill-val">🟡 {summary.moderate_count}</span>
          <span className="pill-lbl">Level 2 Moderate</span>
        </div>
        <div className="summary-pill pill-stable">
          <span className="pill-val">🟢 {summary.low_count}</span>
          <span className="pill-lbl">Level 3 Low</span>
        </div>
      </div>

      {/* Control Bar: Filters & Department Selector */}
      <div className="card card-body queue-controls-card mb-4">
        <div className="queue-filters-row">
          {/* Search Box */}
          <div className="queue-search-box">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="queue-search-input"
              placeholder="Search by patient ID, name, or symptom..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button className="search-clear-btn" onClick={() => setSearchQuery('')}>×</button>
            )}
          </div>

          {/* Department Filter Dropdown (Requested Feature!) */}
          <div className="dept-filter-box">
            <Building size={16} className="dept-icon text-purple" />
            <select
              className="dept-select"
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              title="Filter queue by clinical department"
            >
              <option value="ALL">All Departments (Hospital Wide)</option>
              {availableDepartments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept} Department
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Priority Level Filter Tabs */}
        <div className="priority-tabs-row mt-3">
          <button
            className={`p-tab ${priorityFilter === 'ALL' ? 'p-tab-active' : ''}`}
            onClick={() => setPriorityFilter('ALL')}
          >
            All Patients ({queue.length})
          </button>
          <button
            className={`p-tab p-tab-critical ${priorityFilter === '1' ? 'p-tab-active' : ''}`}
            onClick={() => setPriorityFilter('1')}
          >
            🔴 Critical Level 1 ({queue.filter(p => p.triage_level === 1).length})
          </button>
          <button
            className={`p-tab p-tab-moderate ${priorityFilter === '2' ? 'p-tab-active' : ''}`}
            onClick={() => setPriorityFilter('2')}
          >
            🟡 Moderate Level 2 ({queue.filter(p => p.triage_level === 2).length})
          </button>
          <button
            className={`p-tab p-tab-stable ${priorityFilter === '3' ? 'p-tab-active' : ''}`}
            onClick={() => setPriorityFilter('3')}
          >
            🟢 Low Level 3 ({queue.filter(p => p.triage_level === 3).length})
          </button>
          <button
            className={`p-tab ${priorityFilter === 'DETERIORATING' ? 'p-tab-active p-tab-critical' : ''}`}
            onClick={() => setPriorityFilter('DETERIORATING')}
          >
            ⚠ Deteriorating ({queue.filter(p => p.is_deteriorating).length})
          </button>
          <button
            className={`p-tab ${priorityFilter === 'REASSESS' ? 'p-tab-active p-tab-moderate' : ''}`}
            onClick={() => setPriorityFilter('REASSESS')}
          >
            ⏱ Reassessment Due ({queue.filter(p => p.requires_reassessment).length})
          </button>
        </div>
      </div>

      {/* Main Queue Table */}
      {loading && !queueData ? (
        <LoadingState message="Loading live emergency patient queue…" />
      ) : error ? (
        <ErrorState message={error} onRetry={loadQueue} />
      ) : (
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-primary">
                Displaying {filteredQueue.length} of {queue.length} Patients
              </span>
              {departmentFilter !== 'ALL' && (
                <span className="badge badge-purple">
                  Filter: {departmentFilter}
                </span>
              )}
            </div>
            <span className="text-xs text-muted">
              Click any patient to open review & history drawer
            </span>
          </div>
          <PatientTable
            queue={filteredQueue}
            onSelectPatient={handleSelectPatient}
            compact={false}
          />
        </div>
      )}

      {/* Slide-in Patient Drawer */}
      <PatientDrawer
        patient={selectedPatient}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onRefreshQueue={loadQueue}
      />
    </div>
  );
}
