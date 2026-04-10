"use client";

import { useCallback, useRef } from "react";
import type { SSEEvent, SSEEventType } from "@/types";

interface UseSSEOptions {
  onStart?: (data: Record<string, unknown>) => void;
  onChunk?: (data: Record<string, unknown>) => void;
  onDone?: (data: Record<string, unknown>) => void;
  onError?: (data: Record<string, unknown>) => void;
}

/**
 * Hook for consuming SSE (Server-Sent Events) streams from the backend.
 *
 * Parses the `event: <type>\ndata: <json>\n\n` protocol emitted by
 * the FastAPI `_to_sse` helper and dispatches to typed callbacks.
 */
export function useSSE(options: UseSSEOptions) {
  const abortRef = useRef<AbortController | null>(null);

  const handlers: Record<
    SSEEventType,
    ((data: Record<string, unknown>) => void) | undefined
  > = {
    start: options.onStart,
    chunk: options.onChunk,
    done: options.onDone,
    error: options.onError,
  };

  const consume = useCallback(
    async (response: Response) => {
      const reader = response.body?.getReader();
      if (!reader) throw new Error("Response body is not readable");

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // SSE messages are separated by double newlines
          const messages = buffer.split("\n\n");
          // Keep the last (possibly incomplete) chunk in buffer
          buffer = messages.pop() ?? "";

          for (const msg of messages) {
            if (!msg.trim()) continue;
            const parsed = parseSSEMessage(msg);
            if (parsed) {
              handlers[parsed.event]?.(parsed.data);
            }
          }
        }

        // Process any remaining buffer
        if (buffer.trim()) {
          const parsed = parseSSEMessage(buffer);
          if (parsed) {
            handlers[parsed.event]?.(parsed.data);
          }
        }
      } finally {
        reader.releaseLock();
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [options.onStart, options.onChunk, options.onDone, options.onError],
  );

  const abort = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  return { consume, abort, abortRef };
}

function parseSSEMessage(raw: string): SSEEvent | null {
  let event: SSEEventType = "chunk";
  let dataStr = "";

  for (const line of raw.split("\n")) {
    if (line.startsWith("event: ")) {
      event = line.slice(7).trim() as SSEEventType;
    } else if (line.startsWith("data: ")) {
      dataStr = line.slice(6);
    }
  }

  if (!dataStr) return null;

  try {
    return { event, data: JSON.parse(dataStr) };
  } catch {
    return { event, data: { raw: dataStr } };
  }
}
