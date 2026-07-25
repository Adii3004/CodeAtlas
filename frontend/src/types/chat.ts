/** Client-side conversation model (chat history is not persisted server-side). */

export type ChatRole = "user" | "assistant";
export type ChatMessageStatus = "pending" | "complete" | "error";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  status: ChatMessageStatus;
  /** Assistant-only answer metadata, mirrored from AskResponse. */
  confidence?: number;
  referencedFiles?: string[];
  retrievedChunks?: number;
  contextTokens?: number;
  warnings?: string[];
  generationTime?: number;
}

export function createMessage(
  role: ChatRole,
  content: string,
  overrides: Partial<ChatMessage> = {},
): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    createdAt: new Date().toISOString(),
    status: "complete",
    ...overrides,
  };
}
