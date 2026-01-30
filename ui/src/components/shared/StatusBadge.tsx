interface StatusBadgeProps {
  passed: boolean;
  label?: string;
}

export function StatusBadge({ passed, label }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        passed
          ? "bg-green-100 text-green-800"
          : "bg-red-100 text-red-800"
      }`}
    >
      {label ?? (passed ? "Pass" : "Fail")}
    </span>
  );
}
