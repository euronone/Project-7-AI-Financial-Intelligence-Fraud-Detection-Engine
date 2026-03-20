"use client";

import type { TimelineEvent } from "@/types/case";

interface AlertTimelineProps {
  events: TimelineEvent[];
}

export function AlertTimeline({ events }: AlertTimelineProps) {
  if (!events.length) {
    return <p className="text-sm text-gray-500">No timeline events.</p>;
  }

  return (
    <div className="relative space-y-4 pl-6">
      <div className="absolute left-2 top-2 bottom-2 w-0.5 bg-gray-200" />
      {events.map((event, i) => (
        <div key={i} className="relative">
          <div className="absolute -left-[18px] top-1 h-3 w-3 rounded-full border-2 border-primary-500 bg-white" />
          <div className="rounded-lg bg-gray-50 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900 capitalize">
                {event.type.replace(/_/g, " ")}
              </span>
              <span className="text-xs text-gray-400">
                {new Date(event.timestamp).toLocaleString()}
              </span>
            </div>
            {event.new_status && (
              <p className="mt-1 text-sm text-gray-600">
                Status changed to <span className="font-medium">{event.new_status.replace(/_/g, " ")}</span>
              </p>
            )}
            {event.notes && (
              <p className="mt-1 text-sm text-gray-500">{event.notes}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
