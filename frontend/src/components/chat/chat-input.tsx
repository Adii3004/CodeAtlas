import { CornerDownLeft, Send, Square } from "lucide-react";
import { useRef, useState, type FormEvent, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export interface ChatInputProps {
  onSubmit: (question: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  pending?: boolean;
  placeholder?: string;
  className?: string;
}

/** Auto-growing composer. Enter sends, Shift+Enter inserts a newline. */
export function ChatInput({
  onSubmit,
  onStop,
  disabled = false,
  pending = false,
  placeholder = "Ask about this repository…",
  className,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const question = value.trim();
    if (!question || disabled || pending) return;
    onSubmit(question);
    setValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    submit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={cn("bg-background border-t p-3 lg:p-4", className)}
    >
      <div className="focus-within:ring-ring bg-card relative rounded-xl border transition-shadow focus-within:ring-2">
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={(event) => {
            setValue(event.target.value);
            const element = event.target;
            element.style.height = "auto";
            element.style.height = `${Math.min(element.scrollHeight, 200)}px`;
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          aria-label="Question"
          className="max-h-50 min-h-11 resize-none border-0 bg-transparent py-3 pr-24 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
        />
        <div className="absolute right-2 bottom-2 flex items-center gap-1.5">
          {pending && onStop ? (
            <Button type="button" size="sm" variant="outline" onClick={onStop}>
              <Square className="size-3.5" />
              Stop
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon-sm"
              disabled={disabled || pending || value.trim().length === 0}
              aria-label="Send question"
            >
              <Send className="size-4" />
            </Button>
          )}
        </div>
      </div>
      <p className="text-muted-foreground mt-2 flex items-center gap-1 text-xs">
        <CornerDownLeft className="size-3" aria-hidden />
        Enter to send · Shift + Enter for a new line
      </p>
    </form>
  );
}
