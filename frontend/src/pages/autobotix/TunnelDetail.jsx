import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Network, ArrowLeft, ExternalLink, ShieldAlert } from 'lucide-react';
import { api } from '../../api/client';
import StatusBadge from '../../components/StatusBadge';

export default function TunnelDetail() {
  const { id } = useParams();
  const [tunnel, setTunnel] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getTunnel(id);
        setTunnel(res.tunnel);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading || !tunnel) {
    return <div className="p-8 text-center text-slate-500 font-mono text-xs">Memuat detail tunnel...</div>;
  }

  const domains = tunnel.domains || [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
        <Link
          to="/autobotix/tunnels"
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-extrabold text-white font-mono flex items-center gap-2">
            <span>{tunnel.name}</span>
            <StatusBadge status={tunnel.status} />
          </h1>
          <p className="text-xs text-slate-500 font-mono">UUID: {tunnel.uuid || '—'}</p>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-start gap-2.5">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <span>
          Tunnel Manager berjalan dalam <strong>Mode Aman (Read-Only)</strong>. Penghentian atau restart service cloudflared melalui API dinonaktifkan demi keselamatan operasional.
        </span>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-4 bg-slate-950/60 border-b border-slate-800 flex justify-between items-center">
          <span className="text-xs font-bold text-white">Domain yang Dialihkan Melalui Tunnel Ini</span>
          <span className="text-xs text-slate-400 font-mono">{domains.length} domain</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/40 text-slate-400 text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="p-3 pl-4">Hostname</th>
                <th className="p-3">Upstream Target</th>
                <th className="p-3">Status</th>
                <th className="p-3 pr-4 text-right">Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {domains.map((dom) => (
                <tr key={dom.id} className="hover:bg-slate-800/30">
                  <td className="p-3 pl-4 font-mono font-semibold text-white">{dom.hostname}</td>
                  <td className="p-3 font-mono text-slate-300">
                    {dom.target_host ? `${dom.target_host}:${dom.target_port}` : '—'}
                  </td>
                  <td className="p-3">
                    <StatusBadge status={dom.upstream_status} />
                  </td>
                  <td className="p-3 pr-4 text-right">
                    <Link
                      to={`/autobotix/domains/${dom.id}`}
                      className="text-xs text-indigo-400 hover:underline"
                    >
                      Buka
                    </Link>
                  </td>
                </tr>
              ))}
              {domains.length === 0 && (
                <tr>
                  <td colSpan="4" className="p-6 text-center text-slate-500">
                    Tidak ada domain yang terhubung dengan tunnel ini.
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
