const express = require('express');
const { v4: uuidv4 } = require('uuid');
const { read, write } = require('../data/db');

const router = express.Router();

router.get('/', (req, res) => {
  const invoices = read('invoices');
  const { status } = req.query;
  res.json(status ? invoices.filter(i => i.status === status) : invoices);
});

router.get('/:id', (req, res) => {
  const invoice = read('invoices').find(i => i.id === req.params.id);
  if (!invoice) return res.status(404).json({ error: 'Not found' });
  res.json(invoice);
});

router.post('/', (req, res) => {
  const invoices = read('invoices');
  const invoice = {
    id: uuidv4(),
    invoiceNumber: `INV-${String(invoices.length + 1).padStart(4, '0')}`,
    status: 'draft',
    createdAt: new Date().toISOString(),
    ...req.body,
  };
  invoices.push(invoice);
  write('invoices', invoices);
  res.status(201).json(invoice);
});

router.put('/:id', (req, res) => {
  const invoices = read('invoices');
  const idx = invoices.findIndex(i => i.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  invoices[idx] = { ...invoices[idx], ...req.body, updatedAt: new Date().toISOString() };
  write('invoices', invoices);
  res.json(invoices[idx]);
});

router.delete('/:id', (req, res) => {
  const invoices = read('invoices');
  write('invoices', invoices.filter(i => i.id !== req.params.id));
  res.json({ success: true });
});

// Stats summary
router.get('/stats/summary', (req, res) => {
  const invoices = read('invoices');
  const total = invoices.reduce((s, i) => s + (i.total || 0), 0);
  const paid = invoices.filter(i => i.status === 'paid').reduce((s, i) => s + (i.total || 0), 0);
  const outstanding = invoices.filter(i => i.status !== 'paid').reduce((s, i) => s + (i.total || 0), 0);
  res.json({ total, paid, outstanding, count: invoices.length });
});

module.exports = router;
