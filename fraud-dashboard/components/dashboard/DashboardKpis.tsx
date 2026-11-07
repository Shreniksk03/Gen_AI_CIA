'use client';

import { Activity, ShieldAlert, CheckCircle2, Clock, HelpCircle } from 'lucide-react';
import { AnalyticsData } from '@/types';

interface DashboardKpisProps {
  analytics: AnalyticsData | null;
  loading: boolean;
}

export default function DashboardKpis({ analytics, loading }: DashboardKpisProps) {
  const total = analytics?.total_transactions ?? 0;
  const flagged = analytics?.total_flagged_transactions ?? 0;
  const confirmed = analytics?.total_confirmed_fraud ?? 0;
  const pending = analytics?.transactions_awaiting_review ?? 0;

  const flaggedPercent = total > 0 ? ((flagged / total) * 100).toFixed(1) : '0.0';
  const confirmedPercent = total > 0 ? ((confirmed / total) * 100).toFixed(1) : '0.0';

  const cards = [
    {
      title: 'TOTAL TRANSACTIONS',
      value: total,
      subtext: analytics?.data_source_label || 'Indexed in SQLite Fallback',
      icon: Activity,
      color: 'text-cyan-300',
      badge: 'MONITORED',
      badgeStyle: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
      border: 'border-cyan-500/20',
      tooltip: 'Total historical transactions evaluated by the model and stored in the database.',
    },
    {
      title: 'FLAGGED ANOMALIES',
      value: flagged,
      subtext: `${flaggedPercent}% of transactions exceeding τ = 0.35`,
      icon: ShieldAlert,
      color: 'text-rose-400',
      badge: 'MODEL FLAGGED',
      badgeStyle: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
      border: 'border-rose-500/20',
      tooltip: 'Transactions flagged by the ML model where predicted fraud probability ≥ 0.35.',
    },
    {
      title: 'CONFIRMED FRAUD',
      value: confirmed,
      subtext: `${confirmedPercent}% validated by fraud analysts`,
      icon: CheckCircle2,
      color: 'text-amber-400',
      badge: 'ANALYST CONFIRMED',
      badgeStyle: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
      border: 'border-amber-500/20',
      tooltip: 'Transactions manually reviewed and verified as true fraud by the investigation team.',
    },
    {
      title: 'PENDING INVESTIGATION',
      value: pending,
      subtext: 'Flagged transactions awaiting disposition',
      icon: Clock,
      color: 'text-sky-300',
      badge: 'QUEUE BACKLOG',
      badgeStyle: 'bg-sky-500/10 text-sky-300 border-sky-500/30',
      border: 'border-sky-500/20',
      tooltip: 'Flagged transactions that have not yet received an analyst adjudication.',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <div
            key={card.title}
            className={`p-5 rounded-2xl glass-panel border ${card.border} flex flex-col justify-between transition-all hover:border-opacity-60 bg-void-950/70`}
          >
            <div>
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono tracking-widest uppercase text-slate-400">
                  {card.title}
                </span>
                <span
                  className={`text-[9px] font-mono tracking-wider uppercase px-2 py-0.5 rounded-full border ${card.badgeStyle}`}
                >
                  {card.badge}
                </span>
              </div>

              {/* Metric Value */}
              <div className="flex items-baseline gap-3 mb-2">
                <span className={`text-3xl sm:text-4xl font-bold font-mono ${card.color}`}>
                  {loading ? '--' : card.value.toLocaleString()}
                </span>
                <Icon className={`w-5 h-5 ${card.color} opacity-80`} />
              </div>
            </div>

            {/* Subtitle / Supporting text */}
            <div className="pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span className="truncate">{card.subtext}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

