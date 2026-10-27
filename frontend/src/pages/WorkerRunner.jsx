import React, { useState, useEffect, useRef } from 'react';
import {
  Play,
  Square,
  Monitor,
  RefreshCw,
  Building2,
  Star,
  Terminal,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Plus,
  X,
  Layers,
  MapPin,
  Clock,
  RotateCw,
} from 'lucide-react';
import { api } from '../api/client';

export default function WorkerRunner() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [workerStatus, setWorkerStatus] = useState(null);
  const [selectedBizId, setSelectedBizId] = useState('');
  const [starRating, setStarRating] = useState(5);
  const [selectedLanguage, setSelectedLanguage] = useState('Indonesian');
  const [selectedEmailIds, setSelectedEmailIds] = useState([]);

  // Live Screen
  const [streamTs, setStreamTs] = useState(Date.now());
  const [streamError, setStreamError] = useState(false);

  // Notifications
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Quick Add Business Modal
  const [showAddBizModal, setShowAddBizModal] = useState(false);
  const [bizForm, setBizForm] = useState({ name: '', url: '' });

  // Terminal Logs
  const terminalRef = useRef(null);

  const fetchDashboardData = async () => {
    try {
      const res = await api.getDashboard();
      setData(res);
      if (res?.businesses?.length > 0 && !selectedBizId) {
        setSelectedBizId(String(res.businesses[0].id));
      }
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkerStatus = async () => {
    try {
      const res = await api.getWorkerStatus();
      setWorkerStatus(res);
    } catch (err) {
      console.debug('Failed to fetch worker status:', err);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    fetchWorkerStatus();
    const interval = setInterval(() => {
      fetchWorkerStatus();
      setStreamTs(Date.now());
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll terminal log
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [workerStatus?.system_status?.recent_logs]);

  const handleStartWorker = async () => {
    if (!selectedBizId) {
      setErrorMsg('Pilih target profil Google Maps terlebih dahulu.');
      return;
    }
    setActionLoading(true);
    try {
      const payload = {
        star_1_count: starRating === 1 ? 1 : 0,
        star_2_count: starRating === 2 ? 1 : 0,
        star_3_count: starRating === 3 ? 1 : 0,
        star_4_count: starRating === 4 ? 1 : 0,
        star_5_count: starRating === 5 ? 1 : 0,
        selected_language: selectedLanguage,
        selected_email_ids: selectedEmailIds.length > 0 ? selectedEmailIds : undefined,
      };

      const res = await api.startBot(selectedBizId, payload);
      setSuccessMsg('Worker berhasil diluncurkan! Membuka Chromium di Virtual Display :99.');
      fetchWorkerStatus();
      fetchDashboardData();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menjalankan worker.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopWorker = async () => {
    if (!confirm('Hentikan proses Chromium worker yang sedang aktif?')) return;
    setActionLoading(true);
    try {
      const res = await api.emergencyStopWorker();
      setSuccessMsg(res.message || 'Worker Chromium berhasil dihentikan.');
      fetchWorkerStatus();
      fetchDashboardData();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menghentikan worker.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddBizSubmit = async (e) => {
    e.preventDefault();
    if (!bizForm.name || !bizForm.url) return;
    try {
      const res = await api.addBusiness(bizForm.name, bizForm.url);
      setSuccessMsg(`Target bisnis "${bizForm.name}" berhasil ditambahkan.`);
      setBizForm({ name: '', url: '' });
      setShowAddBizModal(false);
      await fetchDashboardData();
      if (res?.business_id) {
        setSelectedBizId(String(res.business_id));
      }
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menambahkan bisnis.');
    }
  };

  const businesses = data?.businesses || [];
  const emails = data?.all_emails || [];
  const cookies = data?.all_cookies || [];
  const isWorkerRunning = Boolean(workerStatus?.system_status?.is_running);
  const activeLogs = workerStatus?.system_status?.recent_logs || [];
  const currentBiz = businesses.find((b) => String(b.id) === String(selectedBizId));

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Alert Notifications */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg('')} className="text-rose-400 hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-400 hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Top Header & Status Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
              <Play className="w-5 h-5 text-emerald-400 fill-current" />
              <span>Google Maps Review Worker</span>
            </h2>
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${
              isWorkerRunning
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                : 'bg-slate-800 text-slate-400 border-slate-700'
            }`}>
              <span className={`w-2 h-2 rounded-full ${isWorkerRunning ? 'bg-emerald-400 animate-ping' : 'bg-slate-500'}`}></span>
              <span>{isWorkerRunning ? 'Worker Aktif Berjalan' : 'Worker Siaga (Idle)'}</span>
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Jalankan tugas ulasan otomatis menggunakan sesi cookie yang sudah diautentikasi tanpa intervensi manual.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isWorkerRunning ? (
            <button
              onClick={handleStopWorker}
              disabled={actionLoading}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 transition-all cursor-pointer shadow-xs inline-flex items-center gap-2 disabled:opacity-50"
            >
              <Square className="w-4 h-4 fill-current" />
              <span>Hentikan Worker</span>
            </button>
          ) : (
            <button
              onClick={handleStartWorker}
              disabled={actionLoading || businesses.length === 0}
              className="px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 transition-all cursor-pointer shadow-md shadow-emerald-950/40 inline-flex items-center gap-2 disabled:opacity-50"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Jalankan Worker Sekarang</span>
            </button>
          )}
        </div>
      </div>

      {/* Main 2-Column Split: Left Controls, Right Live Monitor */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form & Config (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Building2 className="w-4 h-4 text-emerald-400" />
                <span>Target Bisnis Google Maps</span>
              </h3>
              <button
                onClick={() => setShowAddBizModal(true)}
                className="text-xs text-emerald-400 hover:text-emerald-300 font-medium inline-flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Target Baru</span>
              </button>
            </div>

            {businesses.length === 0 ? (
              <div className="p-4 rounded-xl border border-dashed border-slate-800 text-center text-slate-500">
                <MapPin className="w-6 h-6 mx-auto mb-1 opacity-50" />
                <p className="text-xs">Belum ada target bisnis Google Maps.</p>
                <button
                  onClick={() => setShowAddBizModal(true)}
                  className="mt-2 text-xs text-emerald-400 hover:text-emerald-300 font-semibold"
                >
                  Tambah Target Sekarang
                </button>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Pilih Listing Bisnis
                </label>
                <select
                  value={selectedBizId}
                  onChange={(e) => setSelectedBizId(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-hidden focus:border-emerald-500 transition-colors"
                >
                  {businesses.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.queue_count || 0} antrean)
                    </option>
                  ))}
                </select>
                {currentBiz && (
                  <a
                    href={currentBiz.url}
                    target="_blank"
                    rel="noreferrer"
                    className="mt-2 text-[11px] text-slate-400 hover:text-emerald-400 truncate flex items-center gap-1.5 transition-colors"
                  >
                    <ExternalLink className="w-3 h-3 shrink-0" />
                    <span className="truncate">{currentBiz.url}</span>
                  </a>
                )}
              </div>
            )}

            {/* Rating Selector */}
            <div className="pt-2 border-t border-slate-800/80">
              <label className="block text-xs font-medium text-slate-300 mb-2">
                Pilih Rating Bintang
              </label>
              <div className="flex items-center gap-2">
                {[5, 4, 3, 2, 1].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setStarRating(s)}
                    className={`flex-1 py-2 px-1 rounded-xl text-xs font-bold border transition-all flex items-center justify-center gap-1 cursor-pointer ${
                      starRating === s
                        ? 'bg-amber-500/10 border-amber-500/50 text-amber-300 shadow-xs'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <span>{s}</span>
                    <Star className={`w-3.5 h-3.5 ${starRating === s ? 'fill-amber-400 text-amber-400' : 'text-slate-500'}`} />
                  </button>
                ))}
              </div>
            </div>

            {/* Language Selector */}
            <div className="pt-2 border-t border-slate-800/80">
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Bahasa Ulasan
              </label>
              <div className="grid grid-cols-2 gap-2">
                {['Indonesian', 'English'].map((lang) => (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => setSelectedLanguage(lang)}
                    className={`py-2 px-3 rounded-xl text-xs font-semibold border transition-all cursor-pointer text-center ${
                      selectedLanguage === lang
                        ? 'bg-slate-800 border-slate-700 text-white'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    {lang === 'Indonesian' ? 'Bahasa Indonesia' : 'English'}
                  </button>
                ))}
              </div>
            </div>

            {/* Cookie Pool Notice */}
            <div className="pt-2 border-t border-slate-800/80 p-3 rounded-xl bg-slate-950/60 border border-slate-800">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400">Sesi Cookie Siap:</span>
                <span className="font-mono font-bold text-emerald-400">{cookies.length} Akun</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Worker secara otomatis merotasi akun yang memiliki cookie aktif tanpa fallback kata sandi.
              </p>
            </div>

            {/* Run Action Button */}
            <div className="pt-2">
              {isWorkerRunning ? (
                <button
                  onClick={handleStopWorker}
                  disabled={actionLoading}
                  className="w-full py-3 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 transition-all cursor-pointer shadow-md inline-flex items-center justify-center gap-2"
                >
                  <Square className="w-4 h-4 fill-current" />
                  <span>Hentikan Worker</span>
                </button>
              ) : (
                <button
                  onClick={handleStartWorker}
                  disabled={actionLoading || businesses.length === 0}
                  className="w-full py-3 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 transition-all cursor-pointer shadow-md shadow-emerald-950/40 inline-flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Mulai Ulasan Google Maps</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Live Screen & Terminal Log (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Virtual Display :99 Screen Viewer */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Monitor className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Layar Chromium Virtual (Display :99)
                </h3>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                1366x768 Live
              </span>
            </div>

            <div className="relative aspect-video w-full rounded-xl bg-black border border-slate-800 overflow-hidden flex items-center justify-center group">
              <img
                src={selectedBizId ? `/business/${selectedBizId}/chromium-preview.png?t=${streamTs}` : `/api/worker/preview.png?t=${streamTs}`}
                alt="Live Chromium Screen"
                className="w-full h-full object-contain"
                onError={() => setStreamError(true)}
                onLoad={() => setStreamError(false)}
              />
              {streamError && (
                <div className="absolute inset-0 bg-slate-950/90 flex flex-col items-center justify-center p-4 text-center">
                  <Monitor className="w-8 h-8 text-slate-600 mb-2" />
                  <p className="text-xs text-slate-400 font-medium">Layar Chromium Sedang Siaga (Idle)</p>
                  <p className="text-[11px] text-slate-500 mt-1">Layar akan aktif secara otomatis saat worker dijalankan.</p>
                </div>
              )}
            </div>
          </div>

          {/* Terminal Log */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-slate-400" />
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  Terminal Log Worker
                </h3>
              </div>
              <span className="text-[10px] font-mono text-slate-500">Auto-scroll</span>
            </div>

            <div
              ref={terminalRef}
              className="h-56 p-3 rounded-xl bg-slate-950 border border-slate-800/80 font-mono text-[11px] text-slate-300 overflow-y-auto space-y-1"
            >
              {activeLogs.length === 0 ? (
                <p className="text-slate-600 italic">Menunggu aktivitas worker...</p>
              ) : (
                activeLogs.map((log, idx) => (
                  <div key={idx} className="flex items-start gap-2 leading-relaxed">
                    <span className="text-slate-600 select-none shrink-0">{log.created_at?.slice(11, 19)}</span>
                    <span className={
                      log.level === 'error'
                        ? 'text-rose-400 font-bold'
                        : log.level === 'warning'
                        ? 'text-amber-400'
                        : log.level === 'success'
                        ? 'text-emerald-400'
                        : 'text-slate-300'
                    }>
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modal: Tambah Target Bisnis Baru */}
      {showAddBizModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-5 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Building2 className="w-4 h-4 text-emerald-400" />
                <span>Tambah Target Profil Google Maps</span>
              </h3>
              <button
                onClick={() => setShowAddBizModal(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddBizSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Nama Bisnis / Tempat
                </label>
                <input
                  type="text"
                  required
                  placeholder="contoh: Kedai Kopi Nusantara"
                  value={bizForm.name}
                  onChange={(e) => setBizForm({ ...bizForm, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-emerald-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  URL Google Maps (Link Tempat)
                </label>
                <input
                  type="url"
                  required
                  placeholder="https://maps.app.goo.gl/... atau https://www.google.com/maps/place/..."
                  value={bizForm.url}
                  onChange={(e) => setBizForm({ ...bizForm, url: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-emerald-500 transition-colors"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddBizModal(false)}
                  className="px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-slate-800/60 transition-colors"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition-all cursor-pointer"
                >
                  Simpan Target
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
