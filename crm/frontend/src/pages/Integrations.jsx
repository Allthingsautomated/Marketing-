import React, { useEffect, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

export default function Integrations() {
  const [qbStatus, setQbStatus] = useState(null);
  const [calStatus, setCalStatus] = useState(null);
  const [intStatus, setIntStatus] = useState(null);
  const [testMsg, setTestMsg] = useState('');

  useEffect(() => {
    Promise.all([
      axios.get('/api/quickbooks/status').then(r => setQbStatus(r.data)).catch(() => setQbStatus({ connected: false })),
      axios.get('/api/calendar/status').then(r => setCalStatus(r.data)).catch(() => setCalStatus({ connected: false })),
      axios.get('/api/integrations/status').then(r => setIntStatus(r.data)).catch(() => setIntStatus({})),
    ]);
  }, []);

  async function testSlack() {
    try {
      await axios.post('/api/integrations/slack/notify', { message: testMsg || '🔔 Test from AllThings CRM!' });
      toast.success('Slack message sent!');
    } catch { toast.error('Slack not configured — add SLACK_WEBHOOK_URL to .env'); }
  }

  async function testTeams() {
    try {
      await axios.post('/api/integrations/teams/notify', { message: testMsg || '🔔 Test from AllThings CRM!' });
      toast.success('Teams message sent!');
    } catch { toast.error('Teams not configured — add TEAMS_WEBHOOK_URL to .env'); }
  }

  async function testEmail() {
    try {
      await axios.post('/api/integrations/email/send', {
        to: 'admin@allthingsautomated.com',
        subject: 'Test from AllThings CRM',
        html: '<p>This is a test email from your CRM dashboard.</p>',
      });
      toast.success('Test email sent!');
    } catch { toast.error('Email not configured — add SMTP_USER & SMTP_PASS to .env'); }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <div className="page-header__title">Integrations</div>
          <div className="page-header__sub">Connect your business tools</div>
        </div>
      </div>

      <div style={{ maxWidth: 680 }}>

        {/* QuickBooks */}
        <div className="integration-card">
          <div className="integration-card__info">
            <div className="integration-card__icon">📊</div>
            <div>
              <div className="integration-card__name">QuickBooks Online</div>
              <div className="integration-card__desc">Sync invoices, clients, and payments</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className={`dot${qbStatus?.connected ? ' dot--on' : ''}`} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{qbStatus?.connected ? 'Connected' : 'Not connected'}</span>
            <a href="/api/quickbooks/connect">
              <button className="btn btn--primary btn--sm">{qbStatus?.connected ? 'Reconnect' : 'Connect'}</button>
            </a>
          </div>
        </div>

        {/* Google Calendar */}
        <div className="integration-card">
          <div className="integration-card__info">
            <div className="integration-card__icon">📅</div>
            <div>
              <div className="integration-card__name">Google Calendar</div>
              <div className="integration-card__desc">Two-way sync for job scheduling</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className={`dot${calStatus?.connected ? ' dot--on' : ''}`} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{calStatus?.connected ? 'Connected' : 'Not connected'}</span>
            <a href="/api/calendar/connect">
              <button className="btn btn--primary btn--sm">{calStatus?.connected ? 'Reconnect' : 'Connect'}</button>
            </a>
          </div>
        </div>

        {/* Slack */}
        <div className="integration-card">
          <div className="integration-card__info">
            <div className="integration-card__icon">💬</div>
            <div>
              <div className="integration-card__name">Slack</div>
              <div className="integration-card__desc">Team notifications via webhook</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className={`dot${intStatus?.slack ? ' dot--on' : ''}`} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{intStatus?.slack ? 'Configured' : 'Not configured'}</span>
            <button className="btn btn--ghost btn--sm" onClick={testSlack}>Test</button>
          </div>
        </div>

        {/* Teams */}
        <div className="integration-card">
          <div className="integration-card__info">
            <div className="integration-card__icon">🟦</div>
            <div>
              <div className="integration-card__name">Microsoft Teams</div>
              <div className="integration-card__desc">Team notifications via webhook</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className={`dot${intStatus?.teams ? ' dot--on' : ''}`} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{intStatus?.teams ? 'Configured' : 'Not configured'}</span>
            <button className="btn btn--ghost btn--sm" onClick={testTeams}>Test</button>
          </div>
        </div>

        {/* Email */}
        <div className="integration-card">
          <div className="integration-card__info">
            <div className="integration-card__icon">📧</div>
            <div>
              <div className="integration-card__name">Email (Gmail / Outlook)</div>
              <div className="integration-card__desc">Send invoices and quotes by email</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className={`dot${intStatus?.email ? ' dot--on' : ''}`} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{intStatus?.email ? 'Configured' : 'Not configured'}</span>
            <button className="btn btn--ghost btn--sm" onClick={testEmail}>Test</button>
          </div>
        </div>

        {/* Test message */}
        <div className="card" style={{ marginTop: 24 }}>
          <div className="card__title" style={{ marginBottom: 12 }}>Send Test Notification</div>
          <div style={{ display: 'flex', gap: 10 }}>
            <input placeholder="Custom message (optional)" value={testMsg} onChange={e => setTestMsg(e.target.value)} style={{ flex: 1 }} />
            <button className="btn btn--ghost" onClick={testSlack}>→ Slack</button>
            <button className="btn btn--ghost" onClick={testTeams}>→ Teams</button>
          </div>
        </div>

        {/* Setup guide */}
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card__title" style={{ marginBottom: 12 }}>Setup Guide</div>
          <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.8 }}>
            1. Copy <code style={{ background: 'var(--surface2)', padding: '2px 6px', borderRadius: 4 }}>crm/backend/.env.example</code> to <code style={{ background: 'var(--surface2)', padding: '2px 6px', borderRadius: 4 }}>.env</code><br />
            2. Add your API keys and webhook URLs<br />
            3. Register your app in the <strong>QuickBooks Developer Portal</strong> and <strong>Google Cloud Console</strong><br />
            4. Restart the backend server<br />
            5. Click Connect buttons above to authorize OAuth
          </p>
        </div>
      </div>
    </div>
  );
}
