import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import type { HealthStatus } from '../../types/api';

interface AppLayoutProps {
  children: React.ReactNode;
  isLoading: boolean;
  healthData: HealthStatus | null;
  error: string | null;
  onRetry: () => void;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  isLoading,
  healthData,
  error,
  onRetry,
}) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex flex-1 flex-col overflow-hidden">
        <Header
          onMenuToggle={() => setSidebarOpen(true)}
          isLoading={isLoading}
          healthData={healthData}
          error={error}
          onRetry={onRetry}
        />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
};
