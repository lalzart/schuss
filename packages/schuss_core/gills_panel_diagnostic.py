"""Deterministic Task 022 Gills panel diagnostic host model and C++ seam."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Sequence

from .gills_panel_runtime import ADC_MAX, DEBOUNCE_UPDATES, HOLD_UPDATES, POT_ADC_INDICES


POT_MOVE_THRESHOLD_RAW = 4
POT_LOW_MAX = 512
POT_MIDDLE_MIN = 1536
POT_MIDDLE_MAX = 2559
POT_HIGH_MIN = 3583
STARTUP_UPDATES = 6000
LED_STEP_UPDATES = 1500
LED_CHANNELS = 6


def pot_zone(raw: int) -> str:
    if not 0 <= raw <= ADC_MAX:
        raise ValueError("GILLS_DIAGNOSTIC_ADC_RANGE_INVALID")
    if raw <= POT_LOW_MAX:
        return "low"
    if POT_MIDDLE_MIN <= raw <= POT_MIDDLE_MAX:
        return "middle"
    if POT_HIGH_MIN <= raw:
        return "high"
    return "transition"


@dataclass
class DiagnosticButtonState:
    candidate: bool = False
    stable: bool = False
    candidate_updates: int = 0
    held_updates: int = 0
    hold_sent: bool = False
    event_mask: int = 0


@dataclass
class DiagnosticPotState:
    last_raw: int = 0
    sample_valid: bool = False
    zone_mask: int = 0
    monotonic_stage: int = 0
    discontinuity: bool = False


@dataclass
class DiagnosticState:
    pots: list[DiagnosticPotState] = field(
        default_factory=lambda: [DiagnosticPotState() for _ in range(10)]
    )
    buttons: list[DiagnosticButtonState] = field(
        default_factory=lambda: [DiagnosticButtonState() for _ in range(5)]
    )
    encoder_a_last: bool = True
    encoder_scan_counter: int = 0
    encoder_positive: int = 0
    encoder_negative: int = 0
    control_updates: int = 0
    led_scan_mask: int = 0
    active_led_channel: int = 0
    last_event: str = "READY"


def _button_update(
    state: DiagnosticButtonState, raw: bool, label: str
) -> tuple[DiagnosticButtonState, list[str]]:
    value = copy.deepcopy(state)
    events: list[str] = []
    if raw == value.candidate:
        value.candidate_updates = min(DEBOUNCE_UPDATES, value.candidate_updates + 1)
    else:
        value.candidate = raw
        value.candidate_updates = 1
    if value.candidate_updates == DEBOUNCE_UPDATES and value.stable != value.candidate:
        value.stable = value.candidate
        value.held_updates = 0
        value.hold_sent = False
        if value.stable:
            value.event_mask |= 1
            events.append(label + "-press")
        else:
            value.event_mask |= 2
            events.append(label + "-release")
    if value.stable:
        value.held_updates += 1
        if value.held_updates >= HOLD_UPDATES and not value.hold_sent:
            value.hold_sent = True
            value.event_mask |= 4
            events.append(label + "-hold")
    return value, events


def _pot_update(state: DiagnosticPotState, raw: int) -> DiagnosticPotState:
    value = copy.deepcopy(state)
    zone = pot_zone(raw)
    zone_bits = {"low": 1, "middle": 2, "high": 4}
    if zone in zone_bits:
        value.zone_mask |= zone_bits[zone]
    if zone == "low" and value.monotonic_stage == 0:
        value.monotonic_stage = 1
    elif zone == "middle" and value.monotonic_stage == 1:
        value.monotonic_stage = 2
    elif zone == "high" and value.monotonic_stage == 2:
        value.monotonic_stage = 3
    if value.sample_valid and (
        (value.last_raw <= POT_LOW_MAX and raw >= POT_HIGH_MIN)
        or (value.last_raw >= POT_HIGH_MIN and raw <= POT_LOW_MAX)
    ):
        value.discontinuity = True
    value.last_raw = raw
    value.sample_valid = True
    return value


def _display_lines(value: DiagnosticState) -> list[str]:
    if value.control_updates <= STARTUP_UPDATES:
        return ["SCHUSS", "PANEL TEST", "TASK022", "READY"]
    pots = sum(item.monotonic_stage == 3 for item in value.pots)
    buttons = sum(item.event_mask == 7 for item in value.buttons[:4])
    encoder_ok = value.encoder_positive >= 3 and value.encoder_negative <= -3
    push_ok = value.buttons[4].event_mask == 7
    software_complete = (
        pots == 10
        and buttons == 4
        and encoder_ok
        and push_ok
        and value.led_scan_mask == 0x3F
    )
    if software_complete:
        return [
            f"POTS {pots:02d}/10",
            f"BTNS {buttons:02d}/04",
            "ENC OK PUSH",
            "LED 6 OLED?",
        ]
    encoder_mark = "E" if encoder_ok else "-"
    push_mark = "P" if push_ok else "-"
    return [
        "TASK022",
        value.last_event[:11],
        f"LED{value.active_led_channel} ACTIVE" if value.active_led_channel else "LED START",
        f"P{pots:02d} B{buttons:02d} {encoder_mark}{push_mark}",
    ]


def evaluate_diagnostic_update(
    state: DiagnosticState,
    raw_pots: Sequence[int],
    raw_buttons: Sequence[bool],
    encoder_a: bool,
    encoder_b: bool,
    encoder_push: bool,
) -> tuple[DiagnosticState, dict[str, Any]]:
    if len(raw_pots) != 10 or len(raw_buttons) != 4:
        raise ValueError("GILLS_DIAGNOSTIC_VECTOR_SHAPE_INVALID")
    if any(not 0 <= item <= ADC_MAX for item in raw_pots):
        raise ValueError("GILLS_DIAGNOSTIC_ADC_RANGE_INVALID")
    value = copy.deepcopy(state)
    value.control_updates += 1
    events: list[str] = []

    deltas = [abs(raw - item.last_raw) for raw, item in zip(raw_pots, value.pots)]
    moved = max(range(10), key=lambda index: (deltas[index], -index))
    for index, raw in enumerate(raw_pots):
        value.pots[index] = _pot_update(value.pots[index], raw)
    if deltas[moved] >= POT_MOVE_THRESHOLD_RAW:
        zone = pot_zone(raw_pots[moved])
        zone_label = {"low": "L", "middle": "M", "high": "H"}.get(zone, "-")
        value.last_event = f"P{moved + 1:02d} {raw_pots[moved]:04d} {zone_label}"
        events.append(f"pot-{moved + 1}-{raw_pots[moved]}-{zone}")

    for index, raw in enumerate((*raw_buttons, encoder_push)):
        label = "encoder-push" if index == 4 else f"button-{index + 1}"
        value.buttons[index], new_events = _button_update(
            value.buttons[index], bool(raw), label
        )
        events.extend(new_events)
        for event in new_events:
            suffix = event.rsplit("-", 1)[-1].upper()
            value.last_event = (
                f"EP {suffix}" if index == 4 else f"B{index + 1} {suffix}"
            )

    encoder_delta = 0
    if value.encoder_scan_counter == 0:
        if not encoder_a and value.encoder_a_last:
            encoder_delta = -1 if encoder_b else 1
            if encoder_delta > 0:
                value.encoder_positive += 1
            else:
                value.encoder_negative -= 1
            events.append(
                "encoder-turn-positive" if encoder_delta > 0 else "encoder-turn-negative"
            )
            count = value.encoder_positive if encoder_delta > 0 else value.encoder_negative
            value.last_event = f"ENC {count:+04d}"
        value.encoder_a_last = bool(encoder_a)
    value.encoder_scan_counter = (value.encoder_scan_counter + 1) % 4

    if value.control_updates > STARTUP_UPDATES:
        phase = ((value.control_updates - STARTUP_UPDATES - 1) // LED_STEP_UPDATES) % LED_CHANNELS
        value.active_led_channel = phase + 1
        value.led_scan_mask |= 1 << phase

    return value, {
        "events": events,
        "pot_states": [
            {
                "slot": index + 1,
                "raw": item.last_raw,
                "sample_valid": item.sample_valid,
                "zone_mask": item.zone_mask,
                "monotonic_stage": item.monotonic_stage,
                "discontinuity": item.discontinuity,
            }
            for index, item in enumerate(value.pots)
        ],
        "button_event_masks": [item.event_mask for item in value.buttons],
        "encoder_delta": encoder_delta,
        "encoder_positive": value.encoder_positive,
        "encoder_negative": value.encoder_negative,
        "active_led_channel": value.active_led_channel,
        "led_scan_mask": value.led_scan_mask,
        "display_lines": _display_lines(value),
    }


def diagnostic_host_vectors() -> dict[str, Any]:
    pot_vectors = [
        {
            "slot": index + 1,
            "adc_index": POT_ADC_INDICES[index],
            "samples": [
                {"raw": raw, "zone": pot_zone(raw)}
                for raw in (0, POT_LOW_MAX, POT_MIDDLE_MIN, 2048, POT_MIDDLE_MAX, POT_HIGH_MIN, ADC_MAX)
            ],
        }
        for index in range(10)
    ]
    gesture_vectors = []
    for index in range(5):
        state = DiagnosticState()
        observed: list[str] = []
        for raw, count in (
            (True, DEBOUNCE_UPDATES),
            (True, HOLD_UPDATES),
            (False, DEBOUNCE_UPDATES),
        ):
            for _ in range(count):
                buttons = [False] * 4
                push = False
                if index == 4:
                    push = raw
                else:
                    buttons[index] = raw
                state, output = evaluate_diagnostic_update(
                    state, [0] * 10, buttons, True, True, push
                )
                observed.extend(output["events"])
        gesture_vectors.append(
            {
                "control": "encoder-push" if index == 4 else f"button-{index + 1}",
                "events": observed,
                "event_mask": state.buttons[index].event_mask,
            }
        )
    return {
        "schema_version": "task022-panel-host-vectors-v1",
        "policies": {
            "adc_max": ADC_MAX,
            "pot_move_threshold_raw": POT_MOVE_THRESHOLD_RAW,
            "zones": {
                "low": [0, POT_LOW_MAX],
                "middle": [POT_MIDDLE_MIN, POT_MIDDLE_MAX],
                "high": [POT_HIGH_MIN, ADC_MAX],
            },
            "debounce_updates": DEBOUNCE_UPDATES,
            "hold_updates": HOLD_UPDATES,
            "encoder_scan_divisor": 4,
            "startup_updates": STARTUP_UPDATES,
            "led_step_updates": LED_STEP_UPDATES,
        },
        "pot_vectors": pot_vectors,
        "gesture_vectors": gesture_vectors,
        "startup_lines": ["SCHUSS", "PANEL TEST", "TASK022", "READY"],
        "completion_lines": ["POTS 10/10", "BTNS 04/04", "ENC OK PUSH", "LED 6 OLED?"],
    }


_DIAGNOSTIC_CPP = r'''

struct SchussDiagnosticButton {
  bool candidate;
  bool stable;
  bool hold_sent;
  uint16_t candidate_updates;
  uint16_t held_updates;
  uint8_t event_mask;
};

struct SchussDiagnosticPot {
  uint16_t last_raw;
  bool sample_valid;
  uint8_t zone_mask;
  uint8_t monotonic_stage;
  bool discontinuity;
};

struct SchussDiagnosticRuntime {
  SchussDiagnosticPot pots[10];
  SchussDiagnosticButton buttons[5];
  bool encoder_a_last;
  uint8_t encoder_scan_counter;
  int16_t encoder_positive;
  int16_t encoder_negative;
  uint32_t control_updates;
  uint8_t led_scan_mask;
  uint8_t active_led_channel;
  char display_text[44];
  Thread* oled_thread;
};

static SchussDiagnosticRuntime Diagnostic;
static WORKING_AREA(SchussDiagnosticOledWorkingArea, 192);
static uint8_t SchussDiagnosticOledTx[129] __attribute__((section(".sram2")));
static uint8_t SchussDiagnosticOledCommand[2] __attribute__((section(".sram2")));
static uint8_t SchussDiagnosticOledRx[1] __attribute__((section(".sram2")));

static uint8_t schuss_diagnostic_button_update(SchussDiagnosticButton* state, bool raw) {
  uint8_t events = 0;
  if (raw == state->candidate) {
    if (state->candidate_updates < 4) ++state->candidate_updates;
  } else {
    state->candidate = raw;
    state->candidate_updates = 1;
  }
  if (state->candidate_updates == 4 && state->stable != state->candidate) {
    state->stable = state->candidate;
    state->held_updates = 0;
    state->hold_sent = false;
    events = state->stable ? 1 : 2;
    state->event_mask |= events;
  }
  if (state->stable) {
    if (state->held_updates < 1500) ++state->held_updates;
    if (state->held_updates >= 1500 && !state->hold_sent) {
      state->hold_sent = true;
      events |= 4;
      state->event_mask |= 4;
    }
  }
  return events;
}

static uint8_t schuss_diagnostic_zone(uint16_t raw) {
  if (raw <= 512) return 1;
  if (raw >= 1536 && raw <= 2559) return 2;
  if (raw >= 3583) return 3;
  return 0;
}

static uint8_t schuss_diagnostic_glyph(char value, uint8_t column) {
  static const uint8_t digits[10][5] = {
    {0x3E,0x51,0x49,0x45,0x3E},{0x00,0x42,0x7F,0x40,0x00},{0x42,0x61,0x51,0x49,0x46},{0x21,0x41,0x45,0x4B,0x31},{0x18,0x14,0x12,0x7F,0x10},
    {0x27,0x45,0x45,0x45,0x39},{0x3C,0x4A,0x49,0x49,0x30},{0x01,0x71,0x09,0x05,0x03},{0x36,0x49,0x49,0x49,0x36},{0x06,0x49,0x49,0x29,0x1E}
  };
  if (column >= 5) return 0;
  if (value >= '0' && value <= '9') return digits[value - '0'][column];
  switch (value) {
    case 'A': { static const uint8_t v[5]={0x7E,0x11,0x11,0x11,0x7E}; return v[column]; }
    case 'B': { static const uint8_t v[5]={0x7F,0x49,0x49,0x49,0x36}; return v[column]; }
    case 'C': { static const uint8_t v[5]={0x3E,0x41,0x41,0x41,0x22}; return v[column]; }
    case 'D': { static const uint8_t v[5]={0x7F,0x41,0x41,0x22,0x1C}; return v[column]; }
    case 'E': { static const uint8_t v[5]={0x7F,0x49,0x49,0x49,0x41}; return v[column]; }
    case 'F': { static const uint8_t v[5]={0x7F,0x09,0x09,0x09,0x01}; return v[column]; }
    case 'G': { static const uint8_t v[5]={0x3E,0x41,0x49,0x49,0x7A}; return v[column]; }
    case 'H': { static const uint8_t v[5]={0x7F,0x08,0x08,0x08,0x7F}; return v[column]; }
    case 'I': { static const uint8_t v[5]={0x00,0x41,0x7F,0x41,0x00}; return v[column]; }
    case 'K': { static const uint8_t v[5]={0x7F,0x08,0x14,0x22,0x41}; return v[column]; }
    case 'L': { static const uint8_t v[5]={0x7F,0x40,0x40,0x40,0x40}; return v[column]; }
    case 'M': { static const uint8_t v[5]={0x7F,0x02,0x0C,0x02,0x7F}; return v[column]; }
    case 'N': { static const uint8_t v[5]={0x7F,0x04,0x08,0x10,0x7F}; return v[column]; }
    case 'O': { static const uint8_t v[5]={0x3E,0x41,0x41,0x41,0x3E}; return v[column]; }
    case 'P': { static const uint8_t v[5]={0x7F,0x09,0x09,0x09,0x06}; return v[column]; }
    case 'R': { static const uint8_t v[5]={0x7F,0x09,0x19,0x29,0x46}; return v[column]; }
    case 'S': { static const uint8_t v[5]={0x46,0x49,0x49,0x49,0x31}; return v[column]; }
    case 'T': { static const uint8_t v[5]={0x01,0x01,0x7F,0x01,0x01}; return v[column]; }
    case 'U': { static const uint8_t v[5]={0x3F,0x40,0x40,0x40,0x3F}; return v[column]; }
    case 'V': { static const uint8_t v[5]={0x1F,0x20,0x40,0x20,0x1F}; return v[column]; }
    case 'Y': { static const uint8_t v[5]={0x07,0x08,0x70,0x08,0x07}; return v[column]; }
    case '+': { static const uint8_t v[5]={0x08,0x08,0x3E,0x08,0x08}; return v[column]; }
    case '-': { static const uint8_t v[5]={0x08,0x08,0x08,0x08,0x08}; return v[column]; }
    case '/': { static const uint8_t v[5]={0x20,0x10,0x08,0x04,0x02}; return v[column]; }
    case '?': { static const uint8_t v[5]={0x02,0x01,0x51,0x09,0x06}; return v[column]; }
    default: return 0;
  }
}

static void schuss_diagnostic_oled_command(uint8_t value) {
  SchussDiagnosticOledCommand[0] = 0;
  SchussDiagnosticOledCommand[1] = value;
  i2cMasterTransmitTimeout(&I2CD1, 0x3C, SchussDiagnosticOledCommand, 2, SchussDiagnosticOledRx, 0, 30);
}

static void schuss_diagnostic_oled_page(uint8_t page) {
  static const uint8_t expand[16] = {0x00,0x03,0x0C,0x0F,0x30,0x33,0x3C,0x3F,0xC0,0xC3,0xCC,0xCF,0xF0,0xF3,0xFC,0xFF};
  SchussDiagnosticOledTx[0] = 0x40;
  uint32_t offset = 1;
  const uint8_t line = page >> 1;
  for (uint8_t character = 0; character < 11; ++character) {
    for (uint8_t column = 0; column < 5; ++column) {
      const uint8_t glyph = schuss_diagnostic_glyph(Diagnostic.display_text[line * 11 + character], column);
      const uint8_t pixels = expand[(page & 1) ? ((glyph >> 4) & 15) : (glyph & 15)];
      SchussDiagnosticOledTx[offset++] = pixels;
      SchussDiagnosticOledTx[offset++] = pixels;
    }
    SchussDiagnosticOledTx[offset++] = 0;
  }
  while (offset < 129) SchussDiagnosticOledTx[offset++] = 0;
  i2cAcquireBus(&I2CD1);
  schuss_diagnostic_oled_command(0x21);
  schuss_diagnostic_oled_command(0x00);
  schuss_diagnostic_oled_command(0x7F);
  schuss_diagnostic_oled_command(0x22);
  schuss_diagnostic_oled_command(page);
  schuss_diagnostic_oled_command(page);
  schuss_diagnostic_oled_command(0xB0 + page);
  schuss_diagnostic_oled_command(0x02);
  schuss_diagnostic_oled_command(0x10);
  i2cMasterTransmitTimeout(&I2CD1, 0x3C, SchussDiagnosticOledTx, 129, SchussDiagnosticOledRx, 0, 30);
  i2cReleaseBus(&I2CD1);
}

static msg_t schuss_diagnostic_oled_thread(void*) {
  i2cAcquireBus(&I2CD1);
  const uint8_t commands[] = {0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0x01,0x40,0x8D,0x14,0x20,0x00,0xA1,0xC8,0xDA,0x12,0x81,0xCF,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0x2E,0xAF};
  for (uint32_t index = 0; index < sizeof(commands); ++index) schuss_diagnostic_oled_command(commands[index]);
  i2cReleaseBus(&I2CD1);
  while (!chThdShouldTerminate()) {
    for (uint8_t page = 0; page < 8; ++page) schuss_diagnostic_oled_page(page);
    chThdSleepMilliseconds(32);
  }
  chThdExit((msg_t)0);
  return 0;
}

static void schuss_diagnostic_set_line(uint8_t line, const char* text) {
  uint8_t index = 0;
  while (index < 11 && text[index]) Diagnostic.display_text[line * 11 + index] = text[index++];
  while (index < 11) Diagnostic.display_text[line * 11 + index++] = ' ';
}

static void schuss_diagnostic_u2(char* text, uint8_t offset, uint8_t value) {
  text[offset] = '0' + ((value / 10) % 10);
  text[offset + 1] = '0' + (value % 10);
}

static void schuss_diagnostic_u4(char* text, uint8_t offset, uint16_t value) {
  text[offset] = '0' + ((value / 1000) % 10);
  text[offset + 1] = '0' + ((value / 100) % 10);
  text[offset + 2] = '0' + ((value / 10) % 10);
  text[offset + 3] = '0' + (value % 10);
}

static void schuss_diagnostic_show_pot(uint8_t index, uint16_t raw, uint8_t zone) {
  char line[12] = {'P','0','0',' ','0','0','0','0',' ','-',0,0};
  schuss_diagnostic_u2(line, 1, index + 1);
  schuss_diagnostic_u4(line, 4, raw);
  line[9] = zone == 1 ? 'L' : (zone == 2 ? 'M' : (zone == 3 ? 'H' : '-'));
  schuss_diagnostic_set_line(1, line);
}

static void schuss_diagnostic_show_button(uint8_t index, uint8_t event) {
  char line[12] = {'B','0',' ',' ',' ',' ',' ',' ',' ',' ',' ',0};
  if (index == 4) { line[0] = 'E'; line[1] = 'P'; }
  else line[1] = '1' + index;
  const char* label = (event & 4) ? "HOLD" : ((event & 1) ? "PRESS" : "RELEASE");
  uint8_t offset = 3;
  for (uint8_t i = 0; label[i] && offset < 11; ++i) line[offset++] = label[i];
  schuss_diagnostic_set_line(1, line);
}

static void schuss_diagnostic_show_encoder(int16_t value) {
  char line[12] = {'E','N','C',' ','+','0','0','0',' ',' ',' ',0};
  uint16_t magnitude = value < 0 ? (uint16_t)(-value) : (uint16_t)value;
  line[4] = value < 0 ? '-' : '+';
  line[5] = '0' + ((magnitude / 100) % 10);
  line[6] = '0' + ((magnitude / 10) % 10);
  line[7] = '0' + (magnitude % 10);
  schuss_diagnostic_set_line(1, line);
}

static uint8_t schuss_diagnostic_pot_count(void) {
  uint8_t count = 0;
  for (uint8_t index = 0; index < 10; ++index) if (Diagnostic.pots[index].monotonic_stage == 3) ++count;
  return count;
}

static uint8_t schuss_diagnostic_button_count(void) {
  uint8_t count = 0;
  for (uint8_t index = 0; index < 4; ++index) if (Diagnostic.buttons[index].event_mask == 7) ++count;
  return count;
}

static void schuss_diagnostic_update_summary(void) {
  const uint8_t pots = schuss_diagnostic_pot_count();
  const uint8_t buttons = schuss_diagnostic_button_count();
  const bool encoder = Diagnostic.encoder_positive >= 3 && Diagnostic.encoder_negative <= -3;
  const bool push = Diagnostic.buttons[4].event_mask == 7;
  if (pots == 10 && buttons == 4 && encoder && push && Diagnostic.led_scan_mask == 0x3F) {
    char pots_line[12] = "POTS 00/10";
    char buttons_line[12] = "BTNS 00/04";
    schuss_diagnostic_u2(pots_line, 5, pots);
    schuss_diagnostic_u2(buttons_line, 5, buttons);
    schuss_diagnostic_set_line(0, pots_line);
    schuss_diagnostic_set_line(1, buttons_line);
    schuss_diagnostic_set_line(2, "ENC OK PUSH");
    schuss_diagnostic_set_line(3, "LED 6 OLED?");
    return;
  }
  schuss_diagnostic_set_line(0, "TASK022");
  char led[12] = {'L','E','D','0',' ','A','C','T','I','V','E',0};
  led[3] = Diagnostic.active_led_channel ? ('0' + Diagnostic.active_led_channel) : '-';
  schuss_diagnostic_set_line(2, led);
  char summary[12] = {'P','0','0',' ','B','0','0',' ','-','-',' ',0};
  schuss_diagnostic_u2(summary, 1, pots);
  schuss_diagnostic_u2(summary, 5, buttons);
  summary[8] = encoder ? 'E' : '-';
  summary[9] = push ? 'P' : '-';
  schuss_diagnostic_set_line(3, summary);
}

static void schuss_diagnostic_set_led(uint8_t channel) {
  palWritePad(GPIOG,6, channel == 1);
  palWritePad(GPIOC,6, channel == 2);
  palWritePad(GPIOB,3, channel == 3);
  palWritePad(GPIOB,4, channel == 4);
  palWritePad(GPIOB,6, channel == 5);
  palWritePad(GPIOB,7, channel == 6);
}

static void initialize_gills_diagnostic_hardware(void) {
  palSetPadMode(GPIOB,5,PAL_MODE_INPUT);
  palSetPadMode(GPIOA,10,PAL_MODE_INPUT);
  palSetPadMode(GPIOB,12,PAL_MODE_INPUT);
  palSetPadMode(GPIOB,13,PAL_MODE_INPUT);
  palSetPadMode(GPIOC,7,PAL_MODE_INPUT_PULLUP);
  palSetPadMode(GPIOC,1,PAL_MODE_INPUT_PULLUP);
  palSetPadMode(GPIOA,9,PAL_MODE_INPUT_PULLDOWN);
  sysmon_disable_blinker();
  palSetPadMode(GPIOG,6,PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOC,6,PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB,3,PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB,4,PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB,6,PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB,7,PAL_MODE_OUTPUT_PUSHPULL);
  schuss_diagnostic_set_led(0);
  palSetPadMode(GPIOB,8,PAL_MODE_ALTERNATE(4) | PAL_STM32_PUDR_PULLUP | PAL_STM32_OTYPE_OPENDRAIN);
  palSetPadMode(GPIOB,9,PAL_MODE_ALTERNATE(4) | PAL_STM32_PUDR_PULLUP | PAL_STM32_OTYPE_OPENDRAIN);
  static const I2CConfig i2cfg = {OPMODE_I2C,400000,FAST_DUTY_CYCLE_2};
  i2cStart(&I2CD1,&i2cfg);
  Diagnostic.oled_thread = chThdCreateStatic(SchussDiagnosticOledWorkingArea,sizeof(SchussDiagnosticOledWorkingArea),NORMALPRIO,(tfunc_t)schuss_diagnostic_oled_thread,0);
}

static void initialize_gills_diagnostic_state(void) {
  for (uint8_t index = 0; index < 10; ++index) {
    Diagnostic.pots[index].last_raw = 0;
    Diagnostic.pots[index].sample_valid = false;
    Diagnostic.pots[index].zone_mask = 0;
    Diagnostic.pots[index].monotonic_stage = 0;
    Diagnostic.pots[index].discontinuity = false;
  }
  for (uint8_t index = 0; index < 5; ++index) {
    Diagnostic.buttons[index].candidate = false;
    Diagnostic.buttons[index].stable = false;
    Diagnostic.buttons[index].hold_sent = false;
    Diagnostic.buttons[index].candidate_updates = 0;
    Diagnostic.buttons[index].held_updates = 0;
    Diagnostic.buttons[index].event_mask = 0;
  }
  Diagnostic.encoder_a_last = true;
  Diagnostic.encoder_scan_counter = 0;
  Diagnostic.encoder_positive = 0;
  Diagnostic.encoder_negative = 0;
  Diagnostic.control_updates = 0;
  Diagnostic.led_scan_mask = 0;
  Diagnostic.active_led_channel = 0;
  Diagnostic.oled_thread = 0;
  schuss_diagnostic_set_line(0,"SCHUSS");
  schuss_diagnostic_set_line(1,"PANEL TEST");
  schuss_diagnostic_set_line(2,"TASK022");
  schuss_diagnostic_set_line(3,"READY");
}

static void process_gills_diagnostic(void) {
  static const uint8_t adc_index[10] = {0,1,2,3,6,7,8,9,11,12};
  ++Diagnostic.control_updates;
  uint8_t moved = 0;
  uint16_t moved_delta = 0;
  for (uint8_t index = 0; index < 10; ++index) {
    const uint16_t raw = adcvalues[adc_index[index]];
    const uint16_t delta = raw > Diagnostic.pots[index].last_raw ? raw - Diagnostic.pots[index].last_raw : Diagnostic.pots[index].last_raw - raw;
    if (delta > moved_delta) { moved = index; moved_delta = delta; }
    const uint8_t zone = schuss_diagnostic_zone(raw);
    if (zone) Diagnostic.pots[index].zone_mask |= 1 << (zone - 1);
    if (zone == 1 && Diagnostic.pots[index].monotonic_stage == 0) Diagnostic.pots[index].monotonic_stage = 1;
    else if (zone == 2 && Diagnostic.pots[index].monotonic_stage == 1) Diagnostic.pots[index].monotonic_stage = 2;
    else if (zone == 3 && Diagnostic.pots[index].monotonic_stage == 2) Diagnostic.pots[index].monotonic_stage = 3;
    if (Diagnostic.pots[index].sample_valid && ((Diagnostic.pots[index].last_raw <= 512 && raw >= 3583) || (Diagnostic.pots[index].last_raw >= 3583 && raw <= 512))) Diagnostic.pots[index].discontinuity = true;
    Diagnostic.pots[index].last_raw = raw;
    Diagnostic.pots[index].sample_valid = true;
  }
  if (Diagnostic.control_updates > 6000 && moved_delta >= 4) schuss_diagnostic_show_pot(moved,Diagnostic.pots[moved].last_raw,schuss_diagnostic_zone(Diagnostic.pots[moved].last_raw));

  const bool raw_buttons[5] = {(bool)palReadPad(GPIOB,5),(bool)palReadPad(GPIOA,10),(bool)palReadPad(GPIOB,12),(bool)palReadPad(GPIOB,13),(bool)palReadPad(GPIOA,9)};
  for (uint8_t index = 0; index < 5; ++index) {
    const uint8_t event = schuss_diagnostic_button_update(&Diagnostic.buttons[index],raw_buttons[index]);
    if (event && Diagnostic.control_updates > 6000) schuss_diagnostic_show_button(index,event);
  }
  if (Diagnostic.encoder_scan_counter == 0) {
    const bool encoder_a = (bool)palReadPad(GPIOC,7);
    if (!encoder_a && Diagnostic.encoder_a_last) {
      if (palReadPad(GPIOC,1)) --Diagnostic.encoder_negative;
      else ++Diagnostic.encoder_positive;
      if (Diagnostic.control_updates > 6000) schuss_diagnostic_show_encoder(palReadPad(GPIOC,1) ? Diagnostic.encoder_negative : Diagnostic.encoder_positive);
    }
    Diagnostic.encoder_a_last = encoder_a;
  }
  Diagnostic.encoder_scan_counter = (Diagnostic.encoder_scan_counter + 1) & 3;
  if (Diagnostic.control_updates > 6000) {
    const uint8_t channel = ((Diagnostic.control_updates - 6001) / 1500) % 6;
    Diagnostic.active_led_channel = channel + 1;
    Diagnostic.led_scan_mask |= 1 << channel;
    schuss_diagnostic_set_led(Diagnostic.active_led_channel);
    schuss_diagnostic_update_summary();
  }
  for (uint32_t index = 0; index < BUFSIZE; ++index) {
    AudioOutputLeft[index] = 0;
    AudioOutputRight[index] = 0;
  }
}

static void dispose_gills_diagnostic_hardware(void) {
  schuss_diagnostic_set_led(0);
  if (Diagnostic.oled_thread) {
    chThdTerminate(Diagnostic.oled_thread);
    chThdWait(Diagnostic.oled_thread);
    Diagnostic.oled_thread = 0;
  }
  i2cStop(&I2CD1);
  palSetPadMode(GPIOB,8,PAL_MODE_INPUT_ANALOG);
  palSetPadMode(GPIOB,9,PAL_MODE_INPUT_ANALOG);
}
'''


def diagnostic_cpp(base_cpp: str) -> str:
    anchors = {
        "declaration": "static volatile int32_t SchussBlendInputQ27;\n",
        "state": "  SchussBlendInputQ27 = 0;\n",
        "process": "  process_graph();\n",
        "dispose": "void PatchDispose(void) {\n",
        "hardware": "  initialize_state();\n",
    }
    for name, anchor in anchors.items():
        if base_cpp.count(anchor) != 1:
            raise ValueError(f"GILLS_DIAGNOSTIC_CPP_ANCHOR_INVALID:{name}")
    value = base_cpp.replace(
        anchors["declaration"], anchors["declaration"] + _DIAGNOSTIC_CPP, 1
    )
    value = value.replace(
        anchors["state"], anchors["state"] + "  initialize_gills_diagnostic_state();\n", 1
    )
    value = value.replace(anchors["process"], "  process_gills_diagnostic();\n", 1)
    value = value.replace(
        anchors["dispose"],
        anchors["dispose"] + "  dispose_gills_diagnostic_hardware();\n",
        1,
    )
    value = value.replace(
        anchors["hardware"],
        anchors["hardware"] + "  initialize_gills_diagnostic_hardware();\n",
        1,
    )
    return value


__all__ = [
    "DiagnosticState",
    "diagnostic_cpp",
    "diagnostic_host_vectors",
    "evaluate_diagnostic_update",
    "pot_zone",
]
