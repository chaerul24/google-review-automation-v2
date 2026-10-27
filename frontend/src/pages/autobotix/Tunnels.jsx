import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Network, ChevronRight, ShieldCheck, Server } from 'lucide-react';
import { api } from '../../api/client';
import StatusBadge from '../../components/StatusBadge';

export default function Tunnels() {
  const [tunnels, setTunnels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await api.getTunnels();
        setTunnels(res.tunnels || []);
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
          <Network className="w-5 h-5 text-indigo-400" />
          <span>Tunnel Manager — Cloudflare Ingress</span>
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Daftar Cloudflare Tunnel yang terhubung dengan host ini.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tunnels.map((t) => (
          <div key={t.id} className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 hover:border-slate-700 transition-all flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-sm text-white font-mono">{t.name}</h3>
                <StatusBadge status={t.status || 'active'} />
              </div>
              <p className="text-xs text-slate-500 font-mono mt-1 truncate">UUID: {t.uuid || '—'}</p>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex justify-between text-xs">
                <span className="text-slate-400">Domain Terkait:</span>
                <span className="font-bold text-indigo-400">{t.domain_count || 0} domain</span>
              </div>
            </div>

            <div className="mt-5">
              <Link
                to={`/autobotix/tunnels/${t.id}`}
                className="w-full py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white flex items-center justify-center gap-1.5 transition-all"
              >
                <span>Kelola Tunnel</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}

        {tunnels.length === 0 && !loading && (
          <div className="col-span-full p-8 text-center text-slate-500">
            Tidak ada tunnel terdaftar pada snapshot.
          </div>
        )}
      </div>
    </div>
  );
}
