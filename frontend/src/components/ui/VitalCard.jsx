import React from 'react';
import { Heart, Activity, Thermometer, Wind, Gauge, Flame } from 'lucide-react';
import './VitalCard.css';

export function VitalCard({ label, value, unit, status = 'normal', icon: CustomIcon }) {
  let Icon = Activity;
  if (label.toLowerCase().includes('heart') || label.toLowerCase().includes('pulse')) Icon = Heart;
  else if (label.toLowerCase().includes('spo2') || label.toLowerCase().includes('oxygen')) Icon = Wind;
  else if (label.toLowerCase().includes('temp')) Icon = Thermometer;
  else if (label.toLowerCase().includes('bp') || label.toLowerCase().includes('pressure')) Icon = Gauge;
  else if (label.toLowerCase().includes('pain')) Icon = Flame;

  if (CustomIcon) Icon = CustomIcon;

  return (
    <div className={`vital-card vital-${status}`}>
      <div className="vital-header">
        <span className="vital-icon"><Icon size={16} /></span>
        <span className="vital-label">{label}</span>
      </div>
      <div className="vital-body">
        <span className="vital-val">{value !== undefined && value !== null ? value : '—'}</span>
        {unit && <span className="vital-unit">{unit}</span>}
      </div>
    </div>
  );
}

export function VitalsGrid({ vitals }) {
  if (!vitals) return null;

  const hr = vitals.heart_rate;
  const spo2 = vitals.spo2;
  const temp = vitals.temperature || vitals.temperature_c;
  const bp = vitals.bp_systolic && vitals.bp_diastolic 
    ? `${vitals.bp_systolic}/${vitals.bp_diastolic}` 
    : vitals.blood_pressure_raw;
  const rr = vitals.respiratory_rate;

  const getSpo2Status = (v) => {
    if (!v) return 'normal';
    if (v < 90) return 'critical';
    if (v < 95) return 'warning';
    return 'normal';
  };

  const getHrStatus = (v) => {
    if (!v) return 'normal';
    if (v > 120 || v < 50) return 'critical';
    if (v > 100 || v < 60) return 'warning';
    return 'normal';
  };

  const getTempStatus = (v) => {
    if (!v) return 'normal';
    if (v >= 39.5) return 'critical';
    if (v >= 38.0) return 'warning';
    return 'normal';
  };

  return (
    <div className="vitals-grid">
      <VitalCard label="Heart Rate" value={hr} unit="bpm" status={getHrStatus(hr)} />
      <VitalCard label="SpO₂" value={spo2} unit="%" status={getSpo2Status(spo2)} />
      <VitalCard label="Blood Pressure" value={bp} unit="mmHg" status="normal" />
      <VitalCard label="Temperature" value={temp} unit="°C" status={getTempStatus(temp)} />
      {rr && <VitalCard label="Resp Rate" value={rr} unit="/min" status="normal" />}
    </div>
  );
}
