#include "schuss_rt/runtime_v1.hpp"
#include "schuss_rt/sha256.hpp"

#include <algorithm>
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
    if (allocation_guard.load(std::memory_order_relaxed)) {
        guarded_allocations.fetch_add(1, std::memory_order_relaxed);
    }
    if (void* value = std::malloc(size)) return value;
    throw std::bad_alloc();
}

void operator delete(void* value) noexcept { std::free(value); }
void operator delete(void* value, std::size_t) noexcept { std::free(value); }

namespace {

using schuss::rt::ErrorCode;
using schuss::rt::Event;
using schuss::rt::EventKind;
using schuss::rt::v1::PreparedPackage;
using schuss::rt::v1::Runtime;

void expect(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

std::string read_fixture(const char* path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("cannot open Task 032 package fixture");
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
    throw std::runtime_error("fixture root content hash missing");
}

std::string replaced(
    std::string value, const std::string& before, const std::string& after
) {
    const auto position = value.find(before);
    if (position == std::string::npos) {
        throw std::runtime_error("test mutation source missing");
    }
    value.replace(position, before.size(), after);
    return value;
}

std::string rehashed(std::string value) {
    const std::string embedded = content_hash(value);
    const std::string marker = "\"content_hash\":\"" + embedded + "\",";
    const auto position = value.find(marker);
    if (position == std::string::npos) throw std::runtime_error("root hash missing");
    std::string digest_input = value;
    digest_input.erase(position, marker.size());
    if (!digest_input.empty() && digest_input.back() == '\n') digest_input.pop_back();
    value.replace(
        position + std::string("\"content_hash\":\"").size(),
        embedded.size(),
        "sha256:" + schuss::rt::sha256_hex(digest_input)
    );
    return value;
}

PreparedPackage parse(const std::string& json) {
    PreparedPackage package;
    const auto result = schuss::rt::v1::parse_package(
        json, content_hash(json), package
    );
    expect(static_cast<bool>(result), result.diagnostic.c_str());
    return package;
}

std::vector<std::int32_t> render(
    const PreparedPackage& package, std::uint32_t frames, std::uint32_t block
) {
    Runtime runtime;
    const auto prepared = runtime.prepare(package);
    expect(static_cast<bool>(prepared), prepared.diagnostic.c_str());
    std::vector<std::int32_t> result(static_cast<std::size_t>(frames) * 2U);
    std::vector<std::int32_t> left(block), right(block);
    std::uint32_t cursor = 0;
    while (cursor < frames) {
        const auto count = std::min(block, frames - cursor);
        const auto processed = runtime.process(left.data(), right.data(), count);
        expect(static_cast<bool>(processed), processed.diagnostic.c_str());
        for (std::uint32_t frame = 0; frame < count; ++frame) {
            result[static_cast<std::size_t>(cursor + frame) * 2U] = left[frame];
            result[static_cast<std::size_t>(cursor + frame) * 2U + 1U] = right[frame];
        }
        cursor += count;
    }
    return result;
}

void fixture_test(
    const char* path,
    std::size_t expected_nodes,
    std::size_t expected_connections
) {
    const std::string json = read_fixture(path);
    const PreparedPackage package = parse(json);
    expect(package.nodes.size() == expected_nodes, "node count mismatch");
    expect(package.connection_count == expected_connections, "connection count mismatch");
    const auto reference = render(package, 4097, 127);
    expect(
        std::any_of(reference.begin(), reference.end(), [](std::int32_t value) {
            return value != 0;
        }),
        "variable graph rendered silence"
    );
    for (const std::uint32_t block : {1U, 16U, 512U}) {
        expect(reference == render(package, 4097, block), "block-size output differs");
    }

    Runtime runtime;
    expect(static_cast<bool>(runtime.prepare(package)), "prepare failed");
    std::vector<std::int32_t> left(512), right(512);
    guarded_allocations.store(0, std::memory_order_relaxed);
    allocation_guard.store(true, std::memory_order_relaxed);
    const auto processed = runtime.process(left.data(), right.data(), 512);
    allocation_guard.store(false, std::memory_order_relaxed);
    expect(static_cast<bool>(processed), "guarded process failed");
    expect(
        guarded_allocations.load(std::memory_order_relaxed) == 0,
        "v1 processing allocated memory"
    );

    Event invalid{};
    invalid.node_index = static_cast<std::uint8_t>(package.nodes.size());
    expect(!runtime.enqueue(invalid), "unknown event node accepted");
    Event midi{};
    midi.kind = EventKind::midi_message;
    midi.midi_size = 3;
    expect(runtime.enqueue(midi), "valid MIDI event rejected");
}

void parser_negative_tests(const std::string& valid) {
    PreparedPackage package;
    expect(
        schuss::rt::v1::parse_package("{", "", package).code
            == ErrorCode::json_invalid,
        "malformed JSON accepted"
    );
    expect(
        schuss::rt::v1::parse_package(
            replaced(valid, "schuss.rt.soft-q27-v0", "schuss.rt.other-q27-v0"),
            "",
            package
        ).code == ErrorCode::package_hash_mismatch,
        "tampered package hash accepted"
    );
    expect(
        schuss::rt::v1::parse_package(
            rehashed(replaced(
                valid,
                "schuss.rt.soft-q27-v0",
                "schuss.rt.other-q27-v0"
            )),
            "",
            package
        ).code == ErrorCode::unknown_factory,
        "unknown factory accepted"
    );
    expect(
        schuss::rt::v1::parse_package(
            rehashed(replaced(
                valid,
                "sha256:5444c071225361d2cff4542406fc17d4ecbfd7396884285d1a776f7c51bde7be",
                "sha256:0444c071225361d2cff4542406fc17d4ecbfd7396884285d1a776f7c51bde7be"
            )),
            "",
            package
        ).code == ErrorCode::unknown_factory,
        "stale binding hash accepted"
    );
    expect(
        schuss::rt::v1::parse_package(
            rehashed(replaced(valid, "\"buffer_count\":4", "\"buffer_count\":5")),
            "",
            package
        ).code == ErrorCode::buffer_plan_invalid,
        "non-minimal buffer plan accepted"
    );
}

}  // namespace

int main() {
    try {
        const auto& registry = schuss::rt::v1::factory_registry();
        expect(registry.size() == 7, "factory registry count mismatch");
        std::vector<std::string_view> identities;
        for (const auto& descriptor : registry) identities.push_back(descriptor.factory_id);
        std::sort(identities.begin(), identities.end());
        expect(
            std::adjacent_find(identities.begin(), identities.end()) == identities.end(),
            "factory identity duplicate"
        );
        fixture_test(SCHUSS_RT_V1_SMALLER_FIXTURE_PATH, 3, 3);
        fixture_test(SCHUSS_RT_V1_REFERENCE_FIXTURE_PATH, 7, 7);
        fixture_test(SCHUSS_RT_V1_LARGER_FIXTURE_PATH, 8, 8);
        const PreparedPackage larger = parse(read_fixture(SCHUSS_RT_V1_LARGER_FIXTURE_PATH));
        const auto repeated = std::count_if(
            larger.nodes.begin(), larger.nodes.end(), [](const auto& node) {
                return node.factory_id == "schuss.rt.soft-q27-v0";
            }
        );
        expect(repeated == 2, "repeated factory instances were not retained");
        parser_negative_tests(read_fixture(SCHUSS_RT_V1_LARGER_FIXTURE_PATH));
        std::cout << "schuss_rt_v1_tests: passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "schuss_rt_v1_tests: " << error.what() << '\n';
        return 1;
    }
}
