import React from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  Users,
  Compass,
  Sliders,
  Settings,
  Waves,
  X,
  Lock,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

interface NavItem {
  name: string;
  icon: React.ElementType;
  active?: boolean;
  statusText?: string;
  phase?: string;
}

const navItems: NavItem[] = [
  {
    name: 'Dashboard',
    icon: LayoutDashboard,
    active: true,
  },
  {
    name: 'Risk Analysis',
    icon: ShieldAlert,
    statusText: 'Planned',
    phase: 'Phase 1',
  },
  {
    name: 'Impact Assessment',
    icon: Users,
    statusText: 'Planned',
    phase: 'Phase 2',
  },
  {
    name: 'Shelters & Routes',
    icon: Compass,
    statusText: 'Planned',
    phase: 'Phase 3',
  },
  {
    name: 'Scenario Simulation',
    icon: Sliders,
    statusText: 'Planned',
    phase: 'Phase 4',
  },
  {
    name: 'Settings',
    icon: Settings,
    statusText: 'Planned',
    phase: 'Phase 5',
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-800 bg-slate-900 transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand / Logo */}
        <div className="flex h-16 items-center justify-between border-b border-slate-800 px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-500/10 border border-teal-500/30 text-teal-400">
              <Waves className="h-5 w-5" />
            </div>
            <div>
              <span className="text-base font-bold tracking-wider text-white">
                PRAVAAH
              </span>
              <span className="block text-[10px] uppercase font-mono tracking-widest text-slate-400">
                Disaster Intel
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mb-2 px-3 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Platform Modules
          </div>
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.name} className="relative">
                  {item.active ? (
                    <div
                      className="flex items-center justify-between rounded-lg bg-slate-800 px-3.5 py-2.5 text-sm font-medium text-white shadow-sm ring-1 ring-slate-700/60"
                      aria-current="page"
                    >
                      <div className="flex items-center gap-3">
                        <Icon className="h-4 w-4 text-teal-400" />
                        <span>{item.name}</span>
                      </div>
                      <span className="h-1.5 w-1.5 rounded-full bg-teal-400" />
                    </div>
                  ) : (
                    <div
                      className="group flex cursor-not-allowed items-center justify-between rounded-lg px-3.5 py-2.5 text-sm font-medium text-slate-400 hover:bg-slate-800/40 opacity-70"
                      title={`${item.name} is planned for ${item.phase} and not implemented in Phase 0.`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon className="h-4 w-4 text-slate-500 group-hover:text-slate-400" />
                        <span>{item.name}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] font-medium text-slate-400 border border-slate-700">
                          {item.statusText}
                        </span>
                        <Lock className="h-3 w-3 text-slate-500" />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          <div className="mt-8 rounded-xl border border-slate-800 bg-slate-950/60 p-4">
            <h2 className="text-xs font-semibold text-slate-300">Phase 0 Scope</h2>
            <p className="mt-1 text-xs leading-relaxed text-slate-400">
              Only application foundation, health verification, and project scaffolding are active. Predictive and routing modules are intentionally not functional yet.
            </p>
          </div>
        </div>

        {/* Footer info */}
        <div className="border-t border-slate-800 p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Core Version</span>
            <span className="font-mono text-slate-300">v0.1.0</span>
          </div>
        </div>
      </aside>
    </>
  );
};
