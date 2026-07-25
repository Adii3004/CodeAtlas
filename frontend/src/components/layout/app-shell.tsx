import { AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { PageTransition } from "@/components/common/page-transition";
import { Header } from "@/components/layout/header";
import { Sidebar } from "@/components/layout/sidebar";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
} from "@/components/ui/sheet";
import { useLocalStorage } from "@/hooks/use-local-storage";
import { cn } from "@/lib/utils";

/**
 * Desktop-first application shell: fixed sidebar, sticky header, and a
 * single scrollable content region. Below `lg` the sidebar becomes a sheet.
 */
export function AppShell() {
  const [collapsed, setCollapsed] = useLocalStorage(
    "codeatlas.sidebar-collapsed",
    false,
  );
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const location = useLocation();

  // Close the mobile sheet whenever the route changes.
  useEffect(() => setMobileNavOpen(false), [location.pathname]);

  return (
    <div className="bg-background surface-grain flex h-dvh w-full overflow-hidden">
      <aside
        className={cn(
          "hidden shrink-0 lg:block",
          "transition-[width] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)]",
          collapsed ? "w-[4.25rem]" : "w-64",
        )}
      >
        <Sidebar
          collapsed={collapsed}
          onToggleCollapsed={() => setCollapsed((value) => !value)}
        />
      </aside>

      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-64 p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SheetDescription className="sr-only">
            Primary application navigation
          </SheetDescription>
          <Sidebar
            collapsed={false}
            onToggleCollapsed={() => undefined}
            onNavigate={() => setMobileNavOpen(false)}
            className="border-r-0"
          />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <Header onOpenMobileNav={() => setMobileNavOpen(true)} />
        <main
          id="main-content"
          className="scrollbar-thin flex-1 overflow-y-auto"
        >
          <AnimatePresence mode="wait" initial={false}>
            <PageTransition key={location.pathname}>
              <Outlet />
            </PageTransition>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
