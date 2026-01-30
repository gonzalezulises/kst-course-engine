import { useCourse } from "../../hooks/useCourse";
import { YamlEditor } from "./YamlEditor";
import { FileUpload } from "./FileUpload";
import { ExampleSelector } from "./ExampleSelector";

export function CourseInputPanel() {
  const { yamlSource, courseInput, parseError, setYaml } = useCourse();

  return (
    <div className="flex flex-col gap-3 p-4">
      <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
        Course Definition
      </h2>

      <ExampleSelector onSelect={setYaml} />
      <FileUpload onLoad={setYaml} />
      <YamlEditor value={yamlSource} onChange={setYaml} />

      {parseError && (
        <div className="text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
          {parseError}
        </div>
      )}

      {courseInput && (
        <div className="text-xs text-green-700 bg-green-50 border border-green-200 rounded p-2">
          Loaded: <span className="font-medium">{courseInput.domain.name}</span>{" "}
          ({courseInput.domain.items.length} items,{" "}
          {courseInput.prerequisites?.edges.length ?? 0} edges)
        </div>
      )}
    </div>
  );
}
