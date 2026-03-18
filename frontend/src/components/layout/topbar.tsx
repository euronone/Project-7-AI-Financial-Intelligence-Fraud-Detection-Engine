"use client";

import { signOut, useSession } from "next-auth/react";
import { usePathname } from "next/navigation";

const TITLE_MAP: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/transactions": "Transactions",
  "/fraud-alerts": "Fraud Alerts",
  "/risk-scoring": "Risk Scoring",
  "/case-management": "Case Management",
  "/analytics": "Analytics",
  "/rules-engine": "Rules Engine",
  "/entities": "Entities",
  "/ml-models": "ML Models",
  "/network-graph": "Network Graph",
  "/watchlists": "Watchlists",
  "/audit-log": "Audit Log",
  "/settings": "Settings",
};

export function Topbar() {
  const pathname = usePathname();
  const base = "/" + (pathname.split("/")[1] ?? "");
  const title = TITLE_MAP[base] ?? "FinShield AI";
  const { data: session } = useSession();

  const user = session?.user;
  const initials = user?.name
    ? user.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()
    : "?";

  return (
    <header className="h-14 border-b bg-white flex items-center justify-between px-6 sticky top-0 z-10">
      <h1 className="text-base font-semibold text-gray-900">{title}</h1>
      <div className="flex items-center gap-3">
        {user && (
          <>
            <span className="text-xs text-gray-500 hidden sm:block">{user.email}</span>
            <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold">
              {initials}
            </div>
            <button
              onClick={() => signOut({ callbackUrl: "/login" })}
              className="text-xs text-gray-500 hover:text-red-500 transition-colors px-2 py-1 rounded border border-gray-200 hover:border-red-300"
            >
              Sign out
            </button>
          </>
        )}
      </div>
    </header>
  );
}
