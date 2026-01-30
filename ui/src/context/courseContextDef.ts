import { createContext } from "react";
import type { CourseInput } from "../api/types";

export interface CourseContextValue {
  yamlSource: string;
  courseInput: CourseInput | null;
  parseError: string | null;
  setYaml: (yaml: string) => void;
}

export const CourseContext = createContext<CourseContextValue | null>(null);
