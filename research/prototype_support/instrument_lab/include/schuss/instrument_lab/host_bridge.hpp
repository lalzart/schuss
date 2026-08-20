#pragma once

#include <algorithm>
#include <cstdint>
#include <utility>

namespace schuss::instrument_lab {

enum class SampleRepresentation : std::uint8_t {
    float32,
    q27,
};

struct HostProfile {
    SampleRepresentation sample_representation{SampleRepresentation::float32};
    double sample_rate{};
    std::uint32_t maximum_host_block{};
    std::uint32_t internal_quantum{};
    bool adapter_owns_conversion{};
    bool clears_output_before_process{};
};

template <typename Adapter>
class HostBridge final {
public:
    [[nodiscard]] static constexpr HostProfile profile() noexcept {
        return Adapter::profile();
    }

    void reset() noexcept { adapter_.reset(); }

    template <typename... Arguments>
    decltype(auto) process(Arguments&&... arguments) noexcept(
        noexcept(adapter_.process(std::forward<Arguments>(arguments)...))) {
        return adapter_.process(std::forward<Arguments>(arguments)...);
    }

    [[nodiscard]] Adapter& adapter() noexcept { return adapter_; }
    [[nodiscard]] const Adapter& adapter() const noexcept { return adapter_; }

private:
    Adapter adapter_{};
};

inline void clearStereoOutputs(
    float* const* outputs,
    int output_channel_count,
    int frames
) noexcept {
    if (outputs == nullptr || frames <= 0) return;
    for (int channel = 0; channel < output_channel_count; ++channel) {
        if (outputs[channel] != nullptr) {
            std::fill_n(outputs[channel], frames, 0.0f);
        }
    }
}

}  // namespace schuss::instrument_lab
