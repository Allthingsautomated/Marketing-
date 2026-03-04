/**
 * Slack / Teams webhooks + Email (Nodemailer)
 * Requires in .env:
 *   SLACK_WEBHOOK_URL
 *   TEAMS_WEBHOOK_URL
 *   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
 */
const express = require('express');
const axios = require('axios');
const nodemailer = require('nodemailer');

const router = express.Router();

// --- Slack ---
router.post('/slack/notify', async (req, res) => {
  const { message } = req.body;
  const webhookUrl = process.env.SLACK_WEBHOOK_URL;
  if (!webhookUrl) return res.status(400).json({ error: 'SLACK_WEBHOOK_URL not configured' });
  try {
    await axios.post(webhookUrl, { text: message });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Slack notification failed', details: err.message });
  }
});

// --- Microsoft Teams ---
router.post('/teams/notify', async (req, res) => {
  const { message } = req.body;
  const webhookUrl = process.env.TEAMS_WEBHOOK_URL;
  if (!webhookUrl) return res.status(400).json({ error: 'TEAMS_WEBHOOK_URL not configured' });
  try {
    await axios.post(webhookUrl, {
      '@type': 'MessageCard',
      '@context': 'http://schema.org/extensions',
      text: message,
    });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Teams notification failed', details: err.message });
  }
});

// --- Email ---
router.post('/email/send', async (req, res) => {
  const { to, subject, html } = req.body;
  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT || '587'),
    secure: false,
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS },
  });
  try {
    await transporter.sendMail({ from: process.env.SMTP_USER, to, subject, html });
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: 'Email send failed', details: err.message });
  }
});

// --- Status of all integrations ---
router.get('/status', (req, res) => {
  res.json({
    slack: !!process.env.SLACK_WEBHOOK_URL,
    teams: !!process.env.TEAMS_WEBHOOK_URL,
    email: !!(process.env.SMTP_USER && process.env.SMTP_PASS),
  });
});

module.exports = router;
