import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Layers,
  Network,
  Globe,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Server,
  ArrowRight,
} from 'lucide-react';
import { api } from '../../api/client';
import StatusBadge from '../../components/StatusBadge';

export default function Overview() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [message, setMessage] = useState('');

  const loadOverview = async () => {
    try {
      setLoading(true);
      const res = await api.getAutobotixOverview();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  const handleRefreshSnapshot = async () => {
    try {
      setImporting(true);
      await api.importSnapshot();
      setMessage('Snapshot historis berhasil diperbarui.');
      loadOverview();
    } catch (err) {
      setMessage(`Gagal import snapshot: ${err.message}`);
    } finally {
      setImporting(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="p-8 text-center text-slate-500 font-mono text-xs">
        Memuat AutoBotix Infrastructure Overview...
      </div>
    );
  }

  const tunnels = data?.tunnels || [];
  const services = data?.services || [];
  const domainCount = data?.domain_count || 0;
  const healthyCount = data?.healthy_count || 0;
  const unknownCount = data?.unknown_count || 0;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {message && (
        <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300 flex justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage('')} className="font-bold">✕</button>
        </div>
      )}

      <div>
        <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          <span>Infrastructure Overview — AutoBotix</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Inventory status berasal dari snapshot Cloudflare & host server. Mode aman: read-only tanpa modifikasi service tanpa verifikasi.
        </p>
      </div>

      {/* Top 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-semibold text-slate-400">Tunnel Terinventarisasi</span>
          <p className="text-3xl font-extrabold text-white mt-2">{tunnels.length}</p>
          <Link to="/autobotix/tunnels" className="text-xs text-indigo-400 hover:underline inline-flex items-center gap-1 mt-2">
            Kelola Tunnel <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-semibold text-slate-400">Domain Terinventarisasi</span>
          <p className="text-3xl font-extrabold text-white mt-2">{domainCount}</p>
          <Link to="/autobotix/domains" className="text-xs text-indigo-400 hover:underline inline-flex items-center gap-1 mt-2">
            Lihat Semua Domain <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl">
          <span className="text-xs font-semibold text-slate-400">Upstream 200 Historis</span>
          <p className="text-3xl font-extrabold text-emerald-400 mt-2">{healthyCount}</p>
          <span className="text-xs text-slate-500 block mt-2">{unknownCount} perlu investigasi</span>
        </div>
      </div>

      {/* Safe Mode Panel & Snapshot Refresh */}
      <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-sm text-white flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Mode Aman Operasional</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Semua manipulasi tunnel dibatasi allow-list dan verifikasi target. Anda dapat me-refresh snapshot historis kapan saja.
          </p>
        </div>
        <button
          onClick={handleRefreshSnapshot}
          disabled={importing}
          className="px-4 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 flex items-center gap-2 shrink-0 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${importing ? 'animate-spin' : ''}`} />
          <span>Refresh Snapshot Historis</span>
        </button>
      </div>

      {/* Service Inventory Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-4 bg-slate-950/50 border-b border-slate-800 flex items-center gap-2">
          <Server className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-white">Service Inventory (Audit Historis)</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3.5 pl-5">Nama Service</th>
                <th className="p-3.5">Port</th>
                <th className="p-3.5">Project Path</th>
                <th className="p-3.5">Status Audit</th>
                <th className="p-3.5 pr-5">Terakhir Diobservasi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {services.map((srv) => (
                <tr key={srv.name} className="hover:bg-slate-800/30">
                  <td className="p-3.5 pl-5 font-semibold text-white">{srv.name}</td>
                  <td className="p-3.5 font-mono">{srv.port || '—'}</td>
                  <td className="p-3.5 font-mono text-slate-400">{srv.project_path || '—'}</td>
                  <td className="p-3.5">
                    <StatusBadge status={srv.status || 'unknown'} />
                  </td>
                  <td className="p-3.5 pr-5 font-mono text-[11px] text-slate-500">
                    {srv.observed_at || '—'}
                  </td>
                </tr>
              ))}
              {services.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-slate-500">
                    Tidak ada service pada snapshot.
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
