import { Check, Copy } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard";
import { cn } from "@/lib/utils";

export interface CodeBlockProps {
  children: ReactNode;
  /** Raw source used for the copy action. */
  code: string;
  language?: string;
  className?: string;
}

/** Fenced code block with a language label and copy button. */
export function CodeBlock({
  children,
  code,
  language,
  className,
}: CodeBlockProps) {
  const { copied, copy } = useCopyToClipboard();

  return (
    <div
      className={cn(
        "group bg-muted/40 relative my-4 overflow-hidden rounded-lg border",
        className,
      )}
    >
      <div className="flex items-center justify-between border-b px-3 py-1.5">
        <span className="text-muted-foreground font-mono text-xs">
          {language ?? "code"}
        </span>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={() => void copy(code)}
          aria-label={copied ? "Copied" : "Copy code"}
          className="text-muted-foreground size-7 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
        >
          {copied ? (
            <Check className="size-3.5" />
          ) : (
            <Copy className="size-3.5" />
          )}
        </Button>
      </div>
      <pre className="scrollbar-thin overflow-x-auto p-4 text-[13px] leading-relaxed">
        {children}
      </pre>
    </div>
  );
}
