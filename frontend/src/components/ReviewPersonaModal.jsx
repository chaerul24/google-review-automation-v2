import React, { useState } from 'react';
import {
  Sparkles,
  Star,
  Copy,
  Check,
  X,
  Bot,
  UserCheck,
  RefreshCw,
  Globe,
  MessageSquare,
  Award,
} from 'lucide-react';
import { api } from '../api/client';

export default function ReviewPersonaModal({ isOpen, onClose, defaultBusinessName = '', defaultDescription = '' }) {
  const [businessName, setBusinessName] = useState(defaultBusinessName || 'Coffee Shop Sejahtera');
  const [description, setDescription] = useState(defaultDescription || 'Kafe kekinian dengan kopi nusantara, tempat nyaman untuk kerja, wi-fi kencang.');
  const [persona, setPersona] = useState('local_guide');
  const [starRating, setStarRating] = useState(5);
  const [language, setLanguage] = useState('Indonesian');
  const [generatedText, setGeneratedText] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const personas = [
    { id: 'local_guide', name: 'Google Local Guide Level 7', desc: 'Detail, rekomendasi fasilitas, tips parkir & atmosfer', icon: Award, color: 'text-amber-400' },
    { id: 'casual', name: 'Pelanggan Kasual & Santai', desc: 'Bahasa santai, to the point, pujian natural', icon: UserCheck, color: 'text-emerald-400' },
    { id: 'family', name: 'Keluarga & Rombongan', desc: 'Fokus kebersamaan, keramahan staf, kenyamanan tempat', icon: Bot, color: 'text-indigo-400' },
    { id: 'foodie', name: 'Foodie & Penikmat Rasa', desc: 'Ulasan mendalam rasa, konsistensi penyajian & value', icon: Sparkles, color: 'text-teal-400' },
    { id: 'tourist', name: 'Tourist / Traveler (English)', desc: 'International tone, welcoming hospitality, accessibility', icon: Globe, color: 'text-purple-400' },
  ];

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await api.generatePreview({
        business_name: businessName,
        description: description,
        star_rating: starRating,
        persona: persona,
        language: persona === 'tourist' ? 'English' : language,
        review_style: starRating >= 4 ? 'baik' : 'buruk',
      });
      if (res && res.text) {
        setGeneratedText(res.text);
      }
    } catch (err) {
      console.error('Failed to generate preview:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!generatedText) return;
    navigator.clipboard.writeText(generatedText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#0f1420] border border-slate-800 rounded-3xl p-6 w-full max-w-2xl shadow-2xl relative animate-in fade-in zoom-in-95 max-h-[90vh] overflow-y-auto no-scrollbar">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-300">
              <MessageSquare className="w-4 h-4 text-emerald-400" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Uji Variasi Ulasan Google Maps</h3>
              <p className="text-xs text-slate-400">Simulasikan kalimat ulasan natural dengan berbagai gaya persona pengulas.</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Form */}
        <div className="space-y-4 pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Nama Bisnis Target</label>
              <input
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="Nama tempat / bisnis..."
                className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Rating Bintang Ulasan</label>
              <div className="flex items-center gap-2">
                {[5, 4, 3, 2, 1].map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setStarRating(s)}
                    className={`flex-1 py-1.5 rounded-xl border text-xs font-bold flex items-center justify-center gap-1 transition-all ${
                      starRating === s
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                    }`}
                  >
                    <span>{s}</span>
                    <Star className="w-3 h-3 fill-current text-amber-400" />
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Konteks / Keunggulan Bisnis</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Contoh: Tempat nyaman, kopi enak, parkir mobil luas..."
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white focus:outline-none focus:border-emerald-500"
            />
          </div>

          {/* Persona Selection */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-2">Pilih Karakter Persona Reviewer</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {personas.map((p) => {
                const Icon = p.icon;
                const active = persona === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => setPersona(p.id)}
                    className={`p-3 rounded-2xl border text-left transition-all flex items-start gap-2.5 cursor-pointer ${
                      active
                        ? 'bg-emerald-500/10 border-emerald-500/40 shadow-sm shadow-emerald-500/10'
                        : 'bg-slate-950/70 border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${p.color}`} />
                    <div className="min-w-0">
                      <span className={`text-xs font-bold block truncate ${active ? 'text-emerald-300' : 'text-slate-200'}`}>
                        {p.name}
                      </span>
                      <span className="text-[10px] text-slate-400 line-clamp-1">{p.desc}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Generate Action Button */}
          <button
            type="button"
            onClick={handleGenerate}
            disabled={loading}
            className="w-full py-2.5 rounded-xl font-semibold text-xs bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center gap-2 shadow-xs transition-colors cursor-pointer disabled:opacity-50"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin text-white" />
            ) : (
              <MessageSquare className="w-4 h-4" />
            )}
            <span>Buat Draf Ulasan</span>
          </button>

          {/* Generated Result Card (Google Maps Mockup) */}
          {generatedText && (
            <div className="mt-4 p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2.5 shadow-xs animate-in fade-in">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-slate-800 text-slate-200 border border-slate-700 flex items-center justify-center font-bold text-xs">
                    R
                  </div>
                  <div>
                    <span className="text-xs font-bold text-white block">Reviewer Google Maps</span>
                    <div className="flex items-center gap-1 text-amber-400 text-xs">
                      {[...Array(starRating)].map((_, i) => (
                        <Star key={i} className="w-3 h-3 fill-current" />
                      ))}
                      <span className="text-[10px] text-slate-400 font-mono ml-1.5">• Baru saja</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleCopy}
                  className="px-2.5 py-1 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-750 text-slate-300 hover:text-white text-[11px] font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
                  <span>{copied ? 'Tersalin' : 'Salin'}</span>
                </button>
              </div>

              <p className="text-xs text-slate-200 leading-relaxed pt-1 border-t border-slate-850">
                "{generatedText}"
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
