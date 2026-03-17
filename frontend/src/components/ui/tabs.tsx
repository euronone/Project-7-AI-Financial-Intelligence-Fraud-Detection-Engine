"use client";

import { createContext, useContext, useState } from "react";
import { cn } from "@/lib/utils";

const TabsContext = createContext<{ value: string; onChange: (v: string) => void }>({
  value: "",
  onChange: () => {},
});

interface TabsProps {
  defaultValue: string;
  children: React.ReactNode;
  className?: string;
}

export function Tabs({ defaultValue, children, className }: TabsProps) {
  const [value, setValue] = useState(defaultValue);
  return (
    <TabsContext.Provider value={{ value, onChange: setValue }}>
      <div className={className}>{children}</div>
    </TabsContext.Provider>
  );
}

export function TabsList({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("inline-flex gap-1 rounded-lg bg-gray-100 p-1", className)}>
      {children}
    </div>
  );
}

export function TabsTrigger({ value, children, className }: { value: string; children: React.ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  const active = ctx.value === value;
  return (
    <button
      onClick={() => ctx.onChange(value)}
      className={cn(
        "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
        active ? "bg-white text-gray-900 shadow-sm" : "text-gray-600 hover:text-gray-900",
        className,
      )}
    >
      {children}
    </button>
  );
}

export function TabsContent({ value, children, className }: { value: string; children: React.ReactNode; className?: string }) {
  const ctx = useContext(TabsContext);
  if (ctx.value !== value) return null;
  return <div className={cn("mt-4", className)}>{children}</div>;
}
