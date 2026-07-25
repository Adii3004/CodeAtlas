import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

import { cn } from "@/lib/utils";

/** Openers that work for essentially any codebase. */
export const SUGGESTED_QUESTIONS = [
  "What does this repository do, and how is it structured?",
  "Where does execution start, and what happens first?",
  "How is the code organized into modules and layers?",
  "What are the most important files to read first?",
  "How does error handling work across the codebase?",
  "Which parts of the code are covered by tests?",
] as const;

export interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
  disabled?: boolean;
  limit?: number;
  className?: string;
}

export function SuggestedQuestions({
  onSelect,
  disabled = false,
  limit = 4,
  className,
}: SuggestedQuestionsProps) {
  return (
    <div className={cn("grid gap-2 sm:grid-cols-2", className)}>
      {SUGGESTED_QUESTIONS.slice(0, limit).map((question, index) => (
        <motion.button
          key={question}
          type="button"
          onClick={() => onSelect(question)}
          disabled={disabled}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.3,
            delay: index * 0.05,
            ease: [0.22, 1, 0.36, 1],
          }}
          className={cn(
            "group bg-card hover-lift flex items-start justify-between gap-3 rounded-xl border p-3.5 text-left",
            "hover:border-accent/40 disabled:pointer-events-none disabled:opacity-50",
            "focus-visible:ring-ring focus-visible:outline-none focus-visible:ring-2",
          )}
        >
          <span className="text-sm leading-snug">{question}</span>
          <ArrowUpRight
            className="text-muted-foreground group-hover:text-accent mt-0.5 size-3.5 shrink-0 transition-colors"
            aria-hidden
          />
        </motion.button>
      ))}
    </div>
  );
}
