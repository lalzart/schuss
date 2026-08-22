#include "schuss/dsp/mutable_braids_v1.hpp"

#include "braids/macro_oscillator.h"
#include "braids/settings.h"
#include "stmlib/utils/random.h"

#include <cstring>
#include <new>
#include <stdexcept>

namespace schuss::dsp::mutable_braids_v1 {
namespace {

[[nodiscard]] braids::MacroOscillator* oscillator(void* storage) noexcept {
    return std::launder(reinterpret_cast<braids::MacroOscillator*>(storage));
}

[[nodiscard]] braids::MacroOscillatorShape shape(Model model) {
    switch (model) {
        case Model::kick:
            return braids::MACRO_OSC_SHAPE_KICK;
        case Model::snare:
            return braids::MACRO_OSC_SHAPE_SNARE;
        case Model::cymbal:
            return braids::MACRO_OSC_SHAPE_CYMBAL;
        case Model::sine_triangle:
            return braids::MACRO_OSC_SHAPE_SINE_TRIANGLE;
        case Model::fm:
            return braids::MACRO_OSC_SHAPE_FM;
        case Model::filtered_noise:
            return braids::MACRO_OSC_SHAPE_FILTERED_NOISE;
    }
    throw std::logic_error("unknown Braids model");
}

}  // namespace

static_assert(sizeof(braids::MacroOscillator) <= 18U * 1024U);
static_assert(alignof(braids::MacroOscillator) <= 16U);

Voice::Voice() { reconstruct(); }

Voice::~Voice() {
    if (constructed_) {
        oscillator(storage_.data())->~MacroOscillator();
    }
}

void Voice::reconstruct() {
    if (constructed_) {
        oscillator(storage_.data())->~MacroOscillator();
    }
    std::memset(storage_.data(), 0, storage_.size());
    new (storage_.data()) braids::MacroOscillator();
    constructed_ = true;
    oscillator(storage_.data())->Init();
}

void Voice::reset() { reconstruct(); }

void Voice::reset(Model model, std::int16_t pitch, std::int16_t timbre, std::int16_t color) {
    reconstruct();
    setModel(model);
    setPitch(pitch);
    setParameters(timbre, color);
}

void Voice::setModel(Model model) {
    oscillator(storage_.data())->set_shape(shape(model));
}

void Voice::setPitch(std::int16_t pitch) {
    oscillator(storage_.data())->set_pitch(pitch);
}

void Voice::setParameters(std::int16_t timbre, std::int16_t color) {
    oscillator(storage_.data())->set_parameters(timbre, color);
}

void Voice::strike() { oscillator(storage_.data())->Strike(); }

void Voice::render(std::uint8_t* sync, std::int16_t* output, std::size_t size) {
    oscillator(storage_.data())->Render(sync, output, size);
}

void seedRandom(std::uint32_t seed) noexcept { stmlib::Random::Seed(seed); }

}  // namespace schuss::dsp::mutable_braids_v1
