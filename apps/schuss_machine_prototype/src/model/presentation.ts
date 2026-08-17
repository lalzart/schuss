import palimpsestFixture from "../../../schuss_machine_viewer/fixtures/palimpsest-machine-inspect.json";
import tidePitFixture from "../../../schuss_machine_viewer/fixtures/tide-pit-machine-inspect.json";

import type {
  MachineKey,
  MachinePresentationConfig,
} from "./types";

const block = (number: number) => `presentation-block-${String(number).padStart(6, "0")}`;

const commonPanelLabels: MachinePresentationConfig["panelLabels"] = {
  "device-input-000001": { ALL: "Stage 1" },
  "device-input-000002": { ALL: "Stage 2" },
  "device-input-000003": { ALL: "Stage 3" },
  "device-input-000004": { ALL: "Stage 4" },
  "device-input-000005": { ALL: "Rate" },
  "device-input-000006": { ALL: "Memory" },
  "device-gesture-000004": { ALL: "Mutate" },
  "device-gesture-000007": { ALL: "Lock" },
  "device-gesture-000013": { ALL: "Root" },
  "device-gesture-000014": { ALL: "Scale" },
};

const configs: Record<MachineKey, MachinePresentationConfig> = {
  "tide-pit": {
    key: "tide-pit",
    rows: [[block(1), block(2), block(3), block(4)], [block(5), block(6), block(7), block(8), block(9)]],
    blockParts: {
      [block(1)]: ["four stages", "cycle phase", "memory", "bounded mutation", "root + scale", "wave destination"],
      [block(2)]: ["REED waveguide", "RND sine / triangle", "FOLD sine-fold"],
      [block(3)]: ["sympathetic string", "energy shaping", "low-pass gate"],
      [block(4)]: ["eight response modes", "stereo offsets", "material damping"],
      [block(5)]: ["16-bit record buffer", "six grains", "high-quality interpolation"],
      [block(6)]: ["dry / wet", "stereo spread", "Clouds diffusion tail"],
      [block(7)]: ["CLEAN", "FILT", "DRIVE", "soft pickup"],
      [block(8)]: ["soft clip", "left output", "right output"],
      [block(9)]: ["four stage LEDs", "four OLED lines"],
    },
    oledLines: ["TIDE PIT · PIT · C3", "WAVE 2-5-8-3 · STEP 1", "M75 S50 D50 · CLEAN", "MAJ5 · REED · EVOLVE"],
    panelLabels: {
      ...commonPanelLabels,
      "device-input-000007": { ALL: "Timbre" },
      "device-input-000008": { ALL: "Grain pos." },
      "device-input-000009": { CLEAN: "Grain size", FILT: "Cutoff", DRIVE: "Drive tone" },
      "device-input-000010": { CLEAN: "Depth / tail", FILT: "Resonance", DRIVE: "Drive amt." },
      "device-gesture-000001": { ALL: "Source" },
      "device-gesture-000011": { ALL: "Effect" },
      "device-gesture-000012": { ALL: "Freeze" },
      "device-gesture-000016": { ALL: "Destination" },
    },
  },
  palimpsest: {
    key: "palimpsest",
    rows: [[block(1), block(2), block(3), block(4), block(5)], [block(6), block(7), block(8), block(9)]],
    blockParts: {
      [block(1)]: ["four stages", "cycle phase", "memory", "bounded mutation", "root + scale", "voice recipe"],
      [block(2)]: ["direct strike", "trace 1", "trace 2", "trace 3"],
      [block(3)]: ["16 scheduled events", "fixed event storage", "delayed triggers"],
      [block(4)]: ["16 voices", "quietest-voice stealing", "three partials per voice"],
      [block(5)]: ["Braids sine table", "TRACE", "KNOCK", "SKIN", "SHARD"],
      [block(6)]: ["direct voices", "wake voices", "stereo pan", "motion gain"],
      [block(7)]: ["CLEAN", "FILT", "DRIVE", "soft pickup"],
      [block(8)]: ["rational limiter", "left output", "right output"],
      [block(9)]: ["four stage LEDs", "four OLED lines"],
    },
    oledLines: ["PALIMPSEST · TRACE · C3", "FORM 2-5-8-3 · STEP 1", "M75 S35 D55 · CLEAN", "MAJ5 · EVOLVE"],
    panelLabels: {
      ...commonPanelLabels,
      "device-input-000007": { ALL: "Material" },
      "device-input-000008": { ALL: "Trace space" },
      "device-input-000009": { CLEAN: "Modal decay", FILT: "Cutoff", DRIVE: "Drive tone" },
      "device-input-000010": { CLEAN: "Activity / mix", FILT: "Resonance", DRIVE: "Drive amt." },
      "device-gesture-000001": { ALL: "Voice" },
      "device-gesture-000011": { ALL: "Effect" },
      "device-gesture-000012": { ALL: "Clear" },
    },
  },
};

const rawFixtures: Record<MachineKey, unknown> = {
  "tide-pit": tidePitFixture,
  palimpsest: palimpsestFixture,
};

export function fixtureForMachine(key: MachineKey): unknown {
  return rawFixtures[key];
}

export function presentationForMachine(key: MachineKey): MachinePresentationConfig {
  return configs[key];
}

export const machineChoices: ReadonlyArray<{ key: MachineKey; label: string }> = [
  { key: "tide-pit", label: "Tide Pit" },
  { key: "palimpsest", label: "Palimpsest" },
];
