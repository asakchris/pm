import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ChatSidebar } from "@/components/ChatSidebar";

const baseMessages = [
  { role: "assistant", content: "Hello there." },
  { role: "user", content: "Create a card." },
] as const;

describe("ChatSidebar", () => {
  it("renders existing messages", () => {
    render(
      <ChatSidebar
        messages={[...baseMessages]}
        onSend={() => undefined}
        isSending={false}
      />
    );

    expect(screen.getByText("Hello there.")).toBeInTheDocument();
    expect(screen.getByText("Create a card.")).toBeInTheDocument();
  });

  it("submits a new message", async () => {
    const handleSend = vi.fn();
    render(
      <ChatSidebar messages={[]} onSend={handleSend} isSending={false} />
    );

    await userEvent.type(screen.getByLabelText("Chat message"), "Add a card");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(handleSend).toHaveBeenCalledWith("Add a card");
  });

  it("displays an error message when error prop is set", () => {
    render(
      <ChatSidebar
        messages={[]}
        onSend={() => undefined}
        isSending={false}
        error="Unable to reach the assistant right now."
      />
    );

    expect(
      screen.getByText("Unable to reach the assistant right now.")
    ).toBeInTheDocument();
  });

  it("disables the send button and input while sending", () => {
    render(
      <ChatSidebar messages={[]} onSend={() => undefined} isSending={true} />
    );

    expect(screen.getByRole("button", { name: /send/i })).toBeDisabled();
    expect(screen.getByLabelText("Chat message")).toBeDisabled();
  });
});
