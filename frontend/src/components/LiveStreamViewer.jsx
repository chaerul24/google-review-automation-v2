import React, { useState } from 'react';
import { Play, Pause, RefreshCw, Eye, EyeOff, Monitor } from 'lucide-react';

export default function LiveStreamViewer({ businessId }) {
  const [isPlaying, setIsPlaying] = useState(true);
  const [key, setKey] = useState(Date.now());
  const [streamError, setStreamError] = useState(false);

  const streamUrl = `/business/${businessId}/chromium-stream.mjpg?t=${key}`;
  const previewUrl = `/business/${businessId}/chromium-preview.png?t=${key}`;

  const handleRefresh = () => {
    setKey(Date.now());
    setStreamError(false);
  };

  return (
    <div className="bg-slate-900/80 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
      <div className="p-3.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Monitor className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold text-white tracking-wide">Live Chromium Screen</span>
          <span className="text-[10px] bg-emerald-500/10 text-emerald-300 font-mono px-2 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Display :99
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title={isPlaying ? 'Pause Stream' : 'Resume Stream'}
          >
            {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 text-emerald-400" />}
          </button>
          <button
            onClick={handleRefresh}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="Reload Screen"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="relative aspect-video bg-black flex items-center justify-center overflow-hidden">
        {isPlaying && !streamError ? (
          <img
            src={streamUrl}
            alt="Live Chromium Stream"
            className="w-full h-full object-contain"
            onError={() => setStreamError(true)}
          />
        ) : (
          <div className="text-center p-6">
            <img
              src={previewUrl}
              alt="Chromium Snapshot"
              className="max-h-60 mx-auto rounded-lg border border-slate-800 object-contain mb-3"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <p className="text-xs text-slate-400 font-medium">
              {isPlaying ? 'Menunggu frame browser dari virtual display :99...' : 'Stream dipause.'}
            </p>
            <button
              onClick={handleRefresh}
              className="mt-3 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white inline-flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Muat Ulang Layar
            </button>
          </div>
        )}
      </div>

      <div className="px-4 py-2 bg-slate-950/40 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
        <span>Menampilkan aktivitas browser di server secara real-time via ffmpeg x11grab</span>
        <a
          href={previewUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-400 hover:underline flex items-center gap-1"
        >
          <Eye className="w-3 h-3" /> Snapshot Asli
        </a>
      </div>
    </div>
  );
}
