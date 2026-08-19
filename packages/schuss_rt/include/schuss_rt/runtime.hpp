#pragma once

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace schuss::rt {

inline constexpr std::string_view kRuntimeAbi = "schuss-rt-abi-v0";
inline constexpr std::string_view kPackageSchema = "host-runtime-package-v0";
inline constexpr std::string_view kNumericProfile = "schuss-host-q27-reference-v0";
inline constexpr std::uint32_t kSampleRate = 48000;
inline constexpr std::uint32_t kMaximumBlockFrames = 512;
inline constexpr std::size_t kNodeCount = 7;

enum class ErrorCode {
    ok,
    json_invalid,
    package_schema_unsupported,
    runtime_abi_mismatch,
    numeric_profile_unsupported,
    package_hash_mismatch,
    package_shape_invalid,
    unknown_node,
    unknown_factory,
    port_contract_invalid,
    schedule_invalid,
    cycle_detected,
    state_plan_invalid,
    buffer_plan_invalid,
    event_contract_invalid,
    not_prepared,
    block_too_large,
};

struct Result {
    ErrorCode code{ErrorCode::ok};
    std::string diagnostic;

    explicit operator bool() const noexcept { return code == ErrorCode::ok; }
};

enum class Role : std::uint8_t { saw, pwm, soft, smooth, crossfade, vca, output };

struct Parameter {
    std::string facet_id;
    std::int32_t value_q{};
};

struct Node {
    std::string node_id;
    Role role{};
    std::string factory_id;
    std::array<std::uint8_t, 3> input_buffers{};
    std::uint8_t input_count{};
    std::array<std::uint8_t, 2> output_buffers{};
    std::uint8_t output_count{};
    std::array<Parameter, 4> parameters{};
    std::uint8_t parameter_count{};
    std::uint32_t state_offset_bytes{};
    std::uint32_t state_size_bytes{};
};

struct PreparedPackage {
    std::string content_hash;
    std::array<Node, kNodeCount> nodes{};
    std::array<std::uint8_t, kNodeCount> schedule{};
    std::uint32_t state_bytes{};
    std::uint32_t buffer_count{};
    std::uint32_t buffer_frames{};
    std::uint32_t event_capacity{};
    std::uint8_t left_buffer{};
    std::uint8_t right_buffer{};
};

enum class EventKind : std::uint8_t { parameter_q27, midi_message };

struct Event {
    std::uint32_t frame_offset{};
    std::uint64_t sequence{};
    EventKind kind{EventKind::parameter_q27};
    std::uint8_t node_index{};
    std::uint8_t parameter_index{};
    std::int32_t value_q{};
    std::array<std::uint8_t, 3> midi{};
    std::uint8_t midi_size{};
};

struct Metrics {
    std::uint64_t processed_frames{};
    std::uint64_t events_delivered{};
    std::uint64_t queue_overflows{};
};

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
    Result process(std::int32_t* left_q27, std::int32_t* right_q27, std::uint32_t frames) noexcept;

    const PreparedPackage& package() const noexcept { return package_; }
    Metrics metrics() const noexcept;
    bool prepared() const noexcept { return prepared_; }

private:
    std::int32_t parameter(const Node& node, std::string_view facet, std::int32_t fallback = 0) const noexcept;
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

const char* error_name(ErrorCode code) noexcept;

}  // namespace schuss::rt
