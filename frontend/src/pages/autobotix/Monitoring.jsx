import React, { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, Server, ShieldCheck } from 'lucide-react';
import { api } from '../../api/client';
import StatusBadge from '../../components/StatusBadge';

export default function Monitoring() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getMonitoring();
        setData(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading && !data) {
    return <div className="p-8 text-center text-slate-500 font-mono text-xs">Memuat metrik monitoring...</div>;
  }

  const checks = data?.checks || [];
  const metrics = data?.metrics || [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <span>Sistem Monitoring & Health Checks</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Observabilitas real-time pada service host dan status TCP probe domain target.
        </p>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 bg-slate-950/60 border-b border-slate-800 flex justify-between items-center">
          <span className="text-xs font-bold text-white">Log Pemeriksaan Terbaru</span>
          <span className="text-xs text-slate-400 font-mono">{checks.length} entries</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/40 text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="p-3 pl-4">Waktu</th>
                <th className="p-3">Domain</th>
                <th className="p-3">Layer</th>
                <th className="p-3">Status</th>
                <th className="p-3">Latensi</th>
                <th className="p-3 pr-4">Sumber</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {checks.map((c, i) => (
                <tr key={i} className="hover:bg-slate-800/30">
                  <td className="p-3 pl-4 text-slate-400">{c.checked_at}</td>
                  <td className="p-3 font-semibold text-white">{c.hostname || `ID #${c.domain_id}`}</td>
                  <td className="p-3 uppercase">{c.layer}</td>
                  <td className="p-3">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="p-3">{c.duration_ms ? `${c.duration_ms} ms` : '—'}</td>
                  <td className="p-3 pr-4 text-slate-400">{c.source}</td>
                </tr>
              ))}
              {checks.length === 0 && (
                <tr>
                  <td colSpan="6" className="p-6 text-center text-slate-500">
                    Belum ada data monitoring terbaru.
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
