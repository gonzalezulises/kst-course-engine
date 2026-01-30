import { useState } from "react";
import { useCourse } from "../../hooks/useCourse";
import { fetchValidation } from "../../api/endpoints";
import type { ValidationResponse } from "../../api/types";
import { Card } from "../shared/Card";
import { StatusBadge } from "../shared/StatusBadge";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { ErrorAlert } from "../shared/ErrorAlert";
import { EmptyState } from "../shared/EmptyState";

export function ValidatePage() {
  const { courseInput } = useCourse();
  const [data, setData] = useState<ValidationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (!courseInput) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchValidation(courseInput);
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  if (!courseInput) {
    return <EmptyState message="Load a course definition to validate it." />;
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Validate</h2>
        <button
          onClick={run}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Validating..." : "Run"}
        </button>
      </div>

      {error && <ErrorAlert message={error} />}
      {loading && <LoadingSpinner className="py-8" />}

      {data && !loading && (
        <>
          <div
            className={`rounded-md p-4 ${
              data.is_valid
                ? "bg-green-50 border border-green-200"
                : "bg-red-50 border border-red-200"
            }`}
          >
            <div className="flex items-center gap-2">
              <StatusBadge passed={data.is_valid} label={data.is_valid ? "Valid" : "Invalid"} />
              <span className="text-sm font-medium text-gray-700">{data.summary}</span>
            </div>
          </div>

          <Card title="Axiom Checks">
            <div className="divide-y divide-gray-100">
              {data.results.map((check) => (
                <div key={check.property_name} className="flex items-start gap-3 py-2.5">
                  <StatusBadge passed={check.passed} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-800">
                      {check.property_name}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">{check.message}</p>
                    <p className="text-xs text-gray-400 mt-0.5 italic">
                      {check.reference}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
