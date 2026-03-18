export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      {/* Fintech-style gradient background with subtle grid */}
      <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-primary-950 to-slate-900" />
      <div
        className="fixed inset-0 opacity-30"
        style={{
          backgroundImage: `linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px)`,
          backgroundSize: "48px 48px",
        }}
      />
      <div className="relative w-full max-w-md">{children}</div>
    </div>
  );
}
