import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { Background } from "./components/Background";
import { Scene1Hook } from "./scenes/Scene1Hook";
import { Scene2Architecture } from "./scenes/Scene2Architecture";
import { Scene3AntiBotQueue } from "./scenes/Scene3AntiBotQueue";
import { Scene4TerminalAndCta } from "./scenes/Scene4TerminalAndCta";

export const AutoBotixShorts: React.FC = () => {
  return (
    <AbsoluteFill>
      <Background isVertical={true} />

      {/* Scene 1: Hook & Intro (0s - 3.66s) */}
      <Sequence from={0} durationInFrames={110} name="Hook & Intro">
        <Scene1Hook isVertical={true} />
      </Sequence>

      {/* Scene 2: Zero-VM Architecture (3.66s - 7.33s) */}
      <Sequence from={110} durationInFrames={110} name="Zero-VM Architecture">
        <Scene2Architecture isVertical={true} />
      </Sequence>

      {/* Scene 3: Anti-Bot Queue & Pre-Check (7.33s - 11.0s) */}
      <Sequence from={220} durationInFrames={110} name="Anti-Bot Queue">
        <Scene3AntiBotQueue isVertical={true} />
      </Sequence>

      {/* Scene 4: CLI & Open Source CTA (11.0s - 15.0s) */}
      <Sequence from={330} durationInFrames={120} name="CLI & CTA">
        <Scene4TerminalAndCta isVertical={true} />
      </Sequence>
    </AbsoluteFill>
  );
};
