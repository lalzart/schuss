#pragma once

#include <array>
#include <cstddef>
#include <string_view>

namespace wirefall {

inline constexpr std::string_view kControlMapSha256{"f97dde2a8d2d8d52e29249466b8325afbc703fad847aa9ef337649bae11e2ccd"};

enum class PublicControl : std::size_t {
    tension,
    cut,
    shadow,
    root,
    bite,
    holes,
    edge,
    under,
    swing,
    space,
    void_control,
    open,
    flip,
    flip_cancel,
    downbeat,
    panic,
    tempo,
    tap_tempo,
    reset,
    count,
};

struct PublicControlDescriptor {
    PublicControl id;
    std::string_view name;
    std::string_view selector;
    std::string_view default_value;
    std::string_view semantic_transform;
};

inline constexpr std::array<PublicControlDescriptor, 19> kPublicControlDescriptors{{
    {PublicControl::tension, "TENSION", "device-input-000001", "0.38", "25 ms smoothing; raises Wire pitch by 42*TENSION^1.35 semitones and couples approved fold, Q, drive, and compensation curves"},
    {PublicControl::cut, "CUT", "device-input-000002", "OPEN", "nine equal zones with 0.015 normalized hysteresis; commit on next beat while retaining beat phase"},
    {PublicControl::shadow, "SHADOW", "device-input-000003", "0.0", "8 ms smoothing; complementary gain sqrt(SHADOW)*sin(pi*q/2); zero is true cut silence"},
    {PublicControl::root, "ROOT", "device-input-000004", "0.5", "15 ms smoothing; fRoot=55*2^(2*normalized) shared by Wire and Shadow"},
    {PublicControl::bite, "BITE", "device-input-000005", "0.55", "10 ms smoothing; controls approved SVF center and Q contribution with finite clamps"},
    {PublicControl::holes, "HOLES", "device-input-000006", "3", "integer numerator k over denominator 8; commit on next beat and reset scheduler err to zero"},
    {PublicControl::edge, "EDGE", "device-input-000007", "4.0", "tau=1.5+28.5*normalized^2 ms, clamped to 45 percent of current slot"},
    {PublicControl::under, "UNDER", "device-input-000008", "1/2", "five detented zones with hysteresis and 20 ms equal-power crossfade between two preallocated Shadow oscillators"},
    {PublicControl::swing, "SWING", "device-input-000009", "50", "alternating opportunity displacement with strictly increasing boundaries and at least 32 frames separation"},
    {PublicControl::space, "SPACE", "device-input-000010", "0.12", "10 ms smoothing; voice-local 67/89 ms cross delays, wet 0.28*SPACE, feedback 0.32*SPACE, before complementary VCA"},
    {PublicControl::void_control, "VOID", "device-input-000011", "False", "momentary effective Shadow-zero override with 3 ms ramp; SHADOW target retained"},
    {PublicControl::open, "OPEN", "device-input-000012", "False", "momentary open-Wire override with 3 ms ramp; scheduler remains running"},
    {PublicControl::flip, "FLIP", "device-input-000013", "normal", "swap voice ownership of cut state with 10 ms complementary transition from current q"},
    {PublicControl::flip_cancel, "FLIP_CANCEL", "device-input-000013", "action", "action returning to normal on next beat"},
    {PublicControl::downbeat, "DOWNBEAT", "device-input-000014", "action", "action resetting beat phase and scheduler err without resetting oscillators, filters, delays, or parameters"},
    {PublicControl::panic, "PANIC", "device-input-000014", "action", "hold action latches Panic following state-matrix.md; release after the recognized hold emits PANIC_RELEASE, while RESET uses the full Reset transition"},
    {PublicControl::tempo, "TEMPO", "device-input-000015", "120", "relative encoder steps by 1 BPM below 160 and 2 BPM at or above 160; preserves normalized beat phase"},
    {PublicControl::tap_tempo, "TAP_TEMPO", "device-input-000016", "action", "action using median of last three valid 250-2000 ms intervals; invalid intervals and single taps do not change tempo"},
    {PublicControl::reset, "RESET", "device-input-000016", "action", "full musical reset with the exact down/clear/up timing in state-matrix.md"},
}};

static_assert(kPublicControlDescriptors.size() == static_cast<std::size_t>(PublicControl::count));

}  // namespace wirefall
