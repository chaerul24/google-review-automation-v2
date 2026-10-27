import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Building2,
  Mail,
  Cookie,
  Plus,
  Trash2,
  ExternalLink,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Sparkles,
  RefreshCw,
  Search,
  Check,
  ChevronRight,
  X,
  Layers,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  MapPin,
} from 'lucide-react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import AnalyticsCharts from '../components/AnalyticsCharts';
import ReviewPersonaModal from '../components/ReviewPersonaModal';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const urlTab = searchParams.get('tab');
  const [activeTab, setActiveTabState] = useState(
    urlTab === 'emails' || urlTab === 'cookies' ? urlTab : 'businesses'
  );
  const [searchQuery, setSearchQuery] = useState('');

  // Sync tab with URL search parameter
  useEffect(() => {
    if (urlTab === 'emails' || urlTab === 'cookies' || urlTab === 'businesses') {
      setActiveTabState(urlTab);
    } else if (!urlTab) {
      setActiveTabState('businesses');
    }
  }, [urlTab]);

  const setActiveTab = (tab) => {
    setActiveTabState(tab);
    if (tab === 'businesses') {
      setSearchParams({});
    } else {
      setSearchParams({ tab });
    }
  };

  // Modal states
  const [showBizModal, setShowBizModal] = useState(false);
  const [bizForm, setBizForm] = useState({ name: '', url: '' });

  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailForm, setEmailForm] = useState({ email: '', password: '', totp_secret: '' });

  const [showCookieModal, setShowCookieModal] = useState(false);
  const [cookieForm, setCookieForm] = useState({ email: '', cookie_json: '' });

  const [showPersonaModal, setShowPersonaModal] = useState(false);
  const [personaBizTarget, setPersonaBizTarget] = useState({ name: '', desc: '' });

  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const res = await api.getDashboard();
      setData(res);
    } catch (err) {
      setErrorMsg(err.message || 'Gagal memuat data dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const handleAddBusiness = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.addBusiness(bizForm.name, bizForm.url);
      setSuccessMsg(`Bisnis "${bizForm.name}" berhasil ditambahkan!`);
      setBizForm({ name: '', url: '' });
      setShowBizModal(false);
      loadDashboard();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menambahkan bisnis.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteBusiness = async (id, name) => {
    if (!confirm(`Hapus bisnis "${name}" beserta seluruh antrean reviewnya?`)) return;
    try {
      await api.deleteBusiness(id);
      setSuccessMsg(`Bisnis "${name}" telah dihapus.`);
      loadDashboard();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menghapus bisnis.');
    }
  };

  const handleAddEmail = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.addEmail(emailForm.email, emailForm.password, emailForm.totp_secret);
      setSuccessMsg(`Akun email ${emailForm.email} berhasil didaftarkan!`);
      setEmailForm({ email: '', password: '', totp_secret: '' });
      setShowEmailModal(false);
      loadDashboard();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menambahkan email.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteEmail = async (id, email) => {
    if (!confirm(`Hapus akun ${email} dari pool?`)) return;
    try {
      await api.deleteEmail(id);
      setSuccessMsg(`Akun ${email} telah dihapus.`);
      loadDashboard();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menghapus email.');
    }
  };

  const handleUnflagEmail = async (id) => {
    try {
      await api.unflagEmail(id);
      setSuccessMsg('Flag akun berhasil direset ke status aktif.');
      loadDashboard();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal mereset status email.');
    }
  };

  const handleAddCookie = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.addCookie(cookieForm.email.trim(), cookieForm.cookie_json.trim());
      const savedEmail = res.email || cookieForm.email.trim() || 'Akun Google';
      setSuccessMsg(`Cookie untuk ${savedEmail} berhasil disimpan! (${res.cookie_count || 0} cookies)`);
      setCookieForm({ email: '', cookie_json: '' });
      setShowCookieModal(false);
      loadDashboard();
    } catch (err) {
      setErrorMsg(err.message || 'Format cookie tidak valid atau gagal disimpan.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteCookie = async (id) => {
    if (!confirm('Hapus cookie sesi ini? Akun ini tidak akan bisa login via cookie.')) return;
    try {
      await api.deleteCookie(id);
      setSuccessMsg('Cookie sesi berhasil dihapus.');
      loadDashboard();
    } catch (err) {
      setErrorMsg(err.message || 'Gagal menghapus cookie.');
    }
  };

  if (loading && !data) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400 font-mono">Memuat data dashboard...</span>
        </div>
      </div>
    );
  }

  const businesses = data?.businesses || [];
  const emails = data?.all_emails || [];
  const cookies = data?.all_cookies || [];
  const queueMetrics = data?.queue_metrics || {};

  // Filtering
  const filteredBusinesses = businesses.filter((b) =>
    b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (b.url || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredEmails = emails.filter((e) =>
    e.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredCookies = cookies.filter((c) =>
    c.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Alert Notifications */}
      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center justify-between shadow-lg shadow-rose-950/20 animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={() => setErrorMsg('')}
            className="text-rose-400 hover:text-white p-1 rounded-lg hover:bg-rose-500/20 transition-colors ml-3"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center justify-between shadow-lg shadow-emerald-950/20 animate-in fade-in">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMsg}</span>
          </div>
          <button
            onClick={() => setSuccessMsg('')}
            className="text-emerald-400 hover:text-white p-1 rounded-lg hover:bg-emerald-500/20 transition-colors ml-3"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stat 1 */}
        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Target Listing</span>
            <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <Building2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-white mt-2 font-mono">{businesses.length}</p>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            Profil Google Maps aktif
          </p>
        </div>

        {/* Stat 2 */}
        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Pool Akun Google</span>
            <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <Mail className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-white mt-2 font-mono">{emails.length}</p>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            <span>{data?.eligible_emails || 0} akun siap pakai</span>
            {data?.flagged_emails > 0 && (
              <span className="text-rose-400">({data.flagged_emails} flagged)</span>
            )}
          </p>
        </div>

        {/* Stat 3 */}
        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Sesi Cookie Browser</span>
            <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <Cookie className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-white mt-2 font-mono">{cookies.length}</p>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            Sesi Chromium tanpa password
          </p>
        </div>

        {/* Stat 4 */}
        <div className="bg-[#0f1420] border border-slate-800/80 p-5 rounded-2xl shadow-xs hover:border-slate-700 transition-colors">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Status Antrean Ulasan</span>
            <div className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-white mt-2 font-mono">{queueMetrics.reviewed || 0}</p>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-2 font-medium">
            <span className="text-emerald-400 font-semibold">{queueMetrics.reviewed || 0} selesai</span>
            <span>•</span>
            <span className="text-amber-400 font-semibold">{queueMetrics.pending || 0} pending</span>
          </p>
        </div>
      </div>

      {/* Analytics & Velocity Chart */}
      <AnalyticsCharts />

      {/* Tabs & Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
        {/* Segmented Tab Controls */}
        <div className="bg-[#0f1420] p-1 rounded-xl border border-slate-800/80 flex items-center gap-1 overflow-x-auto no-scrollbar">
          <button
            onClick={() => { setActiveTab('businesses'); setSearchQuery(''); }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 shrink-0 cursor-pointer ${
              activeTab === 'businesses'
                ? 'bg-slate-800 text-white shadow-xs border border-slate-700/60'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Target Bisnis ({businesses.length})</span>
          </button>

          <button
            onClick={() => { setActiveTab('emails'); setSearchQuery(''); }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 shrink-0 cursor-pointer ${
              activeTab === 'emails'
                ? 'bg-slate-800 text-white shadow-xs border border-slate-700/60'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Pool Akun ({emails.length})</span>
          </button>

          <button
            onClick={() => { setActiveTab('cookies'); setSearchQuery(''); }}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-2 shrink-0 cursor-pointer ${
              activeTab === 'cookies'
                ? 'bg-slate-800 text-white shadow-xs border border-slate-700/60'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Cookie className="w-3.5 h-3.5" />
            <span>Cookie Manager ({cookies.length})</span>
          </button>
        </div>

        {/* Right Search & Action Buttons */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          {/* Search Input */}
          <div className="relative flex-1 sm:w-56">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Cari..."
              className="w-full pl-8 pr-3 py-1.5 bg-[#0f1420] border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-slate-600 transition-colors"
            />
          </div>

          {/* Tab Specific Action Button */}
          {activeTab === 'businesses' && (
            <div className="flex items-center gap-2">
              <Link
                to="/review-studio"
                className="px-3 py-1.5 rounded-xl text-xs font-medium bg-[#0f1420] hover:bg-slate-850 text-slate-300 border border-slate-800 hover:border-slate-700 flex items-center gap-1.5 transition-colors shrink-0 shadow-xs"
                title="Buka Studio Variasi Ulasan"
              >
                <span>Studio Ulasan</span>
              </Link>
              <button
                onClick={() => setShowBizModal(true)}
                className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-slate-100 text-slate-950 flex items-center gap-1.5 shadow-xs transition-colors shrink-0 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>Tambah Bisnis</span>
              </button>
            </div>
          )}

          {activeTab === 'emails' && (
            <button
              onClick={() => setShowEmailModal(true)}
              className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-slate-100 text-slate-950 flex items-center gap-1.5 shadow-xs transition-colors shrink-0 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Tambah Email</span>
            </button>
          )}

          {activeTab === 'cookies' && (
            <button
              onClick={() => setShowCookieModal(true)}
              className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-slate-100 text-slate-950 flex items-center gap-1.5 shadow-xs transition-colors shrink-0 cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Impor Cookie JSON</span>
            </button>
          )}
        </div>
      </div>

      {/* Tab 1: Businesses Grid */}
      {activeTab === 'businesses' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {filteredBusinesses.map((biz) => (
            <div
              key={biz.id}
              className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-5 hover:border-slate-700 transition-colors shadow-xs flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <h3 className="font-bold text-sm text-white line-clamp-1">
                    {biz.name}
                  </h3>
                  <button
                    onClick={() => handleDeleteBusiness(biz.id, biz.name)}
                    className="text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-rose-500/10 transition-colors shrink-0"
                    title="Hapus Bisnis"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                <a
                  href={biz.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-slate-400 hover:text-emerald-400 transition-colors flex items-center gap-1 mt-1 truncate"
                >
                  <ExternalLink className="w-3 h-3 shrink-0" />
                  <span className="truncate">{biz.url}</span>
                </a>

                {/* Queue status mini indicators */}
                <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-800/80 text-center">
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 font-mono block">Reviewed</span>
                    <span className="text-sm font-extrabold text-emerald-400 font-mono">{biz.reviewed_count || 0}</span>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 font-mono block">Pending</span>
                    <span className="text-sm font-extrabold text-amber-400 font-mono">{biz.pending_count || 0}</span>
                  </div>
                  <div className="bg-slate-950 p-2 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 font-mono block">Assigned</span>
                    <span className="text-sm font-extrabold text-slate-300 font-mono">{biz.assigned_emails || 0}</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 flex items-center gap-2">
                <Link
                  to={`/business/${biz.id}`}
                  className="flex-1 py-2 rounded-xl font-semibold text-xs bg-slate-800 hover:bg-slate-700 text-white flex items-center justify-center gap-2 transition-colors border border-slate-700/60 shadow-xs"
                >
                  <span>Buka Detail & Worker</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
                <button
                  onClick={() => {
                    setPersonaBizTarget({ name: biz.name, desc: '' });
                    setShowPersonaModal(true);
                  }}
                  className="p-2 rounded-xl text-slate-400 hover:text-slate-200 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 transition-colors cursor-pointer shrink-0"
                  title="Uji generator ulasan untuk bisnis ini"
                >
                  <Sparkles className="w-4 h-4 text-slate-400" />
                </button>
              </div>
            </div>
          ))}

          {filteredBusinesses.length === 0 && (
            <div className="col-span-full p-12 text-center bg-[#0f1420] border border-slate-800/80 rounded-2xl">
              <Building2 className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <p className="text-sm font-semibold text-slate-300">
                {searchQuery ? 'Tidak ada bisnis yang cocok dengan pencarian.' : 'Belum ada target bisnis Google Maps.'}
              </p>
              <p className="text-xs text-slate-500 mt-1">Tambahkan URL profil Google Maps bisnis untuk memulai antrean review.</p>
              {!searchQuery && (
                <button
                  onClick={() => setShowBizModal(true)}
                  className="mt-4 px-4 py-2 rounded-xl text-xs font-semibold bg-white hover:bg-slate-100 text-slate-950 transition-colors cursor-pointer"
                >
                  Tambah Bisnis Pertama
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Account Pool */}
      {activeTab === 'emails' && (
        <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="p-3.5 pl-5">Email Akun Google</th>
                  <th className="p-3.5">Metode Auth</th>
                  <th className="p-3.5">Gagal Sesi</th>
                  <th className="p-3.5">Status Akun</th>
                  <th className="p-3.5 pr-5 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredEmails.map((e) => (
                  <tr key={e.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-3.5 pl-5 font-semibold text-white font-mono">{e.email}</td>
                    <td className="p-3.5">
                      {e.password === 'cookie_auth' ? (
                        <span className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-300 font-mono text-[11px] border border-amber-500/20 font-medium">
                          Cookie Auth
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 font-mono text-[11px]">
                          Password + 2FA
                        </span>
                      )}
                    </td>
                    <td className="p-3.5 font-mono text-slate-400">{e.fail_count || 0} kali</td>
                    <td className="p-3.5">
                      {e.flagged ? (
                        <span className="px-2.5 py-1 rounded-lg bg-rose-500/10 text-rose-300 text-[11px] border border-rose-500/20 font-bold inline-flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                          Flagged (&gt;4x gagal)
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 text-[11px] border border-emerald-500/20 font-bold inline-flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Tersedia
                        </span>
                      )}
                    </td>
                    <td className="p-3.5 pr-5 text-right space-x-2">
                      {e.flagged ? (
                        <button
                          onClick={() => handleUnflagEmail(e.id)}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold border border-slate-700/60 transition-colors"
                        >
                          Unflag
                        </button>
                      ) : null}
                      <button
                        onClick={() => handleDeleteEmail(e.id, e.email)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                        title="Hapus akun dari pool"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}

                {filteredEmails.length === 0 && (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-slate-500">
                      {searchQuery ? 'Tidak ada akun yang cocok.' : 'Belum ada email yang terdaftar pada pool.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Cookie Manager */}
      {activeTab === 'cookies' && (
        <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xs">
          <div className="p-4 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Sesi Chromium dikelola murni menggunakan cookie sah tanpa fallback credential login.</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">Chromium Session Persistence</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="p-3.5 pl-5">Email Akun</th>
                  <th className="p-3.5">Status Validitas</th>
                  <th className="p-3.5">Detail Sesi</th>
                  <th className="p-3.5">Terakhir Dicek</th>
                  <th className="p-3.5 pr-5 text-right">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {filteredCookies.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="p-3.5 pl-5 font-semibold text-white font-mono">{c.email}</td>
                    <td className="p-3.5">
                      <StatusBadge status={c.status || 'active'} label={c.status} />
                    </td>
                    <td className="p-3.5">
                      <span className="text-[11px] text-slate-400">
                        {c.error_reason || 'Sesi siap digunakan'}
                      </span>
                    </td>
                    <td className="p-3.5 font-mono text-[11px] text-slate-500">
                      {c.last_checked_at || c.updated_at || '—'}
                    </td>
                    <td className="p-3.5 pr-5 text-right">
                      <button
                        onClick={() => handleDeleteCookie(c.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                        title="Hapus Cookie"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}

                {filteredCookies.length === 0 && (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-slate-500">
                      {searchQuery ? 'Tidak ada cookie yang cocok.' : 'Belum ada cookie sesi yang tersimpan.'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Tambah Bisnis */}
      {showBizModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-md shadow-2xl relative animate-in fade-in zoom-in-95">
            <button
              onClick={() => setShowBizModal(false)}
              className="absolute right-5 top-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
            <h3 className="font-extrabold text-base text-white mb-1">Tambah Target Bisnis Google Maps</h3>
            <p className="text-xs text-slate-400 mb-5">Masukkan detail target listing bisnis untuk otomatisasi ulasan.</p>

            <form onSubmit={handleAddBusiness} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Nama Bisnis</label>
                <input
                  type="text"
                  required
                  value={bizForm.name}
                  onChange={(e) => setBizForm({ ...bizForm, name: e.target.value })}
                  placeholder="Contoh: Coffee Shop Sejahtera"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">URL Google Maps</label>
                <input
                  type="url"
                  required
                  value={bizForm.url}
                  onChange={(e) => setBizForm({ ...bizForm, url: e.target.value })}
                  placeholder="https://maps.google.com/?cid=..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono transition-colors"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-800/80">
                <button
                  type="button"
                  onClick={() => setShowBizModal(false)}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white transition-all disabled:opacity-50 cursor-pointer shadow-lg shadow-indigo-600/20"
                >
                  {submitting ? 'Menyimpan...' : 'Simpan Bisnis'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Tambah Email */}
      {showEmailModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-md shadow-2xl relative animate-in fade-in zoom-in-95">
            <button
              onClick={() => setShowEmailModal(false)}
              className="absolute right-5 top-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
            <h3 className="font-extrabold text-base text-white mb-1">Daftarkan Akun Email ke Pool</h3>
            <p className="text-xs text-slate-400 mb-5">Tambahkan akun Google untuk rotasi penugasan ulasan.</p>

            <form onSubmit={handleAddEmail} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Alamat Email</label>
                <input
                  type="email"
                  required
                  value={emailForm.email}
                  onChange={(e) => setEmailForm({ ...emailForm, email: e.target.value })}
                  placeholder="user@gmail.com"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Kata Sandi (Password)</label>
                <input
                  type="password"
                  required
                  value={emailForm.password}
                  onChange={(e) => setEmailForm({ ...emailForm, password: e.target.value })}
                  placeholder="Kata sandi..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">TOTP Secret Key (Opsional untuk 2FA)</label>
                <input
                  type="text"
                  value={emailForm.totp_secret}
                  onChange={(e) => setEmailForm({ ...emailForm, totp_secret: e.target.value })}
                  placeholder="Base32 Key..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono transition-colors"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-800/80">
                <button
                  type="button"
                  onClick={() => setShowEmailModal(false)}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all disabled:opacity-50 cursor-pointer shadow-lg shadow-emerald-600/20"
                >
                  {submitting ? 'Menyimpan...' : 'Simpan Akun'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Tambah Cookie */}
      {showCookieModal && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-lg shadow-2xl relative animate-in fade-in zoom-in-95">
            <button
              onClick={() => setShowCookieModal(false)}
              className="absolute right-5 top-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
            <h3 className="font-extrabold text-base text-white mb-1">Impor Cookie Sesi Browser</h3>
            <p className="text-xs text-slate-400 mb-5">
              Tempelkan cookie Google (JSON array Cookie-Editor, format Netscape, atau string header SID=...).
            </p>

            <form onSubmit={handleAddCookie} noValidate className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Email Pemilik Cookie (Opsional)</label>
                <input
                  type="text"
                  value={cookieForm.email}
                  onChange={(e) => setCookieForm({ ...cookieForm, email: e.target.value })}
                  placeholder="user@gmail.com (otomatis dideteksi jika dikosongkan)"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Payload Cookie</label>
                <textarea
                  required
                  rows={7}
                  value={cookieForm.cookie_json}
                  onChange={(e) => setCookieForm({ ...cookieForm, cookie_json: e.target.value })}
                  placeholder='[{"name": "SID", "value": "..."}] atau SID=...; HSID=...'
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-amber-500 font-mono transition-colors"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-800/80">
                <button
                  type="button"
                  onClick={() => setShowCookieModal(false)}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2.5 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white transition-all disabled:opacity-50 cursor-pointer shadow-lg shadow-amber-600/20"
                >
                  {submitting ? 'Memvalidasi...' : 'Validasi & Simpan Cookie'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: AI Persona Review Simulator */}
      <ReviewPersonaModal
        isOpen={showPersonaModal}
        onClose={() => setShowPersonaModal(false)}
        defaultBusinessName={personaBizTarget.name}
        defaultDescription={personaBizTarget.desc}
      />
    </div>
  );
}
