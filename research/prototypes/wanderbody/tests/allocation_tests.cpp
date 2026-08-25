#include "wanderbody/core.hpp"

#include <atomic>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <new>

namespace {

std::atomic<bool> count_allocations{false};
std::atomic<std::size_t> allocation_count{0U};

void* allocate(std::size_t size) {
    if (count_allocations.load(std::memory_order_relaxed)) {
        allocation_count.fetch_add(1U, std::memory_order_relaxed);
    }
    if (void* value = std::malloc(size)) return value;
    throw std::bad_alloc{};
}

}  // namespace

void* operator new(std::size_t size) { return allocate(size); }
void* operator new[](std::size_t size) { return allocate(size); }
void operator delete(void* value) noexcept { std::free(value); }
void operator delete[](void* value) noexcept { std::free(value); }
void operator delete(void* value, std::size_t) noexcept { std::free(value); }
void operator delete[](void* value, std::size_t) noexcept { std::free(value); }

int main() {
    wanderbody::Core core{};
    if (!core.prepare(48000.0, 512U)) return EXIT_FAILURE;
    const auto controls = wanderbody::defaultControls();
    wanderbody::ActionSequences actions{};
    float input_left[512]{};
    float input_right[512]{};
    float output_left[512]{};
    float output_right[512]{};
    for (std::size_t index = 0U; index < 512U; ++index) {
        input_left[index] = index == 0U ? 0.5F : 0.1F;
        input_right[index] = input_left[index];
    }
    for (int warmup = 0; warmup < 200; ++warmup) {
        static_cast<void>(core.process(
            controls, actions, input_left, input_right,
            output_left, output_right, 512U));
    }
    allocation_count.store(0U, std::memory_order_relaxed);
    count_allocations.store(true, std::memory_order_release);
    for (int iteration = 0; iteration < 500; ++iteration) {
        static_cast<void>(core.process(
            controls, actions, input_left, input_right,
            output_left, output_right, 512U));
    }
    count_allocations.store(false, std::memory_order_release);
    const auto observed = allocation_count.load(std::memory_order_acquire);
    if (observed != 0U) {
        std::cerr << "Wanderbody process allocations observed: " << observed << '\n';
        return EXIT_FAILURE;
    }
    std::cout << "Wanderbody process allocation test passed\n";
    return EXIT_SUCCESS;
}
