import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinShield AI — Stop Fraud Before It Happens",
  description: "Real-time ML-powered fraud detection for banks, fintechs, and insurance companies.",
  keywords: ["fraud detection", "ML", "fintech", "banking", "AI", "FinShield"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full bg-[#0A0A0F] text-white antialiased" suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
