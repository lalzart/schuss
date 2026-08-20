#include "instrument_lab_smoke/smoke_adapter.hpp"

#include <algorithm>

namespace instrument_lab_smoke {

void Adapter::reset() noexcept {
    accepted_value_ = 0.0;
    accepted_events_ = 0;
    ++resets_;
}

bool Adapter::accept(const schuss::instrument_lab::RawMidiEnvelope& event) noexcept {
    if (event.size != 3 || event.bytes[0] != 0xb0 || event.bytes[1] != 1
        || event.bytes[2] > 127) return false;
    accepted_value_ = static_cast<double>(event.bytes[2]) / 127.0;
    ++accepted_events_;
    return true;
}

void Adapter::process(float* left, float* right, std::uint32_t frames) noexcept {
    if (left == nullptr || right == nullptr || frames > 64) return;
    std::fill_n(left, frames, static_cast<float>(accepted_value_));
    std::fill_n(right, frames, static_cast<float>(-accepted_value_));
}

Snapshot Adapter::snapshot() const noexcept {
    return {accepted_value_, accepted_events_, resets_};
}

}  // namespace instrument_lab_smoke
