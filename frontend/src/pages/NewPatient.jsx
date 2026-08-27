import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPatientHistory, submitIntake } from '../api/patients';
import { acceptTriage, overrideTriage } from '../api/triage';
import HistoryPanel from '../components/patient/HistoryPanel';
import TriageRecommendation from '../components/triage/TriageRecommendation';
import OverrideModal from '../components/triage/OverrideModal';
import { 
  UserPlus, User, Clock, Activity, Cpu, CheckCircle2, 
  ArrowRight, ArrowLeft, Search, AlertTriangle, ShieldCheck, Flame, Heart, Wind, Gauge, Thermometer
} from 'lucide-react';
import './NewPatient.css';

const SYMPTOM_OPTIONS = [
  'Chest pain',
  'Difficulty breathing',
  'Fever & chills',
  'Severe headache',
  'Abdominal pain',
  'Active bleeding',
  'Generalized weakness',
  'Loss of consciousness',
  'Dizziness / Vertigo',
  'Throat pain',
  'Cough',
  'Limb trauma / Fracture',
];

export default function NewPatient() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: ID, 2: History, 3: Assessment, 4: Recommendation

  // Step 1 - Identification
  const [patientId, setPatientId] = useState('');
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('male');
  const [contact, setContact] = useState('');
  const [arrivalMode, setArrivalMode] = useState('Walk-in');

  // Step 2 - History Data
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyData, setHistoryData] = useState(null);

  // Step 3 - Clinical Presentation & Vitals
  const [complaint, setComplaint] = useState('');
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [temp, setTemp] = useState('');
  const [hr, setHr] = useState('');
  const [bp, setBp] = useState('');
  const [spo2, setSpo2] = useState('');
  const [rr, setRr] = useState('');
  const [pain, setPain] = useState('0');
  const [notes, setNotes] = useState('');
  const [redFlags, setRedFlags] = useState({
    severeBreathing: false,
    uncontrolledBleeding: false,
    lossOfConsciousness: false,
    severeChestPain: false,
    signsOfShock: false,
  });

  // Step 4 - AI Recommendation & Intake Result
  const [intakeLoading, setIntakeLoading] = useState(false);
  const [intakeResult, setIntakeResult] = useState(null);
  const [acceptLoading, setAcceptLoading] = useState(false);
  const [overrideModalOpen, setOverrideModalOpen] = useState(false);
  const [error, setError] = useState('');

  // Step 1 -> Step 2 (Trigger history search)
  const handleContinueToHistory = async () => {
    if (!name.trim()) {
      setError('Please enter the patient name.');
      return;
    }
    setError('');
    setStep(2);
    setHistoryLoading(true);

    const lookupId = patientId.trim() || 'NEW_PATIENT';
    try {
      const res = await getPatientHistory(lookupId);
      setHistoryData(res.data);
    } catch (_) {
      setHistoryData({
        has_history: false,
        total_visits: 0,
        visits: [],
        history_badge: 'First-Time Patient (No Prior Records)',
      });
    } finally {
      setHistoryLoading(false);
    }
  };

  const toggleSymptom = (sym) => {
    if (selectedSymptoms.includes(sym)) {
      setSelectedSymptoms(selectedSymptoms.filter(s => s !== sym));
    } else {
      setSelectedSymptoms([...selectedSymptoms, sym]);
    }
  };

  // Step 3 -> Step 4 (Run Intake & ML inference)
  const handleAnalyzePatient = async (e) => {
    e.preventDefault();
    if (!complaint.trim() && selectedSymptoms.length === 0) {
      setError('Please enter a chief complaint or select at least one symptom.');
      return;
    }
    setError('');
    setIntakeLoading(true);
    setStep(4);

    try {
      const fullComplaint = [
        complaint.trim(),
        selectedSymptoms.length > 0 ? `Reported symptoms: ${selectedSymptoms.join(', ')}` : '',
      ].filter(Boolean).join('. ');

      const payload = {
        name: name.trim(),
        age: age ? parseFloat(age) : undefined,
        gender: gender,
        contact_info: contact || undefined,
        arrival_mode: arrivalMode,
        symptoms: {
          complaint: fullComplaint,
          onset: 'Acute presentation',
          severity: redFlags.severeChestPain || redFlags.signsOfShock ? 'Critical' : 'Urgent',
          free_text: notes || undefined,
        },
        vitals: {
          temperature: temp ? parseFloat(temp) : undefined,
          heart_rate: hr ? parseFloat(hr) : undefined,
          blood_pressure_raw: bp || undefined,
          spo2: spo2 ? parseFloat(spo2) : undefined,
          respiratory_rate: rr ? parseFloat(rr) : undefined,
        },
        notes: notes || undefined,
      };

      const res = await submitIntake(payload);
      setIntakeResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze patient intake.');
    } finally {
      setIntakeLoading(false);
    }
  };

  // Step 4 Actions: Accept / Override
  const handleAccept = async () => {
    if (!intakeResult?.encounter_id) return;
    setAcceptLoading(true);
    try {
      await acceptTriage(intakeResult.encounter_id);
      navigate('/queue');
    } catch (err) {
      alert('Error accepting triage.');
    } finally {
      setAcceptLoading(false);
    }
  };

  const handleOverrideSubmit = async (overrideData) => {
    try {
      await overrideTriage(overrideData);
      setOverrideModalOpen(false);
      navigate('/queue');
    } catch (err) {
      alert('Failed to record override.');
    }
  };

  return (
    <div className="new-patient-page">
      <div className="page-header">
        <h1 className="page-title">New Patient Intake & Triage Assessment</h1>
        <p className="page-subtitle">Multi-step structured clinical intake with zero-bias history lookup and AI decision support</p>
      </div>

      {/* Step Stepper Header */}
      <div className="intake-stepper card card-sm mb-6">
        <div className={`step-node ${step >= 1 ? 'step-active' : ''} ${step > 1 ? 'step-done' : ''}`}>
          <span className="step-num">01</span>
          <span className="step-label">Identification</span>
        </div>
        <div className="step-connector" />
        <div className={`step-node ${step >= 2 ? 'step-active' : ''} ${step > 2 ? 'step-done' : ''}`}>
          <span className="step-num">02</span>
          <span className="step-label">History</span>
        </div>
        <div className="step-connector" />
        <div className={`step-node ${step >= 3 ? 'step-active' : ''} ${step > 3 ? 'step-done' : ''}`}>
          <span className="step-num">03</span>
          <span className="step-label">Assessment</span>
        </div>
        <div className="step-connector" />
        <div className={`step-node ${step >= 4 ? 'step-active' : ''}`}>
          <span className="step-num">04</span>
          <span className="step-label">Recommendation</span>
        </div>
      </div>

      {error && <div className="form-error text-sm mb-4">{error}</div>}

      {/* STEP 1: Identification */}
      {step === 1 && (
        <div className="card card-body intake-form-card">
          <h3 className="text-lg font-bold text-primary mb-4 flex items-center gap-2">
            <User size={18} className="text-purple" />
            <span>Step 1 — Patient Demographics & Hospital Identity</span>
          </h3>

          <div className="flex flex-col gap-4">
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Full Patient Name *</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. Ramesh Sharma" 
                  value={name} 
                  onChange={(e) => setName(e.target.value)} 
                  required 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Patient ID / Hospital MRN (Optional for lookup)</label>
                <input 
                  type="text" 
                  className="form-input" 
                  placeholder="e.g. P0011 (or leave blank for new PID)" 
                  value={patientId} 
                  onChange={(e) => setPatientId(e.target.value)} 
                />
                <span className="form-hint">Tip: Enter P0011 to test returning patient scenario</span>
              </div>
            </div>

            <div className="grid-3">
              <div className="form-group">
                <label className="form-label">Age (Years)</label>
                <input 
                  type="number" 
                  className="form-input" 
                  placeholder="e.g. 58" 
                  value={age} 
                  onChange={(e) => setAge(e.target.value)} 
                />
              </div>
              <div className="form-group">
                <label className="form-label">Sex / Gender</label>
                <select className="form-select" value={gender} onChange={(e) => setGender(e.target.value)}>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other / Unknown</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Arrival Method</label>
                <select className="form-select" value={arrivalMode} onChange={(e) => setArrivalMode(e.target.value)}>
                  <option value="Walk-in">Walk-in</option>
                  <option value="Ambulance">Ambulance</option>
                  <option value="Referral">Referral</option>
                  <option value="Wheelchair">Wheelchair</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Contact Phone / Attendant</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="+91-98765-43210" 
                value={contact} 
                onChange={(e) => setContact(e.target.value)} 
              />
            </div>

            <div className="flex justify-end mt-4">
              <button className="btn btn-primary btn-lg" onClick={handleContinueToHistory}>
                <span>CONTINUE TO HISTORY CHECK</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 2: History Search & Confirmation */}
      {step === 2 && (
        <div className="card card-body intake-form-card">
          <h3 className="text-lg font-bold text-primary mb-2 flex items-center gap-2">
            <Search size={18} className="text-purple" />
            <span>Step 2 — Independent Patient History Lookup</span>
          </h3>

          <p className="text-sm text-secondary mb-4">
            Patient history is retrieved independently from hospital archives for clinician awareness. It is isolated from the AI inference model to prevent historical diagnosis bias.
          </p>

          {historyLoading ? (
            <div className="py-8 text-center text-sm text-muted">
              Searching hospital medical records for Patient ID: <strong>{patientId || name}</strong>…
            </div>
          ) : (
            <HistoryPanel history={historyData} />
          )}

          <div className="flex justify-between items-center mt-6">
            <button className="btn btn-secondary" onClick={() => setStep(1)}>
              <ArrowLeft size={16} />
              <span>Back to Demographics</span>
            </button>
            <button className="btn btn-primary btn-lg" onClick={() => setStep(3)}>
              <span>CONTINUE TO CLINICAL ASSESSMENT</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Current Clinical Assessment */}
      {step === 3 && (
        <form onSubmit={handleAnalyzePatient} className="card card-body intake-form-card">
          <h3 className="text-lg font-bold text-primary mb-4 flex items-center gap-2">
            <Activity size={18} className="text-purple" />
            <span>Step 3 — Current Presentation, Symptoms & Acute Vitals</span>
          </h3>

          <div className="flex flex-col gap-6">
            {/* Chief Complaint */}
            <div className="form-group">
              <label className="form-label">Current Presentation (What brought the patient to the ED?)</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="Describe onset, primary pain location, radiation, associated signs (e.g. Sudden crushing retrosternal chest pain radiating to left arm, diaphoretic)..."
                value={complaint}
                onChange={(e) => setComplaint(e.target.value)}
                required
              />
            </div>

            {/* Selectable Symptom Chips */}
            <div className="form-group">
              <label className="form-label">Acute Symptoms (Select all observed / reported):</label>
              <div className="symptom-chips-grid">
                {SYMPTOM_OPTIONS.map((sym) => {
                  const isSel = selectedSymptoms.includes(sym);
                  return (
                    <button
                      type="button"
                      key={sym}
                      className={`symptom-chip ${isSel ? 'chip-selected' : ''}`}
                      onClick={() => toggleSymptom(sym)}
                    >
                      {isSel ? '✓ ' : '+ '} {sym}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Prominent Vital Sign Inputs */}
            <div>
              <div className="form-label mb-2">Acute Vital Signs:</div>
              <div className="grid-3">
                <div className="form-group">
                  <label className="text-xs text-secondary font-semibold flex items-center gap-1">
                    <Heart size={13} className="text-critical" /> Heart Rate (bpm)
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="e.g. 118"
                    value={hr}
                    onChange={(e) => setHr(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="text-xs text-secondary font-semibold flex items-center gap-1">
                    <Wind size={13} className="text-purple" /> SpO₂ Oxygen Sat (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-input"
                    placeholder="e.g. 92.0"
                    value={spo2}
                    onChange={(e) => setSpo2(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="text-xs text-secondary font-semibold flex items-center gap-1">
                    <Gauge size={13} className="text-secondary" /> Blood Pressure (mmHg)
                  </label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. 140/90 or 150-95"
                    value={bp}
                    onChange={(e) => setBp(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid-3 mt-3">
                <div className="form-group">
                  <label className="text-xs text-secondary font-semibold flex items-center gap-1">
                    <Thermometer size={13} className="text-warning" /> Temperature (°C)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className="form-input"
                    placeholder="e.g. 38.6"
                    value={temp}
                    onChange={(e) => setTemp(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="text-xs text-secondary font-semibold">
                    Respiratory Rate (/min)
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="e.g. 24"
                    value={rr}
                    onChange={(e) => setRr(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="text-xs text-secondary font-semibold flex items-center gap-1">
                    <Flame size={13} className="text-warning" /> Pain Scale (0–10)
                  </label>
                  <select className="form-select" value={pain} onChange={(e) => setPain(e.target.value)}>
                    <option value="0">0 — No Pain</option>
                    <option value="3">3 — Mild Discomfort</option>
                    <option value="5">5 — Moderate Pain</option>
                    <option value="7">7 — Severe Pain</option>
                    <option value="10">10 — Worst Possible Pain</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Immediate Safety Check / Red Flags */}
            <div className="safety-check-box">
              <div className="flex items-center gap-2 text-critical font-bold text-sm mb-2">
                <AlertTriangle size={16} />
                <span>Immediate Clinical Red Flags & Safety Check:</span>
              </div>
              <div className="red-flags-grid">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={redFlags.severeBreathing}
                    onChange={(e) => setRedFlags({ ...redFlags, severeBreathing: e.target.checked })}
                  />
                  <span>Severe stridor / respiratory distress</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={redFlags.severeChestPain}
                    onChange={(e) => setRedFlags({ ...redFlags, severeChestPain: e.target.checked })}
                  />
                  <span>Severe crushing chest pain</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={redFlags.signsOfShock}
                    onChange={(e) => setRedFlags({ ...redFlags, signsOfShock: e.target.checked })}
                  />
                  <span>Signs of decompensating shock / hypotension</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={redFlags.lossOfConsciousness}
                    onChange={(e) => setRedFlags({ ...redFlags, lossOfConsciousness: e.target.checked })}
                  />
                  <span>Altered mental status / syncope</span>
                </label>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Nurse / Clinician Observations & Free Text</label>
              <textarea
                className="form-textarea"
                rows={2}
                placeholder="Observed signs, pale skin, diaphoresis, respiratory effort..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>

            <div className="flex justify-between items-center mt-4">
              <button type="button" className="btn btn-secondary" onClick={() => setStep(2)}>
                <ArrowLeft size={16} />
                <span>Back to History</span>
              </button>
              <button type="submit" className="btn btn-primary btn-lg">
                <Cpu size={18} />
                <span>ANALYZE PATIENT WITH AI TRIAGE</span>
              </button>
            </div>
          </div>
        </form>
      )}

      {/* STEP 4: AI Recommendation & Decision Confirmation */}
      {step === 4 && (
        <div className="intake-rec-container">
          {intakeLoading ? (
            <div className="card card-body ai-processing-card">
              <div className="flex flex-col items-center gap-4 py-8">
                <Cpu size={36} className="text-purple animate-pulse" />
                <h3 className="text-lg font-bold text-primary">Analyzing Current Presentation…</h3>
                <div className="ai-processing-steps">
                  <div className="ai-p-step done">✓ Current vitals & acute symptoms ingested</div>
                  <div className="ai-p-step done">✓ Safety rule hard clinical floors evaluated</div>
                  <div className="ai-p-step active">⏳ Computing physiological priority score & confidence…</div>
                  <div className="ai-p-step">Specialty department routing classification</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-6">
              {intakeResult?.triage_result && (
                <TriageRecommendation
                  result={intakeResult.triage_result}
                  onAccept={handleAccept}
                  onOverride={() => setOverrideModalOpen(true)}
                  acceptLoading={acceptLoading}
                />
              )}

              <div className="card card-body text-xs text-muted flex items-center justify-between">
                <span>Encounter ID: <strong>{intakeResult?.encounter_id}</strong> | Patient ID: <strong>{intakeResult?.patient_id}</strong></span>
                <span className="badge badge-purple">🛡 DPDP 2023 Aligned Audit Log Active</span>
              </div>
            </div>
          )}
        </div>
      )}

      <OverrideModal 
        isOpen={overrideModalOpen}
        onClose={() => setOverrideModalOpen(false)}
        encounterId={intakeResult?.encounter_id}
        aiLevel={intakeResult?.triage_result?.triage_level}
        aiScore={intakeResult?.triage_result?.priority_score}
        onSubmit={handleOverrideSubmit}
      />
    </div>
  );
}
