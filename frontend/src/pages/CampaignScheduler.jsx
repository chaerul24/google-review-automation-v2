import React, { useState, useEffect } from 'react';
import {
  Clock,
  Play,
  Pause,
  ShieldCheck,
  Calendar,
  Layers,
  Zap,
  CheckCircle2,
  AlertCircle,
  X,
  Star,
  Mail,
  RefreshCw,
  Sliders,
} from 'lucide-react';
import { api } from '../api/client';

export default function CampaignScheduler() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form State
  const [form, setForm] = useState({
    drip_min_delay: 30,
    drip_max_delay: 90,
    active_hour_start: 8,
    active_hour_end: 21,
    anti_spam_jitter: 25,
    is_paused: 0,
  });

  const [notification, setNotification] = useState({ type: '', message: '' });

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const res = await api.getCampaigns();
      if (res && res.data) {
        setData(res.data);
        if (res.data.settings) {
          setForm({
            drip_min_delay: res.data.settings.drip_min_delay || 30,
            drip_max_delay: res.data.settings.drip_max_delay || 90,
            active_hour_start: res.data.settings.active_hour_start || 8,
            active_hour_end: res.data.settings.active_hour_end || 21,
            anti_spam_jitter: res.data.settings.anti_spam_jitter || 25,
            is_paused: res.data.settings.is_paused || 0,
          });
        }
      }
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Gagal memuat data kampanye.',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await api.saveCampaignConfig(form);
      setNotification({
        type: 'success',
        message: res.message || 'Konfigurasi jadwal distribusi berhasil diperbarui.',
      });
      loadCampaigns();
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Gagal menyimpan konfigurasi.',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleTogglePause = async () => {
    const nextPaused = form.is_paused ? 0 : 1;
    setSaving(true);
    try {
      await api.saveCampaignConfig({ ...form, is_paused: nextPaused });
      setForm((prev) => ({ ...prev, is_paused: nextPaused }));
      setNotification({
        type: nextPaused ? 'info' : 'success',
        message: nextPaused
          ? 'Distribusi ulasan dijeda sementara.'
          : 'Distribusi ulasan aktif kembali.',
      });
      loadCampaigns();
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Gagal mengubah status jadwal.',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400 font-mono">Menghitung jadwal rilis ulasan...</span>
        </div>
      </div>
    );
  }

  const queue = data?.queue || [];
  const isPaused = Boolean(form.is_paused);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Alert Notifications */}
      {notification.message && (
        <div
          className={`p-3.5 rounded-xl text-xs flex items-center justify-between border transition-all ${
            notification.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/20 text-rose-300'
              : notification.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
              : 'bg-slate-800/80 border-slate-700/80 text-slate-300'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {notification.type === 'error' ? (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            )}
            <span>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification({ type: '', message: '' })}
            className="p-1 rounded hover:bg-white/10 transition-colors ml-4"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Clean Header Bar */}
      <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
              Drip-Feeding & Rate Limiting
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Jadwal & Distribusi Bertahap (Drip Engine)
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Menghindari lonjakan ulasan mendadak yang memicu filter spam Google Maps. Mengatur jeda acak (jitter) dan jam aktif harian agar ritme posting tampak seperti interaksi pengguna nyata.
          </p>
        </div>

        {/* Global Pause / Resume Action */}
        <div className="flex items-center gap-2.5 shrink-0 self-start md:self-auto">
          <button
            onClick={loadCampaigns}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white transition-colors cursor-pointer"
            title="Refresh Jadwal"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={handleTogglePause}
            disabled={saving}
            className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-2 transition-colors cursor-pointer shadow-xs ${
              isPaused
                ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                : 'bg-slate-800 hover:bg-slate-750 text-amber-300 border border-amber-500/30'
            }`}
          >
            {isPaused ? (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Lanjutkan Distribusi</span>
              </>
            ) : (
              <>
                <Pause className="w-3.5 h-3.5 fill-current" />
                <span>Jeda Sementara</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Antrean Menunggu</span>
          <p className="text-3xl font-extrabold text-white mt-2 font-mono">{data?.total_queued || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Ulasan dalam antrean rilis</p>
        </div>

        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Kapasitas Harian</span>
          <p className="text-3xl font-extrabold text-white mt-2 font-mono">~{data?.daily_capacity || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1">Ulasan optimal per 24 jam</p>
        </div>

        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Rentang Jeda</span>
          <p className="text-3xl font-extrabold text-white mt-2 font-mono">
            {form.drip_min_delay}–{form.drip_max_delay}m
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Variasi jeda acak: ±{form.anti_spam_jitter}%</p>
        </div>

        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Status Mesin</span>
          <div className="flex items-center gap-2 mt-2">
            <span className={`w-2.5 h-2.5 rounded-full ${isPaused ? 'bg-amber-400' : 'bg-emerald-400'}`} />
            <p className={`text-xl font-bold ${isPaused ? 'text-amber-400' : 'text-emerald-400'}`}>
              {isPaused ? 'Dijeda' : 'Aktif Berjalan'}
            </p>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Jam operasional: {form.active_hour_start}:00–{form.active_hour_end}:00</p>
        </div>
      </div>

      {/* Main Grid: Parameters & Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left (5 cols): Parameter Controls */}
        <div className="lg:col-span-5">
          <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-5 shadow-xs space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Parameter Jeda (Drip)
              </span>
              <span className="text-[11px] text-slate-400 font-mono">Konfigurasi</span>
            </div>

            <form onSubmit={handleSaveConfig} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Jeda Minimal (Menit)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="300"
                    value={form.drip_min_delay}
                    onChange={(e) => setForm({ ...form, drip_min_delay: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Jeda Maksimal (Menit)
                  </label>
                  <input
                    type="number"
                    min="10"
                    max="600"
                    value={form.drip_max_delay}
                    onChange={(e) => setForm({ ...form, drip_max_delay: Number(e.target.value) })}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">
                  Batas Jam Aktif Harian (WIB)
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-[10px] text-slate-400 block mb-1">Mulai:</span>
                    <select
                      value={form.active_hour_start}
                      onChange={(e) => setForm({ ...form, active_hour_start: Number(e.target.value) })}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
                    >
                      {[...Array(24)].map((_, h) => (
                        <option key={h} value={h}>
                          {String(h).padStart(2, '0')}:00 WIB
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-400 block mb-1">Selesai:</span>
                    <select
                      value={form.active_hour_end}
                      onChange={(e) => setForm({ ...form, active_hour_end: Number(e.target.value) })}
                      className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
                    >
                      {[...Array(24)].map((_, h) => (
                        <option key={h} value={h}>
                          {String(h).padStart(2, '0')}:00 WIB
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <p className="text-[10px] text-slate-400 mt-1.5">
                  Di luar rentang jam ini, proses worker ditahan untuk menjaga kredibilitas akun pengulas.
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-medium text-slate-300">
                    Variasi Acak Waktu (Jitter)
                  </label>
                  <span className="text-xs font-mono font-bold text-emerald-400">
                    ±{form.anti_spam_jitter}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="50"
                  step="5"
                  value={form.anti_spam_jitter}
                  onChange={(e) => setForm({ ...form, anti_spam_jitter: Number(e.target.value) })}
                  className="w-full accent-emerald-500"
                />
                <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
                  <span>0% (Interval Tetap)</span>
                  <span>25% (Rekomendasi)</span>
                  <span>50% (Sangat Acak)</span>
                </div>
              </div>

              {/* Visual 24-Hour Timeline */}
              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
                <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold block">
                  Visual Distribusi Jam Harian
                </span>
                <div className="h-3 w-full bg-slate-900 rounded flex overflow-hidden border border-slate-800">
                  {[...Array(24)].map((_, h) => {
                    const isActive = h >= form.active_hour_start && h < form.active_hour_end;
                    return (
                      <div
                        key={h}
                        className={`flex-1 transition-colors ${
                          isActive ? 'bg-emerald-500/80' : 'bg-slate-900'
                        }`}
                        title={`${h}:00 - ${isActive ? 'Aktif' : 'Mati / Menunggu'}`}
                      />
                    );
                  })}
                </div>
                <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                  <span>00:00</span>
                  <span>06:00</span>
                  <span>12:00</span>
                  <span>18:00</span>
                  <span>24:00</span>
                </div>
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-2.5 rounded-xl font-semibold text-xs bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center gap-2 shadow-xs disabled:opacity-50 transition-colors cursor-pointer"
              >
                {saving ? 'Menyimpan...' : 'Simpan Konfigurasi Jadwal'}
              </button>
            </form>
          </div>
        </div>

        {/* Right (7 cols): Scheduled Queue Timeline */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div>
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                  Timeline Antrean Rilis Ulasan
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Jadwal eksekusi ulasan berikutnya berdasarkan kalkulasi jeda berkala.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {queue.length} tugas
              </span>
            </div>

            {queue.length === 0 ? (
              <div className="p-12 text-center bg-slate-950/40 rounded-xl border border-slate-800/60 flex flex-col items-center justify-center space-y-3">
                <div className="p-3 rounded-xl bg-slate-900 text-slate-400 border border-slate-800">
                  <Clock className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">Tidak Ada Antrean Menunggu</p>
                  <p className="text-xs text-slate-400 max-w-sm mt-1">
                    Seluruh tugas ulasan telah diproses. Anda dapat menambahkan ulasan baru dari menu Target Bisnis atau Studio Ulasan.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-[520px] overflow-y-auto pr-1 no-scrollbar">
                {queue.map((item, idx) => (
                  <div
                    key={item.id}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <span className="text-xs font-mono font-bold text-slate-500 shrink-0 mt-0.5">
                        #{idx + 1}
                      </span>

                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="text-xs font-bold text-white truncate">
                            {item.business_name}
                          </h4>
                          <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-400">
                            {item.star_rating} <Star className="w-3 h-3 fill-current" />
                          </span>
                        </div>

                        <p className="text-[11px] text-slate-400 font-mono mt-0.5 truncate flex items-center gap-1">
                          <Mail className="w-3 h-3 text-slate-500 shrink-0" />
                          <span>{item.email_address}</span>
                        </p>
                      </div>
                    </div>

                    <div className="text-right shrink-0 sm:pl-3 border-t sm:border-t-0 sm:border-l border-slate-800/80 pt-2 sm:pt-0">
                      <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-semibold bg-slate-900 text-emerald-400 border border-slate-800">
                        <Clock className="w-3 h-3" />
                        <span>+{item.eta_minutes}m</span>
                      </div>
                      <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                        {item.estimated_run_at}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
