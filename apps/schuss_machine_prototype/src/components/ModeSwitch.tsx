import type { PerformanceMode } from "../model/types";

const modes: PerformanceMode[] = ["CLEAN", "FILT", "DRIVE"];

interface ModeSwitchProps {
  mode: PerformanceMode;
  onChange: (mode: PerformanceMode) => void;
}

export function ModeSwitch({ mode, onChange }: ModeSwitchProps) {
  return (
    <div className="mode-switch" aria-label="Performance effect mode" role="group">
      {modes.map((candidate) => (
        <button
          aria-pressed={candidate === mode}
          className={candidate === mode ? "is-active" : undefined}
          key={candidate}
          onClick={() => onChange(candidate)}
          type="button"
        >
          {candidate}
        </button>
      ))}
    </div>
  );
}
