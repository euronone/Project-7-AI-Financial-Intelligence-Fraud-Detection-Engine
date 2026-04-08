import Link from "next/link";
import { Shield, Lock } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0A0A0F] flex flex-col">
      {/* Top bar */}
      <nav
        className="flex items-center justify-between px-6 py-4 border-b border-[#1E1E2E] bg-[#0A0A0F]/50 backdrop-blur-sm"
        role="navigation"
        aria-label="Main navigation"
      >
        <Link
          href="/"
          className="flex items-center gap-2 hover:opacity-80 transition-opacity focus:outline-none focus:ring-2 focus:ring-[#00FF87] rounded-lg p-1"
          aria-label="FinShield AI Home"
        >
          <Shield size={22} className="text-[#00FF87]" aria-hidden="true" />
          <span className="text-lg font-bold">
            Fin<span className="text-[#00FF87]">Shield</span> AI
          </span>
        </Link>
        <div className="flex items-center gap-4">
          <span className="text-xs text-gray-600 font-mono hidden sm:inline">
            Enterprise Fraud Detection Platform
          </span>
          <div
            className="flex items-center gap-1 text-xs text-gray-500 px-2 py-1 rounded-lg bg-[#00FF87]/5 border border-[#00FF87]/10"
            aria-label="Privacy status: Your data stays private"
          >
            <Lock size={12} className="text-[#00FF87]" aria-hidden="true" />
            <span className="hidden sm:inline">Your data stays private</span>
            <span className="sm:hidden" aria-hidden="true">Private</span>
          </div>
        </div>
      </nav>

      {/* Grid background */}
      <div className="flex-1 flex items-center justify-center p-6 relative">
        <div
          className="absolute inset-0 opacity-30 pointer-events-none"
          style={{
            backgroundImage:
              "linear-gradient(rgba(30,30,46,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(30,30,46,0.4) 1px, transparent 1px)",
            backgroundSize: "50px 50px",
          }}
          aria-hidden="true"
        />
        <div
          className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-[#00FF87] opacity-[0.03] rounded-full blur-3xl pointer-events-none"
          aria-hidden="true"
        />
        <main className="relative z-10 w-full">
          {children}
        </main>
      </div>
    </div>
  );
}
