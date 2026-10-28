import React from "react";
import {
  AbsoluteFill,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Terminal, ArrowRight, Sparkles, Check, DownloadCloud } from "lucide-react";

const GithubIcon: React.FC<{ size?: number; color?: string }> = ({ size = 24, color = "currentColor" }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke={color}
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
  </svg>
);

export const Scene4TerminalAndCta: React.FC<{ isVertical?: boolean }> = ({ isVertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterSpring = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 90 },
  });

  const buttonPulse = Math.sin(frame * 0.12) * 4;

  return (
    <AbsoluteFill
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: isVertical ? "40px 24px" : "50px 80px",
        transform: `scale(${enterSpring})`,
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
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid rgba(16, 185, 129, 0.4)",
          marginBottom: 16,
        }}
      >
        <Sparkles size={isVertical ? 18 : 20} color="#34D399" />
        <span
          style={{
            color: "#34D399",
            fontWeight: 700,
            fontSize: isVertical ? 18 : 20,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          Open Source & Ready to Deploy
        </span>
      </div>

      <h2
        style={{
          fontSize: isVertical ? 48 : 68,
          fontWeight: 900,
          margin: 0,
          marginBottom: 16,
          textAlign: "center",
          color: "#FFFFFF",
          letterSpacing: "-0.03em",
        }}
      >
        Automate Reviews with Confidence
      </h2>

      <p
        style={{
          fontSize: isVertical ? 22 : 28,
          color: "#94A3B8",
          margin: 0,
          marginBottom: isVertical ? 28 : 36,
          textAlign: "center",
          maxWidth: 900,
        }}
      >
        Windows CMD & Linux Terminal Support • Auto-Updater Built-in
      </p>

      {/* Terminal Card */}
      <div
        style={{
          width: "100%",
          maxWidth: isVertical ? 740 : 1000,
          borderRadius: 16,
          background: "rgba(15, 23, 42, 0.95)",
          border: "1px solid rgba(255, 255, 255, 0.15)",
          boxShadow: "0 16px 40px rgba(0, 0, 0, 0.5)",
          padding: isVertical ? "16px 20px" : "20px 28px",
          fontFamily: "monospace",
          marginBottom: isVertical ? 32 : 40,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 12,
            borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
            paddingBottom: 8,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Terminal size={18} color="#38BDF8" />
            <span style={{ color: "#F1F5F9", fontSize: 14, fontWeight: 700 }}>
              Command Prompt / PowerShell
            </span>
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "rgba(16, 185, 129, 0.15)",
              padding: "4px 10px",
              borderRadius: 6,
              color: "#34D399",
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            <DownloadCloud size={14} /> Auto-Updater: v1.0.3 (Latest)
          </div>
        </div>

        <div style={{ color: "#34D399", fontSize: isVertical ? 16 : 20, marginBottom: 6 }}>
          C:\AutoBotix&gt; python bot_cli.py
        </div>
        <div style={{ color: "#94A3B8", fontSize: isVertical ? 14 : 16 }}>
          ✓ Connected to Dispatch API [Port 8000] • 6 Accounts Loaded • Zero-VM Ready
        </div>
      </div>

      {/* GitHub Call to Action Button */}
      <div
        style={{
          display: "flex",
          flexDirection: isVertical ? "column" : "row",
          alignItems: "center",
          gap: 20,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            padding: isVertical ? "16px 32px" : "20px 44px",
            borderRadius: 9999,
            background: "linear-gradient(135deg, #10B981 0%, #06B6D4 100%)",
            color: "#022C22",
            fontWeight: 800,
            fontSize: isVertical ? 22 : 26,
            boxShadow: "0 10px 30px rgba(16, 185, 129, 0.4)",
            transform: `translateY(${buttonPulse}px)`,
          }}
        >
          <GithubIcon size={isVertical ? 26 : 30} color="#022C22" />
          <span>github.com/chaerul24/google-review-automation-v2</span>
          <ArrowRight size={isVertical ? 24 : 28} color="#022C22" />
        </div>
      </div>

      <div
        style={{
          display: "flex",
          gap: 24,
          marginTop: 24,
          color: "#94A3B8",
          fontSize: isVertical ? 15 : 18,
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Check size={16} color="#10B981" /> 100% Free & Open Source
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Check size={16} color="#10B981" /> MIT License
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Check size={16} color="#10B981" /> Production Tested
        </span>
      </div>
    </AbsoluteFill>
  );
};
