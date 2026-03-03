# Deploy to DigitalOcean — Step by Step

Total time: ~15 minutes. Cost: $6/month.

---

## Step 1 — Create a Droplet

1. Go to https://cloud.digitalocean.com
2. Click **Create → Droplets**
3. Choose:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic → Regular → **$6/month** (1 GB RAM, 1 vCPU)
   - **Region:** Closest to your clients (e.g. New York)
   - **Authentication:** Add your SSH key (or use a password)
4. Click **Create Droplet**
5. Copy your Droplet's IP address

---

## Step 2 — SSH Into Your Server

```bash
ssh root@YOUR_DROPLET_IP
```

---

## Step 3 — Install Docker

```bash
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin
```

---

## Step 4 — Get the Code

```bash
git clone https://github.com/Allthingsautomated/Marketing-.git
cd Marketing-/lead_engine
```

---

## Step 5 — Add Your API Keys

```bash
cp .env.example .env
nano .env
```

Paste in your keys, then save (`Ctrl+X → Y → Enter`).

---

## Step 6 — Launch

```bash
docker compose up -d
```

Your dashboard is now live at:
```
http://YOUR_DROPLET_IP:8000
```

---

## Optional: Add a Domain + HTTPS

If you have a domain (e.g. `leads.allthingsautomated.com`):

1. Point your domain's A record to the Droplet IP
2. Install nginx + certbot:

```bash
apt-get install -y nginx certbot python3-certbot-nginx

# Create nginx config
cat > /etc/nginx/sites-available/lead-engine << 'EOF'
server {
    server_name leads.yourdomain.com;
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/lead-engine /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# Get SSL certificate (free)
certbot --nginx -d leads.yourdomain.com
```

Now it's at `https://leads.yourdomain.com` with a real SSL cert.

---

## Useful Commands

```bash
# View live logs
docker compose logs -f

# Restart the app
docker compose restart

# Update to latest code
git pull && docker compose up -d --build

# Stop everything
docker compose down
```

---

## Backups

The database is stored in `./data/lead_engine.db`.
Download it anytime with:

```bash
scp root@YOUR_DROPLET_IP:~/Marketing-/lead_engine/data/lead_engine.db ./backup.db
```
