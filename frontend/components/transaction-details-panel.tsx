import { AlertTriangle, CheckCircle2, Clock, DollarSign, MapPin, User, CreditCard } from "lucide-react";

interface TransactionDetailsPanelProps {
  transaction?: {
    transaction_id?: string;
    cardholder_name?: string;
    card_number?: string;
    amount?: string | number;
    merchant_name?: string;
    city?: string;
    country_code?: string;
    channel?: string;
    purchase_type?: string;
    device_type?: string;
    is_new_device?: boolean;
  };
  result?: {
    decision?: string;
    risk_score?: number;
    fraud_category?: string;
    fraud_risk_level?: string | null;
    is_blocked?: boolean;
    is_flagged?: boolean;
    journey?: Record<string, { ok?: boolean; ms?: number; [key: string]: unknown }>;
    transaction_id?: string;
  };
  decisionColor?: string;
}

export function TransactionDetailsPanel({ transaction = {}, result = {}, decisionColor = "#6B7280" }: TransactionDetailsPanelProps) {
  // Safe getters to prevent "[object Object]" errors
  const transactionId = result?.transaction_id || transaction?.transaction_id || "—";
  const cardholderName = transaction?.cardholder_name || "—";
  const cardNumber = transaction?.card_number || "—";
  const amount = transaction?.amount ? `₹${Number(transaction.amount).toLocaleString('en-IN')}` : "—";
  const merchantName = transaction?.merchant_name || "—";
  const city = transaction?.city || "—";
  const countryCode = transaction?.country_code || "—";
  const channel = transaction?.channel || "—";
  const purchaseType = transaction?.purchase_type || "—";
  const isNewDevice = transaction?.is_new_device === true;
  const decision = result?.decision || "—";
  const riskScore = result?.risk_score ?? 0;
  const fraudCategory = result?.fraud_category || "—";
  const isBlocked = result?.is_blocked === true;
  const isFlagged = result?.is_flagged === true;

  const formatTime = (ms?: number) => {
    if (!ms) return "—";
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="sticky top-8 h-fit">
      <div className="bg-[#111118] border border-[#1E1E2E] rounded-2xl p-5 space-y-4">
        {/* Header */}
        <div className="border-b border-[#1E1E2E] pb-3">
          <div className="text-xs text-gray-500 uppercase tracking-widest font-medium mb-2">Transaction Summary</div>
          <div className="flex items-center gap-2">
            {decision === "BLOCK" ? (
              <AlertTriangle size={16} className="text-red-500" />
            ) : decision === "ALERT" ? (
              <AlertTriangle size={16} className="text-orange-500" />
            ) : decision === "FLAG" ? (
              <AlertTriangle size={16} className="text-amber-500" />
            ) : (
              <CheckCircle2 size={16} className="text-green-500" />
            )}
            <span className="text-sm font-semibold" style={{ color: decisionColor }}>
              {decision}
            </span>
          </div>
        </div>

        {/* Transaction ID */}
        <div className="space-y-1">
          <div className="text-xs text-gray-500">Transaction ID</div>
          <div className="text-xs font-mono text-gray-300 break-all bg-[#0A0A0F] p-2 rounded border border-[#1E1E2E]">
            {transactionId}
          </div>
        </div>

        {/* Cardholder Info */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <User size={12} className="text-[#3B82F6]" />
            <span className="text-xs text-gray-500 font-medium">Cardholder</span>
          </div>
          <div className="space-y-1 pl-4">
            <div className="text-xs text-white">{cardholderName}</div>
            <div className="text-xs text-gray-400 font-mono">{cardNumber}</div>
          </div>
        </div>

        {/* Amount */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <DollarSign size={12} className="text-[#00FF87]" />
            <span className="text-xs text-gray-500 font-medium">Amount</span>
          </div>
          <div className="pl-4 text-sm font-semibold text-white">{amount}</div>
        </div>

        {/* Merchant Info */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <CreditCard size={12} className="text-[#F59E0B]" />
            <span className="text-xs text-gray-500 font-medium">Merchant</span>
          </div>
          <div className="pl-4 space-y-1">
            <div className="text-xs text-white">{merchantName}</div>
            <div className="text-xs text-gray-400 capitalize">{purchaseType}</div>
          </div>
        </div>

        {/* Location */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5">
            <MapPin size={12} className="text-[#8B5CF6]" />
            <span className="text-xs text-gray-500 font-medium">Location</span>
          </div>
          <div className="pl-4 text-xs text-white">
            {city}, {countryCode}
          </div>
        </div>

        {/* Channel & Device */}
        <div className="space-y-2">
          <div className="text-xs text-gray-500 font-medium">Channel & Device</div>
          <div className="space-y-1 pl-4">
            <div className="text-xs text-white capitalize">{channel}</div>
            <div className={`text-xs flex items-center gap-1 ${
              isNewDevice ? "text-[#F97316]" : "text-[#00FF87]"
            }`}>
              {isNewDevice ? "🆕 New Device" : "✓ Known Device"}
            </div>
          </div>
        </div>

        {/* Risk Score */}
        <div className="space-y-2 border-t border-[#1E1E2E] pt-3">
          <div className="text-xs text-gray-500 font-medium">Risk Score</div>
          <div className="pl-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-2xl font-black" style={{ color: decisionColor }}>
                {(riskScore * 100).toFixed(1)}%
              </span>
            </div>
            <div className="w-full h-1.5 bg-[#0A0A0F] rounded-full overflow-hidden">
              <div
                className="h-full transition-all"
                style={{
                  width: `${Math.min(riskScore * 100, 100)}%`,
                  backgroundColor: decisionColor,
                }}
              />
            </div>
          </div>
        </div>

        {/* Fraud Category */}
        <div className="space-y-1">
          <div className="text-xs text-gray-500 font-medium">Category</div>
          <div className="pl-4 text-xs font-semibold capitalize text-white">
            {fraudCategory}
          </div>
        </div>

        {/* Processing Journey */}
        {result?.journey && Object.keys(result.journey).length > 0 && (
          <div className="space-y-2 border-t border-[#1E1E2E] pt-3">
            <div className="flex items-center gap-1.5">
              <Clock size={12} className="text-gray-500" />
              <span className="text-xs text-gray-500 font-medium">Processing</span>
            </div>
            <div className="pl-4 space-y-1">
              {Object.entries(result.journey).map(([step, data]) => (
                <div key={step} className="text-xs text-gray-400">
                  <span className="capitalize">{step.replace(/_/g, ' ')}:</span>
                  {data?.ok ? (
                    <span className="text-[#00FF87] ml-1">✓ {formatTime(data.ms)}</span>
                  ) : (
                    <span className="text-red-500 ml-1">✗ Failed</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Status Badge */}
        <div className="pt-2 border-t border-[#1E1E2E]">
          <div className="flex items-center gap-2 flex-wrap">
            {isBlocked && (
              <div className="text-xs bg-red-500/20 border border-red-500/40 text-red-400 px-2.5 py-1 rounded-full font-medium">
                🚫 Blocked
              </div>
            )}
            {isFlagged && (
              <div className="text-xs bg-amber-500/20 border border-amber-500/40 text-amber-400 px-2.5 py-1 rounded-full font-medium">
                ⚠️ Flagged
              </div>
            )}
            {!isBlocked && !isFlagged && (
              <div className="text-xs bg-green-500/20 border border-green-500/40 text-green-400 px-2.5 py-1 rounded-full font-medium">
                ✓ Passed
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
