import React from "react";
import { Providers } from "@/components/providers";

export const metadata = {
  title: "FinShield AI",
  description: "AI Financial Intelligence & Fraud Detection Engine",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
