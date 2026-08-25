#include "schuss/pamplist/vst3_processor.hpp"

#include <juce_audio_basics/juce_audio_basics.h>

#include <atomic>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <new>
#include <string_view>

namespace pam = schuss::pamplist;

namespace {

std::atomic<bool> count_allocations{false};
std::atomic<std::size_t> allocation_count{0U};

void setPhysical(
    pam::Vst3ProgramState& program,
    std::string_view id,
    float physical) {
    const auto index = pam::vst3ParameterIndexForId(id);
    if (!index.has_value()) std::abort();
    const auto& descriptor = pam::vst3ParameterDescriptors()[*index];
    program.normalized[*index] = pam::vst3NormalizePhysical(descriptor, physical);
}

}  // namespace

void* operator new(std::size_t size) {
    if (count_allocations.load(std::memory_order_relaxed)) {
        allocation_count.fetch_add(1U, std::memory_order_relaxed);
    }
    if (void* memory = std::malloc(size)) return memory;
    throw std::bad_alloc();
}

void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }

int main() {
    for (const double sample_rate : {48000.0, 44100.0, 96000.0}) {
        pam::Vst3Processor processor;
        auto program = pam::defaultVst3ProgramState();
        setPhysical(program, "pamp.lane1.hits", 16.0F);
        setPhysical(program, "pamp.lane1.chance", 1.0F);
        setPhysical(program, "pamp.lane1.depth", 1.0F);
        setPhysical(program, "pamp.lane1.motion.trigger", 1.0F);
        setPhysical(program, "pamp.lane1.voice.model", 21.0F);
        setPhysical(program, "pamp.lane1.voice.level", 0.2F);
        setPhysical(program, "pamp.run", 1.0F);
        if (!processor.applyProgramState(program)) return 1;
        processor.prepareToPlay(sample_rate, 4096);

        juce::AudioBuffer<float> buffer{2, 4096};
        juce::MidiBuffer midi;
        midi.ensureSize(1024U);
        buffer.clear();
        processor.processBlock(buffer, midi);

        for (int iteration = 0; iteration < 256; ++iteration) {
            midi.addEvent(
                juce::MidiMessage::controllerEvent(16, 29, iteration % 128),
                137);
            midi.addEvent(
                juce::MidiMessage::controllerEvent(
                    16, 20, (iteration + 1) % 128),
                2049);
            count_allocations.store(true, std::memory_order_relaxed);
            processor.processBlock(buffer, midi);
            count_allocations.store(false, std::memory_order_relaxed);
            if (!midi.isEmpty() || processor.processFailureCount() != 0U) {
                return 1;
            }
        }
    }

    const auto allocations = allocation_count.load(std::memory_order_relaxed);
    if (allocations != 0U) {
        std::cerr << "pamplist_vst3_allocation_tests: process allocated "
                  << allocations << " times\n";
        return 1;
    }
    std::cout << "pamplist_vst3_allocation_tests: PASS\n";
    return 0;
}
