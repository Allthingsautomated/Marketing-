import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const EMPTY = { contactId: '', jobId: '', status: 'draft', dueDate: '', items: [{ description: '', qty: 1, rate: 0 }], notes: '' };

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [modal, setModal] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [editing, setEditing] = useState(null);
  const [filter, setFilter] = useState('');

  async function load() {
    const [inv, c, j] = await Promise.all([
      axios.get('/api/invoices', { params: filter ? { status: filter } : {} }).then(r => r.data),
      axios.get('/api/contacts').then(r => r.data),
      axios.get('/api/jobs').then(r => r.data),
    ]);
    setInvoices(inv); setContacts(c); setJobs(j);
  }

  useEffect(() => { load(); }, [filter]);

  function total(items) {
    return (items || []).reduce((s, i) => s + (parseFloat(i.qty) || 0) * (parseFloat(i.rate) || 0), 0);
  }

  function openNew() { setForm(EMPTY); setEditing(null); setModal(true); }
  function openEdit(inv) { setForm({ ...inv, items: inv.items || [{ description: '', qty: 1, rate: 0 }] }); setEditing(inv.id); setModal(true); }

  function updateItem(idx, key, val) {
    setForm(f => {
      const items = [...f.items];
      items[idx] = { ...items[idx], [key]: val };
      return { ...f, items };
    });
  }

  function addItem() { setForm(f => ({ ...f, items: [...f.items, { description: '', qty: 1, rate: 0 }] })); }
  function removeItem(idx) { setForm(f => ({ ...f, items: f.items.filter((_, i) => i !== idx) })); }

  async function save() {
    try {
      const payload = { ...form, total: total(form.items) };
      if (editing) { await axios.put(`/api/invoices/${editing}`, payload); toast.success('Invoice updated'); }
      else { await axios.post('/api/invoices', payload); toast.success('Invoice created'); }
      setModal(false);
      load();
    } catch { toast.error('Failed to save'); }
  }

  async function remove(id) {
    if (!confirm('Delete this invoice?')) return;
    await axios.delete(`/api/invoices/${id}`);
    toast.success('Deleted');
    load();
  }

  const contactName = id => contacts.find(c => c.id === id)?.name || '—';

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__title">Invoices & Quotes</div>
          <div className="page-header__sub">{invoices.length} total</div>
        </div>
        <button className="btn btn--primary" onClick={openNew}>+ New Invoice</button>
      </div>

      <div className="search-bar">
        <select style={{ maxWidth: 200 }} value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">All Statuses</option>
          {['draft', 'sent', 'paid', 'overdue'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Invoice #</th><th>Client</th><th>Total</th><th>Status</th><th>Due Date</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {invoices.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No invoices yet</td></tr>}
              {invoices.map(inv => (
                <tr key={inv.id}>
                  <td style={{ fontWeight: 600 }}>{inv.invoiceNumber}</td>
                  <td>{contactName(inv.contactId)}</td>
                  <td style={{ fontWeight: 700 }}>${(inv.total || 0).toLocaleString()}</td>
                  <td><span className={`badge badge--${inv.status}`}>{inv.status}</span></td>
                  <td>{inv.dueDate || '—'}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn--ghost btn--sm" onClick={() => openEdit(inv)}>Edit</button>
                      <button className="btn btn--danger btn--sm" onClick={() => remove(inv.id)}>Delete</button>
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
          <div className="modal" style={{ maxWidth: 620 }}>
            <div className="modal__header">
              <div className="modal__title">{editing ? 'Edit Invoice' : 'New Invoice'}</div>
              <button className="modal__close" onClick={() => setModal(false)}>×</button>
            </div>
            <div className="grid-2">
              <div className="form-group"><label>Client</label>
                <select value={form.contactId} onChange={e => setForm(f => ({ ...f, contactId: e.target.value }))}>
                  <option value="">Select client…</option>
                  {contacts.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="form-group"><label>Status</label>
                <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                  {['draft', 'sent', 'paid', 'overdue'].map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group"><label>Due Date</label><input type="date" value={form.dueDate} onChange={e => setForm(f => ({ ...f, dueDate: e.target.value }))} /></div>

            <div style={{ marginBottom: 8, fontWeight: 600, fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Line Items</div>
            {form.items.map((item, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 80px 100px 36px', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                <input placeholder="Description" value={item.description} onChange={e => updateItem(i, 'description', e.target.value)} />
                <input placeholder="Qty" type="number" value={item.qty} onChange={e => updateItem(i, 'qty', e.target.value)} />
                <input placeholder="Rate $" type="number" value={item.rate} onChange={e => updateItem(i, 'rate', e.target.value)} />
                <button className="btn btn--danger btn--sm" onClick={() => removeItem(i)} style={{ padding: '8px 10px' }}>×</button>
              </div>
            ))}
            <button className="btn btn--ghost btn--sm" onClick={addItem} style={{ marginBottom: 16 }}>+ Add Line</button>

            <div style={{ textAlign: 'right', fontWeight: 800, fontSize: 18, marginBottom: 16 }}>
              Total: ${total(form.items).toLocaleString()}
            </div>
            <div className="form-group"><label>Notes</label><textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} /></div>
            <div className="modal__footer">
              <button className="btn btn--ghost" onClick={() => setModal(false)}>Cancel</button>
              <button className="btn btn--primary" onClick={save}>Save Invoice</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
