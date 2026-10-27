import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  MapPin,
  Users,
  Cookie,
  Monitor,
  LogOut,
  MessageSquare,
  Clock,
  Search,
  Sparkles,
  RefreshCw,
  Menu,
  X,
  ExternalLink,
  Bot,
  Layers,
  ChevronDown,
} from 'lucide-react';
import { api } from '../api/client';

export default function Navbar({
  title,
  subtitle,
  onOpenCommandPalette,
  onTogglePiP,
  isPiPOpen = false,
  onOpenPersona,
  onRefresh,
  isRefreshing = false,
  actions,
  onLogout,
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await api.logout();
      if (onLogout) onLogout();
      navigate('/login');
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  const navItems = [
    {
      to: '/cookies',
      label: 'Kelola Cookie',
      icon: Cookie,
      badge: 'CDP',
    },
    {
      to: '/worker',
      label: 'Jalankan Worker',
      icon: Monitor,
      live: true,
    },
  ];

  const isItemActive = (item) => {
    return location.pathname === item.to || location.pathname.startsWith(`${item.to}/`);
  };

  return (
    <nav className="sticky top-0 z-40 bg-[#080b11]/90 backdrop-blur-md border-b border-slate-800/80 transition-colors">
      {/* Tier 1: Main Web App Navigation Bar */}
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 gap-3">
          {/* Left: Brand + Desktop Navigation Tabs */}
          <div className="flex items-center gap-6 lg:gap-8 min-w-0">
            {/* Brand Logo */}
            <NavLink
              to="/worker"
              className="flex items-center gap-2.5 shrink-0 group focus:outline-hidden"
            >
              <div className="w-8 h-8 rounded-xl bg-slate-900 border border-slate-700/80 group-hover:border-slate-600 flex items-center justify-center text-emerald-400 transition-all shadow-xs">
                <Bot className="w-4 h-4 transition-transform group-hover:scale-110" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-extrabold tracking-tight text-white font-mono">
                  AutoMap<span className="text-emerald-400">Bot</span>
                </span>
                <span className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-slate-900 text-slate-400 border border-slate-800">
                  :99
                </span>
              </div>
            </NavLink>

            {/* Desktop Navigation Links */}
            <div className="hidden lg:flex items-center gap-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isItemActive(item);
                return (
                  <NavLink
                    key={item.label}
                    to={item.to}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all relative ${
                      active
                        ? 'text-white bg-slate-800/90 shadow-xs border border-slate-700/80'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${active ? 'text-emerald-400' : 'text-slate-500'}`} />
                    <span>{item.label}</span>
                    {item.live && (
                      <span className="relative flex h-2 w-2 ml-0.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                      </span>
                    )}
                    {item.badge && !item.live && (
                      <span className={`text-[10px] font-mono px-1 py-0.2 rounded font-medium ${
                        active ? 'bg-slate-700 text-slate-200' : 'bg-slate-900 text-slate-500'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </div>
          </div>

          {/* Right: Search, Live Stream PiP, Generator, User */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
            {/* Quick Command Palette Button */}
            {onOpenCommandPalette && (
              <button
                onClick={onOpenCommandPalette}
                className="hidden md:flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 transition-all text-xs font-medium cursor-pointer shadow-xs"
                title="Cari perintah atau bisnis (Ctrl+K)"
              >
                <Search className="w-3.5 h-3.5 text-slate-500" />
                <span className="hidden xl:inline text-[11px]">Cari...</span>
                <kbd className="text-[10px] bg-slate-900 border border-slate-800 px-1 py-0.2 rounded text-slate-400 font-mono">⌘K</kbd>
              </button>
            )}

            {/* Quick AI Persona Generator Modal Toggle */}
            {onOpenPersona && (
              <button
                onClick={onOpenPersona}
                className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800/80 text-indigo-300 hover:text-white border border-indigo-500/20 hover:border-indigo-500/40 transition-all text-xs font-medium cursor-pointer"
                title="Buat Variasi Ulasan AI"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span className="hidden md:inline">AI Studio</span>
              </button>
            )}

            {/* Live Chromium :99 PiP Screen Viewer Toggle */}
            {onTogglePiP && (
              <button
                onClick={onTogglePiP}
                className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition-all cursor-pointer shadow-xs ${
                  isPiPOpen
                    ? 'bg-slate-800 text-emerald-300 border-emerald-500/40'
                    : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
                title="Tampilkan layar virtual Chromium Display :99"
              >
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <Monitor className="w-3.5 h-3.5" />
                <span className="font-mono text-[11px]">Live :99</span>
              </button>
            )}

            {/* User Profile / Logout Button */}
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-all text-xs font-medium cursor-pointer"
                aria-label="Menu Pengguna"
              >
                <div className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] font-bold text-slate-300">
                  A
                </div>
                <span className="hidden sm:inline font-mono text-[11px]">Admin</span>
                <ChevronDown className="w-3 h-3 text-slate-500" />
              </button>

              {userMenuOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setUserMenuOpen(false)}
                  ></div>
                  <div className="absolute right-0 mt-1.5 w-48 rounded-xl bg-slate-900 border border-slate-800 shadow-xl py-1 z-50 animate-in fade-in zoom-in-95">
                    <div className="px-3 py-2 border-b border-slate-800/80">
                      <p className="text-xs font-bold text-white">Administrator</p>
                      <p className="text-[11px] font-mono text-slate-400 truncate">admin@automap.local</p>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 transition-colors text-left cursor-pointer"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Keluar (Logout)</span>
                    </button>
                  </div>
                </>
              )}
            </div>

            {/* Mobile Menu Toggle Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors shrink-0"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-slate-800/80 bg-slate-950/95 backdrop-blur-md px-4 py-3 space-y-1 animate-in fade-in slide-in-from-top-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isItemActive(item);
            return (
              <NavLink
                key={item.label}
                to={item.to}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  active
                    ? 'text-white bg-slate-800/90 border border-slate-700/80'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${active ? 'text-emerald-400' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </div>
                {item.live && (
                  <span className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.5 rounded">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                    Live
                  </span>
                )}
                {item.badge && !item.live && (
                  <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-1.5 py-0.5 rounded">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </div>
      )}

      {/* Tier 2: Context Subheader (Title, Subtitle & Page Actions) */}
      {(title || actions || onRefresh) && (
        <div className="border-t border-slate-800/50 bg-[#070a0f]/60 px-4 sm:px-6 lg:px-8 py-2">
          <div className="max-w-[1600px] mx-auto flex items-center justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-xs sm:text-sm font-bold text-slate-200 tracking-tight flex items-center gap-2 truncate">
                <span>{title}</span>
              </h1>
              {subtitle && (
                <p className="text-[11px] text-slate-400 truncate hidden sm:block">
                  {subtitle}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {actions}
              {onRefresh && (
                <button
                  onClick={onRefresh}
                  disabled={isRefreshing}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition-all disabled:opacity-50 cursor-pointer shadow-xs"
                  title="Muat ulang data"
                >
                  <RefreshCw className={`w-3 h-3 text-slate-400 ${isRefreshing ? 'animate-spin text-emerald-400' : ''}`} />
                  <span className="hidden sm:inline text-[11px]">Refresh</span>
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}
