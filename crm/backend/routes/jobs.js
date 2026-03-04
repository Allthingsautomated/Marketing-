const express = require('express');
const { v4: uuidv4 } = require('uuid');
const { read, write } = require('../data/db');

const router = express.Router();

router.get('/', (req, res) => {
  const jobs = read('jobs');
  const { status, assignee } = req.query;
  let result = jobs;
  if (status) result = result.filter(j => j.status === status);
  if (assignee) result = result.filter(j => j.assigneeId === assignee);
  res.json(result);
});

router.get('/:id', (req, res) => {
  const job = read('jobs').find(j => j.id === req.params.id);
  if (!job) return res.status(404).json({ error: 'Not found' });
  res.json(job);
});

router.post('/', (req, res) => {
  const jobs = read('jobs');
  const job = { id: uuidv4(), status: 'new', createdAt: new Date().toISOString(), ...req.body };
  jobs.push(job);
  write('jobs', jobs);
  res.status(201).json(job);
});

router.put('/:id', (req, res) => {
  const jobs = read('jobs');
  const idx = jobs.findIndex(j => j.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: 'Not found' });
  jobs[idx] = { ...jobs[idx], ...req.body, updatedAt: new Date().toISOString() };
  write('jobs', jobs);
  res.json(jobs[idx]);
});

router.delete('/:id', (req, res) => {
  const jobs = read('jobs');
  write('jobs', jobs.filter(j => j.id !== req.params.id));
  res.json({ success: true });
});

module.exports = router;
