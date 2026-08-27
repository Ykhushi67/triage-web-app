import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Zap, ShieldCheck, ArrowRight, Activity, Cpu, Stethoscope, Users } from 'lucide-react';
import './Login.css';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('doctor@hospital.org');
  const [password, setPassword] = useState('doctor123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (roleEmail, rolePass) => {
    setEmail(roleEmail);
    setPassword(rolePass);
  };

  return (
    <div className="login-container">
      {/* Left Branding & Workflow */}
      <div className="login-hero">
        <div className="login-hero-brand">
          <div className="login-logo-box">
            <Zap size={24} fill="currentColor" />
          </div>
          <span className="login-brand-title">PatientTriage.ai</span>
        </div>

        <h1 className="login-hero-heading">
          Intelligent triage support for emergency care.
        </h1>

        <p className="login-hero-desc">
          Objective physiological risk assessment with explicit uncertainty indicators, real-time vital deterioration tracking, and human-in-the-loop clinical governance.
        </p>

        <div className="login-safety-statement">
          <ShieldCheck size={16} />
          <span>
            <strong>Safety-First Principle:</strong> AI recommendations are decision-support only. Clinical decisions remain with authorized medical staff. Aligned with DPDP Act 2023.
          </span>
        </div>
      </div>

      {/* Right Login Form */}
      <div className="login-form-panel">
        <div className="login-card card card-body">
          <div className="login-form-header">
            <h2 className="login-form-title">Hospital Staff Sign In</h2>
            <p className="text-sm text-secondary">
              Access the clinical triage and emergency queue system.
            </p>
          </div>

          {error && <div className="form-error text-sm mb-3">{error}</div>}

          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <div className="form-group">
              <label className="form-label">Staff Email / Hospital ID</label>
              <input
                type="email"
                className="form-input"
                placeholder="doctor@hospital.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={loading}>
              <span>{loading ? 'Authenticating…' : 'Sign In to Station'}</span>
              <ArrowRight size={16} />
            </button>
          </form>

          <div className="divider" />

          {/* Quick Demo Credentials for Judges */}
          <div className="demo-credentials-box">
            <div className="text-xs font-semibold text-secondary uppercase mb-2">
              Demo Environment Roles (One-Click):
            </div>
            <div className="demo-role-buttons">
              <button 
                type="button" 
                className="btn btn-sm btn-secondary"
                onClick={() => handleQuickLogin('doctor@hospital.org', 'doctor123')}
              >
                <Stethoscope size={13} />
                <span>Dr. Rajesh (Doctor)</span>
              </button>
              <button 
                type="button" 
                className="btn btn-sm btn-secondary"
                onClick={() => handleQuickLogin('nurse@hospital.org', 'nurse123')}
              >
                <Activity size={13} />
                <span>Ananya Sen (Nurse)</span>
              </button>
              <button 
                type="button" 
                className="btn btn-sm btn-secondary"
                onClick={() => handleQuickLogin('admin@hospital.org', 'admin123')}
              >
                <Cpu size={13} />
                <span>Admin</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
