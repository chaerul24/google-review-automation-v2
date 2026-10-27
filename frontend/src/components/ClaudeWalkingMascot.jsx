import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  RotateCw,
  Search,
  Pause,
  Play,
  X,
  Layers,
  Activity,
  ChevronUp,
  Sliders,
  Move
} from 'lucide-react';

import claudeWalk1 from '../assets/claude_walk_1.png';
import claudeWalk2 from '../assets/claude_walk_2.png';
import claudeWalk3 from '../assets/claude_walk_3.png';
import claudeJump from '../assets/claude_jump.png';
import claudeInspect from '../assets/claude_mascot_inspect.png';
import claudeControl from '../assets/claude_mascot_control.png';
import claudeHero from '../assets/claude_mascot_hero.png';

const WALK_SPRITES = [claudeWalk1, claudeWalk2, claudeWalk3, claudeWalk2];

const CHATTER_PHRASES = [
  'Saya sedang berpatroli mengawasi seluruh layar paralel Anda! 🐾',
  'Display virtual Xvfb :99 hingga :104 berjalan terisolasi & optimal! 🛡️',
  'Tidak ada tabrakan cookie atau sesi pada slot yang aktif! 🍪',
  'Butuh sinkronisasi frame? Klik tombol Sinkronkan di bawah ini! 🔄',
  'Anda bisa men-drag saya ke mana saja di layar! 🚀',
  'Automasi Google Review berjalan mulus di bawah supervisi Claude AI! ✨'
];

