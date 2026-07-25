import { ArrowLeft, Compass } from "lucide-react";
import { Link, useLocation } from "react-router-dom";

import { Button } from "@/components/ui/button";

export default function NotFoundPage() {
  const { pathname } = useLocation();

  return (
    <div className="flex min-h-[70vh] items-center justify-center p-6">
      <div className="max-w-md space-y-6 text-center">
        <div
          className="bg-accent-soft text-accent mx-auto flex size-12 items-center justify-center rounded-xl"
          aria-hidden
        >
          <Compass className="size-6" />
        </div>
        <div className="space-y-2">
          <p className="text-muted-foreground font-mono text-xs">404</p>
          <p className="font-editorial text-2xl">
            This path isn't on the map.
          </p>
          <p className="text-muted-foreground text-sm leading-relaxed text-balance">
            Nothing is routed to{" "}
            <code className="font-mono text-xs break-all">{pathname}</code>.
          </p>
        </div>
        <Button asChild>
          <Link to="/">
            <ArrowLeft className="size-4" />
            Back to overview
          </Link>
        </Button>
      </div>
    </div>
  );
}
