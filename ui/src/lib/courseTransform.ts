import yaml from "js-yaml";
import type { CourseInput } from "../api/types";

interface YamlItem {
  id: string;
  label?: string;
}

interface YamlDomain {
  name: string;
  description?: string;
  items: YamlItem[];
}

interface YamlPrerequisites {
  edges?: [string, string][];
}

interface YamlCourse {
  domain: YamlDomain;
  prerequisites?: YamlPrerequisites;
}

export function yamlToCourseInput(yamlStr: string): CourseInput {
  const parsed = yaml.load(yamlStr) as YamlCourse;

  if (!parsed || !parsed.domain) {
    throw new Error("Invalid YAML: missing 'domain' section");
  }

  return {
    domain: {
      name: parsed.domain.name,
      description: parsed.domain.description ?? "",
      items: parsed.domain.items.map((item) => ({
        id: item.id,
        label: item.label ?? "",
      })),
    },
    prerequisites: {
      edges: parsed.prerequisites?.edges ?? [],
    },
  };
}
