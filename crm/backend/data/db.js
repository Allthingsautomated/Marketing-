/**
 * Simple JSON file-based store.
 * Replace with PostgreSQL/MongoDB in production.
 */
const fs = require('fs');
const path = require('path');

const FILES = {
  users: path.join(__dirname, 'users.json'),
  contacts: path.join(__dirname, 'contacts.json'),
  jobs: path.join(__dirname, 'jobs.json'),
  invoices: path.join(__dirname, 'invoices.json'),
  team: path.join(__dirname, 'team.json'),
};

function read(collection) {
  if (!fs.existsSync(FILES[collection])) return [];
  return JSON.parse(fs.readFileSync(FILES[collection], 'utf8'));
}

function write(collection, data) {
  fs.writeFileSync(FILES[collection], JSON.stringify(data, null, 2));
}

module.exports = { read, write };
