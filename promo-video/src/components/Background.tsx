import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

export const Background: React.FC<{ isVertical?: boolean }> = ({ isVertical }) => {
  const frame = useCurrentFrame();

  // Floating ambient glow orbs
  const orb1X = Math.sin(frame * 0.03) * 60;
  const orb1Y = Math.cos(frame * 0.02) * 40;
  const orb2X = Math.cos(frame * 0.025) * 50;
  const orb2Y = Math.sin(frame * 0.035) * 60;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#070B14",
        overflow: "hidden",
        fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Dynamic Cyber Grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.04) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.04) 1px, transparent 1px)
          `,
          backgroundSize: isVertical ? "60px 60px" : "80px 80px",
          opacity: 0.7,
        }}
      />

      {/* Ambient Radial Glowing Orbs */}
      <div
        style={{
          position: "absolute",
          top: isVertical ? "15%" : "20%",
          left: isVertical ? "10%" : "25%",
          width: isVertical ? 500 : 700,
          height: isVertical ? 500 : 700,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(16, 185, 129, 0.22) 0%, rgba(16, 185, 129, 0) 70%)",
          transform: `translate(${orb1X}px, ${orb1Y}px)`,
          filter: "blur(40px)",
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          position: "absolute",
          bottom: isVertical ? "15%" : "15%",
          right: isVertical ? "5%" : "20%",
          width: isVertical ? 550 : 750,
          height: isVertical ? 550 : 750,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(6, 182, 212, 0.2) 0%, rgba(59, 130, 246, 0) 70%)",
          transform: `translate(${orb2X}px, ${orb2Y}px)`,
          filter: "blur(50px)",
          pointerEvents: "none",
        }}
      />

      {/* Top subtle vignette */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "radial-gradient(ellipse at center, transparent 40%, rgba(5, 8, 16, 0.8) 100%)",
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};
