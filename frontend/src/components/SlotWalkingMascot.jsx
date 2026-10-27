import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
  RotateCw,
  Maximize2,
  X,
  Bot
} from 'lucide-react';

const SLOT_MESSAGES = {
  1: 'Grok Bot mengawal Layar 01 (:99) di pojok kanan.',
  2: 'Layar 02 (:100) sesi browser mandiri aktif diawasi Grok Bot.',
  3: 'Layar 03 (:101) siap mengeksekusi ulasan bisnis secara otomatis.',
  4: 'Layar 04 (:102) display virtual stabil tanpa hambatan sesi.',
  5: 'Layar 05 (:103) isolasi cookie aman dan terpantau real-time.',
  6: 'Layar 06 (:104) kapasitas maksimal 6 layar paralel beroperasi penuh!'
};

export default function SlotWalkingMascot({
  slot,
  onMaximize,
  onRefresh,
  isLiveActive,
  isTaskRunning,
  isSleeping = false,
  onWake,
}) {
  const botRef = useRef(null);
  const [popoverPos, setPopoverPos] = useState(null);

  // Expression & Eye States (Grok's Rounded Square Eyes)
  const [isBlinking, setIsBlinking] = useState(false);
  const [isWinking, setIsWinking] = useState(false);
  const [isJumping, setIsJumping] = useState(false);
  const [isSpeechOpen, setIsSpeechOpen] = useState(false);
  const [scanOffset, setScanOffset] = useState(0);

  // Calculate viewport coordinates for popover portal outside the overflow:hidden container
  const calcPopoverPosition = useCallback(() => {
    const el = botRef.current;
    if (!el) {
      return { placement: 'top', bottom: 60, right: 16 };
    }
    const rect = el.getBoundingClientRect();
    const spaceAbove = rect.top;
    const spaceBelow = window.innerHeight - rect.bottom;

    // Anchor near mascot right, keeping safely within viewport
    const right = Math.max(12, Math.min(window.innerWidth - 290, window.innerWidth - rect.right - 4));

    if (spaceAbove >= 180 || spaceAbove >= spaceBelow) {
      const bottom = Math.max(12, window.innerHeight - rect.top + 8);
      return { placement: 'top', bottom, right };
    } else {
      const top = Math.max(12, rect.bottom + 8);
      return { placement: 'bottom', top, right };
    }
  }, []);

  // 1. Autonomous Natural Blinking for Rounded Square Eyes
  useEffect(() => {
    let blinkTimer;
    const scheduleBlink = () => {
      const delay = Math.random() * 2800 + 2000;
      blinkTimer = setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => {
          setIsBlinking(false);
          // 20% chance of quick double blink
          if (Math.random() > 0.8) {
            setTimeout(() => {
              setIsBlinking(true);
              setTimeout(() => {
                setIsBlinking(false);
                scheduleBlink();
              }, 80);
            }, 100);
          } else {
            scheduleBlink();
          }
        }, 120);
      }, delay);
    };

    scheduleBlink();
    return () => clearTimeout(blinkTimer);
  }, []);

  // 2. Subtle Eye Scanning when Bot / Screen is actively running
  useEffect(() => {
    if (!isLiveActive) return;
    const scanSteps = [-1.5, 0, 1.5, 0];
    let step = 0;
    const interval = setInterval(() => {
      step = (step + 1) % scanSteps.length;
      setScanOffset(scanSteps[step]);
    }, 700);
    return () => clearInterval(interval);
  }, [isLiveActive]);

  // Keep popover aligned if window resizes or scrolls while open
  useEffect(() => {
    if (!isSpeechOpen) return;
    const handleReposition = () => {
      setPopoverPos(calcPopoverPosition());
    };
    window.addEventListener('resize', handleReposition);
    window.addEventListener('scroll', handleReposition, true);
    return () => {
      window.removeEventListener('resize', handleReposition);
      window.removeEventListener('scroll', handleReposition, true);
    };
  }, [isSpeechOpen, calcPopoverPosition]);

  // 3. Click interaction: Spring jump, wake VM if sleeping, wink & open Portal popover
  const handleClick = (e) => {
    if (e && e.stopPropagation) e.stopPropagation();
    setIsJumping(true);
    setTimeout(() => setIsJumping(false), 500);

    if (isSleeping) {
      if (onWake) onWake();
      return;
    }

    setIsWinking(true);
    setTimeout(() => setIsWinking(false), 500);

    if (!isSpeechOpen) {
      setPopoverPos(calcPopoverPosition());
      setIsSpeechOpen(true);
    } else {
      setIsSpeechOpen(false);
    }
  };

  const slotMsg = SLOT_MESSAGES[slot.slotNumber] || `Grok Bot mengawal Layar 0${slot.slotNumber} (${slot.display})`;
  const currentPos = popoverPos || calcPopoverPosition();

  // Status layar sedang proses
  const isProcessing = Boolean(
    slot?.isProcessing ||
    (isTaskRunning && !slot?.isCompleted && !slot?.isFailed) ||
    (isLiveActive && isTaskRunning) ||
    (slot?.realStatus && /proses|buka|login|isi|kirim|jalan|running|antrean/i.test(slot.realStatus))
  );

  return (
    <div
      className="absolute bottom-1.5 right-2 z-30 select-none pointer-events-auto transition-transform flex flex-col items-end"
    >
      {/* ========================================================================= */}
      {/* 1. SLOT-SPECIFIC SPEECH BUBBLE (PORTAL TO DOCUMENT.BODY - TIDAK KETIMPA)  */}
      {/* ========================================================================= */}
      {isSpeechOpen && typeof document !== 'undefined' && createPortal(
        <div
          data-slot-portal={`slot-${slot.slotNumber}`}
          className="fixed inset-0 z-50 pointer-events-auto bg-black/10 backdrop-blur-[0.5px]"
          onClick={() => setIsSpeechOpen(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'fixed',
              ...(currentPos.placement === 'top'
                ? { bottom: `${currentPos.bottom}px` }
                : { top: `${currentPos.top}px` }),
              right: `${currentPos.right}px`
            }}
            className="w-[260px] sm:w-[280px] max-w-[calc(100vw-24px)] bg-slate-950/95 backdrop-blur-md rounded-xl border border-cyan-400 shadow-[0_12px_35px_rgba(0,0,0,0.85),0_0_15px_rgba(34,211,238,0.35)] p-2.5 sm:p-3 text-[11px] text-white animate-in fade-in zoom-in-95 duration-150 pointer-events-auto"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-1.5 mb-2 border-b border-slate-800">
              <div className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${slot.theme?.dot || 'bg-cyan-400'} animate-pulse`}></span>
                <span className="font-bold text-cyan-300 text-[10px] uppercase tracking-wider flex items-center gap-1">
                  <Bot className="w-3.5 h-3.5 text-cyan-400" />
                  Grok Bot · Layar 0{slot.slotNumber}
                </span>
              </div>
              <button
                onClick={() => setIsSpeechOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer transition"
                aria-label="Tutup"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Speech Message */}
            <p className="text-slate-200 text-[11px] leading-relaxed mb-2 font-medium">
              {slotMsg}
            </p>

            {/* Real Process Status Badge inside Popover */}
            {isTaskRunning && (
              <div className="flex items-center justify-between text-[9px] bg-slate-900/90 px-2 py-1 rounded border border-cyan-500/30 mb-2">
                <span className="text-emerald-400 font-bold flex items-center gap-1 truncate max-w-[190px]">
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    slot.isCompleted ? 'bg-cyan-400' : slot.isFailed ? 'bg-rose-400' : 'bg-emerald-400 animate-ping'
                  }`}></span>
                  <span className="truncate">{slot.realStatus || slot.status || 'Memproses task...'}</span>
                </span>
                <span className="text-cyan-400 font-mono font-bold shrink-0">{slot.realProgress ?? 0}%</span>
              </div>
            )}

            {/* Slot Metadata Badge */}
            <div className="flex items-center justify-between text-[9.5px] font-mono bg-slate-900/90 px-2 py-1 rounded border border-slate-800 mb-2.5">
              <span className="text-slate-400 truncate max-w-[150px]">{slot.account?.email || 'Standby'}</span>
              <span className="text-cyan-400 font-bold shrink-0">{slot.display}</span>
            </div>

            {/* Slot Quick Action Buttons */}
            <div className="grid grid-cols-2 gap-1.5 pt-1.5 border-t border-slate-800">
              <button
                onClick={() => {
                  if (onMaximize) onMaximize();
                  setIsSpeechOpen(false);
                }}
                className="px-2 py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 bg-[#2563EB] hover:bg-blue-600 text-white transition cursor-pointer shadow-sm"
              >
                <Maximize2 className="w-3 h-3" />
                <span>Fokus Layar</span>
              </button>

              <button
                onClick={() => {
                  if (onRefresh) onRefresh();
                  setIsSpeechOpen(false);
                }}
                className="px-2 py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 transition cursor-pointer border border-slate-700/60"
              >
                <RotateCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>
            </div>

            {/* Triangle pointer pointing down or up to the bot */}
            {currentPos.placement === 'top' ? (
              <div
                className="absolute -bottom-1.5 right-5 w-3 h-3 bg-slate-950 border-r border-b border-cyan-400 transform rotate-45 pointer-events-none"
              ></div>
            ) : (
              <div
                className="absolute -top-1.5 right-5 w-3 h-3 bg-slate-950 border-l border-t border-cyan-400 transform rotate-45 pointer-events-none"
              ></div>
            )}
          </div>
        </div>,
        document.body
      )}

      {/* ========================================================================= */}
      {/* 2. GROK BOT WITH DYNAMIC FACE (DOCKED AT BOTTOM RIGHT)                   */}
      {/* - Saat idle/standby: Mata rounded square berkedip natural                */}
      {/* - Saat sedang proses: Muka berubah menjadi "..." loading animation       */}
      {/* ========================================================================= */}
      <div
        ref={botRef}
        role="button"
        tabIndex={0}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick(e);
          }
        }}
        className={`relative group cursor-pointer flex flex-col items-center transition-transform ${
          isJumping ? '-translate-y-2 scale-110' : 'hover:scale-105 active:scale-95'
        }`}
        title={`Grok Bot Layar 0${slot.slotNumber} (${slot.display}) - ${isProcessing ? 'Sedang Proses (...)' : 'Standby'}`}
      >
        {/* Soft ground shadow */}
        <div
          className={`absolute -bottom-0.5 left-1/2 -translate-x-1/2 rounded-full bg-black/70 blur-[1px] transition-all ${
            isJumping ? 'w-5 h-0.5 opacity-30' : 'w-7 h-1 opacity-80'
          }`}
        ></div>

        {/* Sleeping mini-pill badge above mascot */}
        {isSleeping && (
          <div
            onClick={(e) => {
              e.stopPropagation();
              if (onWake) onWake();
            }}
            className="mb-1 px-1.5 py-0.5 rounded-md bg-slate-950/95 border border-amber-400/80 shadow-[0_0_8px_rgba(251,191,36,0.5)] text-[9px] font-bold text-amber-300 flex items-center gap-1 cursor-pointer hover:scale-105 transition-transform"
            title="Klik untuk menyalakan Windows VM"
          >
            <span>💤</span>
            <span className="whitespace-nowrap font-mono">Sleep (Klik)</span>
          </div>
        )}

        {/* Squircle Face Chassis */}
        <div
          className={`w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-[#0b0f17] border-2 ${
            isSleeping
              ? 'border-amber-400/90 shadow-[0_0_12px_rgba(251,191,36,0.6)] animate-pulse'
              : 'border-slate-700/90 group-hover:border-cyan-400/90 shadow-lg'
          } flex items-center justify-center relative overflow-hidden transition-all duration-200 cursor-pointer`}
        >
          {/* Glass glare overlay */}
          <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-white/15 pointer-events-none"></div>

          {/* DYNAMIC FACE: SLEEPING (Zzz), "..." LOADING DOTS, OR ROUNDED SQUARE EYES */}
          {isSleeping ? (
            /* ── PEACEFUL SLEEPING FACE WITH FLOATING Zzz ── */
            <div className="relative flex flex-col items-center justify-center">
              {/* Floating animated Zzz drifting up */}
              <div className="absolute -top-3.5 -right-1 pointer-events-none flex items-center font-mono font-black text-amber-300 drop-shadow-[0_0_6px_rgba(251,191,36,0.9)] select-none animate-pulse">
                <span className="text-[9px] animate-bounce" style={{ animationDuration: '1.2s' }}>z</span>
                <span className="text-[7.5px]" style={{ animationDuration: '1.5s' }}>Z</span>
                <span className="text-[6.5px]">z</span>
              </div>

              {/* Peaceful sleeping closed eyelids (- -) */}
              <div className="flex items-center gap-1.5 transition-all">
                <div className="w-2.5 h-[2.5px] rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.95)]"></div>
                <div className="w-2.5 h-[2.5px] rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.95)]"></div>
              </div>
            </div>
          ) : isProcessing ? (
            /* ── ANIMATED "..." LOADING FACE (SEDANG PROSES) ── */
            <div className="flex items-center justify-center gap-1 px-1">
              <span
                className="w-1.5 h-1.5 rounded-full bg-cyan-300 shadow-[0_0_8px_rgba(103,232,249,0.95)] animate-bounce"
                style={{ animationDelay: '0ms', animationDuration: '0.8s' }}
              />
              <span
                className="w-1.5 h-1.5 rounded-full bg-cyan-300 shadow-[0_0_8px_rgba(103,232,249,0.95)] animate-bounce"
                style={{ animationDelay: '160ms', animationDuration: '0.8s' }}
              />
              <span
                className="w-1.5 h-1.5 rounded-full bg-cyan-300 shadow-[0_0_8px_rgba(103,232,249,0.95)] animate-bounce"
                style={{ animationDelay: '320ms', animationDuration: '0.8s' }}
              />
            </div>
          ) : (
            /* ── THE ICONIC ROUNDED SQUARE EYES (IDLE / STANDBY) ── */
            <div
              className="flex items-center gap-1.5 transition-transform duration-150 ease-out"
              style={{
                transform: `translateX(${scanOffset}px)`
              }}
            >
              {/* Left Rounded Square Eye */}
              <div
                data-eye="left"
                className={`w-2 h-2.5 sm:w-2.5 sm:h-3 rounded-[32%] transition-all duration-120 ${
                  isBlinking || isWinking
                    ? 'scale-y-[0.1] opacity-60'
                    : isLiveActive
                    ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.95)]'
                    : 'bg-cyan-300 shadow-[0_0_8px_rgba(103,232,249,0.9)]'
                }`}
              />

              {/* Right Rounded Square Eye */}
              <div
                data-eye="right"
                className={`w-2 h-2.5 sm:w-2.5 sm:h-3 rounded-[32%] transition-all duration-120 ${
                  isBlinking
                    ? 'scale-y-[0.1] opacity-60'
                    : isLiveActive
                    ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.95)]'
                    : 'bg-cyan-300 shadow-[0_0_8px_rgba(103,232,249,0.9)]'
                }`}
              />
            </div>
          )}

          {/* Running LED beacon */}
          {isLiveActive && (
            <span className="absolute bottom-0.5 w-1 h-1 rounded-full bg-emerald-400 animate-ping"></span>
          )}
        </div>

        {/* Stable resting mini feet */}
        <div className="flex items-center justify-center gap-2 -mt-0.5">
          <div className="w-1.5 h-1 bg-slate-600 rounded-xs"></div>
          <div className="w-1.5 h-1 bg-slate-600 rounded-xs"></div>
        </div>

        {/* Slot Number Pill */}
        <span className="absolute -top-1 -right-1 px-1 py-0.2 rounded-full text-[8px] font-mono font-bold bg-[#0891B2] text-white border border-black/40 shadow-xs">
          0{slot.slotNumber}
        </span>
      </div>
    </div>
  );
}
