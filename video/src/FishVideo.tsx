import {
  AbsoluteFill,
  Easing,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Bubbles } from "./Bubbles";
import { Fish } from "./Fish";

const INTRO = 90;
const SWIM = 150;
const OUTRO = 90;
const FADE = 15;
export const FISH_VIDEO_DURATION = INTRO + SWIM + OUTRO;

type Props = { title: string; subtitle: string };

// Fades a scene in and out over FADE frames so cuts become crossfades.
const Fade: React.FC<{ duration: number; children: React.ReactNode }> = ({ duration, children }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, FADE, duration - FADE, duration], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ opacity }}>{children}</AbsoluteFill>;
};

const Intro: React.FC<Props> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 12 } });
  const sub = interpolate(frame, [25, 45], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ fontSize: 260, fontWeight: 900, color: "white", transform: `scale(${pop})` }}>{title}</div>
      <div style={{ fontSize: 56, color: "#bfe9ff", opacity: sub, transform: `translateY(${(1 - sub) * 30}px)` }}>
        {subtitle}
      </div>
    </AbsoluteFill>
  );
};

const School: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const fish = [
    { color: "#ff8a3d", size: 320, y: 380, delay: 0, speed: 1 },
    { color: "#ffd23f", size: 180, y: 220, delay: 15, speed: 1.3 },
    { color: "#ff5d8f", size: 220, y: 650, delay: 30, speed: 1.15 },
    { color: "#7ae582", size: 140, y: 800, delay: 45, speed: 1.5 },
  ];
  return (
    <AbsoluteFill>
      {fish.map((f, i) => {
        const x = interpolate(frame - f.delay, [0, SWIM / f.speed], [width + 100, -f.size - 100], {
          easing: Easing.inOut(Easing.quad),
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const bob = Math.sin((frame + i * 30) / 12) * 25;
        return (
          <div key={i} style={{ position: "absolute", left: x, top: f.y + bob }}>
            <Fish color={f.color} size={f.size} />
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Outro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const words = ["плыви", "дальше", "🐟"];
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "row", gap: 40 }}>
      {words.map((w, i) => {
        const s = spring({ frame: frame - i * 8, fps, config: { damping: 10 } });
        return (
          <span key={w} style={{ fontSize: 140, fontWeight: 800, color: "white", transform: `translateY(${(1 - s) * 200}px)`, opacity: s }}>
            {w}
          </span>
        );
      })}
    </AbsoluteFill>
  );
};

export const FishVideo: React.FC<Props> = (props) => {
  const frame = useCurrentFrame();
  // Background slowly shifts deeper over the whole video.
  const depth = interpolate(frame, [0, FISH_VIDEO_DURATION], [0, 1]);
  const top = `hsl(200, 80%, ${45 - depth * 20}%)`;
  const bottom = `hsl(215, 85%, ${18 - depth * 10}%)`;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(${top}, ${bottom})`, fontFamily: "sans-serif" }}>
      <Bubbles />
      <Sequence durationInFrames={INTRO}>
        <Fade duration={INTRO}>
          <Intro {...props} />
        </Fade>
      </Sequence>
      <Sequence from={INTRO - FADE} durationInFrames={SWIM + FADE}>
        <Fade duration={SWIM + FADE}>
          <School />
        </Fade>
      </Sequence>
      <Sequence from={INTRO + SWIM} durationInFrames={OUTRO}>
        <Outro />
      </Sequence>
    </AbsoluteFill>
  );
};
