import { Badge } from "@/components/ui/badge";

type StatusType = "active" | "inactive" | "pending" | "error" | "open" | "investigating" | "resolved" | "dismissed" | "completed" | "flagged";

const statusConfig: Record<StatusType, { variant: "success" | "warning" | "danger" | "default" | "primary"; label: string }> = {
  active: { variant: "success", label: "Active" },
  inactive: { variant: "default", label: "Inactive" },
  pending: { variant: "warning", label: "Pending" },
  error: { variant: "danger", label: "Error" },
  open: { variant: "warning", label: "Open" },
  investigating: { variant: "primary", label: "Investigating" },
  resolved: { variant: "success", label: "Resolved" },
  dismissed: { variant: "default", label: "Dismissed" },
  completed: { variant: "success", label: "Completed" },
  flagged: { variant: "danger", label: "Flagged" },
};

interface StatusIndicatorProps {
  status: string;
  className?: string;
}

export function StatusIndicator({ status, className }: StatusIndicatorProps) {
  const config = statusConfig[status as StatusType] || { variant: "default" as const, label: status };
  return (
    <Badge variant={config.variant} dot className={className}>
      {config.label}
    </Badge>
  );
}
