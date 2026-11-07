'use client';

import Link from 'next/link';
import { ShieldCheck, Terminal, ArrowUp } from 'lucide-react';

export default function LandingFooter() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="border-t border-white/10 bg-[#020408] py-16 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-12 border-b border-white/5">
          {/* Brand Info */}
          <div className="md:col-span-5 flex flex-col items-start">
            <Link href="/" className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-cyan-500/20 via-void-900 to-cyan-500/10 border border-cyan-400/40 flex items-center justify-center shadow-[0_0_15px_rgba(56,189,248,0.25)]">
                <ShieldCheck className="w-4 h-4 text-cyan-300" />
              </div>
              <span className="text-base font-bold tracking-widest uppercase text-white font-mono">
                Fraud<span className="text-cyan-400">Sentinel</span>
              </span>
            </Link>

            <p className="text-xs text-slate-400 max-w-sm leading-relaxed mb-6 font-sans">
              AI-Powered Financial Fraud Detection and Investigation Platform. Combines machine learning
              inference with TreeSHAP explainability for high-precision transaction risk scoring.
            </p>

            <div className="flex items-center gap-2 text-[11px] font-mono text-slate-500">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              <span>Production Pipeline v2.1.0 • Calibrated Threshold 0.35</span>
            </div>
          </div>

          {/* Quick Navigation Links */}
          <div className="md:col-span-3">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white mb-4">
              Navigation
            </h4>
            <ul className="space-y-2.5 text-xs font-mono text-slate-400">
              <li>
                <a href="#overview" className="hover:text-cyan-300 transition-colors">
                  Product Overview
                </a>
              </li>
              <li>
                <a href="#workflow" className="hover:text-cyan-300 transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#capabilities" className="hover:text-cyan-300 transition-colors">
                  Capabilities Matrix
                </a>
              </li>
              <li>
                <a href="#technology" className="hover:text-cyan-300 transition-colors">
                  Technology Stack
                </a>
              </li>
              <li>
                <Link href="/boot" className="hover:text-cyan-300 transition-colors text-cyan-400">
                  Launch Console →
                </Link>
              </li>
            </ul>
          </div>

          {/* Architecture Details */}
          <div className="md:col-span-4">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-white mb-4">
              Intelligence Architecture
            </h4>
            <div className="p-4 rounded-xl bg-slate-950 border border-white/5 space-y-2 text-[11px] font-mono text-slate-400">
              <div className="flex justify-between">
                <span>Model Engine:</span>
                <span className="text-cyan-300">XGBoost Extreme Classifier</span>
              </div>
              <div className="flex justify-between">
                <span>Explainability:</span>
                <span className="text-cyan-300">TreeSHAP Log-Odds Margin</span>
              </div>
              <div className="flex justify-between">
                <span>Backend Framework:</span>
                <span className="text-slate-300">FastAPI Async (Uvicorn)</span>
              </div>
              <div className="flex justify-between">
                <span>Primary Datastore:</span>
                <span className="text-slate-300">Supabase PostgreSQL (RLS)</span>
              </div>
              <div className="flex justify-between">
                <span>Fallback Datastore:</span>
                <span className="text-slate-300">SQLite Offline Replica</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Attribution */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs font-mono text-slate-500 gap-4">
          <div>
            © {new Date().getFullYear()} Fraud Sentinel. AI-Powered Financial Fraud Detection System.
          </div>
          <div className="flex items-center gap-6">
            <button
              onClick={scrollToTop}
              className="flex items-center gap-1.5 hover:text-cyan-300 transition-colors"
            >
              <span>Back to Top</span>
              <ArrowUp className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
}
