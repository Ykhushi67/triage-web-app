import React, { useState, useEffect } from 'react';
import { useSurge } from '../context/SurgeContext';
import { getLiveQueue } from '../api/queue';
import { getSurgeStatus, activateSurge, deactivateSurge } from '../api/surge';
import { AlertCard } from '../components/ui/AlertCard';
import PatientDrawer from '../components/patient/PatientDrawer';
import SurgeActivationModal from '../components/surge/SurgeActivationModal';
import { 
  Bell, AlertTriangle, Zap, Clock, ShieldAlert, 
  TrendingDown, CheckCircle2, RefreshCw, ArrowRight 
} from 'lucide-react';
import './Alerts.css';

export default function Alerts() {
  const { surgeState, refresh: refreshSurge } = useSurge();
  const [queueData, setQueueData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activationModalOpen, setActivationModalOpen] = useState(false);
  const [deactivating, setDeactivating] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const qRes = await getLiveQueue();
      setQueueData(qRes.data);
      await refreshSurge();
    } catch (_) {}
    finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, []);

  const queue = queueData?.queue || [];

  // Column 1: Immediate Review Required (Unconfirmed intakes / low confidence cases < 72%)
  const reviewRequired = queue.filter(
    p => p.status === 'WAITING' || (p.confidence_pct && p.confidence_pct < 72)
  );

  // Column 2: Acute Deterioration Alerts
  const deterioratingPatients = queue.filter(p => p.is_deteriorating);

  // Column 3: Overdue Reassessments
  const overdueReassessments = queue.filter(p => p.requires_reassessment);

  const handleOpenPatient = (p) => {
    setSelectedPatient(p);
    setDrawerOpen(true);
  };

  const handleDeactivateSurge = async () => {
    setDeactivating(true);
    try {
      await deactivateSurge({ reason: 'Manual return to normal load' });
      await loadData();
    } catch (_) {}
    finally {
      setDeactivating(false);
    }
  };

  return (
    <div className="alerts-page">
      <div className="page-header flex justify-between items-center">
        <div>
          <h1 className="page-title">Surge Operations & Action Center</h1>
          <p className="page-subtitle">What requires clinical attention right now in the emergency station</p>
        </div>
        <div className="flex gap-2">
          {surgeState.is_surge ? (
            <button 
              className="btn btn-secondary btn-sm"
              onClick={handleDeactivateSurge}
              disabled={deactivating}
            >
              <span>{deactivating ? 'Deactivating…' : 'Return to Normal Mode'}</span>
            </button>
          ) : (
            <button 
              className="btn btn-critical btn-sm"
              onClick={() => setActivationModalOpen(true)}
            >
              <Zap size={14} />
              <span>Activate Surge Mode</span>
            </button>
          )}
          <button className="btn btn-secondary btn-sm" onClick={loadData} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Surge Status Banner */}
      {surgeState.is_surge ? (
        <div className="surge-operational-banner">
          <div className="flex items-center gap-3">
            <div className="surge-banner-pulse-dot" />
            <div>
              <div className="text-md font-bold text-critical">SURGE MODE ACTIVE (Emergency Department Influx)</div>
              <div className="text-xs text-secondary mt-1">
                Reason: <strong>{surgeState.surge_reason || 'Mass casualty / High arrival rate'}</strong> | 
                Capacity: {surgeState.queue_size} waiting, {surgeState.critical_count} critical, avg wait {Math.round(surgeState.avg_wait_min)}m
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="normal-operational-banner">
          <div className="flex items-center gap-2 text-stable font-semibold text-sm">
            <CheckCircle2 size={16} />
            <span>Operating in NORMAL MODE — Automated surge detection monitoring active</span>
          </div>
        </div>
      )}

      {/* 3 Operational Action Columns */}
      <div className="grid-3 mt-6">
        {/* Column 1: Immediate Review Required */}
        <div className="card action-column">
          <div className="card-header bg-purple-subtle">
            <div className="flex items-center gap-2">
              <ShieldAlert size={18} className="text-purple" />
              <span className="font-bold text-sm text-primary">1. Immediate Review Required</span>
            </div>
            <span className="badge badge-purple">{reviewRequired.length}</span>
          </div>
          <div className="card-body action-column-body">
            {reviewRequired.length === 0 ? (
              <div className="text-xs text-muted text-center py-8">
                ✓ No unconfirmed intakes or low-confidence cases.
              </div>
            ) : (
              reviewRequired.map((p) => (
                <AlertCard
                  key={p.encounter_id}
                  type="LOW_CONFIDENCE"
                  title={p.patient_name}
                  subtitle={`ID: ${p.patient_id} • Score: ${p.priority_score}/10 (${p.confidence_pct || 0}% Conf)`}
                  details={p.chief_complaint}
                  actionLabel="REVIEW NOW"
                  onAction={() => handleOpenPatient(p)}
                />
              ))
            )}
          </div>
        </div>

        {/* Column 2: Acute Deterioration Alerts */}
        <div className="card action-column col-critical">
          <div className="card-header bg-red-subtle">
            <div className="flex items-center gap-2">
              <TrendingDown size={18} className="text-critical" />
              <span className="font-bold text-sm text-critical">2. Acute Deterioration Alerts</span>
            </div>
            <span className="badge badge-critical">{deterioratingPatients.length}</span>
          </div>
          <div className="card-body action-column-body">
            {deterioratingPatients.length === 0 ? (
              <div className="text-xs text-muted text-center py-8">
                ✓ No acute vital deteriorations detected.
              </div>
            ) : (
              deterioratingPatients.map((p) => (
                <AlertCard
                  key={p.encounter_id}
                  type="DETERIORATING"
                  title={`⚠ ${p.patient_name}`}
                  subtitle={`ID: ${p.patient_id} • SpO₂ / HR Acute Delta`}
                  details="Sequential vitals indicate worsening hypoxia or haemodynamic instability."
                  actionLabel="ESCALATE BED"
                  onAction={() => handleOpenPatient(p)}
                />
              ))
            )}
          </div>
        </div>

        {/* Column 3: Overdue Reassessments */}
        <div className="card action-column col-warning">
          <div className="card-header bg-amber-subtle">
            <div className="flex items-center gap-2">
              <Clock size={18} className="text-warning" />
              <span className="font-bold text-sm text-primary">3. Overdue Reassessments</span>
            </div>
            <span className="badge badge-moderate">{overdueReassessments.length}</span>
          </div>
          <div className="card-body action-column-body">
            {overdueReassessments.length === 0 ? (
              <div className="text-xs text-muted text-center py-8">
                ✓ All patients within protocol reassessment limits.
              </div>
            ) : (
              overdueReassessments.map((p) => (
                <AlertCard
                  key={p.encounter_id}
                  type="REASSESSMENT"
                  title={p.patient_name}
                  subtitle={`Waiting ${p.waiting_minutes}m • Due Threshold Exceeded`}
                  details="Protocol mandates timely re-check of vitals for active queue safety."
                  actionLabel="REASSESS VITALS"
                  onAction={() => handleOpenPatient(p)}
                />
              ))
            )}
          </div>
        </div>
      </div>

      <SurgeActivationModal
        isOpen={activationModalOpen}
        onClose={() => setActivationModalOpen(false)}
      />

      <PatientDrawer
        patient={selectedPatient}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onRefreshQueue={loadData}
      />
    </div>
  );
}
