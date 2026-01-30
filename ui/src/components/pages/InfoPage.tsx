import { useState } from "react";
import { useCourse } from "../../hooks/useCourse";
import { fetchInfo } from "../../api/endpoints";
import type { InfoResponse } from "../../api/types";
import { Card } from "../shared/Card";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { ErrorAlert } from "../shared/ErrorAlert";
import { EmptyState } from "../shared/EmptyState";

export function InfoPage() {
  const { courseInput } = useCourse();
  const [data, setData] = useState<InfoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!courseInput) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchInfo(courseInput);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  if (!courseInput) {
    return <EmptyState message="Load a course definition to see its overview." />;
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Course Info</h2>
        <button
          onClick={run}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Run"}
        </button>
      </div>

      {error && <ErrorAlert message={error} />}
      {loading && <LoadingSpinner className="py-8" />}

      {data && !loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <Card title="Name">
            <p className="text-lg font-semibold">{data.name}</p>
            {data.description && (
              <p className="text-xs text-gray-500 mt-1">{data.description}</p>
            )}
          </Card>
          <Card title="Items">
            <p className="text-2xl font-bold text-indigo-600">{data.items}</p>
          </Card>
          <Card title="Knowledge States">
            <p className="text-2xl font-bold text-indigo-600">{data.states}</p>
          </Card>
          <Card title="Prerequisites">
            <p className="text-2xl font-bold text-indigo-600">{data.prerequisites}</p>
          </Card>
          <Card title="Critical Path Length">
            <p className="text-2xl font-bold text-indigo-600">{data.critical_path_length}</p>
          </Card>
          <Card title="Learning Paths">
            <p className="text-2xl font-bold text-indigo-600">{data.learning_paths}</p>
          </Card>
          <Card title="Critical Path" className="col-span-full">
            <p className="text-sm font-mono text-gray-700">
              {data.critical_path.join(" -> ")}
            </p>
          </Card>
        </div>
      )}
    </div>
  );
}
