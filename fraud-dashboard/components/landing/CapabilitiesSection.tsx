'use client';

import { motion } from 'framer-motion';
import {
  CheckCircle2,
  Clock,
  Sparkles,
  Shield,
  Layers,
  Database,
  Sliders,
  FileCheck,
  Search,
  Radio,
} from 'lucide-react';

interface CapabilityItem {
  title: string;
  category: string;
  description: string;
  status: 'IMPLEMENTED' | 'PLANNED';
  icon: any;
}

const CAPABILITIES: CapabilityItem[] = [
  {
    title: 'XGBoost ML Fraud Inference',
    category: 'Machine Learning',
    description:
      'Production gradient-boosted decision tree classifier trained on 35 input features and 131 encoded dimensions.',
    status: 'IMPLEMENTED',
    icon: Shield,
  },
  {
    title: 'Game-Theoretic SHAP Explainability',
    category: 'Model Interpretability',
    description:
      'Exact TreeSHAP attributions decomposing raw margin log-odds into positive and negative risk contributors.',
    status: 'IMPLEMENTED',
    icon: Sparkles,
  },
  {
    title: 'Calibrated Risk Classification',
    category: 'Decision Intelligence',
    description:
      'Tiered risk assignment (Low <25%, Medium 25–60%, High/Critical ≥60%) with empirical 0.35 thresholding.',
    status: 'IMPLEMENTED',
    icon: Sliders,
  },
  {
    title: 'Analyst Investigation & Review',
    category: 'Human Governance',
    description:
      'Interactive audit workflow allowing investigators to set review status, record investigation notes, and save audit trails.',
    status: 'IMPLEMENTED',
    icon: FileCheck,
  },
  {
    title: 'Transaction Monitoring & Filtering',
    category: 'Operational Monitoring',
    description:
      'Search, filter by risk band, paginate, and inspect stored predictions directly from the centralized console.',
    status: 'IMPLEMENTED',
    icon: Search,
  },
  {
    title: 'Dual Database Persistence',
    category: 'Data Architecture',
    description:
      'Supabase PostgreSQL remote storage with automated local SQLite fallback ensuring uninterrupted transaction logging.',
    status: 'IMPLEMENTED',
    icon: Database,
  },
  {
    title: 'Live Kafka Event Streaming Ingestion',
    category: 'Distributed Systems',
    description:
      'Sub-millisecond pub/sub streaming ingest from banking payment switches across distributed multi-region clusters.',
    status: 'PLANNED',
    icon: Radio,
  },
  {
    title: 'Autonomous Rule Synthesis Engine',
    category: 'Adaptive Intelligence',
    description:
      'Automated extraction of high-precision declarative velocity heuristics synthesized from recent confirmed fraud clusters.',
    status: 'PLANNED',
    icon: Layers,
  },
];

export default function CapabilitiesSection() {
  return (
    <section id="capabilities" className="py-24 relative border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-white/10 text-slate-300 text-[10px] font-mono tracking-widest uppercase mb-4">
            <Shield className="w-3.5 h-3.5 text-cyan-400" />
            <span>PLATFORM CAPABILITIES MATRIX</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-4">
            ENGINEERED FOR RIGOROUS INVESTIGATION
          </h2>
          <p className="text-base text-slate-400 font-sans">
            Transparently distinguishing verified production systems from planned enterprise scalability
            enhancements.
          </p>
        </div>

        {/* Capabilities Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {CAPABILITIES.map((cap, idx) => {
            const Icon = cap.icon;
            const isImplemented = cap.status === 'IMPLEMENTED';
            return (
              <div
                key={cap.title}
                className={`p-5 rounded-2xl glass-panel border flex flex-col justify-between transition-all ${
                  isImplemented
                    ? 'border-white/10 hover:border-cyan-500/40 bg-void-950/60'
                    : 'border-white/5 bg-void-950/20 opacity-75 hover:opacity-100'
                }`}
              >
                <div>
                  {/* Status Tag */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-9 h-9 rounded-xl bg-slate-900 border border-white/10 flex items-center justify-center">
                      <Icon
                        className={`w-4 h-4 ${
                          isImplemented ? 'text-cyan-400' : 'text-slate-500'
                        }`}
                      />
                    </div>
                    <span
                      className={`text-[9px] font-mono tracking-wider uppercase px-2 py-0.5 rounded-full border ${
                        isImplemented
                          ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                          : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                    >
                      {isImplemented ? 'VERIFIED ACTIVE' : 'ROADMAP'}
                    </span>
                  </div>

                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block mb-1">
                    {cap.category}
                  </span>
                  <h3 className="text-sm font-bold text-white mb-2 leading-snug">
                    {cap.title}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed font-sans mb-4">
                    {cap.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-white/5 flex items-center gap-1.5 text-[10px] font-mono">
                  {isImplemented ? (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-slate-300">FastAPI & Supabase Connected</span>
                    </>
                  ) : (
                    <>
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span className="text-slate-500">Planned Architecture</span>
                    </>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
