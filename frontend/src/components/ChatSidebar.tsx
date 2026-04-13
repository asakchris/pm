"use client";

import { useState, type FormEvent } from "react";
import type { ChatMessage } from "@/lib/api";

const initialFormState = { message: "" };

type ChatSidebarProps = {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  isSending?: boolean;
  error?: string | null;
};

export const ChatSidebar = ({
  messages,
  onSend,
  isSending = false,
  error,
}: ChatSidebarProps) => {
  const [formState, setFormState] = useState(initialFormState);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = formState.message.trim();
    if (!trimmed || isSending) {
      return;
    }
    onSend(trimmed);
    setFormState(initialFormState);
  };

  return (
    <aside className="flex max-h-[calc(100vh-160px)] flex-col overflow-hidden rounded-[28px] border border-[var(--stroke)] bg-white/90 p-5 shadow-[var(--shadow)] backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
            AI Assistant
          </p>
          <h2 className="mt-2 font-display text-2xl font-semibold text-[var(--navy-dark)]">
            Chat
          </h2>
        </div>
        <div className="rounded-full border border-[var(--stroke)] px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-[var(--primary-blue)]">
          Live
        </div>
      </div>

      <div className="mt-5 flex flex-1 flex-col gap-3 overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-4">
        {messages.length === 0 ? (
          <p className="text-sm leading-6 text-[var(--gray-text)]">
            Ask the assistant to create, move, or update cards.
          </p>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={
                message.role === "user"
                  ? "self-end rounded-2xl bg-[var(--primary-blue)] px-4 py-3 text-sm text-white"
                  : "self-start rounded-2xl border border-[var(--stroke)] bg-white px-4 py-3 text-sm text-[var(--navy-dark)]"
              }
            >
              <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-white/70">
                {message.role === "user" ? "You" : "Assistant"}
              </p>
              <p className={message.role === "user" ? "mt-2 text-white" : "mt-2 text-[var(--navy-dark)]"}>
                {message.content}
              </p>
            </div>
          ))
        )}
      </div>

      {error ? (
        <p className="mt-4 text-xs font-semibold text-[var(--secondary-purple)]">
          {error}
        </p>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-3">
        <textarea
          value={formState.message}
          onChange={(event) =>
            setFormState((prev) => ({ ...prev, message: event.target.value }))
          }
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              event.currentTarget.form?.requestSubmit();
            }
          }}
          placeholder="Ask the assistant"
          rows={3}
          className="w-full resize-none rounded-2xl border border-[var(--stroke)] bg-white px-3 py-2 text-sm text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
          aria-label="Chat message"
        />
        <button
          type="submit"
          disabled={isSending}
          className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSending ? "Sending" : "Send"}
        </button>
      </form>
    </aside>
  );
};
