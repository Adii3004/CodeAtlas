import { memo, type ReactNode } from "react";
import Markdown, { type Components } from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

import { CodeBlock } from "@/components/markdown/code-block";
import { cn } from "@/lib/utils";

import "highlight.js/styles/github-dark.css";

/** Flatten React children back to a plain string (for copy + language). */
function toText(children: ReactNode): string {
  if (typeof children === "string") return children;
  if (Array.isArray(children)) return children.map(toText).join("");
  if (
    children &&
    typeof children === "object" &&
    "props" in children &&
    children.props !== null &&
    typeof children.props === "object" &&
    "children" in children.props
  ) {
    return toText((children.props as { children: ReactNode }).children);
  }
  return "";
}

const components: Components = {
  h1: ({ className, ...props }) => (
    <h1
      className={cn("mt-6 mb-3 text-xl font-semibold tracking-tight", className)}
      {...props}
    />
  ),
  h2: ({ className, ...props }) => (
    <h2
      className={cn("mt-6 mb-3 text-lg font-semibold tracking-tight", className)}
      {...props}
    />
  ),
  h3: ({ className, ...props }) => (
    <h3
      className={cn("mt-5 mb-2 text-base font-semibold", className)}
      {...props}
    />
  ),
  p: ({ className, ...props }) => (
    <p className={cn("my-3 leading-7 first:mt-0", className)} {...props} />
  ),
  ul: ({ className, ...props }) => (
    <ul className={cn("my-3 ml-5 list-disc space-y-1.5", className)} {...props} />
  ),
  ol: ({ className, ...props }) => (
    <ol
      className={cn("my-3 ml-5 list-decimal space-y-1.5", className)}
      {...props}
    />
  ),
  li: ({ className, ...props }) => (
    <li className={cn("leading-7", className)} {...props} />
  ),
  a: ({ className, ...props }) => (
    <a
      className={cn("font-medium underline underline-offset-4", className)}
      target="_blank"
      rel="noreferrer noopener"
      {...props}
    />
  ),
  blockquote: ({ className, ...props }) => (
    <blockquote
      className={cn(
        "border-border text-muted-foreground my-4 border-l-2 pl-4 italic",
        className,
      )}
      {...props}
    />
  ),
  hr: ({ className, ...props }) => (
    <hr className={cn("my-6", className)} {...props} />
  ),
  table: ({ className, ...props }) => (
    <div className="scrollbar-thin my-4 w-full overflow-x-auto rounded-lg border">
      <table className={cn("w-full text-sm", className)} {...props} />
    </div>
  ),
  th: ({ className, ...props }) => (
    <th
      className={cn(
        "text-muted-foreground border-b px-3 py-2 text-left text-xs font-medium",
        className,
      )}
      {...props}
    />
  ),
  td: ({ className, ...props }) => (
    <td className={cn("border-b px-3 py-2 last:border-0", className)} {...props} />
  ),
  pre: ({ children }) => <>{children}</>,
  code: ({ className, children, ...props }) => {
    const language = /language-(\w+)/.exec(className ?? "")?.[1];
    const isBlock = Boolean(language) || toText(children).includes("\n");

    if (!isBlock) {
      return (
        <code
          className={cn(
            "bg-muted rounded px-1.5 py-0.5 font-mono text-[0.85em]",
            className,
          )}
          {...props}
        >
          {children}
        </code>
      );
    }

    return (
      <CodeBlock code={toText(children).replace(/\n$/, "")} language={language}>
        <code className={cn("font-mono", className)} {...props}>
          {children}
        </code>
      </CodeBlock>
    );
  },
};

export interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/** Renders trusted markdown (GFM + syntax highlighting). */
export const MarkdownRenderer = memo(function MarkdownRenderer({
  content,
  className,
}: MarkdownRendererProps) {
  return (
    <div className={cn("text-sm", className)}>
      <Markdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeHighlight, { detect: true, ignoreMissing: true }]]}
        components={components}
      >
        {content}
      </Markdown>
    </div>
  );
});
