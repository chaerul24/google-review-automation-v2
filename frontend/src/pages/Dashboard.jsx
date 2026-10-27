import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Users,
  Cookie,
  Server,
  Activity,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Sparkles,
  Plus,
  Trash2,
  ExternalLink,
  Clock,
  Search,
  RefreshCw,
  Play,
  Square,
  LogOut,
  ChevronRight,
  ChevronDown,
  Check,
  X,
  Copy,
  Eye,
  EyeOff,
  Terminal,
  Sliders,
  Cpu,
  HardDrive,
  Layers,
  Tv,
  Monitor,
  BarChart3,
  PieChart,
  TrendingUp,
  MapPin,
  Flame,
  CheckCheck,
  Radio,
  ArrowUpRight,
  Info
} from 'lucide-react';
import { api } from '../api/client';

export default function Dashboard({ onLogout }) {
  const navigate = useNavigate();

  // Navigation Tab State
  // 'overview' | 'accounts' | 'cookies' | 'server' | 'businesses'
  const [activeTab, setActiveTab] = useState('overview');

  // Core Data States
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isCheckingNames, setIsCheckingNames] = useState(false);
  const [data, setData] = useState(null);
  const [cliStatus, setCliStatus] = useState(null);

  // Search & Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [accountFilter, setAccountFilter] = useState('all'); // 'all' | 'active' | 'needs_login' | 'expired' | 'no_cookie' | 'flagged'
  const [cookieFilter, setCookieFilter] = useState('all'); // 'all' | 'active' | 'needs_login' | 'expired'

  // Modals
  const [showAddAccountModal, setShowAddAccountModal] = useState(false);
  const [accountForm, setAccountForm] = useState({ email: '', password: '', totp_secret: '' });

  const [showCookieModal, setShowCookieModal] = useState(false);
  const [cookieForm, setCookieForm] = useState({ email: '', cookie_json: '' });

  const [showAddBizModal, setShowAddBizModal] = useState(false);
  const [bizForm, setBizForm] = useState({ name: '', url: '' });

  const [showFastRunModal, setShowFastRunModal] = useState(false);
  const [fastRunForm, setFastRunForm] = useState({ business_id: '', slots: 1, star_rating: 5 });

  const [snippetModalCookie, setSnippetModalCookie] = useState(null);

  // Notifications
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Mobile sidebar open
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // ── Load All Data ─────────────────────────────────────────────────────────────
  const loadDashboardData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      else setRefreshing(true);

      const [dashRes, cliRes] = await Promise.allSettled([
        api.getDashboard(),
        api.getCliStatus ? api.getCliStatus() : Promise.resolve(null),
      ]);

      if (dashRes.status === 'fulfilled') {
        setData(dashRes.value);
      }
      if (cliRes.status === 'fulfilled' && cliRes.value) {
        setCliStatus(cliRes.value);
      }
    } catch (err) {
      if (!silent) setErrorMsg(err.message || 'Gagal memuat data dari server.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(() => {
      loadDashboardData(true);
    }, 7000);
    return () => clearInterval(interval);
  }, []);

  // ── Handlers ──────────────────────────────────────────────────────────────────
  const handleLogout = async () => {
    try {
      await api.logout();
      if (onLogout) onLogout();
      navigate('/login');
    } catch {
      navigate('/login');
    }
  };

  const handleCheckAccountNames = async () => {
    setIsCheckingNames(true);
    setErrorMsg('');
    setSuccessMsg('');
    try {
      const res = await api.checkAccountNames();
      setSuccessMsg(
        `✓ Pengecekan Google selesai! ${res.active_cookies || 0} akun aktif terverifikasi (${res.checked || 0} cookie dipindai).`
      );
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal memeriksa nama akun: ${err.message || err}`);
    } finally {
      setIsCheckingNames(false);
    }
  };

  const handleAddAccount = async (e) => {
    e.preventDefault();
    if (!accountForm.email) return;
    setSubmitting(true);
    try {
      await api.addEmail(accountForm.email, accountForm.password, accountForm.totp_secret);
      setSuccessMsg(`Akun Google "${accountForm.email}" berhasil didaftarkan!`);
      setAccountForm({ email: '', password: '', totp_secret: '' });
      setShowAddAccountModal(false);
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal mendaftarkan akun: ${err.message || err}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteAccount = async (id, email) => {
    if (!window.confirm(`Hapus akun Google "${email}" dari sistem?`)) return;
    try {
      await api.deleteEmail(id);
      setSuccessMsg(`Akun "${email}" berhasil dihapus.`);
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal menghapus akun: ${err.message || err}`);
    }
  };

  const handleToggleUnflag = async (id, email, isFlagged) => {
    try {
      if (isFlagged) {
        await api.unflagEmail(id);
        setSuccessMsg(`Status flag akun "${email}" berhasil dipulihkan (Aktif).`);
      }
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal mengubah status flag: ${err.message || err}`);
    }
  };

  const handleUnflagAll = async () => {
    if (!window.confirm('Pulihkan semua akun yang terkena flag agar kembali aktif?')) return;
    try {
      await api.unflagAllEmails();
      setSuccessMsg('Semua akun Google berhasil dipulihkan ke status aktif!');
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal unflag semua: ${err.message || err}`);
    }
  };

  const handleAddCookie = async (e) => {
    e.preventDefault();
    if (!cookieForm.cookie_json) return;
    setSubmitting(true);
    try {
      const res = await api.addCookie(cookieForm.email, cookieForm.cookie_json);
      const accName = res.account_name ? ` (Nama: ${res.account_name})` : '';
      setSuccessMsg(
        `✓ Cookie sesi berhasil disimpan & diverifikasi Google! Status: ${res.status?.toUpperCase()}${accName}`
      );
      setCookieForm({ email: '', cookie_json: '' });
      setShowCookieModal(false);
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal menyimpan cookie: ${err.message || err}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteCookie = async (id, email) => {
    if (!window.confirm(`Hapus cookie sesi untuk akun "${email}"?`)) return;
    try {
      await api.deleteCookie(id);
      setSuccessMsg(`Cookie untuk "${email}" berhasil dihapus.`);
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal menghapus cookie: ${err.message || err}`);
    }
  };

  const handleTestCookie = async (id, email) => {
    try {
      setRefreshing(true);
      const res = await api.testCookie(id);
      const isOk = res.is_valid;
      if (isOk) {
        setSuccessMsg(`✓ Sesi akun "${email}" AKTIF dan valid di Google Maps!`);
      } else {
        setErrorMsg(`▲ Sesi akun "${email}" bermasalah: ${res.reason || res.session_status}`);
      }
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal menguji sesi: ${err.message || err}`);
    } finally {
      setRefreshing(false);
    }
  };

  const handleAddBusiness = async (e) => {
    e.preventDefault();
    if (!bizForm.name || !bizForm.url) return;
    setSubmitting(true);
    try {
      await api.addBusiness(bizForm.name, bizForm.url);
      setSuccessMsg(`Bisnis "${bizForm.name}" berhasil ditambahkan!`);
      setBizForm({ name: '', url: '' });
      setShowAddBizModal(false);
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal menambahkan bisnis: ${err.message || err}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteBusiness = async (id, name) => {
    if (!window.confirm(`Hapus bisnis target "${name}" dan riwayat ulasannya?`)) return;
    try {
      await api.deleteBusiness(id);
      setSuccessMsg(`Target bisnis "${name}" berhasil dihapus.`);
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal menghapus bisnis: ${err.message || err}`);
    }
  };

  const handleEmergencyStop = async () => {
    if (!window.confirm('PERINGATAN: Hentikan paksa semua Chromium browser dan batalkan antrean review yang sedang jalan?')) return;
    try {
      setRefreshing(true);
      await api.emergencyStopWorker();
      setSuccessMsg('🛑 Emergency Stop berhasil! Semua browser Chromium dihentikan.');
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal menghentikan worker: ${err.message || err}`);
    } finally {
      setRefreshing(false);
    }
  };

  const handleFastRunSubmit = async (e) => {
    e.preventDefault();
    if (!fastRunForm.business_id) return;
    setSubmitting(true);
    try {
      const params = {
        [`star_${fastRunForm.star_rating}_count`]: parseInt(fastRunForm.slots, 10),
        review_style: 'random',
        selected_language: 'Indonesian',
      };
      await api.startBot(fastRunForm.business_id, params);
      setSuccessMsg(`🚀 Ulasan bot berhasil diluncurkan dengan ${fastRunForm.slots} browser Chromium!`);
      setShowFastRunModal(false);
      loadDashboardData(true);
    } catch (err) {
      setErrorMsg(`Gagal menjalankan bot: ${err.message || err}`);
    } finally {
      setSubmitting(false);
    }
  };

  // ── Derived Data ──────────────────────────────────────────────────────────────
  const emails = data?.all_emails || [];
  const cookies = data?.all_cookies || [];
  const businesses = data?.businesses || [];
  const queueMetrics = data?.queue_metrics || {};
  const hostMetrics = data?.host_metrics || {};
  const displays = data?.displays || cliStatus?.displays || [':99', ':100', ':101', ':102', ':103', ':104'];

  const activeCookiesCount = cookies.filter((c) => c.status === 'active').length;
  const needsLoginCookiesCount = cookies.filter((c) => c.status === 'needs_login').length;
  const expiredCookiesCount = cookies.filter((c) => c.status === 'expired' || c.status === 'invalid').length;

  const activeAccountsCount = emails.filter((e) => e.cookie_status === 'active').length;

  // Filtered Accounts
  const filteredAccounts = useMemo(() => {
    return emails.filter((acc) => {
      const matchSearch =
        acc.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (acc.account_name || '').toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchSearch) return false;

      if (accountFilter === 'active') return acc.cookie_status === 'active';
      if (accountFilter === 'needs_login') return acc.cookie_status === 'needs_login';
      if (accountFilter === 'expired') return acc.cookie_status === 'expired';
      if (accountFilter === 'no_cookie') return !acc.cookie_status || acc.cookie_status === 'no_cookie';
      if (accountFilter === 'flagged') return Boolean(acc.flagged);
      return true;
    });
  }, [emails, searchQuery, accountFilter]);

  // Filtered Cookies
  const filteredCookies = useMemo(() => {
    return cookies.filter((ck) => {
      const matchSearch =
        ck.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (ck.account_name || '').toLowerCase().includes(searchQuery.toLowerCase());
      if (!matchSearch) return false;

      if (cookieFilter === 'active') return ck.status === 'active';
      if (cookieFilter === 'needs_login') return ck.status === 'needs_login';
      if (cookieFilter === 'expired') return ck.status === 'expired' || ck.status === 'invalid';
      return true;
    });
  }, [cookies, searchQuery, cookieFilter]);

  // Host Metric Calculations
  const memTotal = hostMetrics.memory ? Math.round(hostMetrics.memory.total / (1024 * 1024 * 1024) * 10) / 10 : 0;
  const memUsed = hostMetrics.memory ? Math.round(hostMetrics.memory.used / (1024 * 1024 * 1024) * 10) / 10 : 0;
  const memPercent = memTotal > 0 ? Math.round((memUsed / memTotal) * 100) : 0;

  const diskTotal = hostMetrics.storage ? Math.round(hostMetrics.storage.total / (1024 * 1024 * 1024) * 10) / 10 : 0;
  const diskUsed = hostMetrics.storage ? Math.round(hostMetrics.storage.used / (1024 * 1024 * 1024) * 10) / 10 : 0;
  const diskPercent = diskTotal > 0 ? Math.round((diskUsed / diskTotal) * 100) : 0;

  const cpuLoad1 = hostMetrics.cpu?.load_1 ? hostMetrics.cpu.load_1.toFixed(2) : '0.15';
  const cpuLoad5 = hostMetrics.cpu?.load_5 ? hostMetrics.cpu.load_5.toFixed(2) : '0.20';
  const cpuCores = hostMetrics.cpu?.logical_cpus || 4;

  // ── Render ────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#0F172A] flex font-['Plus_Jakarta_Sans',sans-serif]">
      {/* ========================================================================= */}
      {/* SIDEBAR: "hitam tapi bukan kaya hitam" -> Slate-900 (#0F172A) Modern Sleek */}
      {/* ========================================================================= */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-[#0F172A] text-slate-300 border-r border-slate-800/80 flex flex-col justify-between transition-transform duration-200 lg:static lg:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Sidebar Header Brand */}
        <div>
          <div className="h-16 px-5 border-b border-slate-800/80 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center text-white font-extrabold shadow-lg shadow-emerald-500/20">
                <MapPin className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="font-bold text-base text-white tracking-tight">AutoBotix</span>
                  <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                    SaaS
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-medium">Master Akun & Review</p>
              </div>
            </div>
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden text-slate-400 hover:text-white p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <div className="p-3 space-y-1">
            <div className="px-3 pt-3 pb-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Menu Utama
            </div>

            <button
              onClick={() => { setActiveTab('overview'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'overview'
                  ? 'bg-slate-800 text-white shadow-xs border-l-3 border-emerald-500'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <BarChart3 className={`w-4 h-4 ${activeTab === 'overview' ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>Dashboard & Ringkasan</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/60 text-slate-300 font-mono">
                Live
              </span>
            </button>

            <button
              onClick={() => { setActiveTab('accounts'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'accounts'
                  ? 'bg-slate-800 text-white shadow-xs border-l-3 border-emerald-500'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Users className={`w-4 h-4 ${activeTab === 'accounts' ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>Master Akun Google</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/60 text-emerald-400 font-mono font-bold">
                {activeAccountsCount}/{emails.length}
              </span>
            </button>

            <button
              onClick={() => { setActiveTab('cookies'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'cookies'
                  ? 'bg-slate-800 text-white shadow-xs border-l-3 border-emerald-500'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Cookie className={`w-4 h-4 ${activeTab === 'cookies' ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>Kelola Cookie Sesi</span>
              </div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${
                activeCookiesCount > 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400'
              }`}>
                {activeCookiesCount} Aktif
              </span>
            </button>

            <button
              onClick={() => { setActiveTab('server'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'server'
                  ? 'bg-slate-800 text-white shadow-xs border-l-3 border-emerald-500'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Server className={`w-4 h-4 ${activeTab === 'server' ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>Manajemen Server</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/60 text-cyan-400 font-mono">
                Xvfb: 6
              </span>
            </button>

            <button
              onClick={() => { setActiveTab('businesses'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'businesses'
                  ? 'bg-slate-800 text-white shadow-xs border-l-3 border-emerald-500'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              <div className="flex items-center gap-3">
                <Building2 className={`w-4 h-4 ${activeTab === 'businesses' ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>Target Bisnis Maps</span>
              </div>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900/60 text-slate-300 font-mono">
                {businesses.length}
              </span>
            </button>

            <div className="pt-4 pb-1 px-3 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Monitor Visual
            </div>

            <button
              onClick={() => navigate('/worker')}
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800/60 transition-all cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <Monitor className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
                <span>Multi-Screen Viewer</span>
              </div>
              <ArrowUpRight className="w-3.5 h-3.5 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Sidebar Footer: Server & Admin Profile */}
        <div className="p-3 border-t border-slate-800/80 space-y-2">
          {/* Server Uptime Indicator */}
          <div className="bg-slate-950/60 rounded-xl p-2.5 border border-slate-800 text-slate-300 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="text-[11px] font-medium text-slate-300">Native Chromium</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-400 font-bold">ONLINE</span>
          </div>

          {/* Profile Card */}
          <div className="flex items-center justify-between px-2 py-1.5">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-emerald-400 shrink-0">
                AD
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-white truncate">Administrator</p>
                <p className="text-[10px] text-slate-400 truncate">autobotix.my.id</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Keluar"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* MAIN CONTENT AREA: Pure SaaS Light Mode (Crisp White & Slate-50)          */}
      {/* ========================================================================= */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-16 bg-white border-b border-slate-200/90 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 shadow-xs">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="lg:hidden p-2 text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer"
            >
              <Layers className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                {activeTab === 'overview' && 'Executive Dashboard & Ringkasan'}
                {activeTab === 'accounts' && 'Master Akun Google'}
                {activeTab === 'cookies' && 'Manajemen Cookie Sesi Browser'}
                {activeTab === 'server' && 'Manajemen Server & Worker Chromium'}
                {activeTab === 'businesses' && 'Target Bisnis Google Maps'}
              </h1>
              <p className="text-xs text-slate-500 hidden sm:block">
                AutoBotix Cloud Review SaaS • Native Linux Headless Engine
              </p>
            </div>
          </div>

          {/* Quick Header Actions */}
          <div className="flex items-center gap-2">
            {/* Live Check Google MyAccount Button */}
            <button
              onClick={handleCheckAccountNames}
              disabled={isCheckingNames}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-colors cursor-pointer disabled:opacity-50"
              title="Periksa nama profil akun & status sesi ke Google MyAccount"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isCheckingNames ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">
                {isCheckingNames ? 'Memindai Google...' : 'Cek Nama Akun Live'}
              </span>
            </button>

            {/* Fast Run Review Bot Modal trigger */}
            <button
              onClick={() => setShowFastRunModal(true)}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Jalankan Task</span>
            </button>

            {/* Emergency Stop */}
            <button
              onClick={handleEmergencyStop}
              className="p-2 rounded-xl text-slate-500 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
              title="Emergency Stop (Hentikan semua worker & browser)"
            >
              <Square className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Global Notifications Banner */}
        <div className="px-4 sm:px-6 pt-4">
          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-2xs mb-3">
              <div className="flex items-center gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{errorMsg}</span>
              </div>
              <button
                onClick={() => setErrorMsg('')}
                className="text-rose-500 hover:text-rose-800 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {successMsg && (
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-2xs mb-3">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>{successMsg}</span>
              </div>
              <button
                onClick={() => setSuccessMsg('')}
                className="text-emerald-500 hover:text-emerald-800 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* ===================================================================== */}
        {/* TAB 1: 📊 EXECUTIVE OVERVIEW & SAAS CHARTS                            */}
        {/* ===================================================================== */}
        {activeTab === 'overview' && (
          <main className="p-4 sm:p-6 space-y-6">
            {/* Top 4 KPI Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Card 1: Master Akun */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs hover:border-slate-300 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Master Akun Google
                  </span>
                  <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                    <Users className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
                    {emails.length}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">Akun Terdaftar</span>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-600">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>{activeAccountsCount} Akun Aktif</span>
                  </span>
                  {data?.flagged_emails > 0 && (
                    <span className="text-rose-600 font-semibold">{data.flagged_emails} Flagged</span>
                  )}
                </div>
              </div>

              {/* Card 2: Cookie Sesi */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs hover:border-slate-300 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Cookie Sesi Browser
                  </span>
                  <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    <Cookie className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-emerald-600 font-mono tracking-tight">
                    {activeCookiesCount}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">/ {cookies.length} Total Sesi</span>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-600">
                  <span className="text-amber-600 font-medium">
                    {needsLoginCookiesCount} Perlu Login
                  </span>
                  <span className="text-rose-600 font-medium">
                    {expiredCookiesCount} Kedaluwarsa
                  </span>
                </div>
              </div>

              {/* Card 3: Target Bisnis & Ulasan */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs hover:border-slate-300 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Ulasan Terkirim
                  </span>
                  <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                    <Sparkles className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
                    {queueMetrics.reviewed || 0}
                  </span>
                  <span className="text-xs text-emerald-600 font-semibold flex items-center gap-0.5">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Sukses
                  </span>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-600">
                  <span>{businesses.length} Target Bisnis</span>
                  <span className="text-amber-600 font-medium">{queueMetrics.pending || 0} Antrean</span>
                </div>
              </div>

              {/* Card 4: Infrastruktur Server */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs hover:border-slate-300 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Infrastruktur Host
                  </span>
                  <div className="w-8 h-8 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center">
                    <Server className="w-4 h-4" />
                  </div>
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
                    {displays.length}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">Display Xvfb</span>
                </div>
                <div className="mt-3 flex items-center justify-between text-xs text-slate-600">
                  <span>RAM: {memUsed}/{memTotal} GB</span>
                  <span className="font-mono text-emerald-600 font-semibold">{memPercent}%</span>
                </div>
              </div>
            </div>

            {/* Middle Section: SaaS Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Chart 1: Review Velocity & Growth Chart (SVG Area Chart) */}
              <div className="lg:col-span-2 bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-sm text-slate-900">Performa & Aktivitas Ulasan Bot</h3>
                    <p className="text-xs text-slate-500">Distribusi ulasan sukses vs antrean waktu nyata</p>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="flex items-center gap-1 text-slate-600 font-medium">
                      <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span> Sukses ({queueMetrics.reviewed || 0})
                    </span>
                    <span className="flex items-center gap-1 text-slate-600 font-medium ml-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Antrean ({queueMetrics.pending || 0})
                    </span>
                  </div>
                </div>

                {/* SVG Area Chart Graphic */}
                <div className="h-56 w-full relative">
                  <svg className="w-full h-full" viewBox="0 0 600 200" preserveAspectRatio="none">
                    <defs>
                      <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#2563EB" stopOpacity="0.3" />
                        <stop offset="100%" stopColor="#2563EB" stopOpacity="0.0" />
                      </linearGradient>
                      <linearGradient id="pendingGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.25" />
                        <stop offset="100%" stopColor="#F59E0B" stopOpacity="0.0" />
                      </linearGradient>
                    </defs>

                    {/* Horizontal Grid lines */}
                    <line x1="0" y1="40" x2="600" y2="40" stroke="#E2E8F0" strokeDasharray="3 3" />
                    <line x1="0" y1="90" x2="600" y2="90" stroke="#E2E8F0" strokeDasharray="3 3" />
                    <line x1="0" y1="140" x2="600" y2="140" stroke="#E2E8F0" strokeDasharray="3 3" />
                    <line x1="0" y1="190" x2="600" y2="190" stroke="#CBD5E1" />

                    {/* Area 1: Reviewed Reviews */}
                    <path
                      d="M 0 170 Q 100 130, 200 110 T 400 65 T 600 30 L 600 190 L 0 190 Z"
                      fill="url(#areaGradient)"
                    />
                    <path
                      d="M 0 170 Q 100 130, 200 110 T 400 65 T 600 30"
                      fill="none"
                      stroke="#2563EB"
                      strokeWidth="3"
                    />

                    {/* Area 2: Pending Reviews Line */}
                    <path
                      d="M 0 185 Q 120 160, 250 140 T 450 120 T 600 115"
                      fill="none"
                      stroke="#F59E0B"
                      strokeWidth="2.5"
                      strokeDasharray="4 4"
                    />

                    {/* Data Points */}
                    <circle cx="200" cy="110" r="4" fill="#2563EB" stroke="#FFFFFF" strokeWidth="2" />
                    <circle cx="400" cy="65" r="4" fill="#2563EB" stroke="#FFFFFF" strokeWidth="2" />
                    <circle cx="600" cy="30" r="5" fill="#2563EB" stroke="#FFFFFF" strokeWidth="2" />
                  </svg>
                </div>

                <div className="flex justify-between items-center text-[11px] text-slate-500 font-mono mt-2 pt-2 border-t border-slate-100">
                  <span>Batch 1 (Awal)</span>
                  <span>Batch 2</span>
                  <span>Batch 3</span>
                  <span>Batch 4</span>
                  <span>Hari Ini (Real-Time)</span>
                </div>
              </div>

              {/* Chart 2: Cookie Session Health (SVG Donut Chart) */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-sm text-slate-900">Kesehatan Sesi Cookie</h3>
                  <p className="text-xs text-slate-500">Rasio status akun terverifikasi Google</p>

                  {/* Donut Graphic */}
                  <div className="my-6 flex items-center justify-center relative">
                    <svg className="w-40 h-40 transform -rotate-90" viewBox="0 0 120 120">
                      {/* Background circle */}
                      <circle cx="60" cy="60" r="48" stroke="#F1F5F9" strokeWidth="14" fill="none" />
                      {/* Active Arc (Emerald) */}
                      <circle
                        cx="60"
                        cy="60"
                        r="48"
                        stroke="#10B981"
                        strokeWidth="14"
                        fill="none"
                        strokeDasharray="301.6"
                        strokeDashoffset={
                          cookies.length > 0
                            ? 301.6 - (activeCookiesCount / cookies.length) * 301.6
                            : 301.6
                        }
                        strokeLinecap="round"
                        className="transition-all duration-1000"
                      />
                    </svg>

                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span className="text-2xl font-extrabold text-slate-900 font-mono">
                        {cookies.length > 0 ? Math.round((activeCookiesCount / cookies.length) * 100) : 0}%
                      </span>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Sesi Siap</span>
                    </div>
                  </div>
                </div>

                {/* Legend list */}
                <div className="space-y-2 border-t border-slate-100 pt-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-slate-600 font-medium">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                      <span>Aktif & Terverifikasi</span>
                    </span>
                    <span className="font-bold text-slate-900 font-mono">{activeCookiesCount}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-slate-600 font-medium">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                      <span>Perlu Login Ulang</span>
                    </span>
                    <span className="font-bold text-slate-900 font-mono">{needsLoginCookiesCount}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-slate-600 font-medium">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                      <span>Kedaluwarsa / Invalid</span>
                    </span>
                    <span className="font-bold text-slate-900 font-mono">{expiredCookiesCount}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Row: Virtual Displays & Quick Business Launch */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Virtual Display Slots */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-sm text-slate-900">Virtual Xvfb Displays</h3>
                    <p className="text-xs text-slate-500">Alokasi port layar browser Chromium</p>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                    6 Display Siap
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2.5">
                  {[':99', ':100', ':101', ':102', ':103', ':104'].map((disp, i) => (
                    <div
                      key={disp}
                      className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex flex-col items-center justify-center text-center hover:border-slate-300 transition-colors"
                    >
                      <Tv className="w-4 h-4 text-emerald-600 mb-1" />
                      <span className="font-mono font-bold text-xs text-slate-800">{disp}</span>
                      <span className="text-[10px] text-slate-500">Slot {i + 1}</span>
                      <span className="mt-1 inline-flex items-center gap-1 text-[9px] text-emerald-600 font-semibold">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                        Ready
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Target Bisnis Fast List */}
              <div className="lg:col-span-2 bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="font-bold text-sm text-slate-900">Target Google Maps Terbaru</h3>
                    <p className="text-xs text-slate-500">Daftar bisnis yang siap menerima ulasan bot</p>
                  </div>
                  <button
                    onClick={() => setActiveTab('businesses')}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <span>Lihat Semua</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="divide-y divide-slate-100">
                  {businesses.slice(0, 4).map((b) => (
                    <div key={b.id} className="py-3 flex items-center justify-between">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">
                          {b.id}
                        </div>
                        <div className="min-w-0">
                          <p className="font-bold text-xs text-slate-900 truncate">{b.name}</p>
                          <a
                            href={b.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[11px] text-blue-600 hover:underline truncate block"
                          >
                            {b.url}
                          </a>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setFastRunForm((prev) => ({ ...prev, business_id: String(b.id) }));
                          setShowFastRunModal(true);
                        }}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-600 border border-slate-200 transition-colors shrink-0 ml-3"
                      >
                        Jalankan
                      </button>
                    </div>
                  ))}
                  {businesses.length === 0 && (
                    <div className="py-8 text-center text-xs text-slate-500">
                      Belum ada target bisnis Google Maps terdaftar.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </main>
        )}

        {/* ===================================================================== */}
        {/* TAB 2: 👤 MASTER AKUN GOOGLE (DAFTAR & KELOLA AKUN)                   */}
        {/* ===================================================================== */}
        {activeTab === 'accounts' && (
          <main className="p-4 sm:p-6 space-y-5">
            {/* Action & Filter Toolbar */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
              {/* Search Box */}
              <div className="relative flex-1 max-w-md">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Cari berdasarkan nama profil atau email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={handleCheckAccountNames}
                  disabled={isCheckingNames}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-colors cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isCheckingNames ? 'animate-spin' : ''}`} />
                  <span>{isCheckingNames ? 'Memindai Google...' : 'Cek Nama Akun Live'}</span>
                </button>

                <button
                  onClick={handleUnflagAll}
                  className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors cursor-pointer"
                >
                  Unflag Semua
                </button>

                <button
                  onClick={() => setShowAddAccountModal(true)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Tambah Akun Baru</span>
                </button>
              </div>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
              {[
                { id: 'all', label: `Semua (${emails.length})` },
                { id: 'active', label: `● Aktif (${activeAccountsCount})` },
                { id: 'needs_login', label: `▲ Perlu Login (${emails.filter((e) => e.cookie_status === 'needs_login').length})` },
                { id: 'expired', label: `✖ Kedaluwarsa (${emails.filter((e) => e.cookie_status === 'expired').length})` },
                { id: 'no_cookie', label: `Belum Ada Cookie (${emails.filter((e) => !e.cookie_status || e.cookie_status === 'no_cookie').length})` },
                { id: 'flagged', label: `Flagged (${emails.filter((e) => e.flagged).length})` },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setAccountFilter(f.id)}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition-colors shrink-0 cursor-pointer ${
                    accountFilter === f.id
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Accounts Master Table */}
            <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="py-3 px-4">Profil Akun Google</th>
                      <th className="py-3 px-4">Email Google</th>
                      <th className="py-3 px-4">Status Sesi Cookie</th>
                      <th className="py-3 px-4">Flag Keamanan</th>
                      <th className="py-3 px-4">Kredensial</th>
                      <th className="py-3 px-4 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredAccounts.map((acc) => {
                      const isAktif = acc.cookie_status === 'active';
                      const isNeedsLogin = acc.cookie_status === 'needs_login';
                      const isExpired = acc.cookie_status === 'expired';
                      const isNoCookie = !acc.cookie_status || acc.cookie_status === 'no_cookie';

                      return (
                        <tr key={acc.id} className="hover:bg-slate-50/60 transition-colors">
                          {/* Nama Profil Akun */}
                          <td className="py-3.5 px-4 font-medium">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-indigo-600 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-2xs">
                                {(acc.account_name || acc.email || 'A').slice(0, 1).toUpperCase()}
                              </div>
                              <div>
                                <p className="font-bold text-slate-900">
                                  {acc.account_name || (
                                    <span className="text-slate-400 font-normal italic">
                                      {isAktif ? 'Nama Terdaftar' : '- Sesi Belum Login -'}
                                    </span>
                                  )}
                                </p>
                                <span className="text-[10px] text-slate-400 font-mono">ID #{acc.id}</span>
                              </div>
                            </div>
                          </td>

                          {/* Email Akun */}
                          <td className="py-3.5 px-4">
                            <span className="font-mono text-slate-700 select-all">{acc.email}</span>
                          </td>

                          {/* Status Sesi Cookie */}
                          <td className="py-3.5 px-4">
                            {isAktif && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                AKTIF
                              </span>
                            )}
                            {isNeedsLogin && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                                <AlertTriangle className="w-3 h-3 text-amber-600" />
                                PERLU LOGIN
                              </span>
                            )}
                            {isExpired && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                                <X className="w-3 h-3 text-rose-600" />
                                KEDALUWARSA
                              </span>
                            )}
                            {isNoCookie && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-500 border border-slate-200">
                                TIDAK ADA COOKIE
                              </span>
                            )}
                          </td>

                          {/* Status Flag */}
                          <td className="py-3.5 px-4">
                            {acc.flagged ? (
                              <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                                <ShieldAlert className="w-3 h-3" /> Flagged
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-600">
                                <ShieldCheck className="w-3 h-3 text-emerald-600" /> Siap
                              </span>
                            )}
                          </td>

                          {/* Kredensial */}
                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-1.5 text-slate-500 text-[11px]">
                              {acc.password ? (
                                <span className="bg-slate-100 px-1.5 py-0.5 rounded font-mono">••••••••</span>
                              ) : (
                                <span className="text-slate-400">Cookie Only</span>
                              )}
                              {acc.totp_secret && (
                                <span className="bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded font-bold text-[9px]">
                                  2FA
                                </span>
                              )}
                            </div>
                          </td>

                          {/* Aksi */}
                          <td className="py-3.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-1">
                              {/* Pasang / Update Cookie button */}
                              <button
                                onClick={() => {
                                  setCookieForm({ email: acc.email, cookie_json: '' });
                                  setShowCookieModal(true);
                                }}
                                title="Pasang / Perbarui Cookie"
                                className="p-1.5 text-slate-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors cursor-pointer"
                              >
                                <Cookie className="w-4 h-4" />
                              </button>

                              {/* Toggle Unflag */}
                              {Boolean(acc.flagged) && (
                                <button
                                  onClick={() => handleToggleUnflag(acc.id, acc.email, true)}
                                  title="Pulihkan Akun (Unflag)"
                                  className="p-1.5 text-slate-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                                >
                                  <Check className="w-4 h-4" />
                                </button>
                              )}

                              {/* Delete Account */}
                              <button
                                onClick={() => handleDeleteAccount(acc.id, acc.email)}
                                title="Hapus Akun"
                                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}

                    {filteredAccounts.length === 0 && (
                      <tr>
                        <td colSpan="6" className="py-12 text-center text-xs text-slate-500">
                          Tidak ada akun Google yang cocok dengan filter pencarian.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </main>
        )}

        {/* ===================================================================== */}
        {/* TAB 3: 🍪 KELOLA COOKIE SESI BROWSER                                  */}
        {/* ===================================================================== */}
        {activeTab === 'cookies' && (
          <main className="p-4 sm:p-6 space-y-5">
            {/* Toolbar */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="relative flex-1 max-w-md">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Cari cookie berdasarkan email akun..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                />
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleCheckAccountNames}
                  disabled={isCheckingNames}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 transition-colors cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isCheckingNames ? 'animate-spin' : ''}`} />
                  <span>{isCheckingNames ? 'Memindai Google...' : 'Cek Nama Akun Live'}</span>
                </button>

                <button
                  onClick={() => setShowCookieModal(true)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Tambah Cookie Baru</span>
                </button>
              </div>
            </div>

            {/* Cookie Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
              {[
                { id: 'all', label: `Semua Cookie (${cookies.length})` },
                { id: 'active', label: `● Sesi Aktif (${activeCookiesCount})` },
                { id: 'needs_login', label: `▲ Perlu Login (${needsLoginCookiesCount})` },
                { id: 'expired', label: `✖ Kedaluwarsa (${expiredCookiesCount})` },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setCookieFilter(f.id)}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition-colors shrink-0 cursor-pointer ${
                    cookieFilter === f.id
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Cookies Table */}
            <div className="bg-white border border-slate-200/90 rounded-2xl overflow-hidden shadow-xs">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="py-3 px-4">Nama Akun Google</th>
                      <th className="py-3 px-4">Email Sesi</th>
                      <th className="py-3 px-4">Status Sesi</th>
                      <th className="py-3 px-4">Diagnosa / Alasan Respon</th>
                      <th className="py-3 px-4">Terakhir Diperbarui</th>
                      <th className="py-3 px-4 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredCookies.map((ck) => {
                      const isAktif = ck.status === 'active';
                      const isNeedsLogin = ck.status === 'needs_login';
                      const isExpired = ck.status === 'expired' || ck.status === 'invalid';

                      return (
                        <tr key={ck.id} className="hover:bg-slate-50/60 transition-colors">
                          <td className="py-3.5 px-4 font-medium">
                            <div className="flex items-center gap-2.5">
                              <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0">
                                <Cookie className="w-3.5 h-3.5" />
                              </div>
                              <div>
                                <p className="font-bold text-slate-900">
                                  {ck.account_name || (
                                    <span className="text-slate-400 font-normal italic">- Belum Terverifikasi -</span>
                                  )}
                                </p>
                                <span className="text-[10px] text-slate-400 font-mono">Cookie #{ck.id}</span>
                              </div>
                            </div>
                          </td>

                          <td className="py-3.5 px-4 font-mono text-slate-700 select-all">
                            {ck.email}
                          </td>

                          <td className="py-3.5 px-4">
                            {isAktif && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                AKTIF
                              </span>
                            )}
                            {isNeedsLogin && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                                <AlertTriangle className="w-3 h-3 text-amber-600" />
                                PERLU LOGIN
                              </span>
                            )}
                            {isExpired && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                                <X className="w-3 h-3 text-rose-600" />
                                KEDALUWARSA
                              </span>
                            )}
                          </td>

                          <td className="py-3.5 px-4 text-slate-500 max-w-xs truncate" title={ck.error_reason || ''}>
                            {ck.error_reason || (isAktif ? 'Sesi Google aktif dan terverifikasi.' : '-')}
                          </td>

                          <td className="py-3.5 px-4 text-slate-500 text-[11px] font-mono">
                            {ck.updated_at || ck.last_checked_at || '-'}
                          </td>

                          <td className="py-3.5 px-4 text-right">
                            <div className="flex items-center justify-end gap-1">
                              {/* Uji Validitas */}
                              <button
                                onClick={() => handleTestCookie(ck.id, ck.email)}
                                title="Uji Validitas Sesi Google"
                                className="p-1.5 text-slate-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg transition-colors cursor-pointer"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </button>

                              {/* Lihat Snippet JSON */}
                              <button
                                onClick={() => setSnippetModalCookie(ck)}
                                title="Lihat Payload Token"
                                className="p-1.5 text-slate-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                              >
                                <Eye className="w-4 h-4" />
                              </button>

                              {/* Hapus Cookie */}
                              <button
                                onClick={() => handleDeleteCookie(ck.id, ck.email)}
                                title="Hapus Cookie"
                                className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}

                    {filteredCookies.length === 0 && (
                      <tr>
                        <td colSpan="6" className="py-12 text-center text-xs text-slate-500">
                          Belum ada cookie Google terdaftar.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Panduan Singkat Export Cookie */}
            <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-600 flex items-start gap-3">
              <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold text-slate-900">Panduan Tambah Cookie Google</p>
                <p className="mt-1 text-slate-600 leading-relaxed">
                  Buka Google Chrome di laptop/PC Anda, pastikan sudah login ke akun Google di maps.google.com atau myaccount.google.com.
                  Buka ekstensi <b>Cookie-Editor</b> ➔ Klik <b>Export</b> ➔ Pilih <b>Export as JSON</b>.
                  Lalu tempelkan (*paste*) JSON ke tombol <b>Tambah Cookie Baru</b> di atas. Sistem akan memverifikasi sesi dan mengekstrak nama profil akun Google Anda secara otomatis.
                </p>
              </div>
            </div>
          </main>
        )}

        {/* ===================================================================== */}
        {/* TAB 4: 🖥️ MANAJEMEN SERVER & WORKER                                   */}
        {/* ===================================================================== */}
        {activeTab === 'server' && (
          <main className="p-4 sm:p-6 space-y-6">
            {/* Server Overview Resource Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* CPU Load */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase">CPU Load Avg</span>
                  <Cpu className="w-4 h-4 text-blue-600" />
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900 font-mono">{cpuLoad1}</span>
                  <span className="text-xs text-slate-500">/ {cpuCores} Cores</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-2 font-mono">Load 5m: {cpuLoad5}</p>
              </div>

              {/* Memory RAM */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase">Memory RAM</span>
                  <Activity className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900 font-mono">{memUsed}</span>
                  <span className="text-xs text-slate-500">/ {memTotal} GB ({memPercent}%)</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                  <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${memPercent}%` }}></div>
                </div>
              </div>

              {/* Disk Storage */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase">Disk Storage</span>
                  <HardDrive className="w-4 h-4 text-purple-600" />
                </div>
                <div className="mt-3 flex items-baseline gap-2">
                  <span className="text-3xl font-extrabold text-slate-900 font-mono">{diskUsed}</span>
                  <span className="text-xs text-slate-500">/ {diskTotal} GB ({diskPercent}%)</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-1.5 mt-3 overflow-hidden">
                  <div className="bg-purple-500 h-full rounded-full" style={{ width: `${diskPercent}%` }}></div>
                </div>
              </div>

              {/* Native Engine */}
              <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-500 uppercase">Browser Engine</span>
                  <Radio className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="mt-3">
                  <span className="text-lg font-bold text-slate-900">Chromium 155</span>
                  <p className="text-xs text-emerald-600 font-semibold mt-0.5">Native Linux (Zero VM)</p>
                </div>
                <p className="text-[11px] text-slate-500 mt-2 font-mono">Display: :99 s/d :104</p>
              </div>
            </div>

            {/* Virtual Displays Details */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-bold text-sm text-slate-900">Virtual Displays Xvfb (6 Layar Paralel)</h3>
                  <p className="text-xs text-slate-500">Display buffer RAM tempat Chromium merender GUI Google Maps</p>
                </div>
                <button
                  onClick={() => navigate('/worker')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors"
                >
                  <Tv className="w-3.5 h-3.5" />
                  <span>Buka Live Multi-Screen Monitor</span>
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {[':99', ':100', ':101', ':102', ':103', ':104'].map((disp, i) => (
                  <div
                    key={disp}
                    className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-white border border-slate-200 flex items-center justify-center font-bold text-xs text-slate-800 shadow-2xs">
                        {i + 1}
                      </div>
                      <div>
                        <p className="font-mono font-bold text-xs text-slate-900">Display {disp}</p>
                        <p className="text-[10px] text-slate-500">1366x768x24 (Slot {i + 1})</p>
                      </div>
                    </div>
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-semibold bg-emerald-100/80 text-emerald-800 border border-emerald-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                      Aktif
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Server Daemon Services Status & Emergency Stop */}
            <div className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs">
              <h3 className="font-bold text-sm text-slate-900 mb-1">Status Layanan Daemon Server</h3>
              <p className="text-xs text-slate-500 mb-4">Layanan systemd yang menjaga bot review berjalan 24/7</p>

              <div className="space-y-3">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <div>
                      <p className="font-mono font-bold text-xs text-slate-900">google-review-automation.service</p>
                      <p className="text-[11px] text-slate-500">Flask Web API & Remote Client Hub (Port 5000)</p>
                    </div>
                  </div>
                  <span className="font-mono text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                    ACTIVE / RUNNING
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    <div>
                      <p className="font-mono font-bold text-xs text-slate-900">google-review-worker.service</p>
                      <p className="text-[11px] text-slate-500">Background Worker Chromium Scheduler & Dispatcher</p>
                    </div>
                  </div>
                  <span className="font-mono text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                    ACTIVE / RUNNING
                  </span>
                </div>
              </div>

              {/* Action Controls */}
              <div className="mt-6 pt-5 border-t border-slate-100 flex items-center justify-between flex-wrap gap-3">
                <div className="text-xs text-slate-500">
                  Operasi pemulihan darurat dan reset memori antrean worker.
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={loadDashboardData}
                    className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors cursor-pointer"
                  >
                    Refresh Status
                  </button>
                  <button
                    onClick={handleEmergencyStop}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white shadow-xs transition-colors cursor-pointer"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>Emergency Stop (Kill All)</span>
                  </button>
                </div>
              </div>
            </div>
          </main>
        )}

        {/* ===================================================================== */}
        {/* TAB 5: 🏢 TARGET BISNIS GOOGLE MAPS                                   */}
        {/* ===================================================================== */}
        {activeTab === 'businesses' && (
          <main className="p-4 sm:p-6 space-y-5">
            <div className="bg-white border border-slate-200/90 rounded-2xl p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="relative flex-1 max-w-md">
                <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Cari target bisnis Google Maps..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 placeholder-slate-400 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
                />
              </div>

              <button
                onClick={() => setShowAddBizModal(true)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-xs transition-colors cursor-pointer self-start md:self-auto"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Tambah Target Bisnis Baru</span>
              </button>
            </div>

            {/* Business Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {businesses
                .filter(
                  (b) =>
                    b.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    (b.url || '').toLowerCase().includes(searchQuery.toLowerCase())
                )
                .map((b) => (
                  <div
                    key={b.id}
                    className="bg-white border border-slate-200/90 rounded-2xl p-5 shadow-xs flex flex-col justify-between hover:border-slate-300 transition-all"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-xs shrink-0">
                            <MapPin className="w-4 h-4" />
                          </div>
                          <div className="min-w-0">
                            <h4 className="font-bold text-sm text-slate-900 truncate">{b.name}</h4>
                            <span className="text-[10px] text-slate-400 font-mono">ID #{b.id}</span>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteBusiness(b.id, b.name)}
                          className="text-slate-400 hover:text-rose-600 p-1 rounded transition-colors"
                          title="Hapus Bisnis"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>

                      <div className="mt-3">
                        <a
                          href={b.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-blue-600 hover:underline truncate block"
                          title={b.url}
                        >
                          {b.url}
                        </a>
                      </div>
                    </div>

                    <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
                      <span className="text-xs text-slate-500 font-medium">Ulasan Otomatis</span>
                      <button
                        onClick={() => {
                          setFastRunForm((prev) => ({ ...prev, business_id: String(b.id) }));
                          setShowFastRunModal(true);
                        }}
                        className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 transition-colors flex items-center gap-1.5"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>Luncurkan Bot</span>
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </main>
        )}
      </div>

      {/* ========================================================================= */}
      {/* MODALS                                                                    */}
      {/* ========================================================================= */}

      {/* Modal: Tambah Akun Google */}
      {showAddAccountModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-md w-full shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                <span>Tambah Akun Google Baru</span>
              </h3>
              <button
                onClick={() => setShowAddAccountModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddAccount} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email Google *</label>
                <input
                  type="email"
                  required
                  placeholder="contoh: budi.santoso@gmail.com"
                  value={accountForm.email}
                  onChange={(e) => setAccountForm({ ...accountForm, email: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Password (Opsional jika login via Cookie)
                </label>
                <input
                  type="password"
                  placeholder="Password akun jika ada"
                  value={accountForm.password}
                  onChange={(e) => setAccountForm({ ...accountForm, password: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  2FA TOTP Secret Key (Opsional)
                </label>
                <input
                  type="text"
                  placeholder="Contoh: JBSWY3DPEHPK3PXP"
                  value={accountForm.totp_secret}
                  onChange={(e) => setAccountForm({ ...accountForm, totp_secret: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddAccountModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-xs transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Menyimpan...' : 'Simpan Akun'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Tambah / Perbarui Cookie */}
      {showCookieModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-lg w-full shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                <Cookie className="w-5 h-5 text-emerald-600" />
                <span>Tambah / Perbarui Cookie Sesi</span>
              </h3>
              <button
                onClick={() => setShowCookieModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddCookie} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Email Akun (Opsional, otomatis diekstrak jika ada di JSON)
                </label>
                <input
                  type="text"
                  placeholder="contoh: budi.santoso@gmail.com"
                  value={cookieForm.email}
                  onChange={(e) => setCookieForm({ ...cookieForm, email: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  JSON Cookie dari Cookie-Editor *
                </label>
                <textarea
                  required
                  rows={8}
                  placeholder='Tempelkan JSON dari Cookie-Editor di sini (contoh: [{"name": "SID", "value": "..."}, ...])'
                  value={cookieForm.cookie_json}
                  onChange={(e) => setCookieForm({ ...cookieForm, cookie_json: e.target.value })}
                  className="w-full p-3 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 font-mono"
                />
              </div>

              <p className="text-[11px] text-slate-500 leading-relaxed">
                ℹ️ Sistem akan langsung memverifikasi sesi ke Google MyAccount secara otomatis dan mengekstrak nama profil pemilik akun.
              </p>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCookieModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-xs transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Memverifikasi...' : 'Simpan & Verifikasi Google'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Tambah Target Bisnis */}
      {showAddBizModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-md w-full shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                <Building2 className="w-5 h-5 text-blue-600" />
                <span>Tambah Target Bisnis Maps</span>
              </h3>
              <button
                onClick={() => setShowAddBizModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddBusiness} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Nama Bisnis / Tempat *</label>
                <input
                  type="text"
                  required
                  placeholder="contoh: RM Sederhana Senopati"
                  value={bizForm.name}
                  onChange={(e) => setBizForm({ ...bizForm, name: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">URL Google Maps *</label>
                <input
                  type="url"
                  required
                  placeholder="https://maps.google.com/?cid=..."
                  value={bizForm.url}
                  onChange={(e) => setBizForm({ ...bizForm, url: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddBizModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-xs transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Menyimpan...' : 'Simpan Target Bisnis'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Fast Run Review Bot */}
      {showFastRunModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-md w-full shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-base text-slate-900 flex items-center gap-2">
                <Play className="w-5 h-5 text-blue-600 fill-current" />
                <span>Luncurkan Ulasan Bot Otomatis</span>
              </h3>
              <button
                onClick={() => setShowFastRunModal(false)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleFastRunSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Target Bisnis *</label>
                <select
                  required
                  value={fastRunForm.business_id}
                  onChange={(e) => setFastRunForm({ ...fastRunForm, business_id: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  <option value="">-- Pilih Bisnis Target --</option>
                  {businesses.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} (ID #{b.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Jumlah Browser / Slot Paralel (1 s/d 6)
                </label>
                <input
                  type="number"
                  min="1"
                  max={Math.max(1, Math.min(6, activeCookiesCount || 6))}
                  value={fastRunForm.slots}
                  onChange={(e) => setFastRunForm({ ...fastRunForm, slots: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  Maksimal sesuai jumlah akun aktif ({activeCookiesCount} akun siap).
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Rating Bintang</label>
                <select
                  value={fastRunForm.star_rating}
                  onChange={(e) => setFastRunForm({ ...fastRunForm, star_rating: e.target.value })}
                  className="w-full px-3.5 py-2 text-xs border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:outline-hidden focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
                >
                  <option value="5">⭐⭐⭐⭐⭐ 5 Bintang (Sangat Puas)</option>
                  <option value="4">⭐⭐⭐⭐ 4 Bintang (Puas)</option>
                  <option value="3">⭐⭐⭐ 3 Bintang (Netral)</option>
                </select>
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowFastRunModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submitting || activeCookiesCount === 0}
                  className="px-4 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl shadow-xs transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Meluncurkan...' : 'Luncurkan Sekarang 🚀'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: View Cookie Snippet */}
      {snippetModalCookie && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 max-w-lg w-full shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Cookie className="w-4 h-4 text-emerald-600" />
                <span>Payload Cookie #{snippetModalCookie.id} ({snippetModalCookie.email})</span>
              </h3>
              <button
                onClick={() => setSnippetModalCookie(null)}
                className="text-slate-400 hover:text-slate-700 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-900 text-slate-200 p-3 rounded-xl font-mono text-[11px] max-h-80 overflow-y-auto">
              <pre className="whitespace-pre-wrap">
                {snippetModalCookie.cookie_json || 'Tidak ada data JSON tersimpan.'}
              </pre>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setSnippetModalCookie(null)}
                className="px-4 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
