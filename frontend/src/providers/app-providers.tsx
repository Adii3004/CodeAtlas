import type { ReactNode } from "react";

import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { MotionProvider } from "@/providers/motion-provider";
import { QueryProvider } from "@/providers/query-provider";
import { ThemeProvider } from "@/providers/theme-provider";

/** Every cross-cutting provider, composed in one place. */
export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider defaultTheme="dark">
      <QueryProvider>
        <MotionProvider>
          <TooltipProvider>
            {children}
            <Toaster />
          </TooltipProvider>
        </MotionProvider>
      </QueryProvider>
    </ThemeProvider>
  );
}
