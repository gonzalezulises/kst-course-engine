import { useCallback, useState } from "react";

interface FileUploadProps {
  onLoad: (content: string) => void;
}

export function FileUpload({ onLoad }: FileUploadProps) {
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === "string") {
          onLoad(reader.result);
        }
      };
      reader.readAsText(file);
    },
    [onLoad],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`flex flex-col items-center justify-center gap-1 p-4 border-2 border-dashed rounded-md cursor-pointer transition-colors ${
        dragging
          ? "border-indigo-400 bg-indigo-50"
          : "border-gray-300 hover:border-gray-400"
      }`}
    >
      <label className="cursor-pointer text-xs text-gray-500">
        Drop a <span className="font-medium">.kst.yaml</span> file or{" "}
        <span className="text-indigo-600 underline">browse</span>
        <input
          type="file"
          accept=".yaml,.yml"
          onChange={handleChange}
          className="hidden"
        />
      </label>
    </div>
  );
}