export default function ClaudeWalkingMascot({
  accountCount = 3,
  workerStatus = { running: false },
  onSyncScreens,
  onOpenDiagnostic,
  onNavigateSlot
}) {
  // --- Walking & Movement State ---
  const [posX, setPosX] = useState(120);
  const [direction, setDirection] = useState(1); // 1: right, -1: left
  const [isWalking, setIsWalking] = useState(true);
  const [isInspecting, setIsInspecting] = useState(false);
  const [isJumping, setIsJumping] = useState(false);
  const [walkFrameIndex, setWalkFrameIndex] = useState(0);

  // --- Interaction & Speech State ---
  const [isSpeechOpen, setIsSpeechOpen] = useState(false);
  const [speechText, setSpeechText] = useState(
    `Halo! Saya Claude AI, sedang berpatroli memantau ${accountCount} layar paralel Anda!`
  );
  const [isMinimized, setIsMinimized] = useState(false);

  // --- Drag & Drop State ---
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef({ startX: 0, startPosX: 0, hasMoved: false });
  const mascotRef = useRef(null);

  // Synchronize speech when accountCount changes
  useEffect(() => {
    setSpeechText(
      `Claude AI aktif mengawasi seluruh ${accountCount} slot layar (:99 s/d :${98 + accountCount})!`
    );
  }, [accountCount]);

  // When bot starts, Claude jumps with joy!
  useEffect(() => {
    if (workerStatus.running) {
      setIsJumping(true);
      setSpeechText(`Bot sedang berjalan! Saya memantau proses ulasan di ${accountCount} layar simultan.`);
      const timer = setTimeout(() => setIsJumping(false), 900);
      return () => clearTimeout(timer);
    }
  }, [workerStatus.running, accountCount]);

  // Main Walking Movement Loop
  useEffect(() => {
    if (!isWalking || isDragging || isInspecting || isMinimized) return;

    const interval = setInterval(() => {
      setPosX((prevX) => {
        const windowWidth = typeof window !== 'undefined' ? window.innerWidth : 1200;
        const mascotWidth = 72;
        const minX = 16;
        const maxX = Math.max(minX + 100, windowWidth - mascotWidth - 24);

        let nextX = prevX + direction * 2.2;

        // Turn around at right edge
        if (nextX >= maxX) {
          nextX = maxX;
          setDirection(-1);
          // 25% chance to inspect at edge
          if (Math.random() > 0.6) {
            triggerInspect();
          }
        }
        // Turn around at left edge
        else if (nextX <= minX) {
          nextX = minX;
          setDirection(1);
          // 25% chance to inspect at edge
          if (Math.random() > 0.6) {
            triggerInspect();
          }
        }

        return nextX;
      });

      // Animate walking legs
      setWalkFrameIndex((prev) => (prev + 1) % WALK_SPRITES.length);
    }, 75);

    return () => clearInterval(interval);
  }, [isWalking, direction, isDragging, isInspecting, isMinimized]);

  // Temporary Inspection pause
  const triggerInspect = () => {
    setIsInspecting(true);
    setTimeout(() => {
      setIsInspecting(false);
    }, 2800);
  };

  // Drag Handlers
  const handleMouseDown = (e) => {
    if (e.button !== 0) return; // Only left click
    dragRef.current = {
      startX: e.clientX,
      startPosX: posX,
      hasMoved: false
    };
    setIsDragging(true);

    const handleMouseMove = (moveEvent) => {
      const deltaX = moveEvent.clientX - dragRef.current.startX;
      if (Math.abs(deltaX) > 4) {
        dragRef.current.hasMoved = true;
      }
      const windowWidth = window.innerWidth;
      const minX = 16;
      const maxX = Math.max(minX + 100, windowWidth - 90);
      const newX = Math.min(maxX, Math.max(minX, dragRef.current.startPosX + deltaX));
      setPosX(newX);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);

      // If barely moved, trigger click interaction
      if (!dragRef.current.hasMoved) {
        handleMascotClick();
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };

  // Touch Drag for Mobile / Tablet
  const handleTouchStart = (e) => {
    if (!e.touches || e.touches.length === 0) return;
    const touch = e.touches[0];
    dragRef.current = {
      startX: touch.clientX,
      startPosX: posX,
      hasMoved: false
    };
    setIsDragging(true);

    const handleTouchMove = (moveEvent) => {
      if (!moveEvent.touches || moveEvent.touches.length === 0) return;
      const moveTouch = moveEvent.touches[0];
      const deltaX = moveTouch.clientX - dragRef.current.startX;
      if (Math.abs(deltaX) > 4) {
        dragRef.current.hasMoved = true;
      }
      const windowWidth = window.innerWidth;
      const minX = 12;
      const maxX = Math.max(minX + 80, windowWidth - 85);
      const newX = Math.min(maxX, Math.max(minX, dragRef.current.startPosX + deltaX));
      setPosX(newX);
    };

    const handleTouchEnd = () => {
      setIsDragging(false);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleTouchEnd);

      if (!dragRef.current.hasMoved) {
        handleMascotClick();
      }
    };

    window.addEventListener('touchmove', handleTouchMove);
    window.addEventListener('touchend', handleTouchEnd);
  };

  // Mascot Click Interaction
  const handleMascotClick = () => {
    setIsJumping(true);
    setTimeout(() => setIsJumping(false), 600);

    // Pick random chatter if speech already open
    if (isSpeechOpen) {
      const randomIdx = Math.floor(Math.random() * CHATTER_PHRASES.length);
      setSpeechText(CHATTER_PHRASES[randomIdx]);
    } else {
      setIsSpeechOpen(true);
    }
  };

  // Action: Trigger Sync
  const handleSyncAction = () => {
    setIsJumping(true);
    setSpeechText(`Claude AI: Memperbarui snapshot frame untuk seluruh ${accountCount} layar!`);
    setTimeout(() => setIsJumping(false), 700);
    if (onSyncScreens) onSyncScreens();
  };

  // Action: Trigger Inspection
  const handleInspectAction = () => {
    triggerInspect();
    setSpeechText(`Claude AI: Memeriksa Display :99 s/d :${98 + accountCount}... Semua layar responsif! ✨`);
  };

  // Determine which sprite to display
  let currentSprite = claudeWalk2;
  if (isDragging || isJumping) {
    currentSprite = claudeJump;
  } else if (isInspecting) {
    currentSprite = claudeInspect;
  } else if (isWalking) {
    currentSprite = WALK_SPRITES[walkFrameIndex];
  }

  // Minimized Docked Widget
  if (isMinimized) {
    return (
      <div className="fixed bottom-4 left-4 z-40">
        <button
          onClick={() => {
            setIsMinimized(false);
            setIsSpeechOpen(true);
          }}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/95 hover:bg-white text-slate-800 border border-amber-300 shadow-md text-xs font-semibold backdrop-blur-xs transition cursor-pointer hover:scale-105"
          title="Bangunkan Claude AI Mascot"
        >
          <div className="w-5 h-5 rounded-full bg-amber-100 flex items-center justify-center p-0.5">
            <img src={claudeHero} alt="Claude" className="w-full h-full object-contain [image-rendering:pixelated]" />
          </div>
          <span className="text-[#D87653] font-bold">Claude AI</span>
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
        </button>
      </div>
    );
  }

  // Calculate Speech Bubble Alignment (avoid screen overflow)
  const isNearRightEdge = typeof window !== 'undefined' ? posX > window.innerWidth - 320 : false;

  return (
    <div
      ref={mascotRef}
      style={{
        left: `${posX}px`,
        bottom: '18px'
      }}
      className="fixed z-40 select-none transition-transform pointer-events-auto"
    >
      {/* ========================================================================= */}
      {/* 1. INTERACTIVE SPEECH BALLOON                                             */}
      {/* ========================================================================= */}
      {isSpeechOpen && (
        <div
          style={{
            transform: isNearRightEdge ? 'translateX(-70%)' : 'translateX(-20%)'
          }}
          className="absolute -top-3 sm:-top-4 left-1/2 -translate-y-full w-72 sm:w-80 bg-white/95 backdrop-blur-md rounded-2xl border border-amber-300 shadow-xl p-3 sm:p-3.5 text-xs text-slate-800 animate-in fade-in zoom-in-95 duration-150"
        >
          {/* Header Dialog */}
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-amber-100">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="font-bold text-[#D87653] text-[11px] uppercase tracking-wider flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                Claude AI Companion
              </span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsMinimized(true)}
                className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                title="Sembunyikan ke pojok"
              >
                <ChevronUp className="w-3.5 h-3.5 rotate-180" />
              </button>
              <button
                onClick={() => setIsSpeechOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                title="Tutup balon percakapan"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Speech Text Content */}
          <p className="text-slate-700 leading-snug mb-3 font-medium text-[11.5px]">
            {speechText}
          </p>

          {/* Slot Badges Status Bar */}
          <div className="flex items-center gap-1 bg-amber-50/70 p-1.5 rounded-lg border border-amber-200/60 mb-2.5 overflow-x-auto no-scrollbar">
            <span className="text-[10px] font-bold text-amber-800 uppercase shrink-0">Layar:</span>
            {Array.from({ length: accountCount }, (_, i) => i + 1).map((slotNum) => (
              <span
                key={slotNum}
                className="px-1.5 py-0.5 rounded bg-white text-[10px] font-mono font-semibold text-slate-700 border border-slate-200 shrink-0 flex items-center gap-1"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>S0{slotNum}</span>
              </span>
            ))}
          </div>

          {/* Interactive Quick Buttons */}
          <div className="grid grid-cols-2 gap-1.5 pt-1 border-t border-slate-100">
            <button
              onClick={() => setIsWalking(!isWalking)}
              className="px-2 py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 bg-slate-100 hover:bg-slate-200 text-slate-700 transition cursor-pointer"
            >
              {isWalking ? (
                <>
                  <Pause className="w-3 h-3 text-amber-600" />
                  <span>Duduk / Diam</span>
                </>
              ) : (
                <>
                  <Play className="w-3 h-3 text-emerald-600" />
                  <span>Mulai Jalan</span>
                </>
              )}
            </button>

            <button
              onClick={handleSyncAction}
              className="px-2 py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 bg-[#2563EB]/10 hover:bg-[#2563EB]/20 text-[#2563EB] transition cursor-pointer"
            >
              <RotateCw className="w-3 h-3" />
              <span>Sinkronkan</span>
            </button>

            <button
              onClick={handleInspectAction}
              className="px-2 py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 bg-amber-100/70 hover:bg-amber-200/70 text-amber-800 transition cursor-pointer"
            >
              <Search className="w-3 h-3" />
              <span>Cek Layar</span>
            </button>

            <button
              onClick={() => {
                if (onOpenDiagnostic) onOpenDiagnostic();
                setIsSpeechOpen(false);
              }}
              className="px-2 py-1.5 rounded-lg text-[10px] font-bold flex items-center justify-center gap-1 bg-[#172033] hover:bg-slate-800 text-white transition cursor-pointer"
            >
              <Sliders className="w-3 h-3 text-amber-400" />
              <span>Diagnostik</span>
            </button>
          </div>

          {/* Balloon Pointer Arrow */}
          <div
            style={{
              left: isNearRightEdge ? '70%' : '20%'
            }}
            className="absolute -bottom-2 w-3.5 h-3.5 bg-white border-r border-b border-amber-300 transform rotate-45 -translate-x-1/2"
          ></div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 2. CLAUDE WALKING / DRAGGABLE MASCOT AVATAR                               */}
      {/* ========================================================================= */}
      <div
        onClick={() => {
          if (!dragRef.current.hasMoved) {
            handleMascotClick();
          }
        }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        className={`relative group cursor-grab active:cursor-grabbing transition-transform ${
          isJumping ? '-translate-y-5 scale-110' : ''
        } ${isDragging ? 'scale-115 -translate-y-3' : ''}`}
        title="Klik untuk berinteraksi, atau drag untuk memindahkan Claude!"
      >
        {/* Soft Ground Shadow */}
        <div
          className={`absolute -bottom-1.5 left-1/2 -translate-x-1/2 rounded-full bg-slate-900/20 blur-[2px] transition-all ${
            isJumping || isDragging ? 'w-8 h-1 opacity-25' : 'w-12 h-2 opacity-50'
          }`}
        ></div>

        {/* Mascot Sprite Container */}
        <div
          style={{
            transform: direction === -1 ? 'scaleX(-1)' : 'scaleX(1)'
          }}
          className="w-14 h-14 sm:w-16 sm:h-16 flex items-center justify-center filter drop-shadow-md group-hover:drop-shadow-lg transition-transform"
        >
          <img
            src={currentSprite}
            alt="Claude Walking Mascot"
            className="w-full h-full object-contain [image-rendering:pixelated] select-none pointer-events-none"
            draggable={false}
          />
        </div>

        {/* Tiny Status Badge & Ping Dot */}
        <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center shadow-xs">
          <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
        </span>

        {/* Drag Hint on Hover */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-slate-800 text-white text-[9px] font-mono px-1 rounded whitespace-nowrap pointer-events-none">
          Klik / Drag
        </div>
      </div>
    </div>
  );
}
