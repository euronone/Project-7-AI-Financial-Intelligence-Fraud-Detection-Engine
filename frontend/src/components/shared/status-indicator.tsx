import { cn } from "@/lib/utils";
import { TRANSACTION_STATUS_COLORS, TRANSACTION_STATUS_LABELS } from "@/lib/constants";
import type { TransactionStatus } from "@/types/transaction";

interface StatusIndicatorProps {
  status: TransactionStatus;
  className?: string;
}

export function StatusIndicator({ status, className }: StatusIndicatorProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
        TRANSACTION_STATUS_COLORS[status],
        className
      )}
    >
      {TRANSACTION_STATUS_LABELS[status]}
    </span>
  );
}
