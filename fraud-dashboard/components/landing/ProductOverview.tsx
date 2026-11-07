'use client';

import { motion } from 'framer-motion';
import { Cpu, Eye, FileText, CheckCircle2, ChevronRight, BarChart3 } from 'lucide-react';

const PILLARS = [
  {
    icon: Cpu,
    title: 'Intelligent Detection',
    subtitle: 'High-Precision Machine Learning',
    description:
      'Analyze transaction patterns using machine learning to identify potentially fraudulent activity.',
    points: [
      'XGBoost gradient-boosted ensemble trained on real financial data',
      'Transforms 35 raw behavioral features into 131 encoded model inputs',
      'Cost-sensitive loss weighting calibrated to handle extreme imbalance',
      'Sub-15ms real-time inference latency for high-velocity transaction flows',
    ],
    accent: 'cyan',
    badge: 'MODEL INFERENCE',
    glow: 'from-cyan-500/10 to-transparent',
    border: 'border-cyan-500/30',
  },
  {
    icon: Eye,
    title: 'Explainable AI',
    subtitle: 'Transparent TreeSHAP Attribution',
    description:
      'Understand why a transaction receives a particular fraud prediction through SHAP feature contributions.',
    points: [
      'Game-theoretic TreeSHAP decomposes raw margin log-odds contributions',
      'Identifies exact risk-increasing vs. risk-reducing feature drivers',
      'Zero black-box decisions: every prediction maps to verifiable factors',
      'Automated natural language summaries for fast analyst comprehension',
    ],
    accent: 'emerald',
    badge: 'GAME-THEORETIC SHAP',
    glow: 'from-emerald-500/10 to-transparent',
    border: 'border-emerald-500/30',
  },
  {
    icon: FileText,
    title: 'Risk Investigation',
    subtitle: 'Human-in-the-Loop Analyst Hub',
    description:
      'Review suspicious transactions, understand risk factors and record analyst decisions.',
    points: [
      'Tiered risk bands: Low (<25%), Medium (25–60%), and High/Critical (≥60%)',
      'Standardized decision threshold at 0.35 optimized for peak fraud recall',
      'Structured audit workflow: Confirmed Fraud, Legitimate, or Escalated',
      'Audit logging persisted directly to Supabase PostgreSQL with SQLite fallback',
    ],
    accent: 'amber',
    badge: 'AUDIT & GOVERNANCE',
    glow: 'from-amber-500/10 to-transparent',
    border: 'border-amber-500/30',
  },
];

export default function ProductOverview() {
  return (
    <section id="overview" className="py-24 relative border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-white/10 text-slate-300 text-[10px] font-mono tracking-widest uppercase mb-4">
            <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
            <span>ARCHITECTURE OVERVIEW</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-4">
            INTELLIGENCE BEHIND EVERY TRANSACTION
          </h2>
          <p className="text-base text-slate-400 font-sans">
            Three interconnected pillars that transform high-velocity financial transaction streams into
            transparent, explainable intelligence.
          </p>
        </div>

        {/* 3 Pillar Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {PILLARS.map((pillar, idx) => {
            const Icon = pillar.icon;
            return (
              <div
                key={pillar.title}
                className={`p-7 rounded-2xl glass-panel border ${pillar.border} bg-gradient-to-b ${pillar.glow} flex flex-col justify-between hover:border-opacity-60 transition-all`}
              >
                <div>
                  {/* Badge & Icon */}
                  <div className="flex items-center justify-between mb-6">
                    <div className="w-12 h-12 rounded-xl bg-slate-900/90 border border-white/10 flex items-center justify-center">
                      <Icon className="w-6 h-6 text-cyan-300" />
                    </div>
                    <span className="text-[10px] font-mono tracking-wider uppercase px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-slate-300">
                      {pillar.badge}
                    </span>
                  </div>

                  <h3 className="text-xl font-bold text-white mb-1 tracking-tight">
                    {pillar.title}
                  </h3>
                  <p className="text-xs font-mono text-cyan-300/80 mb-4 uppercase tracking-wider">
                    {pillar.subtitle}
                  </p>
                  <p className="text-sm text-slate-300/90 leading-relaxed mb-6 font-sans">
                    {pillar.description}
                  </p>

                  {/* Bullet points */}
                  <ul className="space-y-3 mb-6">
                    {pillar.points.map((pt) => (
                      <li key={pt} className="flex items-start gap-2.5 text-xs text-slate-400 font-sans">
                        <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-4 border-t border-white/5 flex items-center justify-between text-xs font-mono text-slate-400">
                  <span>Pillar 0{idx + 1}</span>
                  <span className="text-cyan-400 flex items-center gap-1">
                    Production Verified <ChevronRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
