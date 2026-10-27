import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Globe, ArrowLeft, ExternalLink, Activity, ShieldCheck, AlertCircle } from 'lucide-react';
import { api } from '../../api/client';
import StatusBadge from '../../components/StatusBadge';

export default function DomainDetail() {
  const { id } = useParams();
  const [domain, setDomain] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getDomain(id);
        setDomain(res.domain);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading || !domain) {
    return <div className="p-8 text-center text-slate-500 font-mono text-xs">Memuat detail domain...</div>;
  }

  const history = domain.history || [];
  const findings = domain.findings || [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <Link
          to="/autobotix/domains"
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-extrabold text-white font-mono flex items-center gap-2">
            <span>{domain.hostname}</span>
            <StatusBadge status={domain.upstream_status} />
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">Tunnel: {domain.tunnel_name || '—'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Target Upstream</h3>
          <div className="space-y-1.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Target Host & Port:</span>
              <span className="font-mono text-white">{domain.target_host ? `${domain.target_host}:${domain.target_port}` : '—'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-400">Project Path:</span>
              <span className="font-mono text-slate-300">{domain.project_path || '—'}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-400">Framework:</span>
              <span className="font-mono text-slate-300">{domain.framework || '—'}</span>
            </div>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Audit Findings</h3>
          {findings.length > 0 ? (
            <div className="space-y-2 text-xs">
              {findings.map((f, i) => (
                <div key={i} className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-200">
                  <p className="font-bold">{f.finding}</p>
                  {f.recommendation && <p className="text-[11px] text-amber-300/80 mt-1">{f.recommendation}</p>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-500">Tidak ada temuan anomali pada domain ini.</p>
          )}
        </div>
      </div>

      {/* History of Health Probes */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="p-4 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" /> Riwayat Health Check
          </span>
          <span className="text-[10px] text-slate-500 font-mono">30 snapshot terakhir</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/40 text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="p-3 pl-4">Waktu Check</th>
                <th className="p-3">Layer</th>
                <th className="p-3">Status</th>
                <th className="p-3">Latensi</th>
                <th className="p-3 pr-4">Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {history.map((h, i) => (
                <tr key={i} className="hover:bg-slate-800/30">
                  <td className="p-3 pl-4 text-slate-400">{h.checked_at}</td>
                  <td className="p-3 uppercase">{h.layer}</td>
                  <td className="p-3">
                    <StatusBadge status={h.status} />
                  </td>
                  <td className="p-3">{h.duration_ms ? `${h.duration_ms} ms` : '—'}</td>
                  <td className="p-3 pr-4 text-slate-400">{h.reason || '—'}</td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-6 text-center text-slate-500">
                    Belum ada riwayat pengecekan TCP/HTTP.
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
