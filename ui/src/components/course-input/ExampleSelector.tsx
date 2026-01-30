import { EXAMPLES } from "../../data/examples";

interface ExampleSelectorProps {
  onSelect: (yaml: string) => void;
}

export function ExampleSelector({ onSelect }: ExampleSelectorProps) {
  return (
    <select
      defaultValue=""
      onChange={(e) => {
        const example = EXAMPLES.find((ex) => ex.name === e.target.value);
        if (example) onSelect(example.yaml);
      }}
      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
    >
      <option value="" disabled>
        Load an example...
      </option>
      {EXAMPLES.map((ex) => (
        <option key={ex.name} value={ex.name}>
          {ex.name} — {ex.description}
        </option>
      ))}
    </select>
  );
}
