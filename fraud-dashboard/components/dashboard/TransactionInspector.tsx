'use client';

import { useState, useEffect } from 'react';
import {
  FileText,
  CreditCard,
  MapPin,
  Calendar,
  Shield,
  Save,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
} from 'lucide-react';
import { Transaction, ReviewStatus } from '@/types';
import { updateTransactionReview } from '@/lib/api';

interface TransactionInspectorProps {
  transaction: Transaction | null;
  onUpdateSuccess: (updated: Transaction) => void;
}

export default function TransactionInspector({
  transaction,
  onUpdateSuccess,
}: TransactionInspectorProps) {
  const [reviewStatus, setReviewStatus] = useState<ReviewStatus>('PENDING');
  const [analystNotes, setAnalystNotes] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Sync state when selected transaction changes
  useEffect(() => {
    if (transaction) {
      setReviewStatus(transaction.reviewStatus || 'PENDING');
      setAnalystNotes(transaction.analystNotes || '');
      setSaveSuccess(false);
      setErrorMsg(null);
    }
  }, [transaction]);

  if (!transaction) {
    return (
      <div className="h-full rounded-2xl glass-panel border border-white/10 bg-void-950/70 p-6 flex flex-col items-center justify-center text-center text-slate-500 font-mono text-xs select-none">
        <FileText className="w-8 h-8 text-slate-600 mb-2" />
        <span className="font-semibold text-slate-400 mb-1">
          No Transaction Selected
        </span>
        <p className="text-[11px] text-slate-500 max-w-sm">
          Select a transaction from the monitoring feed above to inspect its metadata, feature
          breakdown, and record your analyst audit decision.
        </p>
      </div>
    );
  }

  const handleSaveReview = async () => {
    setSaving(true);
    setErrorMsg(null);
    setSaveSuccess(false);
    try {
      const updated = await updateTransactionReview(
        transaction.id,
        reviewStatus,
        analystNotes,
        'Lead Fraud Investigator'
      );
      setSaveSuccess(true);
      onUpdateSuccess(updated);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      console.error('Failed to save review:', err);
      setErrorMsg(err.message || 'Could not update review status.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full rounded-2xl glass-panel border border-white/10 bg-void-950/70 p-5 flex flex-col justify-between select-none">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-white/10">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              Transaction Investigation Workspace
            </span>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-white/10 text-slate-300">
            ID: {transaction.id.slice(0, 16)}...
          </span>
        </div>

        {/* 2-Column Metadata Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5">
            <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
              MERCHANT
            </span>
            <span className="text-xs font-semibold text-white font-sans truncate block">
              {transaction.merchant}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5">
            <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
              AMOUNT
            </span>
            <span className="text-sm font-bold text-cyan-300 font-mono">
              ${transaction.amount.toFixed(2)} USD
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5">
            <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
              CATEGORY / CARD
            </span>
            <span className="text-xs text-slate-300 font-mono truncate block">
              {transaction.category} • ****{transaction.cardLast4}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/60 border border-white/5">
            <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">
              TIMESTAMP
            </span>
            <span className="text-[11px] text-slate-300 font-mono">
              {new Date(transaction.timestamp).toLocaleString([], {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        </div>

        {/* Audit Review Form */}
        <div className="space-y-3 pt-2">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <label className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300">
              Analyst Disposition & Audit Action:
            </label>
            <select
              value={reviewStatus}
              onChange={(e) => setReviewStatus(e.target.value as ReviewStatus)}
              className="bg-slate-900 border border-white/10 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-400"
            >
              <option value="PENDING">PENDING REVIEW</option>
              <option value="UNDER_REVIEW">UNDER INVESTIGATION</option>
              <option value="CONFIRMED_FRAUD">CONFIRMED FRAUD</option>
              <option value="LEGITIMATE">CONFIRMED LEGITIMATE</option>
              <option value="ESCALATED">ESCALATED TO RISK COMMITTEE</option>
            </select>
          </div>

          <div>
            <textarea
              rows={3}
              value={analystNotes}
              onChange={(e) => setAnalystNotes(e.target.value)}
              placeholder="Record investigation notes, merchant callback verification, device heuristics, or rationale..."
              className="w-full bg-slate-900/90 border border-white/10 rounded-xl p-3 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400 custom-scroll resize-none"
            />
          </div>

          {errorMsg && (
            <div className="p-2 rounded-lg bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs font-mono">
              {errorMsg}
            </div>
          )}

          {saveSuccess && (
            <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs font-mono flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              <span>Audit decision persisted to database successfully.</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-4 mt-3 border-t border-white/10 flex items-center justify-between">
        <span className="text-[11px] font-mono text-slate-400">
          Last reviewed: {transaction.reviewedBy || 'Unassigned'}
        </span>

        <button
          onClick={handleSaveReview}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-600 hover:from-cyan-400 hover:to-sky-500 text-slate-950 font-mono font-bold text-xs uppercase tracking-wider transition-all disabled:opacity-50"
        >
          {saving ? (
            <>
              <RotateCw className="w-3.5 h-3.5 animate-spin" />
              <span>Persisting...</span>
            </>
          ) : (
            <>
              <Save className="w-3.5 h-3.5" />
              <span>Save Audit Decision</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

