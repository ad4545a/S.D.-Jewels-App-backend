#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Deployment...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root (use sudo)"
  exit 1
fi

# Get the directory of the script and its parent (backend root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CURRENT_USER=$(logname || echo $SUDO_USER || echo "root")

echo -e "${GREEN}Project Root determined as: $PROJECT_ROOT${NC}"
echo -e "${GREEN}Running as user/owner: $CURRENT_USER${NC}"

# 1. Update and Install System Dependencies
echo -e "${GREEN}Updating system and installing dependencies...${NC}"
apt-get update
apt-get install -y python3-pip python3-venv nginx

# 2. Setup Python Virtual Environment
echo -e "${GREEN}Setting up Python Virtual Environment...${NC}"
cd "$PROJECT_ROOT"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Created .venv"
fi

# 3. Install Python Requirements
echo -e "${GREEN}Installing Python dependencies...${NC}"
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

# 4. Configure Systemd Service
echo -e "${GREEN}Configuring Systemd Service...${NC}"
SERVICE_FILE="/etc/systemd/system/market_monitor.service"

# Read template and replace placeholders
sed -e "s|{{PROJECT_PATH}}|$PROJECT_ROOT|g" \
    -e "s|{{USER}}|$CURRENT_USER|g" \
    "$SCRIPT_DIR/market_monitor.service.template" > "$SERVICE_FILE"

echo "Service file created at $SERVICE_FILE"

# Reload daemon and enable service
systemctl daemon-reload
systemctl enable market_monitor
echo -e "${GREEN}Restarting market_monitor service...${NC}"
systemctl restart market_monitor

# 5. Configure Nginx
echo -e "${GREEN}Configuring Nginx...${NC}"
NGINX_CONF="/etc/nginx/sites-available/market_monitor"
cp "$SCRIPT_DIR/nginx_app.conf" "$NGINX_CONF"

# Enable site (symlink)
if [ ! -L "/etc/nginx/sites-enabled/market_monitor" ]; then
    ln -s "$NGINX_CONF" "/etc/nginx/sites-enabled/market_monitor"
fi

# Remove default if exists (optional, helps avoid conflicts)
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    rm "/etc/nginx/sites-enabled/default"
fi

# Test and Restart Nginx
nginx -t
systemctl restart nginx

echo -e "${GREEN}Deployment Complete!${NC}"
echo "Check status with: systemctl status market_monitor"
echo "Check logs with: journalctl -u market_monitor -f"
