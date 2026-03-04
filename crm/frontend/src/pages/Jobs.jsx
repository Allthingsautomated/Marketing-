import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const EMPTY = { title: '', description: '', contactId: '', status: 'new', priority: 'medium', startDate: '', endDate: '', address: '', notes: '' };
const STATUSES = ['new', 'in-progress', 'pending', 'completed', 'cancelled'];

export default function Jobs() {
  const [jobs, setJobs] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [filter, setFilter] = useState('');
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [editing, setEditing] = useState(null);

  async function load() {
    const [j, c] = await Promise.all([
      axios.get('/api/jobs', { params: filter ? { status: filter } : {} }).then(r => r.data),
      axios.get('/api/contacts').then(r => r.data),
    ]);
    setJobs(j);
    setContacts(c);
  }

  useEffect(() => { load(); }, [filter]);

  function openNew() { setForm(EMPTY); setEditing(null); setModal(true); }
  function openEdit(j) { setForm(j); setEditing(j.id); setModal(true); }

  async function save() {
    try {
      if (editing) { await axios.put(`/api/jobs/${editing}`, form); toast.success('Job updated'); }
      else { await axios.post('/api/jobs', form); toast.success('Job created'); }
      setModal(false);
      load();
    } catch { toast.error('Failed to save'); }
  }

  async function remove(id) {
    if (!confirm('Delete this job?')) return;
    await axios.delete(`/api/jobs/${id}`);
    toast.success('Deleted');
    load();
  }

  const contactName = id => contacts.find(c => c.id === id)?.name || '—';

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__title">Jobs & Projects</div>
          <div className="page-header__sub">{jobs.length} total</div>
        </div>
        <button className="btn btn--primary" onClick={openNew}>+ New Job</button>
      </div>

      <div className="search-bar">
        <select style={{ maxWidth: 180 }} value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">All Statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Title</th><th>Client</th><th>Status</th><th>Priority</th><th>Start</th><th>End</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {jobs.length === 0 && (
                <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No jobs yet</td></tr>
              )}
              {jobs.map(j => (
                <tr key={j.id}>
                  <td style={{ fontWeight: 600 }}>{j.title}</td>
                  <td>{contactName(j.contactId)}</td>
                  <td><span className={`badge badge--${j.status}`}>{j.status}</span></td>
                  <td><PriorityBadge p={j.priority} /></td>
                  <td>{j.startDate || '—'}</td>
                  <td>{j.endDate || '—'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn--ghost btn--sm" onClick={() => openEdit(j)}>Edit</button>
                      <button className="btn btn--danger btn--sm" onClick={() => remove(j.id)}>Delete</button>
                    </div>
                  </td>
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
              <div className="modal__title">{editing ? 'Edit Job' : 'New Job'}</div>
              <button className="modal__close" onClick={() => setModal(false)}>×</button>
            </div>
            <div className="form-group"><label>Title *</label><input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} /></div>
            <div className="form-group"><label>Client</label>
              <select value={form.contactId} onChange={e => setForm(f => ({ ...f, contactId: e.target.value }))}>
                <option value="">Select client…</option>
                {contacts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="grid-2">
              <div className="form-group"><label>Status</label>
                <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                  {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="form-group"><label>Priority</label>
                <select value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>
            <div className="grid-2">
              <div className="form-group"><label>Start Date</label><input type="date" value={form.startDate} onChange={e => setForm(f => ({ ...f, startDate: e.target.value }))} /></div>
              <div className="form-group"><label>End Date</label><input type="date" value={form.endDate} onChange={e => setForm(f => ({ ...f, endDate: e.target.value }))} /></div>
            </div>
            <div className="form-group"><label>Address</label><input value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))} /></div>
            <div className="form-group"><label>Description</label><textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} /></div>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setModal(false)}>Cancel</button>
              <button className="btn btn--primary" onClick={save}>Save Job</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PriorityBadge({ p }) {
  const colors = { high: 'var(--danger)', medium: 'var(--warning)', low: 'var(--success)' };
  return <span style={{ color: colors[p] || 'var(--text-muted)', fontWeight: 600, fontSize: 12 }}>{p || 'medium'}</span>;
}
