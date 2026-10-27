import React, { useState, useEffect, useRef } from 'react';
import {
  Monitor,
  Terminal,
  RefreshCw,
  Play,
  Pause,
  Square,
  Activity,
  Copy,
  Check,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../api/client';

export default function LiveWorkerMonitor() {
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshIntervalSec, setRefreshIntervalSec] = useState(3);
  const [isPaused, setIsPaused] = useState(false);
  const [imageKey, setImageKey] = useState(Date.now());
  const [logFilter, setLogFilter] = useState('all');
  const [copiedLogs, setCopiedLogs] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [notification, setNotification] = useState({ type: '', message: '' });

  const terminalRef = useRef(null);

  const fetchStatus = async () => {
    try {
      const res = await api.getWorkerStatus();
      if (res) {
        setStatusData(res);
      }
    } catch (err) {
      console.debug('Failed to fetch worker status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(() => {
      fetchStatus();
      if (!isPaused) {
        setImageKey(Date.now());
      }
    }, refreshIntervalSec * 1000);

    return () => clearInterval(interval);
  }, [refreshIntervalSec, isPaused]);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [statusData?.system_status?.recent_logs]);

  const handleEmergencyStop = async () => {
    if (!confirm('Hentikan seluruh proses worker Chromium yang sedang aktif?')) return;
    setStopping(true);
    try {
      const res = await api.emergencyStopWorker();
      setNotification({
        type: 'info',
        message: res.message || 'Sinyal penghentian darurat dikirim ke worker.',
      });
      fetchStatus();
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Gagal menghentikan worker.',
      });
    } finally {
      setStopping(false);
    }
  };

  const handleCopyLogs = () => {
    const logs = statusData?.system_status?.recent_logs || [];
    const text = logs.map((l) => `[${l.created_at}] [${l.level?.toUpperCase()}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopiedLogs(true);
    setTimeout(() => setCopiedLogs(false), 2000);
  };

  const allLogs = statusData?.system_status?.recent_logs || [];
  const filteredLogs = allLogs.filter((l) => {
    if (logFilter === 'error') return l.level === 'error';
    if (logFilter === 'warning') return l.level === 'warning';
    if (logFilter === 'info') return l.level === 'info';
    return true;
  });

  const displayActive = statusData?.display_99_active ?? true;
  const workerRunning = statusData?.worker_running ?? false;
  const activeJob = statusData?.system_status?.active_job;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Alert Notifications */}
      {notification.message && (
        <div
          className={`p-3.5 rounded-xl text-xs flex items-center justify-between border transition-all ${
            notification.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/20 text-rose-300'
              : 'bg-slate-800 border-slate-700 text-slate-300'
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
            ✕
          </button>
        </div>
      )}

      {/* Clean Header Bar */}
      <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
              Virtual Display & Worker Console
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Pemantauan Layar & Worker Aktif
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Monitor real-time sesi browser Chromium pada display virtual Xvfb :99. Pantau interaksi elemen Maps dan log proses worker secara langsung.
          </p>
        </div>

        {/* Emergency Stop Action */}
        <div className="flex items-center gap-2.5 shrink-0 self-start md:self-auto">
          <button
            onClick={handleEmergencyStop}
            disabled={stopping}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600/90 hover:bg-rose-600 text-white flex items-center gap-2 transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>{stopping ? 'Menghentikan...' : 'Stop Worker'}</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Display Virtual</span>
          <div className="flex items-center gap-2 mt-2">
            <span className={`w-2.5 h-2.5 rounded-full ${displayActive ? 'bg-emerald-400' : 'bg-rose-400'}`} />
            <p className="text-xl font-bold text-white font-mono">
              {displayActive ? ':99 Aktif' : 'Offline'}
            </p>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Xvfb 1366x768 framebuffer</p>
        </div>

        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Status Proses</span>
          <div className="flex items-center gap-2 mt-2">
            <span className={`w-2.5 h-2.5 rounded-full ${workerRunning ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`} />
            <p className="text-xl font-bold text-white">
              {workerRunning ? 'Berjalan' : 'Siaga (Idle)'}
            </p>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {activeJob ? activeJob.business_name : 'Menunggu tugas'}
          </p>
        </div>

        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Selesai Hari Ini</span>
          <p className="text-3xl font-extrabold text-emerald-400 mt-2 font-mono">
            {statusData?.system_status?.total_reviewed_today || 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Ulasan berhasil terbit</p>
        </div>

        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Antrean Tertunda</span>
          <p className="text-3xl font-extrabold text-slate-200 mt-2 font-mono">
            {statusData?.system_status?.total_pending || 0}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">Ulasan pending</p>
        </div>
      </div>

      {/* Main Grid: Screen Frame & Terminal */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 cols): Chromium Bezel */}
        <div className="lg:col-span-7 space-y-4">
          <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xs">
            {/* Window Bar (macOS/Linux style) */}
            <div className="px-4 py-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-700" />
                </div>
                <span className="text-xs font-mono font-medium text-slate-400">
                  chromium-session [display :99]
                </span>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-2">
                <select
                  value={refreshIntervalSec}
                  onChange={(e) => setRefreshIntervalSec(Number(e.target.value))}
                  className="px-2 py-1 rounded bg-slate-900 border border-slate-700/80 text-[11px] text-slate-300 font-mono cursor-pointer"
                  title="Interval refresh"
                >
                  <option value={1}>1 dtk</option>
                  <option value={3}>3 dtk</option>
                  <option value={5}>5 dtk</option>
                </select>

                <button
                  onClick={() => setIsPaused(!isPaused)}
                  className={`p-1 rounded border transition-colors cursor-pointer ${
                    isPaused
                      ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                      : 'bg-slate-900 text-slate-300 border-slate-700 hover:text-white'
                  }`}
                  title={isPaused ? 'Lanjutkan' : 'Jeda'}
                >
                  {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
                </button>

                <button
                  onClick={() => setImageKey(Date.now())}
                  className="p-1 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700 transition-colors cursor-pointer"
                  title="Refresh manual"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Viewport */}
            <div className="bg-black aspect-video relative flex items-center justify-center overflow-hidden">
              <img
                src={`/api/worker/preview.png?t=${imageKey}`}
                alt="Live Chromium :99 Screen"
                className="w-full h-full object-contain"
                onError={(e) => {
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
                onLoad={(e) => {
                  e.target.style.display = 'block';
                  if (e.target.nextSibling) e.target.nextSibling.style.display = 'none';
                }}
              />
              <div
                style={{ display: 'none' }}
                className="absolute inset-0 flex-col items-center justify-center text-slate-500 space-y-2"
              >
                <Monitor className="w-8 h-8 opacity-40" />
                <span className="text-xs font-mono">Memuat snapshot layar Chromium...</span>
              </div>
            </div>

            <div className="px-4 py-2.5 bg-slate-950 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400 font-mono">
              <span>Resolusi: 1366x768 (Xvfb)</span>
              <span>Diperbarui: {statusData?.timestamp || 'Baru saja'}</span>
            </div>
          </div>
        </div>

        {/* Right Column (5 cols): Developer Terminal */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xs flex flex-col h-[500px]">
            {/* Window Bar */}
            <div className="px-4 py-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-slate-400" />
                <span className="text-xs font-mono font-medium text-slate-300">process.log</span>
              </div>

              <button
                onClick={handleCopyLogs}
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                title="Salin seluruh log"
              >
                {copiedLogs ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>

            {/* Filter Tabs */}
            <div className="px-3 py-2 bg-slate-950/80 border-b border-slate-800/60 flex items-center gap-1">
              {['all', 'info', 'warning', 'error'].map((f) => (
                <button
                  key={f}
                  onClick={() => setLogFilter(f)}
                  className={`px-2.5 py-0.5 rounded text-[10px] font-mono uppercase transition-colors cursor-pointer ${
                    logFilter === f
                      ? 'bg-slate-800 text-white font-semibold'
                      : 'text-slate-400 hover:bg-slate-850 hover:text-slate-300'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>

            {/* Terminal Body */}
            <div
              ref={terminalRef}
              className="flex-1 p-3.5 bg-slate-950 font-mono text-[11px] overflow-y-auto space-y-1"
            >
              {filteredLogs.length === 0 ? (
                <div className="text-slate-600 italic py-4 text-center">
                  Belum ada catatan log aktivitas.
                </div>
              ) : (
                filteredLogs.map((log) => (
                  <div key={log.id} className="leading-relaxed flex items-start gap-2">
                    <span className="text-slate-600 shrink-0 text-[10px]">
                      {log.created_at ? log.created_at.split(' ')[1] : ''}
                    </span>
                    <span
                      className={`font-semibold shrink-0 text-[10px] uppercase ${
                        log.level === 'error'
                          ? 'text-rose-400'
                          : log.level === 'warning'
                          ? 'text-amber-400'
                          : 'text-emerald-400'
                      }`}
                    >
                      [{log.level}]
                    </span>
                    <span className="text-slate-300 break-words flex-1">
                      {log.business_name ? (
                        <span className="text-slate-400 mr-1.5 font-bold">[{log.business_name}]</span>
                      ) : null}
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
