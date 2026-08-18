export const DESKTOP_PREFERENCES_KEY = "schuss.desktop.preferences.v2";
const LEGACY_RECENTS_KEY = "schuss.desktop.recent-projects.v1";

export type DrawerTab = "objects" | "patches";

export type DesktopPreferences = {
  version: 2;
  projectsRoot: string;
  lastWorkspace: string;
  drawer: {
    open: boolean;
    tab: DrawerTab;
    width: number;
  };
};

export const DEFAULT_PREFERENCES: DesktopPreferences = {
  version: 2,
  projectsRoot: "",
  lastWorkspace: "",
  drawer: { open: true, tab: "objects", width: 340 },
};

function boundedWidth(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value)
    ? Math.min(460, Math.max(280, Math.round(value)))
    : DEFAULT_PREFERENCES.drawer.width;
}

export function loadDesktopPreferences(storage: Pick<Storage, "getItem"> = localStorage): DesktopPreferences {
  try {
    const value = JSON.parse(storage.getItem(DESKTOP_PREFERENCES_KEY) ?? "null") as Partial<DesktopPreferences> | null;
    if (value?.version === 2) {
      return {
        version: 2,
        projectsRoot: typeof value.projectsRoot === "string" ? value.projectsRoot : "",
        lastWorkspace: typeof value.lastWorkspace === "string" ? value.lastWorkspace : "",
        drawer: {
          open: typeof value.drawer?.open === "boolean" ? value.drawer.open : true,
          tab: value.drawer?.tab === "patches" ? "patches" : "objects",
          width: boundedWidth(value.drawer?.width),
        },
      };
    }
  } catch {
    // A malformed local preference must not become project state.
  }
  try {
    const legacy = JSON.parse(storage.getItem(LEGACY_RECENTS_KEY) ?? "[]") as unknown;
    const lastWorkspace = Array.isArray(legacy)
      ? legacy.find((item): item is string => typeof item === "string" && item.startsWith("/")) ?? ""
      : "";
    return { ...DEFAULT_PREFERENCES, lastWorkspace };
  } catch {
    return DEFAULT_PREFERENCES;
  }
}

export function saveDesktopPreferences(
  preferences: DesktopPreferences,
  storage: Pick<Storage, "setItem"> = localStorage,
): void {
  storage.setItem(DESKTOP_PREFERENCES_KEY, JSON.stringify(preferences));
}
