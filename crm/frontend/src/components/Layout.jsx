import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NAV = [
  { to: '/', label: 'Dashboard', icon: '📊', end: true },
  { to: '/contacts', label: 'Leads & Contacts', icon: '👥' },
  { to: '/jobs', label: 'Jobs & Projects', icon: '🔧' },
  { to: '/invoices', label: 'Invoices & Quotes', icon: '📄' },
  { to: '/team', label: 'Team & Scheduling', icon: '📅' },
  { to: '/integrations', label: 'Integrations', icon: '🔗' },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar__logo">
          <span>⚡</span>
          <div>AllThings<strong>CRM</strong></div>
        </div>
        <nav className="sidebar__nav">
          {NAV.map(n => (
            <NavLink key={n.to} to={n.to} end={n.end}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
              <span className="icon">{n.icon}</span>
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar__footer">
          <div className="sidebar__user">
            <div className="sidebar__avatar">{user?.name?.[0] || 'O'}</div>
            <div>
              <div style={{ fontWeight: 600 }}>{user?.name}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{user?.role}</div>
            </div>
          </div>
          <button className="btn btn--ghost btn--sm" style={{ width: '100%', marginTop: 12 }} onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
