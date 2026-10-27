import React, { useState, useEffect } from 'react';
import {
  Cookie,
  Plus,
  Trash2,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  X,
  ShieldCheck,
  Check,
  ExternalLink,
  ShieldAlert,
  Code2,
} from 'lucide-react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function CookieManager() {
  const [cookies, setCookies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [testingId, setTestingId] = useState(null);

  // Notifications
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Add Cookie Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState({ email: '', cookie_json: '' });
  const [jsonError, setJsonError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [unflagging, setUnflagging] = useState(false);

  const handleUnflagAll = async () => {
    setUnflagging(true);
    try {
      const res = await api.unflagAllEmails();
      setSuccessMsg(res.message || 'Semua akun berhasil dipulihkan (status flagged direset)!');
      fetchCookies();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal memulihkan status akun.');
    } finally {
      setUnflagging(false);
    }
  };

  const fetchCookies = async () => {
    try {
      const res = await api.getCookieHealth();
      if (res && res.cookies) {
        setCookies(res.cookies);
      }
    } catch (err) {
      console.error('Failed to fetch cookies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCookies();
  }, []);

  const handleJsonChange = (val) => {
    setForm({ ...form, cookie_json: val });
    setJsonError('');
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!form.cookie_json.trim()) {
      setErrorMsg('Cookie tidak boleh kosong.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await api.addCookie(form.email.trim(), form.cookie_json.trim());
      const savedEmail = res.email || form.email.trim() || 'Akun Google';
      setSuccessMsg(`Cookie untuk ${savedEmail} berhasil disimpan! (${res.cookie_count || 0} cookies terdeteksi)`);
      setForm({ email: '', cookie_json: '' });
      setShowAddModal(false);
      fetchCookies();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menyimpan cookie sesi.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id, email) => {
    if (!confirm(`Hapus cookie sesi untuk ${email}? Akun ini tidak akan dapat login di browser.`)) {
      return;
    }
    try {
      await api.deleteCookie(id);
      setSuccessMsg(`Cookie untuk ${email} berhasil dihapus.`);
      fetchCookies();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menghapus cookie.');
    }
  };

  const handleTestCookie = async (id, email) => {
    setTestingId(id);
    try {
      const res = await api.testCookie(id);
      if (res.is_valid) {
        setSuccessMsg(`Sesi ${email} valid! Status: ${res.session_status} (${res.count} cookie siap).`);
      } else {
        setErrorMsg(`Sesi ${email} perlu perhatian: ${res.reason}`);
      }
      fetchCookies();
    } catch (err) {
      setErrorMsg(`Gagal memverifikasi cookie: ${err.message}`);
    } finally {
      setTestingId(null);
    }
  };

  const filteredCookies = cookies.filter((c) =>
    c.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const activeCount = cookies.filter((c) => c.status === 'active').length;
  const needLoginCount = cookies.filter((c) => c.status === 'needs_login' || c.status === 'expired').length;

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto space-y-6">
      {/* Alert Notifications */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg('')} className="text-rose-400 hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg('')} className="text-emerald-400 hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Top Banner & Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl">
        <div>
          <h2 className="text-base sm:text-lg font-bold text-white flex items-center gap-2">
            <Cookie className="w-5 h-5 text-emerald-400" />
            <span>Manajemen Sesi Cookie Google</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Kelola dan validasi token sesi Chromium tanpa input email/password atau TOTP fallback.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleUnflagAll}
            disabled={unflagging}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-amber-300 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 transition-colors cursor-pointer"
            title="Reset status sesi kedaluwarsa untuk semua akun"
          >
            <ShieldCheck className={`w-3.5 h-3.5 ${unflagging ? 'animate-spin' : ''}`} />
            <span>{unflagging ? 'Memulihkan...' : 'Pulihkan Semua Akun'}</span>
          </button>
          <button
            onClick={fetchCookies}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-colors cursor-pointer"
            title="Muat ulang"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-emerald-400' : ''}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition-all cursor-pointer shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>Tambah Cookie</span>
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Akun Terdaftar</span>
          <p className="text-2xl font-extrabold text-white mt-1 font-mono">{cookies.length}</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Akun Google tersimpan di database</p>
        </div>
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Sesi Aktif (Active)</span>
          <p className="text-2xl font-extrabold text-emerald-400 mt-1 font-mono">{activeCount}</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Siap digunakan worker di Google Maps</p>
        </div>
        <div className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Perlu Login / Expired</span>
          <p className="text-2xl font-extrabold text-amber-400 mt-1 font-mono">{needLoginCount}</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Perlu perbarui cookie JSON</p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Cari berdasarkan email akun Google..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-900/70 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-slate-700 transition-colors"
          />
        </div>
      </div>

      {/* Cookies Table (CRUD) */}
      <div className="bg-slate-900/30 border border-slate-800/80 rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-semibold">
                <th className="py-3 px-4">Email Akun Google</th>
                <th className="py-3 px-4">Status Sesi</th>
                <th className="py-3 px-4">Jumlah Cookie</th>
                <th className="py-3 px-4">Detail Validasi</th>
                <th className="py-3 px-4">Terakhir Diperiksa</th>
                <th className="py-3 px-4 text-right">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredCookies.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-12 text-center text-slate-500">
                    <Cookie className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-60" />
                    <p className="text-xs">Belum ada cookie sesi yang tersimpan.</p>
                    <button
                      onClick={() => setShowAddModal(true)}
                      className="mt-3 text-xs text-emerald-400 hover:text-emerald-300 font-medium inline-flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Tambah cookie pertama</span>
                    </button>
                  </td>
                </tr>
              ) : (
                filteredCookies.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-900/50 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-medium text-white flex items-center gap-2">
                      <div className="w-6 h-6 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-[10px] text-slate-300">
                        {c.email.charAt(0).toUpperCase()}
                      </div>
                      <span>{c.email}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-300">
                      {c.count} items
                    </td>
                    <td className="py-3.5 px-4 text-slate-400 max-w-xs truncate text-[11px]" title={c.error_reason || 'Valid'}>
                      {c.error_reason || 'Struktur cookie valid (siap dimuat)'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px]">
                      {c.last_checked_at || c.updated_at || 'Belum dicek'}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-1">
                      <button
                        onClick={() => handleTestCookie(c.id, c.email)}
                        disabled={testingId === c.id}
                        className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors text-[11px] font-medium cursor-pointer disabled:opacity-50 inline-flex items-center gap-1"
                        title="Verifikasi status sesi akun"
                      >
                        <RefreshCw className={`w-3 h-3 ${testingId === c.id ? 'animate-spin text-emerald-400' : ''}`} />
                        <span>{testingId === c.id ? 'Memeriksa...' : 'Cek Status'}</span>
                      </button>
                      <button
                        onClick={() => handleDelete(c.id, c.email)}
                        className="p-1 rounded-lg bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-700 hover:border-rose-500/30 transition-colors cursor-pointer"
                        title="Hapus cookie"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Tambah Cookie */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xs animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-5 sm:p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Cookie className="w-5 h-5 text-emerald-400" />
                <h3 className="text-sm font-bold text-white">Tambah Cookie Sesi Google</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Email Akun Google (Opsional)
                </label>
                <input
                  type="text"
                  placeholder="contoh: akunanda@gmail.com (otomatis dideteksi dari cookie)"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-hidden focus:border-emerald-500 transition-colors"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-medium text-slate-300">
                    Cookie Sesi (JSON, Netscape, atau String Header)
                  </label>
                  {form.cookie_json.trim() ? (
                    <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                      <Check className="w-3 h-3" /> Siap Disimpan
                    </span>
                  ) : null}
                </div>
                <textarea
                  rows="7"
                  required
                  placeholder='[{"name": "SID", "value": "..."}] atau SID=...; HSID=...'
                  value={form.cookie_json}
                  onChange={(e) => handleJsonChange(e.target.value)}
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl font-mono text-xs text-slate-200 placeholder-slate-600 focus:outline-hidden focus:border-emerald-500 transition-colors"
                ></textarea>
                <p className="text-[11px] text-slate-500 mt-1">
                  Pastikan memuat cookie otentikasi Google: <code>SID</code>, <code>HSID</code>, <code>SSID</code>, <code>SAPISID</code>.
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3.5 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-slate-800/60 hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submitting || Boolean(jsonError)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition-all cursor-pointer disabled:opacity-50 inline-flex items-center gap-1.5"
                >
                  {submitting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>Simpan Cookie</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
