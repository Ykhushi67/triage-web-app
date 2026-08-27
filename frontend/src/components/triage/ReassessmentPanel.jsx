import React, { useState } from 'react';
import { Activity, AlertTriangle, Check, RefreshCw } from 'lucide-react';
import { reassessPatient } from '../../api/triage';

export default function ReassessmentPanel({ encounterId, patientName, onComplete }) {
  const [temp, setTemp] = useState('');
  const [hr, setHr] = useState('');
  const [bpSys, setBpSys] = useState('');
  const [bpDia, setBpDia] = useState('');
  const [spo2, setSpo2] = useState('');
  const [rr, setRr] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  const handleReassess = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const payload = {
        encounter_id: encounterId,
        vitals: {
          temperature: temp ? parseFloat(temp) : undefined,
          heart_rate: hr ? parseFloat(hr) : undefined,
          bp_systolic: bpSys ? parseFloat(bpSys) : undefined,
          bp_diastolic: bpDia ? parseFloat(bpDia) : undefined,
          spo2: spo2 ? parseFloat(spo2) : undefined,
          respiratory_rate: rr ? parseFloat(rr) : undefined,
        },
        notes: notes || undefined,
      };
      const res = await reassessPatient(payload);
      setResult(res.data);
      if (onComplete) onComplete(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit reassessment.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card card-body">
      <div className="flex items-center gap-2 mb-3">
        <Activity size={18} className="text-purple" />
        <h4 className="text-md font-bold text-primary">Record Reassessment Vitals</h4>
      </div>

      <p className="text-xs text-secondary mb-4">
        Enter updated sequential vital signs for <strong>{patientName || encounterId}</strong> to detect acute physiological changes or deterioration.
      </p>

      {result?.is_deteriorating && (
        <div className="alert-card alert-critical mb-4">
          <AlertTriangle size={18} className="text-critical" />
          <div className="text-sm font-bold text-critical">
            ⚠ ACUTE DETERIORATION DETECTED — Patient escalated to Level 1 Critical.
          </div>
        </div>
      )}

      <form onSubmit={handleReassess} className="flex flex-col gap-3">
        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Heart Rate (bpm)</label>
            <input 
              type="number" 
              className="form-input" 
              placeholder="e.g. 118" 
              value={hr} 
              onChange={(e) => setHr(e.target.value)} 
            />
          </div>
          <div className="form-group">
            <label className="form-label">SpO₂ (%)</label>
            <input 
              type="number" 
              step="0.1" 
              className="form-input" 
              placeholder="e.g. 91.0" 
              value={spo2} 
              onChange={(e) => setSpo2(e.target.value)} 
            />
          </div>
        </div>

        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">BP Systolic (mmHg)</label>
            <input 
              type="number" 
              className="form-input" 
              placeholder="e.g. 135" 
              value={bpSys} 
              onChange={(e) => setBpSys(e.target.value)} 
            />
          </div>
          <div className="form-group">
            <label className="form-label">BP Diastolic (mmHg)</label>
            <input 
              type="number" 
              className="form-input" 
              placeholder="e.g. 85" 
              value={bpDia} 
              onChange={(e) => setBpDia(e.target.value)} 
            />
          </div>
        </div>

        <div className="grid-2">
          <div className="form-group">
            <label className="form-label">Temperature (°C)</label>
            <input 
              type="number" 
              step="0.1" 
              className="form-input" 
              placeholder="e.g. 38.4" 
              value={temp} 
              onChange={(e) => setTemp(e.target.value)} 
            />
          </div>
          <div className="form-group">
            <label className="form-label">Resp Rate (/min)</label>
            <input 
              type="number" 
              className="form-input" 
              placeholder="e.g. 22" 
              value={rr} 
              onChange={(e) => setRr(e.target.value)} 
            />
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Reassessment Clinical Notes</label>
          <textarea 
            className="form-textarea" 
            rows={2} 
            placeholder="Clinical changes observed, treatment response, oxygen administered..." 
            value={notes} 
            onChange={(e) => setNotes(e.target.value)} 
          />
        </div>

        {error && <div className="form-error">{error}</div>}

        <button type="submit" className="btn btn-primary btn-full mt-2" disabled={loading}>
          {loading ? <RefreshCw size={16} className="animate-spin" /> : <Check size={16} />}
          <span>{loading ? 'Analyzing Vitals & Re-evaluating…' : 'Submit Reassessment'}</span>
        </button>
      </form>
    </div>
  );
}
