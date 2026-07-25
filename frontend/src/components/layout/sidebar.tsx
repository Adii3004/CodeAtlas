import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { NavLink } from "react-router-dom";

import { NAV_ITEMS } from "@/components/layout/nav-items";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

function BrandMark({ collapsed }: { collapsed: boolean }) {
  return (
    <div className="flex h-16 items-center gap-2.5 px-3.5">
      <div
        className="bg-foreground text-background flex size-8 shrink-0 items-center justify-center rounded-lg font-semibold"
        aria-hidden
      >
        <span className="font-editorial text-[15px]">CA</span>
      </div>
      {!collapsed && (
        <div className="min-w-0 leading-tight">
          <p className="truncate text-[15px] font-semibold tracking-tight">
            CodeAtlas
          </p>
          <p className="font-editorial text-accent truncate text-xs italic">
            Repository Intelligence
          </p>
        </div>
      )}
    </div>
  );
}

export interface SidebarProps {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  /** Called after navigating — used to close the mobile sheet. */
  onNavigate?: () => void;
  className?: string;
}

export function Sidebar({
  collapsed,
  onToggleCollapsed,
  onNavigate,
  className,
}: SidebarProps) {
  return (
    <div
      className={cn(
        "bg-sidebar text-sidebar-foreground flex h-full flex-col border-r",
        className,
      )}
    >
      <BrandMark collapsed={collapsed} />

      <nav
        aria-label="Main navigation"
        className="scrollbar-thin flex-1 space-y-0.5 overflow-y-auto px-2.5 py-2"
      >
        {NAV_ITEMS.map((item) => {
          const link = (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={onNavigate}
              className={({ isActive }) =>
                cn(
                  "group relative flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm font-medium",
                  "transition-[background-color,color] duration-200 ease-out",
                  "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  "focus-visible:ring-ring focus-visible:outline-none focus-visible:ring-2",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-muted-foreground",
                  collapsed && "justify-center px-0",
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive ? (
                    <span
                      className="bg-accent absolute top-1/2 left-0 h-5 w-0.5 -translate-y-1/2 rounded-r-full"
                      aria-hidden
                    />
                  ) : null}
                  <item.icon
                    className={cn(
                      "size-4 shrink-0 transition-colors",
                      isActive && "text-accent",
                    )}
                    aria-hidden
                  />
                  {!collapsed && <span className="truncate">{item.title}</span>}
                  {collapsed && <span className="sr-only">{item.title}</span>}
                </>
              )}
            </NavLink>
          );

          return collapsed ? (
            <Tooltip key={item.to}>
              <TooltipTrigger asChild>{link}</TooltipTrigger>
              <TooltipContent side="right">{item.title}</TooltipContent>
            </Tooltip>
          ) : (
            link
          );
        })}
      </nav>

      <div className="hidden p-2.5 lg:block">
        <Button
          variant="ghost"
          size={collapsed ? "icon-sm" : "sm"}
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          className={cn(
            "text-muted-foreground w-full justify-start",
            collapsed && "mx-auto w-8 justify-center",
          )}
        >
          {collapsed ? (
            <PanelLeftOpen className="size-4" />
          ) : (
            <>
              <PanelLeftClose className="size-4" />
              <span>Collapse</span>
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
