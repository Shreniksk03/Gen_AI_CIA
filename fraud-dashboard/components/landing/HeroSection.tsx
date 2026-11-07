'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  ShieldAlert,
  ShieldCheck,
  Cpu,
  Layers,
  ArrowRight,
  TrendingUp,
  Fingerprint,
  Zap,
} from 'lucide-react';

export default function HeroSection() {
  return (
    <section className="relative min-h-[calc(100vh-4rem)] flex items-center justify-center pt-8 pb-16 overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Headlines & Call to Actions */}
          <div className="lg:col-span-7 flex flex-col items-start text-left">
            {/* Pill Tag */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-950/40 border border-cyan-500/30 text-cyan-300 text-[11px] font-mono tracking-widest uppercase mb-6 shadow-[0_0_15px_rgba(56,189,248,0.15)]">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <span>AI-POWERED FINANCIAL INTELLIGENCE</span>
            </div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-white leading-[1.1] mb-6">
              See Through Fraud.{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-amber-300">
                Act Before It Happens.
              </span>
            </h1>

            {/* Supporting Description */}
            <p className="text-base sm:text-lg text-slate-300/90 leading-relaxed max-w-2xl mb-8 font-sans">
              Fraud Sentinel is an intelligent financial transaction monitoring platform that uses machine
              learning and explainable AI to detect suspicious activity, assess transaction risk and help
              analysts make informed decisions.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap items-center gap-4 mb-12">
              <Link
                href="/boot"
                className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-slate-950 font-mono font-bold tracking-wider text-xs uppercase shadow-[0_0_30px_rgba(56,189,248,0.4)] transition-all transform hover:-translate-y-0.5 active:translate-y-0"
              >
                <span>LAUNCH CONSOLE</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <a
                href="#overview"
                className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-slate-900/80 hover:bg-slate-800/80 border border-white/10 hover:border-cyan-500/40 text-slate-300 hover:text-white font-mono text-xs tracking-wider uppercase transition-all"
              >
                <span>EXPLORE PLATFORM</span>
              </a>
            </div>

            {/* Production Telemetry Badges */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full pt-6 border-t border-white/10">
              <div>
                <span className="block text-2xl font-bold font-mono text-cyan-300">131</span>
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                  Encoded Features
                </span>
              </div>
              <div>
                <span className="block text-2xl font-bold font-mono text-emerald-400">TreeSHAP</span>
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                  Attribution Space
                </span>
              </div>
              <div>
                <span className="block text-2xl font-bold font-mono text-amber-400">0.35</span>
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                  Calibrated Threshold
                </span>
              </div>
              <div>
                <span className="block text-2xl font-bold font-mono text-sky-400">&lt;15ms</span>
                <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                  Inference Latency
                </span>
              </div>
            </div>
          </div>

          {/* Right Column: Visual Composition with Telemetry Badges */}
          <div className="lg:col-span-5 relative flex items-center justify-center">
            {/* Visual Glass Frame with Floating Transaction Cards */}
            <div className="relative w-full max-w-md p-6 rounded-2xl glass-panel border border-cyan-500/20 shadow-[0_20px_50px_rgba(0,0,0,0.8)] backdrop-blur-2xl">
              {/* Card Header */}
              <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
                <div className="flex items-center gap-2">
                  <Fingerprint className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-mono tracking-wider uppercase text-slate-300">
                    Live Stream Telemetry
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  MONITORING
                </span>
              </div>

              {/* Sample Live Transaction Stream Cards */}
              <div className="space-y-3">
                {/* High Risk Anomaly Card */}
                <div className="p-3.5 rounded-xl bg-void-950/80 border border-rose-500/30 relative overflow-hidden">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <ShieldAlert className="w-4 h-4 text-rose-400" />
                      <span className="text-xs font-mono font-medium text-slate-200">
                        International POS Terminal
                      </span>
                    </div>
                    <span className="text-xs font-mono font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30">
                      78.4% HIGH RISK
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>$1,850.00 USD</span>
                    <span className="text-amber-400/90">+0.98 SHAP: Cross-Border</span>
                  </div>
                </div>

                {/* Normal Cleared Transaction Card */}
                <div className="p-3.5 rounded-xl bg-void-950/80 border border-emerald-500/25 relative overflow-hidden">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-mono font-medium text-slate-200">
                        Domestic Grocery Store
                      </span>
                    </div>
                    <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/25">
                      1.2% SECURE
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>$42.50 USD</span>
                    <span className="text-cyan-400/90">-1.18 SHAP: Local Radius</span>
                  </div>
                </div>

                {/* Elevated Review Card */}
                <div className="p-3.5 rounded-xl bg-void-950/80 border border-amber-500/30 relative overflow-hidden">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-amber-400" />
                      <span className="text-xs font-mono font-medium text-slate-200">
                        High Velocity Electronics
                      </span>
                    </div>
                    <span className="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30">
                      44.8% REVIEW
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                    <span>$640.00 USD</span>
                    <span className="text-slate-400">Threshold Exceeded (&gt;35%)</span>
                  </div>
                </div>
              </div>

              {/* Explainer Footer Note */}
              <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                  XGBoost Cost-Sensitive Matrix
                </span>
                <span className="text-cyan-300">v2.1.0-production</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
