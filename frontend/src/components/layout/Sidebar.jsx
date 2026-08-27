import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, UserPlus, Users, Bell, Activity,
  ClipboardList, Settings, HelpCircle, LogOut, Zap
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useSurge } from '../../context/SurgeContext';
import './Sidebar.css';

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/dashboard' },
  { icon: UserPlus, label: 'New Patient', to: '/new-patient' },
  { icon: Users, label: 'Live Queue', to: '/queue' },
  { icon: Bell, label: 'Alerts', to: '/alerts' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { surgeState } = useSurge();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <Zap size={18} fill="currentColor" />
        </div>
        <div>
          <div className="sidebar-app-name">PatientTriage.ai</div>
          <div className="sidebar-tagline">Emergency Dept</div>
        </div>
      </div>

      {surgeState.is_surge && (
        <div className="sidebar-surge-indicator">
          <span className="surge-dot" />
          SURGE ACTIVE
        </div>
      )}

      <nav className="sidebar-nav">
        {navItems.map(({ icon: Icon, label, to }) => (
          <NavLink key={to} to={to} className={({ isActive }) =>
            `sidebar-link ${isActive ? 'active' : ''}`
          }>
            <Icon size={18} />
            <span>{label}</span>
            {label === 'Alerts' && surgeState.actions_required?.length > 0 && (
              <span className="sidebar-badge">{surgeState.actions_required.length}</span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <NavLink to="/settings" className="sidebar-link">
          <Settings size={18} />
          <span>Settings</span>
        </NavLink>
        <NavLink to="/help" className="sidebar-link">
          <HelpCircle size={18} />
          <span>Help</span>
        </NavLink>
        <div className="sidebar-user">
          <div className="sidebar-avatar">{user?.name?.[0] || 'U'}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user?.name || 'Staff'}</div>
            <div className="sidebar-user-role">{user?.role?.replace('_', ' ') || 'Unknown'}</div>
          </div>
          <button className="sidebar-logout" onClick={handleLogout} title="Sign out">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}
