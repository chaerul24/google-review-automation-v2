#!/usr/bin/env bash
# AutoBotix Review Automation — Linux / macOS / Termux CLI Launcher

# Pastikan Python tersedia
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo -e "\033[1;31m[ERROR] Python tidak ditemukan!\033[0m"
    echo "Di Termux, install terlebih dahulu dengan menjalankan:"
    echo "  pkg install python -y"
    exit 1
fi

PY_BIN="$(command -v python3 || command -v python)"

# Tentukan server target (Coba IP LAN lokal dulu, fallback ke domain publik)
SERVER_URL="https://autobotix.my.id"
if curl -s --connect-timeout 2 http://192.168.1.17:5000/download/bot_cli.py >/dev/null 2>&1; then
    SERVER_URL="http://192.168.1.17:5000"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo ".")"
CLI_PATH="$SCRIPT_DIR/bot_cli.py"

echo -e "\033[1;36m[1/2] Menghubungkan dan menyinkronkan bot_cli.py terbaru...\033[0m"
curl -s --connect-timeout 5 "$SERVER_URL/download/bot_cli.py" -o "$CLI_PATH.tmp" 2>/dev/null || true

if [ -s "$CLI_PATH.tmp" ] && [ "$(wc -c < "$CLI_PATH.tmp")" -gt 1000 ]; then
    mv -f "$CLI_PATH.tmp" "$CLI_PATH"
    chmod +x "$CLI_PATH"
else
    rm -f "$CLI_PATH.tmp"
fi

if [ ! -f "$CLI_PATH" ]; then
    echo -e "\033[1;31m[ERROR] Gagal mengunduh bot_cli.py dari server!\033[0m"
    echo "Pastikan koneksi internet aktif atau unduh manual dari: $SERVER_URL/download/bot_cli.py"
    exit 1
fi

echo -e "\033[1;32m[2/2] Memulai AutoBotix CLI...\033[0m"
exec "$PY_BIN" "$CLI_PATH" --server "$SERVER_URL" "$@"
