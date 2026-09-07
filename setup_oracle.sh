#!/usr/bin/env bash
# ==============================================================================
# Oracle Cloud Free Tier Setup Script for Discord Troop Bot & Web Panel
# Run this on your Ubuntu 22.04 / 24.04 instance:
#   chmod +x setup_oracle.sh
#   ./setup_oracle.sh
# ==============================================================================

set -e

echo "=========================================================="
echo " [1/4] Updating packages and system dependencies..."
echo "=========================================================="
sudo apt-get update -y
sudo apt-get install -y git curl ufw iptables-persistent netfilter-persistent

echo "=========================================================="
echo " [2/4] Configuring Oracle Cloud OS Firewall..."
echo " (Opening ports 80, 8080, 443, and 22 for SSH)"
echo "=========================================================="
# OCI Ubuntu images have restrictive iptables rules by default.
# Open ports 80 (HTTP), 8080 (Web panel alternate), and 443 (HTTPS)
sudo iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 1 -p tcp --dport 8080 -j ACCEPT
sudo iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT 1 -p tcp --dport 22 -j ACCEPT
sudo netfilter-persistent save

echo "=========================================================="
echo " [3/4] Installing Docker and Docker Compose..."
echo "=========================================================="
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "Docker installed successfully."
else
    echo "Docker is already installed."
fi

# Ensure docker-compose plugin is available
sudo apt-get install -y docker-compose-plugin

echo "=========================================================="
echo " [4/4] Setup completed!"
echo "=========================================================="
echo ""
echo "NEXT STEPS:"
echo "1. Make sure you have your .env file ready:"
echo "     cp .env.example .env"
echo "     nano .env   (paste your DISCORD_TOKEN, ADMIN_PANEL_KEY, etc.)"
echo ""
echo "2. Ensure an empty SQLite file exists before starting:"
echo "     touch troop_bot.db"
echo ""
echo "3. Start the container in background:"
echo "     docker compose up -d --build"
echo ""
echo "4. View logs anytime:"
echo "     docker compose logs -f"
echo ""
echo "Your Web Panel will be live at: http://<YOUR_ORACLE_PUBLIC_IP>/"
echo "=========================================================="
