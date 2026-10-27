import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  MapPin,
  Users,
  Cookie,
  Monitor,
  LogOut,
  ChevronRight,
  X,
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquare,
  Clock,
  Compass,
} from 'lucide-react';
import { api } from '../api/client';

export default function Sidebar({
  isOpen = false,
  onClose,
  collapsed = false,
  onToggleCollapse,
  onLogout,
}) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await api.logout();
      if (onLogout) onLogout();
      navigate('/login');
    } catch (err) {
      console.error('Logout error:', err);
    }
  };

  const handleLinkClick = () => {
    if (onClose) onClose();
  };

  const navSections = [
    {
      title: 'Automasi Ulasan',
      items: [
        {
          to: '/dashboard',
          tab: 'businesses',
          label: 'Target Bisnis Maps',
          icon: MapPin,
          badge: 'Listing',
        },
        {
          to: '/review-studio',
          label: 'Studio Variasi Ulasan',
          icon: MessageSquare,
          badge: 'Editor',
        },
        {
          to: '/campaigns',
          label: 'Jadwal & Drip Engine',
          icon: Clock,
          badge: 'Drip',
        },
        {
          to: '/live-monitor',
          label: 'Live Worker Console',
          icon: Monitor,
          badge: ':99',
        },
      ],
    },
    {
      title: 'Akun & Sesi',
      items: [
        {
          to: '/dashboard?tab=emails',
          tab: 'emails',
          label: 'Pool Akun Google',
          icon: Users,
          badge: 'Gmail',
        },
        {
          to: '/dashboard?tab=cookies',
          tab: 'cookies',
          label: 'Sesi Cookie Browser',
          icon: Cookie,
          badge: 'CDP',
        },
      ],
    },
  ];

  const isItemActive = (item) => {
    if (item.tab) {
      if (location.pathname === '/dashboard') {
        const params = new URLSearchParams(location.search);
        const currentTab = params.get('tab') || 'businesses';
        return currentTab === item.tab;
      }
      return false;
    }
    return location.pathname === item.to;
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-black/70 backdrop-blur-xs z-40 lg:hidden transition-opacity duration-200"
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:sticky top-0 inset-y-0 left-0 z-50 h-screen bg-[#0a0d14] border-r border-slate-800/70 flex flex-col justify-between shrink-0 transition-all duration-200 ease-out select-none ${
          collapsed ? 'lg:w-18' : 'w-72 lg:w-64'
        } ${
          isOpen ? 'translate-x-0 shadow-2xl shadow-black/80' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full min-h-0">
          {/* Brand Header */}
          <div
            className={`h-16 border-b border-slate-800/70 flex items-center justify-between transition-all ${
              collapsed ? 'lg:px-3 lg:justify-center' : 'px-5'
            }`}
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-xl bg-slate-900 border border-slate-700/80 flex items-center justify-center text-emerald-400 shadow-inner shrink-0">
                <Compass className="w-5 h-5 text-emerald-400" />
              </div>
              {!collapsed && (
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-sm tracking-tight text-white truncate">AutoMap</span>
                    <span className="text-[10px] bg-slate-800 text-slate-300 font-mono px-1.5 py-0.5 rounded border border-slate-700/60 font-semibold">
                      v2.4
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 truncate font-medium">Google Maps Engine</p>
                </div>
              )}
            </div>

            {/* Actions: Mobile Close & Desktop Collapse */}
            <div className="flex items-center gap-1">
              <button
                onClick={onClose}
                className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
                title="Tutup menu"
                aria-label="Tutup menu"
              >
                <X className="w-5 h-5" />
              </button>

              {onToggleCollapse && (
                <button
                  onClick={onToggleCollapse}
                  className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors"
                  title={collapsed ? 'Perluas sidebar' : 'Ciutkan sidebar'}
                  aria-label={collapsed ? 'Perluas sidebar' : 'Ciutkan sidebar'}
                >
                  {collapsed ? (
                    <PanelLeftOpen className="w-4 h-4 text-slate-400" />
                  ) : (
                    <PanelLeftClose className="w-4 h-4 text-slate-400" />
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5 no-scrollbar">
            {navSections.map((sec) => (
              <div key={sec.title} className="space-y-1">
                {!collapsed && (
                  <div className="px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    {sec.title}
                  </div>
                )}

                {sec.items.map((item) => {
                  const Icon = item.icon;
                  const active = isItemActive(item);

                  return (
                    <NavLink
                      key={item.label}
                      to={item.to}
                      onClick={handleLinkClick}
                      title={collapsed ? item.label : undefined}
                      className={`group flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs transition-colors duration-150 relative ${
                        collapsed ? 'justify-center px-2 py-2.5' : ''
                      } ${
                        active
                          ? 'bg-slate-800/80 text-white font-semibold shadow-xs border border-slate-700/60'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30 font-medium'
                      }`}
                    >
                      <Icon
                        className={`w-4 h-4 shrink-0 transition-colors ${
                          active ? 'text-emerald-400' : 'text-slate-400 group-hover:text-slate-200'
                        }`}
                      />
                      {!collapsed && (
                        <>
                          <span className="truncate flex-1">{item.label}</span>
                          {item.badge && (
                            <span
                              className={`text-[10px] px-1.5 py-0.5 rounded font-mono transition-colors ${
                                active
                                  ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                                  : 'bg-slate-850 text-slate-500 border border-slate-800'
                              }`}
                            >
                              {item.badge}
                            </span>
                          )}
                          <ChevronRight
                            className={`w-3.5 h-3.5 opacity-30 shrink-0 group-hover:opacity-70 group-hover:translate-x-0.5 transition-all ${
                              active ? 'opacity-80 text-emerald-400' : ''
                            }`}
                          />
                        </>
                      )}
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </nav>

          {/* Footer Info & Logout */}
          <div className="p-3 border-t border-slate-800/70 bg-[#070a10] shrink-0">
            {!collapsed && (
              <div className="mb-2">
                <div className="flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800/60">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="relative flex h-2 w-2 shrink-0">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span className="text-[11px] font-mono text-slate-300 truncate">Display :99</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">1366x768</span>
                </div>
              </div>
            )}

            <button
              onClick={handleLogout}
              title={collapsed ? 'Keluar' : undefined}
              className={`w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-rose-300 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 transition-all cursor-pointer ${
                collapsed ? 'px-2' : ''
              }`}
            >
              <LogOut className="w-4 h-4 shrink-0" />
              {!collapsed && <span>Keluar</span>}
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}
