#!/bin/bash
set -e

echo "=== Starting MedEase EC2 Setup ==="

# 1. Database Setup
echo "--- Setting up MySQL database ---"
# Set root password to ANImam576
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'ANImam576'; FLUSH PRIVILEGES;" || true
sudo mysql -u root -pANImam576 -e "CREATE DATABASE IF NOT EXISTS medease_db;"

# Import schema
echo "--- Importing database schema ---"
sudo mysql -u root -pANImam576 medease_db < /home/ubuntu/MebEZ/database/setup.sql

# 2. Python Virtual Environment Setup
echo "--- Setting up Virtual Environment ---"
cd /home/ubuntu/MebEZ
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Install gunicorn for production serving

# 3. Nginx Reverse Proxy Setup
echo "--- Configuring Nginx ---"
sudo tee /etc/nginx/sites-available/medease <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/medease /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# 4. Start the Application using Systemd
echo "--- Configuring Systemd Service ---"
sudo tee /etc/systemd/system/medease.service <<EOF
[Unit]
Description=MedEase Flask Web App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/MebEZ
Environment="PATH=/home/ubuntu/MebEZ/venv/bin"
ExecStart=/home/ubuntu/MebEZ/venv/bin/gunicorn --bind 127.0.0.1:8081 app:app

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable medease
sudo systemctl restart medease

echo "=== MedEase EC2 Setup Complete ==="
