import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Star, Zap, ShieldCheck, Cpu } from "lucide-react";

export const Scene1Hook: React.FC<{ isVertical?: boolean }> = ({ isVertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring
  const introSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 90 },
  });

  // Exit transition
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
        padding: isVertical ? "40px 24px" : "60px 80px",
        opacity: exitOpacity,
        transform: `scale(${introSpring * exitScale})`,
      }}
    >
      {/* Top Pill Badge */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 10,
          padding: isVertical ? "8px 18px" : "10px 24px",
          borderRadius: 9999,
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid rgba(16, 185, 129, 0.4)",
          backdropFilter: "blur(12px)",
          marginBottom: isVertical ? 24 : 32,
        }}
      >
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: "#10B981",
            boxShadow: "0 0 12px #10B981",
          }}
        />
        <span
          style={{
            color: "#34D399",
            fontWeight: 700,
            fontSize: isVertical ? 20 : 22,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          Google Maps Automation Reimagined
        </span>
      </div>

      {/* Main Title */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 16,
        }}
      >
        <h1
          style={{
            fontSize: isVertical ? 76 : 108,
            fontWeight: 900,
            letterSpacing: "-0.03em",
            margin: 0,
            background: "linear-gradient(135deg, #FFFFFF 20%, #34D399 70%, #06B6D4 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            textAlign: "center",
            textShadow: "0 10px 30px rgba(16, 185, 129, 0.2)",
          }}
        >
          AutoBotix
        </h1>
      </div>

      {/* 5-Star Rating Pop-in */}
      <div
        style={{
          display: "flex",
          gap: isVertical ? 12 : 18,
          marginBottom: isVertical ? 30 : 40,
        }}
      >
        {[0, 1, 2, 3, 4].map((index) => {
          const starSpring = spring({
            frame: frame - 12 - index * 6,
            fps,
            config: { damping: 10, stiffness: 140 },
          });
          const clampedSpring = Math.max(0, starSpring);

          return (
            <div
              key={index}
              style={{
                transform: `scale(${clampedSpring}) rotate(${interpolate(
                  clampedSpring,
                  [0, 1],
                  [-40, 0]
                )}deg)`,
                filter: "drop-shadow(0 0 16px rgba(250, 204, 21, 0.6))",
              }}
            >
              <Star
                size={isVertical ? 42 : 54}
                fill="#FBBF24"
                color="#F59E0B"
                strokeWidth={1.5}
              />
            </div>
          );
        })}
      </div>

      {/* Punchy Subtitle */}
      <p
        style={{
          fontSize: isVertical ? 26 : 34,
          color: "#94A3B8",
          fontWeight: 500,
          maxWidth: isVertical ? 720 : 1100,
          textAlign: "center",
          lineHeight: 1.4,
          margin: 0,
          marginBottom: isVertical ? 40 : 54,
        }}
      >
        Say goodbye to heavy virtual machines and bot bans.{" "}
        <span style={{ color: "#F8FAFC", fontWeight: 700 }}>
          Direct Native Chromium & CDP automation
        </span>{" "}
        delivering fast, natural reviews with zero bloat.
      </p>

      {/* Feature Badges */}
      <div
        style={{
          display: "flex",
          flexDirection: isVertical ? "column" : "row",
          gap: isVertical ? 16 : 24,
          width: isVertical ? "90%" : "auto",
        }}
      >
        {[
          {
            icon: Cpu,
            title: "Zero-VM Architecture",
            desc: "90% Less RAM & CPU",
            color: "#10B981",
          },
          {
            icon: ShieldCheck,
            title: "Anti-Bot Natural Delays",
            desc: "Sequential Humanized Queue",
            color: "#06B6D4",
          },
          {
            icon: Zap,
            title: "Pre-Check Duplicate Skip",
            desc: "Safe & Ban-Proof",
            color: "#8B5CF6",
          },
        ].map((item, i) => {
          const badgeSpring = spring({
            frame: frame - 30 - i * 8,
            fps,
            config: { damping: 12, stiffness: 100 },
          });

          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                padding: isVertical ? "16px 20px" : "16px 28px",
                borderRadius: 16,
                background: "rgba(15, 23, 42, 0.7)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                backdropFilter: "blur(12px)",
                transform: `scale(${Math.max(0, badgeSpring)})`,
                boxShadow: "0 8px 24px rgba(0, 0, 0, 0.3)",
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 12,
                  backgroundColor: `${item.color}22`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <item.icon size={24} color={item.color} />
              </div>
              <div>
                <div style={{ color: "#F8FAFC", fontWeight: 700, fontSize: isVertical ? 20 : 20 }}>
                  {item.title}
                </div>
                <div style={{ color: "#94A3B8", fontSize: isVertical ? 15 : 15, marginTop: 2 }}>
                  {item.desc}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
