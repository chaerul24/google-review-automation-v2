import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, XCircle, ShieldCheck } from 'lucide-react';

export default function StatusBadge({ status, label }) {
  const norm = String(status || '').toLowerCase();

  if (norm === 'reviewed' || norm === 'healthy' || norm === 'active' || norm === 'valid' || norm === 'success') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
        <span>{label || 'Selesai / Aktif'}</span>
      </span>
    );
  }

  if (norm === 'reviewing' || norm === 'processing' || norm === 'starting' || norm === 'running') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 animate-pulse">
        <div className="w-2 h-2 rounded-full bg-indigo-400 animate-ping"></div>
        <span>{label || 'Sedang Diproses'}</span>
      </span>
    );
  }

  if (norm === 'pending' || norm === 'queued' || norm === 'warning' || norm === 'responding_health_unverified') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
        <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
        <span>{label || 'Menunggu (Pending)'}</span>
      </span>
    );
  }

  if (norm === 'failed' || norm === 'unreachable' || norm === 'down' || norm === 'expired' || norm === 'needs_login' || norm === 'invalid') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-300 border border-rose-500/30">
        <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
        <span>{label || status || 'Gagal / Expired'}</span>
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-300 border border-slate-700">
      <span>{label || status || 'Unknown'}</span>
    </span>
  );
}
