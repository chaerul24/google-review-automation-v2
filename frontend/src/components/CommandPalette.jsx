import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Building2,
  Users,
  Cookie,
  Plus,
  Monitor,
  LogOut,
  X,
  ExternalLink,
  ChevronRight,
  Bot,
  Sparkles,
  Clock,
} from 'lucide-react';
import { api } from '../api/client';

export default function CommandPalette({ isOpen, onClose, onOpenPiP, onOpenPersona }) {
  const [query, setQuery] = useState('');
  const [businesses, setBusinesses] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    if (!isOpen) {
      setQuery('');
      return;
    }
    const load = async () => {
      try {
        const res = await api.getDashboard();
        if (res && res.businesses) {
          setBusinesses(res.businesses);
        }
      } catch (err) {
        console.debug('Failed to load businesses for palette:', err);
      }
    };
    load();
  }, [isOpen]);

  // Handle ESC key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filteredBiz = businesses.filter((b) =>
    b.name.toLowerCase().includes(query.toLowerCase()) ||
    (b.url || '').toLowerCase().includes(query.toLowerCase())
  );

  const actions = [
    {
      title: 'Target Bisnis Maps',
      desc: 'Lihat seluruh daftar lokasi bisnis Google Maps',
      icon: Building2,
      color: 'text-indigo-400',
      action: () => { navigate('/dashboard'); onClose(); },
    },
    {
      title: 'Studio Persona & Template AI',
      desc: 'Generator ulasan batch multi-persona dengan keyword targeted',
      icon: Sparkles,
      color: 'text-purple-400',
      action: () => { navigate('/review-studio'); onClose(); },
    },
    {
      title: 'Jadwal & Drip Campaign Engine',
      desc: 'Atur jeda distribusi anti-spam dan jam aktif ulasan harian',
      icon: Clock,
      color: 'text-teal-400',
      action: () => { navigate('/campaigns'); onClose(); },
    },
    {
      title: 'Live Worker Console',
      desc: 'Pantau layar virtual Chromium :99 dan terminal log real-time',
      icon: Monitor,
      color: 'text-emerald-400',
      action: () => { navigate('/live-monitor'); onClose(); },
    },
    {
      title: 'Pool Akun Google',
      desc: 'Kelola akun email, kredensial, dan status unflag',
      icon: Users,
      color: 'text-sky-400',
      action: () => { navigate('/dashboard?tab=emails'); onClose(); },
    },
    {
      title: 'Google Cookie Sessions',
      desc: 'Kelola sesi browser mandiri tanpa fallback password',
      icon: Cookie,
      color: 'text-amber-400',
      action: () => { navigate('/dashboard?tab=cookies'); onClose(); },
    },
  ];

  const filteredActions = actions.filter((a) =>
    a.title.toLowerCase().includes(query.toLowerCase()) ||
    a.desc.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-start justify-center pt-20 p-4">
      <div className="bg-[#0f1420] border border-slate-800 rounded-2xl w-full max-w-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
        {/* Search Input Bar */}
        <div className="p-4 border-b border-slate-800 flex items-center gap-3 bg-slate-950">
          <Search className="w-4 h-4 text-slate-400 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Cari perintah atau nama bisnis... (ESC untuk tutup)"
            autoFocus
            className="w-full bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none font-medium"
          />
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-[60vh] overflow-y-auto p-3 space-y-4 no-scrollbar">
          {/* Quick Actions */}
          {filteredActions.length > 0 && (
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-3 pb-1 block">
                Menu & Fitur Cepat
              </span>
              <div className="space-y-1">
                {filteredActions.map((act, i) => {
                  const Icon = act.icon;
                  return (
                    <button
                      key={i}
                      onClick={act.action}
                      className="w-full p-2.5 rounded-xl hover:bg-slate-800/80 text-left flex items-center gap-3 transition-colors cursor-pointer group"
                    >
                      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 group-hover:border-slate-700">
                        <Icon className={`w-4 h-4 ${act.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-bold text-white block group-hover:text-emerald-300 transition-colors">
                          {act.title}
                        </span>
                        <span className="text-[11px] text-slate-400 truncate block">
                          {act.desc}
                        </span>
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-500 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Business Targets */}
          {filteredBiz.length > 0 && (
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 px-3 pb-1 block">
                Target Bisnis Google Maps ({filteredBiz.length})
              </span>
              <div className="space-y-1">
                {filteredBiz.map((biz) => (
                  <button
                    key={biz.id}
                    onClick={() => { navigate(`/business/${biz.id}`); onClose(); }}
                    className="w-full p-2.5 rounded-xl hover:bg-slate-800/80 text-left flex items-center gap-3 transition-colors cursor-pointer group"
                  >
                    <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                      <Building2 className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className="text-xs font-bold text-white block truncate group-hover:text-indigo-300">
                        {biz.name}
                      </span>
                      <span className="text-[11px] text-slate-400 truncate block font-mono">
                        {biz.url}
                      </span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-mono font-bold">
                      {biz.reviewed_count || 0} reviews
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {filteredActions.length === 0 && filteredBiz.length === 0 && (
            <div className="p-8 text-center text-slate-500 text-xs">
              Tidak ada hasil yang cocok dengan "{query}".
            </div>
          )}
        </div>

        {/* Footer Shortcut hint */}
        <div className="p-2.5 px-4 bg-slate-950/80 border-t border-slate-800 text-[10px] font-mono text-slate-400 flex items-center justify-between">
          <span>Tekan <kbd className="px-1 py-0.5 rounded bg-slate-800 text-slate-300">ESC</kbd> untuk menutup</span>
          <span>AutoMap Bot Command Engine</span>
        </div>
      </div>
    </div>
  );
}
