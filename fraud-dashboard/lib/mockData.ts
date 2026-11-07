// lib/mockData.ts
import { Transaction, FraudAnalysis, ShapValue } from '@/types';

const merchants = [
  'Amazon', 'Netflix', 'Uber', 'Steam', 'Shopify Store',
  'Roblox', 'Unknown Merchant', 'Binance P2P', 'VPN Service',
  'Starbucks', 'Apple Store', 'Google Play', 'AliExpress',
];
const locations = [
  'Mumbai, IN', 'Lagos, NG', 'Unknown VPN', 'New York, US',
  'London, UK', 'Nairobi, KE', 'Kyiv, UA', 'São Paulo, BR',
  'Jakarta, ID', 'Dubai, AE',
];
const categories = [
  'Entertainment', 'Transport', 'E-Commerce', 'Gaming',
  'Crypto', 'SaaS', 'Food & Beverage', 'Retail',
];

function randomId() {
  return 'TXN-' + Math.random().toString(36).substr(2, 8).toUpperCase();
}
function randomChoice<T>(arr: T[]): T {
  return arr[Math.floor(Math.random() * arr.length)];
}
function randomFloat(min: number, max: number, dp = 2) {
  return parseFloat((Math.random() * (max - min) + min).toFixed(dp));
}

export function generateTransaction(): Transaction {
  const fraudScore = randomFloat(0, 100);
  const status =
    fraudScore > 75 ? 'flagged' :
    fraudScore > 45 ? 'reviewing' : 'secure';

  return {
    id: randomId(),
    amount: randomFloat(1, 9999),
    merchant: randomChoice(merchants),
    location: randomChoice(locations),
    timestamp: new Date().toISOString(),
    status,
    fraudScore,
    cardLast4: String(Math.floor(1000 + Math.random() * 9000)),
    category: randomChoice(categories),
  };
}

export function generateInitialTransactions(count = 12): Transaction[] {
  return Array.from({ length: count }, () => generateTransaction()).sort(
    (a, b) => b.fraudScore - a.fraudScore
  );
}

const shapFeatures = [
  { feature: 'Transaction Velocity', description: '3 txns in last 10 min' },
  { feature: 'Geo Anomaly Score', description: 'Location differs from home country' },
  { feature: 'Amount Deviation', description: '4.2σ above user average' },
  { feature: 'Merchant Risk', description: 'First-time merchant interaction' },
  { feature: 'Time-of-Day', description: 'Transaction at 03:14 AM local time' },
  { feature: 'Device Fingerprint', description: 'Unknown device hash detected' },
  { feature: 'Card Present', description: 'Card-not-present transaction' },
  { feature: 'IP Reputation', description: 'IP flagged in threat database' },
];

export function generateFraudAnalysis(txn: Transaction): FraudAnalysis {
  const shapValues: ShapValue[] = shapFeatures.slice(0, 5 + Math.floor(Math.random() * 3)).map((f) => {
    const value = randomFloat(-0.35, 0.45);
    return {
      feature: f.feature,
      value,
      impact: value > 0 ? 'positive' : 'negative',
      description: f.description,
    };
  });

  const riskLevel =
    txn.fraudScore >= 80 ? 'CRITICAL' :
    txn.fraudScore >= 60 ? 'HIGH' :
    txn.fraudScore >= 35 ? 'MEDIUM' : 'LOW';

  return {
    transactionId: txn.id,
    fraudProbability: txn.fraudScore / 100,
    riskLevel,
    shapValues,
    modelConfidence: randomFloat(85, 99.5),
    processingTime: randomFloat(12, 48, 0),
  };
}

