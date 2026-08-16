"""Deterministic Task 018 host model and C++ Gills panel realization."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Sequence


Q27_SCALE = 1 << 27
ADC_MAX = 4095
PICKUP_THRESHOLD_RAW = 16
DEBOUNCE_UPDATES = 4
HOLD_UPDATES = 1500
POT_ADC_INDICES = (0, 1, 2, 3, 6, 7, 8, 9, 11, 12)


def raw_to_q27(raw: int) -> int:
    if not 0 <= raw <= ADC_MAX:
        raise ValueError("GILLS_PANEL_ADC_RANGE_INVALID")
    return (raw * Q27_SCALE) // ADC_MAX


def q27_to_raw(value: int) -> int:
    value = min(Q27_SCALE, max(0, value))
    return (value * ADC_MAX) // Q27_SCALE


def smooth_q27(previous: int, target: int) -> int:
    """Apply the accepted signed arithmetic-shift response once."""

    return previous + ((target - previous) >> 3)


@dataclass
class ButtonState:
    candidate: bool = False
    stable: bool = False
    candidate_updates: int = 0
    held_updates: int = 0
    hold_sent: bool = False


@dataclass
class PanelState:
    smoothed_q27: list[int] = field(
        default_factory=lambda: [Q27_SCALE // 2] + [0] * 9
    )
    prior_pickup_raw: int = ADC_MAX // 2
    pickup_sample_valid: bool = False
    blend_q27: int = Q27_SCALE // 2
    pickup_armed: bool = True
    buttons: list[ButtonState] = field(default_factory=lambda: [ButtonState() for _ in range(5)])
    encoder_value: int = 0
    encoder_a_last: bool = True
    encoder_scan_counter: int = 0


def _button_update(state: ButtonState, raw: bool, label: str) -> tuple[ButtonState, list[str]]:
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
        events.append(label + ("-press" if value.stable else "-release"))
    if value.stable:
        value.held_updates += 1
        if value.held_updates >= HOLD_UPDATES and not value.hold_sent:
            value.hold_sent = True
            events.append(label + "-hold")
    return value, events


def _display_lines(blend_q27: int, pickup_armed: bool) -> list[str]:
    percent = min(100, max(0, (blend_q27 * 100 + (Q27_SCALE // 2)) // Q27_SCALE))
    return ["SCHUSS", f"BLEND {percent:03d}%", "PICKUP ARM" if pickup_armed else "PICKUP SET", "TASK018"]


def evaluate_panel_update(
    state: PanelState,
    raw_pots: Sequence[int],
    raw_buttons: Sequence[bool],
    encoder_a: bool,
    encoder_b: bool,
    encoder_push: bool,
) -> tuple[PanelState, dict[str, Any]]:
    if len(raw_pots) != 10 or len(raw_buttons) != 4:
        raise ValueError("GILLS_PANEL_VECTOR_SHAPE_INVALID")
    value = copy.deepcopy(state)
    transformed = [raw_to_q27(item) for item in raw_pots]
    value.smoothed_q27 = [smooth_q27(old, target) for old, target in zip(value.smoothed_q27, transformed)]
    current_raw = q27_to_raw(value.smoothed_q27[0])
    target_raw = q27_to_raw(value.blend_q27)
    crossed = value.pickup_sample_valid and (
        (value.prior_pickup_raw <= target_raw <= current_raw)
        or (current_raw <= target_raw <= value.prior_pickup_raw)
    )
    if value.pickup_armed and (abs(current_raw - target_raw) <= PICKUP_THRESHOLD_RAW or crossed):
        value.pickup_armed = False
    if not value.pickup_armed:
        value.blend_q27 = value.smoothed_q27[0]
    value.prior_pickup_raw = current_raw
    value.pickup_sample_valid = True

    events: list[str] = []
    for index, raw in enumerate((*raw_buttons, encoder_push)):
        value.buttons[index], new_events = _button_update(value.buttons[index], bool(raw), "encoder-push" if index == 4 else f"button-{index + 1}")
        events.extend(new_events)
    if "button-1-press" in events:
        value.blend_q27 = Q27_SCALE // 2
        value.pickup_armed = True
        value.prior_pickup_raw = current_raw
        value.pickup_sample_valid = True

    encoder_delta = 0
    if value.encoder_scan_counter == 0:
        if not encoder_a and value.encoder_a_last:
            encoder_delta = -1 if encoder_b else 1
            value.encoder_value += encoder_delta
            events.append("encoder-turn-negative" if encoder_delta < 0 else "encoder-turn-positive")
        value.encoder_a_last = bool(encoder_a)
    value.encoder_scan_counter = (value.encoder_scan_counter + 1) % 4
    return value, {
        "transformed_q27": transformed,
        "smoothed_q27": list(value.smoothed_q27),
        "blend_q27": value.blend_q27,
        "pickup_armed": value.pickup_armed,
        "events": events,
        "encoder_delta": encoder_delta,
        "encoder_value": value.encoder_value,
        "feedback": {"device-feedback-000001": value.pickup_armed},
        "display_lines": _display_lines(value.blend_q27, value.pickup_armed),
    }


def host_vectors() -> dict[str, Any]:
    pot_endpoints = [
        {
            "slot_id": f"device-input-{index:06d}",
            "raw_low": 0,
            "q27_low": raw_to_q27(0),
            "raw_mid": 2048,
            "q27_mid": raw_to_q27(2048),
            "raw_high": ADC_MAX,
            "q27_high": raw_to_q27(ADC_MAX),
        }
        for index in range(1, 11)
    ]
    smoothing = []
    value = 0
    for _ in range(4):
        value = smooth_q27(value, Q27_SCALE)
        smoothing.append(value)

    pickup_state = PanelState(
        smoothed_q27=[raw_to_q27(1900)] + [0] * 9,
        prior_pickup_raw=1900,
        pickup_sample_valid=True,
    )
    pickup_trace = []
    for raw in (1900, 2200, 2600, 3000, 3500, 4095):
        pickup_state, output = evaluate_panel_update(pickup_state, [raw] + [0] * 9, [False] * 4, True, True, False)
        pickup_trace.append({
            "raw": raw,
            "smoothed_raw": q27_to_raw(output["smoothed_q27"][0]),
            "blend_q27": output["blend_q27"],
            "pickup_armed": output["pickup_armed"],
        })

    button_state = PanelState()
    button_events: list[str] = []
    for raw, updates in ((True, DEBOUNCE_UPDATES), (True, HOLD_UPDATES), (False, DEBOUNCE_UPDATES)):
        for _ in range(updates):
            button_state, output = evaluate_panel_update(button_state, [0] * 10, [raw, False, False, False], True, True, False)
            button_events.extend(output["events"])

    positive = PanelState(encoder_a_last=True, encoder_scan_counter=0)
    positive, positive_output = evaluate_panel_update(positive, [0] * 10, [False] * 4, False, False, False)
    negative = PanelState(encoder_a_last=True, encoder_scan_counter=0)
    negative, negative_output = evaluate_panel_update(negative, [0] * 10, [False] * 4, False, True, False)
    return {
        "schema_version": "task018-panel-host-vectors-v0",
        "policies": {
            "adc_max": ADC_MAX,
            "q27_scale": Q27_SCALE,
            "smoothing_shift": 3,
            "pickup_threshold_raw": PICKUP_THRESHOLD_RAW,
            "debounce_updates": DEBOUNCE_UPDATES,
            "hold_updates": HOLD_UPDATES,
            "encoder_scan_divisor": 4,
        },
        "pot_endpoints": pot_endpoints,
        "smoothing_full_scale_from_zero": smoothing,
        "pickup_trace": pickup_trace,
        "button_1_events": button_events,
        "encoder_events": [positive_output["events"], negative_output["events"]],
        "display_examples": [_display_lines(0, True), _display_lines(Q27_SCALE // 2, False), _display_lines(Q27_SCALE, False)],
    }


_PANEL_DECLARATIONS = r'''

static const int32_t SchussQ27Scale = (1 << 27);
static const uint16_t SchussAdcMax = 4095;

struct SchussButtonRuntime {
  bool candidate;
  bool stable;
  bool hold_sent;
  uint16_t candidate_updates;
  uint16_t held_updates;
};

struct SchussPanelRuntime {
  int32_t smoothed_q27[10];
  uint16_t prior_pickup_raw;
  bool pickup_sample_valid;
  bool pickup_armed;
  SchussButtonRuntime buttons[5];
  int32_t encoder_value;
  bool encoder_a_last;
  uint8_t encoder_scan_counter;
  char display_text[44];
  Thread* oled_thread;
};

static SchussPanelRuntime Panel;
static WORKING_AREA(SchussOledWorkingArea, 192);
static uint8_t SchussOledTx[129] __attribute__((section(".sram2")));
static uint8_t SchussOledRx[1] __attribute__((section(".sram2")));

static int32_t schuss_raw_to_q27(uint16_t raw) {
  return (int32_t)(((int64_t)raw * SchussQ27Scale) / SchussAdcMax);
}

static uint16_t schuss_q27_to_raw(int32_t value) {
  value = value < 0 ? 0 : (value > SchussQ27Scale ? SchussQ27Scale : value);
  return (uint16_t)(((int64_t)value * SchussAdcMax) / SchussQ27Scale);
}

static uint8_t schuss_button_update(SchussButtonRuntime* state, bool raw) {
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
    events |= state->stable ? 1 : 2;
  }
  if (state->stable) {
    if (state->held_updates < 1500) ++state->held_updates;
    if (state->held_updates >= 1500 && !state->hold_sent) {
      state->hold_sent = true;
      events |= 4;
    }
  }
  return events;
}

static uint8_t schuss_glyph_column(char value, uint8_t column) {
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
    case 'H': { static const uint8_t v[5]={0x7F,0x08,0x08,0x08,0x7F}; return v[column]; }
    case 'I': { static const uint8_t v[5]={0x00,0x41,0x7F,0x41,0x00}; return v[column]; }
    case 'K': { static const uint8_t v[5]={0x7F,0x08,0x14,0x22,0x41}; return v[column]; }
    case 'L': { static const uint8_t v[5]={0x7F,0x40,0x40,0x40,0x40}; return v[column]; }
    case 'M': { static const uint8_t v[5]={0x7F,0x02,0x0C,0x02,0x7F}; return v[column]; }
    case 'N': { static const uint8_t v[5]={0x7F,0x04,0x08,0x10,0x7F}; return v[column]; }
    case 'P': { static const uint8_t v[5]={0x7F,0x09,0x09,0x09,0x06}; return v[column]; }
    case 'R': { static const uint8_t v[5]={0x7F,0x09,0x19,0x29,0x46}; return v[column]; }
    case 'S': { static const uint8_t v[5]={0x46,0x49,0x49,0x49,0x31}; return v[column]; }
    case 'T': { static const uint8_t v[5]={0x01,0x01,0x7F,0x01,0x01}; return v[column]; }
    case 'U': { static const uint8_t v[5]={0x3F,0x40,0x40,0x40,0x3F}; return v[column]; }
    case '%': { static const uint8_t v[5]={0x63,0x13,0x08,0x64,0x63}; return v[column]; }
    default: return 0;
  }
}

static void schuss_oled_command(uint8_t value) {
  uint8_t bytes[2] = {0, value};
  i2cMasterTransmitTimeout(&I2CD1, 0x3C, bytes, 2, SchussOledRx, 0, 30);
}

static void schuss_oled_send_page(uint8_t page) {
  static const uint8_t expand[16] = {0x00,0x03,0x0C,0x0F,0x30,0x33,0x3C,0x3F,0xC0,0xC3,0xCC,0xCF,0xF0,0xF3,0xFC,0xFF};
  SchussOledTx[0] = 0x40;
  uint32_t offset = 1;
  const uint8_t line = page >> 1;
  for (uint8_t character = 0; character < 11; ++character) {
    for (uint8_t column = 0; column < 5; ++column) {
      const uint8_t glyph = schuss_glyph_column(Panel.display_text[line * 11 + character], column);
      const uint8_t pixels = expand[(page & 1) ? ((glyph >> 4) & 15) : (glyph & 15)];
      SchussOledTx[offset++] = pixels;
      SchussOledTx[offset++] = pixels;
    }
    SchussOledTx[offset++] = 0;
  }
  while (offset < 129) SchussOledTx[offset++] = 0;
  i2cAcquireBus(&I2CD1);
  schuss_oled_command(0x21);
  schuss_oled_command(0x00);
  schuss_oled_command(0x7F);
  schuss_oled_command(0x22);
  schuss_oled_command(page);
  schuss_oled_command(page);
  schuss_oled_command(0xB0 + page);
  schuss_oled_command(0x02);
  schuss_oled_command(0x10);
  i2cMasterTransmitTimeout(&I2CD1, 0x3C, SchussOledTx, 129, SchussOledRx, 0, 30);
  i2cReleaseBus(&I2CD1);
}

static msg_t schuss_oled_thread(void*) {
  i2cAcquireBus(&I2CD1);
  const uint8_t commands[] = {0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0x01,0x40,0x8D,0x14,0x20,0x00,0xA1,0xC8,0xDA,0x12,0x81,0xCF,0xD9,0xF1,0xDB,0x40,0xA4,0xA6,0x2E,0xAF};
  for (uint32_t index = 0; index < sizeof(commands); ++index) schuss_oled_command(commands[index]);
  i2cReleaseBus(&I2CD1);
  while (!chThdShouldTerminate()) {
    for (uint8_t page = 0; page < 8; ++page) schuss_oled_send_page(page);
    chThdSleepMilliseconds(32);
  }
  chThdExit((msg_t)0);
  return 0;
}

static void schuss_set_display_line(uint8_t line, const char* text) {
  uint8_t index = 0;
  while (index < 11 && text[index]) {
    Panel.display_text[line * 11 + index] = text[index];
    ++index;
  }
  while (index < 11) Panel.display_text[line * 11 + index++] = ' ';
}

static void schuss_update_display(void) {
  char blend[11] = {'B','L','E','N','D',' ', '0','0','0','%',0};
  int32_t percent = (SchussBlendInputQ27 * 100 + (SchussQ27Scale >> 1)) / SchussQ27Scale;
  percent = percent < 0 ? 0 : (percent > 100 ? 100 : percent);
  blend[6] = '0' + ((percent / 100) % 10);
  blend[7] = '0' + ((percent / 10) % 10);
  blend[8] = '0' + (percent % 10);
  schuss_set_display_line(0, "SCHUSS");
  schuss_set_display_line(1, blend);
  schuss_set_display_line(2, Panel.pickup_armed ? "PICKUP ARM" : "PICKUP SET");
  schuss_set_display_line(3, "TASK018");
}

static void initialize_gills_panel_hardware(void) {
  const uint8_t button_pins[4] = {5,10,12,13};
  palSetPadMode(GPIOB, button_pins[0], PAL_MODE_INPUT);
  palSetPadMode(GPIOA, button_pins[1], PAL_MODE_INPUT);
  palSetPadMode(GPIOB, button_pins[2], PAL_MODE_INPUT);
  palSetPadMode(GPIOB, button_pins[3], PAL_MODE_INPUT);
  palSetPadMode(GPIOC, 7, PAL_MODE_INPUT_PULLUP);
  palSetPadMode(GPIOC, 1, PAL_MODE_INPUT_PULLUP);
  palSetPadMode(GPIOA, 9, PAL_MODE_INPUT_PULLDOWN);
  sysmon_disable_blinker();
  palSetPadMode(GPIOG, 6, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOC, 6, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB, 3, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB, 4, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB, 6, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB, 7, PAL_MODE_OUTPUT_PUSHPULL);
  palSetPadMode(GPIOB, 8, PAL_MODE_ALTERNATE(4) | PAL_STM32_PUDR_PULLUP | PAL_STM32_OTYPE_OPENDRAIN);
  palSetPadMode(GPIOB, 9, PAL_MODE_ALTERNATE(4) | PAL_STM32_PUDR_PULLUP | PAL_STM32_OTYPE_OPENDRAIN);
  static const I2CConfig i2cfg = {OPMODE_I2C, 400000, FAST_DUTY_CYCLE_2};
  i2cStart(&I2CD1, &i2cfg);
  Panel.oled_thread = chThdCreateStatic(SchussOledWorkingArea, sizeof(SchussOledWorkingArea), NORMALPRIO, (tfunc_t)schuss_oled_thread, 0);
}

static void initialize_gills_panel_state(void) {
  for (uint8_t index = 0; index < 10; ++index) Panel.smoothed_q27[index] = 0;
  Panel.smoothed_q27[0] = SchussQ27Scale >> 1;
  Panel.prior_pickup_raw = SchussAdcMax >> 1;
  Panel.pickup_sample_valid = false;
  Panel.pickup_armed = true;
  for (uint8_t index = 0; index < 5; ++index) {
    Panel.buttons[index].candidate = false;
    Panel.buttons[index].stable = false;
    Panel.buttons[index].hold_sent = false;
    Panel.buttons[index].candidate_updates = 0;
    Panel.buttons[index].held_updates = 0;
  }
  Panel.encoder_value = 0;
  Panel.encoder_a_last = true;
  Panel.encoder_scan_counter = 0;
  Panel.oled_thread = 0;
  SchussBlendInputQ27 = SchussQ27Scale >> 1;
  schuss_update_display();
}

static void process_gills_panel(void) {
  static const uint8_t adc_index[10] = {0,1,2,3,6,7,8,9,11,12};
  for (uint8_t index = 0; index < 10; ++index) {
    const int32_t target = schuss_raw_to_q27(adcvalues[adc_index[index]]);
    Panel.smoothed_q27[index] += (target - Panel.smoothed_q27[index]) >> 3;
  }
  const uint16_t current_raw = schuss_q27_to_raw(Panel.smoothed_q27[0]);
  const uint16_t target_raw = schuss_q27_to_raw(SchussBlendInputQ27);
  const bool crossed = Panel.pickup_sample_valid && ((Panel.prior_pickup_raw <= target_raw && target_raw <= current_raw) || (current_raw <= target_raw && target_raw <= Panel.prior_pickup_raw));
  const int32_t distance = (int32_t)current_raw - target_raw;
  if (Panel.pickup_armed && ((distance >= -16 && distance <= 16) || crossed)) Panel.pickup_armed = false;
  if (!Panel.pickup_armed) SchussBlendInputQ27 = Panel.smoothed_q27[0];
  Panel.prior_pickup_raw = current_raw;
  Panel.pickup_sample_valid = true;

  const bool raw_buttons[5] = {
    (bool)palReadPad(GPIOB,5), (bool)palReadPad(GPIOA,10), (bool)palReadPad(GPIOB,12), (bool)palReadPad(GPIOB,13), (bool)palReadPad(GPIOA,9)
  };
  uint8_t events[5];
  for (uint8_t index = 0; index < 5; ++index) events[index] = schuss_button_update(&Panel.buttons[index], raw_buttons[index]);
  if (events[0] & 1) {
    SchussBlendInputQ27 = SchussQ27Scale >> 1;
    Panel.pickup_armed = true;
    Panel.prior_pickup_raw = current_raw;
    Panel.pickup_sample_valid = true;
  }
  if (Panel.encoder_scan_counter == 0) {
    const bool encoder_a = (bool)palReadPad(GPIOC,7);
    if (!encoder_a && Panel.encoder_a_last) Panel.encoder_value += palReadPad(GPIOC,1) ? -1 : 1;
    Panel.encoder_a_last = encoder_a;
  }
  Panel.encoder_scan_counter = (Panel.encoder_scan_counter + 1) & 3;
  palWritePad(GPIOG,6, Panel.pickup_armed);
  schuss_update_display();
}

static void dispose_gills_panel_hardware(void) {
  if (Panel.oled_thread) {
    chThdTerminate(Panel.oled_thread);
    chThdWait(Panel.oled_thread);
    Panel.oled_thread = 0;
  }
  i2cStop(&I2CD1);
  palSetPadMode(GPIOB, 8, PAL_MODE_INPUT_ANALOG);
  palSetPadMode(GPIOB, 9, PAL_MODE_INPUT_ANALOG);
}
'''


def mapped_cpp(base_cpp: str) -> str:
    anchors = {
        "declaration": "static volatile int32_t SchussBlendInputQ27;\n",
        "state": "  SchussBlendInputQ27 = 0;\n",
        "process": "  process_graph();\n",
        "dispose": "void PatchDispose(void) {\n",
        "hardware": "  initialize_state();\n",
    }
    for name, anchor in anchors.items():
        if base_cpp.count(anchor) != 1:
            raise ValueError(f"GILLS_PANEL_CPP_ANCHOR_INVALID:{name}")
    value = base_cpp.replace(anchors["declaration"], anchors["declaration"] + _PANEL_DECLARATIONS, 1)
    value = value.replace(anchors["state"], "  initialize_gills_panel_state();\n", 1)
    value = value.replace(anchors["process"], "  process_gills_panel();\n" + anchors["process"], 1)
    value = value.replace(anchors["dispose"], anchors["dispose"] + "  dispose_gills_panel_hardware();\n", 1)
    value = value.replace(anchors["hardware"], anchors["hardware"] + "  initialize_gills_panel_hardware();\n", 1)
    return value


def correct_mapped_cpp_dma_buffers(mapped_cpp_value: str) -> str:
    """Version an existing Task 018 mapped source at the two unsafe anchors."""

    value = mapped_cpp_value
    replacements = (
        (
            'static uint8_t SchussOledTx[129] __attribute__((section(".sram2")));\n'
            'static uint8_t SchussOledRx[1] __attribute__((section(".sram2")));\n',
            'static uint8_t SchussOledTx[129] __attribute__((section(".sram2")));\n'
            'static uint8_t SchussOledCommand[2] __attribute__((section(".sram2")));\n'
            'static uint8_t SchussOledRx[1] __attribute__((section(".sram2")));\n',
            "declaration",
        ),
        (
            "static void schuss_oled_command(uint8_t value) {\n"
            "  uint8_t bytes[2] = {0, value};\n"
            "  i2cMasterTransmitTimeout(&I2CD1, 0x3C, bytes, 2, SchussOledRx, 0, 30);\n"
            "}\n",
            "static void schuss_oled_command(uint8_t value) {\n"
            "  SchussOledCommand[0] = 0;\n"
            "  SchussOledCommand[1] = value;\n"
            "  i2cMasterTransmitTimeout(&I2CD1, 0x3C, SchussOledCommand, 2, SchussOledRx, 0, 30);\n"
            "}\n",
            "command-buffer",
        ),
    )
    for original, corrected, name in replacements:
        if value.count(original) != 1:
            raise ValueError(f"GILLS_PANEL_DMA_SAFE_ANCHOR_INVALID:{name}")
        value = value.replace(original, corrected, 1)
    return value


def mapped_cpp_dma_safe(base_cpp: str) -> str:
    """Return the Task 021 successor with DMA-visible OLED command storage."""

    return correct_mapped_cpp_dma_buffers(mapped_cpp(base_cpp))


__all__ = [
    "PanelState",
    "correct_mapped_cpp_dma_buffers",
    "evaluate_panel_update",
    "host_vectors",
    "mapped_cpp",
    "mapped_cpp_dma_safe",
    "q27_to_raw",
    "raw_to_q27",
    "smooth_q27",
]
