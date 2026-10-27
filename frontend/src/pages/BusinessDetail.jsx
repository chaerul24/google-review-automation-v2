import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  Square,
  RefreshCw,
  ExternalLink,
  Star,
  Settings,
  Terminal,
  Clock,
  ShieldCheck,
  AlertCircle,
  Eye,
  RotateCcw,
  Trash2,
  CheckCircle2,
  Plus,
  Minus,
  Sparkles,
  Search,
  X,
  Layers,
  Check,
  MessageSquare,
} from 'lucide-react';
import { api } from '../api/client';
import StatusBadge from '../components/StatusBadge';
import LiveStreamViewer from '../components/LiveStreamViewer';
import ReviewPersonaModal from '../components/ReviewPersonaModal';

export default function BusinessDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [workerRunning, setWorkerRunning] = useState(false);
  const [activeTab, setActiveTab] = useState('queue'); // 'queue' | 'reviews' | 'config'
  const [reviewSearch, setReviewSearch] = useState('');

  // Star queue input form
  const [starCounts, setStarCounts] = useState({
    star_1: 0,
    star_2: 0,
    star_3: 0,
    star_4: 0,
    star_5: 1,
  });
  const [selectedLanguage, setSelectedLanguage] = useState('Indonesian');
  const [selectedStyle, setSelectedStyle] = useState('random');
  const [selectedEmails, setSelectedEmails] = useState([]);

  // Config form
  const [configForm, setConfigForm] = useState({
    business_description: '',
    review_style: 'random',
    delay_seconds: 60,
  });

  // Modal inspection
  const [inspectModal, setInspectModal] = useState({ show: false, data: null, loading: false });
  const [showPersonaModal, setShowPersonaModal] = useState(false);

  const [notification, setNotification] = useState({ type: '', message: '' });
  const [actionLoading, setActionLoading] = useState(false);
  const logContainerRef = useRef(null);

  const loadData = async () => {
    try {
      const res = await api.getBusinessDetail(id);
      setData(res);
      if (res.config) {
        setConfigForm({
          business_description: res.config.business_description || '',
          review_style: res.config.review_style || 'random',
          delay_seconds: res.config.delay_seconds || 60,
        });
      }
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Gagal memuat detail bisnis.' });
    } finally {
      setLoading(false);
    }
  };

  const pollLogs = async () => {
    try {
      const res = await api.getProcessLogs(id);
      if (res && res.logs) {
        setLogs(res.logs);
        setWorkerRunning(res.status === 'reviewing');
      }
    } catch (err) {
      console.debug('Log poll failed:', err);
    }
  };

  useEffect(() => {
    loadData();
    pollLogs();
    const interval = setInterval(pollLogs, 3000);
    return () => clearInterval(interval);
  }, [id]);

  // Auto-scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const updateStarCount = (star, delta) => {
    setStarCounts((prev) => {
      const current = prev[`star_${star}`] || 0;
      const next = Math.max(0, Math.min(50, current + delta));
      return { ...prev, [`star_${star}`]: next };
    });
  };

  const handleStartBot = async () => {
    const totalStars = Object.values(starCounts).reduce((a, b) => a + Number(b), 0);
    if (totalStars <= 0) {
      alert('Pilih setidaknya 1 bintang ulasan untuk antrean.');
      return;
    }

    setActionLoading(true);
    try {
      setNotification({ type: 'info', message: 'Menginisialisasi tugas review...' });
      const payload = {
        star_1_count: starCounts.star_1,
        star_2_count: starCounts.star_2,
        star_3_count: starCounts.star_3,
        star_4_count: starCounts.star_4,
        star_5_count: starCounts.star_5,
        selected_language: selectedLanguage,
        review_style: selectedStyle,
        selected_email_ids: selectedEmails,
      };
      const res = await api.startBot(id, payload);
      setNotification({
        type: 'success',
        message: `Berhasil! ${res.jobs_created || 0} tugas ulasan langsung mulai diproses worker.`,
      });
      loadData();
      pollLogs();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Gagal menjalankan bot review.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleStopBot = async () => {
    if (!confirm('Hentikan worker aktif dan hapus tugas yang masih dalam antrean pending?')) return;
    setActionLoading(true);
    try {
      const res = await api.stopBot(id);
      setNotification({
        type: 'info',
        message: `Worker dihentikan. ${res.jobs_deleted || 0} tugas antrean dibatalkan.`,
      });
      loadData();
      pollLogs();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Gagal menghentikan bot.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await api.saveBusinessConfig(id, configForm);
      setNotification({ type: 'success', message: 'Konfigurasi ulasan berhasil diperbarui!' });
      loadData();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Gagal menyimpan konfigurasi.' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleInspectReview = async (reviewId) => {
    setInspectModal({ show: true, data: null, loading: true });
    try {
      const res = await api.inspectReview(id, reviewId);
      setInspectModal({ show: true, data: res, loading: false });
    } catch (err) {
      setInspectModal({
        show: true,
        data: { status: 'error', message: err.message || 'Pemeriksaan gagal.' },
        loading: false,
      });
    }
  };

  const handleResetReview = async (reviewId) => {
    try {
      await api.resetReview(id, reviewId);
      setNotification({ type: 'success', message: 'Status review direset ke pending.' });
      loadData();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Gagal mereset review.' });
    }
  };

  const handleDeleteReview = async (reviewId) => {
    if (!confirm('Hapus item review ini dari daftar?')) return;
    try {
      await api.deleteReview(id, reviewId);
      setNotification({ type: 'success', message: 'Review dihapus.' });
      loadData();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Gagal menghapus review.' });
    }
  };

  if (loading && !data) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400 font-mono">Memuat detail bisnis...</span>
        </div>
      </div>
    );
  }

  const biz = data?.business || {};
  const reviews = data?.reviews || [];
  const allEmails = data?.all_emails || [];
  const usedEmailIds = new Set(data?.used_email_ids || []);

  const filteredReviews = reviews.filter((r) =>
    (r.email || '').toLowerCase().includes(reviewSearch.toLowerCase()) ||
    (r.review_text || '').toLowerCase().includes(reviewSearch.toLowerCase()) ||
    (r.status || '').toLowerCase().includes(reviewSearch.toLowerCase())
  );

  const totalSelectedStars = Object.values(starCounts).reduce((a, b) => a + Number(b), 0);

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800/80 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5 min-w-0">
          <Link
            to="/dashboard"
            className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors shrink-0"
            title="Kembali ke Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="min-w-0">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-base sm:text-lg font-extrabold text-white tracking-tight truncate">
                {biz.name}
              </h1>
              {workerRunning ? (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5 shadow-sm shadow-indigo-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping"></span>
                  Worker Aktif Berjalan
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">
                  Standby / Idle
                </span>
              )}
            </div>
            <a
              href={biz.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-indigo-400/90 hover:text-indigo-300 hover:underline flex items-center gap-1.5 mt-1 truncate"
            >
              <ExternalLink className="w-3 h-3 shrink-0" />
              <span className="truncate max-w-xs sm:max-w-md">{biz.url}</span>
            </a>
          </div>
        </div>

        {/* Quick Launch / Stop Action */}
        <div className="flex items-center gap-2 shrink-0">
          {workerRunning ? (
            <button
              onClick={handleStopBot}
              disabled={actionLoading}
              className="px-4 py-2.5 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white flex items-center gap-2 shadow-lg shadow-rose-600/20 transition-all cursor-pointer disabled:opacity-50"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Hentikan Worker</span>
            </button>
          ) : (
            <button
              onClick={() => setActiveTab('queue')}
              className="px-4 py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white flex items-center gap-2 shadow-lg shadow-emerald-600/20 transition-all cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Mulai Antrean Review</span>
            </button>
          )}
        </div>
      </div>

      {/* Notifications Banner */}
      {notification.message && (
        <div
          className={`p-4 rounded-2xl text-xs flex items-center justify-between shadow-lg animate-in fade-in ${
            notification.type === 'error'
              ? 'bg-rose-500/10 border border-rose-500/20 text-rose-300 shadow-rose-950/20'
              : notification.type === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 shadow-emerald-950/20'
              : 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 shadow-indigo-950/20'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {notification.type === 'error' ? (
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            ) : (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            )}
            <span>{notification.message}</span>
          </div>
          <button
            onClick={() => setNotification({ type: '', message: '' })}
            className="p-1 rounded-lg hover:bg-white/10 transition-colors ml-4"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main 2-Column Responsive Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 cols): Tabs for Queue Controls, Review List, Config */}
        <div className="lg:col-span-7 space-y-5">
          {/* SubTab Navigation */}
          <div className="flex items-center gap-2 border-b border-slate-800/80 pb-3 overflow-x-auto no-scrollbar">
            <button
              onClick={() => setActiveTab('queue')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
                activeTab === 'queue'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              Antrean & Peluncuran
            </button>
            <button
              onClick={() => setActiveTab('reviews')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
                activeTab === 'reviews'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              Daftar Ulasan ({reviews.length})
            </button>
            <button
              onClick={() => setActiveTab('config')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 cursor-pointer ${
                activeTab === 'config'
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              Pengaturan Bisnis
            </button>
          </div>

          {/* SubTab 1: Queue Config & Launch Panel */}
          {activeTab === 'queue' && (
            <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 space-y-6 shadow-xl">
              <div>
                <div className="flex items-center justify-between">
                  <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
                    <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                    <span>Distribusi Rating Bintang</span>
                  </h3>
                  <span className="text-xs font-bold px-2 py-0.5 rounded-lg bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                    Total: {totalSelectedStars} Ulasan
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Atur berapa jumlah ulasan per bintang yang akan ditugaskan ke worker secara acak.
                </p>

                {/* 5 Star Counters */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-4">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <div
                      key={star}
                      className="bg-slate-950/70 p-3 rounded-2xl border border-slate-800/80 text-center flex flex-col justify-between"
                    >
                      <div className="flex items-center justify-center gap-1 text-amber-400 text-xs font-bold mb-2">
                        <span>{star}</span>
                        <Star className="w-3.5 h-3.5 fill-current" />
                      </div>

                      <div className="flex items-center justify-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => updateStarCount(star, -1)}
                          className="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition-colors cursor-pointer"
                        >
                          <Minus className="w-3 h-3" />
                        </button>
                        <span className="font-extrabold text-sm text-white w-7 text-center">
                          {starCounts[`star_${star}`] || 0}
                        </span>
                        <button
                          type="button"
                          onClick={() => updateStarCount(star, 1)}
                          className="w-7 h-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition-colors cursor-pointer"
                        >
                          <Plus className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Language & Tone Style Settings */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Bahasa Ulasan (Language)
                  </label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="Indonesian">Bahasa Indonesia</option>
                    <option value="English">English</option>
                    <option value="Spanish">Español</option>
                    <option value="Chinese">中文 (Chinese)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Tone / Gaya Bahasa Ulasan
                  </label>
                  <select
                    value={selectedStyle}
                    onChange={(e) => setSelectedStyle(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="random">Acak Positif & Netral (Rekomendasi)</option>
                    <option value="baik">Dominan Pujian & Layanan Bagus</option>
                    <option value="buruk">Catatan Evaluasi / Netral Kritis</option>
                  </select>
                </div>
              </div>

              {/* Launch Action */}
              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setShowPersonaModal(true)}
                  className="px-4 py-3 rounded-xl font-semibold text-xs bg-slate-800 hover:bg-slate-750 text-slate-200 border border-slate-700/80 flex items-center justify-center gap-2 shadow-xs transition-colors cursor-pointer shrink-0"
                  title="Simulasikan teks ulasan berbasis persona pengulas"
                >
                  <MessageSquare className="w-4 h-4 text-slate-400" />
                  <span className="hidden sm:inline">Uji Variasi Gaya</span>
                </button>
                <button
                  onClick={handleStartBot}
                  disabled={workerRunning || totalSelectedStars === 0 || actionLoading}
                  className="flex-1 py-3 rounded-xl font-semibold text-xs bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center gap-2 shadow-xs disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
                >
                  <Play className="w-4 h-4 fill-current" />
                  <span>Jalankan {totalSelectedStars} Ulasan Sekarang</span>
                </button>
              </div>
            </div>
          )}

          {/* SubTab 2: Reviews Table */}
          {activeTab === 'reviews' && (
            <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
              <div className="p-3.5 bg-slate-950/60 border-b border-slate-800 flex items-center justify-between gap-3">
                <div className="relative flex-1 max-w-xs">
                  <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                  <input
                    type="text"
                    value={reviewSearch}
                    onChange={(e) => setReviewSearch(e.target.value)}
                    placeholder="Filter ulasan..."
                    className="w-full pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <span className="text-[11px] text-slate-400 font-mono">
                  {filteredReviews.length} dari {reviews.length} total
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                    <tr>
                      <th className="p-3.5 pl-4">Akun Google</th>
                      <th className="p-3.5">Rating</th>
                      <th className="p-3.5">Status</th>
                      <th className="p-3.5">Teks Ulasan</th>
                      <th className="p-3.5 pr-4 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {filteredReviews.map((rev) => (
                      <tr key={rev.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="p-3.5 pl-4 font-mono font-medium text-white">{rev.email}</td>
                        <td className="p-3.5">
                          <span className="inline-flex items-center gap-1 font-bold text-amber-400">
                            {rev.star_rating || 5} <Star className="w-3 h-3 fill-current" />
                          </span>
                        </td>
                        <td className="p-3.5">
                          <StatusBadge status={rev.status} />
                        </td>
                        <td className="p-3.5 max-w-[220px]">
                          <span className="line-clamp-2 text-slate-400 text-[11px]">
                            {rev.review_text || '—'}
                          </span>
                        </td>
                        <td className="p-3.5 pr-4 text-right space-x-1.5">
                          <button
                            onClick={() => handleInspectReview(rev.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-indigo-300 hover:bg-indigo-500/10 transition-colors"
                            title="Inspeksi Ulasan di Browser"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleResetReview(rev.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-amber-300 hover:bg-amber-500/10 transition-colors"
                            title="Reset Ulasan ke Antrean"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDeleteReview(rev.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                            title="Hapus"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))}

                    {filteredReviews.length === 0 && (
                      <tr>
                        <td colSpan="5" className="p-8 text-center text-slate-500">
                          {reviewSearch ? 'Tidak ada ulasan yang cocok.' : 'Belum ada tugas review pada bisnis ini.'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* SubTab 3: Review Configuration */}
          {activeTab === 'config' && (
            <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl p-5 shadow-xl">
              <form onSubmit={handleSaveConfig} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Deskripsi Bisnis & Kata Kunci (Keywords)
                  </label>
                  <textarea
                    rows={4}
                    value={configForm.business_description}
                    onChange={(e) =>
                      setConfigForm({ ...configForm, business_description: e.target.value })
                    }
                    placeholder="Contoh: Tempat makan keluarga dengan masakan khas Sunda, suasana asri, parkir luas, dan pelayanan ramah."
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                  <span className="text-[11px] text-slate-500 block mt-1">
                    Worker AI akan menyusun kalimat ulasan alami berdasarkan konteks deskripsi ini.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Jeda Waktu Antar Ulasan (Detik)
                  </label>
                  <input
                    type="number"
                    min="5"
                    max="1800"
                    value={configForm.delay_seconds}
                    onChange={(e) =>
                      setConfigForm({
                        ...configForm,
                        delay_seconds: parseInt(e.target.value) || 60,
                      })
                    }
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  />
                  <span className="text-[11px] text-slate-500 block mt-1">
                    Jeda pengaman otomatis ditambah waktu acak 0-300 detik per ulasan untuk simulasi manusiawi.
                  </span>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={actionLoading}
                    className="px-5 py-2.5 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 transition-all cursor-pointer disabled:opacity-50"
                  >
                    {actionLoading ? 'Menyimpan...' : 'Simpan Pengaturan'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>

        {/* Right Column (5 cols): Live Stream Viewer & Real-time Logs */}
        <div className="lg:col-span-5 space-y-5">
          {/* Live Chromium Stream Component */}
          <LiveStreamViewer businessId={id} />

          {/* Process Logs Box */}
          <div className="bg-slate-900/90 border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
            <div className="p-3.5 bg-slate-950/70 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-white">Live Process Logs</span>
              </div>
              <span className="text-[10px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                Auto-polling 3s
              </span>
            </div>

            <div
              ref={logContainerRef}
              className="p-3 max-h-72 overflow-y-auto font-mono text-[11px] space-y-1.5 bg-slate-950/90 no-scrollbar"
            >
              {logs.map((log) => {
                const isError = log.level === 'error';
                const isWarn = log.level === 'warning';
                const isSuccess = log.level === 'success';

                return (
                  <div
                    key={log.id}
                    className={`leading-relaxed p-1.5 rounded-lg transition-colors ${
                      isError
                        ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                        : isWarn
                        ? 'bg-amber-500/10 text-amber-300'
                        : isSuccess
                        ? 'bg-emerald-500/10 text-emerald-300'
                        : 'text-slate-300 hover:bg-slate-900/50'
                    }`}
                  >
                    <span className="text-slate-500 text-[10px] mr-2">[{log.created_at}]</span>
                    <span>{log.message}</span>
                  </div>
                );
              })}

              {logs.length === 0 && (
                <div className="p-6 text-center text-slate-500 text-xs">
                  Belum ada log aktivitas untuk proses ulasan ini.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modal Inspection */}
      {inspectModal.show && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 w-full max-w-lg shadow-2xl relative animate-in fade-in zoom-in-95">
            <button
              onClick={() => setInspectModal({ show: false, data: null, loading: false })}
              className="absolute right-5 top-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
            <h3 className="font-extrabold text-base text-white mb-1">Inspeksi Ulasan Google Maps</h3>
            <p className="text-xs text-slate-400 mb-4">
              Mode baca (read-only): memeriksa status ulasan langsung pada Google Maps tanpa mengubah konten publik.
            </p>

            {inspectModal.loading ? (
              <div className="p-8 text-center">
                <div className="w-8 h-8 border-3 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mx-auto mb-3"></div>
                <span className="text-xs text-slate-400 font-mono">
                  Membuka Chromium dan memeriksa ulasan...
                </span>
              </div>
            ) : (
              <div className="space-y-3.5 text-xs">
                <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-slate-500 text-[11px] block mb-1">Status Pemeriksaan:</span>
                  <StatusBadge status={inspectModal.data?.status || 'unknown'} />
                  <p className="text-slate-300 mt-2 font-mono text-[11px]">{inspectModal.data?.message}</p>
                </div>

                {inspectModal.data?.old_text && (
                  <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800">
                    <span className="text-slate-500 text-[11px] block mb-1">Teks Ulasan Sebelumnya:</span>
                    <p className="text-slate-300 italic">{inspectModal.data?.old_text}</p>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-end pt-5 mt-4 border-t border-slate-800">
              <button
                onClick={() => setInspectModal({ show: false, data: null, loading: false })}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 transition-colors"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: AI Persona Review Simulator */}
      <ReviewPersonaModal
        isOpen={showPersonaModal}
        onClose={() => setShowPersonaModal(false)}
        defaultBusinessName={biz.name}
        defaultDescription={configForm.business_description}
      />
    </div>
  );
}
