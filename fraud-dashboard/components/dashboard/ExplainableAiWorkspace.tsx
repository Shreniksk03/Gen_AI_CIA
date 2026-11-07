'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  Info,
  CheckCircle2,
  AlertCircle,
  FileText,
} from 'lucide-react';
import { FraudAnalysis, ShapValue } from '@/types';

interface ExplainableAiWorkspaceProps {
  analysis: FraudAnalysis | null;
  loading?: boolean;
}

export default function ExplainableAiWorkspace({
  analysis,
  loading = false,
}: ExplainableAiWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<'waterfall' | 'narrative'>('waterfall');

  const shapValues = analysis?.shapValues || [];
  const narrative = analysis?.summaryNarrative || [];
  const baseValue = analysis?.baseValue ?? -1.78;

  // Find max absolute value to scale bars accurately
  const maxAbsVal = Math.max(
    0.1,
    ...shapValues.map((s) => Math.abs(s.value))
  );

  return (
    <div className="h-full rounded-2xl glass-panel border border-white/10 bg-void-950/70 p-5 flex flex-col justify-between select-none">
      {/* Top Header */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              TreeSHAP Explainability
            </span>
          </div>

          {/* View Tab Buttons */}
          <div className="flex items-center rounded-lg bg-slate-900 border border-white/10 p-0.5 text-[10px] font-mono">
            <button
              onClick={() => setActiveTab('waterfall')}
              className={`px-2.5 py-1 rounded transition-colors ${
                activeTab === 'waterfall'
                  ? 'bg-cyan-500/20 text-cyan-300 font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Feature Attribution
            </button>
            <button
              onClick={() => setActiveTab('narrative')}
              className={`px-2.5 py-1 rounded transition-colors ${
                activeTab === 'narrative'
                  ? 'bg-cyan-500/20 text-cyan-300 font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Auditor Narrative
            </button>
          </div>
        </div>

        {/* Baseline Output Space Subtitle */}
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pb-3 mb-3 border-b border-white/5">
          <span>Log-Odds Base Margin: {baseValue.toFixed(2)}</span>
          <span className="text-slate-500">Output: Raw Margin (Log-Odds)</span>
        </div>
      </div>

      {/* Main Body */}
      <div className="flex-1 overflow-y-auto custom-scroll pr-1 my-2 min-h-[220px]">
        {loading ? (
          <div className="space-y-3 py-4">
            <div className="h-5 bg-slate-800/60 rounded animate-pulse w-full" />
            <div className="h-5 bg-slate-800/60 rounded animate-pulse w-4/5" />
            <div className="h-5 bg-slate-800/60 rounded animate-pulse w-3/4" />
          </div>
        ) : shapValues.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center text-center text-slate-500 font-mono text-xs">
            <AlertCircle className="w-6 h-6 mb-2 text-slate-600" />
            <span>Select a transaction to inspect its TreeSHAP attribution</span>
          </div>
        ) : activeTab === 'waterfall' ? (
          /* Horizontal Contribution Chart */
          <div className="space-y-3">
            {shapValues.map((item, idx) => {
              const isPositive = item.value > 0;
              const barWidthPercent = Math.min(100, (Math.abs(item.value) / maxAbsVal) * 100);

              return (
                <div key={idx} className="group">
                  {/* Feature Label & Value */}
                  <div className="flex items-center justify-between text-[11px] font-mono mb-1">
                    <span className="text-slate-300 font-medium truncate max-w-[200px]" title={item.displayName || item.feature}>
                      {item.displayName || item.feature}
                    </span>
                    <div className="flex items-center gap-2">
                      {item.featureValue !== undefined && (
                        <span className="text-[10px] text-slate-500">
                          (val: {String(item.featureValue)})
                        </span>
                      )}
                      <span
                        className={`font-bold ${
                          isPositive ? 'text-rose-400' : 'text-emerald-400'
                        }`}
                      >
                        {isPositive ? `+${item.value.toFixed(3)}` : item.value.toFixed(3)}
                      </span>
                    </div>
                  </div>

                  {/* Horizontal Bar */}
                  <div className="w-full h-2 rounded-full bg-slate-900 border border-white/5 overflow-hidden flex">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${barWidthPercent}%` }}
                      transition={{ duration: 0.6, delay: idx * 0.05 }}
                      className={`h-full rounded-full ${
                        isPositive
                          ? 'bg-gradient-to-r from-rose-500 to-amber-500'
                          : 'bg-gradient-to-r from-cyan-500 to-emerald-400'
                      }`}
                    />
                  </div>

                  {/* Human readable description */}
                  <div className="text-[10px] text-slate-400 font-sans mt-0.5 truncate">
                    {item.description}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Natural Language Narrative Summary */
          <div className="space-y-2.5">
            {narrative.length === 0 ? (
              <p className="text-xs font-mono text-slate-400">
                No narrative summary generated for this record.
              </p>
            ) : (
              narrative.map((note, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-slate-900/60 border border-white/5 flex items-start gap-2.5 text-xs text-slate-300 font-sans leading-relaxed"
                >
                  <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                  <span>{note}</span>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Footer Legend */}
      <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-slate-400">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-rose-500" />
            <span>Risk-Increasing (+SHAP)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Risk-Reducing (-SHAP)</span>
          </span>
        </div>
        <span className="text-slate-500">Trained Model Artifacts</span>
      </div>
    </div>
  );
}

