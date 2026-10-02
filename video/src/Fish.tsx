import { interpolate, useCurrentFrame } from "remotion";

// Simple SVG fish whose tail wags based on the current frame.
export const Fish: React.FC<{ color: string; size: number }> = ({ color, size }) => {
  const frame = useCurrentFrame();
  const wag = Math.sin(frame / 3) * 12;
  return (
    <svg width={size} height={size * 0.6} viewBox="0 0 200 120">
      <g transform={`rotate(${wag} 150 60)`}>
        <polygon points="150,60 200,20 200,100" fill={color} opacity={0.85} />
      </g>
      <ellipse cx="85" cy="60" rx="75" ry="45" fill={color} />
      <circle cx="40" cy="48" r="9" fill="white" />
      <circle cx="37" cy="48" r="4" fill="#0b1d2e" />
      <path
        d={`M 90 30 Q 110 ${interpolate(Math.sin(frame / 5), [-1, 1], [5, 15])} 130 30`}
        stroke="white"
        strokeOpacity={0.4}
        strokeWidth={4}
        fill="none"
      />
    </svg>
  );
};
