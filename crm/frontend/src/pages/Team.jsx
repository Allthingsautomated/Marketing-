import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const EMPTY = { name: '', email: '', phone: '', role: 'technician', availability: 'full-time', skills: '', notes: '' };

export default function Team() {
  const [team, setTeam] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [editing, setEditing] = useState(null);

  async function load() {
    const [t, j] = await Promise.all([
      axios.get('/api/team').then(r => r.data),
      axios.get('/api/jobs').then(r => r.data),
    ]);
    setTeam(t);
    setJobs(j);
  }

  useEffect(() => { load(); }, []);

  function openNew() { setForm(EMPTY); setEditing(null); setModal(true); }
  function openEdit(m) { setForm(m); setEditing(m.id); setModal(true); }

  async function save() {
    try {
      if (editing) { await axios.put(`/api/team/${editing}`, form); toast.success('Updated'); }
      else { await axios.post('/api/team', form); toast.success('Team member added'); }
      setModal(false);
      load();
    } catch { toast.error('Failed to save'); }
  }

  async function remove(id) {
    if (!confirm('Remove this team member?')) return;
    await axios.delete(`/api/team/${id}`);
    toast.success('Removed');
    load();
  }

  function jobsFor(memberId) {
    return jobs.filter(j => j.assigneeId === memberId);
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__title">Team & Scheduling</div>
          <div className="page-header__sub">{team.length} members</div>
        </div>
        <button className="btn btn--primary" onClick={openNew}>+ Add Member</button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16, marginBottom: 28 }}>
        {team.length === 0 && (
          <div className="card">
            <p style={{ color: 'var(--text-muted)' }}>No team members yet</p>
          </div>
        )}
        {team.map(m => (
          <div className="card" key={m.id}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
              <div style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700, fontSize: 16, flexShrink: 0 }}>
                {m.name?.[0]?.toUpperCase()}
              </div>
              <div>
                <div style={{ fontWeight: 700 }}>{m.name}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{m.role}</div>
              </div>
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 4 }}>📧 {m.email || '—'}</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 4 }}>📞 {m.phone || '—'}</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 12 }}>🔧 {m.skills || '—'}</div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 12, background: 'var(--surface2)', padding: '3px 10px', borderRadius: 20 }}>{jobsFor(m.id).length} active jobs</span>
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="btn btn--ghost btn--sm" onClick={() => openEdit(m)}>Edit</button>
                <button className="btn btn--danger btn--sm" onClick={() => remove(m.id)}>Remove</button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Upcoming jobs schedule */}
      <div className="card">
        <div className="card__title" style={{ marginBottom: 16 }}>Job Schedule</div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Job</th><th>Assigned To</th><th>Status</th><th>Start</th><th>End</th></tr></thead>
            <tbody>
              {jobs.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center', padding: 30, color: 'var(--text-muted)' }}>No jobs scheduled</td></tr>}
              {jobs.map(j => (
                <tr key={j.id}>
                  <td style={{ fontWeight: 600 }}>{j.title}</td>
                  <td>{team.find(m => m.id === j.assigneeId)?.name || 'Unassigned'}</td>
                  <td><span className={`badge badge--${j.status}`}>{j.status}</span></td>
                  <td>{j.startDate || '—'}</td>
                  <td>{j.endDate || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {modal && (
        <div className="modal-overlay" onClick={e => e.target === e.currentTarget && setModal(false)}>
          <div className="modal">
            <div className="modal__header">
              <div className="modal__title">{editing ? 'Edit Member' : 'New Team Member'}</div>
              <button className="modal__close" onClick={() => setModal(false)}>×</button>
            </div>
            <div className="grid-2">
              <div className="form-group"><label>Name *</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></div>
              <div className="form-group"><label>Role</label>
                <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
                  <option value="technician">Technician</option>
                  <option value="electrician">Electrician</option>
                  <option value="installer">Installer</option>
                  <option value="project-manager">Project Manager</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            <div className="grid-2">
              <div className="form-group"><label>Email</label><input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} /></div>
              <div className="form-group"><label>Phone</label><input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} /></div>
            </div>
            <div className="form-group"><label>Skills (comma separated)</label><input value={form.skills} onChange={e => setForm(f => ({ ...f, skills: e.target.value }))} placeholder="Smart Home, Electrical, Networking…" /></div>
            <div className="form-group"><label>Availability</label>
              <select value={form.availability} onChange={e => setForm(f => ({ ...f, availability: e.target.value }))}>
                <option value="full-time">Full Time</option>
                <option value="part-time">Part Time</option>
                <option value="on-call">On Call</option>
                <option value="contractor">Contractor</option>
              </select>
            </div>
            <div className="form-group"><label>Notes</label><textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setModal(false)}>Cancel</button>
              <button className="btn btn--primary" onClick={save}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
