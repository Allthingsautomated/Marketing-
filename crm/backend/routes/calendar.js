/**
 * Google Calendar Integration
 * Requires: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI in .env
 */
const express = require('express');
const axios = require('axios');

const router = express.Router();

const GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth';
const GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token';
const CALENDAR_BASE = 'https://www.googleapis.com/calendar/v3';

let gTokens = {};

router.get('/connect', (req, res) => {
  const params = new URLSearchParams({
    client_id: process.env.GOOGLE_CLIENT_ID || 'YOUR_GOOGLE_CLIENT_ID',
    redirect_uri: process.env.GOOGLE_REDIRECT_URI || 'http://localhost:5000/api/calendar/callback',
    response_type: 'code',
    scope: 'https://www.googleapis.com/auth/calendar',
    access_type: 'offline',
    prompt: 'consent',
  });
  res.redirect(`${GOOGLE_AUTH_URL}?${params.toString()}`);
});

router.get('/callback', async (req, res) => {
  const { code } = req.query;
  try {
    const { data } = await axios.post(GOOGLE_TOKEN_URL, {
      code,
      client_id: process.env.GOOGLE_CLIENT_ID,
      client_secret: process.env.GOOGLE_CLIENT_SECRET,
      redirect_uri: process.env.GOOGLE_REDIRECT_URI,
      grant_type: 'authorization_code',
    });
    gTokens = data;
    res.json({ success: true, message: 'Google Calendar connected!' });
  } catch (err) {
    res.status(500).json({ error: 'Google OAuth failed', details: err.message });
  }
});

router.get('/events', async (req, res) => {
  if (!gTokens.access_token) return res.status(400).json({ error: 'Google Calendar not connected. Visit /api/calendar/connect first.' });
  try {
    const { data } = await axios.get(`${CALENDAR_BASE}/calendars/primary/events`, {
      headers: { Authorization: `Bearer ${gTokens.access_token}` },
      params: { timeMin: new Date().toISOString(), maxResults: 50, singleEvents: true, orderBy: 'startTime' },
    });
    res.json(data.items || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch events', details: err.message });
  }
});

router.post('/events', async (req, res) => {
  if (!gTokens.access_token) return res.status(400).json({ error: 'Google Calendar not connected.' });
  try {
    const { data } = await axios.post(`${CALENDAR_BASE}/calendars/primary/events`, req.body, {
      headers: { Authorization: `Bearer ${gTokens.access_token}`, 'Content-Type': 'application/json' },
    });
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to create event', details: err.message });
  }
});

router.get('/status', (req, res) => {
  res.json({ connected: !!gTokens.access_token });
});

module.exports = router;
