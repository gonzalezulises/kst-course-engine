import { useContext } from "react";
import { CourseContext, type CourseContextValue } from "../context/CourseContext";

export function useCourse(): CourseContextValue {
  const ctx = useContext(CourseContext);
  if (!ctx) {
    throw new Error("useCourse must be used within a CourseProvider");
  }
  return ctx;
}
