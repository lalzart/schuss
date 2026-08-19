#include "schuss_rt/runtime.hpp"
#include "schuss_rt/sha256.hpp"

#include <atomic>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <new>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
std::atomic<bool> allocation_guard{false};
std::atomic<std::uint64_t> guarded_allocations{0};
}

void* operator new(std::size_t size) {
    if (allocation_guard.load(std::memory_order_relaxed)) guarded_allocations.fetch_add(1, std::memory_order_relaxed);
    if (void* value = std::malloc(size)) return value;
    throw std::bad_alloc();
}

void operator delete(void* value) noexcept { std::free(value); }
void operator delete(void* value, std::size_t) noexcept { std::free(value); }

namespace {

using schuss::rt::ErrorCode;
using schuss::rt::Event;
using schuss::rt::EventKind;
using schuss::rt::PreparedPackage;
using schuss::rt::Runtime;

void expect(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

std::string fixture() {
    std::ifstream stream(SCHUSS_RT_FIXTURE_PATH, std::ios::binary);
    if (!stream) throw std::runtime_error("cannot open Task 031 package fixture");
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

std::string content_hash(const std::string& json) {
    const std::string marker = "\"content_hash\":\"";
    std::size_t begin = 0;
    while ((begin = json.find(marker, begin)) != std::string::npos) {
        const auto value_begin = begin + marker.size();
        const auto end = json.find('"', value_begin);
        if (json.compare(end + 1, 24, ",\"control_period_frames\"") == 0) {
            return json.substr(value_begin, end - value_begin);
        }
        begin = end + 1;
    }
    throw std::runtime_error("fixture root content hash missing");
}

std::string replaced(std::string value, const std::string& before, const std::string& after) {
    const auto position = value.find(before);
    if (position == std::string::npos) throw std::runtime_error("test mutation source missing");
    value.replace(position, before.size(), after);
    return value;
}

std::string rehashed(std::string value) {
    const std::string marker = "\"content_hash\":\"";
    std::size_t begin = 0;
    std::size_t root_begin = std::string::npos;
    std::size_t value_begin = 0;
    std::size_t value_end = 0;
    while ((begin = value.find(marker, begin)) != std::string::npos) {
        const auto candidate_begin = begin + marker.size();
        const auto candidate_end = value.find('"', candidate_begin);
        if (value.compare(candidate_end + 1U, 24, ",\"control_period_frames\"") == 0) {
            root_begin = begin;
            value_begin = candidate_begin;
            value_end = candidate_end;
            break;
        }
        begin = candidate_end + 1U;
    }
    if (root_begin == std::string::npos) throw std::runtime_error("root package hash missing");
    std::string digest_input = value;
    digest_input.erase(root_begin, value_end - root_begin + 2U);
    if (!digest_input.empty() && digest_input.back() == '\n') digest_input.pop_back();
    value.replace(value_begin, value_end - value_begin, "sha256:" + schuss::rt::sha256_hex(digest_input));
    return value;
}

PreparedPackage parse(const std::string& json) {
    PreparedPackage package;
    const auto result = schuss::rt::parse_package(json, content_hash(json), package);
    expect(static_cast<bool>(result), result.diagnostic.c_str());
    return package;
}

std::vector<std::int32_t> render(Runtime& runtime, std::uint32_t frames, std::uint32_t block) {
    std::vector<std::int32_t> result(static_cast<std::size_t>(frames) * 2U);
    std::vector<std::int32_t> left(block);
    std::vector<std::int32_t> right(block);
    std::uint32_t cursor = 0;
    while (cursor < frames) {
        const auto count = std::min(block, frames - cursor);
        const auto status = runtime.process(left.data(), right.data(), count);
        expect(static_cast<bool>(status), status.diagnostic.c_str());
        for (std::uint32_t index = 0; index < count; ++index) {
            result[static_cast<std::size_t>(cursor + index) * 2U] = left[index];
            result[static_cast<std::size_t>(cursor + index) * 2U + 1U] = right[index];
        }
        cursor += count;
    }
    return result;
}

void parser_negative_tests(const std::string& valid) {
    PreparedPackage package;
    expect(schuss::rt::parse_package("{", "", package).code == ErrorCode::json_invalid, "malformed JSON accepted");
    expect(
        schuss::rt::parse_package(rehashed(replaced(valid, "schuss-rt-abi-v0", "schuss-rt-abi-v9")), "", package).code == ErrorCode::runtime_abi_mismatch,
        "ABI mismatch accepted"
    );
    expect(schuss::rt::parse_package(valid, "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", package).code == ErrorCode::package_hash_mismatch, "hash mismatch accepted");
    expect(
        schuss::rt::parse_package(replaced(valid, "schuss.rt.saw-q27-v0", "schuss.rt.unknown-q27-v0"), "", package).code == ErrorCode::package_hash_mismatch,
        "tampered package content hash accepted"
    );
    expect(
        schuss::rt::parse_package(rehashed(replaced(valid, "schuss.rt.saw-q27-v0", "schuss.rt.unknown-q27-v0")), "", package).code == ErrorCode::unknown_factory,
        "unknown factory accepted"
    );
    expect(
        schuss::rt::parse_package(
            rehashed(replaced(valid, "schuss-compute-target-000002", "schuss-compute-target-999999")),
            "",
            package
        ).code == ErrorCode::package_shape_invalid,
        "unknown target reference accepted"
    );
    expect(
        schuss::rt::parse_package(
            rehashed(replaced(valid, "schuss-implementation-000162", "schuss-implementation-999999")),
            "",
            package
        ).code == ErrorCode::package_shape_invalid,
        "unknown binding reference accepted"
    );
    expect(
        schuss::rt::parse_package(
            rehashed(replaced(valid, "component-parameter-000001", "component-parameter-999999")),
            "",
            package
        ).code == ErrorCode::port_contract_invalid,
        "unknown parameter facet accepted"
    );
    expect(
        schuss::rt::parse_package(
            rehashed(replaced(valid, "\"value_q\":-50331648", "\"value_q\":0.5")),
            "",
            package
        ).code == ErrorCode::json_invalid,
        "non-integer parameter accepted"
    );
    expect(
        schuss::rt::parse_package(
            rehashed(replaced(
                valid,
                "\"input_buffers\":[],\"node_id\":\"graph-node-000001\"",
                "\"input_buffers\":[],\"node_id\":\"graph-node-999999\""
            )),
            "",
            package
        ).code == ErrorCode::unknown_node,
        "unknown node ID accepted"
    );
    expect(
        schuss::rt::parse_package(rehashed(replaced(valid, "\"buffer_index\":0", "\"buffer_index\":31")), "", package).code == ErrorCode::port_contract_invalid,
        "connection buffer mismatch accepted"
    );
    expect(
        schuss::rt::parse_package(rehashed(replaced(valid, "\"state_bytes\":48", "\"state_bytes\":40")), "", package).code == ErrorCode::state_plan_invalid,
        "state overrun accepted"
    );
    expect(
        schuss::rt::parse_package(rehashed(replaced(valid, "\"facet_id\":\"component-port-000002\",\"node_id\":\"graph-node-000001\"", "\"facet_id\":\"component-port-000002\",\"node_id\":\"graph-node-000008\"")), "", package).code == ErrorCode::cycle_detected,
        "cycle/back-edge accepted"
    );
}

void runtime_tests(const PreparedPackage& package) {
    Runtime unprepared;
    std::int32_t left[1]{};
    std::int32_t right[1]{};
    expect(unprepared.process(left, right, 1).code == ErrorCode::not_prepared, "unprepared runtime executed");

    Runtime runtime;
    expect(static_cast<bool>(runtime.prepare(package)), "runtime prepare failed");
    expect(runtime.process(left, right, 513).code == ErrorCode::block_too_large, "oversized block executed");

    const auto first = render(runtime, 1031, 127);
    expect(runtime.metrics().processed_frames == 1031, "processed frame metric mismatch");
    expect(std::any_of(first.begin(), first.end(), [](std::int32_t value) { return value != 0; }), "render is silent");
    runtime.reset();
    const auto second = render(runtime, 1031, 127);
    expect(first == second, "reset render is nondeterministic");

    runtime.reset();
    Event later{};
    later.frame_offset = 17;
    later.sequence = 2;
    later.kind = EventKind::parameter_q27;
    later.node_index = 4;
    later.parameter_index = 0;
    later.value_q = 0;
    Event earlier = later;
    earlier.frame_offset = 7;
    earlier.sequence = 1;
    earlier.value_q = 1 << 27;
    expect(runtime.enqueue(later) && runtime.enqueue(earlier), "event enqueue failed");
    std::vector<std::int32_t> event_left(64), event_right(64);
    expect(static_cast<bool>(runtime.process(event_left.data(), event_right.data(), 64)), "event render failed");
    expect(runtime.metrics().events_delivered == 2, "event delivery metric mismatch");

    runtime.reset();
    Event malformed{};
    malformed.node_index = static_cast<std::uint8_t>(package.nodes.size());
    expect(!runtime.enqueue(malformed), "unknown event node accepted");
    malformed = {};
    malformed.parameter_index = package.nodes[0].parameter_count;
    expect(!runtime.enqueue(malformed), "unknown event parameter accepted");
    malformed = {};
    malformed.frame_offset = schuss::rt::kMaximumBlockFrames;
    expect(!runtime.enqueue(malformed), "out-of-range event offset accepted");
    malformed = {};
    malformed.kind = EventKind::midi_message;
    expect(!runtime.enqueue(malformed), "empty MIDI event accepted");
    malformed.midi_size = 4;
    expect(!runtime.enqueue(malformed), "oversized MIDI event accepted");
    malformed = {};
    malformed.kind = static_cast<EventKind>(255);
    expect(!runtime.enqueue(malformed), "unknown event kind accepted");
    expect(runtime.metrics().events_delivered == 0, "malformed event partially activated");

    for (std::uint32_t index = 0; index < package.event_capacity; ++index) {
        Event event{};
        event.sequence = index;
        expect(runtime.enqueue(event), "queue rejected within declared capacity");
    }
    Event overflow{};
    expect(!runtime.enqueue(overflow), "queue overflow was not rejected");
    expect(runtime.metrics().queue_overflows == 1, "queue overflow metric mismatch");

    runtime.reset();
    std::vector<std::int32_t> guarded_left(512), guarded_right(512);
    guarded_allocations.store(0, std::memory_order_relaxed);
    allocation_guard.store(true, std::memory_order_relaxed);
    const auto guarded_result = runtime.process(guarded_left.data(), guarded_right.data(), 512);
    allocation_guard.store(false, std::memory_order_relaxed);
    expect(static_cast<bool>(guarded_result), "guarded process failed");
    expect(guarded_allocations.load(std::memory_order_relaxed) == 0, "process path allocated memory");
}

}  // namespace

int main() {
    try {
        expect(
            schuss::rt::sha256_hex("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "empty SHA-256 vector mismatch"
        );
        expect(
            schuss::rt::sha256_hex("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            "SHA-256 vector mismatch"
        );
        const std::string json = fixture();
        parser_negative_tests(json);
        runtime_tests(parse(json));
        std::cout << "schuss_rt_tests: passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "schuss_rt_tests: " << error.what() << '\n';
        return 1;
    }
}
