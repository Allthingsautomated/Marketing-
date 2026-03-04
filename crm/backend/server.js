require('dotenv').config();
const express = require('express');
const cors = require('cors');

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

app.listen(PORT, () => console.log(`CRM backend running on port ${PORT}`));
