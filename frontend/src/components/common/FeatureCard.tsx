import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface FeatureCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  targetPhase: string;
  statusLabel?: string;
  capabilities: string[];
}

export const FeatureCard: React.FC<FeatureCardProps> = ({
  title,
  description,
  icon: Icon,
  targetPhase,
  statusLabel = 'Planned',
  capabilities,
}) => {
  return (
    <div className="group relative flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-5 transition-all duration-200 hover:border-slate-700 hover:bg-slate-900/80">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-500/10 border border-teal-500/20 text-teal-400 group-hover:scale-105 transition-transform">
            <Icon className="h-5 w-5" />
          </div>
          <div className="flex flex-col items-end">
            <span className="inline-flex items-center rounded-full bg-slate-800 px-2.5 py-0.5 text-[11px] font-medium text-slate-300 border border-slate-700">
              {statusLabel}
            </span>
            <span className="mt-1 text-[10px] font-mono text-slate-500">
              {targetPhase}
            </span>
          </div>
        </div>

        <h3 className="mt-4 text-base font-semibold text-white">
          {title}
        </h3>
        <p className="mt-2 text-xs leading-relaxed text-slate-400">
          {description}
        </p>
      </div>

      <div className="mt-5 border-t border-slate-800/80 pt-3">
        <span className="text-[10px] uppercase font-mono tracking-wider text-slate-400">
          Future Capabilities:
        </span>
        <ul className="mt-1.5 space-y-1">
          {capabilities.map((cap, idx) => (
            <li key={idx} className="flex items-center gap-1.5 text-xs text-slate-400">
              <span className="h-1 w-1 rounded-full bg-teal-500/60" />
              <span>{cap}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
