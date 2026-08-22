import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";

vi.mock("./components/DesktopApp", () => ({
  DesktopApp: () => <div>Always-on patcher shell</div>,
}));

describe("App shell", () => {
  it("hosts the desktop surface below the native titlebar", () => {
    render(<App />);
    expect(screen.getByText("Always-on patcher shell")).toBeVisible();
    expect(screen.getByText("DESKTOP")).toBeVisible();
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Objects" })).not.toBeInTheDocument();
  });
});
