import { useState } from "react";
import { useCourse } from "../../hooks/useCourse";
import { useAssessment } from "../../hooks/useAssessment";
import { Card } from "../shared/Card";
import { StatusBadge } from "../shared/StatusBadge";
import { LoadingSpinner } from "../shared/LoadingSpinner";
import { ErrorAlert } from "../shared/ErrorAlert";
import { EmptyState } from "../shared/EmptyState";

export function AssessPage() {
  const { courseInput } = useCourse();
  const assessment = useAssessment();

  const [beta, setBeta] = useState(0.1);
  const [eta, setEta] = useState(0.1);

  if (!courseInput) {
    return <EmptyState message="Load a course definition to start an assessment." />;
  }

  // Phase 1: Configuration
  if (assessment.phase === "idle") {
    return (
      <div className="max-w-xl space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">Assessment</h2>
        {assessment.error && <ErrorAlert message={assessment.error} />}

        <Card title="BLIM Parameters">
          <div className="grid grid-cols-2 gap-4">
            <label className="block">
              <span className="text-xs text-gray-600">Beta (slip)</span>
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
              <span className="text-xs text-gray-600">Eta (guess)</span>
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

        <button
          onClick={() => assessment.start(courseInput, beta, eta)}
          disabled={assessment.loading}
          className="w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {assessment.loading ? "Starting..." : "Start Assessment"}
        </button>
      </div>
    );
  }

  // Phase 2: Q&A
  if (assessment.phase === "in_progress") {
    return (
      <div className="max-w-xl space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Assessment</h2>
          <button
            onClick={assessment.reset}
            className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Restart
          </button>
        </div>

        {assessment.error && <ErrorAlert message={assessment.error} />}

        <Card title={`Question ${assessment.steps.length + 1}`}>
          <div className="text-center py-4">
            <p className="text-sm text-gray-500 mb-2">
              Can the learner answer correctly?
            </p>
            <p className="text-xl font-bold text-gray-900 mb-6">
              {assessment.currentItem}
            </p>
            <div className="flex justify-center gap-3">
              <button
                onClick={() => assessment.respond(true)}
                disabled={assessment.loading}
                className="px-6 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                Correct
              </button>
              <button
                onClick={() => assessment.respond(false)}
                disabled={assessment.loading}
                className="px-6 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                Incorrect
              </button>
            </div>
            {assessment.loading && <LoadingSpinner className="mt-4" />}
          </div>
        </Card>

        {assessment.steps.length > 0 && (
          <Card title="History">
            <div className="divide-y divide-gray-100">
              {assessment.steps.map((step, i) => (
                <div key={i} className="flex items-center justify-between py-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{i + 1}.</span>
                    <span className="text-sm font-mono text-gray-700">
                      {step.item_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge
                      passed={step.correct}
                      label={step.correct ? "Correct" : "Incorrect"}
                    />
                    <span className="text-xs text-gray-400">
                      H: {step.entropy_before.toFixed(2)} → {step.entropy_after.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    );
  }

  // Phase 3: Summary
  return (
    <div className="max-w-xl space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Assessment Complete</h2>
        <button
          onClick={assessment.reset}
          className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200"
        >
          New Assessment
        </button>
      </div>

      {assessment.summary && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Card title="Total Questions">
              <p className="text-2xl font-bold text-indigo-600">
                {assessment.summary.total_questions}
              </p>
            </Card>
            <Card title="Confidence">
              <p className="text-2xl font-bold text-indigo-600">
                {(assessment.summary.confidence * 100).toFixed(1)}%
              </p>
            </Card>
          </div>

          <Card title="Mastered">
            {assessment.summary.mastered.length > 0 ? (
              <div className="flex flex-wrap gap-1">
                {assessment.summary.mastered.map((id) => (
                  <span
                    key={id}
                    className="px-2 py-0.5 text-xs font-mono bg-green-100 text-green-800 rounded"
                  >
                    {id}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">None</p>
            )}
          </Card>

          <Card title="Not Mastered">
            {assessment.summary.not_mastered.length > 0 ? (
              <div className="flex flex-wrap gap-1">
                {assessment.summary.not_mastered.map((id) => (
                  <span
                    key={id}
                    className="px-2 py-0.5 text-xs font-mono bg-red-100 text-red-800 rounded"
                  >
                    {id}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">None</p>
            )}
          </Card>

          <Card title="History">
            <div className="divide-y divide-gray-100">
              {assessment.steps.map((step, i) => (
                <div key={i} className="flex items-center justify-between py-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{i + 1}.</span>
                    <span className="text-sm font-mono text-gray-700">
                      {step.item_id}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge
                      passed={step.correct}
                      label={step.correct ? "Correct" : "Incorrect"}
                    />
                    <span className="text-xs text-gray-400">
                      H: {step.entropy_before.toFixed(2)} → {step.entropy_after.toFixed(2)}
                    </span>
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
