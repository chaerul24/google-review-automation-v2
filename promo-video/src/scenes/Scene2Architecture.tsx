import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Server, XCircle, CheckCircle2, Monitor } from "lucide-react";

export const Scene2Architecture: React.FC<{ isVertical?: boolean }> = ({ isVertical }) => {
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

  // Display slot pulse
  const pulse = Math.sin(frame * 0.15) > 0 ? 1 : 0.6;

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: isVertical ? "40px 24px" : "50px 80px",
        opacity: exitOpacity,
        transform: `scale(${enterSpring * exitScale})`,
      }}
    >
      {/* Header Tag */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 10,
          padding: isVertical ? "8px 18px" : "8px 22px",
          borderRadius: 9999,
          background: "rgba(6, 182, 212, 0.15)",
          border: "1px solid rgba(6, 182, 212, 0.4)",
          marginBottom: 16,
        }}
      >
        <Server size={isVertical ? 18 : 20} color="#22D3EE" />
        <span
          style={{
            color: "#38BDF8",
            fontWeight: 700,
            fontSize: isVertical ? 18 : 20,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          High-Efficiency Architecture
        </span>
      </div>

      <h2
        style={{
          fontSize: isVertical ? 48 : 64,
          fontWeight: 900,
          margin: 0,
          marginBottom: isVertical ? 24 : 36,
          textAlign: "center",
          color: "#FFFFFF",
          letterSpacing: "-0.02em",
        }}
      >
        Zero-VM vs Bulky Emulators
      </h2>

      {/* Comparison Grid */}
      <div
        style={{
          display: "flex",
          flexDirection: isVertical ? "column" : "row",
          gap: isVertical ? 20 : 36,
          width: "100%",
          maxWidth: isVertical ? 760 : 1380,
          justifyContent: "center",
        }}
      >
        {/* Left: Traditional VM */}
        <div
          style={{
            flex: 1,
            borderRadius: 20,
            background: "rgba(30, 20, 25, 0.6)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            padding: isVertical ? "20px 24px" : "28px 32px",
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.3)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 16,
              color: "#F87171",
            }}
          >
            <XCircle size={28} />
            <h3 style={{ margin: 0, fontSize: isVertical ? 24 : 28, fontWeight: 700 }}>
              Old Approach (Heavy VMs)
            </h3>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[
              "Requires 4-8 GB RAM per virtual machine",
              "Slow boot times & constant freezing",
              "Easily fingerprinted by Google anti-fraud",
              "Maximum 1-2 accounts before host crashes",
            ].map((text, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ color: "#EF4444", fontSize: 18 }}>✕</span>
                <span style={{ color: "#94A3B8", fontSize: isVertical ? 18 : 20 }}>{text}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: AutoBotix Zero-VM */}
        <div
          style={{
            flex: 1.15,
            borderRadius: 20,
            background: "rgba(10, 30, 30, 0.75)",
            border: "2px solid rgba(16, 185, 129, 0.6)",
            padding: isVertical ? "20px 24px" : "28px 32px",
            boxShadow: "0 10px 40px rgba(16, 185, 129, 0.2)",
            position: "relative",
          }}
        >
          {/* Recommended Tag */}
          <div
            style={{
              position: "absolute",
              top: -14,
              right: 24,
              backgroundColor: "#10B981",
              color: "#022C22",
              fontWeight: 800,
              fontSize: 14,
              padding: "4px 14px",
              borderRadius: 9999,
              letterSpacing: "0.05em",
            }}
          >
            AUTOBOTIX NATIVE
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              marginBottom: 16,
              color: "#34D399",
            }}
          >
            <CheckCircle2 size={28} />
            <h3 style={{ margin: 0, fontSize: isVertical ? 24 : 28, fontWeight: 800 }}>
              Zero-VM Chromium Engine
            </h3>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
            {[
              "100% Native Linux Chromium & CDP Control",
              "Virtual Xvfb Displays (:99, :100, :101, ...)",
              "Real persistent Google profiles & cookie auth",
              "Run 10+ accounts concurrently on $5 VPS",
            ].map((text, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ color: "#10B981", fontSize: 18 }}>✓</span>
                <span style={{ color: "#F1F5F9", fontSize: isVertical ? 18 : 20, fontWeight: 500 }}>
                  {text}
                </span>
              </div>
            ))}
          </div>

          {/* Active Virtual Displays Live Strip */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "10px 14px",
              borderRadius: 12,
              backgroundColor: "rgba(15, 23, 42, 0.8)",
              border: "1px solid rgba(52, 211, 153, 0.3)",
            }}
          >
            <Monitor size={18} color="#34D399" />
            <span style={{ color: "#94A3B8", fontSize: 14, fontWeight: 600 }}>Active Slots:</span>
            {[":99", ":100", ":101", ":102"].map((disp, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "3px 8px",
                  borderRadius: 6,
                  background: "rgba(16, 185, 129, 0.15)",
                  border: "1px solid rgba(16, 185, 129, 0.4)",
                  fontSize: 13,
                  color: "#34D399",
                  fontWeight: 700,
                }}
              >
                <div
                  style={{
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    backgroundColor: "#10B981",
                    opacity: pulse,
                  }}
                />
                Display {disp}
              </div>
            ))}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
