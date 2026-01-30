import { useCourse } from "../../hooks/useCourse";

interface HeaderProps {
  onToggleSidebar: () => void;
}

export function Header({ onToggleSidebar }: HeaderProps) {
  const { courseInput } = useCourse();

  return (
    <header className="flex items-center gap-3 h-14 px-4 border-b border-gray-200 bg-white">
      <button
        onClick={onToggleSidebar}
        className="lg:hidden p-1.5 rounded-md text-gray-500 hover:bg-gray-100"
        aria-label="Toggle sidebar"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <h1 className="text-sm font-medium text-gray-700 truncate">
        {courseInput ? courseInput.domain.name : "No course loaded"}
      </h1>
    </header>
  );
}
