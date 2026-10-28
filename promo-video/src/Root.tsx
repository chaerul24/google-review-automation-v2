import "./index.css";
import { Composition, Folder } from "remotion";
import { AutoBotixPromo } from "./AutoBotixPromo";
import { AutoBotixShorts } from "./AutoBotixShorts";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="AutoBotix-Promos">
        {/* Landscape Promo 16:9 (1920x1080) for YouTube / Twitter / GitHub */}
        <Composition
          id="AutoBotixPromo"
          component={AutoBotixPromo}
          durationInFrames={450}
          fps={30}
          width={1920}
          height={1080}
        />

        {/* Vertical Promo 9:16 (1080x1920) for TikTok / Instagram Reels / YouTube Shorts */}
        <Composition
          id="AutoBotixShorts"
          component={AutoBotixShorts}
          durationInFrames={450}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>
    </>
  );
};
