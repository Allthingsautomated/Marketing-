/**
 * QuickBooks Online Integration
 * Uses OAuth 2.0 — requires QB Developer credentials in .env:
 *   QB_CLIENT_ID, QB_CLIENT_SECRET, QB_REDIRECT_URI, QB_REALM_ID
 */
const express = require('express');
const axios = require('axios');

const router = express.Router();

const QB_BASE = 'https://sandbox-quickbooks.api.intuit.com'; // Switch to production URL when ready
const AUTH_URL = 'https://appcenter.intuit.com/connect/oauth2';
const TOKEN_URL = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer';

let qbTokens = {}; // Store in DB/env in production

// Step 1: Redirect owner to QuickBooks login
router.get('/connect', (req, res) => {
  const params = new URLSearchParams({
    client_id: process.env.QB_CLIENT_ID || 'YOUR_QB_CLIENT_ID',
    scope: 'com.intuit.quickbooks.accounting',
    redirect_uri: process.env.QB_REDIRECT_URI || 'http://localhost:5000/api/quickbooks/callback',
    response_type: 'code',
    state: 'crm-qb-connect',
  });
  res.redirect(`${AUTH_URL}?${params.toString()}`);
});

// Step 2: Handle QB OAuth callback
router.get('/callback', async (req, res) => {
  const { code, realmId } = req.query;
  try {
    const response = await axios.post(TOKEN_URL,
      new URLSearchParams({ grant_type: 'authorization_code', code, redirect_uri: process.env.QB_REDIRECT_URI }),
      { auth: { username: process.env.QB_CLIENT_ID, password: process.env.QB_CLIENT_SECRET } }
    );
    qbTokens = { ...response.data, realmId };
    res.json({ success: true, message: 'QuickBooks connected!' });
  } catch (err) {
    res.status(500).json({ error: 'QB OAuth failed', details: err.message });
  }
});

// Get QB customers
router.get('/customers', async (req, res) => {
  if (!qbTokens.access_token) return res.status(400).json({ error: 'QuickBooks not connected. Visit /api/quickbooks/connect first.' });
  try {
    const { data } = await axios.get(
      `${QB_BASE}/v3/company/${qbTokens.realmId}/query?query=select * from Customer&minorversion=65`,
      { headers: { Authorization: `Bearer ${qbTokens.access_token}`, Accept: 'application/json' } }
    );
    res.json(data.QueryResponse.Customer || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch QB customers', details: err.message });
  }
});

// Get QB invoices
router.get('/invoices', async (req, res) => {
  if (!qbTokens.access_token) return res.status(400).json({ error: 'QuickBooks not connected.' });
  try {
    const { data } = await axios.get(
      `${QB_BASE}/v3/company/${qbTokens.realmId}/query?query=select * from Invoice&minorversion=65`,
      { headers: { Authorization: `Bearer ${qbTokens.access_token}`, Accept: 'application/json' } }
    );
    res.json(data.QueryResponse.Invoice || []);
  } catch (err) {
    res.status(500).json({ error: 'Failed to fetch QB invoices', details: err.message });
  }
});

// Push invoice to QB
router.post('/invoices/push', async (req, res) => {
  if (!qbTokens.access_token) return res.status(400).json({ error: 'QuickBooks not connected.' });
  try {
    const { data } = await axios.post(
      `${QB_BASE}/v3/company/${qbTokens.realmId}/invoice?minorversion=65`,
      req.body,
      { headers: { Authorization: `Bearer ${qbTokens.access_token}`, 'Content-Type': 'application/json', Accept: 'application/json' } }
    );
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: 'Failed to push invoice to QB', details: err.message });
  }
});

router.get('/status', (req, res) => {
  res.json({ connected: !!qbTokens.access_token, realmId: qbTokens.realmId || null });
});

module.exports = router;
