import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { SurgeProvider } from './context/SurgeContext';

import Sidebar from './components/layout/Sidebar';
import TopBar from './components/layout/TopBar';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import NewPatient from './pages/NewPatient';
import LiveQueue from './pages/LiveQueue';
import Alerts from './pages/Alerts';
import Settings from './pages/Settings';
import Help from './pages/Help';

import './App.css';

// Protected layout wrapper
function ProtectedLayout() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="app-main">
        <TopBar />
        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <SurgeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            <Route element={<ProtectedLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/new-patient" element={<NewPatient />} />
              <Route path="/queue" element={<LiveQueue />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/help" element={<Help />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </SurgeProvider>
    </AuthProvider>
  );
}
