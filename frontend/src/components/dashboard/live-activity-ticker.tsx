"use client";

import { memo, useEffect, useRef, useCallback } from "react";
import { cn } from "@/lib/utils";

interface ActivityEvent {
  id: string;
  message: string;
  type: "transaction" | "alert" | "system" | "model";
  timestamp: string;
}

interface LiveActivityTickerProps {
  events: ActivityEvent[];
}

const TYPE_STYLES: Record<ActivityEvent["type"], string> = {
  transaction: "text-blue-600 dark:text-blue-400",
  alert: "text-red-600 dark:text-red-400",
  system: "text-gray-600 dark:text-gray-400",
  model: "text-purple-600 dark:text-purple-400",
};

const TYPE_DOT: Record<ActivityEvent["type"], string> = {
  transaction: "bg-blue-500",
  alert: "bg-red-500",
  system: "bg-gray-500",
  model: "bg-purple-500",
};

export const LiveActivityTicker = memo(function LiveActivityTicker({
  events,
}: LiveActivityTickerProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number | null>(null);
  const pausedRef = useRef(false);

  const animate = useCallback(() => {
    const el = scrollRef.current;
    if (!el || pausedRef.current) {
      animationRef.current = requestAnimationFrame(animate);
      return;
    }

    el.scrollLeft += 0.5;

    if (el.scrollLeft >= el.scrollWidth - el.clientWidth) {
      el.scrollLeft = 0;
    }

    animationRef.current = requestAnimationFrame(animate);
  }, []);

  useEffect(() => {
    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [animate]);

  const handleMouseEnter = useCallback(() => {
    pausedRef.current = true;
  }, []);

  const handleMouseLeave = useCallback(() => {
    pausedRef.current = false;
  }, []);

  if (events.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 bg-white dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center gap-2 border-b border-gray-200 px-4 py-2 dark:border-gray-800">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </span>
        <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">
          Live Activity
        </span>
      </div>

      <div
        ref={scrollRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="scrollbar-hide flex gap-6 overflow-x-hidden px-4 py-3"
      >
        {events.map((event) => (
          <div
            key={event.id}
            className="flex shrink-0 items-center gap-2"
          >
            <span
              className={cn(
                "inline-block h-1.5 w-1.5 rounded-full",
                TYPE_DOT[event.type]
              )}
            />
            <span
              className={cn(
                "whitespace-nowrap text-xs font-medium",
                TYPE_STYLES[event.type]
              )}
            >
              {event.message}
            </span>
            <span className="whitespace-nowrap text-[10px] text-gray-400 dark:text-gray-500">
              {new Date(event.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
          </div>
        ))}

        {events.map((event) => (
          <div
            key={`dup-${event.id}`}
            className="flex shrink-0 items-center gap-2"
            aria-hidden="true"
          >
            <span
              className={cn(
                "inline-block h-1.5 w-1.5 rounded-full",
                TYPE_DOT[event.type]
              )}
            />
            <span
              className={cn(
                "whitespace-nowrap text-xs font-medium",
                TYPE_STYLES[event.type]
              )}
            >
              {event.message}
            </span>
            <span className="whitespace-nowrap text-[10px] text-gray-400 dark:text-gray-500">
              {new Date(event.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
});
