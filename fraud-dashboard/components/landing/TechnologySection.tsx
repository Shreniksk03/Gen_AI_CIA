'use client';

import { motion } from 'framer-motion';
import { Terminal, Database, Code, Cpu, Shield, Sparkles, Layers, Box } from 'lucide-react';

const TECH_STACK = [
  {
    name: 'Python 3.12',
    role: 'Core Scientific Runtime',
    detail: 'Powers model scoring, numerical array matrix operations, and asynchronous API workers.',
    category: 'Backend & Data Science',
    icon: Terminal,
    tag: 'Python runtime',
  },
  {
    name: 'XGBoost 2.1.0',
    role: 'Gradient Boosted Trees',
    detail: 'Extreme Gradient Boosting classifier optimized with cost-sensitive scale_pos_weight.',
    category: 'Machine Learning',
    icon: Cpu,
    tag: 'XGBClassifier',
  },
  {
    name: 'SHAP (Explainable AI)',
    role: 'TreeExplainer Engine',
    detail: 'Decomposes raw margin space log-odds into exact game-theoretic Shapley attributions.',
    category: 'Model Interpretability',
    icon: Sparkles,
    tag: 'TreeExplainer',
  },
  {
    name: 'Scikit-Learn',
    role: 'Feature Preprocessing',
    detail: 'ColumnTransformer applying StandardScaler on 26 numericals and OneHotEncoder on 9 categoricals.',
    category: 'Machine Learning',
    icon: Layers,
    tag: 'ColumnTransformer',
  },
  {
    name: 'FastAPI',
    role: 'Asynchronous REST Service',
    detail: 'High-throughput async Python API with Pydantic v2 schemas and strict CORS isolation.',
    category: 'API Architecture',
    icon: Code,
    tag: 'FastAPI / Uvicorn',
  },
  {
    name: 'Next.js 14 (App Router)',
    role: 'Modern Web Framework',
    detail: 'React Server Components, client-side hydration, and dynamic Three.js canvas integration.',
    category: 'Frontend Engineering',
    icon: Box,
    tag: 'Next.js / React 18',
  },
  {
    name: 'Supabase',
    role: 'Cloud DB & Storage',
    detail: 'PostgreSQL database with Row Level Security (RLS) and backend service-role authorization.',
    category: 'Cloud Infrastructure',
    icon: Database,
    tag: 'Supabase BaaS',
  },
  {
    name: 'PostgreSQL + SQLite',
    role: 'Relational & Fallback DB',
    detail: 'Transactional storage with automatic offline fallback to local SQLite when cloud is offline.',
    category: 'Data Persistence',
    icon: Shield,
    tag: 'PostgreSQL / SQLite',
  },
];

export default function TechnologySection() {
  return (
    <section id="technology" className="py-24 relative border-t border-white/5 bg-void-950/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-white/10 text-slate-300 text-[10px] font-mono tracking-widest uppercase mb-4">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>TECHNOLOGY FOUNDATION</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-4">
            PRODUCTION-GRADE TECHNOLOGY STACK
          </h2>
          <p className="text-base text-slate-400 font-sans">
            Built on mathematically verified algorithms, resilient asynchronous microservices, and modern web
            architecture.
          </p>
        </div>

        {/* Tech Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {TECH_STACK.map((tech, idx) => {
            const Icon = tech.icon;
            return (
              <div
                key={tech.name}
                className="p-5 rounded-2xl glass-panel border border-white/10 hover:border-cyan-500/40 bg-void-950/80 flex flex-col justify-between group transition-all"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-slate-900 border border-white/10 flex items-center justify-center group-hover:border-cyan-400/50 transition-colors">
                      <Icon className="w-5 h-5 text-cyan-400" />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                      {tech.tag}
                    </span>
                  </div>

                  <h3 className="text-base font-bold text-white mb-0.5 group-hover:text-cyan-300 transition-colors">
                    {tech.name}
                  </h3>
                  <div className="text-[11px] font-mono text-cyan-400/80 mb-2 uppercase tracking-wide">
                    {tech.role}
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed font-sans mb-4">
                    {tech.detail}
                  </p>
                </div>

                <div className="pt-3 border-t border-white/5 text-[10px] font-mono text-slate-500">
                  <span>{tech.category}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
