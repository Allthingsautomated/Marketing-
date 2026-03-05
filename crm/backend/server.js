require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');

const authRoutes = require('./routes/auth');
const contactsRoutes = require('./routes/contacts');
const jobsRoutes = require('./routes/jobs');
const invoicesRoutes = require('./routes/invoices');
const teamRoutes = require('./routes/team');
const quickbooksRoutes = require('./routes/quickbooks');
const calendarRoutes = require('./routes/calendar');
const integrationsRoutes = require('./routes/integrations');

const { verifyToken } = require('./middleware/auth');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors({ origin: process.env.FRONTEND_URL || '*' }));
app.use(express.json());

// Public routes
app.use('/api/auth', authRoutes);

// Protected routes
app.use('/api/contacts', verifyToken, contactsRoutes);
app.use('/api/jobs', verifyToken, jobsRoutes);
app.use('/api/invoices', verifyToken, invoicesRoutes);
app.use('/api/team', verifyToken, teamRoutes);
app.use('/api/quickbooks', verifyToken, quickbooksRoutes);
app.use('/api/calendar', verifyToken, calendarRoutes);
app.use('/api/integrations', verifyToken, integrationsRoutes);

app.get('/api/health', (req, res) => res.json({ status: 'ok', timestamp: new Date() }));

// Temporary debug endpoint — remove after login is confirmed working
app.get('/api/debug', (req, res) => {
  const fs = require('fs');
  const usersPath = path.join(__dirname, 'data/users.json');
  const exists = fs.existsSync(usersPath);
  const users = exists ? JSON.parse(fs.readFileSync(usersPath, 'utf8')) : [];
  res.json({
    usersFileExists: exists,
    usersFilePath: usersPath,
    userCount: users.length,
    users: users.map(u => ({ id: u.id, email: u.email, role: u.role, hasPassword: !!u.password })),
    jwtSecretSet: !!process.env.JWT_SECRET,
    nodeEnv: process.env.NODE_ENV,
  });
});

// Serve React frontend in production
const frontendDist = path.join(__dirname, '../frontend/dist');
app.use(express.static(frontendDist));
app.get('*', (req, res) => res.sendFile(path.join(frontendDist, 'index.html')));

app.listen(PORT, '0.0.0.0', () => console.log(`CRM running on port ${PORT}`));
