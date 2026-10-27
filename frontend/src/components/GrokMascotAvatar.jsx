import React, { useState, useEffect, useRef } from 'react';

/**
 * GrokMascotAvatar
 * Authentic animated Grok AI Character (Black Orb with Iconic Tilted Pill Eyes)
 * 
 * Features:
 * - Natural autonomous blinking & occasional double-blink
 * - Mouse gaze tracking: eyes subtly look towards the cursor
 * - State reactions:
 *   - Idle: calm glowing eyes, periodic blinking
 *   - Typing / Thinking: eyes look up with soft cyan pulse
 *   - Working / Running: bright emerald cyber glow, scanning movement
 *   - Happy / Wink: playful wink or curved smiling eyes on click or greeting
 * - Spring bounce reaction on click
 */
export default function GrokMascotAvatar({
  size = 'md', // 'sm' (34px), 'md' (48px), 'lg' (56px)
  isRunning = false,
  isTyping = false,
  mood = 'idle', // 'idle' | 'happy' | 'thinking' | 'working' | 'wink'
  onClick,
  interactive = true,
  className = '',
}) {
  const containerRef = useRef(null);
  const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });
  const [isBlinking, setIsBlinking] = useState(false);
  const [isWinking, setIsWinking] = useState(false);
  const [isClicked, setIsClicked] = useState(false);
  const [scanOffset, setScanOffset] = useState(0);

  // Pixel sizing mapping
  const sizeMap = {
    sm: { px: 34, viewBox: 100, eyeScale: 1 },
    md: { px: 48, viewBox: 100, eyeScale: 1 },
    lg: { px: 56, viewBox: 100, eyeScale: 1.05 },
    xl: { px: 68, viewBox: 100, eyeScale: 1.1 },
  }[size] || { px: 48, viewBox: 100, eyeScale: 1 };

  // 1. Mouse Gaze Tracking
  useEffect(() => {
    if (!interactive) return;
    const handleMouseMove = (e) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      const deltaX = e.clientX - centerX;
      const deltaY = e.clientY - centerY;
      const distance = Math.hypot(deltaX, deltaY);

      // Maximum eye travel distance (in SVG units)
      const maxDist = 4.5;
      const factor = Math.min(distance, 500) / 500;
      const angle = Math.atan2(deltaY, deltaX);

      setEyeOffset({
        x: Math.cos(angle) * maxDist * factor,
        y: Math.sin(angle) * maxDist * factor,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [interactive]);

  // 2. Natural Autonomous Blinking
  useEffect(() => {
    let blinkTimer;
    const scheduleNextBlink = () => {
      const interval = Math.random() * 3200 + 2400; // between 2.4s and 5.6s
      blinkTimer = setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => {
          setIsBlinking(false);
          // 25% chance of an immediate cute double-blink
          if (Math.random() < 0.25) {
            setTimeout(() => {
              setIsBlinking(true);
              setTimeout(() => {
                setIsBlinking(false);
                scheduleNextBlink();
              }, 90);
            }, 120);
          } else {
            scheduleNextBlink();
          }
        }, 110);
      }, interval);
    };

    scheduleNextBlink();
    return () => clearTimeout(blinkTimer);
  }, []);

  // 3. Worker Scanning Movement (when automation running)
  useEffect(() => {
    if (!isRunning) return;
    let step = 0;
    const scanSteps = [-2.5, -1, 1.5, 3, 1, -1.5];
    const interval = setInterval(() => {
      step = (step + 1) % scanSteps.length;
      setScanOffset(scanSteps[step]);
    }, 600);
    return () => clearInterval(interval);
  }, [isRunning]);

  // 4. Click Handler: Spring bounce & wink reaction
  const handleClick = (e) => {
    setIsClicked(true);
    setIsWinking(true);
    setTimeout(() => setIsWinking(false), 500);
    setTimeout(() => setIsClicked(false), 350);

    if (onClick) {
      onClick(e);
    }
  };

  // Determine current active mood
  const currentMood = isTyping
    ? 'thinking'
    : isRunning
    ? 'working'
    : isWinking || mood === 'wink'
    ? 'wink'
    : mood === 'happy'
    ? 'happy'
    : 'idle';

  // Eye color and glow styling based on mood
  const eyeColor = currentMood === 'working'
    ? '#34D399' // Emerald
    : currentMood === 'thinking'
    ? '#38BDF8' // Cyan / Sky
    : currentMood === 'happy'
    ? '#60A5FA' // Soft Blue
    : '#FFFFFF'; // Crisp White

  const eyeGlowColor = currentMood === 'working'
    ? 'rgba(52, 211, 153, 0.7)'
    : currentMood === 'thinking'
    ? 'rgba(56, 189, 248, 0.7)'
    : 'rgba(255, 255, 255, 0.45)';

  // Calculate final eye translation
  const eyeTranslateX = (isRunning ? eyeOffset.x * 0.4 + scanOffset : eyeOffset.x);
  const eyeTranslateY = (isTyping ? -3 : eyeOffset.y);

  return (
    <div
      ref={containerRef}
      onClick={handleClick}
      style={{ width: sizeMap.px, height: sizeMap.px }}
      className={`relative select-none cursor-pointer flex items-center justify-center transition-transform duration-200 ${
        isClicked ? 'scale-90 rotate-[-6deg]' : 'hover:scale-105 active:scale-95'
      } ${className}`}
      title="Grok AI Robot Mascot (Klik untuk respon)"
    >
      {/* Outer Pulse Glow Ring (Active when running or thinking) */}
      {(isRunning || isTyping) && (
        <span
          className={`absolute inset-[-4px] rounded-full opacity-60 animate-ping pointer-events-none ${
            isRunning ? 'bg-emerald-400' : 'bg-cyan-400'
          }`}
        ></span>
      )}

      {/* SVG Mascot Orb */}
      <svg
        viewBox="0 0 100 100"
        className="w-full h-full drop-shadow-md overflow-visible"
      >
        <defs>
          {/* Sphere Body Radial Gradient */}
          <radialGradient id={`grokSphere-${size}`} cx="36%" cy="30%" r="68%">
            <stop offset="0%" stop-color="#1F2937" />
            <stop offset="55%" stop-color="#0B0F17" />
            <stop offset="100%" stop-color="#020408" />
          </radialGradient>

          {/* Eye Dynamic Glow Filter */}
          <filter id={`eyeGlowFilter-${size}`} x="-30%" y="-30%" width="160%" height="160%">
            <feDropShadow dx="0" dy="0" stdDeviation="1.8" flood-color={eyeGlowColor} flood-opacity="0.9" />
          </filter>
        </defs>

        {/* 1. Main Black Sphere Body */}
        <circle
          cx="50"
          cy="50"
          r="46"
          fill={`url(#grokSphere-${size})`}
          className="transition-colors duration-300"
        />

        {/* 2. Sleek Glass Specular Reflection Highlight */}
        <ellipse
          cx="38"
          cy="20"
          rx="18"
          ry="7"
          fill="#FFFFFF"
          opacity="0.06"
        />

        {/* 3. Eyes Group with Eye Movement & Blink / Wink */}
        <g
          filter={`url(#eyeGlowFilter-${size})`}
          style={{
            transform: `translate(${eyeTranslateX}px, ${eyeTranslateY}px)`,
            transition: 'transform 0.12s ease-out',
          }}
        >
          {/* Happy Arcs Eyes: ^ ^ */}
          {currentMood === 'happy' ? (
            <g stroke={eyeColor} strokeWidth="4" strokeLinecap="round" fill="none">
              <path d="M 54 44 Q 59 36 64 44" />
              <path d="M 68 42 Q 72 35 77 42" />
            </g>
          ) : isRunning ? (
            /* Loading "..." face when running / processing */
            <g fill={eyeColor}>
              <circle cx="53" cy="43" r="3.2" className="animate-pulse" />
              <circle cx="63" cy="43" r="3.2" className="animate-pulse" style={{ animationDelay: '200ms' }} />
              <circle cx="73" cy="43" r="3.2" className="animate-pulse" style={{ animationDelay: '400ms' }} />
            </g>
          ) : (
            <>
              {/* Inner Left Pill Eye */}
              <g
                style={{
                  transformOrigin: '59px 44px',
                  transform: isBlinking ? 'scaleY(0.08)' : 'scaleY(1)',
                  transition: 'transform 0.08s ease-in-out',
                }}
              >
                <rect
                  x="54.5"
                  y="33"
                  width="9.5"
                  height="22"
                  rx="4.75"
                  fill={eyeColor}
                  transform="rotate(19 59.25 44)"
                />
              </g>

              {/* Outer Right Pill Eye (Winks on click/wink mood) */}
              <g
                style={{
                  transformOrigin: '72px 41px',
                  transform: isBlinking || isWinking || currentMood === 'wink'
                    ? 'scaleY(0.08)'
                    : 'scaleY(1)',
                  transition: 'transform 0.08s ease-in-out',
                }}
              >
                <rect
                  x="67.5"
                  y="31"
                  width="8.5"
                  height="19"
                  rx="4.25"
                  fill={eyeColor}
                  transform="rotate(23 71.75 40.5)"
                />
              </g>
            </>
          )}
        </g>

        {/* Status Indicator Dot (Tiny active LED on the sphere) */}
        {isRunning && (
          <circle cx="50" cy="88" r="2.5" fill="#34D399" className="animate-pulse" />
        )}
      </svg>

      {/* Online indicator badge in corner */}
      <span
        className={`absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-white flex items-center justify-center ${
          isRunning ? 'bg-emerald-500' : 'bg-blue-500'
        }`}
      >
        <span
          className={`w-1.5 h-1.5 rounded-full bg-white ${
            isRunning ? 'animate-ping' : ''
          }`}
        ></span>
      </span>
    </div>
  );
}
