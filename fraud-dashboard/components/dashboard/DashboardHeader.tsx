'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ShieldCheck,
  RefreshCw,
  Clock,
  Database,
  Cpu,
  User,
  ArrowLeft,
  Activity,
} from 'lucide-react';
import { ModelInfo } from '@/types';

interface DashboardHeaderProps {
  backendOnline: boolean | null;
  databaseConnected: boolean;
  databaseSource?: string;
  databaseSourceLabel?: string;
  modelInfo: ModelInfo | null;
  loading: boolean;
  onRefresh: () => void;
}

export default function DashboardHeader({
  backendOnline,
  databaseConnected,
  databaseSource,
  databaseSourceLabel,
  modelInfo,
  loading,
  onRefresh,
}: DashboardHeaderProps) {
  const [timeString, setTimeString] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeString(
        now.toLocaleTimeString('en-US', {
          hour12: false,
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          timeZoneName: 'short',
        })
      );
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="w-full glass-panel border-b border-white/10 px-4 sm:px-6 py-3.5 mb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 select-none">
      {/* Left: Brand Identity & Home Link */}
      <div className="flex items-center gap-3">
        <Link
          href="/"
          title="Return to Product Home"
          className="group flex items-center gap-2.5 hover:opacity-90 transition-opacity"
        >
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500/20 via-void-900 to-amber-500/20 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_15px_rgba(56,189,248,0.3)] shrink-0">
            <ShieldCheck className="w-4 h-4 text-cyan-300 group-hover:scale-105 transition-transform" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold font-mono tracking-widest uppercase text-white">
                Fraud<span className="text-cyan-400">Sentinel</span>
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-cyan-300">
                CONSOLE
              </span>
            </div>
            <div className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
              <ArrowLeft className="w-3 h-3 group-hover:-translate-x-0.5 transition-transform" />
              <span>Back to Overview</span>
            </div>
          </div>
        </Link>
      </div>

      {/* Center: System Status & Diagnostic Indicators */}
      <div className="flex flex-wrap items-center gap-2.5 text-[11px] font-mono">
        {/* Backend Online Pill */}
        <div
          className={`flex items-center gap-2 px-3 py-1 rounded-lg border ${
            backendOnline === true
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : backendOnline === false
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              : 'bg-slate-900 border-white/10 text-slate-400'
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              backendOnline === true
                ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                : backendOnline === false
                ? 'bg-rose-500'
                : 'bg-amber-400 animate-pulse'
            }`}
          />
          <span>
            {backendOnline === true
              ? 'API ONLINE'
              : backendOnline === false
              ? 'API DISCONNECTED'
              : 'CHECKING API'}
          </span>
        </div>

        {/* Database Status Pill */}
        <div
          title={
            databaseSource === 'SUPABASE_POSTGRESQL'
              ? 'Authoritative Supabase Cloud PostgreSQL'
              : 'Local SQLite Fallback (Supabase RLS Blocked / Key Missing)'
          }
          className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border ${
            databaseSource === 'SUPABASE_POSTGRESQL'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span>
            DB:{' '}
            <strong className="font-semibold">
              {databaseSourceLabel || (databaseConnected ? 'PostgreSQL' : 'SQLite Fallback')}
            </strong>
          </span>
        </div>

        {/* Model Threshold Pill */}
        <div
          title="Trained XGBoost Classifier Threshold"
          className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/80 border border-white/10 text-slate-300"
        >
          <Cpu className="w-3.5 h-3.5 text-amber-400" />
          <span>
            MODEL:{' '}
            <strong className="text-white font-semibold">
              XGBoost (τ = {modelInfo?.selected_threshold ?? 0.35})
            </strong>
          </span>
        </div>

        {/* Clock */}
        <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-900/80 border border-white/10 text-slate-400">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{timeString || '--:--:--'}</span>
        </div>
      </div>

      {/* Right: Refresh & Analyst Profile */}
      <div className="flex items-center gap-3">
        <button
          onClick={onRefresh}
          disabled={loading}
          title="Refresh transaction telemetry and analytics"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 hover:border-cyan-400/40 text-slate-300 hover:text-cyan-300 text-xs font-mono transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>

        {/* Analyst Profile Badge */}
        <div className="flex items-center gap-2 pl-3 border-l border-white/10">
          <div className="w-7 h-7 rounded-full bg-slate-800 border border-cyan-500/30 flex items-center justify-center text-cyan-300">
            <User className="w-3.5 h-3.5" />
          </div>
          <div className="hidden xl:flex flex-col text-left">
            <span className="text-[11px] font-mono font-semibold text-slate-200">
              Lead Investigator
            </span>
            <span className="text-[9px] font-mono text-cyan-400/80">Tier 3 Auth</span>
          </div>
        </div>
      </div>
    </header>
  );
}

