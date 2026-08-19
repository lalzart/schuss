#include "schuss_rt/runtime_replacement.hpp"

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <memory>
#include <new>
#include <stdexcept>
#include <string>
#include <thread>

namespace {
std::atomic<bool> allocation_guard{false};
std::atomic<std::uint64_t> guarded_allocations{0};
}

void* operator new(std::size_t size) {
    if (allocation_guard.load(std::memory_order_relaxed)) {
        guarded_allocations.fetch_add(1, std::memory_order_relaxed);
    }
    if (void* value = std::malloc(size)) return value;
    throw std::bad_alloc();
}

void operator delete(void* value) noexcept { std::free(value); }
void operator delete(void* value, std::size_t) noexcept { std::free(value); }

namespace {

void expect(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

std::string fixture(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("replacement fixture unavailable");
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

std::string content_hash(const std::string& json) {
    const std::string marker = "\"content_hash\":\"";
    std::size_t begin = 0;
    while ((begin = json.find(marker, begin)) != std::string::npos) {
        const auto value_begin = begin + marker.size();
        const auto end = json.find('"', value_begin);
        if (json.compare(end + 1U, 24, ",\"control_period_frames\"") == 0) {
            return json.substr(value_begin, end - value_begin);
        }
        begin = end + 1U;
    }
    throw std::runtime_error("root hash unavailable");
}

std::unique_ptr<schuss::rt::v1::Runtime> runtime(const char* path) {
    const std::string json = fixture(path);
    schuss::rt::v1::PreparedPackage package;
    const auto parsed = schuss::rt::v1::parse_package(
        json, content_hash(json), package
    );
    expect(static_cast<bool>(parsed), parsed.diagnostic.c_str());
    auto result = std::make_unique<schuss::rt::v1::Runtime>();
    const auto prepared = result->prepare(package);
    expect(static_cast<bool>(prepared), prepared.diagnostic.c_str());
    return result;
}

}  // namespace

int main() {
    try {
        const std::string smaller_hash = content_hash(fixture(SMALLER_PACKAGE));
        const std::string larger_hash = content_hash(fixture(LARGER_PACKAGE));
        schuss::rt::v1::RuntimeReplacementSlot slot;
        expect(slot.install_initial(runtime(SMALLER_PACKAGE), smaller_hash), "initial install failed");
        auto* original = slot.active();
        expect(original != nullptr && slot.generation() == 1, "initial identity invalid");

        expect(
            !slot.prepare_successor(runtime(LARGER_PACKAGE), larger_hash, 2, smaller_hash),
            "stale generation prepared"
        );
        expect(slot.active() == original && !slot.has_pending(), "stale prepare changed active runtime");
        expect(
            !slot.prepare_successor(runtime(LARGER_PACKAGE), larger_hash, 1, larger_hash),
            "stale hash prepared"
        );
        expect(slot.active() == original && !slot.has_pending(), "stale hash changed active runtime");

        expect(
            slot.prepare_successor(runtime(LARGER_PACKAGE), larger_hash, 1, smaller_hash),
            "valid successor prepare failed"
        );
        expect(
            !slot.prepare_successor(runtime(LARGER_PACKAGE), larger_hash, 1, smaller_hash),
            "concurrent successor prepare accepted"
        );
        expect(
            slot.request_activation(1, smaller_hash, larger_hash),
            "activation request failed"
        );
        guarded_allocations.store(0, std::memory_order_relaxed);
        allocation_guard.store(true, std::memory_order_relaxed);
        auto* successor = slot.begin_block();
        allocation_guard.store(false, std::memory_order_relaxed);
        expect(successor != nullptr && successor != original, "callback did not exchange runtime");
        expect(guarded_allocations.load(std::memory_order_relaxed) == 0, "callback exchange allocated");
        expect(slot.generation() == 2 && slot.activation_observed(), "activation was not acknowledged");
        schuss::rt::v1::ReplacementTelemetry telemetry;
        expect(slot.complete_activation(telemetry), "off-thread completion failed");
        expect(telemetry.old_package_content_hash == smaller_hash, "old hash missing");
        expect(telemetry.new_package_content_hash == larger_hash, "new hash missing");
        expect(telemetry.activation_generation == 2, "activation generation mismatch");
        expect(slot.active_hash() == larger_hash && !slot.has_pending(), "successor not active");

        expect(
            slot.prepare_successor(runtime(SMALLER_PACKAGE), smaller_hash, 2, larger_hash),
            "cancel fixture prepare failed"
        );
        expect(slot.request_activation(2, larger_hash, smaller_hash), "cancel activation request failed");
        expect(slot.cancel_pending(), "pending activation cancellation failed");
        expect(slot.active_hash() == larger_hash && slot.generation() == 2, "cancellation changed active runtime");

        std::atomic<bool> callback_running{true};
        std::thread callback([&slot, &callback_running] {
            while (callback_running.load(std::memory_order_acquire)) {
                static_cast<void>(slot.begin_block());
                std::this_thread::yield();
            }
        });
        bool active_is_larger = true;
        for (std::uint64_t iteration = 0; iteration < 64; ++iteration) {
            const char* successor_path = active_is_larger
                ? SMALLER_PACKAGE
                : LARGER_PACKAGE;
            const std::string& successor_hash = active_is_larger
                ? smaller_hash
                : larger_hash;
            const std::string& active_hash = active_is_larger
                ? larger_hash
                : smaller_hash;
            const auto generation = 2U + iteration;
            expect(
                slot.prepare_successor(
                    runtime(successor_path), successor_hash, generation, active_hash
                ),
                "stress successor prepare failed"
            );
            expect(
                slot.request_activation(generation, active_hash, successor_hash),
                "stress activation request failed"
            );
            const auto deadline = std::chrono::steady_clock::now()
                + std::chrono::seconds(2);
            while (!slot.activation_observed()
                && std::chrono::steady_clock::now() < deadline) {
                std::this_thread::yield();
            }
            expect(slot.activation_observed(), "stress callback activation timed out");
            schuss::rt::v1::ReplacementTelemetry stress_telemetry;
            expect(
                slot.complete_activation(stress_telemetry),
                "stress activation completion failed"
            );
            expect(
                stress_telemetry.activation_generation == generation + 1U,
                "stress activation generation mismatch"
            );
            active_is_larger = !active_is_larger;
        }
        callback_running.store(false, std::memory_order_release);
        callback.join();

        slot.clear_after_callback_stopped();
        expect(slot.active() == nullptr && slot.generation() == 0, "slot clear failed");
        std::cout << "runtime_replacement_tests: passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "runtime_replacement_tests: " << error.what() << '\n';
        return 1;
    }
}
