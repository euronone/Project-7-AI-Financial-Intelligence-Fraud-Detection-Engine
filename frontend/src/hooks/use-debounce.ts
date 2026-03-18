"use client";

import { useEffect, useState } from "react";

/**
 * Debounce a value by the given delay in milliseconds.
 * Useful for delaying search input queries until the user stops typing.
 */
export function useDebounce<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState<T>(value);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(id);
  }, [value, delayMs]);

  return debounced;
}
