import type {
  ControlMapping,
  MachineDefinition,
  MachineKey,
  PerformanceMode,
} from "./types";
import { PERFORMANCE_MODES } from "./types";

const allModes = (label: string): Record<PerformanceMode, string> => ({
  clean: label,
  drive: label,
  filter: label,
});

const control = (
  controlId: string,
  physicalLabel: string,
  label: string | Record<PerformanceMode, string>,
  targetId: string,
  detail?: string,
): ControlMapping => ({
  controlId,
  detail,
  kind: controlId.startsWith("pot-") || controlId === "encoder-turn" ? "control" : "event",
  labels: typeof label === "string" ? allModes(label) : label,
  mapped: true,
  physicalLabel,
  targetId,
});

const sharedOutputs = [
  {
    detail: "Stereo audio service",
    kind: "audio" as const,
    label: "Stereo L / R",
    outputId: "stereo-out",
    targetId: "gills-stereo",
  },
  ...([1, 2, 3, 4] as const).map((stage) => ({
    detail: `Gesture stage ${stage} activity`,
    kind: "feedback" as const,
    label: `LED${stage} · Stage ${stage}`,
    outputId: `stage-led-${stage}`,
    targetId: `gills-led-${stage}`,
  })),
  {
    detail: "Instrument status and parameter text",
    kind: "feedback" as const,
    label: "OLED status",
    outputId: "oled-status",
    targetId: "gills-oled",
  },
] as const;

const tidePitControls: readonly ControlMapping[] = [
  control("pot-1", "P1", "Stage 1", "stage-1"),
  control("pot-2", "P2", "Stage 2", "stage-2"),
  control("pot-3", "P3", "Stage 3", "stage-3"),
  control("pot-4", "P4", "Stage 4", "stage-4"),
  control("pot-5", "P5", "Rate", "rate"),
  control("pot-6", "P6", "Memory", "memory"),
  control("pot-7", "P7", "Material", "material", "Oscillator timbre"),
  control("pot-8", "P8", "Grain Position", "grain-position"),
  control(
    "pot-9",
    "P9",
    { clean: "Grain Size", drive: "Tone", filter: "Cutoff" },
    "mode-parameter-1",
  ),
  control(
    "pot-10",
    "P10",
    { clean: "Depth / Tail", drive: "Amount", filter: "Resonance" },
    "mode-parameter-2",
  ),
  control("button-1", "B1", "Source", "source-select", "REED · RND · FOLD"),
  control("button-2", "B2", "Mutate", "mutate"),
  control("button-3", "B3", "Lock", "lock"),
  control("button-4", "B4", "Effect / Freeze", "effect-freeze", "Tap effect · hold capture"),
  control("encoder-turn", "ENC ↻", "Root", "root"),
  control("encoder-push", "ENC PUSH", "Scale", "scale"),
  control("encoder-hold", "ENC HOLD", "Destination", "destination", "Pitch · body · grain · all"),
];

const palimpsestControls: readonly ControlMapping[] = [
  control("pot-1", "P1", "Stage 1 pitch", "stage-1"),
  control("pot-2", "P2", "Stage 2 pitch", "stage-2"),
  control("pot-3", "P3", "Stage 3 pitch", "stage-3"),
  control("pot-4", "P4", "Stage 4 pitch", "stage-4"),
  control("pot-5", "P5", "Rate", "rate"),
  control("pot-6", "P6", "Memory", "memory"),
  control("pot-7", "P7", "Material", "material"),
  control("pot-8", "P8", "Trace Spacing", "trace-spacing"),
  control(
    "pot-9",
    "P9",
    { clean: "Modal Decay", drive: "Tone", filter: "Cutoff" },
    "mode-parameter-1",
  ),
  control(
    "pot-10",
    "P10",
    { clean: "Activity / Mix", drive: "Amount", filter: "Resonance" },
    "mode-parameter-2",
  ),
  control("button-1", "B1", "Voice", "voice-select", "TRACE · KNOCK · SKIN · SHARD"),
  control("button-2", "B2", "Mutate", "mutate"),
  control("button-3", "B3", "Lock", "lock"),
  control("button-4", "B4", "Effect / Clear", "effect-clear", "Tap effect · hold clear"),
  control("encoder-turn", "ENC ↻", "Root", "root"),
  control("encoder-push", "ENC PUSH", "Scale", "scale"),
  {
    controlId: "encoder-hold",
    detail: "Intentionally unused in the inspected source",
    kind: "event",
    labels: allModes("Unmapped"),
    mapped: false,
    physicalLabel: "ENC HOLD",
    targetId: "encoder-hold-unmapped",
  },
];

export const MACHINES: Record<MachineKey, MachineDefinition> = {
  "tide-pit": {
    controls: tidePitControls,
    displayName: "Tide Pit",
    key: "tide-pit",
    outputs: sharedOutputs,
    performanceModes: PERFORMANCE_MODES,
    sourceObject: "projects/tide-pit-gills/tidepit.axo",
    sourcePatch: "projects/tide-pit-gills/tidepit-gills.axp",
    sourceRevision: "local inspected Gills source",
    subtitle: "Gesture-driven physical model and granular memory",
    summary: "A four-stage gesture instrument whose exciter, body, captured memory, grains, and effects remain one source-defined compound.",
    sourceOutline: [
      { detail: "Four stored stages with mutation and lock behavior", label: "Gesture sequencer" },
      { detail: "REED, random, and folded excitation paths", label: "Voice exciter" },
      { detail: "Main oscillator and sympathetic-string response", label: "Physical body" },
      { detail: "16-bit recording memory feeding six grains", label: "Capture + grain cloud" },
      { detail: "CLEAN, FILT, and DRIVE routes with final soft clip", label: "Effect lane" },
    ],
  },
  palimpsest: {
    controls: palimpsestControls,
    displayName: "Palimpsest",
    key: "palimpsest",
    outputs: sharedOutputs,
    performanceModes: PERFORMANCE_MODES,
    sourceObject: "projects/palimpsest-gills/palimpsest.axo",
    sourcePatch: "projects/palimpsest-gills/palimpsest-gills.axp",
    sourceRevision: "local inspected Gills source",
    subtitle: "Layered gestures across a sixteen-voice modal field",
    summary: "A four-stage mutation instrument that schedules trace and strike events through a fixed voice pool, modal synthesis, wake mix, and effects.",
    sourceOutline: [
      { detail: "Four pitch stages with memory, mutation, and lock", label: "Gesture sequencer" },
      { detail: "Trace spacing and strike-event generation", label: "Trace / strike events" },
      { detail: "Fixed sixteen-event scheduler and voice allocation", label: "Event scheduler" },
      { detail: "Sixteen modal voices using retained Braids sine modes", label: "Modal voice pool" },
      { detail: "Direct/wake blend, CLEAN/FILT/DRIVE, rational limiter", label: "Mix + effect lane" },
    ],
  },
};

export const MACHINE_KEYS = Object.keys(MACHINES) as MachineKey[];
