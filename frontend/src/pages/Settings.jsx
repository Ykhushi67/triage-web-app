import React from 'react';
import { Settings as SettingsIcon, ShieldCheck, Database, Cpu, Wifi } from 'lucide-react';

export default function Settings() {
  return (
    <div className="settings-page">
      <div className="page-header">
        <h1 className="page-title">Station Configuration & System Settings</h1>
        <p className="page-subtitle">Hospital emergency department parameters and clinical decision support thresholds</p>
      </div>

      <div className="flex flex-col gap-6" style={{ maxWidth: '800px' }}>
        <div className="card card-body">
          <h3 className="text-md font-bold text-primary mb-3 flex items-center gap-2">
            <Cpu size={18} className="text-purple" />
            <span>AI Model & Clinical Safety Parameters</span>
          </h3>

          <div className="flex flex-col gap-3 text-sm">
            <div className="flex justify-between py-2 border-bottom">
              <span className="text-secondary">Mandatory Clinician Review Threshold:</span>
              <strong>Confidence &lt; 72%</strong>
            </div>
            <div className="flex justify-between py-2 border-bottom">
              <span className="text-secondary">Hard Safety Floor (SpO₂ Hypoxemia):</span>
              <strong>SpO₂ &lt; 90% ➔ Forced Level 1 Critical (Score ≥ 8.5)</strong>
            </div>
            <div className="flex justify-between py-2 border-bottom">
              <span className="text-secondary">Haemodynamic Shock Index Floor:</span>
              <strong>Shock Index ≥ 1.0 (HR / Systolic BP) ➔ Level 1 (Score ≥ 7.5)</strong>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-secondary">Missing Vital Penalty:</span>
              <strong>-8% Confidence reduction per omitted critical vital</strong>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <h3 className="text-md font-bold text-primary mb-3 flex items-center gap-2">
            <Database size={18} className="text-purple" />
            <span>Operational Reassessment Intervals</span>
          </h3>

          <div className="flex flex-col gap-3 text-sm">
            <div className="flex justify-between py-2 border-bottom">
              <span className="text-secondary">🔴 Level 1 (Critical) Reassessment Protocol:</span>
              <strong>Every 15 minutes</strong>
            </div>
            <div className="flex justify-between py-2 border-bottom">
              <span className="text-secondary">🟡 Level 2 (Moderate) Reassessment Protocol:</span>
              <strong>Every 30 minutes</strong>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-secondary">🟢 Level 3 (Low) Reassessment Protocol:</span>
              <strong>Every 60 minutes</strong>
            </div>
          </div>
        </div>

        <div className="card card-body">
          <h3 className="text-md font-bold text-primary mb-3 flex items-center gap-2">
            <ShieldCheck size={18} className="text-stable" />
            <span>DPDP Act 2023 Compliance Status</span>
          </h3>
          <p className="text-xs text-secondary leading-relaxed">
            Data Minimization: ACTIVE • Role-Based Access Control: ENFORCED • Immutable Audit Logging: ACTIVE • On-Premise Hospital Custody: VERIFIED.
          </p>
        </div>
      </div>
    </div>
  );
}
