'use client';

import { motion } from 'framer-motion';
import AnimatedNumber from './AnimatedNumber';

interface FraudGaugeProps {
  score: number; // 0–100
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  processingTime: number;
  loading?: boolean;
}

const RISK_CONFIG = {
  LOW: {
    label: 'SECURE MATRIX',
    fromColor: '#00d4ff',
    toColor: '#10b981',
    glowColor: 'rgba(16, 185, 129, 0.45)',
    badgeBg: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
  },
  MEDIUM: {
    label: 'ELEVATED REVIEW',
    fromColor: '#38bdf8',
    toColor: '#f59e0b',
    glowColor: 'rgba(245, 158, 11, 0.45)',
    badgeBg: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
  },
  HIGH: {
    label: 'HIGH SUSPICION',
    fromColor: '#f59e0b',
    toColor: '#ef4444',
    glowColor: 'rgba(239, 68, 68, 0.55)',
    badgeBg: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  },
  CRITICAL: {
    label: 'CRITICAL THREAT',
    fromColor: '#f59e0b',
    toColor: '#dc2626',
    glowColor: 'rgba(220, 38, 38, 0.65)',
    badgeBg: 'bg-crimson-500/20 text-rose-300 border-crimson-500/40',
  },
};

export default function FraudGauge({
  score,
  riskLevel,
  confidence,
  processingTime,
  loading = false,
}: FraudGaugeProps) {
  const radius = 86;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const cfg = RISK_CONFIG[riskLevel || 'LOW'];

  return (
    <div className="flex flex-col items-center gap-3 w-full">
      <div className="relative w-52 h-52 sm:w-56 sm:h-56 flex items-center justify-center">
        {/* Ambient volumetric backdrop glow behind the gauge */}
        <div
          className="absolute inset-4 rounded-full blur-2xl transition-colors duration-1000"
          style={{ backgroundColor: cfg.glowColor, opacity: loading ? 0.45 : 0.28 }}
        />

        <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 220 220">
          <defs>
            {/* Smooth animated SVG gradient */}
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={cfg.fromColor} />
              <stop offset="100%" stopColor={cfg.toColor} />
            </linearGradient>

            {/* Soft volumetric filter */}
            <filter id="gaugeGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Outer technical dash ring */}
          <circle
            cx="110"
            cy="110"
            r="102"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1.5"
            strokeDasharray="4 8"
            fill="none"
          />

          {/* Background track */}
          <circle
            cx="110"
            cy="110"
            r={radius}
            stroke="rgba(255,255,255,0.05)"
            strokeWidth="13"
            strokeLinecap="round"
            fill="none"
          />

          {/* Foreground Animated Value Arc */}
          <motion.circle
            cx="110"
            cy="110"
            r={radius}
            stroke="url(#gaugeGradient)"
            strokeWidth="13"
            strokeLinecap="round"
            fill="none"
            filter="url(#gaugeGlow)"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{
              strokeDashoffset: loading ? circumference * 0.5 : strokeDashoffset,
              rotate: loading ? [0, 360] : 0,
            }}
            transition={{
              strokeDashoffset: { duration: 1.2, ease: [0.16, 1, 0.3, 1] },
              rotate: loading ? { repeat: Infinity, duration: 2, ease: 'linear' } : undefined,
            }}
          />
        </svg>

        {/* Center Digital Telemetry Display */}
        <div className="relative z-10 flex flex-col items-center justify-center text-center select-none">
          <span className="text-[9px] font-mono tracking-[0.25em] text-slate-400 uppercase mb-1">
            {loading ? 'ANALYZING' : 'FRAUD PROBABILITY'}
          </span>

          <div className="flex items-baseline font-sans font-extrabold tracking-tight">
            <span
              className="text-4xl sm:text-5xl font-extrabold tracking-tight font-sans"
              style={{
                color: cfg.toColor,
                filter: `drop-shadow(0 0 16px ${cfg.glowColor})`,
              }}
            >
              {loading ? (
                <span className="animate-pulse text-3xl font-mono text-cyan-300">...</span>
              ) : (
                <AnimatedNumber value={score} decimals={1} />
              )}
            </span>
            {!loading && <span className="text-xl sm:text-2xl text-slate-400 font-mono ml-0.5">%</span>}
          </div>

          {/* Categorical Risk Matrix Badge */}
          <motion.div
            key={loading ? 'loading' : riskLevel}
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`mt-2 px-3 py-0.5 rounded-full text-[9px] font-mono tracking-[0.2em] font-semibold border ${
              loading ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30 animate-pulse' : cfg.badgeBg
            }`}
          >
            {loading ? 'INFERRING XGBOOST' : cfg.label}
          </motion.div>
        </div>
      </div>

      {/* Auxiliary Metadata Badges */}
      <div className="flex items-center justify-between w-full max-w-xs px-2 pt-1 text-[10px] font-mono text-slate-400 border-t border-white/[0.06]">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
          <span>ACCURACY:</span>
          <span className="text-slate-200 font-semibold">{confidence}%</span>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>LATENCY:</span>
          <span className="text-slate-200 font-semibold">{processingTime}ms</span>
        </div>
      </div>
    </div>
  );
}
