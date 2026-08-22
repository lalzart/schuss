#!/usr/bin/env python3
"""Generate the prototype's bounded C++ rhythm bank and lane recipes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_PRESET = ROOT / "fixtures" / "preset-v0.json"
LEGACY_RHYTHM_EXTENSION = ROOT / "fixtures" / "rhythm-bank-v1.json"
RHYTHM_EXTENSION = ROOT / "fixtures" / "rhythm-bank-v2.json"
OUTPUT = ROOT / "generated" / "preset_data.hpp"
LANES = (
    "kick",
    "snare",
    "hat",
    "percussion_1",
    "percussion_2",
    "percussion_3",
)
MODELS = {
    "kick": "kick",
    "snare": "snare",
    "cymbal": "cymbal",
    "sine_triangle": "sine_triangle",
    "fm": "fm",
    "filtered_noise": "filtered_noise",
}


def fail(message: str) -> None:
    raise ValueError(message)


def canonical_bytes(document: Any) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode()


def decay_multiplier_q31(milliseconds: int) -> int:
    if not 1 <= milliseconds <= 10000:
        fail(f"decay milliseconds out of range: {milliseconds}")
    frames = milliseconds * 48
    return round(math.pow(0.0001, 1.0 / frames) * 2147483647.0)


def meter_bar_length(rhythm: dict[str, Any], label: str) -> Fraction:
    meter = rhythm.get("meter")
    if not isinstance(meter, dict):
        fail(f"{label}: meter must be an object")
    numerator = meter.get("numerator")
    denominator = meter.get("note_value_denominator")
    if not isinstance(numerator, int) or not 1 <= numerator <= 16:
        fail(f"{label}: meter numerator out of range")
    if not isinstance(denominator, int) or denominator not in {1, 2, 4, 8, 16}:
        fail(f"{label}: note-value denominator is unsupported")
    return Fraction(numerator * 4, denominator)


def validate_position(
    position: Any,
    label: str,
    bar_length: Fraction,
) -> tuple[int, int]:
    if not isinstance(position, list) or len(position) != 2:
        fail(f"{label}: position must contain numerator and denominator")
    numerator, denominator = position
    if not isinstance(numerator, int) or not isinstance(denominator, int):
        fail(f"{label}: rational fields must be integers")
    if numerator < 0 or denominator < 1 or denominator > 64:
        fail(f"{label}: rational position is out of bounds")
    if math.gcd(numerator, denominator) != 1:
        fail(f"{label}: rational position must be reduced")
    if Fraction(numerator, denominator) >= bar_length:
        fail(f"{label}: event falls outside its meter-specific bar")
    return numerator, denominator


def expand_templates(
    templates: Any,
    group: int,
    ordinal: int,
    phrase_bars: int,
    bar_length: Fraction,
    rhythm_label: str,
) -> tuple[list[dict[str, int]], int]:
    if not isinstance(templates, list):
        fail(f"{rhythm_label}: event template collection must be a list")
    expanded: list[dict[str, int]] = []
    for template_index, template in enumerate(templates):
        label = f"{rhythm_label} event template {template_index}"
        if not isinstance(template, dict):
            fail(f"{label} must be an object")
        lane = template.get("lane")
        if lane not in LANES:
            fail(f"{label}: unknown lane {lane!r}")
        numerator, denominator = validate_position(
            template.get("position"), label, bar_length
        )
        threshold = template.get("threshold")
        velocity = template.get("velocity")
        articulation = template.get("articulation")
        if not isinstance(threshold, int) or not 0 <= threshold <= 65535:
            fail(f"{label}: threshold out of range")
        if not isinstance(velocity, int) or not 0 <= velocity <= 32767:
            fail(f"{label}: velocity out of range")
        if not isinstance(articulation, int) or not 0 <= articulation <= 255:
            fail(f"{label}: articulation out of range")
        bars = template.get("bars")
        if not isinstance(bars, list) or not bars:
            fail(f"{label}: bars must not be empty")
        for bar in bars:
            if not isinstance(bar, int) or not 0 <= bar < phrase_bars:
                fail(f"{label}: bar out of range")
            expanded.append(
                {
                    "bar": bar,
                    "numerator": numerator,
                    "denominator": denominator,
                    "lane": LANES.index(lane),
                    "threshold": threshold,
                    "velocity": velocity,
                    "articulation": articulation,
                    "group": group,
                    "ordinal": ordinal,
                }
            )
            ordinal += 1
    return expanded, ordinal


def compile_rhythm(
    rhythm: dict[str, Any],
    fingerprint: str,
) -> dict[str, Any]:
    rhythm_id = rhythm.get("id")
    name = rhythm.get("name")
    if not isinstance(rhythm_id, str) or not rhythm_id:
        fail("rhythm id must be a nonempty string")
    if not isinstance(name, str) or not name:
        fail(f"{rhythm_id}: name must be a nonempty string")
    family = rhythm.get("family")
    grouping = rhythm.get("grouping")
    source_relationship = rhythm.get("source_relationship")
    source_urls = rhythm.get("source_urls")
    authenticity_claim = rhythm.get("authenticity_claim")
    if not isinstance(family, str) or not family:
        fail(f"{rhythm_id}: family must be a nonempty string")
    if not isinstance(grouping, str) or not grouping:
        fail(f"{rhythm_id}: grouping must be a nonempty string")
    if not isinstance(source_relationship, str) or not source_relationship:
        fail(f"{rhythm_id}: source_relationship must be a nonempty string")
    if (not isinstance(source_urls, list) or not source_urls
            or not all(isinstance(url, str) and url.startswith("https://") for url in source_urls)):
        fail(f"{rhythm_id}: source_urls must contain public HTTPS references")
    if authenticity_claim is not False:
        fail(f"{rhythm_id}: prototype studies must explicitly decline authenticity claims")
    phrase_bars = rhythm.get("phrase_bars")
    if not isinstance(phrase_bars, int) or not 1 <= phrase_bars <= 8:
        fail(f"{rhythm_id}: phrase_bars out of range")
    bar_length = meter_bar_length(rhythm, rhythm_id)

    events: list[dict[str, int]] = []
    ordinal = 0
    added, ordinal = expand_templates(
        rhythm.get("event_templates"), 0, ordinal, phrase_bars, bar_length, rhythm_id
    )
    events.extend(added)
    minimums = [0, 0, 0]
    groups = rhythm.get("variation_groups")
    if not isinstance(groups, list) or [group.get("id") for group in groups] != [1, 2]:
        fail(f"{rhythm_id}: variation groups 1 and 2 are required")
    for group in groups:
        group_id = group["id"]
        minimum = group.get("minimum_enthusiasm")
        if not isinstance(minimum, int) or not 1 <= minimum <= 65535:
            fail(f"{rhythm_id} variation group {group_id}: invalid minimum")
        minimums[group_id] = minimum
        added, ordinal = expand_templates(
            group.get("events"), group_id, ordinal, phrase_bars, bar_length, rhythm_id
        )
        events.extend(added)
    fill_group = rhythm.get("fill_group")
    if not isinstance(fill_group, dict) or fill_group.get("id") != 100:
        fail(f"{rhythm_id}: fill group 100 is required")
    added, ordinal = expand_templates(
        fill_group.get("events"), 100, ordinal, phrase_bars, bar_length, rhythm_id
    )
    events.extend(added)
    events.sort(
        key=lambda event: (
            event["bar"],
            Fraction(event["numerator"], event["denominator"]),
            event["lane"],
            event["ordinal"],
        )
    )
    denominator_lcm = math.lcm(*(event["denominator"] for event in events))
    if denominator_lcm > 65535:
        fail(f"{rhythm_id}: denominator LCM exceeds 65535")
    return {
        "id": rhythm_id,
        "name": name,
        "family": family,
        "grouping": grouping,
        "source_relationship": source_relationship,
        "authenticity_claim": authenticity_claim,
        "fingerprint": fingerprint,
        "meter_numerator": rhythm["meter"]["numerator"],
        "note_value_denominator": rhythm["meter"]["note_value_denominator"],
        "phrase_bars": phrase_bars,
        "denominator_lcm": denominator_lcm,
        "minimums": minimums,
        "events": events,
    }


def render() -> str:
    preset = json.loads(BASE_PRESET.read_text(encoding="utf-8"))
    legacy_extension = json.loads(LEGACY_RHYTHM_EXTENSION.read_text(encoding="utf-8"))
    extension = json.loads(RHYTHM_EXTENSION.read_text(encoding="utf-8"))
    if preset.get("schema_version") != "schuss-generative-drum-preset-prototype-v0":
        fail("base preset schema version mismatch")
    if legacy_extension.get("schema_version") != "schuss-generative-rhythm-bank-extension-prototype-v1":
        fail("legacy rhythm extension schema version mismatch")
    if extension.get("schema_version") != "schuss-generative-rhythm-bank-extension-prototype-v2":
        fail("rhythm extension schema version mismatch")

    recipes = preset.get("recipes")
    if not isinstance(recipes, list) or [item.get("lane") for item in recipes] != list(LANES):
        fail("recipes must contain the six lanes in canonical order")

    base_rhythm = {
        "id": "first-light",
        "name": preset.get("name"),
        "meter": preset.get("meter"),
        "phrase_bars": preset.get("phrase_bars"),
        "event_templates": preset.get("event_templates"),
        "variation_groups": preset.get("variation_groups"),
        "fill_group": preset.get("fill_group"),
        "family": "Schuss original",
        "grouping": "4/4",
        "source_relationship": "Independently authored Schuss reference groove.",
        "source_urls": ["https://github.com/pichenettes/eurorack"],
        "authenticity_claim": False,
    }
    legacy_rhythms = legacy_extension.get("rhythms")
    new_rhythms = extension.get("rhythms")
    if not isinstance(legacy_rhythms, list) or len(legacy_rhythms) != 3:
        fail("legacy rhythm extension must contain exactly three rhythms")
    if not isinstance(new_rhythms, list) or len(new_rhythms) != 11:
        fail("rhythm extension v2 must contain exactly eleven rhythms")
    extra_rhythms = []
    for legacy in legacy_rhythms:
        upgraded = dict(legacy)
        upgraded.update({
            "family": "Schuss original",
            "grouping": f"{legacy['meter']['numerator']}/{legacy['meter']['note_value_denominator']}",
            "source_relationship": "Independently authored Schuss reference groove retained from prototype v0.3.",
            "source_urls": ["https://github.com/pichenettes/eurorack"],
            "authenticity_claim": False,
        })
        extra_rhythms.append(upgraded)
    extra_rhythms.extend(new_rhythms)
    rhythm_inputs = [base_rhythm, *extra_rhythms]
    if [item.get("id") for item in rhythm_inputs] != [
        "first-light", "three-turn", "rolling-six", "five-across",
        "samba-enredo-study", "partido-alto-study", "samba-de-roda-study",
        "samba-reggae-study", "maracatu-pulse-study", "candombe-conversation",
        "chacarera-cross-meter", "aksak-five-study", "aksak-seven-study",
        "aksak-nine-study", "jhaptal-cycle-study",
    ]:
        fail("rhythm bank identity/order drift")
    fingerprints = [hashlib.sha256(canonical_bytes(preset)).hexdigest()]
    fingerprints.extend(
        hashlib.sha256(canonical_bytes(item)).hexdigest() for item in extra_rhythms
    )
    rhythms = [
        compile_rhythm(item, fingerprints[index])
        for index, item in enumerate(rhythm_inputs)
    ]
    bank_fingerprint = hashlib.sha256(
        canonical_bytes({"base": preset, "legacy_extension": legacy_extension, "extension": extension})
    ).hexdigest()

    flat_events: list[dict[str, int]] = []
    for rhythm in rhythms:
        rhythm["event_offset"] = len(flat_events)
        flat_events.extend(rhythm["events"])

    lines = [
        "// Generated by tools/generate_fixture.py; do not edit.",
        "#pragma once",
        "",
        "#include \"schuss/generative_drum_machine/core.hpp\"",
        "",
        "#include <array>",
        "#include <cstdint>",
        "",
        "namespace schuss::generative_drum_machine::generated {",
        "",
        "struct RhythmPresetDescriptor final {",
        "    const char* id;",
        "    const char* name;",
        "    const char* family;",
        "    const char* grouping;",
        "    const char* source_relationship;",
        "    const char* fingerprint;",
        "    std::uint8_t meter_numerator;",
        "    std::uint8_t note_value_denominator;",
        "    std::uint8_t phrase_bars;",
        "    std::uint16_t denominator_lcm;",
        "    std::uint32_t event_offset;",
        "    std::uint32_t event_count;",
        "    std::array<std::uint16_t, 3> variation_minimum_enthusiasm;",
        "    bool authenticity_claim;",
        "};",
        "",
        f'inline constexpr const char* kPresetName = "First Light Rhythm Bank";',
        f'inline constexpr const char* kPresetFingerprint = "{bank_fingerprint}";',
        "",
        "inline constexpr std::array<LaneRecipe, kLogicalLaneCount> kLaneRecipes{{",
    ]
    fast_multipliers: list[int] = []
    slow_multipliers: list[int] = []
    for recipe in recipes:
        model = recipe.get("model")
        if model not in MODELS:
            fail(f"unknown model {model!r}")
        scalar_fields = (
            "base_pitch_q7", "timbre_u15", "color_u15", "pitch_env_amount_q7",
            "timbre_env_amount_s15", "color_env_amount_s15", "gain_q15", "pan_s15",
            "choke_group", "priority",
        )
        for field in scalar_fields:
            if not isinstance(recipe.get(field), int):
                fail(f"recipe {recipe['lane']}: {field} must be an integer")
        amp_ms = recipe.get("amp_decay_ms")
        transient_ms = recipe.get("transient_decay_ms")
        amp = decay_multiplier_q31(amp_ms)
        transient = decay_multiplier_q31(transient_ms)
        fast_multipliers.append(decay_multiplier_q31(max(1, round(amp_ms / 4))))
        slow_multipliers.append(decay_multiplier_q31(amp_ms * 4))
        lines.append(
            "    LaneRecipe{BraidsModel::%s, %d, %dU, %dU, %d, %d, %d, %dU, %dU, %dU, %d, %dU, %dU},"
            % (
                MODELS[model], recipe["base_pitch_q7"], recipe["timbre_u15"],
                recipe["color_u15"], recipe["pitch_env_amount_q7"],
                recipe["timbre_env_amount_s15"], recipe["color_env_amount_s15"],
                amp, transient, recipe["gain_q15"], recipe["pan_s15"],
                recipe["choke_group"], recipe["priority"],
            )
        )
    lines.extend(
        [
            "}};",
            "",
            "inline constexpr std::array<std::uint32_t, kLogicalLaneCount> kFastAmpDecayMultipliers{{",
            "    " + ", ".join(f"{value}U" for value in fast_multipliers) + ",",
            "}};",
            "inline constexpr std::array<std::uint32_t, kLogicalLaneCount> kSlowAmpDecayMultipliers{{",
            "    " + ", ".join(f"{value}U" for value in slow_multipliers) + ",",
            "}};",
            "",
            f"inline constexpr std::array<RhythmPresetDescriptor, {len(rhythms)}> kRhythmPresets{{{{",
        ]
    )
    for rhythm in rhythms:
        minimums = rhythm["minimums"]
        lines.append(
            "    {%s, %s, %s, %s, %s, %s, %dU, %dU, %dU, %dU, %dU, %dU, {{%dU, %dU, %dU}}, %s},"
            % (
                json.dumps(rhythm["id"]), json.dumps(rhythm["name"]),
                json.dumps(rhythm["family"]), json.dumps(rhythm["grouping"]),
                json.dumps(rhythm["source_relationship"]),
                json.dumps(rhythm["fingerprint"]), rhythm["meter_numerator"],
                rhythm["note_value_denominator"], rhythm["phrase_bars"],
                rhythm["denominator_lcm"], rhythm["event_offset"],
                len(rhythm["events"]), minimums[0], minimums[1], minimums[2],
                "true" if rhythm["authenticity_claim"] else "false",
            )
        )
    lines.extend(
        [
            "}};",
            "",
            f"inline constexpr std::array<PatternEvent, {len(flat_events)}> kPatternEvents{{{{",
        ]
    )
    for event in flat_events:
        lines.append(
            "    PatternEvent{%dU, Rational{%dU, %dU}, Lane::%s, %dU, %dU, %dU, %dU, %dU},"
            % (
                event["bar"], event["numerator"], event["denominator"],
                LANES[event["lane"]], event["threshold"], event["velocity"],
                event["articulation"], event["group"], event["ordinal"],
            )
        )
    lines.extend(["}};", "", "}  // namespace schuss::generative_drum_machine::generated", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = render()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"fixture generation failed: {error}")
        return 1
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
            print(f"generated fixture is stale: {OUTPUT}")
            return 1
        print("generative drum fixture: fresh")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(expected, encoding="utf-8", newline="\n")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
