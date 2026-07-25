import { motion } from "framer-motion";
import { AlertTriangle, Bot, Check, Copy, RefreshCw, User } from "lucide-react";
import { toast } from "sonner";

import { ConfidenceBadge } from "@/components/chat/confidence-badge";
import { MarkdownRenderer } from "@/components/markdown/markdown-renderer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard";
import { formatDuration, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { ChatMessage } from "@/types/chat";

function Avatar({ role }: { role: ChatMessage["role"] }) {
  const isUser = role === "user";
  return (
    <div
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-lg border",
        isUser ? "bg-secondary" : "bg-accent-soft border-transparent",
      )}
      aria-hidden
    >
      {isUser ? (
        <User className="size-4" />
      ) : (
        <Bot className="text-accent size-4" />
      )}
    </div>
  );
}

/** Three-dot thinking indicator shown while an answer is generating. */
function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-2 py-1" role="status" aria-live="polite">
      <div className="flex gap-1">
        {[0, 1, 2].map((index) => (
          <motion.span
            key={index}
            className="bg-accent size-1.5 rounded-full"
            animate={{ opacity: [0.25, 1, 0.25] }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              delay: index * 0.18,
              ease: "easeInOut",
            }}
          />
        ))}
      </div>
      <span className="text-muted-foreground text-sm">
        Reading the repository…
      </span>
    </div>
  );
}

export interface MessageBubbleProps {
  message: ChatMessage;
  onRetry?: () => void;
}

/** One conversation turn. Assistant turns carry answer quality metadata. */
export function MessageBubble({ message, onRetry }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const { copied, copy } = useCopyToClipboard();

  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className={cn("flex gap-3", isUser && "flex-row-reverse")}
      aria-label={isUser ? "Your message" : "CodeAtlas answer"}
    >
      <Avatar role={message.role} />

      <div
        className={cn(
          "min-w-0 max-w-[min(48rem,88%)] space-y-2.5",
          isUser && "flex flex-col items-end",
        )}
      >
        <div
          className={cn(
            "rounded-2xl border px-4 py-3",
            isUser
              ? "bg-secondary rounded-tr-sm"
              : message.status === "error"
                ? "border-destructive/30 bg-destructive/5 rounded-tl-sm"
                : "bg-card rounded-tl-sm shadow-soft",
          )}
        >
          {message.status === "pending" ? (
            <ThinkingIndicator />
          ) : isUser ? (
            <p className="text-sm leading-6 whitespace-pre-wrap">
              {message.content}
            </p>
          ) : message.status === "error" ? (
            <div className="space-y-2">
              <p className="flex items-start gap-2 text-sm">
                <AlertTriangle className="text-destructive mt-0.5 size-4 shrink-0" />
                <span>{message.content}</span>
              </p>
              {onRetry ? (
                <Button variant="outline" size="sm" onClick={onRetry}>
                  <RefreshCw className="size-3.5" />
                  Try again
                </Button>
              ) : null}
            </div>
          ) : (
            <MarkdownRenderer content={message.content} />
          )}
        </div>

        {message.role === "assistant" && message.status === "complete" ? (
          <div className="flex flex-wrap items-center gap-1.5">
            {typeof message.confidence === "number" ? (
              <ConfidenceBadge confidence={message.confidence} />
            ) : null}
            {typeof message.retrievedChunks === "number" ? (
              <Badge variant="muted">
                {formatNumber(message.retrievedChunks)} chunks
              </Badge>
            ) : null}
            {typeof message.contextTokens === "number" ? (
              <Badge variant="muted">
                {formatNumber(message.contextTokens)} tokens
              </Badge>
            ) : null}
            {typeof message.generationTime === "number" ? (
              <Badge variant="muted">
                {formatDuration(message.generationTime)}
              </Badge>
            ) : null}

            <div className="ml-auto flex items-center gap-0.5">
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={async () => {
                  const ok = await copy(message.content);
                  if (ok) toast.success("Answer copied to clipboard");
                  else toast.error("Could not access the clipboard");
                }}
                aria-label={copied ? "Answer copied" : "Copy answer"}
                className="text-muted-foreground size-7"
              >
                {copied ? (
                  <Check className="size-3.5" />
                ) : (
                  <Copy className="size-3.5" />
                )}
              </Button>
              {onRetry ? (
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={onRetry}
                  aria-label="Regenerate answer"
                  className="text-muted-foreground size-7"
                >
                  <RefreshCw className="size-3.5" />
                </Button>
              ) : null}
            </div>
          </div>
        ) : null}

        {message.warnings && message.warnings.length > 0 ? (
          <ul className="space-y-1">
            {message.warnings.map((warning) => (
              <li
                key={warning}
                className="text-warning flex items-start gap-1.5 text-xs"
              >
                <AlertTriangle className="mt-0.5 size-3 shrink-0" aria-hidden />
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </motion.article>
  );
}
