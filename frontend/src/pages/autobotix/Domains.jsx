import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Globe, Search, Filter, ExternalLink, ChevronRight } from 'lucide-react';
import { api } from '../../api/client';
import StatusBadge from '../../components/StatusBadge';

export default function Domains() {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const loadDomains = async () => {
    try {
      setLoading(true);
      const res = await api.getDomains(search, statusFilter);
      setDomains(res.domains || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDomains();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadDomains();
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center gap-2">
            <Globe className="w-5 h-5 text-indigo-400" />
            <span>Domain Intelligence</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Daftar domain publik Cloudflare Tunnel beserta status upstream dan mapping proyek.
          </p>
        </div>

        {/* Search & Filter */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cari domain..."
              className="pl-9 pr-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 w-44 sm:w-56"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
          >
            <option value="">Semua Status</option>
            <option value="healthy">Healthy (200)</option>
            <option value="responding_health_unverified">Unverified</option>
            <option value="unreachable">Unreachable</option>
          </select>

          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            Cari
          </button>
        </form>
      </div>

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3.5 pl-5">Hostname</th>
                <th className="p-3.5">Tunnel Asal</th>
                <th className="p-3.5">Upstream Target</th>
                <th className="p-3.5">Status Upstream</th>
                <th className="p-3.5 pr-5 text-right">Detail</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {domains.map((dom) => (
                <tr key={dom.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-3.5 pl-5 font-semibold text-white font-mono flex items-center gap-1.5">
                    <a
                      href={`https://${dom.hostname}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline text-indigo-300 flex items-center gap-1"
                    >
                      <span>{dom.hostname}</span>
                      <ExternalLink className="w-3 h-3 text-slate-500" />
                    </a>
                  </td>
                  <td className="p-3.5 text-slate-400 font-mono text-[11px]">{dom.tunnel_name || '—'}</td>
                  <td className="p-3.5 font-mono text-slate-300">
                    {dom.target_host ? `${dom.target_host}:${dom.target_port}` : '—'}
                  </td>
                  <td className="p-3.5">
                    <StatusBadge status={dom.upstream_status || 'unknown'} />
                  </td>
                  <td className="p-3.5 pr-5 text-right">
                    <Link
                      to={`/autobotix/domains/${dom.id}`}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium"
                    >
                      <span>Lihat</span>
                      <ChevronRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}

              {domains.length === 0 && (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-slate-500">
                    Tidak ada domain yang sesuai kriteria pencarian.
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
