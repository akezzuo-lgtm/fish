import { AbsoluteFill, random, useCurrentFrame, useVideoConfig } from "remotion";

export const Bubbles: React.FC<{ count?: number }> = ({ count = 40 }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill>
      {new Array(count).fill(0).map((_, i) => {
        const x = random(`x${i}`) * width;
        const speed = 2 + random(`s${i}`) * 4;
        const r = 4 + random(`r${i}`) * 14;
        const y = height + 50 - ((frame * speed + random(`o${i}`) * height) % (height + 100));
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x + Math.sin((frame + i * 20) / 15) * 15,
              top: y,
              width: r,
              height: r,
              borderRadius: "50%",
              border: "2px solid rgba(255,255,255,0.5)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
