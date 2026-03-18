/**
 * Currency, date, number, and score formatters.
 */

/** Format a decimal amount string as a localised currency string. */
export function formatCurrency(
  amount: string | number,
  currency = "USD"
): string {
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(num);
}

/** Format an ISO 8601 timestamp as a readable date-time string. */
export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date(iso));
}

/** Format an ISO 8601 timestamp as a short date. */
export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(iso));
}

/** Format a fraud score (0–1) as a percentage string. */
export function formatFraudScore(score: string | number | null): string {
  if (score === null || score === undefined) return "—";
  const num = typeof score === "string" ? parseFloat(score) : score;
  return `${(num * 100).toFixed(1)}%`;
}

/** Format a number with comma separators. */
export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

/** Truncate a string to maxLen characters with ellipsis. */
export function truncate(str: string, maxLen = 40): string {
  if (str.length <= maxLen) return str;
  return `${str.slice(0, maxLen)}…`;
}
