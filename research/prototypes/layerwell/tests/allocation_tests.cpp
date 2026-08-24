#include "layerwell/core.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <new>

namespace {

std::atomic<bool> count_allocations{false};
std::atomic<std::size_t> allocation_count{0U};

void account() noexcept {
    if (count_allocations.load(std::memory_order_relaxed)) {
        allocation_count.fetch_add(1U, std::memory_order_relaxed);
    }
}

void* allocate(std::size_t size) {
    account();
    if (void* memory = std::malloc(size)) return memory;
    throw std::bad_alloc{};
}

}  // namespace

void* operator new(std::size_t size) { return allocate(size); }
void* operator new[](std::size_t size) { return allocate(size); }
void operator delete(void* pointer) noexcept { std::free(pointer); }
void operator delete[](void* pointer) noexcept { std::free(pointer); }
void operator delete(void* pointer, std::size_t) noexcept { std::free(pointer); }
void operator delete[](void* pointer, std::size_t) noexcept { std::free(pointer); }

int main() {
    layerwell::Core core;
    if (!core.prepare()) {
        std::cerr << "Core preparation failed\n";
        return 1;
    }

    std::array<float, layerwell::kMaximumBlockFrames> left{};
    std::array<float, layerwell::kMaximumBlockFrames> right{};
    const layerwell::Event start{
        0U, 1U, layerwell::EventKind::capture_press, 0U, 0.0};
    core.process(left.data(), right.data(), 128U, &start, 1U);

    std::array<layerwell::Event, 2> events{{
        {0U, 2U, layerwell::EventKind::adjust_layer_pan, 0U, 65.0},
        {64U, 3U, layerwell::EventKind::set_master_level, 0U, 0.6},
    }};
    allocation_count.store(0U, std::memory_order_relaxed);
    count_allocations.store(true, std::memory_order_release);
    for (int iteration = 0; iteration < 100; ++iteration) {
        core.process(
            left.data(), right.data(), 128U,
            events.data(), events.size());
        events[0].ingress_sequence += 2U;
        events[1].ingress_sequence += 2U;
    }
    count_allocations.store(false, std::memory_order_release);

    const auto observed = allocation_count.load(std::memory_order_acquire);
    if (observed != 0U) {
        std::cerr << "process() allocations observed: " << observed << '\n';
        return 1;
    }
    std::cout << "Layerwell process allocation test passed\n";
    return 0;
}
