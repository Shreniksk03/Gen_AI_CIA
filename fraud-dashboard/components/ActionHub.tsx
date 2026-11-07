'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import AnimatedNumber from './AnimatedNumber';

interface ActionHubProps {
  onSimulate: (scenario?: 'random' | 'fraud' | 'legit') => void | Promise<void>;
  onClearFlagged: () => void;
  stats: {
    total: number;
    flagged: number;
    secure: number;
    reviewing: number;
  };
  simulating?: boolean;
}

export default function ActionHub({
  onSimulate,
  onClearFlagged,
  stats,
  simulating = false,
}: ActionHubProps) {
  const [internalSimulating, setInternalSimulating] = useState(false);
  const isBusy = simulating || internalSimulating;

  const handleSimulateClick = async (scenario: 'random' | 'fraud' | 'legit' = 'random') => {
    if (isBusy) return;
    setInternalSimulating(true);
    try {
      await onSimulate(scenario);
    } finally {
      setTimeout(() => setInternalSimulating(false), 500);
    }
  };

  const statCards = [
    {
      label: 'TOTAL TELEMETRY',
      value: stats.total,
      color: 'text-cyan-300',
      border: 'border-cyan-500/20',
      badge: 'PERSISTED',
      indicator: 'bg-cyan-400',
    },
    {
      label: 'FLAGGED ANOMALIES',
      value: stats.flagged,
      color: 'text-rose-400',
      border: 'border-rose-500/30',
      badge: 'REQUIRES ACTION',
      indicator: 'bg-rose-500 animate-pulse',
    },
    {
      label: 'MANUAL REVIEW',
      value: stats.reviewing,
      color: 'text-amber-300',
      border: 'border-amber-500/25',
      badge: 'ELEVATED RISK',
      indicator: 'bg-amber-400',
    },
    {
      label: 'SECURE VERIFIED',
      value: stats.secure,
      color: 'text-emerald-400',
      border: 'border-emerald-500/25',
      badge: 'CLEARED',
      indicator: 'bg-emerald-400',
    },
  ];

  return (
    <div className="space-y-2.5">
      {/* 4 Telemetry Metric Glass Panels */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5 sm:gap-3">
        {statCards.map((s, i) => (
          <motion.div
            key={s.label}
            className={`glass-panel glass-panel-hover rounded-xl p-2.5 sm:p-3 border ${s.border} relative overflow-hidden`}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06, duration: 0.4 }}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-mono tracking-[0.2em] text-slate-400 uppercase">
                {s.label}
              </span>
              <div className={`w-1.5 h-1.5 rounded-full ${s.indicator}`} />
            </div>

            <div className="flex items-baseline justify-between mt-0.5">
              <div className={`text-xl sm:text-2xl font-bold font-sans ${s.color}`}>
                <AnimatedNumber value={s.value} />
              </div>
              <span className="text-[9px] font-mono tracking-wider text-slate-400 uppercase">
                {s.badge}
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Action Buttons Hub */}
      <div className="flex items-center gap-2.5 flex-wrap">
        {/* Primary Command Button: Simulate Random Transaction */}
        <motion.button
          onClick={() => handleSimulateClick('random')}
          disabled={isBusy}
          className="btn-command group flex-1 min-w-[200px] flex items-center justify-center gap-2.5 px-4 py-2.5 rounded-xl font-medium text-xs font-mono tracking-[0.2em] uppercase text-white border border-cyan-400/40 bg-gradient-to-r from-cyan-950/40 via-void-900/60 to-amber-950/40 shadow-[0_0_20px_rgba(56,189,248,0.2)] hover:border-cyan-300 hover:shadow-[0_0_30px_rgba(56,189,248,0.35)] disabled:opacity-50"
          whileHover={{ scale: 1.015 }}
          whileTap={{ scale: 0.985 }}
          transition={{ type: 'spring', stiffness: 400, damping: 25 }}
        >
          {isBusy ? (
            <>
              <motion.div
                className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full"
                animate={{ rotate: 360 }}
                transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
              />
              <span className="text-cyan-300">EVALUATING MODEL...</span>
            </>
          ) : (
            <>
              <svg className="w-4 h-4 text-cyan-400 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span className="text-cyan-200 group-hover:text-white transition-colors">
                SIMULATE TRANSACTION
              </span>
              <span className="text-[10px] text-cyan-400/60 font-mono hidden sm:inline">
                [LIVE DATA]
              </span>
            </>
          )}
        </motion.button>

        {/* Dedicated Test Fraud Attack Trigger */}
        <motion.button
          onClick={() => handleSimulateClick('fraud')}
          disabled={isBusy}
          title="Simulate high-risk fraud case sampled from actual dataset"
          className="flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl font-mono text-xs tracking-wider uppercase text-amber-300 border border-amber-500/30 bg-amber-950/20 hover:bg-amber-900/30 hover:border-amber-400/50 transition-all shadow-[0_0_15px_rgba(245,158,11,0.15)] disabled:opacity-50"
          whileHover={{ scale: 1.015 }}
          whileTap={{ scale: 0.985 }}
        >
          <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <span className="hidden sm:inline">TEST</span> FRAUD SCENARIO
        </motion.button>

        {/* Dismiss Flagged */}
        <motion.button
          onClick={onClearFlagged}
          className="flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl font-mono text-xs tracking-wider uppercase text-slate-400 border border-white/10 bg-void-900/40 hover:bg-white/5 hover:text-slate-200 transition-all"
          whileHover={{ scale: 1.015 }}
          whileTap={{ scale: 0.985 }}
        >
          CLEAR FLAGGED
        </motion.button>
      </div>
    </div>
  );
}
