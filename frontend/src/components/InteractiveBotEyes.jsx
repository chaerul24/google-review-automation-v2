import React, { useState, useEffect, useRef } from 'react';

/**
 * Interactive Rounded Square Eyes (Inspired by Benji Taylor's Grok Bot)
 * 
 * Expressive Bot Companion with:
 * - Dynamic speech bubble above head ("aku proses ya", "membuka google", "login berhasil", "waduh login gagal", "membuka map", "review map", "komentar map", "sudah selesai")
 * - Animated question mark "?" badge for confused/error states
 * - Lively "busy working" eye movement during worker execution
 * - Real-time gaze tracking following the cursor
 * - Autonomous blinking & interactive click reaction
 */
export default function InteractiveBotEyes({
  size = 'md', // 'sm' (36px), 'md' (46px), 'lg' (58px)
  isRunning = false,
  speechText = '',
  showQuestion = false,
  mood = 'idle', // 'idle' | 'working' | 'happy' | 'confused' | 'focus' | 'celebrate'
}) {
  const containerRef = useRef(null);
  const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });
  const [isBlinking, setIsBlinking] = useState(false);
  const [isWinking, setIsWinking] = useState(false);
  const [workCycle, setWorkCycle] = useState(0);

  // 1. Mouse Gaze Tracking (Eyes follow cursor when idle/hovered)
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const deltaX = e.clientX - centerX;
      const deltaY = e.clientY - centerY;
      const distance = Math.hypot(deltaX, deltaY);

      // Max offset in pixels
      const maxOffset = size === 'lg' ? 6 : size === 'sm' ? 2.5 : 4;
      const clampDist = Math.min(distance, 400) / 400;

      const angle = Math.atan2(deltaY, deltaX);
      const offsetX = Math.cos(angle) * maxOffset * clampDist;
      const offsetY = Math.sin(angle) * maxOffset * clampDist;

      setEyeOffset({ x: offsetX, y: offsetY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [size]);

  // 2. Active "Ngerjain Sesuatu" Working Animation Cycle
  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => {
      setWorkCycle((prev) => (prev + 1) % 6);
    }, 700);
    return () => clearInterval(interval);
  }, [isRunning]);

  // 3. Autonomous Natural Blinking
  useEffect(() => {
    let timeoutId;
    const triggerBlink = () => {
      setIsBlinking(true);
      setTimeout(() => {
        setIsBlinking(false);
        const nextInterval = Math.random() * 3200 + 2200;
        timeoutId = setTimeout(triggerBlink, nextInterval);
      }, 130);
    };

    timeoutId = setTimeout(triggerBlink, 2500);
    return () => clearTimeout(timeoutId);
  }, []);

  // 4. Click interaction: Playful wink
  const handleClick = () => {
    setIsWinking(true);
    setTimeout(() => {
      setIsWinking(false);
    }, 400);
  };

  // Dimensions based on size prop
  const sizeConfig = {
    sm: {
      box: 'w-9 h-9 rounded-xl',
      eye: 'w-2 h-2.5 rounded-[30%]',
      gap: 'gap-1.5',
    },
    md: {
      box: 'w-11 h-11 rounded-2xl',
      eye: 'w-2.5 h-3.5 rounded-[32%]',
      gap: 'gap-2',
    },
    lg: {
      box: 'w-14 h-14 rounded-2xl',
      eye: 'w-3.5 h-4.5 rounded-[34%]',
      gap: 'gap-2.5',
    },
  }[size] || {
    box: 'w-11 h-11 rounded-2xl',
    eye: 'w-2.5 h-3.5 rounded-[32%]',
    gap: 'gap-2',
  };

  // Determine eye translation: if working, combine gaze with scanning movement
  const getEyeTranslation = () => {
    if (isRunning) {
      const scanX = [-3, -1, 2, 3, 1, -2][workCycle] || 0;
      const scanY = [-1, 1, 0, 1, -1, 0][workCycle] || 0;
      return `translate(${eyeOffset.x * 0.4 + scanX}px, ${eyeOffset.y * 0.4 + scanY}px)`;
    }
    return `translate(${eyeOffset.x}px, ${eyeOffset.y}px)`;
  };

  // Eye styles & colors based on mood
  const getLeftEyeStyle = () => {
    if (mood === 'confused' || showQuestion) {
      return 'bg-amber-400 shadow-[0_0_10px_rgba(251,191,36,0.9)] scale-y-110';
    }
    if (mood === 'happy' || mood === 'celebrate') {
      return 'bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.9)] scale-y-75 rounded-t-full';
    }
    if (isRunning) {
      return 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.95)]';
    }
    return 'bg-slate-100 shadow-[0_0_8px_rgba(241,245,249,0.5)]';
  };

  const getRightEyeStyle = () => {
    if (mood === 'confused' || showQuestion) {
      // Right eye squints in confusion / eyebrow raised effect
      return 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.9)] scale-y-[0.35] translate-y-0.5';
    }
    if (mood === 'happy' || mood === 'celebrate') {
      return 'bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.9)] scale-y-75 rounded-t-full';
    }
    if (isRunning) {
      return 'bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.95)]';
    }
    return 'bg-slate-100 shadow-[0_0_8px_rgba(241,245,249,0.5)]';
  };

  // Display text in the speech bubble
  const activeSpeech = speechText || (isRunning ? 'aku proses ya' : 'siap bertugas!');
  const isQuestionActive = showQuestion || mood === 'confused';

  return (
    <div className="relative flex flex-col items-center select-none" ref={containerRef}>
      {/* ── 1. Text Speech Bubble di Atas Bot ── */}
      <div className="mb-2 relative flex flex-col items-center animate-in fade-in slide-in-from-bottom-1 duration-200">
        <div data-bot-speech="true" className={`px-2.5 py-1 rounded-xl text-[11px] font-mono font-bold shadow-xl border flex items-center gap-1.5 whitespace-nowrap transition-colors ${
          isQuestionActive
            ? 'bg-amber-950/90 text-amber-300 border-amber-500/40 shadow-amber-950/50'
            : mood === 'happy' || mood === 'celebrate'
            ? 'bg-emerald-950/90 text-emerald-300 border-emerald-500/40 shadow-emerald-950/50'
            : isRunning
            ? 'bg-slate-900/95 text-emerald-400 border-emerald-500/30 shadow-emerald-950/30'
            : 'bg-slate-900/90 text-slate-200 border-slate-700/80'
        }`}>
          <span>{activeSpeech}</span>
        </div>
        {/* Speech Bubble Arrow Indicator */}
        <div className={`w-2 h-2 rotate-45 -mt-1 border-r border-b ${
          isQuestionActive
            ? 'bg-amber-950/90 border-amber-500/40'
            : mood === 'happy' || mood === 'celebrate'
            ? 'bg-emerald-950/90 border-emerald-500/40'
            : isRunning
            ? 'bg-slate-900/95 border-emerald-500/30'
            : 'bg-slate-900/90 border-slate-700/80'
        }`}></div>
      </div>

      {/* ── 2. Bot Face Body & Eyes ── */}
      <div className="relative">
        {/* Floating Animated Question Mark "?" */}
        {isQuestionActive && (
          <div className="absolute -top-3 -right-2 z-20 animate-bounce">
            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-400 text-slate-950 font-black text-xs font-mono shadow-lg shadow-amber-400/50 rotate-12">
              ?
            </span>
          </div>
        )}

        {/* Bot Face Squircle */}
        <button
          type="button"
          onClick={handleClick}
          className={`${sizeConfig.box} bg-[#0c1017] border-2 transition-all flex items-center justify-center cursor-pointer shadow-xl relative overflow-hidden group active:scale-95 ${
            isQuestionActive
              ? 'border-amber-500/60 shadow-amber-500/20'
              : isRunning
              ? 'border-emerald-500/70 shadow-emerald-500/30 ring-2 ring-emerald-500/20'
              : 'border-slate-700/80 hover:border-slate-500'
          }`}
          title="Grok Bot Companion"
        >
          {/* Subtle Screen Reflection */}
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-white/10 pointer-events-none"></div>

          {/* Eyes Container (Tracks Mouse & Scans when working) */}
          <div
            className={`flex items-center ${sizeConfig.gap} transition-transform duration-100 ease-out`}
            style={{
              transform: getEyeTranslation(),
            }}
          >
            {/* Left Eye */}
            <div
              className={`${sizeConfig.eye} ${getLeftEyeStyle()} transition-all duration-150 ${
                isBlinking || isWinking
                  ? 'scale-y-[0.1] opacity-70'
                  : ''
              }`}
            ></div>

            {/* Right Eye */}
            <div
              className={`${sizeConfig.eye} ${getRightEyeStyle()} transition-all duration-150 ${
                isBlinking
                  ? 'scale-y-[0.1] opacity-70'
                  : ''
              }`}
            ></div>
          </div>

          {/* Running Status Dot */}
          {isRunning && (
            <span className="absolute bottom-1 w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
          )}
        </button>
      </div>
    </div>
  );
}

