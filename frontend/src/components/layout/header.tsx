import { Menu } from "lucide-react";
import { useLocation } from "react-router-dom";

import { NAV_ITEMS } from "@/components/layout/nav-items";
import { ConnectionStatus } from "@/components/common/connection-status";
import { ThemeToggle } from "@/components/common/theme-toggle";
import { Button } from "@/components/ui/button";

function useCurrentNavItem() {
  const { pathname } = useLocation();
  return (
    NAV_ITEMS.find((item) =>
      item.end ? pathname === item.to : pathname.startsWith(item.to),
    ) ?? null
  );
}

export function Header({ onOpenMobileNav }: { onOpenMobileNav: () => void }) {
  const current = useCurrentNavItem();

  return (
    <header className="bg-background/80 sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b px-4 backdrop-blur-sm lg:px-6">
      <Button
        variant="ghost"
        size="icon-sm"
        className="lg:hidden"
        onClick={onOpenMobileNav}
        aria-label="Open navigation"
      >
        <Menu className="size-4" />
      </Button>

      <div className="min-w-0 flex-1">
        <h1 className="truncate text-sm font-semibold">
          {current?.title ?? "CodeAtlas"}
        </h1>
        <p className="text-muted-foreground hidden truncate text-xs sm:block">
          {current?.description ?? "AI-powered repository intelligence"}
        </p>
      </div>

      <div className="flex items-center gap-1.5">
        <ConnectionStatus />
        <ThemeToggle />
      </div>
    </header>
  );
}
