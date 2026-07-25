import { MessagesSquare, PanelRightClose, Sparkles, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { ChatInput } from "@/components/chat/chat-input";
import { MessageBubble } from "@/components/chat/message-bubble";
import { ReferencedFilesPanel } from "@/components/chat/referenced-files-panel";
import { SuggestedQuestions } from "@/components/chat/suggested-questions";
import { EmptyState } from "@/components/common/empty-state";
import { RepositorySelector } from "@/components/common/repository-selector";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAskQuestion } from "@/hooks/use-api";
import { useActiveRepository } from "@/hooks/use-active-repository";
import { usePreferences } from "@/hooks/use-preferences";
import { createMessage, type ChatMessage } from "@/types/chat";

export default function ChatPage() {
  const { preferences } = usePreferences();
  const { active, repositories } = useActiveRepository();
  const ask = useAskQuestion();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [showFiles, setShowFiles] = useState(preferences.showReferencedFiles);
  const scrollRef = useRef<HTMLDivElement>(null);

  const indexed = repositories.filter((repository) => repository.collectionName);
  const ready = Boolean(active?.collectionName);

  // Keep the newest turn in view as the conversation grows.
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages]);

  const runQuestion = useCallback(
    (question: string) => {
      if (!active?.collectionName) return;

      const userMessage = createMessage("user", question);
      const pendingMessage = createMessage("assistant", "", {
        status: "pending",
      });
      setMessages((previous) => [...previous, userMessage, pendingMessage]);

      ask.mutate(
        {
          collection_name: active.collectionName,
          repository_path: active.path,
          question,
          top_k: preferences.topK,
          max_context_tokens: preferences.maxContextTokens,
          temperature: preferences.temperature,
        },
        {
          onSuccess: (answer) => {
            setMessages((previous) =>
              previous.map((message) =>
                message.id === pendingMessage.id
                  ? {
                      ...message,
                      content: answer.answer,
                      status: "complete",
                      confidence: answer.confidence,
                      referencedFiles: answer.referenced_files,
                      retrievedChunks: answer.retrieved_chunks,
                      contextTokens: answer.context_tokens,
                      warnings: answer.warnings,
                      generationTime: answer.generation_time,
                    }
                  : message,
              ),
            );
          },
          onError: (error) => {
            setMessages((previous) =>
              previous.map((message) =>
                message.id === pendingMessage.id
                  ? { ...message, content: error.message, status: "error" }
                  : message,
              ),
            );
            toast.error("Could not answer that", {
              description: error.message,
            });
          },
        },
      );
    },
    [active, ask, preferences],
  );

  /** Re-run the question that produced a given assistant turn. */
  const retryFrom = useCallback(
    (assistantId: string) => {
      const index = messages.findIndex((message) => message.id === assistantId);
      const question = messages
        .slice(0, index)
        .reverse()
        .find((message) => message.role === "user");
      if (!question) return;
      setMessages((previous) =>
        previous.filter((_, position) => position < index - 1),
      );
      runQuestion(question.content);
    },
    [messages, runQuestion],
  );

  const referencedFiles =
    [...messages]
      .reverse()
      .find(
        (message) =>
          message.role === "assistant" && message.status === "complete",
      )?.referencedFiles ?? [];

  return (
    <div className="flex h-full">
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex h-14 shrink-0 items-center justify-between gap-3 border-b px-4 lg:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <RepositorySelector indexedOnly />
            {ready ? (
              <Badge variant="success" className="hidden sm:inline-flex">
                Ready
              </Badge>
            ) : null}
          </div>

          <div className="flex items-center gap-1">
            <p className="text-muted-foreground mr-2 hidden text-xs lg:block">
              top_k {preferences.topK} · {preferences.maxContextTokens} tokens ·
              temp {preferences.temperature}
            </p>
            {messages.length > 0 ? (
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() => setMessages([])}
                aria-label="Clear conversation"
              >
                <Trash2 className="size-4" />
              </Button>
            ) : null}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => setShowFiles((value) => !value)}
              aria-label={
                showFiles ? "Hide referenced files" : "Show referenced files"
              }
              className="hidden xl:inline-flex"
            >
              <PanelRightClose className="size-4" />
            </Button>
          </div>
        </div>

        <div ref={scrollRef} className="scrollbar-thin flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-4xl p-4 lg:p-8">
            {indexed.length === 0 ? (
              <EmptyState
                icon={MessagesSquare}
                title="Index a repository, then ask it anything."
                description="CodeAtlas answers only from code it has read, and tells you which files it used. Index a repository to begin."
                action={
                  <Button asChild>
                    <Link to="/repositories">Index a repository</Link>
                  </Button>
                }
                className="mt-8"
              />
            ) : messages.length === 0 ? (
              <div className="mt-6 space-y-8">
                <div className="space-y-2 text-center">
                  <p className="font-editorial text-3xl">Ask CodeAtlas</p>
                  <p className="text-muted-foreground mx-auto max-w-md text-sm leading-relaxed text-balance">
                    Every answer is grounded in{" "}
                    <span className="text-foreground font-medium">
                      {active?.name}
                    </span>
                    , with the files it relied on listed alongside.
                  </p>
                </div>
                <SuggestedQuestions
                  onSelect={runQuestion}
                  disabled={!ready || ask.isPending}
                />
              </div>
            ) : (
              <div
                className="space-y-7"
                role="log"
                aria-live="polite"
                aria-label="Conversation"
              >
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    onRetry={
                      message.role === "assistant" &&
                      message.status !== "pending"
                        ? () => retryFrom(message.id)
                        : undefined
                    }
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        <ChatInput
          onSubmit={runQuestion}
          disabled={!ready}
          pending={ask.isPending}
          placeholder={
            ready
              ? `Ask about ${active?.name}…`
              : "Index a repository to start asking questions"
          }
        />
      </div>

      {showFiles ? (
        <ReferencedFilesPanel
          files={referencedFiles}
          className="hidden w-72 shrink-0 xl:flex"
        />
      ) : null}
    </div>
  );
}

/** Small helper so the empty state can hint at what CodeAtlas is good at. */
export function ChatHint() {
  return (
    <p className="text-muted-foreground flex items-center gap-1.5 text-xs">
      <Sparkles className="size-3" aria-hidden />
      Answers cite the files they came from.
    </p>
  );
}
