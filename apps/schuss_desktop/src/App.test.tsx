import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";

vi.mock("./components/DesktopApp", () => ({
  DesktopApp: () => <div>Always-on patcher shell</div>,
}));

describe("App shell", () => {
  it("opens directly into one patcher application without page navigation", () => {
    render(<App />);
    expect(screen.getByText("Always-on patcher shell")).toBeVisible();
    expect(screen.getByText("PATCHER")).toBeVisible();
    expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Objects" })).not.toBeInTheDocument();
  });
});
