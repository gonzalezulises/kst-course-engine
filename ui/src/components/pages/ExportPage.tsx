import { useState } from "react";
import { useCourse } from "../../hooks/useCourse";
import { fetchExport } from "../../api/endpoints";
import type { ExportResponse } from "../../api/types";
import { Card } from "../shared/Card";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { ErrorAlert } from "../shared/ErrorAlert";
import { EmptyState } from "../shared/EmptyState";
import { MermaidDiagram } from "../shared/MermaidDiagram";

export function ExportPage() {
  const { courseInput } = useCourse();
  const [data, setData] = useState<ExportResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [format, setFormat] = useState<"dot" | "mermaid" | "json">("mermaid");
  const [type, setType] = useState<"hasse" | "prerequisites">("hasse");
  const [copied, setCopied] = useState(false);

  const run = async () => {
    if (!courseInput) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchExport({
        domain: courseInput.domain,
        prerequisites: courseInput.prerequisites,
        format,
        type,
      });
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!data) return;
    await navigator.clipboard.writeText(data.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!courseInput) {
    return <EmptyState message="Load a course definition to export." />;
  }

  return (
    <div className="max-w-4xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Export</h2>
        <button
          onClick={run}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Exporting..." : "Run"}
        </button>
      </div>

      <Card title="Options">
        <div className="flex gap-4">
          <label className="block">
            <span className="text-xs text-gray-600">Format</span>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as "dot" | "mermaid" | "json")}
              className="mt-1 block w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="mermaid">Mermaid</option>
              <option value="dot">DOT (Graphviz)</option>
              <option value="json">JSON</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs text-gray-600">Type</span>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as "hasse" | "prerequisites")}
              className="mt-1 block w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="hasse">Hasse Diagram</option>
              <option value="prerequisites">Prerequisites</option>
            </select>
          </label>
        </div>
      </Card>

      {error && <ErrorAlert message={error} />}
      {loading && <LoadingSpinner className="py-8" />}

      {data && !loading && (
        <>
          {data.format === "mermaid" && (
            <Card title="Diagram">
              <MermaidDiagram chart={data.content} />
            </Card>
          )}
          <Card title="Source">
            <div className="relative">
              <button
                onClick={copyToClipboard}
                className="absolute top-2 right-2 px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
              <pre className="p-3 bg-gray-50 rounded-md text-xs font-mono text-gray-700 overflow-x-auto max-h-96 whitespace-pre-wrap">
                {data.content}
              </pre>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
