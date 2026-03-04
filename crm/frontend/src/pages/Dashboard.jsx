import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const COLORS = { stroke: '#6366f1', fill: 'rgba(99,102,241,0.15)' };

export default function Dashboard() {
  const [stats, setStats] = useState({ contacts: 0, jobs: 0, invoices: 0, revenue: 0, outstanding: 0 });
  const [recentJobs, setRecentJobs] = useState([]);
  const [recentContacts, setRecentContacts] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const [contacts, jobs, invoiceStats] = await Promise.all([
          axios.get('/api/contacts').then(r => r.data),
          axios.get('/api/jobs').then(r => r.data),
          axios.get('/api/invoices/stats/summary').then(r => r.data).catch(() => ({ paid: 0, outstanding: 0, count: 0 })),
        ]);
        setStats({
          contacts: contacts.length,
          jobs: jobs.length,
          invoices: invoiceStats.count,
          revenue: invoiceStats.paid,
          outstanding: invoiceStats.outstanding,
        });
        setRecentJobs(jobs.slice(-5).reverse());
        setRecentContacts(contacts.slice(-5).reverse());
      } catch {}
    }
    load();
  }, []);

  const chartData = [
    { month: 'Oct', revenue: 4200 },
    { month: 'Nov', revenue: 6800 },
    { month: 'Dec', revenue: 5100 },
    { month: 'Jan', revenue: 8900 },
    { month: 'Feb', revenue: 7400 },
    { month: 'Mar', revenue: stats.revenue || 0 },
  ];

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__title">Dashboard</div>
          <div className="page-header__sub">Welcome back — here's what's happening today</div>
        </div>
      </div>

      <div className="stats-grid">
        <StatCard title="Total Contacts" value={stats.contacts} icon="👥" sub="leads & clients" />
        <StatCard title="Active Jobs" value={stats.jobs} icon="🔧" sub="all projects" />
        <StatCard title="Revenue Collected" value={`$${stats.revenue.toLocaleString()}`} icon="💰" sub="paid invoices" color="var(--success)" />
        <StatCard title="Outstanding" value={`$${stats.outstanding.toLocaleString()}`} icon="📄" sub="unpaid invoices" color="var(--warning)" />
      </div>

      <div className="grid-2" style={{ gap: 20, marginBottom: 24 }}>
        <div className="card">
          <div className="card__title">Revenue Trend</div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={chartData}>
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `$${v/1000}k`} />
              <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2e3350', borderRadius: 8 }} labelStyle={{ color: '#e2e8f0' }} formatter={v => [`$${v.toLocaleString()}`, 'Revenue']} />
              <Area type="monotone" dataKey="revenue" stroke={COLORS.stroke} fill={COLORS.fill} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card__title">Jobs by Month</div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData}>
              <XAxis dataKey="month" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: '#1a1d27', border: '1px solid #2e3350', borderRadius: 8 }} labelStyle={{ color: '#e2e8f0' }} />
              <Bar dataKey="revenue" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2" style={{ gap: 20 }}>
        <div className="card">
          <div className="card__title" style={{ marginBottom: 16 }}>Recent Jobs</div>
          {recentJobs.length === 0
            ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No jobs yet</p>
            : <table><tbody>
                {recentJobs.map(j => (
                  <tr key={j.id}>
                    <td>{j.title || 'Untitled'}</td>
                    <td><span className={`badge badge--${j.status}`}>{j.status}</span></td>
                  </tr>
                ))}
              </tbody></table>
          }
        </div>
        <div className="card">
          <div className="card__title" style={{ marginBottom: 16 }}>Recent Contacts</div>
          {recentContacts.length === 0
            ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No contacts yet</p>
            : <table><tbody>
                {recentContacts.map(c => (
                  <tr key={c.id}>
                    <td>{c.name}</td>
                    <td><span className={`badge badge--${c.status || 'lead'}`}>{c.status || 'lead'}</span></td>
                  </tr>
                ))}
              </tbody></table>
          }
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, sub, color }) {
  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <div className="card__title">{title}</div>
        <span style={{ fontSize: 22 }}>{icon}</span>
      </div>
      <div className="card__value" style={color ? { color } : {}}>{value}</div>
      <div className="card__sub">{sub}</div>
    </div>
  );
}
