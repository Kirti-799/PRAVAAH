/**
 * frontend/src/components/common/ErrorBoundary.tsx
 *
 * Top-level and component-level React Error Boundary for PRAVAAH.
 * Catches unhandled runtime exceptions (including Leaflet map errors, canvas issues,
 * and asynchronous data-parsing failures) to guarantee the page never vanishes or blanks out.
 */

import { Component, type ReactNode, type ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
  isMapContainer?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[PRAVAAH ErrorBoundary] Caught unhandled component error:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.isMapContainer) {
        return (
          <div className="flex h-full w-full flex-col items-center justify-center rounded-xl border border-[#EAE3D9] bg-[#FFFDF9] p-6 text-center text-[#3E3026]">
            <AlertTriangle className="h-8 w-8 text-[#B45309] mb-2" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#2C221E]">
              {this.props.fallbackTitle || 'Map Layer Preview Unavailable'}
            </h4>
            <p className="mt-1 max-w-sm text-xs text-[#635347]">
              {this.props.fallbackMessage || 'The spatial geometry layer encountered a rendering issue. Map telemetry is preserved.'}
            </p>
            <button
              onClick={this.handleReset}
              className="mt-3 flex items-center gap-1.5 rounded-lg border border-[#EAE3D9] bg-[#FFFFFF] px-3 py-1 text-xs font-semibold text-[#8B4513] shadow-xs hover:bg-[#F5EFEB] transition-colors"
            >
              <RefreshCw className="h-3 w-3" />
              <span>Retry Map View</span>
            </button>
          </div>
        );
      }

      return (
        <div className="flex min-h-[300px] h-full w-full flex-col items-center justify-center bg-[#FBF9F5] p-6 text-[#2C221E]">
          <div className="max-w-md rounded-2xl border border-[#EAE3D9] bg-[#FFFFFF] p-6 shadow-sm text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-amber-800 mb-4">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <h3 className="text-base font-bold text-[#2C221E]">
              {this.props.fallbackTitle || 'Workspace Recovered'}
            </h3>
            <p className="mt-2 text-xs text-[#635347] leading-relaxed">
              {this.props.fallbackMessage ||
                'A temporary component issue occurred, but PRAVAAH system services remain operational. Click below to refresh the active workspace.'}
            </p>
            <div className="mt-5 flex items-center justify-center gap-3">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 rounded-xl bg-[#8B4513] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#70360E] transition-all"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                <span>Reload Workspace</span>
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
