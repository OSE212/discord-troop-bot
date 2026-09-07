# Deploying to Oracle Cloud Free Tier (No Domain Name Needed)

This guide walks you step-by-step through hosting your **Discord Bot** and **Web Admin Panel** 24/7 on Oracle Cloud Infrastructure (OCI) **Always Free Tier**, completely free forever, with **no domain name required**.

---

## Architecture Overview

```
                        [ Internet ]
                             │
                  Public IP (or <IP>.nip.io)
                             │
                    ┌────────▼────────┐
                    │ Oracle Cloud VM │
                    │ (Always Free)   │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
     [ Discord Bot (run.py) ]   [ Web Panel (Port 80) ]
                │                         │
                └────────────┬────────────┘
                             │
                  [ SQLite: troop_bot.db ]
```

- **Both services run 24/7 together** inside a lightweight Docker container (or native systemd service).
- **Public IP Direct Access**: You access the admin dashboard directly in your browser at `http://<YOUR_PUBLIC_IP>` (Port 80).
- **No Domain Required**: You can use your raw Public IP or the free automatic wildcard hostname `http://<YOUR_PUBLIC_IP>.nip.io`.

---

## Step 1: Create Your Free VM on Oracle Cloud

1. Log into your [Oracle Cloud Console](https://cloud.oracle.com).
2. Go to the navigation menu (top left) ➜ **Compute** ➜ **Instances**.
3. Click **Create Instance**.
4. Configure the instance:
   - **Name**: `troop-bot`
   - **Image**: Click *Change Image* ➜ Select **Canonical Ubuntu 24.04** (or **22.04**).
   - **Shape**:
     - *Best option (Recommended)*: **Ampere (ARM)** ➜ `VM.Standard.A1.Flex` (Allocate 2 to 4 OCPUs and 12 to 24 GB RAM — Always Free!).
     - *Alternative*: **AMD** ➜ `VM.Standard.E2.1.Micro` (1 OCPU, 1 GB RAM — Always Free).
   - **Networking**:
     - Virtual cloud network: Create new or use default.
     - **Assign a public IPv4 address**: Select **Yes, assign a public IPv4 address** (⚠️ CRITICAL!).
   - **Add SSH keys**:
     - Choose **Generate a key pair for me** ➜ Click **Save Private Key** (saves a `.key` file to your PC).
   - Click **Create**.
5. Wait 1–2 minutes until the instance state changes from **PROVISIONING** to **RUNNING**.
6. Note down the **Public IP Address** displayed on the instance summary page.

---

## Step 2: Open Ports in Oracle Cloud Firewall (Security List)

By default, Oracle Cloud blocks incoming web traffic. You must allow Port 80 and 8080:

1. On your Instance Details page, under **Instance Information**, click on your **Subnet** link (e.g. `subnet-202...`).
2. Click on the **Default Security List for...**.
3. Under **Ingress Rules**, click **Add Ingress Rules**.
4. Fill in:
   - **Source Type**: `CIDR`
   - **Source CIDR**: `0.0.0.0/0`
   - **IP Protocol**: `TCP`
   - **Destination Port Range**: `80,8080,443`
   - **Description**: `Allow HTTP & Web Panel`
5. Click **Add Ingress Rules**.

---

## Step 3: Connect to Your Server via SSH

Open **PowerShell** or **Terminal** on your computer:

```bash
# Replace with the path to the .key file you downloaded, and your Oracle VM Public IP
ssh -i "D:\F2Projects\ssh-key-2026-09-07.key" ubuntu@51.170.133.36
```

*(If you get a file permissions warning on the key in Windows, move the key into `C:\Users\<YourUser>\.ssh\` and try again).*

---

## Step 4: Clone & Run the 1-Click Setup

Once connected to your Ubuntu VM:

### 4.1 Clone your repository
```bash
git clone <YOUR_GIT_REPO_URL> discord-troop-bot
cd discord-troop-bot
```
*(Or upload your project files via SFTP / SCP).*

### 4.2 Run the automated setup script
```bash
chmod +x setup_oracle.sh
./setup_oracle.sh
```
This script automatically:
- Updates package manager
- **Fixes Oracle's internal iptables firewall** (unblocking ports 80 & 8080)
- Installs Docker & Docker Compose

### 4.3 Configure your `.env` file
```bash
cp .env.example .env
nano .env
```
Update these key values:
```ini
DISCORD_TOKEN=your_bot_token_here
ADMIN_PANEL_KEY=your_strong_passkey_here
WEB_PORT=8080
ENABLE_WEB_PANEL=true
```

*(Optional - if using Discord OAuth2 login for the panel):*
```ini
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=http://<YOUR_PUBLIC_IP>/api/auth/discord/callback
```
*(Press `CTRL + O`, `Enter` to save, and `CTRL + X` to exit nano).*

---

## Step 5: Launch with Docker (24/7 Always-On)

Make sure the database file exists so Docker doesn't create it as a directory:
```bash
touch troop_bot.db
```

Start the bot and web panel in background:
```bash
docker compose up -d --build
```

That's it! Your bot is online on Discord, and your web panel is live.

---

## Step 6: Access Your Web Panel (No Domain Needed!)

Open your browser and navigate to:
```
http://51.170.133.36
```
*(e.g. `http://129.152.34.82`)*

### Free Domain Hostname Alternative (nip.io)
If you need a valid hostname for Discord OAuth2 or prefer not typing bare numbers, you can use **nip.io** instantly (zero setup, resolves automatically to your IP):
```
http://<YOUR_PUBLIC_IP>.nip.io
```
*(e.g. `http://129.152.34.82.nip.io`)*

Log in using your `ADMIN_PANEL_KEY` (or the default `admin123` if you haven't changed it).

---

## Useful Maintenance Commands

| Action | Command |
|---|---|
| **View live logs** | `docker compose logs -f` |
| **Restart services** | `docker compose restart` |
| **Stop services** | `docker compose down` |
| **Update to latest code** | `git pull && docker compose up -d --build` |
| **Check container status** | `docker compose ps` |

---

## Troubleshooting

### Web page won't load?
1. **Check OCI Security List**: Ensure Port 80 is added in your Oracle Cloud Subnet Ingress rules (Step 2).
2. **Check OS Firewall**: Run this on the VM to verify iptables:
   ```bash
   sudo iptables -L -n -v | grep 80
   ```
   If needed, rerun:
   ```bash
   sudo iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
   sudo netfilter-persistent save
   ```
3. **Check container logs**:
   ```bash
   docker compose logs -f
   ```

### SQLite database persistence:
The `docker-compose.yml` mounts `./troop_bot.db` into the container. All registered players, rosters, formations, and hero settings are saved directly on the host disk and survive any reboot or container updates.
