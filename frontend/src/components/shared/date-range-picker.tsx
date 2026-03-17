"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface DateRangePickerProps {
  from?: string;
  to?: string;
  onChange: (range: { from: string; to: string }) => void;
  className?: string;
}

export function DateRangePicker({ from = "", to = "", onChange, className }: DateRangePickerProps) {
  const [localFrom, setLocalFrom] = useState(from);
  const [localTo, setLocalTo] = useState(to);

  const handleFromChange = (value: string) => {
    setLocalFrom(value);
    if (value && localTo) onChange({ from: value, to: localTo });
  };

  const handleToChange = (value: string) => {
    setLocalTo(value);
    if (localFrom && value) onChange({ from: localFrom, to: value });
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="relative">
        <input
          type="date"
          value={localFrom}
          onChange={(e) => handleFromChange(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>
      <span className="text-sm text-gray-400">to</span>
      <div className="relative">
        <input
          type="date"
          value={localTo}
          min={localFrom}
          onChange={(e) => handleToChange(e.target.value)}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>
    </div>
  );
}
