// types/index.ts

export type TransactionStatus = 'secure' | 'flagged' | 'reviewing';

export type ReviewStatus =
  | 'PENDING'
  | 'UNDER_REVIEW'
  | 'CONFIRMED_FRAUD'
  | 'LEGITIMATE'
  | 'ESCALATED';

export interface ShapValue {
  feature: string;
  displayName?: string;
  value: number;
  featureValue?: string | number | boolean;
  impact: 'positive' | 'negative';
  description: string;
  humanReadable?: string;
}

export interface FraudAnalysis {
  transactionId: string;
  fraudProbability: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  shapValues: ShapValue[];
  positiveContributions?: ShapValue[];
  negativeContributions?: ShapValue[];
  summaryNarrative?: string[];
  baseValue?: number;
  modelConfidence: number;
  processingTime: number;
}

export interface Transaction {
  id: string;
  amount: number;
  merchant: string;
  location: string;
  timestamp: string;
  status: TransactionStatus;
  fraudScore: number;
  cardLast4: string;
  category: string;
  analysis?: FraudAnalysis;
  rawFeatures?: Record<string, any>;
  reviewStatus?: ReviewStatus;
  analystNotes?: string | null;
  reviewedBy?: string | null;
  reviewedAt?: string | null;
  isFlagged?: boolean;
}

export interface AnalyticsData {
  time_range: string;
  total_transactions: number;
  total_flagged_transactions: number;
  total_confirmed_fraud: number;
  total_legitimate: number;
  transactions_awaiting_review: number;
  fraud_detection_rate: number;
  fraud_percentage: number;
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
    CRITICAL: number;
  };
  volume_over_time: Array<{
    timestamp: string;
    count: number;
    volume_amount: number;
  }>;
  fraud_volume_over_time: Array<{
    timestamp: string;
    flagged_count: number;
    flagged_amount: number;
  }>;
  data_source?: string;
  data_source_label?: string;
}

export interface ModelInfo {
  model_name: string;
  algorithm: string;
  version: string;
  training_date: string;
  number_of_features: number;
  number_of_encoded_features: number;
  input_feature_schema: string[];
  preprocessing: {
    pipeline: string;
    numerical_scaler: string;
    categorical_encoder: string;
    class_imbalance_technique: string;
  };
  shap_output_space: string;
  selected_threshold: number;
  decision_rationale: string;
  risk_band_configuration: Record<string, string>;
}
