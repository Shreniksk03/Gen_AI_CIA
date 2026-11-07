'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { ShieldCheck, Activity, Terminal, ArrowRight, ExternalLink } from 'lucide-react';
import { checkBackendHealth } from '@/lib/api';

export default function LandingNavbar() {
  const [backendStatus, setBackendStatus] = useState<'checking' | 'healthy' | 'down'>('checking');
  const [dbConnected, setDbConnected] = useState(false);
  const [dbSourceLabel, setDbSourceLabel] = useState<string>('');

  useEffect(() => {
    let mounted = true;
    checkBackendHealth()
      .then((res) => {
        if (!mounted) return;
        setBackendStatus(res.status === 'healthy' ? 'healthy' : 'down');
        setDbConnected(res.database_connected);
        setDbSourceLabel(res.database_source_label || (res.database_connected ? 'PostgreSQL' : 'SQLite Fallback'));
      })
      .catch(() => {
        if (!mounted) return;
        setBackendStatus('down');
        setDbConnected(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-[#03050B]/80 border-b border-white/5 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500/20 via-void-900 to-cyan-500/10 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_15px_rgba(56,189,248,0.25)] group-hover:border-cyan-400/80 transition-all">
            <ShieldCheck className="w-4 h-4 text-cyan-300" />
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold tracking-widest uppercase text-white font-mono flex items-center gap-1.5">
              Fraud<span className="text-cyan-400">Sentinel</span>
            </span>
            <span className="text-[9px] tracking-wider text-slate-400 uppercase font-mono">
              AI Financial Intelligence
            </span>
          </div>
        </Link>

        {/* Center Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-xs uppercase tracking-widest text-slate-400 font-mono">
          <a href="#overview" className="hover:text-cyan-300 transition-colors">
            Overview
          </a>
          <a href="#workflow" className="hover:text-cyan-300 transition-colors">
            How It Works
          </a>
          <a href="#capabilities" className="hover:text-cyan-300 transition-colors">
            Capabilities
          </a>
          <a href="#technology" className="hover:text-cyan-300 transition-colors">
            Technology
          </a>
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          {/* Live System Status Pill */}
          <div
            title={
              backendStatus === 'healthy'
                ? `FastAPI Online • ${dbSourceLabel || (dbConnected ? 'PostgreSQL' : 'SQLite Fallback')}`
                : 'FastAPI Offline'
            }
            className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/80 border border-white/10 text-[11px] font-mono text-slate-300"
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                backendStatus === 'healthy'
                  ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]'
                  : backendStatus === 'checking'
                  ? 'bg-amber-400 animate-pulse'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-[10px] tracking-wider uppercase text-slate-400">
              {backendStatus === 'healthy'
                ? `API Online (${dbSourceLabel.includes('Supabase') ? 'Supabase' : 'SQLite'})`
                : backendStatus === 'checking'
                ? 'Connecting'
                : 'Offline'}
            </span>
          </div>

          {/* Launch Console CTA */}
          <Link
            href="/boot"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500/20 via-cyan-500/30 to-amber-500/20 hover:from-cyan-500/30 hover:to-amber-500/30 border border-cyan-400/50 hover:border-cyan-300 text-xs font-mono font-semibold tracking-wider text-cyan-200 shadow-[0_0_20px_rgba(56,189,248,0.2)] transition-all group"
          >
            <Terminal className="w-3.5 h-3.5 text-cyan-300 group-hover:rotate-12 transition-transform" />
            <span>LAUNCH CONSOLE</span>
            <ArrowRight className="w-3.5 h-3.5 text-cyan-300 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>
    </header>
  );
}

