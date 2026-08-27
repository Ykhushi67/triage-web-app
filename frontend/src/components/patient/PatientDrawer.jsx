import React, { useState, useEffect } from 'react';
import { X, Clock, User, Building, ShieldAlert, Activity, History, ClipboardList, CheckCircle, ChevronRight } from 'lucide-react';
import { PriorityBadge, StatusBadge } from '../ui/Badges';
import ConfidenceIndicator from '../ui/ConfidenceIndicator';
import HistoryPanel from './HistoryPanel';
import Timeline from './Timeline';
import ReassessmentPanel from '../triage/ReassessmentPanel';
import OverrideModal from '../triage/OverrideModal';
import { getPatientHistory } from '../../api/patients';
import { getPatientTimeline } from '../../api/audit';
import { acceptTriage, overrideTriage } from '../../api/triage';
import { completeEncounter } from '../../api/queue';
import './PatientDrawer.css';

export default function PatientDrawer({ patient, isOpen, onClose, onRefreshQueue }) {
  if (!isOpen || !patient) return null;

  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'history' | 'reassess' | 'timeline'
  const [historyData, setHistoryData] = useState(null);
  const [timelineData, setTimelineData] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [overrideModalOpen, setOverrideModalOpen] = useState(false);
  const [overrideLoading, setOverrideLoading] = useState(false);
  const [message, setMessage] = useState('');

  const {
    encounter_id,
    patient_id,
    patient_name,
    age,
    sex,
    triage_level,
    triage_label,
    priority_score,
    department,
    chief_complaint,
    arrival_mode,
    waiting_minutes,
    confidence_pct,
    safety_flags = [],
    is_deteriorating,
    requires_reassessment,
    is_overridden,
  } = patient;

  useEffect(() => {
    if (patient_id) {
      setLoadingHistory(true);
      getPatientHistory(patient_id)
        .then(res => setHistoryData(res.data))
        .catch(() => setHistoryData(null))
        .finally(() => setLoadingHistory(false));

      setLoadingTimeline(true);
      getPatientTimeline(patient_id)
        .then(res => setTimelineData(res.data))
        .catch(() => setTimelineData([]))
        .finally(() => setLoadingTimeline(false));
    }
  }, [patient_id, encounter_id]);

  const handleAccept = async () => {
    setAccepting(true);
    setMessage('');
    try {
      await acceptTriage(encounter_id);
      setMessage('✓ AI triage recommendation accepted by clinician.');
      if (onRefreshQueue) onRefreshQueue();
    } catch (err) {
      setMessage('Error accepting triage.');
    } finally {
      setAccepting(false);
    }
  };

  const handleOverrideSubmit = async (overrideData) => {
    setOverrideLoading(true);
    try {
      await overrideTriage(overrideData);
      setOverrideModalOpen(false);
      setMessage('✓ Clinician override successfully recorded and applied to queue.');
      if (onRefreshQueue) onRefreshQueue();
    } catch (err) {
      alert('Failed to record override.');
    } finally {
      setOverrideLoading(false);
    }
  };

  const handleComplete = async () => {
    if (!window.confirm('Discharge / mark encounter as completed?')) return;
    setCompleting(true);
    try {
      await completeEncounter(encounter_id);
      onClose();
      if (onRefreshQueue) onRefreshQueue();
    } catch (err) {
      alert('Failed to complete encounter.');
    } finally {
      setCompleting(false);
    }
  };

  return (
    <>
      <div className="drawer-overlay" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-header">
          <div className="drawer-title-col">
            <div className="flex items-center gap-2">
              <PriorityBadge level={triage_level} label={triage_label} />
              <span className="text-xs text-muted">ID: {patient_id}</span>
            </div>
            <h3 className="drawer-patient-name">{patient_name}</h3>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={onClose}><X size={18} /></button>
        </div>

        {/* Tab Strip */}
        <div className="drawer-tabs">
          <button 
            className={`drawer-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button 
            className={`drawer-tab ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            History {historyData?.has_history && <span className="tab-dot" />}
          </button>
          <button 
            className={`drawer-tab ${activeTab === 'reassess' ? 'active' : ''}`}
            onClick={() => setActiveTab('reassess')}
          >
            Reassess
          </button>
        </div>

        <div className="drawer-body">
          {message && (
            <div className="drawer-alert-banner">
              {message}
            </div>
          )}

          {activeTab === 'overview' && (
            <div className="flex flex-col gap-4">
              {/* Critical Alert Flag */}
              {is_deteriorating && (
                <div className="alert-card alert-critical">
                  <ShieldAlert size={18} className="text-critical" />
                  <div className="text-sm font-bold text-critical">
                    ⚠ ACUTE DETERIORATION DETECTED — Urgent bedside evaluation required!
                  </div>
                </div>
              )}

              {/* Patient Core Meta */}
              <div className="drawer-info-grid">
                <div className="info-box">
                  <span className="info-lbl">Age / Sex</span>
                  <span className="info-val">{age ? `${age} yrs` : '—'} / {sex || '—'}</span>
                </div>
                <div className="info-box">
                  <span className="info-lbl">Arrival Method</span>
                  <span className="info-val">{arrival_mode || 'Walk-in'}</span>
                </div>
                <div className="info-box">
                  <span className="info-lbl">Wait Time</span>
                  <span className="info-val">{waiting_minutes} mins</span>
                </div>
                <div className="info-box">
                  <span className="info-lbl">Assigned Dept</span>
                  <span className="info-val">{department || 'General Medicine'}</span>
                </div>
              </div>

              {/* Chief Complaint */}
              <div className="drawer-section">
                <div className="section-title">Chief Complaint & Clinical Presentation</div>
                <div className="complaint-quote">
                  "{chief_complaint || 'No complaint notes recorded.'}"
                </div>
              </div>

              {/* AI Triage Recommendation Details */}
              <div className="drawer-section">
                <div className="section-title">AI Decision Support Assessment</div>
                <div className="ai-rec-box">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-bold text-primary">Triage Priority Score</span>
                    <span className="text-xl font-extrabold text-primary">{priority_score?.toFixed(1)} / 10</span>
                  </div>
                  <ConfidenceIndicator 
                    confidencePct={confidence_pct}
                    missingCount={0}
                  />
                  {safety_flags && safety_flags.length > 0 && (
                    <div className="mt-2 text-xs text-critical">
                      <strong>Safety Flags:</strong> {safety_flags.join(', ')}
                    </div>
                  )}
                </div>
              </div>

              {/* Clinician Decision Buttons */}
              <div className="drawer-actions-block">
                <div className="text-xs text-secondary font-semibold uppercase mb-2">Clinician Action:</div>
                <div className="flex gap-2">
                  <button 
                    className="btn btn-success btn-full" 
                    onClick={handleAccept}
                    disabled={accepting}
                  >
                    <CheckCircle size={15} />
                    <span>{accepting ? 'Accepting…' : 'Accept AI Triage'}</span>
                  </button>
                  <button 
                    className="btn btn-warning btn-full"
                    onClick={() => setOverrideModalOpen(true)}
                  >
                    <span>Override Score</span>
                  </button>
                </div>
                <button 
                  className="btn btn-secondary btn-sm btn-full mt-2"
                  onClick={handleComplete}
                  disabled={completing}
                >
                  {completing ? 'Completing…' : 'Discharge / Complete Encounter'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="flex flex-col gap-3">
              {loadingHistory ? (
                <div className="text-sm text-muted">Searching hospital records…</div>
              ) : (
                <HistoryPanel history={historyData} />
              )}
            </div>
          )}

          {activeTab === 'reassess' && (
            <ReassessmentPanel 
              encounterId={encounter_id} 
              patientName={patient_name}
              onComplete={() => {
                if (onRefreshQueue) onRefreshQueue();
              }}
            />
          )}
        </div>
      </aside>

      <OverrideModal 
        isOpen={overrideModalOpen}
        onClose={() => setOverrideModalOpen(false)}
        encounterId={encounter_id}
        aiLevel={triage_level}
        aiScore={priority_score}
        onSubmit={handleOverrideSubmit}
        loading={overrideLoading}
      />
    </>
  );
}
