#!/usr/bin/env bash
# ==============================================================================
# AutoBotix — Multi-VM Node Provisioning Script (Debian / Ubuntu)
# ==============================================================================
set -e

echo "=== [1/6] Memperbarui Repository & Menginstall Dependensi Sistem ==="
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    python3 python3-pip python3-venv xvfb ffmpeg chromium git curl jq sqlite3

echo "=== [2/6] Menyiapkan Direktori & Environment ==="
mkdir -p /root/google-review-automation
cd /root/google-review-automation

# Buat virtual environment python
if [ ! -d "/root/google-review-automation/.venv" ]; then
    python3 -m venv /root/google-review-automation/.venv
fi

echo "=== [3/6] Mengunduh Dependensi Python ==="
/root/google-review-automation/.venv/bin/pip install --upgrade pip -q
/root/google-review-automation/.venv/bin/pip install -q \
    Flask Werkzeug selenium seleniumbase requests python-dotenv psutil Jinja2

echo "=== [4/6] Mengonfigurasi 6 Layar Virtual Xvfb (:99 s/d :104) ==="
cat << 'EOF' > /etc/systemd/system/chromium-display.service
[Unit]
Description=Virtual display for Google Review Automation Display :99
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :99 -screen 0 1366x768x24 -nolisten tcp
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

for port in 100 101 102 103 104; do
cat << EOF > /etc/systemd/system/chromium-display-${port}.service
[Unit]
Description=Virtual display for Google Review Automation Display :${port}
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/Xvfb :${port} -screen 0 1366x768x24 -nolisten tcp
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
done

systemctl daemon-reload
systemctl enable --now chromium-display.service chromium-display-100.service chromium-display-101.service chromium-display-102.service chromium-display-103.service chromium-display-104.service

echo "=== [5/6] Mengonfigurasi Service AutoBotix Dashboard ==="
cat << 'EOF' > /etc/systemd/system/google-review-automation.service
[Unit]
Description=Google Review Automation dashboard
After=network.target chromium-display.service
Wants=chromium-display.service

[Service]
Type=simple
WorkingDirectory=/root/google-review-automation
EnvironmentFile=-/root/google-review-automation/.env
Environment=DISPLAY=:99
Environment=CHROMIUM_DISPLAY=:99
ExecStart=/root/google-review-automation/.venv/bin/python /root/google-review-automation/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable google-review-automation.service

echo "=== [6/6] Selesai! ==="
echo "Salin file kode dari Host/VM-1, lalu jalankan: systemctl restart google-review-automation"
