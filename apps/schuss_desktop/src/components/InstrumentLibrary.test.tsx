import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { InstrumentLibrary } from "./InstrumentLibrary";

const dispatchMock = vi.fn();

vi.mock("../core/bridge", () => ({
  dispatchDesktopOperation: (...args: unknown[]) => dispatchMock(...args),
}));

const entries = [
  {
    prototype_id: "cinderwheel",
    revision: "0.1",
    display_name: "Cinderwheel",
    summary: "A resonant counterpoint instrument.",
    controller_label: "Launch Control 3",
    lane: "new-design",
    availability: "build-required",
    launchable: false,
    evidence: { application_launch: "not-evaluated", listening: "not-evaluated", physical_controller: "not-evaluated" },
  },
  {
    prototype_id: "wirefall-r02",
    revision: "0.2",
    display_name: "Wirefall 0.2",
    summary: "A gated drone instrument.",
    controller_label: "Gills panel",
    lane: "new-design",
    availability: "verified-local-build",
    launchable: true,
    executable_sha256: "a".repeat(64),
    evidence: { application_launch: "not-evaluated", listening: "not-evaluated", physical_controller: "not-evaluated" },
  },
] as const;

describe("InstrumentLibrary", () => {
  beforeEach(() => dispatchMock.mockReset());

  it("loads exact entries and explains unavailable builds", async () => {
    dispatchMock.mockResolvedValueOnce({
      library_id: "instrument-lab-audition-library",
      library_revision: 1,
      claims: { canonical_schuss_records: false, production_ready: false },
      instrument_count: entries.length,
      instruments: entries,
    });
    render(<InstrumentLibrary />);
    expect(await screen.findByRole("heading", { name: "Cinderwheel" })).toBeVisible();
    expect(screen.getByText("A fresh verified native build is required.")).toBeVisible();
    expect(screen.getByRole("button", { name: "Open Cinderwheel" })).toBeDisabled();
    expect(dispatchMock).toHaveBeenCalledWith(expect.objectContaining({ operation: "instrument.library.list" }));
  });

  it("opens a selected verified instrument and inspects its session", async () => {
    const user = userEvent.setup();
    dispatchMock
      .mockResolvedValueOnce({
        library_id: "instrument-lab-audition-library",
        library_revision: 1,
        claims: { canonical_schuss_records: false, production_ready: false },
        instrument_count: entries.length,
        instruments: entries,
      })
      .mockResolvedValueOnce({
        instrument_session_id: "instrument-session-000001",
        prototype_id: "wirefall-r02",
        revision: "0.2",
        display_name: "Wirefall 0.2",
        status: "running",
        executable_sha256: "a".repeat(64),
      })
      .mockResolvedValueOnce({
        instrument_session_id: "instrument-session-000001",
        prototype_id: "wirefall-r02",
        revision: "0.2",
        display_name: "Wirefall 0.2",
        status: "exited",
        executable_sha256: "a".repeat(64),
        exit_code: 0,
      });
    render(<InstrumentLibrary />);
    await user.click(await screen.findByRole("button", { name: /Wirefall 0.2.*Ready/ }));
    await user.click(screen.getByRole("button", { name: "Open Wirefall 0.2" }));
    expect(await screen.findByText("Instrument open")).toBeVisible();
    expect(dispatchMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        operation: "instrument.session.start",
        payload: expect.objectContaining({ launch_intent: "explicit-native-juce-audition" }),
      }),
    );
    await user.click(screen.getByRole("button", { name: "Check status" }));
    await waitFor(() => expect(screen.getByText("Instrument closed")).toBeVisible());
    expect(screen.getByText(/exit 0/)).toBeVisible();
  });
});
