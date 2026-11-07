'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ShieldAlert,
  ShieldCheck,
  Zap,
  Info,
  Sliders,
  Play,
  RotateCw,
} from 'lucide-react';
import { Transaction, FraudAnalysis } from '@/types';

interface FraudProbabilityMatrixProps {
  analysis: FraudAnalysis | null;
  selectedTransaction: Transaction | null;
  threshold?: number;
  onSimulate: (scenario: 'random' | 'fraud' | 'legit') => Promise<void>;
  simulating: boolean;
}

export default function FraudProbabilityMatrix({
  analysis,
  selectedTransaction,
  threshold = 0.35,
  onSimulate,
  simulating,
}: FraudProbabilityMatrixProps) {
  const [simulationScenario, setSimulationScenario] = useState<'random' | 'fraud' | 'legit'>(
    'random'
  );

  const prob = analysis?.fraudProbability ?? (selectedTransaction ? selectedTransaction.fraudScore / 100 : 0);
  const percent = (prob * 100).toFixed(1);
  const thresholdPercent = (threshold * 100).toFixed(0);
  const isFlagged = prob >= threshold || selectedTransaction?.isFlagged || selectedTransaction?.status === 'flagged';
  const riskLevel = analysis?.riskLevel || (prob >= 0.6 ? 'CRITICAL' : prob >= 0.35 ? 'HIGH' : prob >= 0.25 ? 'MEDIUM' : 'LOW');

  // Gauge calculation (radial arc)
  const radius = 74;
  const circumference = 2 * Math.PI * radius;
  // Arc angle of 260 degrees
  const arcLength = circumference * (260 / 360);
  const strokeDashoffset = arcLength - (arcLength * Math.min(100, Math.max(0, prob * 100))) / 100;

  const getRiskTheme = () => {
    if (riskLevel === 'CRITICAL') {
      return {
        color: 'text-rose-400',
        stroke: '#f43f5e',
        badgeBg: 'bg-rose-500/15 text-rose-300 border-rose-500/40',
        label: 'CRITICAL THREAT',
      };
    }
    if (riskLevel === 'HIGH') {
      return {
        color: 'text-amber-400',
        stroke: '#f59e0b',
        badgeBg: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
        label: 'HIGH SUSPICION',
      };
    }
    if (riskLevel === 'MEDIUM') {
      return {
        color: 'text-yellow-300',
        stroke: '#eab308',
        badgeBg: 'bg-yellow-500/10 text-yellow-300 border-yellow-500/30',
        label: 'ELEVATED QUEUE',
      };
    }
    return {
      color: 'text-emerald-400',
      stroke: '#10b981',
      badgeBg: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
      label: 'SECURE MATRIX',
    };
  };

  const theme = getRiskTheme();

  return (
    <div className="h-full rounded-2xl glass-panel border border-white/10 bg-void-950/70 p-5 flex flex-col justify-between select-none">
      {/* Top Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
            Fraud Probability Matrix
          </span>
        </div>
        <span
          className={`px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${theme.badgeBg}`}
        >
          {theme.label}
        </span>
      </div>

      {/* Main Radial Dial */}
      <div className="relative my-auto flex flex-col items-center justify-center py-2">
        <div className="relative w-48 h-48 flex items-center justify-center">
          <svg
            className="w-full h-full transform -rotate-130"
            viewBox="0 0 180 180"
          >
            {/* Background Arc Track */}
            <circle
              cx="90"
              cy="90"
              r={radius}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="12"
              fill="none"
              strokeDasharray={`${arcLength} ${circumference}`}
              strokeLinecap="round"
            />

            {/* Threshold Marker Indicator */}
            <circle
              cx="90"
              cy="90"
              r={radius}
              stroke="rgba(245, 158, 11, 0.4)"
              strokeWidth="14"
              fill="none"
              strokeDasharray={`3 ${circumference}`}
              strokeDashoffset={arcLength - (arcLength * threshold * 100) / 100}
              strokeLinecap="round"
            />

            {/* Dynamic Active Probability Arc */}
            <motion.circle
              cx="90"
              cy="90"
              r={radius}
              stroke={theme.stroke}
              strokeWidth="12"
              fill="none"
              strokeDasharray={`${arcLength} ${circumference}`}
              initial={{ strokeDashoffset: arcLength }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: [0.16, 1, 0.3, 1] }}
              strokeLinecap="round"
              style={{
                filter: `drop-shadow(0 0 12px ${theme.stroke}60)`,
              }}
            />
          </svg>

          {/* Center Numerical Score Display */}
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-3xl sm:text-4xl font-bold font-mono text-white tracking-tight">
              {percent}%
            </span>
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mt-0.5">
              ESTIMATED RISK
            </span>
            <div className="mt-1 flex items-center gap-1 text-[10px] font-mono text-slate-500">
              <span>Threshold:</span>
              <span className="text-amber-400 font-semibold">{thresholdPercent}%</span>
            </div>
          </div>
        </div>

        {/* Flagged Status Banner */}
        <div className="mt-1">
          {isFlagged ? (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/15 border border-rose-500/40 text-rose-300 text-[11px] font-mono">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
              <span>DECISION: FLAGGED FOR REVIEW</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-[11px] font-mono">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>DECISION: AUTOMATED CLEARANCE</span>
            </div>
          )}
        </div>
      </div>

      {/* Advisory Note */}
      <div className="p-2.5 rounded-xl bg-slate-900/60 border border-white/5 flex items-start gap-2 mb-3">
        <Info className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
        <p className="text-[10px] font-mono text-slate-400 leading-relaxed">
          Probability is a statistical anomaly estimate calibrated on stratified validation holdouts. Final
          fraud confirmation requires human analyst adjudication.
        </p>
      </div>

      {/* Real-time ML Inference Simulator */}
      <div className="pt-3 border-t border-white/10">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-mono uppercase text-slate-400 flex items-center gap-1">
            <Zap className="w-3 h-3 text-cyan-400" />
            Live Inference Simulation
          </span>
          <select
            value={simulationScenario}
            onChange={(e) =>
              setSimulationScenario(e.target.value as 'random' | 'fraud' | 'legit')
            }
            className="bg-slate-900 border border-white/10 rounded px-2 py-0.5 text-[10px] font-mono text-slate-300 focus:outline-none focus:border-cyan-400"
          >
            <option value="random">Random Sample</option>
            <option value="fraud">High Risk Anomaly</option>
            <option value="legit">Legitimate Domestic</option>
          </select>
        </div>

        <button
          onClick={() => onSimulate(simulationScenario)}
          disabled={simulating}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-r from-cyan-500/20 via-cyan-500/30 to-amber-500/20 hover:from-cyan-500/30 hover:to-amber-500/30 border border-cyan-400/40 text-cyan-200 text-xs font-mono font-semibold tracking-wider uppercase transition-all disabled:opacity-50"
        >
          {simulating ? (
            <>
              <RotateCw className="w-3.5 h-3.5 animate-spin text-cyan-300" />
              <span>Running Inference & TreeSHAP...</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 text-cyan-300" />
              <span>Simulate Real Transaction</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

