import { Composition } from "remotion";
import { FishVideo, FISH_VIDEO_DURATION } from "./FishVideo";

export const Root: React.FC = () => (
  <Composition
    id="FishVideo"
    component={FishVideo}
    durationInFrames={FISH_VIDEO_DURATION}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{ title: "fish", subtitle: "смонтировано в Remotion" }}
  />
);
