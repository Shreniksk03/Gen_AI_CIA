'use client';

import { motion } from 'framer-motion';
import {
  CreditCard,
  Binary,
  Cpu,
  Eye,
  AlertTriangle,
  UserCheck,
  ArrowRight,
  GitCommit,
} from 'lucide-react';

const WORKFLOW_STEPS = [
  {
    step: '01',
    title: 'Transaction Input',
    icon: CreditCard,
    short: 'Raw Telemetry Ingestion',
    description:
      'Transaction stream captures merchant details, amounts, device telemetry, card metadata, and spatial coordinates.',
    tech: 'Pydantic Payload Validation',
  },
  {
    step: '02',
    title: 'Feature Processing',
    icon: Binary,
    short: '35 → 131 Dimensions',
    description:
      'StandardScaler handles 26 numericals; OneHotEncoder maps 9 categorical dimensions with zero-leakage pipeline rules.',
    tech: 'Scikit-Learn ColumnTransformer',
  },
  {
    step: '03',
    title: 'ML Prediction',
    icon: Cpu,
    short: 'XGBoost Classification',
    description:
      'Trained ensemble calculates probability with cost-sensitive pos_weight=47.66 addressing class imbalance.',
    tech: 'XGBClassifier Matrix',
  },
  {
    step: '04',
    title: 'SHAP Explanation',
    icon: Eye,
    short: 'TreeExplainer Decomposition',
    description:
      'Decomposes model decision into additive log-odds game-theoretic values for both positive and negative drivers.',
    tech: 'Raw Margin Space Attribution',
  },
  {
    step: '05',
    title: 'Risk Assessment',
    icon: AlertTriangle,
    short: 'Decision Calibration (0.35)',
    description:
      'Applies stratified validation threshold (0.35) and segments scores into Low, Medium, High, and Critical risk bands.',
    tech: 'Empirical PR-AUC Optimization',
  },
  {
    step: '06',
    title: 'Analyst Review',
    icon: UserCheck,
    short: 'Human-in-the-Loop Audit',
    description:
      'Fraud investigators inspect top SHAP factors, adjust disposition (Confirmed Fraud/Legit), and log audit history.',
    tech: 'Supabase Audit Records',
  },
];

export default function WorkflowSection() {
  return (
    <section id="workflow" className="py-24 relative border-t border-white/5 bg-void-950/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-white/10 text-slate-300 text-[10px] font-mono tracking-widest uppercase mb-4">
            <GitCommit className="w-3.5 h-3.5 text-cyan-400" />
            <span>PIPELINE EXECUTION FLOW</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-4">
            HOW FRAUD SENTINEL WORKS
          </h2>
          <p className="text-base text-slate-400 font-sans">
            An end-to-end mathematical and human-in-the-loop pipeline executing from transaction arrival to final
            adjudication.
          </p>
        </div>

        {/* 6-Step Visual Workflow Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative">
          {WORKFLOW_STEPS.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                className="relative p-6 rounded-2xl glass-panel border border-white/10 hover:border-cyan-500/40 transition-all flex flex-col justify-between group"
              >
                <div>
                  {/* Step header */}
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-2xl font-mono font-bold text-cyan-400/80 group-hover:text-cyan-300 transition-colors">
                      {item.step}
                    </span>
                    <div className="w-10 h-10 rounded-xl bg-slate-900 border border-white/10 flex items-center justify-center group-hover:border-cyan-400/50 transition-colors">
                      <Icon className="w-5 h-5 text-slate-300 group-hover:text-cyan-300 transition-colors" />
                    </div>
                  </div>

                  <h3 className="text-base font-bold text-white mb-1">{item.title}</h3>
                  <div className="text-[11px] font-mono text-cyan-300/80 uppercase tracking-wider mb-3">
                    {item.short}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed font-sans mb-4">
                    {item.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[10px] font-mono text-slate-500">
                  <span className="text-slate-400">{item.tech}</span>
                  {idx < WORKFLOW_STEPS.length - 1 && (
                    <span className="text-cyan-400 hidden lg:inline">
                      <ArrowRight className="w-3 h-3" />
                    </span>
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
