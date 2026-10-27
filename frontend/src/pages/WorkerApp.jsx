import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Monitor,
  Cookie,
  LogOut,
  Video,
  Pause,
  Play,
  RotateCw,
  Maximize2,
  Sliders,
  Terminal,
  RotateCcw,
  SlidersHorizontal,
  Plus,
  ChevronDown,
  ExternalLink,
  Clock,
  Square,
  Search,
  ArrowDownToLine,
  Trash2,
  Copy,
  X,
  Download,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Info,
  Users,
  Layers,
  ArrowLeft,
  Sparkles,
  Activity,
  ShieldCheck,
  MousePointer,
  Star,
  ShieldAlert,
  Flag,
  Eye,
  EyeOff,
  Building2,
  Wrench
} from 'lucide-react';
import { api } from '../api/client';
import GrokMascotAvatar from '../components/GrokMascotAvatar';
import SlotWalkingMascot from '../components/SlotWalkingMascot';

export default function WorkerApp({ onLogout }) {
  // --- Core State ---
  const [businesses, setBusinesses] = useState([]);
  const [selectedBusinessId, setSelectedBusinessId] = useState(null);
  const [businessDetail, setBusinessDetail] = useState(null);
  const [workerStatus, setWorkerStatus] = useState({ running: false, active_business_id: null });
  const [cookiesList, setCookiesList] = useState([]);

  // --- Multi-Account & Dynamic Sharescreen State ---
  const [accountCount, setAccountCount] = useState(6); // 1 s/d 6 accounts = 1 s/d 6 sharescreens
  const [accountShuffleSeed, setAccountShuffleSeed] = useState(() => Math.floor(Math.random() * 100000));
  const [lockedRunningAccounts, setLockedRunningAccounts] = useState(null);

  // --- Claude AI Mascot Supervisor State ---
  const [isClaudeModalOpen, setIsClaudeModalOpen] = useState(false);
  const [claudeMood, setClaudeMood] = useState('active'); // 'active' | 'syncing'

  // --- Sharescreen Player State ---
  const [currentView, setCurrentView] = useState('split'); // 'split' | 'acc1' | 'acc2' | 'acc3'
  const [streamMode, setStreamMode] = useState('PNG'); // 'PNG' | 'MJPEG' | 'CARDS'
  const [streamSource, setStreamSource] = useState('windows'); // 'windows' | 'chromium' | 'auto'
  const [streamPaused, setStreamPaused] = useState(false);
  const [streamTimestamp, setStreamTimestamp] = useState(Date.now());
  const [streamError, setStreamError] = useState(false);
  const streamContainerRef = useRef(null);
  const [vmStates, setVmStates] = useState({});

  // --- Right Panel Tabs ---
  const [activeRightTab, setActiveRightTab] = useState('config'); // 'config' | 'terminal'
  const [executionMode, setExecutionMode] = useState('parallel'); // 'parallel' | 'single'

  // --- Logcat State ---
  const [logs, setLogs] = useState([]);
  const [logSearch, setLogSearch] = useState('');
  const [logFilterLevel, setLogFilterLevel] = useState('ALL');
  const [autoScroll, setAutoScroll] = useState(true);
  const [logPaused, setLogPaused] = useState(false);
  const terminalEndRef = useRef(null);

  // --- Modals State ---
  const [isCookieModalOpen, setIsCookieModalOpen] = useState(false);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [isAddBusinessModalOpen, setIsAddBusinessModalOpen] = useState(false);

  // --- Form State in Modals ---
  const [newCookieEmail, setNewCookieEmail] = useState('');
  const [newCookieJson, setNewCookieJson] = useState('');
  const cookieEmailInputRef = useRef(null);
  const cookieTextareaRef = useRef(null);
  const [configTone, setConfigTone] = useState('casual');
  const [configPrompt, setConfigPrompt] = useState('');
  const [configRating, setConfigRating] = useState('5');
  const [configDelay, setConfigDelay] = useState(65);
  const [geminiToken, setGeminiToken] = useState('');
  const [showGeminiToken, setShowGeminiToken] = useState(false);
  const [businessCategory, setBusinessCategory] = useState('');
  const [isTestingGemini, setIsTestingGemini] = useState(false);
  const [geminiTestResult, setGeminiTestResult] = useState(null);
  const [settingTab, setSettingTab] = useState('general'); // 'general' | 'stars' | 'dark_mode'
  const [starMode, setStarMode] = useState('all5'); // 'all5' | 'natural' | 'custom'
  const [customStars, setCustomStars] = useState({ 5: 5, 4: 1, 3: 0, 2: 0, 1: 0 });
  const [isDeletingComments, setIsDeletingComments] = useState(false);
  const [isDeletingMapsReviews, setIsDeletingMapsReviews] = useState(false);
  const [isReportingMap, setIsReportingMap] = useState(false);
  const [reportReason, setReportReason] = useState('spam_fake');
  const [reportNote, setReportNote] = useState('');
  const [reportAccountCount, setReportAccountCount] = useState(3);
  const [newBusinessName, setNewBusinessName] = useState('');
  const [newBusinessUrl, setNewBusinessUrl] = useState('');

  // --- Action Loading States ---
  const [isStartingBot, setIsStartingBot] = useState(false);
  const [isStoppingBot, setIsStoppingBot] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [isAddingBusiness, setIsAddingBusiness] = useState(false);
  const [isAddingCookie, setIsAddingCookie] = useState(false);

  // --- Toast Notifications ---
  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  };

  const formatReviewTime = (dateStr) => {
    if (!dateStr) return 'Baru saja';
    try {
      const parts = String(dateStr).split(' ');
      if (parts.length === 2 && parts[1]) {
        return parts[1].substring(0, 8);
      }
      const d = new Date(String(dateStr).replace(' ', 'T'));
      if (isNaN(d.getTime())) return String(dateStr);
      const hours = String(d.getHours()).padStart(2, '0');
      const minutes = String(d.getMinutes()).padStart(2, '0');
      const seconds = String(d.getSeconds()).padStart(2, '0');
      return `${hours}:${minutes}:${seconds}`;
    } catch {
      return String(dateStr);
    }
  };

  // --- Data Fetching ---
  const loadDashboardData = async (refreshLogsOnly = false) => {
    try {
      if (!refreshLogsOnly) {
        const dash = await api.getDashboard();
        if (dash && dash.businesses) {
          setBusinesses(dash.businesses);
          if (!selectedBusinessId && dash.businesses.length > 0) {
            setSelectedBusinessId(dash.businesses[0].id);
          }
        }
        if (dash && Array.isArray(dash.all_cookies)) {
          setCookiesList(dash.all_cookies);
        }
      }

      // Always synchronize cookie list with cookie health
      try {
        const cHealth = await api.getCookieHealth();
        if (cHealth && Array.isArray(cHealth.cookies)) {
          setCookiesList(cHealth.cookies);
        }
      } catch {}

      const wStatus = await api.getWorkerStatus();
      if (wStatus) {
        const isRunning = Boolean(
          wStatus.running ||
          wStatus.worker_running ||
          wStatus.is_running ||
          (wStatus.system_status && (wStatus.system_status.running || wStatus.system_status.is_running || wStatus.system_status.worker_running))
        );
        setWorkerStatus({
          ...wStatus,
          running: isRunning,
        });
        if (wStatus.vm_states) {
          setVmStates(wStatus.vm_states);
        }
        if (!isRunning) {
          setLockedRunningAccounts(null);
        }
      }

      if (selectedBusinessId) {
        const detail = await api.getBusinessDetail(selectedBusinessId);
        if (detail && !detail.error) {
          setBusinessDetail(detail);
          if (detail.cookies && Array.isArray(detail.cookies)) {
            setCookiesList(detail.cookies);
          }
          if (detail.config && !refreshLogsOnly) {
            if (detail.config.review_style) setConfigTone(detail.config.review_style);
            if (detail.config.custom_prompt) setConfigPrompt(detail.config.custom_prompt);
            if (detail.config.delay_min) setConfigDelay(detail.config.delay_min);
            if (detail.config.screen_count) setAccountCount(Math.max(1, Math.min(6, detail.config.screen_count)));
            if (detail.config.gemini_token !== undefined) setGeminiToken(detail.config.gemini_token || '');
            if (detail.config.business_category !== undefined) setBusinessCategory(detail.config.business_category || '');
          }
        }

        // Fetch logs
        if (!logPaused) {
          const logRes = await api.getProcessLogs(selectedBusinessId);
          if (logRes && Array.isArray(logRes.logs)) {
            setLogs(logRes.logs);
          }
        }
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    }
  };

  // Initial load
  useEffect(() => {
    loadDashboardData();
  }, [selectedBusinessId]);

  // Polling loop for worker status & logs
  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboardData(true);
    }, 2500);
    return () => clearInterval(interval);
  }, [selectedBusinessId, logPaused]);

  // Auto-scroll terminal
  useEffect(() => {
    if (autoScroll && activeRightTab === 'terminal' && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll, activeRightTab]);

  // Stream snapshot ticker when not paused
  useEffect(() => {
    if (!streamPaused) {
      const intervalMs = streamMode === 'PNG' ? 1400 : 2500;
      const timer = setInterval(() => {
        setStreamTimestamp(Date.now());
      }, intervalMs);
      return () => clearInterval(timer);
    }
  }, [streamMode, streamPaused]);

  // --- Handlers ---
  const handleVmControl = async (slotNumber, action, params = {}) => {
    const vmid = 100 + Number(slotNumber);
    try {
      const data = await api.controlVm(vmid, action, params);
      if (data && data.status === 'ok') {
        showToast(`VM-${vmid}: Input '${action}' terkirim`, 'success');
      } else {
        showToast(data?.message || 'Gagal mengirim kontrol', 'warning');
      }
    } catch (e) {
      showToast('Koneksi kontrol VM gagal', 'error');
    }
  };

  const handleWakeVm = async (slotNumber) => {
    const vmid = 100 + Number(slotNumber);
    try {
      showToast(`Membangunkan Windows VM-${vmid}... ⚡`, 'info');
      setVmStates((prev) => ({
        ...prev,
        [vmid]: { ...prev[vmid], is_sleeping: false },
      }));
      const data = await api.controlVm(vmid, 'wake');
      if (data && data.status === 'ok') {
        showToast(`Layar Windows VM-${vmid} telah menyala! 💡`, 'success');
      }
      setTimeout(() => setStreamTimestamp(Date.now()), 300);
    } catch (e) {
      showToast(`Gagal membangunkan VM-${vmid}`, 'error');
    }
  };

  const handleToggleVmSleep = async (slotNumber) => {
    const vmid = 100 + Number(slotNumber);
    try {
      const data = await api.controlVm(vmid, 'toggle_sleep');
      if (data && data.status === 'ok') {
        setVmStates((prev) => ({
          ...prev,
          [vmid]: { ...prev[vmid], is_sleeping: data.is_sleeping },
        }));
        showToast(
          data.is_sleeping
            ? `Windows VM-${vmid} diset mode sleep 💤`
            : `Windows VM-${vmid} dinyalakan! ⚡`,
          'info'
        );
        setTimeout(() => setStreamTimestamp(Date.now()), 300);
      }
    } catch (e) {
      showToast(`Gagal mengubah mode sleep VM-${vmid}`, 'error');
    }
  };

  const handleScreenViewportClick = (e, slotNumber) => {
    const vmid = 100 + Number(slotNumber);
    if (vmStates[vmid]?.is_sleeping) {
      handleWakeVm(slotNumber);
      return;
    }
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
    handleVmControl(slotNumber, 'click', { x, y, button: 'left' });
  };

  const handleTargetChange = (businessId) => {
    setSelectedBusinessId(Number(businessId));
    setStreamTimestamp(Date.now());
    const bName = businesses.find((b) => b.id === Number(businessId))?.name || businessId;
    showToast(`Beralih ke target: ${bName}`, 'info');
  };

  const handleStartBot = async () => {
    if (!selectedBusinessId) {
      showToast('Pilih target bisnis terlebih dahulu!', 'warning');
      return;
    }
    // Lock the exact accounts running for this session so they NEVER switch
    const runningBatch = availableAccounts.slice(0, accountCount);
    setLockedRunningAccounts(runningBatch);
    setIsStartingBot(true);
    try {
      const selectedIds = runningBatch.map((a) => a.id).filter(Boolean);
      let s5 = accountCount;
      let s4 = 0;
      let s3 = 0;
      let s2 = 0;
      let s1 = 0;
      if (starMode === 'natural') {
        s5 = Math.max(1, accountCount - 1);
        s4 = 1;
      } else if (starMode === 'custom') {
        s5 = parseInt(customStars[5], 10) || 0;
        s4 = parseInt(customStars[4], 10) || 0;
        s3 = parseInt(customStars[3], 10) || 0;
        s2 = parseInt(customStars[2], 10) || 0;
        s1 = parseInt(customStars[1], 10) || 0;
      }

      const res = await api.startBot(selectedBusinessId, {
        mode: accountCount > 1 ? 'parallel' : 'single',
        count: accountCount,
        star_5_count: s5,
        star_4_count: s4,
        star_3_count: s3,
        star_2_count: s2,
        star_1_count: s1,
        selected_email_ids: selectedIds,
      });
      if (res && (res.status === 'ok' || res.status === 'processing')) {
        showToast(
          `Worker berhasil dijalankan! Membuka ${accountCount} jendela browser Chromium di Display :99.`,
          'success'
        );
        setStreamError(false);
        setStreamTimestamp(Date.now());
        await loadDashboardData();
      } else {
        setLockedRunningAccounts(null);
        showToast(res.message || 'Gagal memulai worker.', 'error');
      }
    } catch (err) {
      setLockedRunningAccounts(null);
      showToast(err.message || 'Error saat menjalankan worker.', 'error');
    } finally {
      setIsStartingBot(false);
    }
  };

  const handleStopBot = async () => {
    setIsStoppingBot(true);
    setLockedRunningAccounts(null);
    try {
      const res = await api.stopBot(selectedBusinessId);
      try {
        await api.emergencyStopWorker();
      } catch {}

      showToast(res?.message || 'Worker dan seluruh proses engine berhasil dipaksa berhenti.', 'info');
      setWorkerStatus({ running: false, is_running: false, worker_running: false });
      await loadDashboardData();
    } catch (err) {
      showToast(err.message || 'Error saat menghentikan bot.', 'error');
    } finally {
      setIsStoppingBot(false);
    }
  };

  const handleClaudeSyncAllScreens = () => {
    setStreamTimestamp(Date.now());
    setStreamError(false);
    setClaudeMood('syncing');
    showToast(`Claude AI: Mensinkronkan seluruh ${accountCount} slot layar...`, 'success');
    setTimeout(() => {
      setClaudeMood('active');
    }, 1200);
  };

  const handleResetReviews = async () => {
    if (!selectedBusinessId) return;
    if (
      !window.confirm(
        'Apakah Anda yakin ingin mereset seluruh antrean ulasan untuk bisnis ini? Ulasan akan kembali ke status pending.'
      )
    ) {
      return;
    }
    try {
      const res = await api.resetAllBusinessReviews(selectedBusinessId);
      if (res && res.status === 'ok') {
        showToast('Seluruh status ulasan target berhasil direset ke status pending.', 'success');
        await loadDashboardData();
      } else {
        showToast(res.message || 'Gagal mereset ulasan.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Error saat mereset ulasan.', 'error');
    }
  };

  const handleSaveConfig = async (e) => {
    e.preventDefault();
    if (!selectedBusinessId) return;
    setIsSavingConfig(true);
    try {
      let s5 = accountCount;
      let s4 = 0;
      let s3 = 0;
      let s2 = 0;
      let s1 = 0;
      if (starMode === 'natural') {
        s5 = Math.max(1, accountCount - 1);
        s4 = 1;
      } else if (starMode === 'custom') {
        s5 = parseInt(customStars[5], 10) || 0;
        s4 = parseInt(customStars[4], 10) || 0;
        s3 = parseInt(customStars[3], 10) || 0;
        s2 = parseInt(customStars[2], 10) || 0;
        s1 = parseInt(customStars[1], 10) || 0;
      }

      const payload = {
        review_style: configTone,
        custom_prompt: configPrompt,
        business_description: configPrompt,
        delay_seconds: parseInt(configDelay, 10) || 60,
        delay_min: parseInt(configDelay, 10) || 60,
        delay_max: (parseInt(configDelay, 10) || 60) + 30,
        screen_count: accountCount,
        star_5_count: s5,
        star_4_count: s4,
        star_3_count: s3,
        star_2_count: s2,
        star_1_count: s1,
        gemini_token: geminiToken,
        business_category: businessCategory,
      };
      const res = await api.saveBusinessConfig(selectedBusinessId, payload);
      if (res && res.status === 'ok') {
        showToast('Konfigurasi target, bintang & AI prompt berhasil disimpan!', 'success');
        setIsConfigModalOpen(false);
        await loadDashboardData();
      } else {
        showToast(res.message || 'Gagal menyimpan konfigurasi.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Error menyimpan konfigurasi.', 'error');
    } finally {
      setIsSavingConfig(false);
    }
  };

  const handleTestGemini = async () => {
    if (!selectedBusinessId) return;
    if (!geminiToken.trim()) {
      showToast('Masukkan Token AI Gemini terlebih dahulu untuk melakukan tes.', 'error');
      return;
    }
    setIsTestingGemini(true);
    setGeminiTestResult(null);
    try {
      const res = await api.testGeminiReview(selectedBusinessId, {
        gemini_token: geminiToken,
        business_category: businessCategory,
        custom_prompt: configPrompt,
        review_style: configTone,
        star_rating: 5,
      });
      if (res && res.status === 'ok') {
        setGeminiTestResult(res);
        showToast(`AI Gemini berhasil meracik ulasan untuk ${res.business_name}!`, 'success');
      } else {
        showToast(res.message || 'Gagal menghubungi Gemini AI.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Error saat tes AI Gemini.', 'error');
    } finally {
      setIsTestingGemini(false);
    }
  };

  const handleDeleteAllComments = async () => {
    if (!selectedBusinessId) return;
    const bName = businesses.find((b) => b.id === selectedBusinessId)?.name || 'target';
    if (!confirm(`[DARK MODE] Yakin ingin menghapus semua ulasan & draft komentar untuk "${bName}"?\n\nRiwayat ulasan dan antrean untuk bisnis ini akan dibersihkan dari database.`)) {
      return;
    }
    setIsDeletingComments(true);
    try {
      const res = await api.deleteBusinessComments(selectedBusinessId);
      if (res && res.status === 'ok') {
        showToast(res.message || 'Semua ulasan dan komentar target berhasil dihapus!', 'success');
        await loadDashboardData();
      } else {
        showToast(res.message || 'Gagal menghapus ulasan target.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Error saat menghapus komentar target.', 'error');
    } finally {
      setIsDeletingComments(false);
    }
  };

  const handleDeleteOwnReviewsOnMaps = async (emailId = null) => {
    if (!selectedBusinessId) return;
    const bName = businesses.find((b) => b.id === selectedBusinessId)?.name || 'target';
    const confirmMsg = emailId
      ? `[GOOGLE MAPS LIVE] Hapus ulasan dan komentar milik akun ini langsung dari Google Maps untuk target "${bName}"?`
      : `[GOOGLE MAPS LIVE] Hapus seluruh ulasan & komentar akun sendiri yang sudah terbit di Google Maps untuk target "${bName}" via browser Chromium?`;
    if (!confirm(confirmMsg)) {
      return;
    }
    setIsDeletingMapsReviews(true);
    try {
      const res = await api.deleteOwnReviewsOnMaps(selectedBusinessId, emailId ? { email_id: emailId } : {});
      if (res && res.status === 'ok') {
        showToast(res.message || 'Proses penghapusan ulasan di Google Maps telah dijalankan.', 'success');
        await loadDashboardData();
      } else {
        showToast(res.message || 'Gagal memulai penghapusan ulasan di Google Maps.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Error saat menghubungi server.', 'error');
    } finally {
      setIsDeletingMapsReviews(false);
    }
  };

  const handleSendReportMap = async () => {
    if (!selectedBusinessId) return;
    const bName = businesses.find((b) => b.id === selectedBusinessId)?.name || 'target';
    if (!confirm(`[DARK MODE] Kirim sinyal pelaporan Google Maps untuk "${bName}" dengan ${reportAccountCount} akun?`)) {
      return;
    }
    setIsReportingMap(true);
    try {
      const payload = {
        reason: reportReason,
        custom_note: reportNote.trim(),
        account_count: reportAccountCount,
      };
      const res = await api.reportBusinessMap(selectedBusinessId, payload);
      if (res && res.status === 'ok') {
        showToast(res.message || 'Sinyal Report Map berhasil dikirim!', 'success');
        setReportNote('');
        await loadDashboardData();
      } else {
        showToast(res.message || 'Gagal mengirim sinyal report map.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Error saat mengirim report map.', 'error');
    } finally {
      setIsReportingMap(false);
    }
  };

  const handleAddNewBusiness = async (e) => {
    e.preventDefault();
    if (!newBusinessName.trim() || !newBusinessUrl.trim()) {
      showToast('Nama dan URL Google Maps wajib diisi!', 'warning');
      return;
    }
    setIsAddingBusiness(true);
    try {
      const res = await api.addBusiness(newBusinessName.trim(), newBusinessUrl.trim());
      if (res && res.status === 'ok') {
        showToast(`Target bisnis "${newBusinessName}" berhasil ditambahkan!`, 'success');
        setIsAddBusinessModalOpen(false);
        setNewBusinessName('');
        setNewBusinessUrl('');
        const dash = await api.getDashboard();
        if (dash && dash.businesses) {
          setBusinesses(dash.businesses);
          if (res.business_id) setSelectedBusinessId(res.business_id);
        }
      } else {
        showToast(res.message || 'Gagal menambahkan bisnis.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Error menambahkan bisnis.', 'error');
    } finally {
      setIsAddingBusiness(false);
    }
  };

  const handleOpenCookieModal = async () => {
    setIsCookieModalOpen(true);
    try {
      const cHealth = await api.getCookieHealth();
      if (cHealth && Array.isArray(cHealth.cookies)) {
        setCookiesList(cHealth.cookies);
      }
    } catch {}
  };

  const handleAddCookie = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const emailVal = (newCookieEmail || cookieEmailInputRef.current?.value || '').trim();
    const cookieVal = (newCookieJson || cookieTextareaRef.current?.value || '').trim();

    if (!cookieVal) {
      showToast('Payload cookie wajib diisi!', 'warning');
      return;
    }
    setIsAddingCookie(true);
    try {
      const res = await api.addCookie(emailVal, cookieVal);
      if (res && res.status === 'ok') {
        const savedEmail = res.email || emailVal || 'Akun Google';
        showToast(`Cookie ${savedEmail} berhasil disimpan! (${res.cookie_count || 0} cookies)`, 'success');
        setNewCookieEmail('');
        setNewCookieJson('');
        if (cookieEmailInputRef.current) cookieEmailInputRef.current.value = '';
        if (cookieTextareaRef.current) cookieTextareaRef.current.value = '';

        try {
          const cHealth = await api.getCookieHealth();
          if (cHealth && Array.isArray(cHealth.cookies)) {
            setCookiesList(cHealth.cookies);
          }
        } catch {}
        await loadDashboardData();
      } else {
        showToast(res.message || 'Gagal menyimpan cookie.', 'error');
      }
    } catch (err) {
      showToast(err.message || 'Gagal memproses cookie.', 'error');
    } finally {
      setIsAddingCookie(false);
    }
  };

  const handleQuickUnflagAll = async () => {
    try {
      const res = await api.unflagAllEmails();
      showToast(res.message || 'Semua akun berhasil dipulihkan (unflagged)!', 'success');
      await loadDashboardData();
    } catch (err) {
      showToast(err.message || 'Gagal memulihkan status akun.', 'error');
    }
  };

  const handleTestCookie = async (cookieId, email) => {
    try {
      showToast(`Menguji validitas sesi ${email}...`, 'info');
      const res = await api.testCookie(cookieId);
      if (res && res.valid) {
        showToast(`Sesi ${email} AKTIF dan valid!`, 'success');
      } else {
        showToast(`Sesi ${email} sudah kadaluarsa / perlu login ulang.`, 'warning');
      }
      try {
        const cHealth = await api.getCookieHealth();
        if (cHealth && Array.isArray(cHealth.cookies)) {
          setCookiesList(cHealth.cookies);
        }
      } catch {}
      await loadDashboardData();
    } catch (err) {
      showToast(err.message || 'Error saat menguji cookie.', 'error');
    }
  };

  const handleDeleteCookie = async (cookieId, email) => {
    if (!window.confirm(`Hapus cookie akun ${email}?`)) return;
    try {
      const res = await api.deleteCookie(cookieId);
      if (res && res.status === 'ok') {
        showToast(`Cookie ${email} berhasil dihapus.`, 'info');
        setCookiesList((prev) => prev.filter((c) => c.id !== cookieId));
        await loadDashboardData();
      }
    } catch (err) {
      showToast(err.message || 'Gagal menghapus cookie.', 'error');
    }
  };

  const handleClearTerminal = async () => {
    if (!selectedBusinessId) return;
    try {
      await api.clearProcessLogs(selectedBusinessId);
      setLogs([]);
      showToast('Logcat berhasil dibersihkan.', 'info');
    } catch (err) {
      showToast('Gagal membersihkan logcat.', 'error');
    }
  };

  const handleCopyLogs = () => {
    const rawText = filteredLogs
      .map((l) => `${l.time || ''} [${l.level || 'INFO'}] ${l.message || ''}`)
      .join('\n');
    navigator.clipboard.writeText(rawText);
    showToast('Seluruh teks log berhasil disalin ke clipboard!', 'success');
  };

  const handleDownloadLogs = () => {
    const rawText = filteredLogs
      .map((l) => `${l.time || ''} [${l.level || 'INFO'}] ${l.message || ''}`)
      .join('\n');
    const blob = new Blob([rawText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `logcat-autobotix-${selectedBusinessId || 'all'}-${Date.now()}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    showToast('File logcat berhasil diunduh.', 'success');
  };

  const toggleFullscreen = () => {
    if (!streamContainerRef.current) return;
    if (!document.fullscreenElement) {
      streamContainerRef.current.requestFullscreen().catch((err) => {
        showToast(`Gagal mode fullscreen: ${err.message}`, 'warning');
      });
    } else {
      document.exitFullscreen();
    }
  };

  // --- Filtered Logs ---
  const filteredLogs = useMemo(() => {
    let result = Array.isArray(logs) ? logs : [];
    if (logFilterLevel !== 'ALL') {
      result = result.filter((item) => (item.level || '').toUpperCase() === logFilterLevel);
    }
    if (logSearch.trim()) {
      const q = logSearch.toLowerCase();
      result = result.filter(
        (item) =>
          (item.message || '').toLowerCase().includes(q) ||
          (item.source || '').toLowerCase().includes(q) ||
          (item.time || '').toLowerCase().includes(q)
      );
    }
    return result;
  }, [logs, logFilterLevel, logSearch]);

  // --- Available Accounts & Dynamic Slots ---
  const availableAccounts = useMemo(() => {
    let rawAccounts = [];
    if (businessDetail && Array.isArray(businessDetail.all_emails) && businessDetail.all_emails.length > 0) {
      rawAccounts = [...businessDetail.all_emails];
    } else if (cookiesList && cookiesList.length > 0) {
      rawAccounts = cookiesList.map((c) => ({
        id: c.id,
        email: c.email,
        cookie_status: c.status,
        session_hash: c.session_hash,
        is_duplicate: c.is_duplicate,
      }));
    }

    if (rawAccounts.length === 0) {
      return [{ id: 24, email: 'google.session.0273@gmail.com' }];
    }

    // 1. DEDUPLIKASI: Pastikan tiap entri akun unik berdasarkan email
    const seenEmails = new Set();
    const distinctAccounts = [];
    for (const acc of rawAccounts) {
      if (!acc.email || seenEmails.has(acc.email)) continue;
      seenEmails.add(acc.email);
      distinctAccounts.push(acc);
    }

    // 2. Pisahkan akun aktif dan akun cadangan
    const activeCookieAccounts = [];
    const otherAccounts = [];
    for (const acc of distinctAccounts) {
      const hasActive =
        acc.cookie_status === 'active' ||
        (cookiesList || []).some((c) => c.email === acc.email && c.status === 'active');
      if (hasActive) {
        activeCookieAccounts.push(acc);
      } else {
        otherAccounts.push(acc);
      }
    }

    // 3. ACAK RANDOM STABIL (Deterministic Pseudo-Random Shuffle via Mulberry32 PRNG)
    // Menggunakan accountShuffleSeed sehingga akun TIDAK AKAN PERNAH berubah saat polling / re-render
    let s = Number(accountShuffleSeed) || 12345;
    const nextRandom = () => {
      let t = (s += 0x6d2b79f5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };

    const shuffleArray = (arr) => {
      const copy = [...arr];
      for (let i = copy.length - 1; i > 0; i--) {
        const j = Math.floor(nextRandom() * (i + 1));
        [copy[i], copy[j]] = [copy[j], copy[i]];
      }
      return copy;
    };

    const shuffledActive = shuffleArray(activeCookieAccounts);
    const shuffledOthers = shuffleArray(otherAccounts);

    return [...shuffledActive, ...shuffledOthers];
  }, [businessDetail?.all_emails, cookiesList, accountShuffleSeed]);

  // Helper to compute 100% REAL progress & status from backend database reviews and live logs
  const calculateRealSlotProgress = (review, latestLog, isRunning) => {
    // 1. If database already marked as reviewed / posted
    if (review?.status === 'reviewed' || review?.status === 'posted') {
      return {
        statusText: 'Ulasan Berhasil Terbit',
        progress: 100,
        isCompleted: true,
        isFailed: false,
        isProcessing: isRunning,
      };
    }

    // 2. If review failed in database
    if (review?.status === 'failed') {
      const rawMsg = latestLog?.message?.replace(/^\[.*?\]\s*/, '') || 'Gagal mengirim ulasan';
      const cleanMsg = rawMsg.length > 40 ? `${rawMsg.slice(0, 37)}...` : rawMsg;
      return {
        statusText: cleanMsg,
        progress: 0,
        isCompleted: false,
        isFailed: true,
        isProcessing: isRunning,
      };
    }

    // 3. When Task is actively running (Jalankan Task)
    if (isRunning) {
      if (latestLog && latestLog.message) {
        const msg = latestLog.message.replace(/^\[.*?\]\s*/, '');
        const low = msg.toLowerCase();

        if (low.includes('berhasil dikirim') || low.includes('berhasil terbit') || low.includes('sukses')) {
          return { statusText: msg, progress: 100, isCompleted: true, isFailed: false, isProcessing: true };
        }
        if (low.includes('mengirim review') || low.includes('post') || low.includes('done')) {
          return { statusText: 'Mengirim review ke Google Maps...', progress: 90, isCompleted: false, isFailed: false, isProcessing: true };
        }
        if (low.includes('membuat teks') || low.includes('mengetik') || low.includes('memilih rating') || low.includes('rating')) {
          return { statusText: 'Mengetik ulasan & rating bintang 5...', progress: 75, isCompleted: false, isFailed: false, isProcessing: true };
        }
        if (low.includes('form review') || low.includes('write a review') || low.includes('tulis ulasan')) {
          return { statusText: 'Membuka form review Google Maps...', progress: 60, isCompleted: false, isFailed: false, isProcessing: true };
        }
        if (low.includes('maps') || low.includes('navigasi')) {
          return { statusText: 'Navigasi ke halaman profil Maps...', progress: 40, isCompleted: false, isFailed: false, isProcessing: true };
        }
        if (low.includes('browser') || low.includes('cookie') || low.includes('sesi') || low.includes('memulai')) {
          return { statusText: 'Verifikasi sesi cookie & Chromium...', progress: 20, isCompleted: false, isFailed: false, isProcessing: true };
        }
        const shortMsg = msg.length > 40 ? `${msg.slice(0, 37)}...` : msg;
        return { statusText: shortMsg, progress: 30, isCompleted: false, isFailed: false, isProcessing: true };
      }

      if (review?.status === 'reviewing') {
        return { statusText: 'Memulai proses review...', progress: 15, isCompleted: false, isFailed: false, isProcessing: true };
      }

      return { statusText: 'Menunggu giliran antrean...', progress: 0, isCompleted: false, isFailed: false, isProcessing: true };
    }

    // 4. When Task is NOT running (Idle / Standby)
    return {
      statusText: review?.status ? (review.status === 'pending' ? 'Siap di antrean' : review.status) : 'Standby',
      progress: 0,
      isCompleted: false,
      isFailed: false,
      isProcessing: false,
    };
  };

  // Dynamic slots based on accountCount (1 s/d 6 Layar)
  const activeSlots = useMemo(() => {
    const slotThemes = [
      { border: 'border-blue-500/80', ring: 'ring-blue-500/30', text: 'text-blue-400', dot: 'bg-emerald-400', badge: 'bg-blue-900/60 text-blue-300' },
      { border: 'border-cyan-500/80', ring: 'ring-cyan-500/30', text: 'text-cyan-400', dot: 'bg-cyan-400', badge: 'bg-cyan-900/60 text-cyan-300' },
      { border: 'border-amber-500/80', ring: 'ring-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-400', badge: 'bg-amber-900/60 text-amber-300' },
      { border: 'border-purple-500/80', ring: 'ring-purple-500/30', text: 'text-purple-400', dot: 'bg-purple-400', badge: 'bg-purple-900/60 text-purple-300' },
      { border: 'border-rose-500/80', ring: 'ring-rose-500/30', text: 'text-rose-400', dot: 'bg-rose-400', badge: 'bg-rose-900/60 text-rose-300' },
      { border: 'border-emerald-500/80', ring: 'ring-emerald-500/30', text: 'text-emerald-400', dot: 'bg-emerald-400', badge: 'bg-emerald-900/60 text-emerald-300' },
    ];
    const displays = [':99', ':100', ':101', ':102', ':103', ':104'];

    return Array.from({ length: accountCount }, (_, i) => {
      // 1. Kunci akun saat bot sedang berjalan agar akun TIDAK PERNAH berubah saat run
      let acc = null;
      if ((workerStatus.running || isStartingBot) && lockedRunningAccounts && lockedRunningAccounts[i]) {
        acc = lockedRunningAccounts[i];
      } else {
        acc = availableAccounts[i] || {
          id: i + 1,
          email: `akun.google.0${i + 1}@gmail.com`,
        };
      }
      const rev = (businessDetail?.reviews || []).find((r) => r.email === acc?.email || r.email_id === acc?.id) || {};
      const theme = slotThemes[i] || slotThemes[0];
      const slotDisplay = displays[i] || `:99`;

      // Filter real logs for this slot
      const slotLogs = logs.filter((l) => {
        if (rev && rev.id && l.review_id === rev.id) return true;
        if (acc && acc.email && l.message && l.message.includes(acc.email)) return true;
        if (l.message && (l.message.includes(`Slot 0${i + 1}`) || l.message.includes(`Display ${slotDisplay}`))) return true;
        return false;
      });
      const latestLog = slotLogs.length > 0 ? slotLogs[slotLogs.length - 1] : null;

      const realInfo = calculateRealSlotProgress(rev, latestLog, workerStatus.running);

      return {
        slotIndex: i,
        slotNumber: i + 1,
        display: slotDisplay,
        account: acc,
        review: rev,
        theme,
        status: realInfo.statusText,
        realStatus: realInfo.statusText,
        realProgress: realInfo.progress,
        isProcessing: realInfo.isProcessing,
        isCompleted: realInfo.isCompleted,
        isFailed: realInfo.isFailed,
        rating: rev.star_rating || 5,
        reviewText:
          rev.review_text ||
          (i === 0
            ? '“Pelayanan memuaskan, pengiriman cepat & aman. Sangat direkomendasikan!”'
            : i === 1
            ? '“Tempat rekomendasi untuk kebutuhan kantor, respon admin sangat sigap.”'
            : `Menunggu giliran tugas Slot 0${i + 1}...`),
      };
    });
  }, [accountCount, availableAccounts, lockedRunningAccounts, businessDetail?.reviews, logs, workerStatus.running, isStartingBot]);

  // Dynamic Tabs for Sharescreen Multi-View
  const viewTabs = useMemo(() => {
    if (accountCount === 1) {
      return [{ id: 'split', label: '1 Layar (Utama)' }];
    }
    const tabs = [{ id: 'split', label: `Split View (${accountCount} Layar)` }];
    for (let i = 0; i < accountCount; i++) {
      tabs.push({ id: `acc${i + 1}`, label: `Akun ${i + 1}` });
    }
    return tabs;
  }, [accountCount]);

  // --- Metrics Calculation ---
  const activeBusiness = businesses.find((b) => b.id === selectedBusinessId) || businesses[0] || {};
  const reviews = businessDetail?.reviews || [];
  const completedReviews = reviews.filter((r) => r.status === 'posted');
  const processingReviews = reviews.filter((r) => r.status === 'reviewing' || r.status === 'processing');
  const failedReviews = reviews.filter((r) => r.status === 'failed');
  const pendingReviews = reviews.filter((r) => !r.status || r.status === 'pending');
  const queueProgressPercent = reviews.length > 0 ? Math.round((completedReviews.length / reviews.length) * 100) : 0;
  const taskCount = accountCount;
  const readyCount = availableAccounts.length;

  return (
    <div className="min-h-screen bg-[#F5F7FB] text-[#172033] flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      {/* ========================================================================= */}
      {/* 1. TOPBAR / NAVBAR (ADAPTIVE HEADER)                                      */}
      {/* ========================================================================= */}
      <header className="h-14 bg-white border-b border-[#DCE3ED] px-2.5 sm:px-4 lg:px-6 flex items-center justify-between sticky top-0 z-40 shadow-xs shrink-0 w-full overflow-hidden">
        {/* Left: Branding & Status Badges */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 min-w-0 shrink">
          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#2563EB] to-[#0891B2] flex items-center justify-center text-white font-bold text-base shadow-sm shrink-0">
              A
            </div>
            <div className="flex items-baseline gap-1 shrink-0">
              <span className="font-bold text-base sm:text-lg tracking-tight text-[#172033]">
                Auto<span className="text-[#2563EB]">Botix</span>
              </span>
              <span className="text-[9px] sm:text-[10px] font-semibold text-[#64748B] bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 hidden sm:inline">
                v2.4-pro
              </span>
            </div>
          </div>

          <a
            href="/dashboard"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors shrink-0"
            title="Kembali ke Master Dashboard"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Master Dashboard</span>
          </a>

          <div className="h-4 w-px bg-[#DCE3ED] mx-1 hidden lg:block"></div>

          {/* Worker Status Badge (Desktop Large/Laptop) */}
          <div
            className={`hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border shrink-0 ${
              workerStatus.running
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-slate-100 border-slate-200 text-slate-600'
            }`}
          >
            <span className="relative flex h-2 w-2">
              <span
                className={`radar-pulse absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  workerStatus.running ? 'bg-emerald-400' : 'bg-slate-400'
                }`}
              ></span>
              <span
                className={`relative inline-flex rounded-full h-2 w-2 ${
                  workerStatus.running ? 'bg-[#059669]' : 'bg-slate-500'
                }`}
              ></span>
            </span>
            <span>{workerStatus.running ? 'Worker Aktif (Running)' : 'Worker Siaga (Idle)'}</span>
          </div>

          {/* Compact Status Indicator for Tablet / Mobile (<1024px) */}
          <div
            className={`flex lg:hidden items-center gap-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] font-semibold border shrink-0 ${
              workerStatus.running
                ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                : 'bg-slate-100 border-slate-200 text-slate-600'
            }`}
            title={workerStatus.running ? 'Worker Aktif (Running)' : 'Worker Siaga (Idle)'}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${workerStatus.running ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`}></span>
            <span className="hidden sm:inline">{workerStatus.running ? 'Running' : 'Idle'}</span>
          </div>

          {/* Virtual Display Badge (XL Desktop only) */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-[#64748B] text-xs font-mono shrink-0">
            <Monitor className="w-3.5 h-3.5 text-[#0891B2]" />
            <span>Display :99 (Xvfb)</span>
          </div>
        </div>

        {/* Right: Quick Actions, Account, Cookie Manager */}
        <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
          {/* Quick Unflag All Button */}
          <button
            onClick={handleQuickUnflagAll}
            className="min-h-[36px] sm:min-h-[38px] flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1.5 rounded-lg border border-amber-300 bg-amber-50 hover:bg-amber-100 active:bg-amber-200 transition text-xs font-semibold text-amber-800 shadow-xs cursor-pointer shrink-0"
            title="Reset status sesi kedaluwarsa untuk semua akun Google"
          >
            <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
            <span className="hidden md:inline">Pulihkan Akun</span>
          </button>

          {/* Cookie Manager Trigger Button */}
          <button
            onClick={handleOpenCookieModal}
            className="min-h-[36px] sm:min-h-[38px] flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1.5 rounded-lg border border-[#DCE3ED] bg-white hover:bg-slate-50 active:bg-slate-100 transition text-xs font-semibold text-[#172033] shadow-xs cursor-pointer shrink-0"
            title="Kelola Cookie Akun"
          >
            <Cookie className="w-4 h-4 text-amber-500 shrink-0" />
            <span className="hidden md:inline">Kelola Cookie</span>
            <span className="bg-blue-50 text-[#2563EB] text-[10px] font-bold px-1.5 py-0.5 rounded-full border border-blue-200">
              {cookiesList.length} <span className="hidden sm:inline">Akun</span>
            </span>
          </button>

          {/* Connection Tunnel Ping (XL Desktop Only) */}
          <div className="hidden xl:flex items-center gap-1 text-[11px] font-medium text-[#64748B] bg-slate-50 px-2 py-1 rounded border border-[#DCE3ED] shrink-0">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>Tunnel: 18ms</span>
          </div>

          {/* User Account Info */}
          <div className="flex items-center gap-1.5 pl-1 border-l border-[#DCE3ED] shrink-0">
            <div className="w-7 h-7 rounded-full bg-blue-100 border border-blue-200 text-[#2563EB] flex items-center justify-center font-bold text-xs shrink-0">
              OP
            </div>
            <span className="text-xs font-medium text-[#172033] hidden lg:inline">Operator</span>
          </div>

          {/* Logout Button */}
          <button
            onClick={async () => {
              await api.logout();
              if (onLogout) onLogout();
            }}
            className="min-h-[36px] min-w-[36px] flex items-center justify-center rounded-lg text-[#64748B] hover:text-[#DC2626] hover:bg-red-50 transition border border-transparent hover:border-red-200 cursor-pointer shrink-0"
            title="Logout Sesi"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* ========================================================================= */}
      {/* 2. MAIN RESPONSIVE DASHBOARD LAYOUT                                       */}
      {/* ========================================================================= */}
      <main className="autobotix-dashboard items-start">
        {/* ==================== PANEL KIRI: LIVE SHARESCREEN MONITOR ==================== */}
        <section className="flex flex-col bg-white rounded-xl border border-[#DCE3ED] shadow-xs overflow-hidden min-w-0 h-auto">
          {/* Header Stream Player */}
          <div className="px-2.5 sm:px-3.5 py-2 sm:py-2.5 bg-slate-50/90 border-b border-[#DCE3ED] flex flex-wrap items-center justify-between gap-2 shrink-0">
            {/* Title */}
            <div className="flex items-center gap-1.5 sm:gap-2">
              <h2 className="text-xs font-bold uppercase tracking-wider text-[#172033] flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Live Sharescreen Monitor</span>
              </h2>
            </div>

            {/* Dynamic Multi-View Tabs based on accountCount */}
            <div className="flex items-center gap-1 bg-white p-0.5 rounded-lg border border-[#DCE3ED] max-w-full overflow-x-auto no-scrollbar">
              {viewTabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setCurrentView(tab.id)}
                  className={`px-2 sm:px-2.5 py-1 text-[10px] sm:text-[11px] rounded-md transition cursor-pointer whitespace-nowrap min-h-[30px] font-semibold ${
                    currentView === tab.id
                      ? 'bg-[#2563EB] text-white shadow-2xs'
                      : 'text-[#64748B] hover:text-[#172033] hover:bg-slate-50 font-medium'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Stream Source Toggle (Windows VM vs Chromium vs Auto) */}
            <div className="flex items-center gap-1 bg-white p-0.5 rounded-lg border border-[#DCE3ED]">
              <button
                type="button"
                onClick={() => {
                  setStreamSource('windows');
                  setStreamTimestamp(Date.now());
                  showToast('Menampilkan Layar Windows (Proxmox KVM)', 'info');
                }}
                className={`px-2 py-1 text-[10px] sm:text-[11px] rounded-md transition cursor-pointer whitespace-nowrap min-h-[30px] font-bold flex items-center gap-1 ${
                  streamSource === 'windows'
                    ? 'bg-blue-600 text-white shadow-2xs'
                    : 'text-[#64748B] hover:text-[#172033] hover:bg-slate-50'
                }`}
                title="Tampilkan Layar Desktop Windows VM KVM"
              >
                <span>🪟 Windows (VM)</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setStreamSource('chromium');
                  setStreamTimestamp(Date.now());
                  showToast('Menampilkan Layar Browser Chromium', 'info');
                }}
                className={`px-2 py-1 text-[10px] sm:text-[11px] rounded-md transition cursor-pointer whitespace-nowrap min-h-[30px] font-bold flex items-center gap-1 ${
                  streamSource === 'chromium'
                    ? 'bg-blue-600 text-white shadow-2xs'
                    : 'text-[#64748B] hover:text-[#172033] hover:bg-slate-50'
                }`}
                title="Tampilkan Layar Browser Chromium Bot"
              >
                <span>🌐 Chromium</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setStreamSource('auto');
                  setStreamTimestamp(Date.now());
                  showToast('Mode Pintar: Chromium saat proses ulasan, Windows saat standby', 'info');
                }}
                className={`px-2 py-1 text-[10px] sm:text-[11px] rounded-md transition cursor-pointer whitespace-nowrap min-h-[30px] font-bold flex items-center gap-1 ${
                  streamSource === 'auto'
                    ? 'bg-blue-600 text-white shadow-2xs'
                    : 'text-[#64748B] hover:text-[#172033] hover:bg-slate-50'
                }`}
                title="Otomatis: Chromium saat ulasan, Windows saat siaga"
              >
                <span>⚡ Auto</span>
              </button>
            </div>

            {/* Video Player Actions */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => {
                  const nextMode = streamMode === 'MJPEG' ? 'PNG' : 'MJPEG';
                  setStreamMode(nextMode);
                  showToast(`Mode tampilan: ${nextMode === 'MJPEG' ? 'Stream MJPEG' : 'Snapshot PNG'}`, 'info');
                }}
                className="min-h-[32px] p-1 rounded text-[#64748B] hover:text-[#2563EB] hover:bg-slate-100 border border-slate-200 text-[11px] font-medium flex items-center gap-1 px-2 cursor-pointer"
                title="Ganti Mode Stream MJPEG / Snapshot PNG"
              >
                <Video className="w-3.5 h-3.5 text-emerald-600" />
                <span>{streamMode}</span>
              </button>

              <button
                onClick={() => {
                  setStreamPaused(!streamPaused);
                  showToast(streamPaused ? 'Streaming dilanjutkan' : 'Streaming dijeda', 'info');
                }}
                className="min-h-[32px] min-w-[32px] flex items-center justify-center p-1.5 rounded text-[#64748B] hover:text-[#172033] hover:bg-slate-100 border border-slate-200 cursor-pointer"
                title="Jeda/Lanjutkan Stream"
              >
                {streamPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
              </button>

              <button
                onClick={() => {
                  setStreamTimestamp(Date.now());
                  setStreamError(false);
                  showToast('Preview frame diperbarui', 'info');
                }}
                className="min-h-[32px] min-w-[32px] flex items-center justify-center p-1.5 rounded text-[#64748B] hover:text-[#172033] hover:bg-slate-100 border border-slate-200 cursor-pointer"
                title="Reload Frame Snapshot"
              >
                <RotateCw className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={toggleFullscreen}
                className="min-h-[32px] min-w-[32px] flex items-center justify-center p-1.5 rounded text-[#64748B] hover:text-[#172033] hover:bg-slate-100 border border-slate-200 cursor-pointer"
                title="Fullscreen Monitor"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Video Player Screen (DYNAMIC 1 S/D 6 SHARESCREEN MONITORS) */}
          <div className="p-2 sm:p-3 lg:p-4 bg-slate-100/60 flex flex-col justify-center items-center">
            <div
              ref={streamContainerRef}
              className="w-full max-w-full bg-slate-900 rounded-xl overflow-hidden border border-slate-700/80 shadow-md relative p-2 sm:p-2.5 flex flex-col justify-between"
            >
              {/* Scanlines Effect Overlay */}
              <div className="stream-scanlines absolute inset-0 z-10 pointer-events-none opacity-25"></div>

              {/* SHARED SCREEN CONTAINER */}
              <div className="relative z-20 w-full flex flex-col justify-center">
                {currentView === 'split' ? (
                  /* MULTI-SCREEN GRID (1, 2, OR 3 MONITORS BASED ON accountCount) */
                  <div
                    className={`w-full grid gap-2 sm:gap-2.5 ${
                      accountCount === 1
                        ? 'grid-cols-1'
                        : accountCount === 2
                        ? 'grid-cols-1 sm:grid-cols-2'
                        : accountCount === 3
                        ? 'grid-cols-1 sm:grid-cols-3'
                        : accountCount === 4
                        ? 'grid-cols-1 sm:grid-cols-2'
                        : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
                    }`}
                  >
                    {activeSlots.map((slot) => {
                      const isLiveActive = streamMode !== 'CARDS' && selectedBusinessId;

                      return (
                        <div
                          key={slot.slotIndex}
                          className={`flex flex-col bg-slate-900/90 rounded-xl border ${slot.theme.border} overflow-hidden shadow-md flex-1 min-w-0 transition-all`}
                        >
                          {/* Screen Header Bar */}
                          <div className="bg-slate-800/95 px-2.5 py-1.5 border-b border-slate-700/80 flex items-center justify-between text-xs text-white shrink-0">
                            <div className="flex items-center gap-1.5 min-w-0">
                              <span
                                className={`w-2 h-2 rounded-full ${slot.theme.dot} ${
                                  workerStatus.running ? 'animate-pulse' : ''
                                }`}
                              ></span>
                              <span className="font-bold text-[11px] text-white whitespace-nowrap">
                                Layar 0{slot.slotNumber}
                              </span>
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 font-mono font-semibold flex items-center gap-1 shrink-0">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                                VM-{100 + slot.slotNumber}
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono truncate max-w-[120px] sm:max-w-[170px]">
                                {slot.account.email}
                              </span>
                            </div>

                            <div className="flex items-center gap-1 shrink-0">
                              <button
                                onClick={() => handleToggleVmSleep(slot.slotNumber)}
                                className={`p-1 rounded transition cursor-pointer text-xs flex items-center justify-center ${
                                  vmStates[100 + slot.slotNumber]?.is_sleeping
                                    ? 'text-amber-400 hover:text-amber-300 bg-amber-950/70 border border-amber-500/50'
                                    : 'text-slate-400 hover:text-cyan-300 hover:bg-slate-700'
                                }`}
                                title={
                                  vmStates[100 + slot.slotNumber]?.is_sleeping
                                    ? `Bangunkan Windows VM-${100 + slot.slotNumber} (Layar Nyala)`
                                    : `Set Mode Sleep Windows VM-${100 + slot.slotNumber}`
                                }
                              >
                                <span>{vmStates[100 + slot.slotNumber]?.is_sleeping ? '⚡' : '💤'}</span>
                              </button>
                              <a
                                href={`https://${window.location.hostname}:8006/?console=kvm&novnc=1&vmid=${100 + slot.slotNumber}&vmname=Win10-Review-Worker-0${slot.slotNumber}&node=pve`}
                                target="_blank"
                                rel="noreferrer"
                                className="p-1 rounded text-slate-400 hover:text-emerald-400 hover:bg-slate-700 transition cursor-pointer"
                                title={`Buka Console noVNC Proxmox VM-${100 + slot.slotNumber} (Full Kontrol)`}
                              >
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                              <button
                                onClick={() => setCurrentView(`acc${slot.slotNumber}`)}
                                className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 transition cursor-pointer"
                                title={`Perbesar Layar Akun ${slot.slotNumber}`}
                              >
                                <Maximize2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </div>

                          {/* Screen Live Viewport (Dedicated Chromium Slot Stream) */}
                          <div
                            className={`relative w-full ${
                              accountCount === 1
                                ? 'aspect-video sm:h-[320px] md:h-[380px]'
                                : accountCount === 2
                                ? 'aspect-video sm:h-[200px] md:h-[240px]'
                                : accountCount === 3
                                ? 'aspect-video sm:h-[160px] md:h-[190px]'
                                : 'aspect-video sm:h-[140px] md:h-[170px]'
                            } bg-black overflow-hidden flex items-center justify-center`}
                          >
                            <div className="stream-scanlines absolute inset-0 z-10 pointer-events-none opacity-30"></div>

                            <div
                              onClick={(e) => handleScreenViewportClick(e, slot.slotNumber)}
                              className="relative w-full h-full overflow-hidden bg-black flex items-center justify-center cursor-crosshair"
                            >
                              <img
                                src={
                                  streamMode === 'MJPEG' && !streamPaused
                                    ? `/business/${selectedBusinessId || 37}/slot/${slot.slotNumber}/chromium-stream.mjpg?source=${streamSource}&t=${streamTimestamp}`
                                    : `/business/${selectedBusinessId || 37}/slot/${slot.slotNumber}/chromium-preview.png?source=${streamSource}&t=${streamTimestamp}`
                                }
                                alt={`Layar Akun ${slot.slotNumber}`}
                                onError={() => {
                                  setTimeout(() => setStreamTimestamp(Date.now()), 1500);
                                }}
                                className="w-full h-full object-contain pointer-events-none"
                              />

                              {/* Sleeping Screen Overlay with click to wake */}
                              {vmStates[100 + slot.slotNumber]?.is_sleeping && (
                                <div
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleWakeVm(slot.slotNumber);
                                  }}
                                  className="absolute inset-0 z-20 bg-black/60 backdrop-blur-[1px] flex flex-col items-center justify-center cursor-pointer hover:bg-black/45 transition-colors group"
                                  title="Klik untuk menyalakan layar Windows VM"
                                >
                                  <div className="px-2.5 py-1.5 rounded-xl bg-slate-950/95 border border-amber-400/80 shadow-[0_0_15px_rgba(251,191,36,0.4)] flex items-center gap-2 text-white group-hover:scale-105 transition-transform">
                                    <span className="text-base animate-pulse">💤</span>
                                    <div className="flex flex-col text-left">
                                      <span className="text-amber-300 text-[10px] font-bold">Windows Sleep</span>
                                      <span className="text-[9px] text-slate-300">Klik untuk menyalakan ⚡</span>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>

                            {/* Claude AI Walking Mascot inside this Slot (Layar 01 s/d Layar 06) */}
                            <SlotWalkingMascot
                              slot={slot}
                              isLiveActive={isLiveActive}
                              isTaskRunning={workerStatus.running}
                              isSleeping={Boolean(vmStates[100 + slot.slotNumber]?.is_sleeping)}
                              onWake={() => handleWakeVm(slot.slotNumber)}
                              onMaximize={() => setCurrentView(`acc${slot.slotNumber}`)}
                              onRefresh={() => {
                                setStreamTimestamp(Date.now());
                                showToast(`Snapshot Layar 0${slot.slotNumber} diperbarui`, 'info');
                              }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  /* SINGLE FOCUSED MONITOR VIEW WITH BACK BUTTON */
                  (() => {
                    const accIdx = Math.max(0, parseInt(currentView.replace('acc', ''), 10) - 1);
                    const focusedSlot = activeSlots[accIdx] || activeSlots[0];
                    const isLiveActive = streamMode !== 'CARDS' && selectedBusinessId;

                    return (
                      <div className="w-full h-full flex flex-col justify-between relative bg-black rounded-lg overflow-hidden border border-slate-800">
                        {/* Focused Header Overlay */}
                        <div className="absolute top-2 left-2 right-2 z-30 flex items-center justify-between bg-black/85 backdrop-blur-xs px-2.5 py-1.5 rounded-lg border border-white/10 text-white text-xs">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className={`w-2 h-2 rounded-full ${focusedSlot.theme.dot} animate-pulse`}></span>
                            <span className="font-bold text-[11px] text-white whitespace-nowrap">
                              Fokus: Layar 0{focusedSlot.slotNumber} (VM-{100 + focusedSlot.slotNumber} · Slot 0{focusedSlot.slotNumber})
                            </span>
                            <span className="text-[10px] text-slate-300 font-mono truncate max-w-[130px] sm:max-w-[220px]">
                              {focusedSlot.account.email}
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5 shrink-0">
                            <button
                              onClick={() => handleToggleVmSleep(focusedSlot.slotNumber)}
                              className={`px-2 py-0.5 rounded text-[10px] font-mono transition cursor-pointer flex items-center gap-1 ${
                                vmStates[100 + focusedSlot.slotNumber]?.is_sleeping
                                  ? 'bg-amber-950/80 hover:bg-amber-900 text-amber-300 border border-amber-600/70'
                                  : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                              }`}
                              title={
                                vmStates[100 + focusedSlot.slotNumber]?.is_sleeping
                                  ? 'Bangunkan Layar Windows VM'
                                  : 'Set Mode Sleep Layar Windows VM'
                              }
                            >
                              <span>{vmStates[100 + focusedSlot.slotNumber]?.is_sleeping ? '⚡ Bangunkan' : '💤 Sleep'}</span>
                            </button>
                            <button
                              onClick={() => handleVmControl(focusedSlot.slotNumber, 'key', { key: 'ret' })}
                              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-200 border border-slate-700 font-mono transition cursor-pointer"
                              title="Kirim Tombol Enter ke VM"
                            >
                              Enter ↵
                            </button>
                            <button
                              onClick={() => handleVmControl(focusedSlot.slotNumber, 'key', { key: 'spc' })}
                              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-200 border border-slate-700 font-mono transition cursor-pointer"
                              title="Kirim Tombol Spasi ke VM"
                            >
                              Spasi ␣
                            </button>
                            <button
                              onClick={() => handleVmControl(focusedSlot.slotNumber, 'key', { key: 'tab' })}
                              className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-200 border border-slate-700 font-mono transition cursor-pointer"
                              title="Kirim Tombol Tab ke VM"
                            >
                              Tab ⇥
                            </button>
                            <a
                              href={`https://${window.location.hostname}:8006/?console=kvm&novnc=1&vmid=${100 + focusedSlot.slotNumber}&vmname=Win10-Review-Worker-0${focusedSlot.slotNumber}&node=pve`}
                              target="_blank"
                              rel="noreferrer"
                              className="px-2 py-0.5 rounded bg-emerald-950/80 hover:bg-emerald-900 text-emerald-400 border border-emerald-800/80 text-[10px] font-semibold flex items-center gap-1 transition"
                              title="Buka Console noVNC Proxmox (Layar Penuh & Kontrol Lengkap)"
                            >
                              <ExternalLink className="w-3 h-3" />
                              <span>noVNC PVE</span>
                            </a>
                            <button
                              onClick={() => setCurrentView('split')}
                              className="flex items-center gap-1 text-[11px] font-semibold text-blue-400 hover:text-white bg-blue-950/70 px-2.5 py-1 rounded border border-blue-500/40 cursor-pointer transition shrink-0 ml-1"
                            >
                              <ArrowLeft className="w-3.5 h-3.5" />
                              <span>Kembali</span>
                            </button>
                          </div>
                        </div>

                        {/* Focused Stream Video Viewport */}
                        <div className="relative w-full aspect-video sm:h-[360px] md:h-[400px] flex items-center justify-center overflow-hidden">
                          <div className="stream-scanlines absolute inset-0 z-10 pointer-events-none opacity-30"></div>

                          <div
                            onClick={(e) => handleScreenViewportClick(e, focusedSlot.slotNumber)}
                            className="relative w-full h-full flex items-center justify-center cursor-crosshair group"
                            title="Klik di layar untuk mengirim klik mouse langsung ke VM"
                          >
                            <img
                              src={
                                streamMode === 'MJPEG' && !streamPaused
                                  ? `/business/${selectedBusinessId || 37}/slot/${focusedSlot.slotNumber}/chromium-stream.mjpg?source=${streamSource}&t=${streamTimestamp}`
                                  : `/business/${selectedBusinessId || 37}/slot/${focusedSlot.slotNumber}/chromium-preview.png?source=${streamSource}&t=${streamTimestamp}`
                              }
                              alt={`Layar Akun ${focusedSlot.slotNumber}`}
                              onError={() => {
                                setTimeout(() => setStreamTimestamp(Date.now()), 1500);
                              }}
                              className="w-full h-full object-contain pointer-events-none"
                            />

                            {/* Sleeping Screen Overlay with click to wake */}
                            {vmStates[100 + focusedSlot.slotNumber]?.is_sleeping && (
                              <div
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleWakeVm(focusedSlot.slotNumber);
                                }}
                                className="absolute inset-0 z-20 bg-black/60 backdrop-blur-[1.5px] flex flex-col items-center justify-center cursor-pointer hover:bg-black/45 transition-colors group"
                                title="Klik untuk menyalakan layar Windows VM"
                              >
                                <div className="px-3.5 py-2 rounded-xl bg-slate-950/95 border border-amber-400/80 shadow-[0_0_20px_rgba(251,191,36,0.4)] flex items-center gap-2.5 text-white group-hover:scale-105 transition-transform">
                                  <span className="text-xl animate-pulse">💤</span>
                                  <div className="flex flex-col text-left">
                                    <span className="text-amber-300 text-xs font-bold">Windows VM-{100 + focusedSlot.slotNumber} Sleep Mode</span>
                                    <span className="text-[10px] text-slate-300">Klik layar atau maskot bot untuk menyalakan ⚡</span>
                                  </div>
                                </div>
                              </div>
                            )}

                            <div className="absolute bottom-2 left-2 z-20 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity bg-black/80 px-2 py-1 rounded text-[10px] text-cyan-300 border border-cyan-500/30 flex items-center gap-1 backdrop-blur-xs">
                              <MousePointer className="w-3 h-3 text-cyan-400" />
                              <span>Klik layar untuk mengirim event mouse ke VM</span>
                            </div>
                          </div>

                          {/* Claude AI Walking Mascot inside Focused Screen */}
                          <SlotWalkingMascot
                            slot={focusedSlot}
                            isLiveActive={isLiveActive}
                            isTaskRunning={workerStatus.running}
                            isSleeping={Boolean(vmStates[100 + focusedSlot.slotNumber]?.is_sleeping)}
                            onWake={() => handleWakeVm(focusedSlot.slotNumber)}
                            onMaximize={() => {}}
                            onRefresh={() => {
                              setStreamTimestamp(Date.now());
                              showToast(`Snapshot Layar 0${focusedSlot.slotNumber} diperbarui`, 'info');
                            }}
                          />
                        </div>
                      </div>
                    );
                  })()
                )}
              </div>
            </div>
          </div>
        </section>

        {/* ==================== PANEL KANAN: KONFIGURASI & LOGCAT ==================== */}
        <section className="flex flex-col bg-white rounded-xl border border-[#DCE3ED] shadow-xs overflow-hidden min-w-0 h-auto">
          {/* TAB NAVIGATION HEADER */}
          <div className="px-2.5 sm:px-3.5 pt-2 pb-0 bg-slate-50/90 border-b border-[#DCE3ED] flex items-center justify-between gap-1.5 sm:gap-2 shrink-0">
            {/* Navigation Buttons */}
            <div className="flex items-center gap-1 sm:gap-2">
              <button
                onClick={() => setActiveRightTab('config')}
                className={`min-h-[40px] flex items-center gap-1.5 px-2.5 sm:px-3.5 py-2 text-xs font-bold border-b-2 transition cursor-pointer ${
                  activeRightTab === 'config'
                    ? 'border-[#2563EB] text-[#2563EB]'
                    : 'border-transparent text-[#64748B] hover:text-[#172033]'
                }`}
              >
                <Sliders className="w-4 h-4 shrink-0" />
                <span className="truncate">Konfigurasi & Kontrol</span>
              </button>

              <button
                onClick={() => setActiveRightTab('terminal')}
                className={`min-h-[40px] flex items-center gap-1.5 px-2.5 sm:px-3.5 py-2 text-xs font-bold border-b-2 transition cursor-pointer ${
                  activeRightTab === 'terminal'
                    ? 'border-[#2563EB] text-[#2563EB]'
                    : 'border-transparent text-[#64748B] hover:text-[#172033]'
                }`}
              >
                <Terminal className="w-4 h-4 shrink-0" />
                <span>Logcat</span>
                <span className="bg-slate-200 text-slate-700 text-[10px] px-1.5 py-0.2 rounded-full font-mono">
                  {logs.length}
                </span>
              </button>
            </div>

            {/* Right Quick Action in Tab Bar */}
            <div className="flex items-center gap-1.5 pb-1.5 shrink-0">
              <span className="relative flex h-2 w-2">
                <span className="radar-pulse absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#059669]"></span>
              </span>
              <span className="text-[11px] font-semibold text-emerald-700 hidden sm:inline">
                Engine Ready
              </span>
            </div>
          </div>

          {/* TAB CONTENT CONTAINER */}
          <div className="flex flex-col">
            {/* ==================== TAB 1: KONFIGURASI TARGET & EKSEKUSI ==================== */}
            {activeRightTab === 'config' && (
              <div className="p-3 sm:p-3.5 lg:p-4 space-y-3 sm:space-y-3.5">
                {/* 1. Target Bisnis Selector Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#172033]">
                      Pilihan Target Bisnis
                    </h3>
                    <p className="text-[11px] text-[#64748B]">
                      Tentukan target dan jalankan otomasi ulasan langsung.
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 flex-wrap sm:flex-nowrap">
                    <button
                      onClick={handleResetReviews}
                      className="min-h-[36px] inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-[#64748B] hover:text-[#DC2626] hover:bg-red-50 rounded-md border border-slate-200 transition cursor-pointer"
                      title="Reset Status Ulasan Target"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Reset</span>
                    </button>

                    <button
                      onClick={() => setIsConfigModalOpen(true)}
                      className="min-h-[36px] inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-[#172033] hover:text-[#2563EB] hover:bg-blue-50 rounded-md border border-slate-200 transition cursor-pointer"
                      title="Pengaturan Target & AI"
                    >
                      <SlidersHorizontal className="w-3.5 h-3.5 text-[#2563EB]" />
                      <span>Setting</span>
                    </button>

                    <button
                      onClick={() => setIsAddBusinessModalOpen(true)}
                      className="min-h-[36px] inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-white bg-[#2563EB] hover:bg-[#1D4ED8] rounded-md transition shadow-2xs cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>Tambah</span>
                    </button>
                  </div>
                </div>

                {/* 2. Business Dropdown & Maps Link */}
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <select
                      value={selectedBusinessId || ''}
                      onChange={(e) => handleTargetChange(e.target.value)}
                      className="min-h-[42px] w-full bg-white border border-[#DCE3ED] text-[#172033] text-xs sm:text-sm font-semibold rounded-lg px-3 py-2 pr-8 appearance-none focus:outline-none focus:ring-2 focus:ring-[#2563EB]/20 focus:border-[#2563EB] cursor-pointer"
                    >
                      {businesses.map((biz) => (
                        <option key={biz.id} value={biz.id}>
                          {biz.name}
                        </option>
                      ))}
                    </select>
                    <div className="absolute right-2.5 top-3 pointer-events-none text-slate-400">
                      <ChevronDown className="w-4 h-4" />
                    </div>
                  </div>

                  {activeBusiness.url && (
                    <a
                      href={activeBusiness.url}
                      target="_blank"
                      rel="noreferrer"
                      className="min-h-[42px] min-w-[42px] flex items-center justify-center rounded-lg border border-[#DCE3ED] text-[#2563EB] hover:bg-blue-50 transition shrink-0"
                      title="Buka di Google Maps"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>

                {/* Auto-Pilot Daemon Live Status Banner */}
                <div className="px-3 py-2 rounded-lg bg-emerald-950/70 border border-emerald-500/40 flex items-center justify-between text-xs text-emerald-300">
                  <div className="flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                    <span className="font-bold text-[11px] text-emerald-200">
                      Auto-Pilot Berjalan Otomatis (Tanpa Manual)
                    </span>
                  </div>
                  <span className="text-[10px] text-emerald-400 font-mono bg-emerald-900/60 px-2 py-0.5 rounded border border-emerald-700/50">
                    24/7 Background Scheduler
                  </span>
                </div>

                {/* 3. FAST ACTION BUTTONS (Responsive Grid & Touch-Friendly) */}
                <div className="grid grid-cols-1 sm:grid-cols-12 gap-2 pt-1">
                  <button
                    onClick={handleStopBot}
                    disabled={isStoppingBot}
                    className="sm:col-span-4 min-h-[44px] py-2.5 px-3 rounded-lg text-xs font-bold text-[#DC2626] bg-red-50 border border-red-200 hover:bg-red-100 disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center justify-center gap-1.5 cursor-pointer shadow-xs active:scale-[0.98]"
                    title="Paksa hentikan seluruh proses worker, Chromium browser, dan background scheduler"
                  >
                    <Square className="w-3.5 h-3.5 fill-current" />
                    <span>{isStoppingBot ? 'Menghentikan...' : 'Stop Engine'}</span>
                  </button>

                  <button
                    onClick={handleStartBot}
                    disabled={workerStatus.running || isStartingBot}
                    className="sm:col-span-8 min-h-[44px] py-2.5 px-4 rounded-lg text-xs font-bold text-white bg-gradient-to-r from-[#2563EB] to-[#1D4ED8] hover:brightness-105 disabled:opacity-50 active:scale-[0.99] transition flex items-center justify-center gap-2 shadow-sm shadow-blue-500/25 cursor-pointer"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>
                      {isStartingBot
                        ? 'Menyiapkan Engine...'
                        : `Jalankan Task (${accountCount} Akun · ${accountCount} Sharescreen)`}
                    </span>
                  </button>
                </div>

                {/* 4. Quick Metrics Bar */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-2.5 p-2.5 sm:p-3 rounded-lg bg-[#F8FAFC] border border-[#DCE3ED]">
                  <div>
                    <span className="block text-[10px] font-bold text-[#64748B] uppercase">
                      Tugas Terjadwal
                    </span>
                    <div className="text-xs sm:text-sm font-bold text-[#172033] flex items-center gap-1 mt-0.5">
                      <span>{accountCount} Task</span>
                      <span className="text-[10px] text-emerald-600 font-semibold bg-emerald-50 px-1 rounded border border-emerald-200">
                        Siap
                      </span>
                    </div>
                  </div>

                  <div>
                    <span className="block text-[10px] font-bold text-[#64748B] uppercase">
                      Kesiapan Akun
                    </span>
                    <div className="text-xs sm:text-sm font-bold text-[#172033] mt-0.5 truncate">
                      <span className="text-emerald-600">{completedReviews.length} Selesai</span>
                      {' · '}
                      <span className="text-[#2563EB]">{accountCount} Dipilih</span>
                    </div>
                  </div>

                  <div>
                    <span className="block text-[10px] font-bold text-[#64748B] uppercase">
                      Rating Target
                    </span>
                    <div className="text-xs sm:text-sm font-bold text-amber-500 flex items-center gap-1 mt-0.5">
                      <span className="text-[#172033]">5.0</span>
                      <span>★★★★★</span>
                    </div>
                  </div>

                  <div>
                    <span className="block text-[10px] font-bold text-[#64748B] uppercase">
                      Jeda Anti-Spam
                    </span>
                    <div className="text-xs sm:text-sm font-bold text-[#172033] flex items-center gap-1 mt-0.5">
                      <Clock className="w-3.5 h-3.5 text-[#0891B2] shrink-0" />
                      <span>{configDelay}s (±25%)</span>
                    </div>
                  </div>
                </div>

                {/* 5. PEMILIHAN JUMLAH AKUN & TAMPILAN SHARESCREEN */}
                <div className="p-3 bg-white border border-[#DCE3ED] rounded-lg space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5 text-[#2563EB]" />
                      <span className="text-xs font-bold text-[#172033]">
                        Atur Jumlah Layar (Maksimal 6):
                      </span>
                    </div>
                    <span className="text-[10px] font-mono font-bold text-[#2563EB] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {accountCount} Layar Aktif
                    </span>
                  </div>

                  {/* 6 Opsi Pilihan Layar: 1 s/d 6 */}
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 sm:gap-2">
                    {[
                      { count: 1, label: '1 Layar', desc: 'Single', mode: 'single' },
                      { count: 2, label: '2 Layar', desc: 'Paralel', mode: 'parallel' },
                      { count: 3, label: '3 Layar', desc: 'Paralel', mode: 'parallel' },
                      { count: 4, label: '4 Layar', desc: 'Paralel', mode: 'parallel' },
                      { count: 5, label: '5 Layar', desc: 'Paralel', mode: 'parallel' },
                      { count: 6, label: '6 Layar', desc: 'Maks 6', mode: 'parallel' },
                    ].map((opt) => (
                      <button
                        key={opt.count}
                        type="button"
                        onClick={() => {
                          setAccountCount(opt.count);
                          setExecutionMode(opt.mode);
                          setCurrentView('split');
                          showToast(`Mode dipilih: ${opt.count} Layar Monitor (Display :99 s/d :${98 + opt.count})`, 'info');
                        }}
                        className={`min-h-[46px] p-1.5 rounded-lg border text-center transition cursor-pointer flex flex-col items-center justify-center ${
                          accountCount === opt.count
                            ? 'border-[#2563EB] bg-blue-50/80 ring-2 ring-blue-500/20 shadow-2xs'
                            : 'border-slate-200 hover:bg-slate-50'
                        }`}
                      >
                        <span className={`block text-xs font-bold ${accountCount === opt.count ? 'text-[#2563EB]' : 'text-[#172033]'}`}>
                          {opt.label}
                        </span>
                        <span className="block text-[9px] text-slate-500">
                          {opt.desc}
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Preview Akun yang Ditugaskan */}
                  <div className="pt-1.5 border-t border-slate-100 flex flex-wrap gap-1.5 items-center justify-between">
                    <div className="flex flex-wrap gap-1.5 items-center">
                      <span className="text-[10px] text-slate-500 font-semibold">Slot Ditugaskan:</span>
                      {availableAccounts.slice(0, accountCount).map((acc, idx) => (
                        <span key={acc.id || idx} className="text-[10px] font-mono bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200 flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          <span className="font-bold text-blue-600">Slot-0{idx + 1} (:{99 + idx}):</span>
                          <span className="truncate max-w-[105px]">{acc.email}</span>
                        </span>
                      ))}
                    </div>
                    <button
                      type="button"
                      disabled={workerStatus.running || isStartingBot}
                      onClick={() => {
                        if (workerStatus.running || isStartingBot) return;
                        setAccountShuffleSeed(Date.now() + Math.floor(Math.random() * 1000));
                        showToast('Urutan akun layar berhasil diacak secara random!', 'info');
                      }}
                      className={`text-[10px] font-bold flex items-center gap-1 px-2 py-1 rounded-md border transition ${
                        workerStatus.running || isStartingBot
                          ? 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed opacity-60'
                          : 'text-blue-600 hover:text-blue-800 bg-blue-50 border-blue-200 hover:bg-blue-100 cursor-pointer'
                      }`}
                      title={workerStatus.running || isStartingBot ? 'Akun terkunci saat bot sedang berjalan' : 'Acak random akun yang ditugaskan ke layar'}
                    >
                      <RotateCw className="w-3 h-3" />
                      <span>{workerStatus.running || isStartingBot ? 'Akun Terkunci' : 'Acak Akun'}</span>
                    </button>
                  </div>
                </div>

                {/* 6. Queue Summary List With Progress Bar */}
                <div className="pt-1 space-y-2">
                  {/* Queue Header & Progress Status */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-[#172033]">
                          Daftar Antrean Ulasan ({reviews.length})
                        </span>
                        {queueProgressPercent === 100 && reviews.length > 0 ? (
                          <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded-full flex items-center gap-1 border border-emerald-200">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            <span>Selesai Semua</span>
                          </span>
                        ) : workerStatus.running ? (
                          <span className="text-[10px] font-bold text-blue-700 bg-blue-100 px-1.5 py-0.2 rounded-full flex items-center gap-1 border border-blue-200">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse"></span>
                            <span>Memproses...</span>
                          </span>
                        ) : null}
                      </div>

                      <div className="flex items-center gap-1 text-[11px] font-semibold">
                        <span className="text-[#2563EB] font-bold font-mono">
                          {completedReviews.length}/{reviews.length}
                        </span>
                        <span className="text-slate-400">·</span>
                        <span className="text-slate-700 font-mono font-bold bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                          {queueProgressPercent}%
                        </span>
                      </div>
                    </div>

                    {/* Modern Animated Progress Bar */}
                    <div className="w-full bg-slate-200/80 rounded-full h-2.5 overflow-hidden p-0.5 border border-slate-300/60 shadow-2xs">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ease-out ${
                          queueProgressPercent === 100
                            ? 'bg-gradient-to-r from-emerald-500 to-teal-500'
                            : 'bg-gradient-to-r from-[#2563EB] via-indigo-500 to-emerald-500'
                        } ${workerStatus.running ? 'animate-pulse' : ''}`}
                        style={{ width: `${Math.max(queueProgressPercent, reviews.length > 0 ? 3 : 0)}%` }}
                      ></div>
                    </div>

                    {/* Progress Detail Badges */}
                    <div className="flex items-center justify-between text-[10px] text-slate-500 font-mono pt-0.5 px-0.5">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                          <span className="text-emerald-700 font-bold">{completedReviews.length}</span> Selesai
                        </span>
                        {processingReviews.length > 0 && (
                          <span className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></span>
                            <span className="text-blue-700 font-bold">{processingReviews.length}</span> Proses
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                          <span>{pendingReviews.length}</span> Antrean
                        </span>
                        {failedReviews.length > 0 && (
                          <span className="flex items-center gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                            <span className="text-rose-600 font-bold">{failedReviews.length}</span> Gagal
                          </span>
                        )}
                      </div>
                      <span className="font-semibold text-slate-600 font-sans hidden sm:inline">
                        Progress Task
                      </span>
                    </div>
                  </div>

                  {/* Antrean Items Scroll Container (Gemini AI Review Queue Cards) */}
                  <div className="bg-[#F8FAFC] border border-[#DCE3ED] rounded-xl p-2 sm:p-2.5 text-xs space-y-2.5 max-h-[380px] sm:max-h-[440px] overflow-y-auto">
                    {reviews.length > 0 ? (
                      reviews.map((rev, idx) => {
                        const isReviewing = rev.status === 'processing' || rev.status === 'reviewing';
                        const isCompleted = rev.status === 'posted' || rev.status === 'reviewed';
                        const isFailed = rev.status === 'failed';

                        // Format timestamp from reviewed_at or created_at
                        const timeStr = formatReviewTime(rev.reviewed_at || rev.created_at);

                        return (
                          <div
                            key={rev.id || idx}
                            className={`rounded-xl p-3 border transition-all duration-200 shadow-2xs ${
                              isReviewing
                                ? 'bg-gradient-to-b from-blue-50/70 via-indigo-50/40 to-white border-blue-400 ring-2 ring-blue-500/20 shadow-md'
                                : isCompleted
                                ? 'bg-white border-slate-200 hover:border-slate-300'
                                : isFailed
                                ? 'bg-rose-50/40 border-rose-200 hover:border-rose-300'
                                : 'bg-white/90 border-slate-200 hover:border-slate-300'
                            }`}
                          >
                            {/* ── BAGIAN ATAS: NAMA AKUN + TIME + STAR + STATUS GEMINI ── */}
                            <div className="flex items-center justify-between gap-2 pb-2 border-b border-slate-100 flex-wrap">
                              {/* Nama Akun & Rating */}
                              <div className="flex items-center gap-1.5 min-w-0">
                                <span className="font-mono text-[10px] font-extrabold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 shrink-0">
                                  #{idx + 1}
                                </span>
                                <span className="font-bold text-slate-800 text-[11px] truncate max-w-[160px] sm:max-w-[210px]" title={rev.email}>
                                  {rev.email || `Akun Google #${idx + 1}`}
                                </span>
                                <span className="inline-flex items-center text-amber-500 text-[11px] font-bold shrink-0">
                                  ★ {rev.star_rating || 5}
                                </span>
                              </div>

                              {/* Time + Status Gemini Badge */}
                              <div className="flex items-center gap-1.5 shrink-0 ml-auto">
                                <span className="inline-flex items-center gap-1 text-[10px] text-slate-500 font-mono">
                                  <Clock className="w-3 h-3 text-slate-400" />
                                  <span>{isReviewing ? 'Sedang Proses' : timeStr}</span>
                                </span>

                                {isReviewing ? (
                                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xs animate-pulse">
                                    <Sparkles className="w-3 h-3 text-cyan-300 animate-spin" />
                                    <span>Gemini Berpikir...</span>
                                  </span>
                                ) : isCompleted ? (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                                    <span>Gemini Selesai</span>
                                  </span>
                                ) : isFailed ? (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-700 border border-rose-200">
                                    <AlertCircle className="w-3 h-3 text-rose-600" />
                                    <span>Gagal</span>
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
                                    <Sparkles className="w-3 h-3 text-amber-500" />
                                    <span>Antrean AI</span>
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* ── BAGIAN BAWAH: ULASAN GEMINI / THINKING LOADING ── */}
                            <div className="pt-2">
                              {isReviewing ? (
                                rev.review_text ? (
                                  /* Gemini already formulated the review text and is actively typing it in Chromium */
                                  <div className="p-2.5 rounded-lg bg-blue-50/70 border border-blue-200 text-slate-800 text-[11px] leading-relaxed">
                                    <div className="flex items-center justify-between mb-1">
                                      <span className="text-[10px] font-bold text-blue-700 flex items-center gap-1">
                                        <Sparkles className="w-3 h-3 text-blue-600" />
                                        Gemini Mengetik Ulasan di Maps:
                                      </span>
                                      <span className="text-[9px] text-blue-600 font-mono font-bold animate-pulse">● LIVE MENGETIK</span>
                                    </div>
                                    <p className="italic text-slate-800 font-sans">
                                      "{rev.review_text}"
                                    </p>
                                  </div>
                                ) : (
                                  /* Gemini is thinking / loading and formulating review */
                                  <div className="p-2.5 rounded-lg bg-gradient-to-r from-blue-50 via-indigo-50/70 to-purple-50 border border-blue-200 text-slate-800 space-y-2">
                                    <div className="flex items-center justify-between">
                                      <span className="text-[11px] font-bold text-blue-900 flex items-center gap-1.5">
                                        <Sparkles className="w-3.5 h-3.5 text-blue-600 animate-spin" />
                                        <span>Gemini sedang berpikir & menganalisis ulasan</span>
                                        <span className="flex gap-0.5 ml-1">
                                          <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-bounce [animation-delay:-0.3s]"></span>
                                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-bounce [animation-delay:-0.15s]"></span>
                                          <span className="w-1.5 h-1.5 rounded-full bg-purple-600 animate-bounce"></span>
                                        </span>
                                      </span>
                                      <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 border border-blue-200">
                                        Gemini AI
                                      </span>
                                    </div>
                                    <p className="text-[11px] text-blue-900/80 italic leading-relaxed">
                                      Sedang menganalisis jenis usaha <strong>{activeBusiness.name || 'target'}</strong>, meracik pengalaman ulasan bintang {rev.star_rating || 5}, dan menginjeksi ke formulir ulasan Google Maps...
                                    </p>
                                    <div className="w-full bg-blue-200/50 h-1.5 rounded-full overflow-hidden">
                                      <div className="h-full bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400 rounded-full animate-pulse w-3/4"></div>
                                    </div>
                                  </div>
                                )
                              ) : isCompleted ? (
                                /* Review Successfully Completed and Published by Gemini */
                                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-800 text-[11px] leading-relaxed">
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="text-[10px] font-bold text-emerald-700 flex items-center gap-1">
                                      <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                                      Ulasan Terbit (Google Maps):
                                    </span>
                                    <div className="flex items-center gap-2">
                                      <span className="text-amber-500 font-bold text-[10px]">
                                        {'★'.repeat(rev.star_rating || 5)}{'☆'.repeat(5 - (rev.star_rating || 5))}
                                      </span>
                                      <button
                                        type="button"
                                        onClick={() => handleDeleteOwnReviewsOnMaps(rev.email_id)}
                                        disabled={isDeletingMapsReviews}
                                        className="text-[9.5px] font-semibold text-rose-600 hover:text-rose-800 hover:bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200 transition cursor-pointer flex items-center gap-0.5"
                                        title="Hapus ulasan ini langsung dari Google Maps"
                                      >
                                        <Trash2 className="w-2.5 h-2.5" />
                                        <span>Hapus di Maps</span>
                                      </button>
                                    </div>
                                  </div>
                                  <p className="italic text-slate-700 font-sans">
                                    "{rev.review_text || 'Pelayanan memuaskan dan sangat direkomendasikan.'}"
                                  </p>
                                </div>
                              ) : isFailed ? (
                                /* Failed / Needs Retry */
                                <div className="p-2.5 rounded-lg bg-rose-50/70 border border-rose-200 text-rose-800 text-[11px] flex items-center justify-between">
                                  <span className="flex items-center gap-1.5">
                                    <AlertCircle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                                    <span>{rev.review_text || 'Proses ulasan belum berhasil dikirim (sesi akun atau browser terkendala).'}</span>
                                  </span>
                                  <span className="text-[10px] font-bold uppercase text-rose-600 font-mono shrink-0 ml-2">Gagal</span>
                                </div>
                              ) : (
                                /* Pending / Waiting for Gemini */
                                <div className="p-2 rounded-lg bg-slate-50/70 border border-dashed border-slate-200 text-slate-500 text-[11px] flex items-center justify-between">
                                  <span className="italic flex items-center gap-1.5">
                                    <Sparkles className="w-3 h-3 text-slate-400 shrink-0" />
                                    Menunggu antrean: Gemini AI akan otomatis meracik ulasan bintang {rev.star_rating || 5}...
                                  </span>
                                  <span className="text-[10px] font-bold text-slate-400 uppercase font-mono shrink-0 ml-2">Menunggu</span>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <div className="text-center py-6 text-slate-400 text-xs">
                        Belum ada tugas ulasan. Klik tombol <strong>Jalankan Task</strong> untuk memproses ulasan otomatis.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ==================== TAB 2: LOGCAT / LIVE TERMINAL WORKER ==================== */}
            {activeRightTab === 'terminal' && (
              <div className="flex flex-col bg-white">
                {/* Terminal Toolbar: Search & Quick Filters */}
                <div className="px-2.5 sm:px-3.5 py-2 bg-slate-100/75 border-b border-[#DCE3ED] flex flex-wrap items-center justify-between gap-2 text-xs shrink-0">
                  {/* Search */}
                  <div className="relative flex-1 min-w-[140px]">
                    <input
                      type="text"
                      value={logSearch}
                      onChange={(e) => setLogSearch(e.target.value)}
                      placeholder="Cari akun, kata kunci, slot..."
                      className="min-h-[34px] w-full bg-white border border-[#DCE3ED] rounded-md px-2.5 py-1 text-[11px] font-mono focus:outline-none focus:border-[#2563EB]"
                    />
                    <Search className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-2.5 pointer-events-none" />
                  </div>

                  {/* Level Filters with horizontal scrolling on mobile */}
                  <div className="flex items-center gap-1 text-[11px] overflow-x-auto no-scrollbar py-0.5">
                    {['ALL', 'INFO', 'SUCCESS', 'WARN', 'ERROR'].map((lvl) => (
                      <button
                        key={lvl}
                        onClick={() => setLogFilterLevel(lvl)}
                        className={`min-h-[30px] px-2 py-0.5 rounded transition cursor-pointer font-semibold whitespace-nowrap ${
                          logFilterLevel === lvl
                            ? 'bg-[#2563EB] text-white'
                            : 'text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {lvl}
                      </button>
                    ))}
                  </div>

                  {/* Terminal Actions */}
                  <div className="flex items-center gap-1 flex-wrap">
                    <button
                      onClick={() => setAutoScroll(!autoScroll)}
                      className={`min-h-[32px] p-1 rounded border text-[11px] font-medium flex items-center gap-1 px-1.5 cursor-pointer ${
                        autoScroll
                          ? 'text-[#2563EB] bg-blue-50 border-blue-200'
                          : 'text-slate-500 bg-white border-slate-200'
                      }`}
                      title="Toggle Auto-Scroll"
                    >
                      <ArrowDownToLine className="w-3.5 h-3.5" />
                      <span className="text-[10px]">Auto</span>
                    </button>

                    <button
                      onClick={() => setLogPaused(!logPaused)}
                      className={`min-h-[32px] min-w-[32px] flex items-center justify-center p-1 rounded border cursor-pointer ${
                        logPaused
                          ? 'text-amber-600 bg-amber-50 border-amber-200'
                          : 'text-[#64748B] hover:text-[#172033] hover:bg-slate-200 border-slate-200'
                      }`}
                      title="Jeda Aliran Log"
                    >
                      <Pause className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={handleCopyLogs}
                      className="min-h-[32px] min-w-[32px] flex items-center justify-center p-1 rounded border text-[#64748B] hover:text-[#172033] hover:bg-slate-200 border-slate-200 cursor-pointer"
                      title="Salin Log"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={handleDownloadLogs}
                      className="min-h-[32px] min-w-[32px] flex items-center justify-center p-1 rounded border text-[#64748B] hover:text-[#172033] hover:bg-slate-200 border-slate-200 cursor-pointer"
                      title="Download Log"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>

                    <button
                      onClick={handleClearTerminal}
                      className="min-h-[32px] inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold text-[#DC2626] hover:bg-red-50 rounded border border-red-200 transition cursor-pointer"
                      title="Bersihkan Tampilan Log"
                    >
                      <Trash2 className="w-3 h-3" />
                      <span>Clear</span>
                    </button>
                  </div>
                </div>

                {/* Terminal Output Viewport */}
                <div className="h-[420px] sm:h-[480px] p-2.5 sm:p-3.5 bg-[#F8FAFC] overflow-y-auto font-mono text-[10px] sm:text-[11px] leading-relaxed select-text space-y-1">
                  {filteredLogs.length > 0 ? (
                    filteredLogs.map((item, idx) => {
                      const lvl = (item.level || 'INFO').toUpperCase();
                      const lvlColor =
                        lvl === 'ERROR'
                          ? 'text-rose-600 bg-rose-50'
                          : lvl === 'WARN'
                          ? 'text-amber-600 bg-amber-50'
                          : lvl === 'SUCCESS'
                          ? 'text-emerald-600 bg-emerald-50'
                          : 'text-blue-600 bg-blue-50';

                      return (
                        <div
                          key={idx}
                          className="log-row text-slate-600 flex items-start gap-1.5 sm:gap-2 hover:bg-slate-100/80 px-1 py-0.5 rounded transition"
                        >
                          <span className="text-slate-400 select-none text-[9px] sm:text-[10px] shrink-0">
                            {item.time || '12:00:00'}
                          </span>
                          <span className={`font-bold px-1 rounded text-[9px] sm:text-[10px] shrink-0 ${lvlColor}`}>
                            [{lvl}]
                          </span>
                          {item.source && (
                            <span className="text-slate-500 font-bold shrink-0 text-[9px] sm:text-[10px]">
                              [{item.source}]
                            </span>
                          )}
                          <span className="text-slate-700 break-words flex-1 min-w-0">
                            {item.message}
                          </span>
                        </div>
                      );
                    })
                  ) : (
                    <div className="h-full flex items-center justify-center text-slate-400 italic py-8">
                      Tidak ada rekaman logcat.
                    </div>
                  )}
                  <div ref={terminalEndRef} />
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      {/* ========================================================================= */}
      {/* 3. MODALS (RESPONSIVE DIALOGS)                                            */}
      {/* ========================================================================= */}

      {/* MODAL 1: COOKIE MANAGER */}
      {isCookieModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-2.5 sm:p-4">
          <div className="bg-white rounded-xl border border-[#DCE3ED] shadow-xl max-w-xl w-full max-h-[90dvh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-4 sm:px-5 py-3 sm:py-3.5 bg-slate-50 border-b border-[#DCE3ED] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <div className="p-1 rounded-md bg-amber-100 text-amber-600">
                  <Cookie className="w-4 h-4" />
                </div>
                <h3 className="text-sm font-bold text-[#172033]">Kelola Cookie & Akun Google</h3>
              </div>
              <button
                onClick={() => setIsCookieModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-md cursor-pointer min-h-[36px] min-w-[36px] flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3.5 sm:p-5 space-y-3 sm:space-y-4 text-xs overflow-y-auto flex-1 min-h-0">
              <p className="text-slate-600 leading-normal">
                Injeksi cookie JSON langsung via CDP bypass login manual dan 2FA Google. Setiap layar monitor (Layar 01 s/d 06) memerlukan cookie dari <strong>akun Google yang berbeda</strong> agar ulasan dapat terbit tanpa tabrakan akun.
              </p>

              {/* Alert Banner if Duplicate Cookies Detected */}
              {cookiesList.some((c) => c.is_duplicate) && (
                <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
                  <div className="space-y-1">
                    <p className="font-bold text-amber-800">
                      Perhatian: Terdeteksi Cookie dengan Sesi Akun yang Sama
                    </p>
                    <p className="text-[11px] text-amber-700 leading-relaxed">
                      Beberapa entri cookie di bawah memiliki token sesi identik dari 1 akun Google yang sama. Google Maps hanya mengizinkan 1 ulasan per akun per lokasi. Hapus entri duplikat dan pastikan Anda menyalin cookie dari <strong>profil akun Google yang berbeda</strong> di browser Anda untuk tiap layar.
                    </p>
                  </div>
                </div>
              )}

              {/* Akun List Table (Responsive with horizontal scrolling) */}
              <div className="border border-[#DCE3ED] rounded-lg overflow-x-auto w-full">
                <table className="w-full text-left text-slate-700 min-w-[320px]">
                  <thead className="bg-slate-50 border-b border-[#DCE3ED] text-[10px] font-bold uppercase text-[#64748B]">
                    <tr>
                      <th className="p-2 sm:p-2.5">Email Akun</th>
                      <th className="p-2 sm:p-2.5">Status Sesi</th>
                      <th className="p-2 sm:p-2.5 text-right">Aksi</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                    {cookiesList.length > 0 ? (
                      cookiesList.map((c) => (
                        <tr key={c.id} className={c.is_duplicate ? 'bg-amber-50/40' : ''}>
                          <td className="p-2 sm:p-2.5 font-medium">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="truncate max-w-[150px] sm:max-w-none">{c.email}</span>
                              {c.is_duplicate && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-amber-200 text-amber-900 border border-amber-300">
                                  Duplikat Sesi
                                </span>
                              )}
                            </div>
                            {c.is_duplicate && c.duplicate_with && c.duplicate_with.length > 0 && (
                              <span className="block text-[9.5px] text-amber-600 font-sans mt-0.5">
                                Sesi sama dengan: {c.duplicate_with[0]}
                              </span>
                            )}
                          </td>
                          <td className="p-2 sm:p-2.5 whitespace-nowrap">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                                c.status === 'valid' || c.status === 'active'
                                  ? 'bg-emerald-100 text-emerald-700'
                                  : 'bg-amber-100 text-amber-700'
                              }`}
                            >
                              {c.status || 'Valid (Active)'}
                            </span>
                          </td>
                          <td className="p-2 sm:p-2.5 text-right space-x-2 whitespace-nowrap">
                            <button
                              onClick={() => handleTestCookie(c.id, c.email)}
                              className="text-[#2563EB] hover:underline font-sans text-xs cursor-pointer py-1"
                            >
                              Cek Sesi
                            </button>
                            <button
                              onClick={() => handleDeleteCookie(c.id, c.email)}
                              className="text-rose-600 hover:underline font-sans text-xs cursor-pointer py-1"
                            >
                              Hapus
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="3" className="p-3 text-center text-slate-400">
                          Belum ada cookie tersimpan. Silakan tambahkan di bawah.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Add New Cookie Box */}
              <form onSubmit={handleAddCookie} noValidate className="space-y-2 pt-2 border-t border-slate-200">
                <label className="block font-bold text-[#172033] text-xs">
                  Tambah Cookie Akun Google Baru:
                </label>
                <input
                  ref={cookieEmailInputRef}
                  type="text"
                  value={newCookieEmail}
                  onChange={(e) => setNewCookieEmail(e.target.value)}
                  placeholder="Email akun Google (Wajib beda untuk tiap layar, contoh: budi1@gmail.com)"
                  className="min-h-[40px] w-full bg-[#F8FAFC] border border-[#DCE3ED] rounded-lg p-2 text-xs focus:outline-none focus:border-[#2563EB]"
                />
                <textarea
                  ref={cookieTextareaRef}
                  value={newCookieJson}
                  onChange={(e) => setNewCookieJson(e.target.value)}
                  placeholder='Tempel cookie di sini: format JSON [ { "name": "SID", "value": "..." } ], Netscape, atau string header SID=...; HSID=...'
                  rows="3"
                  className="w-full bg-[#F8FAFC] border border-[#DCE3ED] rounded-lg p-2 font-mono text-[10px] focus:outline-none focus:border-[#2563EB]"
                ></textarea>
                <p className="text-[10px] text-slate-500">
                  💡 <strong>Panduan Multi-Layar</strong>: Untuk mengisi Layar 01 s/d 06 dengan akun berbeda, buka profil akun Google lain di browser Anda, salin cookie-nya, dan masukkan email yang sesuai di atas sebelum klik simpan.
                </p>
                <div className="flex justify-end">
                  <button
                    type="submit"
                    onClick={handleAddCookie}
                    disabled={isAddingCookie}
                    className="min-h-[40px] px-4 py-1.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-semibold cursor-pointer disabled:opacity-50"
                  >
                    {isAddingCookie ? 'Menyimpan...' : 'Simpan & Injeksi'}
                  </button>
                </div>
              </form>
            </div>

            <div className="px-4 sm:px-5 py-3 bg-slate-50 border-t border-[#DCE3ED] flex items-center justify-between shrink-0">
              <button
                onClick={() => showToast('Template format JSON cookie disalin ke clipboard.', 'info')}
                className="text-xs text-[#2563EB] hover:underline font-medium flex items-center gap-1 cursor-pointer py-1"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Unduh Format Template</span>
              </button>
              <button
                onClick={() => setIsCookieModalOpen(false)}
                className="min-h-[38px] px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 text-xs font-semibold cursor-pointer"
              >
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: KONFIGURASI TARGET, PILIH STAR & DARK MODE */}
      {isConfigModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-2.5 sm:p-4 animate-in fade-in duration-150">
          <div className="bg-white rounded-xl border border-[#DCE3ED] shadow-2xl max-w-xl w-full max-h-[92dvh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-4 sm:px-5 py-3 sm:py-3.5 bg-slate-50 border-b border-[#DCE3ED] flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-blue-100 text-[#2563EB]">
                  <SlidersHorizontal className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#172033] flex items-center gap-1.5">
                    <span>Pengaturan Target & Engine</span>
                    <span className="text-[10px] font-mono text-slate-500 font-normal">
                      ({activeBusiness.name || 'Bisnis'})
                    </span>
                  </h3>
                </div>
              </div>
              <button
                onClick={() => setIsConfigModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-md cursor-pointer min-h-[36px] min-w-[36px] flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* TAB NAVIGATION: "Umum & AI" | "Pilih Star" | "Dark Mode" */}
            <div className="flex border-b border-[#DCE3ED] bg-slate-100/70 px-3 sm:px-4 gap-1 shrink-0 pt-1.5">
              <button
                type="button"
                onClick={() => setSettingTab('general')}
                className={`py-2 px-3 text-xs font-bold border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
                  settingTab === 'general'
                    ? 'border-[#2563EB] text-[#2563EB] bg-white rounded-t-lg border-t border-x -mb-[1px] shadow-2xs'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                <span>Umum & AI</span>
              </button>

              <button
                type="button"
                onClick={() => setSettingTab('stars')}
                className={`py-2 px-3 text-xs font-bold border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
                  settingTab === 'stars'
                    ? 'border-amber-500 text-amber-600 bg-white rounded-t-lg border-t border-x -mb-[1px] shadow-2xs'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                <span>Pilih Star</span>
              </button>

              <button
                type="button"
                onClick={() => setSettingTab('dark_mode')}
                className={`py-2 px-3 text-xs font-bold border-b-2 transition flex items-center gap-1.5 cursor-pointer ${
                  settingTab === 'dark_mode'
                    ? 'border-purple-600 text-purple-700 bg-white rounded-t-lg border-t border-x -mb-[1px] shadow-2xs'
                    : 'border-transparent text-slate-500 hover:text-slate-800'
                }`}
              >
                <ShieldAlert className="w-3.5 h-3.5 text-purple-600" />
                <span>Dark Mode</span>
                <span className="text-[9px] bg-purple-100 text-purple-700 font-extrabold px-1.5 py-0.2 rounded-full border border-purple-200">
                  Hapus & Report
                </span>
              </button>
            </div>

            {/* TAB CONTENTS */}
            <form onSubmit={handleSaveConfig} className="flex flex-col flex-1 min-h-0">
              <div className="p-3.5 sm:p-5 space-y-3.5 text-xs overflow-y-auto flex-1 min-h-0">
                {/* ── TAB 1: UMUM & PROMPT AI ── */}
                {settingTab === 'general' && (
                  <div className="space-y-3.5 animate-in fade-in duration-100">
                    {/* INPUT 1: TOKEN AI GEMINI (PASSWORD & EYE TOGGLE) */}
                    <div className="p-3 bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-slate-50 border border-blue-200/80 rounded-xl space-y-2">
                      <div className="flex items-center justify-between">
                        <label className="font-bold text-slate-800 flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                          <span>Token AI Gemini (API Key):</span>
                        </label>
                        {geminiToken ? (
                          <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full border border-emerald-300 flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Token Terpasang</span>
                          </span>
                        ) : (
                          <span className="text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200 font-medium">
                            Opsional / Menggunakan Template AI
                          </span>
                        )}
                      </div>

                      <div className="relative">
                        <input
                          type={showGeminiToken ? 'text' : 'password'}
                          value={geminiToken}
                          onChange={(e) => setGeminiToken(e.target.value)}
                          placeholder="Masukkan API Key Gemini (AIzaSy...)"
                          className="min-h-[40px] w-full bg-white border border-[#DCE3ED] rounded-lg pl-3 pr-10 py-2 text-xs font-mono text-slate-800 focus:outline-none focus:border-[#2563EB] focus:ring-2 focus:ring-blue-500/20"
                        />
                        <button
                          type="button"
                          onClick={() => setShowGeminiToken(!showGeminiToken)}
                          className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-700 transition cursor-pointer"
                          title={showGeminiToken ? "Sembunyikan Token" : "Tampilkan Token"}
                        >
                          {showGeminiToken ? <EyeOff className="w-4 h-4 text-slate-600" /> : <Eye className="w-4 h-4" />}
                        </button>
                      </div>

                      <div className="flex items-center justify-between text-[10px] text-slate-500 pt-0.5">
                        <span>Dapatkan token di Google AI Studio (aistudio.google.com).</span>
                        {geminiToken && (
                          <button
                            type="button"
                            onClick={handleTestGemini}
                            disabled={isTestingGemini}
                            className="font-bold text-blue-600 hover:text-blue-800 underline flex items-center gap-1 cursor-pointer disabled:opacity-50"
                          >
                            {isTestingGemini ? (
                              <span className="flex items-center gap-1">
                                <span className="w-2.5 h-2.5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></span>
                                Sedang Menguji AI...
                              </span>
                            ) : (
                              <span>✨ Uji Koneksi & Contoh Review</span>
                            )}
                          </button>
                        )}
                      </div>

                      {/* Box Pratinjau Ulasan Gemini AI jika dites */}
                      {geminiTestResult && (
                        <div className="mt-2 p-2.5 bg-white border border-blue-200 rounded-lg text-slate-800 text-[11px] animate-in fade-in duration-200">
                          <div className="flex items-center justify-between font-bold text-blue-700 mb-1">
                            <span className="flex items-center gap-1">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                              {geminiTestResult.message}
                            </span>
                            <span className="text-[10px] text-slate-500 font-normal">Kategori: {geminiTestResult.category_used}</span>
                          </div>
                          <p className="italic text-slate-700 bg-slate-50 p-2 rounded border border-slate-100">
                            "{geminiTestResult.sample_review}"
                          </p>
                        </div>
                      )}
                    </div>

                    {/* INPUT 2: BIDANG / JENIS USAHA TARGET (AI NICHE CONTEXT) */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <label className="block font-bold text-slate-700 flex items-center gap-1.5">
                          <Building2 className="w-3.5 h-3.5 text-blue-600" />
                          <span>Bidang / Jenis Usaha Target:</span>
                        </label>
                        <span className="text-[10px] text-blue-600 font-medium bg-blue-50 px-2 py-0.5 rounded border border-blue-100">
                          AI menyesuaikan topik ulasan
                        </span>
                      </div>
                      <select
                        value={businessCategory || 'auto'}
                        onChange={(e) => {
                          if (e.target.value === 'auto') setBusinessCategory('');
                          else if (e.target.value === 'Bengkel') setBusinessCategory('Bengkel / Otomotif (Servis, Oli, Aki, Montir, Ban, Sparepart)');
                          else if (e.target.value === 'Restoran') setBusinessCategory('Restoran / Cafe / Kuliner (Makanan, Minuman, Rasa, Pelayanan)');
                          else if (e.target.value === 'Klinik') setBusinessCategory('Klinik / Dokter / Apotek (Kesehatan, Pelayanan Medis, Obat)');
                          else if (e.target.value === 'Toko') setBusinessCategory('Toko / Retail / Swalayan (Kelengkapan Barang, Harga, Kasir)');
                          else if (e.target.value === 'Hotel') setBusinessCategory('Hotel / Penginapan / Wisma (Kamar, Kebersihan, Sarapan)');
                          else if (e.target.value === 'Jasa') setBusinessCategory('Jasa & Layanan Profesional (Ketepatan Waktu, Mutu)');
                          else setBusinessCategory(e.target.value);
                        }}
                        className="min-h-[40px] w-full bg-white border border-[#DCE3ED] rounded-lg px-3 py-2 text-xs font-medium focus:outline-none focus:border-[#2563EB]"
                      >
                        <option value="auto">🔍 Deteksi Otomatis AI (Dari Nama: "{activeBusiness.name || 'Target Bisnis'}")</option>
                        <option value="Bengkel">🔧 Bengkel & Otomotif (Servis kendaraan, Ganti Oli, Aki, Montir teliti, Ban, Sparepart)</option>
                        <option value="Restoran">🍽️ Restoran, Cafe & Kuliner (Cita rasa, Menu, Suasana, Porsi, Pelayanan)</option>
                        <option value="Klinik">🏥 Klinik, Dokter & Kesehatan (Penanganan dokter, Perawat ramah, Kebersihan, Obat)</option>
                        <option value="Toko">🛒 Toko Retail & Swalayan (Kelengkapan barang, Harga terjangkau, Kasir ramah)</option>
                        <option value="Hotel">🏨 Hotel, Wisma & Penginapan (Kamar bersih, Fasilitas, Sarapan enak, Resepsionis)</option>
                        <option value="Jasa">💼 Jasa & Layanan Profesional (Ketepatan waktu, Komunikasi ramah, Mutu)</option>
                        <option value="custom">✏️ Kustom / Input Sendiri...</option>
                      </select>
                      {(businessCategory && !['Bengkel / Otomotif (Servis, Oli, Aki, Montir, Ban, Sparepart)', 'Restoran / Cafe / Kuliner (Makanan, Minuman, Rasa, Pelayanan)', 'Klinik / Dokter / Apotek (Kesehatan, Pelayanan Medis, Obat)', 'Toko / Retail / Swalayan (Kelengkapan Barang, Harga, Kasir)', 'Hotel / Penginapan / Wisma (Kamar, Kebersihan, Sarapan)', 'Jasa & Layanan Profesional (Ketepatan Waktu, Mutu)'].includes(businessCategory)) && (
                        <input
                          type="text"
                          value={businessCategory}
                          onChange={(e) => setBusinessCategory(e.target.value)}
                          placeholder="Ketik jenis usaha spesifik (contoh: Bengkel AC Mobil, Salon Kecantikan, Toko Bangunan)..."
                          className="mt-1.5 min-h-[36px] w-full bg-[#F8FAFC] border border-[#DCE3ED] rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-[#2563EB]"
                        />
                      )}
                      <span className="text-[10px] text-slate-500 font-medium mt-1 block">
                        Contoh bengkel: AI Gemini akan otomatis mengulas montir, servis, oli, aki, atau ruang tunggu ber-AC.
                      </span>
                    </div>

                    {/* INPUT 3: GAYA BAHASA (TONE) */}
                    <div>
                      <label className="block font-bold text-slate-700 mb-1">
                        Gaya Bahasa Ulasan (Tone):
                      </label>
                      <select
                        value={configTone}
                        onChange={(e) => setConfigTone(e.target.value)}
                        className="min-h-[40px] w-full bg-white border border-[#DCE3ED] rounded-lg px-3 py-2 text-xs font-medium focus:outline-none focus:border-[#2563EB]"
                      >
                        <option value="formal">👔 Formal & Sopan (Profesional & Kemitraan Bisnis)</option>
                        <option value="casual">😊 Santai & Ramah (Pelanggan Kasual)</option>
                        <option value="enthusiastic">🌟 Sangat Puas / Antusias (Rekomendasi Tinggi)</option>
                        <option value="compact">⚡ Singkat & Padat (To the point)</option>
                        <option value="random">🎲 Acak / Variatif (Campuran Otomatis AI)</option>
                      </select>
                    </div>

                    {/* INPUT 4: PROMPT KATA KUNCI */}
                    <div>
                      <label className="block font-bold text-slate-700 mb-1">
                        Instruksi / Kata Kunci Tambahan (Opsional):
                      </label>
                      <textarea
                        value={configPrompt}
                        onChange={(e) => setConfigPrompt(e.target.value)}
                        rows="2"
                        className="w-full bg-[#F8FAFC] border border-[#DCE3ED] rounded-lg p-2.5 text-xs text-slate-800 focus:outline-none focus:border-[#2563EB]"
                        placeholder="Contoh: Tekankan pelayanan cepat, mekanik ramah, dan suku cadang asli..."
                      ></textarea>
                    </div>

                    {/* INPUT 5: JEDA & TARGET */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block font-bold text-slate-700 mb-1">
                          Jeda Antar Ulasan (Detik):
                        </label>
                        <input
                          type="number"
                          min="30"
                          value={configDelay}
                          onChange={(e) => setConfigDelay(e.target.value)}
                          className="min-h-[40px] w-full bg-white border border-[#DCE3ED] rounded-lg px-3 py-2 text-xs font-mono font-bold focus:outline-none focus:border-[#2563EB]"
                        />
                        <span className="text-[10px] text-emerald-600 font-medium mt-0.5 block">
                          Aman dari shadowban (≥ 60s)
                        </span>
                      </div>

                      <div>
                        <label className="block font-bold text-slate-700 mb-1">
                          Target Lokasi Bisnis:
                        </label>
                        <div className="min-h-[40px] bg-slate-50 border border-[#DCE3ED] rounded-lg px-3 py-2 text-slate-600 font-medium truncate flex items-center justify-between">
                          <span className="truncate">{activeBusiness.name || 'Target Terpilih'}</span>
                          {activeBusiness.url && (
                            <a href={activeBusiness.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline shrink-0 ml-1">
                              Maps ↗
                            </a>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Pengaturan Jumlah Layar Sharescreen (Max 6) */}
                    <div className="pt-2 border-t border-slate-100">
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="block font-bold text-slate-700">
                          Jumlah Layar Monitor / Worker Paralel:
                        </label>
                        <span className="text-[10px] font-mono font-bold text-[#2563EB] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                          {accountCount} Layar Aktif
                        </span>
                      </div>
                      <div className="grid grid-cols-6 gap-1.5">
                        {[1, 2, 3, 4, 5, 6].map((num) => (
                          <button
                            key={num}
                            type="button"
                            onClick={() => setAccountCount(num)}
                            className={`min-h-[42px] rounded-lg border text-xs font-bold transition cursor-pointer flex flex-col items-center justify-center ${
                              accountCount === num
                                ? 'bg-[#2563EB] text-white border-[#2563EB] shadow-xs ring-2 ring-blue-500/20'
                                : 'bg-white text-slate-700 border-[#DCE3ED] hover:bg-slate-50'
                            }`}
                          >
                            <span className="text-sm">{num}</span>
                            <span className="text-[9px] opacity-80 font-normal">Layar</span>
                          </button>
                        ))}
                      </div>
                      <span className="text-[10px] text-slate-500 font-medium mt-1 block">
                        Setiap layar terisolasi di virtual display terpisah (:99 s/d :104) dengan browser Chromium mandiri.
                      </span>
                    </div>
                  </div>
                )}

                {/* ── TAB 2: PILIH STAR (RATING MANAGEMENT) ── */}
                {settingTab === 'stars' && (
                  <div className="space-y-4 animate-in fade-in duration-100">
                    <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-900 flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="p-1.5 rounded-lg bg-amber-100 text-amber-600">
                          <Star className="w-4 h-4 fill-amber-500" />
                        </div>
                        <div>
                          <h4 className="font-bold text-xs text-amber-900">Distribusi Rating Bintang</h4>
                          <p className="text-[10.5px] text-amber-700">Tentukan persentase dan bintang yang akan dikirim bot ke target bisnis.</p>
                        </div>
                      </div>
                    </div>

                    {/* Mode Pilihan Star Preset */}
                    <div className="space-y-2">
                      <label className="block font-bold text-slate-700 text-xs">Pilih Pola Distribusi Bintang:</label>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        {/* Preset 1: 100% Bintang 5 */}
                        <div
                          role="button"
                          tabIndex={0}
                          onClick={() => { setStarMode('all5'); setConfigRating('5'); }}
                          className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                            starMode === 'all5'
                              ? 'border-amber-500 bg-amber-50/40 ring-2 ring-amber-500/20 shadow-xs'
                              : 'border-slate-200 bg-white hover:bg-slate-50'
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-bold text-xs text-slate-900">Maksimal Boost</span>
                              <span className="text-[9px] font-bold bg-emerald-100 text-emerald-800 px-1.5 py-0.2 rounded-full">100%</span>
                            </div>
                            <div className="flex text-amber-400 gap-0.5 text-xs mb-1">
                              ★★★★★
                            </div>
                            <p className="text-[10px] text-slate-500 leading-tight">Seluruh ulasan bot dijamin bintang 5 penuh.</p>
                          </div>
                        </div>

                        {/* Preset 2: Natural Mix */}
                        <div
                          role="button"
                          tabIndex={0}
                          onClick={() => { setStarMode('natural'); setConfigRating('5'); }}
                          className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                            starMode === 'natural'
                              ? 'border-amber-500 bg-amber-50/40 ring-2 ring-amber-500/20 shadow-xs'
                              : 'border-slate-200 bg-white hover:bg-slate-50'
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-bold text-xs text-slate-900">Natural Organic</span>
                              <span className="text-[9px] font-bold bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded-full">80/20</span>
                            </div>
                            <div className="flex items-center gap-1 text-[11px] mb-1">
                              <span className="text-amber-500 font-bold">5★ & 4★</span>
                            </div>
                            <p className="text-[10px] text-slate-500 leading-tight">Campuran 80% Bintang 5 & 20% Bintang 4 agar profil tampak sangat organik.</p>
                          </div>
                        </div>

                        {/* Preset 3: Kustom Manual */}
                        <div
                          role="button"
                          tabIndex={0}
                          onClick={() => setStarMode('custom')}
                          className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between ${
                            starMode === 'custom'
                              ? 'border-amber-500 bg-amber-50/40 ring-2 ring-amber-500/20 shadow-xs'
                              : 'border-slate-200 bg-white hover:bg-slate-50'
                          }`}
                        >
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-bold text-xs text-slate-900">Kustom Manual</span>
                              <span className="text-[9px] font-bold bg-purple-100 text-purple-800 px-1.5 py-0.2 rounded-full">1★ - 5★</span>
                            </div>
                            <div className="flex items-center gap-1 text-[11px] mb-1 text-slate-700 font-bold">
                              Bebas Atur
                            </div>
                            <p className="text-[10px] text-slate-500 leading-tight">Tentukan rasio bintang 1 sampai 5 secara terperinci.</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Jika Kustom Dipilih: Input Kontrol per Level Bintang */}
                    {starMode === 'custom' && (
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2 animate-in fade-in duration-100">
                        <span className="font-bold text-[11px] text-slate-700 block">Atur Jumlah Review Tiap Bintang:</span>
                        <div className="grid grid-cols-5 gap-2">
                          {[5, 4, 3, 2, 1].map((st) => (
                            <div key={st} className="flex flex-col items-center bg-white p-2 rounded-lg border border-slate-200 shadow-2xs">
                              <span className="text-xs font-bold text-slate-800 flex items-center gap-0.5">
                                {st}<Star className="w-3 h-3 text-amber-500 fill-amber-500" />
                              </span>
                              <input
                                type="number"
                                min="0"
                                max="100"
                                value={customStars[st] ?? 0}
                                onChange={(e) => setCustomStars({ ...customStars, [st]: Math.max(0, parseInt(e.target.value, 10) || 0) })}
                                className="w-full text-center mt-1 py-1 border border-slate-300 rounded font-bold text-xs font-mono focus:outline-none focus:border-amber-500"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Visual Star Preview Bar */}
                    <div className="p-3 bg-slate-900 rounded-xl text-white space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-300">Pratinjau Bobot Bintang:</span>
                        <span className="text-amber-400 font-bold font-mono">
                          {starMode === 'all5' ? '5.0 ★ Sempurna' : starMode === 'natural' ? '4.8 ★ Natural' : 'Kustom Mode'}
                        </span>
                      </div>
                      <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden flex">
                        {starMode === 'all5' && <div className="h-full bg-amber-400 w-full"></div>}
                        {starMode === 'natural' && (
                          <>
                            <div className="h-full bg-amber-400 w-[80%]"></div>
                            <div className="h-full bg-sky-400 w-[20%]"></div>
                          </>
                        )}
                        {starMode === 'custom' && (
                          <>
                            <div style={{ width: `${Math.min(100, Math.max(10, (customStars[5] || 0) * 15))}%` }} className="h-full bg-amber-400"></div>
                            <div style={{ width: `${Math.min(100, Math.max(5, (customStars[4] || 0) * 15))}%` }} className="h-full bg-sky-400"></div>
                            <div style={{ width: `${Math.min(100, (customStars[3] || 0) * 15)}%` }} className="h-full bg-yellow-500"></div>
                            <div style={{ width: `${Math.min(100, (customStars[2] || 0) * 15)}%` }} className="h-full bg-orange-500"></div>
                            <div style={{ width: `${Math.min(100, (customStars[1] || 0) * 15)}%` }} className="h-full bg-rose-500"></div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* ── TAB 3: DARK MODE (HAPUS KOMENTAR & REPORT MAP) ── */}
                {settingTab === 'dark_mode' && (
                  <div className="space-y-3.5 animate-in fade-in duration-100">
                    <div className="p-3 rounded-xl bg-slate-950 border border-purple-900/50 text-white flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-lg bg-purple-950 border border-purple-700/50 text-purple-400">
                          <ShieldAlert className="w-5 h-5" />
                        </div>
                        <div>
                          <h4 className="font-bold text-xs text-purple-200 flex items-center gap-1.5">
                            <span>Dark Mode Operasi Khusus</span>
                            <span className="text-[9px] bg-purple-500/20 text-purple-300 font-mono px-1.5 py-0.2 rounded border border-purple-500/30">Hapus & Report</span>
                          </h4>
                          <p className="text-[10px] text-slate-400">Fitur penghapusan komentar ulasan & pelaporan profil Google Maps.</p>
                        </div>
                      </div>
                    </div>

                    {/* Section 1: Hapus Komentar & Ulasan Target */}
                    <div className="p-3.5 rounded-xl bg-rose-50/50 border border-rose-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Trash2 className="w-4 h-4 text-rose-600" />
                          <span className="font-bold text-xs text-rose-900">1. Hapus Komentar & Riwayat Ulasan Target</span>
                        </div>
                        <span className="text-[9.5px] font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full border border-rose-200">
                          Bersihkan Database
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600 leading-relaxed">
                        Hapus seluruh ulasan dan draft komentar bot untuk target <strong>"{activeBusiness.name}"</strong> dari sistem. Antrean akan dibersihkan dan akun-akun Google terkait dapat ditugaskan kembali.
                      </p>
                      <div className="pt-1 flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-mono">
                          Total Riwayat: {(businessDetail?.reviews || []).length} Ulasan
                        </span>
                        <button
                          type="button"
                          onClick={handleDeleteAllComments}
                          disabled={isDeletingComments}
                          className="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 disabled:opacity-50 transition cursor-pointer flex items-center gap-1.5 shadow-xs"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>{isDeletingComments ? 'Menghapus...' : 'Hapus Semua Komentar Target'}</span>
                        </button>
                      </div>
                    </div>

                    {/* Section 2: Hapus Review & Komentar Akun Sendiri Langsung di Google Maps (Live Chromium) */}
                    <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-300/80 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Trash2 className="w-4 h-4 text-amber-700" />
                          <span className="font-bold text-xs text-amber-950">2. Hapus Review & Komentar Akun Sendiri di Google Maps</span>
                        </div>
                        <span className="text-[9.5px] font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full border border-amber-200 flex items-center gap-1">
                          <Sparkles className="w-3 h-3 text-amber-600" />
                          <span>Live Maps Deletion</span>
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-700 leading-relaxed">
                        Bot akan membuka browser Chromium dengan akun Google Anda, mendeteksi kartu <strong>"Ulasan Anda"</strong> pada Google Maps target <strong>"{activeBusiness.name}"</strong>, mengklik menu opsi ulasan, lalu mengeksekusi konfirmasi <strong>"Hapus ulasan"</strong> secara permanen langsung dari Google Maps publik.
                      </p>

                      <div className="p-2.5 rounded-lg bg-white border border-amber-200 text-[11px] space-y-1">
                        <div className="flex items-center justify-between text-slate-700 font-semibold">
                          <span>Ulasan Akun Sendiri Terbit di Maps:</span>
                          <span className="font-bold font-mono text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            {completedReviews.length} Ulasan Terbit
                          </span>
                        </div>
                        {completedReviews.length > 0 ? (
                          <div className="text-[10px] text-slate-500 font-mono truncate">
                            Akun: {completedReviews.map((r) => r.email).join(', ')}
                          </div>
                        ) : (
                          <div className="text-[10px] text-slate-400 italic">
                            Belum ada ulasan terbit dari akun bot pada target ini.
                          </div>
                        )}
                      </div>

                      <div className="pt-1 flex items-center justify-between">
                        <span className="text-[10px] text-amber-800/80 font-medium">
                          ⚠️ Aksi ini menghapus ulasan asli di Google Maps publik.
                        </span>
                        <button
                          type="button"
                          onClick={() => handleDeleteOwnReviewsOnMaps(null)}
                          disabled={isDeletingMapsReviews || completedReviews.length === 0}
                          className="px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 transition cursor-pointer flex items-center gap-1.5 shadow-xs"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>{isDeletingMapsReviews ? 'Sedang Menghapus di Maps...' : 'Hapus Review Sendiri di Google Maps'}</span>
                        </button>
                      </div>
                    </div>

                    {/* Section 3: Report Map */}
                    <div className="p-3.5 rounded-xl bg-purple-50/50 border border-purple-200 space-y-2.5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Flag className="w-4 h-4 text-purple-700" />
                          <span className="font-bold text-xs text-purple-900">3. Report Map Google</span>
                        </div>
                        <span className="text-[9.5px] font-bold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full border border-purple-200">
                          Sinyal Pelaporan
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600 leading-relaxed">
                        Kirim sinyal laporan resmi ke Google Maps untuk profil target kompetitor atau listing yang terindikasi melanggar pedoman Google Maps.
                      </p>

                      <div>
                        <label className="block text-[10.5px] font-bold text-slate-700 mb-1">
                          Kategori / Alasan Laporan Google:
                        </label>
                        <select
                          value={reportReason}
                          onChange={(e) => setReportReason(e.target.value)}
                          className="min-h-[38px] w-full bg-white border border-[#DCE3ED] rounded-lg px-2.5 py-1.5 text-xs font-medium focus:outline-none focus:border-purple-600"
                        >
                          <option value="spam_fake">🚨 Spam, Ulasan Palsu, atau Akun Bot Kompetitor</option>
                          <option value="closed_nonexistent">⛔ Tempat Bisnis Tutup Permanen / Fiktif</option>
                          <option value="conflict_interest">⚠️ Konflik Kepentingan / Manipulasi Reputasi</option>
                          <option value="offensive_content">❌ Konten Ofensif / Pelanggaran Pedoman Google</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-[10.5px] font-bold text-slate-700 mb-1">
                          Catatan Tambahan Laporan (Opsional):
                        </label>
                        <input
                          type="text"
                          value={reportNote}
                          onChange={(e) => setReportNote(e.target.value)}
                          placeholder="Contoh: Tempat tidak beroperasi di alamat ini / spam ulasan massal"
                          className="min-h-[36px] w-full bg-white border border-[#DCE3ED] rounded-lg px-2.5 py-1.5 text-xs text-slate-800 focus:outline-none focus:border-purple-600"
                        />
                      </div>

                      <div className="flex items-center justify-between pt-1 flex-wrap gap-2">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[11px] font-bold text-slate-700">Jumlah Akun:</span>
                          <div className="flex gap-1">
                            {[1, 2, 3, 6].map((cnt) => (
                              <button
                                key={cnt}
                                type="button"
                                onClick={() => setReportAccountCount(cnt)}
                                className={`px-2 py-1 rounded text-[10px] font-bold border transition cursor-pointer ${
                                  reportAccountCount === cnt
                                    ? 'bg-purple-600 text-white border-purple-600 shadow-2xs'
                                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                                }`}
                              >
                                {cnt} Akun
                              </button>
                            ))}
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={handleSendReportMap}
                          disabled={isReportingMap}
                          className="px-3.5 py-1.5 rounded-lg text-xs font-bold text-white bg-purple-700 hover:bg-purple-800 disabled:opacity-50 transition cursor-pointer flex items-center gap-1.5 shadow-xs"
                        >
                          <Flag className="w-3.5 h-3.5" />
                          <span>{isReportingMap ? 'Mengirim...' : 'Kirim Sinyal Report Map'}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="px-4 sm:px-5 py-3 bg-slate-50 border-t border-[#DCE3ED] flex items-center justify-between shrink-0">
                <span className="text-[11px] text-slate-400 font-mono">
                  Target: {activeBusiness.name || 'Pilih target'}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsConfigModalOpen(false)}
                    className="min-h-[38px] px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 text-xs font-semibold cursor-pointer"
                  >
                    Tutup
                  </button>
                  <button
                    type="submit"
                    disabled={isSavingConfig}
                    className="min-h-[38px] px-4 py-1.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-semibold cursor-pointer shadow-xs disabled:opacity-50"
                  >
                    {isSavingConfig ? 'Menyimpan...' : 'Simpan & Terapkan'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: TAMBAH TARGET BISNIS */}
      {isAddBusinessModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-2.5 sm:p-4">
          <div className="bg-white rounded-xl border border-[#DCE3ED] shadow-xl max-w-md w-full max-h-[90dvh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-4 sm:px-5 py-3 sm:py-3.5 bg-slate-50 border-b border-[#DCE3ED] flex items-center justify-between shrink-0">
              <h3 className="text-sm font-bold text-[#172033]">Tambah Target Bisnis Baru</h3>
              <button
                onClick={() => setIsAddBusinessModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1.5 rounded-md cursor-pointer min-h-[36px] min-w-[36px] flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddNewBusiness} className="flex flex-col flex-1 min-h-0">
              <div className="p-3.5 sm:p-5 space-y-3 text-xs overflow-y-auto flex-1 min-h-0">
                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    Nama Bisnis / Entitas:
                  </label>
                  <input
                    type="text"
                    required
                    value={newBusinessName}
                    onChange={(e) => setNewBusinessName(e.target.value)}
                    placeholder="Contoh: Toko Berkah Abadi Pemalang"
                    className="min-h-[40px] w-full bg-white border border-[#DCE3ED] rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-[#2563EB]"
                  />
                </div>

                <div>
                  <label className="block font-bold text-slate-700 mb-1">
                    URL Google Maps Bisnis:
                  </label>
                  <input
                    type="url"
                    required
                    value={newBusinessUrl}
                    onChange={(e) => setNewBusinessUrl(e.target.value)}
                    placeholder="https://maps.app.goo.gl/..."
                    className="min-h-[40px] w-full bg-white border border-[#DCE3ED] rounded-lg px-3 py-2 text-xs focus:outline-none focus:border-[#2563EB]"
                  />
                </div>
              </div>

              <div className="px-4 sm:px-5 py-3 bg-slate-50 border-t border-[#DCE3ED] flex items-center justify-end gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => setIsAddBusinessModalOpen(false)}
                  className="min-h-[40px] px-3.5 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 text-xs font-semibold cursor-pointer"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={isAddingBusiness}
                  className="min-h-[40px] px-4 py-1.5 rounded-lg bg-[#2563EB] hover:bg-[#1D4ED8] text-white text-xs font-semibold cursor-pointer"
                >
                  {isAddingBusiness ? 'Menambahkan...' : 'Tambah Target'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: GROK BOT MULTI-SCREEN SUPERVISOR MODAL */}
      {isClaudeModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full max-h-[92dvh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="px-4 sm:px-5 py-3.5 bg-gradient-to-r from-slate-900 via-slate-800 to-cyan-950 border-b border-slate-700 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-slate-950 border border-cyan-500/40 flex items-center justify-center p-0.5">
                  <GrokMascotAvatar size="sm" isRunning={workerStatus.running} interactive={false} />
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
                    <span>Grok AI Multi-Screen Supervisor</span>
                    <span className="text-[10px] bg-cyan-500 text-slate-950 font-bold px-1.5 py-0.2 rounded-full">Rounded Square Eyes</span>
                  </h3>
                  <p className="text-[11px] text-slate-400">Grok Bot Mengawasi Seluruh {accountCount} Layar</p>
                </div>
              </div>
              <button
                onClick={() => setIsClaudeModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-4 sm:p-5 space-y-4 text-xs overflow-y-auto flex-1 min-h-0">
              {/* Mascot Spotlight Card */}
              <div className="flex items-center gap-3.5 bg-gradient-to-br from-slate-900 to-slate-800 p-3.5 rounded-xl border border-slate-700 text-white">
                <div className="w-16 h-16 sm:w-18 sm:h-18 shrink-0 bg-slate-950 rounded-xl border border-cyan-500/30 flex items-center justify-center p-1 shadow-xs">
                  <GrokMascotAvatar size="md" isRunning={workerStatus.running} interactive={false} />
                </div>
                <div className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-cyan-400" />
                    Rounded Square Eyes Companion
                  </span>
                  <h4 className="font-bold text-white text-sm">Grok Bot Mengawal Semua Layar</h4>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    Grok Bot bertindak sebagai supervisor dengan mata rounded square eyes yang memantau {accountCount} proses browser independen di latar belakang. Tidak ada tabrakan sesi karena tiap slot dialokasikan ke display virtual Xvfb terpisah (:99 s/d :{98 + accountCount}).
                  </p>
                </div>
              </div>

              {/* Status Grid */}
              <div className="grid grid-cols-2 gap-2.5">
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 space-y-0.5">
                  <span className="text-[10px] text-slate-500 font-semibold uppercase">Total Layar Aktif</span>
                  <p className="font-bold text-slate-800 text-sm flex items-center gap-1 text-[#2563EB]">
                    <Layers className="w-4 h-4" />
                    <span>{accountCount} Slot Simultan</span>
                  </p>
                  <span className="text-[10px] text-emerald-600 font-medium">Display :99 s/d :{98 + accountCount}</span>
                </div>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 space-y-0.5">
                  <span className="text-[10px] text-slate-500 font-semibold uppercase">Isolasi Profil & Cookie</span>
                  <p className="font-bold text-slate-800 text-sm flex items-center gap-1 text-emerald-600">
                    <ShieldCheck className="w-4 h-4" />
                    <span>100% Terpisah</span>
                  </p>
                  <span className="text-[10px] text-slate-500 font-medium">Setiap slot mandiri</span>
                </div>
              </div>

              {/* Active Slots Telemetry List */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-slate-700 font-bold">
                  <span>Slot Layar yang Diawasi Claude AI:</span>
                  <span className="text-[11px] font-mono text-slate-500">{activeSlots.length} Online</span>
                </div>
                <div className="space-y-1.5">
                  {activeSlots.map((slot) => (
                    <div
                      key={slot.slotIndex}
                      className="flex items-center justify-between p-2 rounded-lg bg-white border border-slate-200 text-xs shadow-2xs"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className={`w-2.5 h-2.5 rounded-full ${slot.theme.dot}`}></span>
                        <span className="font-bold text-slate-800">Layar 0{slot.slotNumber}</span>
                        <span className="text-[11px] font-mono text-slate-500 truncate max-w-[150px]">
                          {slot.account.email}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0 font-mono text-[10px]">
                        <span className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-700 font-semibold">
                          Display {slot.display}
                        </span>
                        <span className="px-1.5 py-0.5 bg-emerald-50 text-emerald-700 rounded font-semibold border border-emerald-200">
                          {slot.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-4 sm:px-5 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between shrink-0">
              <span className="text-[11px] text-slate-500 flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-emerald-500" />
                <span>Supervisi aktif real-time</span>
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleClaudeSyncAllScreens}
                  className="min-h-[36px] px-3 py-1.5 rounded-lg border border-[#2563EB]/40 bg-white hover:bg-blue-50 text-[#2563EB] text-xs font-semibold flex items-center gap-1.5 cursor-pointer shadow-2xs"
                >
                  <RotateCw className="w-3.5 h-3.5" />
                  <span>Sinkronkan Frame</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsClaudeModalOpen(false)}
                  className="min-h-[36px] px-4 py-1.5 rounded-lg bg-[#172033] hover:bg-slate-800 text-white text-xs font-semibold cursor-pointer shadow-2xs"
                >
                  Tutup
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. TOAST NOTIFICATION CONTAINER                                           */}
      {/* ========================================================================= */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none max-w-[calc(100vw-32px)]">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto px-4 py-2.5 rounded-lg shadow-lg border text-xs font-medium flex items-center gap-2 animate-in slide-in-from-bottom-2 duration-200 ${
              toast.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : toast.type === 'error'
                ? 'bg-rose-50 border-rose-200 text-rose-800'
                : toast.type === 'warning'
                ? 'bg-amber-50 border-amber-200 text-amber-800'
                : 'bg-white border-[#DCE3ED] text-[#172033]'
            }`}
          >
            {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />}
            {toast.type === 'error' && <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />}
            {toast.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />}
            {toast.type === 'info' && <Info className="w-4 h-4 text-[#2563EB] shrink-0" />}
            <span className="break-words">{toast.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
