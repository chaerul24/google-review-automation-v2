import React from 'react';
import { Menu, ShieldCheck, RefreshCw, Monitor, Search, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Header({
  title,
  subtitle,
  onRefresh,
  isRefreshing = false,
  onOpenSidebar,
  onOpenCommandPalette,
  onTogglePiP,
  isPiPOpen = false,
  actions,
}) {
  return (
    <header className="h-16 border-b border-slate-800/70 bg-[#0a0d14]/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 transition-colors">
      {/* Left: Mobile Toggle & Page Title */}
      <div className="flex items-center gap-3 sm:gap-4 min-w-0">
        {onOpenSidebar && (
          <button
            onClick={onOpenSidebar}
            className="lg:hidden p-2 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-300 hover:text-white hover:bg-slate-700/80 transition-colors shrink-0"
            aria-label="Buka menu navigasi"
          >
            <Menu className="w-5 h-5" />
          </button>
        )}

        <div className="min-w-0">
          <h1 className="text-sm sm:text-base font-bold text-white tracking-tight flex items-center gap-2 truncate">
            <span>{title}</span>
          </h1>
          {subtitle && (
            <p className="text-[11px] sm:text-xs text-slate-400 truncate hidden xs:block font-medium">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      {/* Right: Search, Live Screen, Actions, Refresh */}
      <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
        {onOpenCommandPalette && (
          <button
            onClick={onOpenCommandPalette}
            className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 transition-all text-xs font-medium cursor-pointer shadow-xs"
            title="Cari perintah atau bisnis (Ctrl+K)"
          >
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden lg:inline text-[11px]">Cari perintah / bisnis...</span>
            <kbd className="text-[10px] bg-slate-950 border border-slate-800 px-1.5 py-0.5 rounded text-slate-400 font-mono">⌘K</kbd>
          </button>
        )}

        {onTogglePiP && (
          <button
            onClick={onTogglePiP}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all cursor-pointer shadow-xs ${
              isPiPOpen
                ? 'bg-slate-800 text-emerald-300 border-emerald-500/40 shadow-xs'
                : 'bg-slate-900 hover:bg-slate-850 text-slate-300 border-slate-800 hover:border-slate-700'
            }`}
            title="Tampilkan layar virtual Chromium Display :99"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <Monitor className="w-3.5 h-3.5" />
            <span className="hidden sm:inline font-mono">Live :99</span>
          </button>
        )}

        {actions}

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition-all disabled:opacity-50 cursor-pointer shadow-xs"
            title="Muat ulang data"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-slate-400 ${isRefreshing ? 'animate-spin text-indigo-400' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
        )}

        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-mono bg-slate-900 text-slate-300 border border-slate-800">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          <span className="truncate">autobotix.my.id</span>
        </div>
      </div>
    </header>
  );
}
