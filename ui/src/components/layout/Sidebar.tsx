import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Info" },
  { to: "/validate", label: "Validate" },
  { to: "/paths", label: "Paths" },
  { to: "/simulate", label: "Simulate" },
  { to: "/export", label: "Export" },
  { to: "/assess", label: "Assess" },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Overlay for mobile */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/30 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-56 bg-white border-r border-gray-200 transform transition-transform lg:translate-x-0 lg:static lg:z-auto ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-2 px-4 h-14 border-b border-gray-200">
          <span className="font-semibold text-sm text-gray-800 tracking-tight">
            KST Engine
          </span>
        </div>
        <nav className="flex flex-col gap-1 p-2">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={onClose}
              className={({ isActive }) =>
                `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-indigo-50 text-indigo-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
