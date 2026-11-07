'use client';

import { BarChart3, PieChart, TrendingUp, ShieldCheck, ShieldAlert } from 'lucide-react';
import { AnalyticsData } from '@/types';

interface AnalyticsTelemetryChartsProps {
  analytics: AnalyticsData | null;
}

export default function AnalyticsTelemetryCharts({
  analytics,
}: AnalyticsTelemetryChartsProps) {
  const dist = analytics?.risk_distribution || { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };
  const totalDist = dist.LOW + dist.MEDIUM + dist.HIGH + dist.CRITICAL || 1;

  const lowPercent = Math.round((dist.LOW / totalDist) * 100);
  const medPercent = Math.round((dist.MEDIUM / totalDist) * 100);
  const highPercent = Math.round((dist.HIGH / totalDist) * 100);
  const critPercent = Math.round((dist.CRITICAL / totalDist) * 100);

  const total = analytics?.total_transactions || 0;
  const flagged = analytics?.total_flagged_transactions || 0;
  const confirmed = analytics?.total_confirmed_fraud || 0;

  return (
    <div className="h-full rounded-2xl glass-panel border border-white/10 bg-void-950/70 p-5 flex flex-col justify-between select-none">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              Risk Distribution & Portfolio Telemetry
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            Window: {analytics?.time_range || '7d'}
          </span>
        </div>

        {/* 1. Risk Tier Proportions Bar */}
        <div className="mb-5">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-300 mb-1.5">
            <span>Portfolio Risk Tiers</span>
            <span className="text-slate-400">{total} evaluated</span>
          </div>

          {/* Segmented Progress Bar */}
          <div className="w-full h-3 rounded-full bg-slate-900 border border-white/5 overflow-hidden flex">
            <div
              style={{ width: `${lowPercent}%` }}
              title={`LOW: ${dist.LOW} (${lowPercent}%)`}
              className="bg-emerald-400 h-full transition-all"
            />
            <div
              style={{ width: `${medPercent}%` }}
              title={`MEDIUM: ${dist.MEDIUM} (${medPercent}%)`}
              className="bg-yellow-400 h-full transition-all"
            />
            <div
              style={{ width: `${highPercent}%` }}
              title={`HIGH: ${dist.HIGH} (${highPercent}%)`}
              className="bg-amber-500 h-full transition-all"
            />
            <div
              style={{ width: `${critPercent}%` }}
              title={`CRITICAL: ${dist.CRITICAL} (${critPercent}%)`}
              className="bg-rose-500 h-full transition-all"
            />
          </div>

          {/* Legend Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-3 text-[10px] font-mono">
            <div className="p-2 rounded bg-slate-900/60 border border-emerald-500/20 flex flex-col">
              <span className="text-emerald-400 font-bold">{dist.LOW} ({lowPercent}%)</span>
              <span className="text-slate-400">Low (&lt;25%)</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-yellow-500/20 flex flex-col">
              <span className="text-yellow-400 font-bold">{dist.MEDIUM} ({medPercent}%)</span>
              <span className="text-slate-400">Medium (25-60%)</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-amber-500/20 flex flex-col">
              <span className="text-amber-400 font-bold">{dist.HIGH} ({highPercent}%)</span>
              <span className="text-slate-400">High (60-80%)</span>
            </div>
            <div className="p-2 rounded bg-slate-900/60 border border-rose-500/20 flex flex-col">
              <span className="text-rose-400 font-bold">{dist.CRITICAL} ({critPercent}%)</span>
              <span className="text-slate-400">Critical (≥80%)</span>
            </div>
          </div>
        </div>

        {/* 2. Flagged vs. Confirmed Fraud Ratio */}
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-slate-300">Model Flagged vs Analyst Confirmed</span>
            <span className="text-cyan-300">
              {flagged > 0 ? ((confirmed / flagged) * 100).toFixed(1) : 0}% Confirmed
            </span>
          </div>

          <div className="w-full h-2 rounded-full bg-slate-950 overflow-hidden flex">
            <div
              style={{
                width: `${flagged > 0 ? (confirmed / flagged) * 100 : 0}%`,
              }}
              className="bg-amber-400 h-full"
            />
          </div>

          <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
            <span>{confirmed} Confirmed Fraud</span>
            <span>{flagged} Total Flagged by Model</span>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-slate-500">
        <span>Source: PostgreSQL Transaction Store</span>
        <span>Updated Live</span>
      </div>
    </div>
  );
}

