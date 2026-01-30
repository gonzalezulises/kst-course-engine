import { useState, useCallback, type ReactNode } from "react";
import { yamlToCourseInput } from "../lib/courseTransform";
import { CourseContext } from "./courseContextDef";

export type { CourseContextValue } from "./courseContextDef";
export { CourseContext } from "./courseContextDef";

export function CourseProvider({ children }: { children: ReactNode }) {
  const [yamlSource, setYamlSource] = useState("");
  const [courseInput, setCourseInput] = useState<import("../api/types").CourseInput | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  const setYaml = useCallback((yaml: string) => {
    setYamlSource(yaml);
    if (!yaml.trim()) {
      setCourseInput(null);
      setParseError(null);
      return;
    }
    try {
      const input = yamlToCourseInput(yaml);
      setCourseInput(input);
      setParseError(null);
    } catch (e) {
      setCourseInput(null);
      setParseError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  return (
    <CourseContext.Provider value={{ yamlSource, courseInput, parseError, setYaml }}>
      {children}
    </CourseContext.Provider>
  );
}
