import { RouterProvider } from "react-router-dom";

import { ErrorBoundary } from "@/components/common/error-boundary";
import { AppProviders } from "@/providers/app-providers";
import { router } from "@/router";

export default function App() {
  return (
    <ErrorBoundary>
      <AppProviders>
        <a
          href="#main-content"
          className="bg-background focus:ring-ring sr-only z-50 rounded-md border px-3 py-2 text-sm focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:ring-2"
        >
          Skip to content
        </a>
        <RouterProvider router={router} />
      </AppProviders>
    </ErrorBoundary>
  );
}
