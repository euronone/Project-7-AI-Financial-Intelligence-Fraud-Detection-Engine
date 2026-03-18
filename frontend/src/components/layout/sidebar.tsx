"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "⬛" },
  { href: "/transactions", label: "Transactions", icon: "💳" },
  { href: "/fraud-alerts", label: "Fraud Alerts", icon: "🚨" },
  { href: "/risk-scoring", label: "Risk Scoring", icon: "📊" },
  { href: "/case-management", label: "Cases", icon: "📁" },
  { href: "/analytics", label: "Analytics", icon: "📈" },
  { href: "/rules-engine", label: "Rules Engine", icon: "⚙️" },
  { href: "/entities", label: "Entities", icon: "👤" },
  { href: "/ml-models", label: "ML Models", icon: "🤖" },
  { href: "/network-graph", label: "Network Graph", icon: "🕸️" },
  { href: "/watchlists", label: "Watchlists", icon: "🛡️" },
  { href: "/audit-log", label: "Audit Log", icon: "📋" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 shrink-0 bg-gray-900 text-white flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-700">
        <span className="text-lg font-bold text-white">FinShield AI</span>
        <p className="text-xs text-gray-400 mt-0.5">Fraud Detection Engine</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                active
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              )}
            >
              <span className="text-base leading-none">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-700 text-xs text-gray-500">
        v1.0.0 — F1 Transaction Monitoring
      </div>
    </aside>
  );
}
