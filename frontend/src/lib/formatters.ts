import { format, formatDistanceToNow } from "date-fns";

export function formatDate(date: string | Date): string {
  return format(new Date(date), "MMM d, yyyy");
}

export function formatDateTime(date: string | Date): string {
  return format(new Date(date), "MMM d, yyyy HH:mm:ss");
}

export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function maskPII(value: string, visibleChars: number = 4): string {
  if (value.length <= visibleChars) return value;
  return "•".repeat(value.length - visibleChars) + value.slice(-visibleChars);
}
