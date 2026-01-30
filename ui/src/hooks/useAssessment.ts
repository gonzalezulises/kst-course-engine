import { useState, useCallback } from "react";
import type { CourseInput, AssessStepResponse, AssessSummaryResponse } from "../api/types";
import { startAssessment, respondAssessment, fetchAssessmentSummary } from "../api/endpoints";

type AssessmentPhase = "idle" | "in_progress" | "complete";

export interface AssessmentState {
  phase: AssessmentPhase;
  sessionId: string | null;
  currentItem: string | null;
  steps: AssessStepResponse[];
  summary: AssessSummaryResponse | null;
  error: string | null;
  loading: boolean;
}

export function useAssessment() {
  const [state, setState] = useState<AssessmentState>({
    phase: "idle",
    sessionId: null,
    currentItem: null,
    steps: [],
    summary: null,
    error: null,
    loading: false,
  });

  const start = useCallback(async (courseInput: CourseInput, beta: number, eta: number) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const res = await startAssessment({
        domain: courseInput.domain,
        prerequisites: courseInput.prerequisites,
        beta,
        eta,
      });
      setState({
        phase: "in_progress",
        sessionId: res.session_id,
        currentItem: res.first_item,
        steps: [],
        summary: null,
        error: null,
        loading: false,
      });
    } catch (e) {
      setState((s) => ({
        ...s,
        loading: false,
        error: e instanceof Error ? e.message : String(e),
      }));
    }
  }, []);

  const respond = useCallback(async (correct: boolean) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const sessionId = state.sessionId;
      if (!sessionId) throw new Error("No active session");

      const res = await respondAssessment(sessionId, { correct });
      const newSteps = [...state.steps, res.step];

      if (res.is_complete) {
        const summary = await fetchAssessmentSummary(sessionId);
        setState({
          phase: "complete",
          sessionId,
          currentItem: null,
          steps: newSteps,
          summary,
          error: null,
          loading: false,
        });
      } else {
        setState({
          phase: "in_progress",
          sessionId,
          currentItem: res.next_item,
          steps: newSteps,
          summary: null,
          error: null,
          loading: false,
        });
      }
    } catch (e) {
      setState((s) => ({
        ...s,
        loading: false,
        error: e instanceof Error ? e.message : String(e),
      }));
    }
  }, [state.sessionId, state.steps]);

  const reset = useCallback(() => {
    setState({
      phase: "idle",
      sessionId: null,
      currentItem: null,
      steps: [],
      summary: null,
      error: null,
      loading: false,
    });
  }, []);

  return { ...state, start, respond, reset };
}
