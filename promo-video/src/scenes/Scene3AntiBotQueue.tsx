import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { ShieldCheck, FastForward, CheckCircle, Clock } from "lucide-react";

export const Scene3AntiBotQueue: React.FC<{ isVertical?: boolean }> = ({ isVertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 85 },
  });

  const exitOpacity = interpolate(frame, [95, 112], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exitScale = interpolate(frame, [95, 112], [1, 0.94], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: isVertical ? "40px 20px" : "40px 80px",
        opacity: exitOpacity,
        transform: `scale(${enterSpring * exitScale})`,
      }}
    >
      {/* Top Tag */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 10,
          padding: isVertical ? "8px 18px" : "8px 22px",
          borderRadius: 9999,
          background: "rgba(139, 92, 246, 0.15)",
          border: "1px solid rgba(139, 92, 246, 0.4)",
          marginBottom: 16,
        }}
      >
        <ShieldCheck size={isVertical ? 18 : 20} color="#A78BFA" />
        <span
          style={{
            color: "#C4B5FD",
            fontWeight: 700,
            fontSize: isVertical ? 18 : 20,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          Anti-Bot Queue & Safety
        </span>
      </div>

      <h2
        style={{
          fontSize: isVertical ? 44 : 60,
          fontWeight: 900,
          margin: 0,
          marginBottom: isVertical ? 20 : 30,
          textAlign: "center",
          color: "#FFFFFF",
          letterSpacing: "-0.02em",
        }}
      >
        Sequential Queue & Duplicate Pre-Check
      </h2>

      {/* Terminal Mockup Window */}
      <div
        style={{
          width: "100%",
          maxWidth: isVertical ? 760 : 1240,
          borderRadius: 18,
          background: "rgba(11, 15, 25, 0.92)",
          border: "1px solid rgba(255, 255, 255, 0.15)",
          boxShadow: "0 20px 50px rgba(0, 0, 0, 0.6)",
          overflow: "hidden",
        }}
      >
        {/* Terminal Titlebar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "12px 20px",
            background: "rgba(18, 24, 38, 0.95)",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#EF4444" }} />
            <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#F59E0B" }} />
            <div style={{ width: 12, height: 12, borderRadius: "50%", backgroundColor: "#10B981" }} />
            <span
              style={{
                marginLeft: 12,
                color: "#94A3B8",
                fontSize: 14,
                fontFamily: "monospace",
                fontWeight: 600,
              }}
            >
              AutoBotix Live Worker Console — [Display :99]
            </span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              fontSize: 12,
              color: "#34D399",
              fontWeight: 700,
              fontFamily: "monospace",
            }}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                backgroundColor: "#10B981",
                boxShadow: "0 0 8px #10B981",
              }}
            />
            STATUS: ACTIVE
          </div>
        </div>

        {/* Terminal Logs Body */}
        <div
          style={{
            padding: isVertical ? "18px 20px" : "24px 28px",
            display: "flex",
            flexDirection: "column",
            gap: 12,
            fontFamily: "Consolas, Monaco, 'Courier New', monospace",
            fontSize: isVertical ? 15 : 18,
          }}
        >
          {/* Log 1 */}
          <div
            style={{
              opacity: interpolate(frame, [5, 18], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              display: "flex",
              alignItems: "center",
              gap: 10,
              color: "#E2E8F0",
            }}
          >
            <span style={{ color: "#38BDF8" }}>[23:47:37]</span>
            <span style={{ color: "#A78BFA", fontWeight: 700 }}>[chaerulbisnis17@gmail.com]</span>
            <span>──&gt; Sesi Google Maps aktif (Active Session Verified)</span>
            <span style={{ color: "#10B981" }}>✓</span>
          </div>

          {/* Log 2 - Pre Check Skip */}
          <div
            style={{
              opacity: interpolate(frame, [25, 38], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              display: "flex",
              alignItems: "center",
              gap: 10,
              color: "#FBBF24",
              background: "rgba(245, 158, 11, 0.08)",
              padding: "6px 10px",
              borderRadius: 6,
            }}
          >
            <span style={{ color: "#38BDF8" }}>[23:48:08]</span>
            <FastForward size={18} color="#FBBF24" />
            <span style={{ fontWeight: 700 }}>
              ▲ SKIP: Akun ini sudah memiliki ulasan pada Maps target! (Anti-Duplicate Prevention)
            </span>
          </div>

          {/* Log 3 - Queue Delay */}
          <div
            style={{
              opacity: interpolate(frame, [45, 58], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              display: "flex",
              alignItems: "center",
              gap: 10,
              color: "#94A3B8",
            }}
          >
            <span style={{ color: "#38BDF8" }}>[23:48:09]</span>
            <Clock size={16} color="#60A5FA" />
            <span style={{ color: "#60A5FA" }}>
              ⏳ [JEDA ANTREAN ALAMI] Menunggu jeda anti-bot 30s sebelum akun berikutnya...
            </span>
          </div>

          {/* Log 4 - Next Account Success */}
          <div
            style={{
              opacity: interpolate(frame, [65, 78], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }),
              display: "flex",
              alignItems: "center",
              gap: 10,
              color: "#34D399",
              background: "rgba(16, 185, 129, 0.08)",
              padding: "6px 10px",
              borderRadius: 6,
            }}
          >
            <span style={{ color: "#38BDF8" }}>[23:48:42]</span>
            <CheckCircle size={18} color="#34D399" />
            <span style={{ color: "#A78BFA", fontWeight: 700 }}>[unknowns@gmail.com]</span>
            <span style={{ fontWeight: 700 }}>
              ──&gt; ✓ Ulasan 5 Bintang ⭐⭐⭐⭐⭐ Berhasil Dipublikasikan di Google Maps!
            </span>
          </div>
        </div>

        {/* Live Counters Footer */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: isVertical ? "12px 18px" : "14px 28px",
            background: "rgba(15, 23, 42, 0.95)",
            borderTop: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <div style={{ display: "flex", gap: isVertical ? 12 : 24, fontSize: isVertical ? 14 : 16 }}>
            <span style={{ color: "#34D399", fontWeight: 700 }}>✓ Total Berhasil: 12</span>
            <span style={{ color: "#FBBF24", fontWeight: 700 }}>▲ Total Skip: 3</span>
            <span style={{ color: "#F87171", fontWeight: 700 }}>✕ Gagal: 0</span>
          </div>
          <div style={{ color: "#94A3B8", fontSize: 14 }}>Mode Antrean Tunggal (Anti-Bot Safe)</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
