import { RefreshCw } from "lucide-react";
import { Component, type ErrorInfo, type ReactNode } from "react";

import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/** Catches render-time errors so one broken page cannot blank the app. */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  override state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  override componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Unhandled UI error:", error, info.componentStack);
  }

  private readonly reset = () => this.setState({ error: null });

  override render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    if (this.props.fallback) return this.props.fallback(error, this.reset);

    return (
      <div className="flex min-h-[60vh] items-center justify-center p-6">
        <div className="max-w-md space-y-4 text-center">
          <div className="space-y-1.5">
            <h2 className="text-lg font-semibold">This view crashed</h2>
            <p className="text-muted-foreground text-sm">
              An unexpected error occurred while rendering. You can retry, or
              reload the application.
            </p>
          </div>
          <pre className="bg-muted text-muted-foreground scrollbar-thin max-h-32 overflow-auto rounded-lg p-3 text-left font-mono text-xs">
            {error.message}
          </pre>
          <div className="flex justify-center gap-2">
            <Button variant="outline" size="sm" onClick={this.reset}>
              <RefreshCw className="size-4" />
              Try again
            </Button>
            <Button size="sm" onClick={() => window.location.reload()}>
              Reload app
            </Button>
          </div>
        </div>
      </div>
    );
  }
}
