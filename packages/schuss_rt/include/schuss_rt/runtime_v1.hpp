#pragma once

#include "schuss_rt/runtime.hpp"

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace schuss::rt::v1 {

inline constexpr std::string_view kRuntimeAbi = "schuss-rt-abi-v1";
inline constexpr std::string_view kPackageSchema = "host-runtime-package-v1";
inline constexpr std::string_view kProtocolAbi = "schuss-audio-engine-protocol-v1";
inline constexpr std::string_view kRegistryVersion = "schuss-rt-factory-registry-v1";
inline constexpr std::size_t kMaximumNodes = 64;
inline constexpr std::size_t kMaximumConnections = 192;
inline constexpr std::size_t kMaximumBuffers = 128;
inline constexpr std::size_t kMaximumStateBytes = 65536;
inline constexpr std::size_t kMaximumParameters = 256;
inline constexpr std::size_t kMaximumEvents = 1024;

enum class InputSource : std::uint8_t { buffer, constant };

struct Input {
    std::string facet_id;
    InputSource source{InputSource::constant};
    std::uint8_t buffer_index{};
    std::int32_t value_q{};
    std::uint8_t fractional_bits{};
};

struct Output {
    std::string facet_id;
    std::uint8_t buffer_index{};
};

struct Node {
    std::string node_id;
    Role role{};
    std::string contract_id;
    std::string binding_id;
    std::string factory_id;
    std::array<Input, 3> inputs{};
    std::uint8_t input_count{};
    std::array<Output, 2> outputs{};
    std::uint8_t output_count{};
    std::array<Parameter, 4> parameters{};
    std::uint8_t parameter_count{};
    std::uint32_t state_offset_bytes{};
    std::uint32_t state_size_bytes{};
    std::uint8_t state_alignment_bytes{1};
    std::uint8_t factory_index{};
};

struct PreparedPackage {
    std::string content_hash;
    std::vector<Node> nodes;
    std::vector<std::uint8_t> schedule;
    std::uint32_t connection_count{};
    std::uint32_t state_bytes{};
    std::uint32_t buffer_count{};
    std::uint32_t buffer_frames{};
    std::uint32_t parameter_count{};
    std::uint32_t event_capacity{};
    std::uint8_t left_buffer{};
    std::uint8_t right_buffer{};
};

class Runtime;
using PrepareFunction = bool (*)(const Node&) noexcept;
using ResetFunction = void (*)(std::uint8_t*, std::uint32_t) noexcept;
using EventFunction = bool (*)(Node&, const Event&) noexcept;
using ProcessFunction = void (*)(Runtime&, Node&, std::uint32_t, std::uint32_t) noexcept;

struct PortDescriptor {
    std::string_view facet_id;
    std::uint8_t fractional_bits;
};

struct FactoryDescriptor {
    std::string_view role_name;
    Role role;
    std::string_view contract_id;
    std::string_view contract_hash;
    std::string_view binding_id;
    std::string_view binding_hash;
    std::string_view factory_id;
    std::array<PortDescriptor, 3> inputs;
    std::uint8_t input_count;
    std::array<PortDescriptor, 2> outputs;
    std::uint8_t output_count;
    std::array<std::string_view, 4> parameters;
    std::uint8_t parameter_count;
    std::uint32_t state_size_bytes;
    std::uint8_t state_alignment_bytes;
    PrepareFunction prepare;
    ResetFunction reset;
    EventFunction event;
    ProcessFunction process;
};

const std::array<FactoryDescriptor, 7>& factory_registry() noexcept;
const FactoryDescriptor* find_factory(std::string_view factory_id) noexcept;

Result parse_package(
    std::string_view json,
    std::string_view expected_content_hash,
    PreparedPackage& destination
);

class Runtime {
public:
    Runtime() = default;
    Runtime(const Runtime&) = delete;
    Runtime& operator=(const Runtime&) = delete;

    Result prepare(const PreparedPackage& package);
    void reset() noexcept;
    bool enqueue(const Event& event) noexcept;
    Result process(
        std::int32_t* left_q27,
        std::int32_t* right_q27,
        std::uint32_t frames
    ) noexcept;

    const PreparedPackage& package() const noexcept { return package_; }
    Metrics metrics() const noexcept;
    bool prepared() const noexcept { return prepared_; }

    std::int32_t* buffer(std::uint8_t index) noexcept;
    const std::int32_t* buffer(std::uint8_t index) const noexcept;
    std::uint8_t* state(const Node& node) noexcept;
    std::int32_t input(const Node& node, std::size_t input_index, std::uint32_t frame) const noexcept;
    std::int32_t parameter(const Node& node, std::string_view facet, std::int32_t fallback = 0) const noexcept;

private:
    void apply_event(const Event& event) noexcept;
    void process_segment(std::uint32_t begin, std::uint32_t end) noexcept;

    PreparedPackage package_{};
    std::vector<std::uint8_t> state_;
    std::vector<std::int32_t> buffers_;
    std::vector<Event> event_ring_;
    std::vector<Event> callback_events_;
    std::atomic<std::uint32_t> event_write_{0};
    std::atomic<std::uint32_t> event_read_{0};
    std::atomic<std::uint64_t> queue_overflows_{0};
    std::atomic<std::uint64_t> processed_frames_{0};
    std::atomic<std::uint64_t> events_delivered_{0};
    bool prepared_{};
};

}  // namespace schuss::rt::v1
