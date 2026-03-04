import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const EMPTY = { name: '', email: '', phone: '', company: '', status: 'lead', notes: '' };

export default function Contacts() {
  const [contacts, setContacts] = useState([]);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [editing, setEditing] = useState(null);

  async function load() {
    const { data } = await axios.get('/api/contacts', { params: { search } });
    setContacts(data);
  }

  useEffect(() => { load(); }, [search]);

  function openNew() { setForm(EMPTY); setEditing(null); setModal(true); }
  function openEdit(c) { setForm(c); setEditing(c.id); setModal(true); }

  async function save() {
    try {
      if (editing) {
        await axios.put(`/api/contacts/${editing}`, form);
        toast.success('Contact updated');
      } else {
        await axios.post('/api/contacts', form);
        toast.success('Contact added');
      }
      setModal(false);
      load();
    } catch { toast.error('Failed to save'); }
  }

  async function remove(id) {
    if (!confirm('Delete this contact?')) return;
    await axios.delete(`/api/contacts/${id}`);
    toast.success('Deleted');
    load();
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__title">Leads & Contacts</div>
          <div className="page-header__sub">{contacts.length} total</div>
        </div>
        <button className="btn btn--primary" onClick={openNew}>+ Add Contact</button>
      </div>

      <div className="search-bar">
        <input className="search-input" placeholder="Search contacts…" value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th><th>Company</th><th>Email</th><th>Phone</th><th>Status</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {contacts.length === 0 && (
                <tr><td colSpan={6} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No contacts yet — add your first one!</td></tr>
              )}
              {contacts.map(c => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 600 }}>{c.name}</td>
                  <td>{c.company || '—'}</td>
                  <td>{c.email}</td>
                  <td>{c.phone || '—'}</td>
                  <td><span className={`badge badge--${c.status}`}>{c.status}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn--ghost btn--sm" onClick={() => openEdit(c)}>Edit</button>
                      <button className="btn btn--danger btn--sm" onClick={() => remove(c.id)}>Delete</button>
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
              <div className="modal__title">{editing ? 'Edit Contact' : 'New Contact'}</div>
              <button className="modal__close" onClick={() => setModal(false)}>×</button>
            </div>
            <div className="grid-2">
              <div className="form-group"><label>Name *</label><input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} /></div>
              <div className="form-group"><label>Company</label><input value={form.company} onChange={e => setForm(f => ({ ...f, company: e.target.value }))} /></div>
            </div>
            <div className="grid-2">
              <div className="form-group"><label>Email</label><input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} /></div>
              <div className="form-group"><label>Phone</label><input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} /></div>
            </div>
            <div className="form-group">
              <label>Status</label>
              <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                <option value="lead">Lead</option>
                <option value="active">Active Client</option>
                <option value="completed">Past Client</option>
              </select>
            </div>
            <div className="form-group"><label>Notes</label><textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setModal(false)}>Cancel</button>
              <button className="btn btn--primary" onClick={save}>Save Contact</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
