import React, { useState, useEffect } from 'react';
import { History, Shield, User, Clock } from 'lucide-react';
import { api } from '../../api/client';
import StatusBadge from '../../components/StatusBadge';

export default function Activity() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getActivity();
        setLogs(res.logs || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <History className="w-5 h-5 text-indigo-400" />
          <span>Activity Audit Logs</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Catatan riwayat tindakan administratif dan aksi sistem AutoBotix.
        </p>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/60 text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="p-3.5 pl-5">Waktu</th>
                <th className="p-3.5">Actor</th>
                <th className="p-3.5">Aksi</th>
                <th className="p-3.5">Target</th>
                <th className="p-3.5">Outcome</th>
                <th className="p-3.5 pr-5">Pesan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {logs.map((l) => (
                <tr key={l.id} className="hover:bg-slate-800/30">
                  <td className="p-3.5 pl-5 text-slate-400">{l.created_at}</td>
                  <td className="p-3.5 font-semibold text-white">{l.actor}</td>
                  <td className="p-3.5 font-bold text-indigo-400">{l.action}</td>
                  <td className="p-3.5 text-slate-300">{l.target || '—'}</td>
                  <td className="p-3.5">
                    <StatusBadge status={l.outcome} />
                  </td>
                  <td className="p-3.5 pr-5 text-slate-400 max-w-xs truncate">{l.message || '—'}</td>
                </tr>
              ))}
              {logs.length === 0 && !loading && (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-slate-500">
                    Belum ada catatan aktivitas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
