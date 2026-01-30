import { useState } from "react";
import { useCourse } from "../../hooks/useCourse";
import { fetchSimulation } from "../../api/endpoints";
import type { SimulateResponse } from "../../api/types";
import { Card } from "../shared/Card";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { ErrorAlert } from "../shared/ErrorAlert";
import { EmptyState } from "../shared/EmptyState";

export function SimulatePage() {
  const { courseInput } = useCourse();
  const [data, setData] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [learners, setLearners] = useState(100);
  const [beta, setBeta] = useState(0.1);
  const [eta, setEta] = useState(0.1);
  const [seed, setSeed] = useState<string>("42");

  const run = async () => {
    if (!courseInput) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchSimulation({
        domain: courseInput.domain,
        prerequisites: courseInput.prerequisites,
        learners,
        beta,
        eta,
        seed: seed.trim() ? Number(seed) : null,
      });
      setData(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  if (!courseInput) {
    return <EmptyState message="Load a course definition to simulate learners." />;
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Simulate</h2>
        <button
          onClick={run}
          disabled={loading}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Simulating..." : "Run"}
        </button>
      </div>

      <Card title="Configuration">
        <div className="grid grid-cols-2 gap-4">
          <label className="block">
            <span className="text-xs text-gray-600">Learners</span>
            <input
              type="number"
              value={learners}
              onChange={(e) => setLearners(Number(e.target.value))}
              min={1}
              max={10000}
              className="mt-1 block w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-600">Seed (optional)</span>
            <input
              type="text"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              placeholder="Random"
              className="mt-1 block w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-600">Beta (slip prob)</span>
            <input
              type="number"
              value={beta}
              onChange={(e) => setBeta(Number(e.target.value))}
              min={0}
              max={0.49}
              step={0.01}
              className="mt-1 block w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </label>
          <label className="block">
            <span className="text-xs text-gray-600">Eta (guess prob)</span>
            <input
              type="number"
              value={eta}
              onChange={(e) => setEta(Number(e.target.value))}
              min={0}
              max={0.49}
              step={0.01}
              className="mt-1 block w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </label>
        </div>
      </Card>

      {error && <ErrorAlert message={error} />}
      {loading && <LoadingSpinner className="py-8" />}

      {data && !loading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <Card title="Learners">
            <p className="text-2xl font-bold text-indigo-600">{data.learners}</p>
          </Card>
          <Card title="Accuracy">
            <p className="text-2xl font-bold text-indigo-600">{data.accuracy_pct}%</p>
            <p className="text-xs text-gray-500">{data.accuracy}/{data.learners} correct</p>
          </Card>
          <Card title="Avg Questions">
            <p className="text-2xl font-bold text-indigo-600">{data.avg_questions}</p>
          </Card>
          <Card title="Expected Steps">
            <p className="text-2xl font-bold text-indigo-600">{data.expected_steps}</p>
            <p className="text-xs text-gray-500">Markov model</p>
          </Card>
          <Card title="Simulated Avg Steps">
            <p className="text-2xl font-bold text-indigo-600">{data.simulated_avg_steps}</p>
            <p className="text-xs text-gray-500">Monte Carlo</p>
          </Card>
        </div>
      )}
    </div>
  );
}
