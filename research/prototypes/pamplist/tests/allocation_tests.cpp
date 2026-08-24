#include "schuss/pamplist/core.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdlib>
#include <iostream>
#include <new>

namespace {

std::atomic<bool> count_allocations{false};
std::atomic<std::size_t> allocation_count{0U};

}  // namespace

void* operator new(std::size_t size) {
    if (count_allocations.load(std::memory_order_relaxed)) {
        allocation_count.fetch_add(1U, std::memory_order_relaxed);
    }
    if (void* memory = std::malloc(size)) return memory;
    throw std::bad_alloc();
}

void* operator new[](std::size_t size) {
    return ::operator new(size);
}

void operator delete(void* memory) noexcept { std::free(memory); }
void operator delete[](void* memory) noexcept { std::free(memory); }
void operator delete(void* memory, std::size_t) noexcept { std::free(memory); }
void operator delete[](void* memory, std::size_t) noexcept { std::free(memory); }

int main() {
    schuss::pamplist::Core core;
    auto controls = schuss::pamplist::defaultControls();
    std::array<std::int32_t, schuss::pamplist::kMaximumHostBlockFrames> main{};
    std::array<std::int32_t, schuss::pamplist::kMaximumHostBlockFrames> auxiliary{};
    count_allocations.store(true, std::memory_order_relaxed);
    for (int iteration = 0; iteration < 512; ++iteration) {
        const auto frames = static_cast<std::size_t>(1 + iteration % 512);
        if (!core.process(controls, main.data(), auxiliary.data(), frames)) return 1;
    }
    count_allocations.store(false, std::memory_order_relaxed);
    if (allocation_count.load(std::memory_order_relaxed) != 0U) {
        std::cerr << "pamplist_allocation_tests: process allocated "
                  << allocation_count.load(std::memory_order_relaxed) << " times\n";
        return 1;
    }
    std::cout << "pamplist_allocation_tests: pass\n";
    return 0;
}
