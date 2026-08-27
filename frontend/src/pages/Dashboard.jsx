import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getLiveQueue } from '../api/queue';
import { triggerDeterioration, triggerSurgeInflux, resetDemo } from '../api/demo';
import { deactivateSurge } from '../api/surge';
import { useSurge } from '../context/SurgeContext';
import PatientCard from '../components/patient/PatientCard';
import PatientTable from '../components/patient/PatientTable';
import PatientDrawer from '../components/patient/PatientDrawer';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/States';
import { AlertCard } from '../components/ui/AlertCard';
import { 
  Users, AlertTriangle, Clock, RefreshCw, Zap, ArrowRight, 
  ShieldAlert, Activity, CheckCircle2, Play, RotateCcw
} from 'lucide-react';
import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const { surgeState, refresh: refreshSurge } = useSurge();
  const [queueData, setQueueData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [actionMessage, setActionMessage] = useState('');

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getLiveQueue();
      setQueueData(res.data);
    } catch (err) {
      setError('Unable to retrieve current triage queue from hospital server.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue();
    const interval = setInterval(loadQueue, 15000); // 15s refresh
    return () => clearInterval(interval);
  }, [loadQueue]);

  const handleSelectPatient = (patient) => {
    setSelectedPatient(patient);
    setDrawerOpen(true);
  };

  // Demo scenario trigger helpers
  const handleTriggerDeterioration = async () => {
    setActionMessage('Simulating acute SpO₂ deterioration…');
    try {
      await triggerDeterioration();
      await loadQueue();
      await refreshSurge();
      setActionMessage('⚠ Deterioration alert triggered on waiting patient (SpO₂ dropped to 88%).');
    } catch (_) {
      setActionMessage('Could not trigger deterioration scenario.');
    }
  };

  const handleTriggerSurge = async () => {
    setActionMessage('Injecting 3× mass-casualty wave (8 emergency patients)…');
    try {
      await triggerSurgeInflux();
      await loadQueue();
      await refreshSurge();
      setActionMessage('🚨 3× Surge Wave Injected! Auto-surge state recommended.');
    } catch (_) {
      setActionMessage('Could not trigger surge influx.');
    }
  };

  const handleResetDemo = async () => {
    setActionMessage('Resetting demo database to baseline 22 scenarios and Normal Mode…');
    try {
      await resetDemo();
      try {
        await deactivateSurge({ reason: 'Demo database reset to normal baseline' });
      } catch (_) {}
      await loadQueue();
      await refreshSurge();
      setActionMessage('✓ Demo database reset to Normal Mode with all 15 clinical criteria.');
    } catch (_) {
      setActionMessage('Failed to reset demo database.');
    }
  };

  const handleReturnToNormal = async () => {
    setActionMessage('Restoring Normal Mode…');
    try {
      await deactivateSurge({ reason: 'Normal operational load restored' });
      await loadQueue();
      await refreshSurge();
      setActionMessage('✓ Operating Mode restored to NORMAL.');
    } catch (_) {
      setActionMessage('Could not deactivate Surge Mode.');
    }
  };

  const summary = queueData?.summary || {
    total_waiting: 0,
    critical_count: 0,
    moderate_count: 0,
    low_count: 0,
    overdue_reassessment: 0,
    avg_wait_min: 0,
  };

  const queue = queueData?.queue || [];

  // Filter urgent "Attention Required" patients
  const attentionPatients = queue.filter(
    p => p.triage_level === 1 || p.is_deteriorating || p.requires_reassessment || (p.confidence_pct && p.confidence_pct < 72)
  );

  return (
    <div className="dashboard-page">
      {/* Top Demo Scenario Bar for Judges */}
      <div className="demo-scenario-toolbar">
        <div className="demo-bar-label">
          <Play size={14} className="text-purple" />
          <span>Demo Controls:</span>
        </div>
        <div className="demo-pills-list">
          <button className="demo-pill-btn" onClick={handleResetDemo} title="Reset demo dataset to baseline">
            🔄 Reset 22 Cases (Normal Mode)
          </button>
          <button className="demo-pill-btn alert-pill" onClick={handleTriggerDeterioration} title="Scenario 15: Drop SpO2 to 88%">
            ⚠ Deterioration Alert
          </button>
          <button className="demo-pill-btn surge-pill" onClick={handleTriggerSurge} title="Scenario 11: 8 incoming ambulance patients">
            🚨 3× Surge Wave
          </button>
          {surgeState.is_surge && (
            <button 
              className="demo-pill-btn" 
              onClick={handleReturnToNormal}
              style={{ background: 'var(--color-stable-bg)', color: 'var(--color-stable)', borderColor: 'var(--color-stable-border)' }}
            >
              ✓ Return to Normal Mode
            </button>
          )}
          <button className="demo-pill-btn" onClick={() => navigate('/new-patient')}>
            ➕ New Patient Intake
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="dashboard-toast">
          <span>{actionMessage}</span>
          <button className="toast-close" onClick={() => setActionMessage('')}>×</button>
        </div>
      )}

      {/* Page Header */}
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Emergency Department Command Center</h1>
          <p className="page-subtitle">Real-time physiological risk monitoring & triage decision support</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadQueue} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* KPI Cards Strip */}
      <div className="grid-kpi mb-6">
        <div className="card kpi-card">
          <div className="kpi-icon-box bg-purple-subtle text-purple"><Users size={20} /></div>
          <div className="kpi-content">
            <span className="kpi-val">{summary.total_waiting}</span>
            <span className="kpi-lbl">Total Waiting</span>
          </div>
        </div>

        <div className="card kpi-card kpi-critical">
          <div className="kpi-icon-box bg-red-subtle text-critical"><ShieldAlert size={20} /></div>
          <div className="kpi-content">
            <span className="kpi-val text-critical">{summary.critical_count}</span>
            <span className="kpi-lbl">Critical (Level 1)</span>
          </div>
        </div>

        <div className="card kpi-card kpi-warning">
          <div className="kpi-icon-box bg-amber-subtle text-warning"><AlertTriangle size={20} /></div>
          <div className="kpi-content">
            <span className="kpi-val text-warning">{summary.overdue_reassessment}</span>
            <span className="kpi-lbl">Reassessment Due</span>
          </div>
        </div>

        <div className="card kpi-card">
          <div className="kpi-icon-box bg-secondary text-secondary"><Clock size={20} /></div>
          <div className="kpi-content">
            <span className="kpi-val">{Math.round(summary.avg_wait_min)} <small className="text-sm">min</small></span>
            <span className="kpi-lbl">Average Wait Time</span>
          </div>
        </div>
      </div>

      {loading && !queueData ? (
        <LoadingState message="Connecting to Emergency Department live queue…" />
      ) : error ? (
        <ErrorState message={error} onRetry={loadQueue} />
      ) : (
        <div className="grid-dashboard">
          {/* Main Left: Attention Required + Queue Table */}
          <div className="dashboard-main-col flex flex-col gap-6">
            {/* Attention Required Section */}
            <div className="dashboard-section">
              <div className="section-header flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <span className="attention-dot" />
                  <h2 className="text-lg font-bold text-primary">Attention Required</h2>
                  <span className="badge badge-critical">{attentionPatients.length}</span>
                </div>
                <span className="text-xs text-muted">Prioritized by clinical severity & deterioration</span>
              </div>

              {attentionPatients.length === 0 ? (
                <div className="card card-body text-sm text-secondary text-center py-4">
                  ✓ All waiting patients currently stable within protocol monitoring limits.
                </div>
              ) : (
                <div className="grid-2">
                  {attentionPatients.slice(0, 4).map((p) => (
                    <PatientCard 
                      key={p.encounter_id} 
                      patient={p} 
                      onReview={handleSelectPatient} 
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Live Queue Preview Section */}
            <div className="dashboard-section">
              <div className="section-header flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <Activity size={18} className="text-purple" />
                  <h2 className="text-lg font-bold text-primary">Live Emergency Queue Preview</h2>
                </div>
                <button className="btn btn-sm btn-secondary" onClick={() => navigate('/queue')}>
                  <span>VIEW FULL QUEUE ({queue.length})</span>
                  <ArrowRight size={14} />
                </button>
              </div>

              <div className="card">
                <PatientTable 
                  queue={queue.slice(0, 6)} 
                  onSelectPatient={handleSelectPatient}
                  compact={false}
                />
              </div>
            </div>
          </div>

          {/* Right Sidebar: AI Operations & Surge Actions */}
          <div className="dashboard-side-col flex flex-col gap-4">
            {/* Surge Mode Recommendation Box if detected */}
            {queueData?.surge_recommended && !surgeState.is_surge && (
              <div className="card card-body surge-prompt-card">
                <div className="flex items-center gap-2 mb-2 text-critical font-bold text-sm">
                  <AlertTriangle size={18} />
                  <span>POSSIBLE SURGE DETECTED</span>
                </div>
                <p className="text-xs text-secondary mb-3">
                  {queueData.surge_reason || 'Queue volume and critical arrivals exceed normal capacity.'}
                </p>
                <button 
                  className="btn btn-critical btn-sm btn-full"
                  onClick={() => navigate('/alerts')}
                >
                  <Zap size={14} />
                  <span>Review Surge Action Center</span>
                </button>
              </div>
            )}

            {/* AI Operations Status Card */}
            <div className="card card-body ai-ops-card">
              <div className="text-xs font-bold text-secondary uppercase tracking-wider mb-3">
                AI Decision Support Operations
              </div>

              <div className="ai-ops-metric-row">
                <span className="text-sm text-secondary">Awaiting Review:</span>
                <span className="badge badge-purple">{queue.filter(p => p.status === 'WAITING').length}</span>
              </div>

              <div className="ai-ops-metric-row">
                <span className="text-sm text-secondary">Low Confidence Cases:</span>
                <span className="badge badge-warning">
                  {queue.filter(p => p.confidence_pct && p.confidence_pct < 72).length}
                </span>
              </div>

              <div className="ai-ops-metric-row">
                <span className="text-sm text-secondary">Deterioration Alerts:</span>
                <span className="badge badge-critical">
                  {queue.filter(p => p.is_deteriorating).length}
                </span>
              </div>

              <div className="divider" />

              <div className="text-xs text-muted">
                🛡 <strong>DPDP Act 2023:</strong> All predictions are audited and require clinician sign-off.
              </div>
            </div>

            {/* Quick Actions Panel */}
            <div className="card card-body">
              <div className="text-xs font-bold text-secondary uppercase tracking-wider mb-3">
                Quick Navigation
              </div>
              <div className="flex flex-col gap-2">
                <button className="btn btn-primary btn-sm btn-full" onClick={() => navigate('/new-patient')}>
                  <span>+ New Patient Intake</span>
                </button>
                <button className="btn btn-secondary btn-sm btn-full" onClick={() => navigate('/queue')}>
                  <span>Live Queue & Dept Filter</span>
                </button>
                <button className="btn btn-secondary btn-sm btn-full" onClick={() => navigate('/alerts')}>
                  <span>Surge & Operational Alerts</span>
                </button>
              </div>
            </div>
          </div>
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
