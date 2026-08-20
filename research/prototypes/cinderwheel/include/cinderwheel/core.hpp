#pragma once

#include "cinderwheel/control_map.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>

namespace cinderwheel {

inline constexpr double kReferenceSampleRate = 48000.0;
inline constexpr std::uint32_t kMaximumBlockFrames = 512;
inline constexpr std::size_t kMaximumMidiEventsPerBlock = 128;
inline constexpr float kOutputCeiling = 0.891250938f;  // -1 dBFS.

enum class SourceMode : std::uint8_t { reed, rnd, fold, dust };
enum class ScaleMode : std::uint8_t { minor_pentatonic, dorian, harmonic_minor, fifths };
enum class FxMode : std::uint8_t { clean, filter, drive };
enum class WaveTarget : std::uint8_t { pitch, body, grain, all };
enum class WakeEventKind : std::uint8_t { primary, afterstrike };

struct MidiEvent {
    std::uint32_t sample_offset{};
    std::uint64_t ingress_sequence{};
    std::array<std::uint8_t, 3> bytes{};
    std::uint8_t size{3};
};

struct WakeEvent {
    // Absolute index of the first output sample affected by the strike.
    std::uint64_t sample_index{};
    std::uint64_t ingress_sequence{};
    std::uint32_t transition_index{};
    std::uint8_t voice{};
    WakeEventKind kind{WakeEventKind::primary};
    float ledger_energy{};
};

struct Diagnostics {
    std::uint64_t processed_frames{};
    std::uint64_t stage_transitions{};
    std::uint64_t primary_strikes{};
    std::uint64_t afterstrikes{};
    std::uint64_t event_cap_hits{};
    std::uint64_t event_sink_overflows{};
    std::uint64_t ignored_midi_messages{};
    std::uint64_t malformed_midi_messages{};
    std::uint64_t midi_events_dropped{};
    std::uint64_t duplicate_button_edges{};
    std::uint64_t non_finite_clears{};
    std::uint64_t reset_count{};
    std::uint64_t panic_count{};
    std::uint64_t unsupported_process_calls{};
};

struct ProcessReport {
    std::size_t events_written{};
    std::size_t events_dropped{};
};

struct StateSnapshot {
    std::array<float, 4> stage_values{};
    std::array<float, 4> ledger_energy{};
    std::array<std::uint8_t, 4> rotor_positions{};
    std::uint64_t absolute_sample{};
    std::size_t grain_write_index{};
    std::uint32_t stage_transition_index{};
    std::uint32_t pulse_counter{};
    double cycle_phase{};
    double rate_hz{};
    double fx_a{};
    double fx_b{};
    double parent_frequency_hz{};
    double undertow_frequency_hz{};
    double undertow_resonator_frequency_hz{};
    std::int32_t root_note{};
    std::uint8_t undertow_divisor{};
    std::uint8_t pulse_divide{};
    SourceMode source{SourceMode::reed};
    ScaleMode scale{ScaleMode::minor_pentatonic};
    FxMode fx_mode{FxMode::clean};
    WaveTarget wave_target{WaveTarget::pitch};
    bool locked{};
    bool frozen{};
    bool fx_a_pickup_armed{};
    bool fx_b_pickup_armed{};
    bool bloom_armed{};
    bool panic_latched{};
};

class Core final {
public:
    Core();
    ~Core();

    Core(const Core&) = delete;
    Core& operator=(const Core&) = delete;
    Core(Core&&) noexcept;
    Core& operator=(Core&&) noexcept;

    bool prepare(double sample_rate, std::uint32_t maximum_block_frames = kMaximumBlockFrames) noexcept;
    void reset() noexcept;

    ProcessReport process(
        float* output_left,
        float* output_right,
        std::uint32_t frames,
        const MidiEvent* midi_events = nullptr,
        std::size_t midi_event_count = 0,
        WakeEvent* event_output = nullptr,
        std::size_t event_capacity = 0
    ) noexcept;
    // The caller supplies events ordered by sample_offset, with strictly
    // increasing ingress_sequence values for equal offsets. On an unsupported
    // call the Core records a diagnostic and does not touch output buffers;
    // host adapters must clear their outputs before invoking it.

    // This shares the MIDI mapping path without pretending that a UI/control
    // call is a physical-controller observation.
    bool setControlNormalized(ControlId control, double normalized) noexcept;
    void noteDroppedMidiEvents(std::size_t count) noexcept;

    [[nodiscard]] Diagnostics diagnostics() const noexcept;
    [[nodiscard]] StateSnapshot snapshot() const noexcept;
    [[nodiscard]] double sampleRate() const noexcept;
    [[nodiscard]] bool isPrepared() const noexcept;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

}  // namespace cinderwheel
