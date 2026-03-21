"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const labelOverrides: Record<string, string> = {
  dashboard: "Dashboard",
  transactions: "Transactions",
  alerts: "Fraud Alerts",
  cases: "Cases",
  entities: "Entities",
  watchlists: "Watchlists",
  rules: "Rules Engine",
  reports: "Reports",
  network: "Network Graph",
  models: "ML Models",
  audit: "Audit Log",
  settings: "Settings",
};

export function Breadcrumbs({ className }: { className?: string }) {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length <= 1) return null;

  const crumbs = segments.map((segment, idx) => {
    const href = "/" + segments.slice(0, idx + 1).join("/");
    const label = labelOverrides[segment] || segment.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    const isLast = idx === segments.length - 1;
    return { label, href, isLast };
  });

  return (
    <nav className={cn("flex items-center gap-1 text-sm", className)}>
      {crumbs.map((crumb, idx) => (
        <span key={crumb.href} className="flex items-center gap-1">
          {idx > 0 && (
            <svg className="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
            </svg>
          )}
          {crumb.isLast ? (
            <span className="font-medium text-gray-900">{crumb.label}</span>
          ) : (
            <Link href={crumb.href} className="text-gray-500 hover:text-gray-700">
              {crumb.label}
            </Link>
          )}
        </span>
      ))}
    </nav>
  );
}
