import Link from "next/link";
import { Shield } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0A0A0F] flex flex-col">
      {/* Top bar */}
      <nav className="flex items-center justify-between px-6 py-4 border-b border-[#1E1E2E]">
        <Link href="/" className="flex items-center gap-2">
          <Shield size={22} className="text-[#00FF87]" />
          <span className="text-lg font-bold">
            Fin<span className="text-[#00FF87]">Shield</span> AI
          </span>
        </Link>
        <span className="text-xs text-gray-600 font-mono">Enterprise Fraud Detection Platform</span>
      </nav>

      {/* Grid background */}
      <div className="flex-1 flex items-center justify-center p-6 relative">
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "linear-gradient(rgba(30,30,46,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(30,30,46,0.4) 1px, transparent 1px)",
            backgroundSize: "50px 50px",
          }}
        />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-[#00FF87] opacity-[0.03] rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 w-full">{children}</div>
      </div>
    </div>
  );
}
