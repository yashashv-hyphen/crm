import { useEffect, useRef } from 'react'

/**
 * Opens a persistent SSE connection to `url` with credentials.
 * Calls `onMessage(parsedData)` for every `data:` frame received.
 * Browser auto-reconnects on drop — no manual retry needed.
 */
export function useEventSource(url, onMessage) {
  const onMessageRef = useRef(onMessage)
  onMessageRef.current = onMessage

  useEffect(() => {
    const es = new EventSource(url, { withCredentials: true })

    es.onmessage = (e) => {
      try {
        onMessageRef.current(JSON.parse(e.data))
      } catch {
        // ignore malformed frames
      }
    }

    es.onerror = () => {
      // EventSource auto-reconnects; nothing to do here
    }

    return () => es.close()
  }, [url])
}
