'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Transaction,
  FraudAnalysis,
  AnalyticsData,
  ModelInfo,
} from '@/types';
import {
  checkBackendHealth,
  fetchModelInfo,
  fetchAnalytics,
  fetchRecentTransactions,
  fetchSimulationSample,
  predictTransaction,
} from '@/lib/api';
import DashboardHeader from '@/components/dashboard/DashboardHeader';
import DashboardKpis from '@/components/dashboard/DashboardKpis';
import TransactionMonitoringFeed from '@/components/dashboard/TransactionMonitoringFeed';
import FraudProbabilityMatrix from '@/components/dashboard/FraudProbabilityMatrix';
import ExplainableAiWorkspace from '@/components/dashboard/ExplainableAiWorkspace';
import TransactionInspector from '@/components/dashboard/TransactionInspector';
import AnalyticsTelemetryCharts from '@/components/dashboard/AnalyticsTelemetryCharts';
import { CheckCircle2, AlertOctagon } from 'lucide-react';

export default function DashboardPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null);
  const [analysis, setAnalysis] = useState<FraudAnalysis | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);

  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [databaseConnected, setDatabaseConnected] = useState<boolean>(false);
  const [databaseSource, setDatabaseSource] = useState<string | undefined>(undefined);
  const [databaseSourceLabel, setDatabaseSourceLabel] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(true);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // 1. Initial Health & Diagnostics Check
  const loadSystemDiagnostics = useCallback(async () => {
    try {
      const health = await checkBackendHealth();
      setBackendOnline(health.status === 'healthy');
      setDatabaseConnected(health.database_connected);
      setDatabaseSource(health.database_source);
      setDatabaseSourceLabel(health.database_source_label);

      const info = await fetchModelInfo();
      if (info) setModelInfo(info);
    } catch {
      setBackendOnline(false);
      setDatabaseConnected(false);
    }
  }, []);

  // 2. Fetch Recent Transactions and Analytics
  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const [txns, stats] = await Promise.all([
        fetchRecentTransactions(100),
        fetchAnalytics(),
      ]);

      setTransactions(txns);
      if (stats) setAnalytics(stats);

      // Auto-select first or maintain current selection
      if (txns.length > 0) {
        setSelectedTxn((prev) => {
          if (prev) {
            const found = txns.find((t) => t.id === prev.id);
            if (found) {
              setAnalysis(found.analysis ?? null);
              return found;
            }
          }
          const first = txns[0];
          setAnalysis(first.analysis ?? null);
          return first;
        });
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSystemDiagnostics();
    loadDashboardData();

    // Periodic health & telemetry auto-refresh
    const interval = setInterval(() => {
      loadSystemDiagnostics();
      loadDashboardData();
    }, 15000);
    return () => clearInterval(interval);
  }, [loadSystemDiagnostics, loadDashboardData]);

  // Select Transaction
  const handleSelectTransaction = useCallback((txn: Transaction) => {
    setSelectedTxn(txn);
    setAnalysis(txn.analysis ?? null);
  }, []);

  // Update transaction review in state
  const handleUpdateReviewSuccess = useCallback((updated: Transaction) => {
    setTransactions((prev) =>
      prev.map((t) => (t.id === updated.id ? updated : t))
    );
    setSelectedTxn(updated);
    if (updated.analysis) setAnalysis(updated.analysis);

    // Refresh analytics to reflect updated review counts
    fetchAnalytics().then((stats) => {
      if (stats) setAnalytics(stats);
    });

    setToastMessage('Analyst review status updated.');
    setTimeout(() => setToastMessage(null), 3500);
  }, []);

  // Real ML Simulation: fetches raw feature sample and posts to /predict
  const handleSimulate = useCallback(
    async (scenario: 'random' | 'fraud' | 'legit' = 'random') => {
      setSimulating(true);
      try {
        const samplePayload = await fetchSimulationSample(scenario);
        const prediction = await predictTransaction(samplePayload);

        // Convert prediction into local Transaction item
        const score = prediction.fraud_probability * 100;
        const newTxn: Transaction = {
          id: prediction.transaction_id,
          amount: Number(samplePayload.transaction_amount || 120.0),
          merchant: samplePayload.merchant_category
            ? `${samplePayload.merchant_category} Merchant`
            : 'Payment Terminal',
          location: samplePayload.high_risk_country ? 'International' : 'Domestic POS',
          timestamp: prediction.timestamp || new Date().toISOString(),
          status: prediction.is_flagged ? 'flagged' : score >= 25 ? 'reviewing' : 'secure',
          fraudScore: score,
          cardLast4: '4242',
          category: samplePayload.merchant_category || 'Retail',
          isFlagged: prediction.is_flagged,
          reviewStatus: 'PENDING',
          analysis: {
            transactionId: prediction.transaction_id,
            fraudProbability: prediction.fraud_probability,
            riskLevel: prediction.risk_level,
            shapValues: prediction.top_contributors.map((c) => ({
              feature: c.feature,
              displayName: c.display_name,
              value: c.shap_value,
              featureValue: c.feature_value,
              impact: c.shap_value > 0 ? 'positive' : 'negative',
              description: c.human_readable || c.description,
              humanReadable: c.human_readable,
            })),
            summaryNarrative: prediction.summary_narrative,
            baseValue: prediction.base_value,
            modelConfidence: 97.4,
            processingTime: 12,
          },
        };

        // Prepend to transaction feed and select
        setTransactions((prev) => [newTxn, ...prev]);
        setSelectedTxn(newTxn);
        setAnalysis(newTxn.analysis ?? null);

        // Refresh stats and transactions list from authoritative store
        fetchAnalytics().then((stats) => {
          if (stats) setAnalytics(stats);
        });
        fetchRecentTransactions(100).then((txns) => {
          if (txns && txns.length > 0) setTransactions(txns);
        });

        setToastMessage(
          `Simulated transaction evaluated: ${score.toFixed(1)}% fraud probability (${prediction.risk_level})`
        );
        setTimeout(() => setToastMessage(null), 4000);
      } catch (err: any) {
        console.error('Simulation failed:', err);
        setToastMessage(`Simulation error: ${err.message}`);
        setTimeout(() => setToastMessage(null), 4000);
      } finally {
        setSimulating(false);
      }
    },
    []
  );

  return (
    <div className="min-h-screen w-full p-4 sm:p-6 lg:p-8 flex flex-col justify-start">
      {/* Toast Notification */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-5 right-5 z-50 px-4 py-2.5 rounded-xl bg-slate-900/95 border border-cyan-400/50 shadow-[0_10px_30px_rgba(0,0,0,0.8)] text-xs font-mono text-cyan-200 flex items-center gap-2 backdrop-blur-xl"
          >
            <CheckCircle2 className="w-4 h-4 text-cyan-400" />
            <span>{toastMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <DashboardHeader
        backendOnline={backendOnline}
        databaseConnected={databaseConnected}
        databaseSource={databaseSource}
        databaseSourceLabel={databaseSourceLabel}
        modelInfo={modelInfo}
        loading={loading}
        onRefresh={() => {
          loadSystemDiagnostics();
          loadDashboardData();
        }}
      />

      {/* 4 Large KPI Cards */}
      <DashboardKpis analytics={analytics} loading={loading} />

      {/* Main Section Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mb-6">
        {/* Left Column (5 cols on lg, 4 on xl): Transaction Monitoring Feed */}
        <div className="lg:col-span-5 xl:col-span-4 min-h-[580px]">
          <TransactionMonitoringFeed
            transactions={transactions}
            selectedTransaction={selectedTxn}
            onSelectTransaction={handleSelectTransaction}
            loading={loading}
            onRefresh={loadDashboardData}
          />
        </div>

        {/* Right Column (7 cols on lg, 8 on xl): Split into Gauge and SHAP Panel */}
        <div className="lg:col-span-7 xl:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6 min-h-[580px]">
          {/* Fraud Probability Matrix */}
          <FraudProbabilityMatrix
            analysis={analysis}
            selectedTransaction={selectedTxn}
            threshold={modelInfo?.selected_threshold ?? 0.35}
            onSimulate={handleSimulate}
            simulating={simulating}
          />

          {/* Explainable AI Workspace */}
          <ExplainableAiWorkspace analysis={analysis} loading={loading} />
        </div>
      </div>

      {/* Bottom Row Grid: Inspector + Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Transaction Inspector Workspace (7 cols) */}
        <div className="lg:col-span-7">
          <TransactionInspector
            transaction={selectedTxn}
            onUpdateSuccess={handleUpdateReviewSuccess}
          />
        </div>

        {/* Analytics & Risk Distribution (5 cols) */}
        <div className="lg:col-span-5">
          <AnalyticsTelemetryCharts analytics={analytics} />
        </div>
      </div>
    </div>
  );
}
