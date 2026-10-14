import React from 'react';
import { motion } from 'framer-motion';

export default function ConfidenceGauge({ score = 0, size = 60, strokeWidth = 5 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const percentage = score * 100;
  const offset = circumference - (percentage / 100) * circumference;

  let color = '#556B2F'; // success (olive)
  if (score < 0.6) color = '#8B0000'; // critical (rust)
  else if (score < 0.8) color = '#B7791F'; // warning (mustard)

  return (
    <div className="relative flex items-center justify-center bg-subtle rounded-full border border-default" style={{ width: size, height: size }}>
      <svg className="transform -rotate-90" width={size} height={size}>
        <circle
          className="text-slate-200"
          strokeWidth={strokeWidth}
          stroke="currentColor"
          fill="transparent"
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />
        <motion.circle
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          strokeLinecap="round"
          fill="transparent"
          r={radius}
          cx={size / 2}
          cy={size / 2}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1, ease: "easeInOut" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center">
        <span className="text-xs font-bold text-muted">
          {Math.round(percentage)}%
        </span>
      </div>
    </div>
  );
}
