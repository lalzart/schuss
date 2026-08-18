import { describe, expect, it } from "vitest";
import {
  DEFAULT_PREFERENCES,
  DESKTOP_PREFERENCES_KEY,
  loadDesktopPreferences,
} from "./desktopPreferences";

function storage(values: Record<string, string>): Pick<Storage, "getItem"> {
  return { getItem: (key) => values[key] ?? null };
}

describe("desktop preferences", () => {
  it("loads only the versioned presentation fields and bounds drawer width", () => {
    expect(loadDesktopPreferences(storage({
      [DESKTOP_PREFERENCES_KEY]: JSON.stringify({
        version: 2,
        projectsRoot: "/tmp/projects",
        lastWorkspace: "/tmp/projects/patch",
        drawer: { open: false, tab: "patches", width: 999 },
      }),
    }))).toEqual({
      version: 2,
      projectsRoot: "/tmp/projects",
      lastWorkspace: "/tmp/projects/patch",
      drawer: { open: false, tab: "patches", width: 460 },
    });
  });

  it("migrates only the last legacy workspace and never infers a projects root", () => {
    expect(loadDesktopPreferences(storage({
      "schuss.desktop.recent-projects.v1": JSON.stringify(["/tmp/projects/patch"]),
    }))).toEqual({
      ...DEFAULT_PREFERENCES,
      lastWorkspace: "/tmp/projects/patch",
      projectsRoot: "",
    });
  });

  it("falls back safely when stored JSON is malformed", () => {
    expect(loadDesktopPreferences(storage({ [DESKTOP_PREFERENCES_KEY]: "{" }))).toEqual(DEFAULT_PREFERENCES);
  });
});
