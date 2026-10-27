import React, { useState, useEffect } from 'react';
import {
  Monitor,
  X,
  Maximize2,
  Minimize2,
  RefreshCw,
  Play,
  Pause,
  ExternalLink,
} from 'lucide-react';

export default function FloatingLiveViewer({ isOpen, onClose }) {
  const [minimized, setMinimized] = useState(false);
  const [key, setKey] = useState(Date.now());
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Auto-refresh preview snapshot every 3 seconds when open and autoRefresh is true
  useEffect(() => {
    if (!isOpen || minimized || !autoRefresh) return;
    const interval = setInterval(() => {
      setKey(Date.now());
    }, 3000);
    return () => clearInterval(interval);
  }, [isOpen, minimized, autoRefresh]);

  if (!isOpen) return null;

  const previewUrl = `/api/worker/preview.png?t=${key}`;

  return (
    <div
      className={`fixed z-40 transition-all duration-300 ${
        minimized
          ? 'bottom-5 right-5'
          : 'bottom-5 right-5 w-80 sm:w-96 shadow-2xl'
      }`}
    >
      {minimized ? (
        // Minimized floating pill
        <button
          onClick={() => setMinimized(false)}
          className="flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-slate-900/95 border border-emerald-500/40 text-white shadow-2xl backdrop-blur-xl hover:border-emerald-400 transition-all cursor-pointer group"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <Monitor className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold font-mono">LIVE :99 Worker</span>
          <Maximize2 className="w-3.5 h-3.5 text-slate-400 group-hover:text-white" />
        </button>
      ) : (
        // Expanded floating window
        <div className="bg-slate-900/95 border border-slate-700/80 rounded-2xl overflow-hidden backdrop-blur-xl shadow-2xl ring-1 ring-black/40">
          {/* PiP Header */}
          <div className="p-3 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <Monitor className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-xs font-bold text-white tracking-wide">Chromium Live Screen</span>
              <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-300 px-1.5 py-0.2 rounded border border-emerald-500/20">
                :99
              </span>
            </div>

            {/* Header Controls */}
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`p-1 rounded text-slate-400 hover:text-white transition-colors ${
                  autoRefresh ? 'text-emerald-400' : ''
                }`}
                title={autoRefresh ? 'Auto-refresh Aktif (3s)' : 'Auto-refresh Dijeda'}
              >
                {autoRefresh ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
              </button>
              <button
                onClick={() => setKey(Date.now())}
                className="p-1 rounded text-slate-400 hover:text-white transition-colors"
                title="Refresh Snapshot Sekarang"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
              <button
                onClick={() => setMinimized(true)}
                className="p-1 rounded text-slate-400 hover:text-white transition-colors"
                title="Kecilkan ke floating pill"
              >
                <Minimize2 className="w-3 h-3" />
              </button>
              <button
                onClick={onClose}
                className="p-1 rounded text-slate-400 hover:text-rose-400 transition-colors"
                title="Tutup Monitor"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          </div>

          {/* Screen Display Frame */}
          <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
            <img
              src={previewUrl}
              alt="Live Screen Chromium"
              className="w-full h-full object-contain"
              onError={(e) => {
                e.target.style.opacity = '0.5';
              }}
            />
          </div>

          {/* PiP Footer Info */}
          <div className="p-2 px-3 bg-slate-950/60 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-400">
            <span>Server Virtual Display (Xvfb)</span>
            <span className="text-emerald-400">● 1366x768 Real-time</span>
          </div>
        </div>
      )}
    </div>
  );
}
