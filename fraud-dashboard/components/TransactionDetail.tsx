'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Transaction } from '@/types';
import AnimatedNumber from './AnimatedNumber';

interface TransactionDetailProps {
  transaction: Transaction | null;
}

function formatAmount(amount: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
}

export default function TransactionDetail({ transaction }: TransactionDetailProps) {
  if (!transaction) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <div className="w-10 h-10 rounded-xl glass-panel border border-white/10 flex items-center justify-center mb-2 text-cyan-300">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
          </svg>
        </div>
        <p className="text-xs font-mono tracking-wider text-slate-400">
          AWAITING TRANSACTION SELECTION
        </p>
      </div>
    );
  }

  const isFraud = transaction.status === 'flagged';

  const fields = [
    { label: 'TRANSACTION ID', value: transaction.id },
    { label: 'MERCHANT ENTITY', value: transaction.merchant },
    { label: 'CATEGORY', value: transaction.category },
    { label: 'AMOUNT', value: formatAmount(transaction.amount) },
    { label: 'GEOLOCATION', value: transaction.location },
    { label: 'PAYMENT CARD', value: `•••• •••• •••• ${transaction.cardLast4}` },
    { label: 'TIMESTAMP UTC', value: new Date(transaction.timestamp).toLocaleString() },
  ];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={transaction.id}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.25 }}
        className="h-full min-h-0 flex flex-col space-y-2.5 overflow-y-auto pr-1 custom-scroll scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent"
      >
        {/* Status Header Badge */}
        <div className="flex items-center justify-between">
          <div
            className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-mono tracking-[0.2em] font-semibold uppercase border ${
              isFraud
                ? 'text-rose-300 bg-rose-500/15 border-rose-500/40 shadow-[0_0_12px_rgba(244,63,94,0.3)]'
                : transaction.status === 'reviewing'
                ? 'text-amber-300 bg-amber-500/15 border-amber-500/40 shadow-[0_0_12px_rgba(245,158,11,0.2)]'
                : 'text-emerald-300 bg-emerald-500/15 border-emerald-500/40 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
            }`}
          >
            <div
              className={`w-1.5 h-1.5 rounded-full ${
                isFraud
                  ? 'bg-rose-400 animate-ping'
                  : transaction.status === 'reviewing'
                  ? 'bg-amber-400'
                  : 'bg-emerald-400'
              }`}
            />
            {transaction.status.toUpperCase()}
          </div>

          <span className="text-[10px] font-mono text-slate-400">
            AUDIT RECORD VERIFIED
          </span>
        </div>

        {/* Technical Key-Value Rows */}
        <div className="divide-y divide-white/[0.05] rounded-xl glass-panel p-3 border border-white/[0.06]">
          {fields.map((f) => (
            <div key={f.label} className="flex items-center justify-between py-1.5 first:pt-0 last:pb-0 gap-3">
              <span className="text-[9px] font-mono tracking-wider text-slate-400 uppercase shrink-0">
                {f.label}
              </span>
              <span className="text-xs font-mono font-medium text-slate-200 truncate text-right">
                {f.value}
              </span>
            </div>
          ))}
        </div>

        {/* Linear Gauge with Fluid Gradient */}
        <div className="rounded-xl glass-panel p-3 border border-white/[0.06]">
          <div className="flex justify-between items-center mb-1.5">
            <span className="text-[9px] font-mono tracking-[0.2em] text-slate-400 uppercase">
              FRAUD CONFIDENCE RATIO
            </span>
            <div className={`text-xs font-mono font-bold ${isFraud ? 'text-rose-400' : 'text-emerald-400'}`}>
              <AnimatedNumber value={transaction.fraudScore} decimals={1} suffix=" / 100" />
            </div>
          </div>

          <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{
                background: isFraud
                  ? 'linear-gradient(90deg, #f59e0b, #ef4444)'
                  : transaction.status === 'reviewing'
                  ? 'linear-gradient(90deg, #38bdf8, #f59e0b)'
                  : 'linear-gradient(90deg, #00d4ff, #10b981)',
              }}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(transaction.fraudScore, 100)}%` }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            />
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
