import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";

vi.mock("./components/DesktopApp", () => ({
  DesktopApp: ({ route, navigate, onEditorDirtyChange }: {
    route: { view: string };
    navigate: (route: { view: "patches" } | { view: "editor"; workspace: string }) => void;
    onEditorDirtyChange: (dirty: boolean) => void;
  }) => (
    <div>
      <span data-testid="route">{route.view}</span>
      <button type="button" onClick={() => navigate({ view: "editor", workspace: "/tmp/test" })}>Open editor</button>
      <button type="button" onClick={() => onEditorDirtyChange(true)}>Make dirty</button>
    </div>
  ),
}));

describe("App unsaved navigation guard", () => {
  it("keeps the editor open when the user declines to discard the draft", async () => {
    const user = userEvent.setup();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<App />);

    await user.click(screen.getByRole("button", { name: "Open editor" }));
    await user.click(screen.getByRole("button", { name: "Make dirty" }));
    await user.click(screen.getByRole("button", { name: "Patches" }));

    expect(confirm).toHaveBeenCalledWith("Close this patch and discard its unsaved edits?");
    expect(screen.getByTestId("route")).toHaveTextContent("editor");
  });
});
