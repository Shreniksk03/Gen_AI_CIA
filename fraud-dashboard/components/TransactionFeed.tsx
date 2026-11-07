'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Transaction } from '@/types';

interface TransactionFeedProps {
  transactions: Transaction[];
  selectedId: string | null;
  onSelect: (txn: Transaction) => void;
  loading?: boolean;
  onSimulate?: () => void;
}

const STATUS_CONFIG = {
  secure: {
    label: 'SECURE',
    color: 'text-emerald-300',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    dot: 'bg-emerald-400',
    glow: 'shadow-[0_0_15px_rgba(16,185,129,0.12)]',
  },
  reviewing: {
    label: 'REVIEW',
    color: 'text-amber-300',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
    dot: 'bg-amber-400',
    glow: 'shadow-[0_0_15px_rgba(245,158,11,0.15)]',
  },
  flagged: {
    label: 'FLAGGED',
    color: 'text-rose-300',
    bg: 'bg-rose-500/15',
    border: 'border-rose-500/40',
    dot: 'bg-rose-400 animate-pulse',
    glow: 'shadow-[0_0_20px_rgba(244,63,94,0.25)]',
  },
};

function formatAmount(amount: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  } catch {
    return '00:00:00';
  }
}

export default function TransactionFeed({
  transactions,
  selectedId,
  onSelect,
  loading = false,
  onSimulate,
}: TransactionFeedProps) {
  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between mb-3 pb-2.5 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-slate-200">
            Live Stream Feed
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono tracking-wider text-slate-400 glass-panel rounded-full px-2.5 py-0.5">
            {loading ? 'CONNECTING...' : `${transactions.length} EVENTS`}
          </span>
        </div>
      </div>

      {/* Feed list with independent scroll and custom dark glass scrollbar */}
      <div className="flex-1 min-h-0 overflow-y-auto space-y-2 pr-1.5 custom-scroll scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
        {loading ? (
          /* Loading Skeletons */
          <div className="space-y-2.5 py-1">
            {[1, 2, 3, 4, 5].map((idx) => (
              <div
                key={idx}
                className="rounded-xl p-3 border border-white/[0.06] bg-void-900/40 animate-pulse space-y-2"
              >
                <div className="flex justify-between items-center">
                  <div className="h-3 w-28 bg-white/10 rounded" />
                  <div className="h-3 w-16 bg-white/10 rounded" />
                </div>
                <div className="flex justify-between items-center pt-1">
                  <div className="h-2.5 w-20 bg-white/5 rounded" />
                  <div className="h-4 w-12 bg-white/10 rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : transactions.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3">
            <div className="w-12 h-12 rounded-2xl glass-panel border border-white/10 flex items-center justify-center text-slate-400">
              <svg className="w-6 h-6 text-cyan-400/80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <div>
              <p className="text-xs font-mono tracking-wider text-slate-300 uppercase">
                Zero Recorded Telemetry
              </p>
              <p className="text-[10px] font-mono text-slate-400 mt-1">
                No transactions currently found in database.
              </p>
            </div>
            {onSimulate && (
              <button
                onClick={onSimulate}
                className="mt-2 px-3 py-1.5 rounded-lg glass-panel border border-cyan-400/40 text-[10px] font-mono tracking-wider text-cyan-300 hover:bg-cyan-500/10 transition-colors uppercase"
              >
                + Ingest First Event
              </button>
            )}
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {transactions.map((txn, i) => {
              const cfg = STATUS_CONFIG[txn.status];
              const isSelected = txn.id === selectedId;

              return (
                <motion.div
                  key={txn.id}
                  layout
                  initial={{ opacity: 0, x: -16, scale: 0.98 }}
                  animate={{ opacity: 1, x: 0, scale: 1 }}
                  exit={{ opacity: 0, x: 16, scale: 0.96 }}
                  transition={{ type: 'spring', stiffness: 350, damping: 28, delay: i < 5 ? i * 0.02 : 0 }}
                  onClick={() => onSelect(txn)}
                  className={`
                    relative cursor-pointer rounded-xl p-3 border transition-all duration-200
                    ${isSelected
                      ? `${cfg.bg} ${cfg.border} ring-1 ring-cyan-400/40 ${cfg.glow}`
                      : 'bg-void-900/40 border-white/[0.06] hover:bg-void-900/70 hover:border-white/[0.14]'
                    }
                  `}
                >
                  {/* Active Indicator Bar */}
                  {isSelected && (
                    <motion.div
                      layoutId="activeFeedBar"
                      className="absolute left-0 top-2 bottom-2 w-1 rounded-r-full bg-cyan-400 shadow-[0_0_8px_#38bdf8]"
                    />
                  )}

                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2 truncate">
                      <div className={`w-2 h-2 rounded-full shrink-0 ${cfg.dot}`} />
                      <span className="font-semibold text-xs tracking-tight text-slate-100 truncate">
                        {txn.merchant}
                      </span>
                    </div>

                    <span className="font-mono font-bold text-xs tracking-tight text-white shrink-0">
                      {formatAmount(txn.amount)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span className="truncate max-w-[140px] text-slate-400">{txn.location}</span>
                    <div className="flex items-center gap-2 shrink-0">
                      <span>{formatTime(txn.timestamp)}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${cfg.color} ${cfg.bg} border ${cfg.border}`}>
                        {txn.fraudScore.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
