'use client';

import { useState, useMemo } from 'react';
import {
  Search,
  Filter,
  ArrowUpDown,
  ShieldAlert,
  ShieldCheck,
  Clock,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
} from 'lucide-react';
import { Transaction } from '@/types';

interface TransactionMonitoringFeedProps {
  transactions: Transaction[];
  selectedTransaction: Transaction | null;
  onSelectTransaction: (txn: Transaction) => void;
  loading: boolean;
  onRefresh: () => void;
}

type FilterOption =
  | 'ALL'
  | 'FLAGGED'
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL'
  | 'CONFIRMED_FRAUD'
  | 'PENDING';

type SortOption = 'RISK_DESC' | 'NEWEST' | 'AMOUNT_DESC';

export default function TransactionMonitoringFeed({
  transactions,
  selectedTransaction,
  onSelectTransaction,
  loading,
  onRefresh,
}: TransactionMonitoringFeedProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<FilterOption>('ALL');
  const [sortOption, setSortOption] = useState<SortOption>('NEWEST');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12;

  // Filter & Search
  const filteredTransactions = useMemo(() => {
    return transactions.filter((txn) => {
      // Search matching
      const query = searchQuery.toLowerCase().trim();
      if (query) {
        const matchId = txn.id.toLowerCase().includes(query);
        const matchMerchant = txn.merchant.toLowerCase().includes(query);
        const matchCategory = txn.category.toLowerCase().includes(query);
        const matchCard = txn.cardLast4.includes(query);
        if (!matchId && !matchMerchant && !matchCategory && !matchCard) {
          return false;
        }
      }

      // Filter matching
      if (activeFilter === 'ALL') return true;
      if (activeFilter === 'FLAGGED') return txn.status === 'flagged' || txn.isFlagged;
      if (activeFilter === 'LOW') return txn.analysis?.riskLevel === 'LOW';
      if (activeFilter === 'MEDIUM') return txn.analysis?.riskLevel === 'MEDIUM';
      if (activeFilter === 'HIGH') return txn.analysis?.riskLevel === 'HIGH';
      if (activeFilter === 'CRITICAL') return txn.analysis?.riskLevel === 'CRITICAL';
      if (activeFilter === 'CONFIRMED_FRAUD') return txn.reviewStatus === 'CONFIRMED_FRAUD';
      if (activeFilter === 'PENDING') return txn.reviewStatus === 'PENDING';
      return true;
    });
  }, [transactions, searchQuery, activeFilter]);

  // Sort
  const sortedTransactions = useMemo(() => {
    const list = [...filteredTransactions];
    if (sortOption === 'RISK_DESC') {
      list.sort((a, b) => b.fraudScore - a.fraudScore);
    } else if (sortOption === 'NEWEST') {
      list.sort(
        (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
    } else if (sortOption === 'AMOUNT_DESC') {
      list.sort((a, b) => b.amount - a.amount);
    }
    return list;
  }, [filteredTransactions, sortOption]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(sortedTransactions.length / pageSize));
  const pagedTransactions = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedTransactions.slice(start, start + pageSize);
  }, [sortedTransactions, currentPage, pageSize]);

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const getRiskBadge = (riskLevel?: string, score?: number) => {
    const level = riskLevel || (score && score >= 60 ? 'CRITICAL' : score && score >= 35 ? 'HIGH' : 'LOW');
    if (level === 'CRITICAL') {
      return {
        bg: 'bg-rose-500/15 text-rose-300 border-rose-500/40',
        text: 'CRITICAL',
      };
    }
    if (level === 'HIGH') {
      return {
        bg: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
        text: 'HIGH',
      };
    }
    if (level === 'MEDIUM') {
      return {
        bg: 'bg-yellow-500/10 text-yellow-300 border-yellow-500/30',
        text: 'MEDIUM',
      };
    }
    return {
      bg: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
      text: 'LOW',
    };
  };

  return (
    <div className="h-full flex flex-col rounded-2xl glass-panel border border-white/10 bg-void-950/70 p-5 select-none">
      {/* Top Header & Search Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-wider text-white">
              Transaction Feed
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-900 border border-white/10 text-slate-400">
              {filteredTransactions.length} of {transactions.length}
            </span>
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <ArrowUpDown className="w-3.5 h-3.5 text-cyan-400" />
            <select
              value={sortOption}
              onChange={(e) => setSortOption(e.target.value as SortOption)}
              className="bg-slate-900 border border-white/10 rounded px-2 py-1 text-[11px] text-slate-300 focus:outline-none focus:border-cyan-400"
            >
              <option value="NEWEST">Newest First</option>
              <option value="RISK_DESC">Highest Risk</option>
              <option value="AMOUNT_DESC">Highest Amount</option>
            </select>
          </div>
        </div>

        {/* Search Input Box */}
        <div className="relative mb-3">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Search by merchant, card number, or transaction ID..."
            className="w-full bg-slate-900/90 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400/60 transition-colors"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-2.5 text-xs text-slate-500 hover:text-white font-mono"
            >
              ✕
            </button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-[10px] font-mono">
          {(
            [
              'ALL',
              'FLAGGED',
              'CRITICAL',
              'HIGH',
              'MEDIUM',
              'LOW',
              'CONFIRMED_FRAUD',
              'PENDING',
            ] as FilterOption[]
          ).map((filt) => (
            <button
              key={filt}
              onClick={() => {
                setActiveFilter(filt);
                setCurrentPage(1);
              }}
              className={`px-2.5 py-1 rounded-lg border whitespace-nowrap transition-colors ${
                activeFilter === filt
                  ? 'bg-cyan-500/20 text-cyan-200 border-cyan-400/50'
                  : 'bg-slate-900/60 text-slate-400 border-white/5 hover:border-white/15 hover:text-slate-200'
              }`}
            >
              {filt.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Transactions List */}
      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1 custom-scroll min-h-[380px] max-h-[580px]">
        {loading && transactions.length === 0 ? (
          // Loading Skeletons
          Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="p-3.5 rounded-xl bg-slate-900/40 border border-white/5 animate-pulse"
            >
              <div className="h-4 bg-slate-800 rounded w-1/3 mb-2" />
              <div className="h-3 bg-slate-800/60 rounded w-2/3" />
            </div>
          ))
        ) : pagedTransactions.length === 0 ? (
          // Empty State
          <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-slate-400 font-mono text-xs">
            <AlertTriangle className="w-8 h-8 text-slate-600 mb-2" />
            <span className="font-semibold text-slate-300 mb-1">No Matching Transactions</span>
            <p className="text-[11px] text-slate-500 max-w-xs">
              No transactions match the selected filter or search terms. Try adjusting the query or click refresh.
            </p>
          </div>
        ) : (
          pagedTransactions.map((txn) => {
            const isSelected = selectedTransaction?.id === txn.id;
            const badge = getRiskBadge(txn.analysis?.riskLevel, txn.fraudScore);
            const isFlagged = txn.status === 'flagged' || txn.isFlagged;

            return (
              <button
                key={txn.id}
                onClick={() => onSelectTransaction(txn)}
                className={`w-full text-left p-3.5 rounded-xl border transition-all ${
                  isSelected
                    ? 'bg-cyan-950/40 border-cyan-400/60 shadow-[0_0_15px_rgba(56,189,248,0.2)]'
                    : 'bg-void-950/60 border-white/5 hover:border-white/20 hover:bg-void-900/70'
                }`}
              >
                {/* Top Row: Merchant & Amount */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-semibold text-white truncate font-sans">
                      {txn.merchant}
                    </span>
                    {txn.reviewStatus === 'CONFIRMED_FRAUD' && (
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-mono bg-rose-500/20 text-rose-300 border border-rose-500/40 shrink-0">
                        CONFIRMED
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono font-bold text-white shrink-0 ml-2">
                    ${txn.amount.toFixed(2)}
                  </span>
                </div>

                {/* Bottom Row: Score, Risk Badge & Time */}
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${badge.bg}`}
                    >
                      {badge.text}
                    </span>
                    <span
                      className={
                        isFlagged ? 'text-rose-400 font-bold' : 'text-slate-300 font-medium'
                      }
                    >
                      {txn.fraudScore.toFixed(1)}% Prob
                    </span>
                  </div>

                  <span className="text-[10px] text-slate-500">
                    {new Date(txn.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Pagination Footer */}
      <div className="pt-3 mt-3 border-t border-white/5 flex items-center justify-between text-xs font-mono text-slate-400">
        <span>
          Page {currentPage} of {totalPages}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage <= 1}
            className="p-1 rounded bg-slate-900 border border-white/10 hover:border-cyan-400/40 text-slate-300 disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage >= totalPages}
            className="p-1 rounded bg-slate-900 border border-white/10 hover:border-cyan-400/40 text-slate-300 disabled:opacity-30 disabled:pointer-events-none"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

