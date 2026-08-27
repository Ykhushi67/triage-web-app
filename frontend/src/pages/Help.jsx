import React from 'react';
import { HelpCircle, Play, ShieldAlert, Cpu, Activity, UserCheck } from 'lucide-react';

export default function Help() {
  return (
    <div className="help-page" style={{ maxWidth: '840px' }}>
      <div className="page-header">
        <h1 className="page-title">Help & Demonstration Guide</h1>
        <p className="page-subtitle">Interactive walkthrough for clinicians and hackathon judges</p>
      </div>

      <div className="flex flex-col gap-6">
        <div className="card card-body">
          <h3 className="text-md font-bold text-primary mb-2 flex items-center gap-2">
            <Play size={18} className="text-purple" />
            <span>How to Demonstrate the Core Value Proposition in 60 Seconds</span>
          </h3>

          <ol className="flex flex-col gap-3 text-sm text-secondary pl-4" style={{ listStyleType: 'decimal' }}>
            <li>
              <strong>1. Review Main Dashboard:</strong> Observe the live waiting queue sorted by clinical severity (Priority Score descending) and wait time.
            </li>
            <li>
              <strong>2. Test Returning Patient vs First-Time:</strong> Click <em>New Patient</em>, enter <code>P0011</code> (Ramesh Sharma) ➔ Step 2 instantly renders the rich past visit history card with zero ML bias.
            </li>
            <li>
              <strong>3. Test AI Triage & Safety Floors:</strong> Enter SpO₂ = 88% ➔ AI recommendation automatically enforces hard clinical floor (Level 1 Critical + Emergency routing).
            </li>
            <li>
              <strong>4. Test Clinician Override:</strong> Click <em>Override Recommendation</em> ➔ Select Level 1 with mandatory reason <code>PATIENT_CLINICALLY_WORSE</code> ➔ Queue dynamically updates with doctor's final decision.
            </li>
            <li>
              <strong>5. Trigger Deterioration Alert:</strong> On dashboard top toolbar, click <em>⚠ Deterioration Alert</em> ➔ Observe real-time red banner and patient escalation.
            </li>
            <li>
              <strong>6. Trigger 3× Surge Wave:</strong> Click <em>🚨 3× Surge Wave</em> ➔ Auto-surge recommendation triggers with prioritized action columns.
            </li>
            <li>
              <strong>7. Inspect Immutable Audit Trail:</strong> Go to <em>Audit Log</em> ➔ Verify every AI and clinician action is logged with pseudonymous IDs.
            </li>
          </ol>
        </div>

        <div className="card card-body">
          <h3 className="text-md font-bold text-primary mb-2 flex items-center gap-2">
            <ShieldAlert size={18} className="text-critical" />
            <span>Clinical Disclaimer</span>
          </h3>
          <p className="text-xs text-secondary leading-relaxed">
            PatientTriage.ai is a clinical decision-support prototype. It does not replace medical judgment. All automated suggestions must be validated by licensed clinicians.
          </p>
        </div>
      </div>
    </div>
  );
}
