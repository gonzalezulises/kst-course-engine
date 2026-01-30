interface YamlEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export function YamlEditor({ value, onChange }: YamlEditorProps) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Paste or type YAML here..."
      spellCheck={false}
      className="w-full h-64 p-3 font-mono text-xs bg-gray-50 border border-gray-200 rounded-md resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
    />
  );
}
