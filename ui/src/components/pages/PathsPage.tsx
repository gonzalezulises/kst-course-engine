import { useState } from "react";
import { useCourse } from "../../hooks/useCourse";
import { fetchPaths } from "../../api/endpoints";
import type { PathsResponse } from "../../api/types";
import { Card } from "../shared/Card";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { ErrorAlert } from "../shared/ErrorAlert";
import { EmptyState } from "../shared/EmptyState";

export function PathsPage() {
  const { courseInput } = useCourse();
  const [data, setData] = useState<PathsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!courseInput) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchPaths(courseInput);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  if (!courseInput) {
    return <EmptyState message="Load a course definition to enumerate learning paths." />;
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Learning Paths</h2>
        <button
          onClick={run}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Computing..." : "Run"}
        </button>
      </div>

      {error && <ErrorAlert message={error} />}
      {loading && <LoadingSpinner className="py-8" />}

      {data && !loading && (
        <>
          <Card title="Total Paths">
            <p className="text-2xl font-bold text-indigo-600">{data.total}</p>
          </Card>

          <Card title="All Paths">
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {data.paths.map((path, i) => (
                <div
                  key={i}
                  className="flex items-center gap-1 text-sm font-mono text-gray-700 bg-gray-50 rounded px-3 py-2"
                >
                  <span className="text-xs text-gray-400 mr-2 w-6 text-right shrink-0">
                    {i + 1}.
                  </span>
                  {path.map((item, j) => (
                    <span key={j} className="flex items-center gap-1">
                      {j > 0 && <span className="text-gray-400">-&gt;</span>}
                      <span className="bg-white border border-gray-200 rounded px-1.5 py-0.5 text-xs">
                        {item}
                      </span>
                    </span>
                  ))}
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
