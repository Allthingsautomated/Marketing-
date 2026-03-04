const express = require('express');
const { v4: uuidv4 } = require('uuid');
const { read, write } = require('../data/db');

const router = express.Router();

router.get('/', (req, res) => {
  const contacts = read('contacts');
  const { search, status } = req.query;
  let result = contacts;
  if (search) result = result.filter(c => `${c.name} ${c.email} ${c.phone} ${c.company}`.toLowerCase().includes(search.toLowerCase()));
  if (status) result = result.filter(c => c.status === status);
  res.json(result);
});

router.get('/:id', (req, res) => {
  const contact = read('contacts').find(c => c.id === req.params.id);
  if (!contact) return res.status(404).json({ error: 'Not found' });
  res.json(contact);
});

router.post('/', (req, res) => {
  const contacts = read('contacts');
  const contact = { id: uuidv4(), createdAt: new Date().toISOString(), ...req.body };
  contacts.push(contact);
  write('contacts', contacts);
  res.status(201).json(contact);
});

router.put('/:id', (req, res) => {
  const contacts = read('contacts');
  const idx = contacts.findIndex(c => c.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  contacts[idx] = { ...contacts[idx], ...req.body, updatedAt: new Date().toISOString() };
  write('contacts', contacts);
  res.json(contacts[idx]);
});

router.delete('/:id', (req, res) => {
  const contacts = read('contacts');
  const filtered = contacts.filter(c => c.id !== req.params.id);
  write('contacts', filtered);
  res.json({ success: true });
});

module.exports = router;
