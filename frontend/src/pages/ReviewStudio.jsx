import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Star,
  Copy,
  Check,
  Send,
  Plus,
  Trash2,
  Bookmark,
  Award,
  UserCheck,
  Globe,
  Coffee,
  HeartPulse,
  Hotel,
  Wrench,
  Utensils,
  Briefcase,
  AlertCircle,
  CheckCircle2,
  X,
  Building2,
  Mail,
  ChevronRight,
  Sliders,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';

export default function ReviewStudio() {
  const [businesses, setBusinesses] = useState([]);
  const [emails, setEmails] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);

  // Form State
  const [selectedBizId, setSelectedBizId] = useState('');
  const [businessName, setBusinessName] = useState('Kopi Senja Utama');
  const [category, setCategory] = useState('Kafe & Kuliner');
  const [persona, setPersona] = useState('local_guide');
  const [starRating, setStarRating] = useState(5);
  const [language, setLanguage] = useState('Indonesian');
  const [description, setDescription] = useState('Kafe modern dengan racikan kopi nusantara, tempat kerja nyaman, wi-fi kencang.');
  const [keywords, setKeywords] = useState('kopi enak, suasana nyaman, barista ramah, wi-fi kencang');
  const [includeMinorCritique, setIncludeMinorCritique] = useState(true);

  // Output State
  const [generating, setGenerating] = useState(false);
  const [variations, setVariations] = useState([]);
  const [copiedId, setCopiedId] = useState(null);

  // Modals
  const [pushModal, setPushModal] = useState({ open: false, text: '', star: 5, persona: '' });
  const [pushBizId, setPushBizId] = useState('');
  const [pushEmailId, setPushEmailId] = useState('');
  const [submittingPush, setSubmittingPush] = useState(false);

  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [newTemplateTitle, setNewTemplateTitle] = useState('');
  const [savingTemplate, setSavingTemplate] = useState(false);

  const [notification, setNotification] = useState({ type: '', message: '' });

  const personas = [
    {
      id: 'local_guide',
      name: 'Google Local Guide',
      subtitle: 'Level 7 • Detail & Informatif',
      desc: 'Menjelaskan fasilitas, kemudahan parkir, kecepatan staf, dan atmosfer keseluruhan.',
      avatarColor: 'bg-amber-600',
      badge: 'Local Guide',
    },
    {
      id: 'foodie',
      name: 'Penikmat Rasa & Kuliner',
      subtitle: 'Food Enthusiast',
      desc: 'Fokus pada kelezatan racikan, konsistensi rasa makanan/minuman, dan value per porsi.',
      avatarColor: 'bg-emerald-600',
      badge: 'Foodie',
    },
    {
      id: 'casual',
      name: 'Pelanggan Santai',
      subtitle: 'Casual Customer',
      desc: 'Gaya bahasa to-the-point, santai, dan tidak kaku, layaknya ulasan pelanggan biasa.',
      avatarColor: 'bg-slate-700',
      badge: 'Pelanggan',
    },
    {
      id: 'family',
      name: 'Keluarga & Rombongan',
      subtitle: 'Family Trip',
      desc: 'Fokus pada keramahan pelayanan, kenyamanan tempat duduk, dan suasana yang ramah anak.',
      avatarColor: 'bg-indigo-600',
      badge: 'Family',
    },
    {
      id: 'tourist',
      name: 'International Traveler',
      subtitle: 'English Review',
      desc: 'Ulasan berbahasa Inggris dengan nada ramah untuk turis atau ekspatriat.',
      avatarColor: 'bg-sky-600',
      badge: 'Traveler',
    },
  ];

  const categories = [
    { name: 'Kafe & Kuliner', icon: Coffee, keywords: 'kopi enak, suasana nyaman, barista ramah, wi-fi kencang, spot foto estetik' },
    { name: 'Kesehatan', icon: HeartPulse, keywords: 'dokter ramah, penjelasan detail, tempat bersih, antrean teratur, staf responsif' },
    { name: 'Hospitality', icon: Hotel, keywords: 'kamar bersih, kasur empuk, sarapan lezat, lokasi strategis, kolam renang anak' },
    { name: 'Otomotif', icon: Wrench, keywords: 'mekanik jujur, estimasi harga transparan, pengerjaan rapi, ruang tunggu adem' },
    { name: 'Restoran', icon: Utensils, keywords: 'porsi pas, bumbu meresap, tempat parkir luas, cocok rombongan, harga bersahabat' },
    { name: 'Jasa Profesional', icon: Briefcase, keywords: 'komunikasi responsif, pengerjaan rapi, konsultasi jelas, tepat waktu' },
  ];

  const mockReviewerNames = [
    { name: 'Bambang Sudiro', meta: 'Local Guide • 94 ulasan • 140 foto' },
    { name: 'Dian Anggraini', meta: 'Local Guide • 62 ulasan • 88 foto' },
    { name: 'Rian Pratama', meta: '18 ulasan • 12 foto' },
  ];

  const loadInitialData = async () => {
    try {
      const [dashRes, tplRes] = await Promise.all([
        api.getDashboard(),
        api.getTemplates(),
      ]);

      if (dashRes) {
        setBusinesses(dashRes.businesses || []);
        setEmails(dashRes.all_emails || []);
        if (dashRes.businesses?.length > 0 && !selectedBizId) {
          setSelectedBizId(dashRes.businesses[0].id);
          setBusinessName(dashRes.businesses[0].name);
        }
      }
      if (tplRes && tplRes.templates) {
        setTemplates(tplRes.templates);
      }
    } catch (err) {
      console.error('Failed to load initial studio data:', err);
    } finally {
      setLoadingTemplates(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleSelectBusiness = (id) => {
    setSelectedBizId(id);
    const found = businesses.find((b) => String(b.id) === String(id));
    if (found) {
      setBusinessName(found.name);
    }
  };

  const handleApplyCategory = (cat) => {
    setCategory(cat.name);
    setKeywords(cat.keywords);
  };

  const handleApplyTemplate = (tpl) => {
    setBusinessName(businessName || tpl.title);
    setCategory(tpl.category || 'Umum');
    setPersona(tpl.persona || 'local_guide');
    setStarRating(tpl.star_rating || 5);
    setDescription(tpl.prompt_template || '');
    setKeywords(tpl.keywords || '');
    setNotification({
      type: 'success',
      message: `Template "${tpl.title}" berhasil dimuat ke editor!`,
    });
  };

  const handleGenerateVariations = async () => {
    setGenerating(true);
    setVariations([]);
    try {
      const res = await api.batchGenerate({
        business_name: businessName,
        category,
        description,
        keywords,
        persona,
        star_rating: starRating,
        language: persona === 'tourist' ? 'English' : language,
        include_minor_critique: includeMinorCritique,
      });

      if (res && res.variations) {
        setVariations(res.variations);
        setNotification({
          type: 'success',
          message: `${res.variations.length} draf ulasan berhasil dibuat.`,
        });
      }
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Gagal membuat variasi ulasan.',
      });
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleOpenPushModal = (variant) => {
    setPushModal({
      open: true,
      text: variant.text,
      star: variant.star_rating,
      persona: variant.persona,
    });
    setPushBizId(selectedBizId || (businesses[0]?.id || ''));
    const eligibleEmails = emails.filter((e) => !e.flagged);
    setPushEmailId(eligibleEmails[0]?.id || '');
  };

  const handlePushReview = async (e) => {
    e.preventDefault();
    if (!pushBizId) {
      alert('Pilih bisnis tujuan.');
      return;
    }
    setSubmittingPush(true);
    try {
      const res = await api.pushToBusiness({
        business_id: pushBizId,
        email_id: pushEmailId || undefined,
        star_rating: pushModal.star,
        review_text: pushModal.text,
        language: language,
      });
      setNotification({
        type: 'success',
        message: res.message || 'Ulasan berhasil dimasukkan ke antrean worker!',
      });
      setPushModal({ open: false, text: '', star: 5, persona: '' });
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Gagal menugaskan ulasan ke bisnis.',
      });
    } finally {
      setSubmittingPush(false);
    }
  };

  const handleSaveTemplate = async (e) => {
    e.preventDefault();
    if (!newTemplateTitle.trim()) return;
    setSavingTemplate(true);
    try {
      await api.addTemplate({
        title: newTemplateTitle.trim(),
        category,
        persona,
        star_rating: starRating,
        prompt_template: description,
        keywords,
        sample_output: variations[0]?.text || '',
      });
      setNotification({
        type: 'success',
        message: `Template "${newTemplateTitle}" disimpan ke pustaka!`,
      });
      setNewTemplateTitle('');
      setSaveModalOpen(false);
      const tplRes = await api.getTemplates();
      if (tplRes && tplRes.templates) setTemplates(tplRes.templates);
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Gagal menyimpan template.',
      });
    } finally {
      setSavingTemplate(false);
    }
  };

  const handleDeleteTemplate = async (id, title) => {
    if (!confirm(`Hapus template "${title}"?`)) return;
    try {
      await api.deleteTemplate(id);
      setTemplates((prev) => prev.filter((t) => t.id !== id));
      setNotification({
        type: 'info',
        message: `Template "${title}" telah dihapus.`,
      });
    } catch (err) {
      setNotification({
        type: 'error',
        message: err.message || 'Gagal menghapus template.',
      });
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Notifications */}
      {notification.message && (
        <div
          className={`p-3.5 rounded-xl text-xs flex items-center justify-between border transition-all ${
            notification.type === 'error'
              ? 'bg-rose-500/10 border-rose-500/20 text-rose-300'
              : notification.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
              : 'bg-slate-800/80 border-slate-700/80 text-slate-300'
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
            className="p-1 rounded hover:bg-white/10 transition-colors ml-4"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Clean Header Bar */}
      <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
              Review Editor & Previewer
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
            Studio Variasi Ulasan Google Maps
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
            Rancang draf ulasan dengan gaya bahasa natural (Local Guide, Pelanggan, Foodie), sisipkan kata kunci spesifik, dan pratinjau kartu ulasan sebelum ditugaskan ke antrean.
          </p>
        </div>

        <button
          onClick={() => setSaveModalOpen(true)}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/80 flex items-center gap-2 transition-colors cursor-pointer self-start md:self-auto shrink-0 shadow-xs"
        >
          <Bookmark className="w-3.5 h-3.5" />
          <span>Simpan Preset</span>
        </button>
      </div>

      {/* Main Studio 2-Column Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols): Studio Configuration Form */}
        <div className="lg:col-span-5 space-y-5">
          <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-5 space-y-5 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Parameter Ulasan
              </span>
              <span className="text-[11px] text-slate-400 font-mono">Editor Panel</span>
            </div>

            {/* Target Business */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Target Listing Google Maps
              </label>
              {businesses.length > 0 ? (
                <select
                  value={selectedBizId}
                  onChange={(e) => handleSelectBusiness(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer"
                >
                  <option value="">-- Ketik Nama Bebas / Non-Listing --</option>
                  {businesses.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name} ({b.reviewed_count || 0} reviews)
                    </option>
                  ))}
                </select>
              ) : null}

              <input
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="Nama tempat di Google Maps"
                className="w-full mt-2 px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            {/* Category Pills */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Kategori Bisnis
              </label>
              <div className="grid grid-cols-3 gap-2">
                {categories.map((cat) => {
                  const Icon = cat.icon;
                  const isSelected = category === cat.name;
                  return (
                    <button
                      key={cat.name}
                      type="button"
                      onClick={() => handleApplyCategory(cat)}
                      className={`p-2 rounded-xl border text-left transition-colors cursor-pointer flex flex-col justify-between ${
                        isSelected
                          ? 'bg-slate-800 text-white border-slate-600 shadow-xs'
                          : 'bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 mb-1 ${isSelected ? 'text-emerald-400' : 'text-slate-500'}`} />
                      <span className="text-[11px] font-medium truncate">{cat.name}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Persona Selector */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Gaya Bahasa Pengulas (Persona)
              </label>
              <div className="space-y-1.5">
                {personas.map((p) => {
                  const isSelected = persona === p.id;
                  return (
                    <div
                      key={p.id}
                      onClick={() => setPersona(p.id)}
                      className={`p-3 rounded-xl border transition-colors cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? 'bg-slate-800/90 border-slate-600 text-white'
                          : 'bg-slate-950/50 border-slate-800/80 text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={`w-8 h-8 rounded-lg ${p.avatarColor} text-white flex items-center justify-center font-bold text-xs shrink-0`}>
                          {p.name.charAt(0)}
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-white truncate">{p.name}</p>
                          <p className="text-[11px] text-slate-400 truncate">{p.desc}</p>
                        </div>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-emerald-400 shrink-0 ml-2" />}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Star Rating & Language */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Rating Bintang</label>
                <div className="flex items-center gap-1 bg-slate-950 px-3 py-2 rounded-xl border border-slate-800">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => setStarRating(star)}
                      className={`p-0.5 transition-transform ${star <= starRating ? 'text-amber-400 scale-105' : 'text-slate-700'}`}
                    >
                      <Star className="w-4 h-4 fill-current" />
                    </button>
                  ))}
                  <span className="text-xs font-mono font-bold text-amber-400 ml-auto">{starRating}★</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Bahasa</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer"
                >
                  <option value="Indonesian">Bahasa Indonesia</option>
                  <option value="English">English</option>
                </select>
              </div>
            </div>

            {/* Keyword Injection */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Kata Kunci yang Disisipkan
              </label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="kopi enak, wifi kencang, pelayanan cepat"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
              <p className="text-[10px] text-slate-400 mt-1">Dipisahkan dengan koma. Kata kunci akan disisipkan secara mengalir dan natural.</p>
            </div>

            {/* Description / Context */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">
                Deskripsi / Catatan Tempat
              </label>
              <textarea
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Fasilitas, suasana, menu rekomendasi, atau nilai plus tempat..."
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            {/* 4 Star Organic Option */}
            <label className="flex items-center gap-2.5 text-xs text-slate-300 cursor-pointer p-2.5 rounded-xl bg-slate-950 border border-slate-800">
              <input
                type="checkbox"
                checked={includeMinorCritique}
                onChange={(e) => setIncludeMinorCritique(e.target.checked)}
                className="rounded text-emerald-600 focus:ring-emerald-500 h-4 w-4"
              />
              <div className="min-w-0">
                <span className="font-semibold block text-slate-200">Sertakan Varian 4★ Realistis</span>
                <span className="text-[10px] text-slate-400 block">Menghasilkan 1 opsi bintang 4 dengan pujian positif agar profil ulasan terlihat alami.</span>
              </div>
            </label>

            {/* Primary Action Button */}
            <button
              onClick={handleGenerateVariations}
              disabled={generating || !businessName.trim()}
              className="w-full py-3 rounded-xl font-semibold text-xs bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center gap-2 shadow-xs disabled:opacity-50 cursor-pointer transition-colors"
            >
              {generating ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Membuat Draf Ulasan...</span>
                </>
              ) : (
                <>
                  <MessageSquare className="w-4 h-4" />
                  <span>Buat 3 Variasi Ulasan</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column (7 cols): Google Maps Card Previews & Preset Library */}
        <div className="lg:col-span-7 space-y-6">
          {/* Section: Google Maps Realistic Previews */}
          <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div>
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                  Pratinjau Ulasan Google Maps
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5 font-medium">
                  Tampilan nyata kartu ulasan sebagaimana terlihat oleh publik di Google Maps.
                </p>
              </div>
              <span className="text-xs font-mono text-slate-400">
                {variations.length} draf siap
              </span>
            </div>

            {variations.length === 0 ? (
              <div className="p-12 text-center bg-slate-950/40 rounded-xl border border-slate-800/60 flex flex-col items-center justify-center space-y-3">
                <div className="p-3 rounded-xl bg-slate-900 text-slate-400 border border-slate-800">
                  <MessageSquare className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-200">Belum Ada Draf Ulasan</p>
                  <p className="text-xs text-slate-400 max-w-sm mt-1">
                    Isi nama bisnis di panel kiri dan klik "Buat 3 Variasi Ulasan" untuk menghasilkan draf ulasan Google Maps.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {variations.map((v, i) => {
                  const mock = mockReviewerNames[i % mockReviewerNames.length];
                  return (
                    <div
                      key={v.id}
                      className="p-5 rounded-2xl bg-[#090d14] border border-slate-800 hover:border-slate-700 transition-colors space-y-3 font-sans"
                    >
                      {/* Realistic Google Maps Review Header */}
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-slate-800 text-slate-200 border border-slate-700 flex items-center justify-center font-bold text-sm">
                            {mock.name.charAt(0)}
                          </div>
                          <div>
                            <p className="text-xs font-bold text-white leading-tight">
                              {mock.name}
                            </p>
                            <p className="text-[11px] text-slate-400 mt-0.5">
                              {mock.meta}
                            </p>
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-1.5 shrink-0">
                          <button
                            onClick={() => handleCopy(v.id, v.text)}
                            className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-300 bg-slate-850 hover:bg-slate-800 border border-slate-700/60 transition-colors flex items-center gap-1 cursor-pointer"
                            title="Salin teks ulasan"
                          >
                            {copiedId === v.id ? (
                              <>
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                                <span className="text-emerald-400 text-[11px]">Tersalin</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5 text-slate-400" />
                                <span className="text-[11px]">Salin</span>
                              </>
                            )}
                          </button>

                          <button
                            onClick={() => handleOpenPushModal(v)}
                            className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-500 transition-colors flex items-center gap-1.5 cursor-pointer shadow-xs"
                          >
                            <Send className="w-3 h-3" />
                            <span>Tugaskan</span>
                          </button>
                        </div>
                      </div>

                      {/* Stars & Timestamp */}
                      <div className="flex items-center gap-1.5">
                        <div className="flex items-center gap-0.5 text-amber-400">
                          {[...Array(v.star_rating)].map((_, idx) => (
                            <Star key={idx} className="w-3.5 h-3.5 fill-current" />
                          ))}
                        </div>
                        <span className="text-[11px] text-slate-500 font-medium">Baru saja</span>
                      </div>

                      {/* Review Text */}
                      <p className="text-xs sm:text-sm text-slate-200 leading-relaxed pt-1">
                        {v.text}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Section: Preset Library */}
          <div className="bg-[#0f1420] border border-slate-800/80 rounded-2xl p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div>
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
                  Pustaka Preset Template
                </span>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Preset konfigurasi yang tersimpan di database lokal SQLite.
                </p>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {templates.length} preset
              </span>
            </div>

            {loadingTemplates ? (
              <div className="p-6 text-center text-xs text-slate-400 font-mono">
                Memuat preset...
              </div>
            ) : templates.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                Belum ada preset tersimpan.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1 no-scrollbar">
                {templates.map((tpl) => (
                  <div
                    key={tpl.id}
                    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition-colors flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-900 text-slate-300 border border-slate-800">
                          {tpl.category}
                        </span>
                        <button
                          onClick={() => handleDeleteTemplate(tpl.id, tpl.title)}
                          className="text-slate-500 hover:text-rose-400 p-1 rounded hover:bg-rose-500/10 transition-colors"
                          title="Hapus preset"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      <h4 className="text-xs font-bold text-white mt-2">
                        {tpl.title}
                      </h4>
                      <p className="text-[11px] text-slate-400 line-clamp-2 mt-1">
                        {tpl.prompt_template}
                      </p>
                    </div>

                    <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between">
                      <span className="text-[10px] text-amber-400 font-bold flex items-center gap-1">
                        <Star className="w-3 h-3 fill-current" />
                        <span>{tpl.star_rating}★</span>
                      </span>

                      <button
                        onClick={() => handleApplyTemplate(tpl)}
                        className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition-colors cursor-pointer"
                      >
                        <span>Terapkan</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal: Push Review to Queue */}
      {pushModal.open && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#0f1420] border border-slate-800 rounded-3xl p-6 w-full max-w-lg shadow-2xl relative">
            <button
              onClick={() => setPushModal({ open: false, text: '', star: 5, persona: '' })}
              className="absolute right-5 top-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>

            <h3 className="font-bold text-base text-white mb-1">Tugaskan Ulasan ke Antrean</h3>
            <p className="text-xs text-slate-400 mb-4">
              Ulasan ini akan disimpan ke antrean pending dan diproses secara otomatis oleh worker.
            </p>

            <form onSubmit={handlePushReview} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Target Listing Bisnis</label>
                <select
                  required
                  value={pushBizId}
                  onChange={(e) => setPushBizId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer"
                >
                  {businesses.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Akun Pengulas (Gmail)</label>
                <select
                  value={pushEmailId}
                  onChange={(e) => setPushEmailId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500 cursor-pointer"
                >
                  <option value="">-- Rotasi Otomatis dari Pool Akun Aktif --</option>
                  {emails
                    .filter((e) => !e.flagged)
                    .map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.email}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Teks Ulasan</label>
                <textarea
                  rows={4}
                  value={pushModal.text}
                  onChange={(e) => setPushModal({ ...pushModal, text: e.target.value })}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setPushModal({ open: false, text: '', star: 5, persona: '' })}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={submittingPush}
                  className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {submittingPush ? 'Menugaskan...' : 'Tugaskan Sekarang'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Save Template */}
      {saveModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-[#0f1420] border border-slate-800 rounded-3xl p-6 w-full max-w-md shadow-2xl relative">
            <button
              onClick={() => setSaveModalOpen(false)}
              className="absolute right-5 top-5 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>

            <h3 className="font-bold text-base text-white mb-1">Simpan Preset Template</h3>
            <p className="text-xs text-slate-400 mb-4">
              Simpan parameter formulir saat ini untuk digunakan kembali pada bisnis lain.
            </p>

            <form onSubmit={handleSaveTemplate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5">Nama Preset</label>
                <input
                  type="text"
                  required
                  value={newTemplateTitle}
                  onChange={(e) => setNewTemplateTitle(e.target.value)}
                  placeholder="misal: Kafe & Resto Modern"
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-[11px] space-y-1 text-slate-400">
                <p><strong className="text-slate-300">Kategori:</strong> {category}</p>
                <p><strong className="text-slate-300">Gaya:</strong> {persona} ({starRating}★)</p>
                <p className="truncate"><strong className="text-slate-300">Keywords:</strong> {keywords || '-'}</p>
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setSaveModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white"
                >
                  Batal
                </button>
                <button
                  type="submit"
                  disabled={savingTemplate}
                  className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {savingTemplate ? 'Menyimpan...' : 'Simpan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
