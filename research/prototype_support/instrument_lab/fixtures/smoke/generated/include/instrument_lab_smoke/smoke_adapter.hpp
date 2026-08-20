#pragma once

#include "schuss/instrument_lab/bounded_midi.hpp"
#include "schuss/instrument_lab/host_bridge.hpp"

#include <array>
#include <cstdint>

namespace instrument_lab_smoke {

struct Snapshot {
    double accepted_value{};
    std::uint64_t accepted_events{};
    std::uint64_t resets{};
};

class Adapter final {
public:
    static constexpr schuss::instrument_lab::HostProfile profile() noexcept {
        return {schuss::instrument_lab::SampleRepresentation::float32,
                48000.0, 64, 0,
                false, true};
    }

    void reset() noexcept;
    bool accept(const schuss::instrument_lab::RawMidiEnvelope& event) noexcept;
    void process(float* left, float* right, std::uint32_t frames) noexcept;
    [[nodiscard]] Snapshot snapshot() const noexcept;

private:
    double accepted_value_{};
    std::uint64_t accepted_events_{};
    std::uint64_t resets_{};
};

using Host = schuss::instrument_lab::HostBridge<Adapter>;

}  // namespace instrument_lab_smoke
