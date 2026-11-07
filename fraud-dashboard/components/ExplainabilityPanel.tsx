'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShapValue } from '@/types';

interface ExplainabilityPanelProps {
  shapValues: ShapValue[];
  transactionId: string | null;
  baseValue?: number;
  summaryNarrative?: string[];
  loading?: boolean;
}

export default function ExplainabilityPanel({
  shapValues,
  transactionId,
  baseValue = 0.164,
  summaryNarrative = [],
  loading = false,
}: ExplainabilityPanelProps) {
  const [activeTab, setActiveTab] = useState<'all' | 'positive' | 'negative'>('all');

  const maxAbs = Math.max(...shapValues.map((s) => Math.abs(s.value)), 0.01);
  const positiveList = shapValues.filter((s) => s.value > 0);
  const negativeList = shapValues.filter((s) => s.value < 0);

  const displayedList =
    activeTab === 'positive'
      ? positiveList
      : activeTab === 'negative'
      ? negativeList
      : shapValues.slice().sort((a, b) => Math.abs(b.value) - Math.abs(a.value));

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden">
      {/* Header */}
      <div className="shrink-0 flex items-center justify-between mb-2.5 pb-2 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
          <h2 className="text-xs font-mono tracking-[0.2em] uppercase text-slate-200">
            TreeSHAP Explainability
          </h2>
        </div>
        <div className="flex items-center gap-1.5">
          {transactionId && (
            <span className="text-[9px] font-mono tracking-wider text-slate-400 glass-panel rounded-full px-2 py-0.5 border border-white/[0.06]">
              {transactionId}
            </span>
          )}
          {baseValue !== undefined && (
            <span
              className="text-[9px] font-mono text-cyan-400/80 glass-panel rounded-full px-2 py-0.5 border border-cyan-500/20"
              title="Expected Baseline Value E[f(x)]"
            >
              E[f(x)]: {baseValue.toFixed(2)}
            </span>
          )}
        </div>
      </div>

      {loading ? (
        /* Loading Skeleton */
        <div className="flex-1 flex flex-col justify-center space-y-3 p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span className="text-[10px] font-mono text-cyan-300 uppercase tracking-widest">
              Extracting TreeSHAP Attributions...
            </span>
          </div>
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="glass-panel p-2.5 rounded-lg border border-white/[0.06] animate-pulse space-y-2">
              <div className="flex justify-between">
                <div className="h-3 w-32 bg-white/10 rounded" />
                <div className="h-3 w-12 bg-white/10 rounded" />
              </div>
              <div className="h-2 w-full bg-white/5 rounded-full" />
            </div>
          ))}
        </div>
      ) : !transactionId ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
          <div className="w-12 h-12 rounded-2xl glass-panel border border-white/10 flex items-center justify-center mb-3 text-cyan-300">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
            </svg>
          </div>
          <p className="text-xs font-mono tracking-wider text-slate-400">
            SELECT A TRANSACTION TO INSPECT
          </p>
          <span className="text-[10px] font-mono text-slate-400 mt-1">
            Real TreeSHAP feature attributions will load here
          </span>
        </div>
      ) : shapValues.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6 space-y-2">
          <div className="w-10 h-10 rounded-xl glass-panel border border-amber-500/30 flex items-center justify-center text-amber-400">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
          </div>
          <p className="text-xs font-mono tracking-wider text-slate-300 uppercase">
            Historical Transaction Record
          </p>
          <p className="text-[10px] font-mono text-slate-400 max-w-xs">
            This transaction record was persisted without localized TreeSHAP attribution data. Run &quot;Simulate Transaction&quot; to inspect full real-time SHAP vectors.
          </p>
        </div>
      ) : (
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
          {/* Contribution Filter Tabs */}
          <div className="shrink-0 flex items-center gap-1 mb-2.5 p-0.5 rounded-lg bg-void-900/60 border border-white/[0.06]">
            <button
              onClick={() => setActiveTab('all')}
              className={`flex-1 py-1 px-2 rounded-md text-[9px] font-mono tracking-wider uppercase transition-colors ${
                activeTab === 'all'
                  ? 'bg-white/10 text-white font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Top Impact ({shapValues.length})
            </button>
            <button
              onClick={() => setActiveTab('positive')}
              className={`flex-1 py-1 px-2 rounded-md text-[9px] font-mono tracking-wider uppercase transition-colors ${
                activeTab === 'positive'
                  ? 'bg-rose-500/20 text-rose-300 font-semibold border border-rose-500/30'
                  : 'text-slate-400 hover:text-rose-300'
              }`}
            >
              Risk Drivers ({positiveList.length})
            </button>
            <button
              onClick={() => setActiveTab('negative')}
              className={`flex-1 py-1 px-2 rounded-md text-[9px] font-mono tracking-wider uppercase transition-colors ${
                activeTab === 'negative'
                  ? 'bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30'
                  : 'text-slate-400 hover:text-emerald-300'
              }`}
            >
              Safeguards ({negativeList.length})
            </button>
          </div>

          {/* Feature Impact Bar List */}
          <div className="flex-1 min-h-0 overflow-y-auto space-y-2 pr-1.5 custom-scroll scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
            <AnimatePresence initial={false}>
              {displayedList.map((item, idx) => {
                const isRiskIncreasing = item.value > 0;
                const absVal = Math.abs(item.value);
                const widthPercent = Math.min((absVal / maxAbs) * 100, 100);

                return (
                  <motion.div
                    key={item.feature + idx}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ delay: idx * 0.03, duration: 0.25 }}
                    className="group rounded-xl p-2.5 border border-white/[0.06] bg-void-900/40 hover:bg-void-900/70 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-1.5 truncate max-w-[210px]">
                        <span
                          className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                            isRiskIncreasing ? 'bg-rose-400' : 'bg-emerald-400'
                          }`}
                        />
                        <span className="text-xs font-mono font-medium text-slate-200 truncate" title={item.feature}>
                          {item.displayName || item.feature}
                        </span>
                      </div>

                      <div className="flex items-center gap-1 shrink-0 font-mono text-xs">
                        <span
                          className={`font-semibold ${
                            isRiskIncreasing ? 'text-rose-400' : 'text-emerald-400'
                          }`}
                        >
                          {isRiskIncreasing ? '+' : ''}
                          {item.value.toFixed(3)}
                        </span>
                      </div>
                    </div>

                    {/* Proportional Diverging Impact Bar */}
                    <div className="relative h-1.5 w-full rounded-full bg-void-950 overflow-hidden mb-1.5 border border-white/[0.04]">
                      <motion.div
                        className={`h-full rounded-full ${
                          isRiskIncreasing
                            ? 'bg-gradient-to-r from-rose-500 to-amber-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]'
                            : 'bg-gradient-to-r from-cyan-400 to-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]'
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.max(widthPercent, 6)}%` }}
                        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                      />
                    </div>

                    {/* Contextual Human Readable Narrative */}
                    <div className="text-[10px] font-mono text-slate-400 leading-tight">
                      {item.humanReadable || item.description}
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>

          {/* Plain-Language Narrative Summary Section */}
          {summaryNarrative.length > 0 && (
            <div className="shrink-0 mt-2 pt-2 border-t border-white/[0.06] text-[10px] font-mono space-y-1">
              <span className="text-[9px] uppercase tracking-wider text-slate-400">Model Narrative:</span>
              <ul className="list-disc list-inside text-slate-300 space-y-0.5">
                {summaryNarrative.slice(0, 2).map((line, i) => (
                  <li key={i} className="truncate">{line}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
