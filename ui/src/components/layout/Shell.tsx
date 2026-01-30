import { useState, type ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { CourseInputPanel } from "../course-input/CourseInputPanel";

interface ShellProps {
  children: ReactNode;
}

export function Shell({ children }: ShellProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex flex-col flex-1 min-w-0">
        <Header onToggleSidebar={() => setSidebarOpen((o) => !o)} />
        <div className="flex flex-1 overflow-hidden">
          <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white overflow-y-auto hidden md:block">
            <CourseInputPanel />
          </div>
          <main className="flex-1 overflow-y-auto p-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
