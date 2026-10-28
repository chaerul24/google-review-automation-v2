# 🎬 AutoBotix — Promo Video (Remotion)

Video promosi terprogram (programmatic video) untuk **AutoBotix (Google Review Automation)** yang dibuat menggunakan [Remotion](https://www.remotion.dev/) dan React.

Tersedia dalam 2 format resolusi:
1. **Landscape 16:9** (`1920x1080`, 15 detik @ 30fps) — Sangat cocok untuk YouTube, Twitter/X, Website Landing Page, dan GitHub README.
2. **Vertical Shorts 9:16** (`1080x1920`, 15 detik @ 30fps) — Siap pakai untuk TikTok, Instagram Reels, dan YouTube Shorts.

---

## 🚀 Fitur & Adegan Video

- **Scene 1 (0s - 3.66s): Hook & Solusi**
  - Animasi rating bintang 5 emas (⭐⭐⭐⭐⭐).
  - Judul AutoBotix dengan glowing cyber gradient.
  - Perkenalan teknologi otomasi ulasan Google Maps anti-ribet tanpa VM berat.
- **Scene 2 (3.66s - 7.33s): Arsitektur Zero-VM vs Heavy Emulator**
  - Komparasi visual: Emulator tradisional (boros 8GB RAM, lambat, rawan banned) vs AutoBotix Native Chromium + Virtual Displays (`Xvfb :99, :100, :101`).
  - Indikator live status slot browser aktif.
- **Scene 3 (7.33s - 11.0s): Sistem Anti-Bot & Pre-Check Skip**
  - Simulasi Live Worker Console: Verifikasi sesi akun Google aktif.
  - Fitur pintar: Otomatis mendeteksi ulasan yang sudah ada di Maps target dan **Auto-Skip** akun duplikat.
  - Jeda antrean organik alami (30s-60s) agar tidak terdeteksi bot Google.
- **Scene 4 (11.0s - 15.0s): Windows CLI & GitHub Call To Action**
  - Tampilan Command Prompt Windows / Terminal Linux dengan ASCII banner & Auto-Updater `v1.0.3`.
  - Tombol Call-to-action repositori GitHub: `github.com/chaerul24/google-review-automation-v2`.

---

## 🛠️ Cara Menjalankan & Render

Masuk ke folder `promo-video`:
```bash
cd /root/google-review-automation/promo-video
```

### 1. Pratinjau Interaktif (Remotion Studio)
Untuk melihat video langsung di browser dengan kontrol timeline frame-by-frame:
```bash
npm run dev
# atau
npm run studio
```

### 2. Render Video MP4 Landscape (16:9)
```bash
npm run render:landscape
```
Hasil video akan disimpan di: `out/autobotix-promo-landscape.mp4`.

### 3. Render Video MP4 Vertical Shorts (9:16)
```bash
npm run render:shorts
```
Hasil video akan disimpan di: `out/autobotix-promo-shorts.mp4`.

### 4. Render Semua Format Sekaligus
```bash
npm run render:all
```

---

## 📁 Struktur Kode

```text
promo-video/
├── out/                           # Hasil render file video MP4
│   ├── autobotix-promo-landscape.mp4
│   └── autobotix-promo-shorts.mp4
├── src/
│   ├── components/
│   │   └── Background.tsx         # Latar belakang animasi grid & radial glow orbs
│   ├── scenes/
│   │   ├── Scene1Hook.tsx         # Adegan 1: Hook & bintang 5
│   │   ├── Scene2Architecture.tsx # Adegan 2: Komparasi Zero-VM
│   │   ├── Scene3AntiBotQueue.tsx # Adegan 3: Antrean antidetect & duplicate skip
│   │   └── Scene4TerminalAndCta.tsx# Adegan 4: Terminal CLI & CTA GitHub
│   ├── AutoBotixPromo.tsx         # Komposisi Landscape 16:9
│   ├── AutoBotixShorts.tsx        # Komposisi Vertical 9:16
│   └── Root.tsx                   # Pendaftaran komposisi Remotion
├── package.json
└── remotion.config.ts
```
