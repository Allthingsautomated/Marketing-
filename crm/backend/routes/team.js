const express = require('express');
const { v4: uuidv4 } = require('uuid');
const { read, write } = require('../data/db');

const router = express.Router();

router.get('/', (req, res) => res.json(read('team')));

router.get('/:id', (req, res) => {
  const member = read('team').find(m => m.id === req.params.id);
  if (!member) return res.status(404).json({ error: 'Not found' });
  res.json(member);
});

router.post('/', (req, res) => {
  const team = read('team');
  const member = { id: uuidv4(), createdAt: new Date().toISOString(), ...req.body };
  team.push(member);
  write('team', team);
  res.status(201).json(member);
});

router.put('/:id', (req, res) => {
  const team = read('team');
  const idx = team.findIndex(m => m.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  team[idx] = { ...team[idx], ...req.body, updatedAt: new Date().toISOString() };
  write('team', team);
  res.json(team[idx]);
});

router.delete('/:id', (req, res) => {
  write('team', read('team').filter(m => m.id !== req.params.id));
  res.json({ success: true });
});

module.exports = router;
