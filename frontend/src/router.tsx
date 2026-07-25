import { lazy, Suspense } from "react";
import { createBrowserRouter, type RouteObject } from "react-router-dom";

import { ErrorBoundary } from "@/components/common/error-boundary";
import { PageLoader } from "@/components/common/loading";
import { AppShell } from "@/components/layout/app-shell";

// Route-level code splitting keeps the initial bundle small.
const DashboardPage = lazy(() => import("@/pages/dashboard"));
const RepositoriesPage = lazy(() => import("@/pages/repositories"));
const ChatPage = lazy(() => import("@/pages/chat"));
const GraphPage = lazy(() => import("@/pages/graph"));
const ReportPage = lazy(() => import("@/pages/report"));
const SettingsPage = lazy(() => import("@/pages/settings"));
const NotFoundPage = lazy(() => import("@/pages/not-found"));

/** Wrap each route so a failure is contained to the page. */
function route(element: React.ReactNode): React.ReactNode {
  return (
    <ErrorBoundary>
      <Suspense fallback={<PageLoader />}>{element}</Suspense>
    </ErrorBoundary>
  );
}

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: route(<DashboardPage />) },
      { path: "repositories", element: route(<RepositoriesPage />) },
      { path: "chat", element: route(<ChatPage />) },
      { path: "graph", element: route(<GraphPage />) },
      { path: "report", element: route(<ReportPage />) },
      { path: "settings", element: route(<SettingsPage />) },
      { path: "*", element: route(<NotFoundPage />) },
    ],
  },
];

export const router = createBrowserRouter(routes);