/**
 * Intelligent Log Parser to derive the exact stage text for the Bot Companion
 */
export function parseBotStageFromLogs(logs, isRunning) {
  if (!isRunning) {
    if (logs && logs.length > 0) {
      const last = logs[logs.length - 1];
      const text = (last.message || '').toLowerCase();
      if (text.includes('selesai memproses') || text.includes('selesai') || text.includes('sukses') || text.includes('berhasil dikirim')) {
        return { speech: 'sudah selesai', mood: 'celebrate', showQuestion: false };
      }
      if (text.includes('tidak valid') || text.includes('gagal') || text.includes('needs_login') || text.includes('error')) {
        return { speech: 'waduh login gagal', mood: 'confused', showQuestion: true };
      }
    }
    return { speech: 'siap bertugas!', mood: 'idle', showQuestion: false };
  }

  // WHEN RUNNING: Never show 'siap bertugas!'
  if (!logs || logs.length === 0) {
    return { speech: 'aku proses ya', mood: 'working', showQuestion: false };
  }

  // Inspect the latest log messages
  const lastMsg = (logs[logs.length - 1].message || '').toLowerCase();

  // 1. Error / Login issues -> "waduh login gagal" with "?"
  if (
    lastMsg.includes('tidak valid') ||
    lastMsg.includes('needs_login') ||
    lastMsg.includes('gagal') ||
    lastMsg.includes('expired') ||
    lastMsg.includes('login prompt')
  ) {
    return { speech: 'waduh login gagal', mood: 'confused', showQuestion: true };
  }

  // 2. Selesai -> "sudah selesai"
  if (lastMsg.includes('selesai memproses') || lastMsg.includes('berhasil dikirim') || lastMsg.includes('worker selesai')) {
    return { speech: 'sudah selesai', mood: 'celebrate', showQuestion: false };
  }

  // 3. Inisialisasi awal -> "aku proses ya"
  if (
    lastMsg.includes('memulai worker') ||
    lastMsg.includes('memulai proses') ||
    lastMsg.includes('masuk ke antrean') ||
    lastMsg.includes('antrean') ||
    lastMsg.includes('countdown')
  ) {
    return { speech: 'aku proses ya', mood: 'working', showQuestion: false };
  }

  // 4. Membuka google -> "membuka google"
  if (lastMsg.includes('membuka browser') || lastMsg.includes('google.com') || lastMsg.includes('chromium')) {
    return { speech: 'membuka google', mood: 'working', showQuestion: false };
  }

  // 5. Login berhasil -> "login berhasil"
  if (lastMsg.includes('berhasil diverifikasi') || lastMsg.includes('sesi google aktif') || lastMsg.includes('sesi akun')) {
    return { speech: 'login berhasil', mood: 'happy', showQuestion: false };
  }

  // 6. Membuka map -> "membuka map"
  if (lastMsg.includes('halaman google maps') || lastMsg.includes('maps.google') || lastMsg.includes('membuka maps') || lastMsg.includes('maps listing')) {
    return { speech: 'membuka map', mood: 'working', showQuestion: false };
  }

  // 7. Review map -> "review map"
  if ((lastMsg.includes('memilih rating') || lastMsg.includes('rating review') || lastMsg.includes('bintang review') || lastMsg.includes('goog-reviews-write-widget') || lastMsg.includes('form review')) && !lastMsg.includes('memulai worker')) {
    return { speech: 'review map', mood: 'focus', showQuestion: false };
  }

  // 8. Komentar map -> "komentar map"
  if (lastMsg.includes('mengisi teks') || lastMsg.includes('menulis ulasan') || lastMsg.includes('komentar') || lastMsg.includes('teks ulasan') || lastMsg.includes('mengirim review')) {
    return { speech: 'komentar map', mood: 'working', showQuestion: false };
  }

  return { speech: 'aku proses ya', mood: 'working', showQuestion: false };

  return { speech: 'aku proses ya', mood: 'working', showQuestion: false };
}
