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

const pamplistEntry = {
  prototype_id: "pamplist",
  revision: "0.6",
  display_name: "Pamplist",
  summary: "Seven independent generative percussion voices.",
  controller_label: "Launch Control 3",
  lane: "source-derived",
  canonical_identity: {
    status: "canonical",
    instrument_reference: { instrument_id: "schuss-instrument-000007", revision: 1, content_hash: `sha256:${"a".repeat(64)}` },
    graph_reference: { graph_id: "schuss-graph-000009", revision: 1, content_hash: `sha256:${"b".repeat(64)}` },
    record_set_reference: { record_set_id: "schuss-record-set-000036", revision: 1, content_hash: `sha256:${"c".repeat(64)}` },
  },
  availability: "verified-local-build",
  launchable: true,
  executable_sha256: "d".repeat(64),
  evidence: { application_launch: "not-evaluated", listening: "not-evaluated", physical_controller: "not-evaluated" },
} as const;

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

  it("distinguishes canonical musical identity from its audition runtime", async () => {
    dispatchMock.mockResolvedValueOnce({
      library_id: "instrument-lab-audition-library",
      library_revision: 2,
      claims: { canonical_identity_count: 1, production_ready: false, runtime_authority: "prototype-build-only" },
      instrument_count: 1,
      instruments: [pamplistEntry],
    });
    render(<InstrumentLibrary />);
    expect(await screen.findByRole("heading", { name: "Pamplist" })).toBeVisible();
    expect(screen.getByText("SCHUSS INSTRUMENTS")).toBeVisible();
    expect(screen.getByText("Canonical")).toBeVisible();
    expect(screen.getByText(/This musical identity is canonical/)).toBeVisible();
  });
});
