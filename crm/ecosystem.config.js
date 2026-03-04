// PM2 ecosystem config — for self-hosted VPS
module.exports = {
  apps: [
    {
      name: 'crm-backend',
      script: './backend/server.js',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      env: {
        NODE_ENV: 'production',
        PORT: 5000,
      },
    },
  ],
};
