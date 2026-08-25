#include "tidepit/vst3_processor.hpp"

#include <juce_audio_basics/juce_audio_basics.h>

#include <atomic>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <new>

namespace {

std::atomic<bool> count_allocations{false};
std::atomic<std::size_t> allocation_count{0U};

void setPhysical(
    tidepit::Vst3ProgramState& program,
    std::size_t index,
    float physical) {
    const auto& descriptor = tidepit::vst3ParameterDescriptors()[index];
    program.normalized[index] = tidepit::vst3NormalizePhysical(
        descriptor, physical);
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
        tidepit::Vst3Processor processor;
        auto program = tidepit::defaultVst3ProgramState();
        setPhysical(program, 0U, 0.73F);
        setPhysical(program, 1U, 0.17F);
        setPhysical(program, 2U, 0.91F);
        setPhysical(program, 3U, 0.42F);
        setPhysical(program, tidepit::kVst3RateIndex, 0.82F);
        setPhysical(program, tidepit::kVst3MemoryIndex, 0.66F);
        setPhysical(program, tidepit::kVst3MaterialIndex, 0.27F);
        setPhysical(program, tidepit::kVst3PositionIndex, 0.84F);
        setPhysical(program, tidepit::kVst3FxAIndex, 0.14F);
        setPhysical(program, tidepit::kVst3FxBIndex, 0.88F);
        setPhysical(program, tidepit::kVst3RootIndex, 67.0F);
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
        std::cerr << "tide_pit_vst3_allocation_tests: process allocated "
                  << allocations << " times\n";
        return 1;
    }
    std::cout << "tide_pit_vst3_allocation_tests: PASS\n";
    return 0;
}
