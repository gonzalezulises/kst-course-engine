import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "loose",
});

let idCounter = 0;

export function MermaidDiagram({ chart }: { chart: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !chart.trim()) return;

    const id = `mermaid-${++idCounter}`;

    let cancelled = false;
    mermaid
      .render(id, chart)
      .then(({ svg }) => {
        if (!cancelled) {
          el.innerHTML = svg;
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [chart]);

  if (error) {
    return (
      <div className="text-sm text-red-600 p-2">
        Failed to render diagram: {error}
      </div>
    );
  }

  return <div ref={containerRef} className="overflow-x-auto" />;
}
