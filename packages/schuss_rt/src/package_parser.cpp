#include "schuss_rt/runtime.hpp"
#include "schuss_rt/sha256.hpp"

#include <algorithm>
#include <array>
#include <charconv>
#include <cctype>
#include <cstdint>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace schuss::rt {
namespace {

struct JsonError final : std::runtime_error {
    using std::runtime_error::runtime_error;
};

struct Value {
    enum class Kind { null_value, boolean, integer, string, array, object };
    using Array = std::vector<Value>;
    using Object = std::map<std::string, Value>;

    Kind kind{Kind::null_value};
    bool boolean{};
    std::int64_t integer{};
    std::string string;
    Array array;
    Object object;
};

class Parser {
public:
    explicit Parser(std::string_view source) : source_(source) {}

    Value parse() {
        Value value = parse_value();
        whitespace();
        if (position_ != source_.size()) {
            fail("trailing JSON data");
        }
        return value;
    }

private:
    [[noreturn]] void fail(const char* message) const {
        throw JsonError(std::string(message) + " at byte " + std::to_string(position_));
    }

    void whitespace() {
        while (position_ < source_.size()) {
            const unsigned char character = static_cast<unsigned char>(source_[position_]);
            if (character != ' ' && character != '\n' && character != '\r' && character != '\t') {
                break;
            }
            ++position_;
        }
    }

    char take() {
        if (position_ >= source_.size()) {
            fail("unexpected end of JSON");
        }
        return source_[position_++];
    }

    bool consume(char character) {
        whitespace();
        if (position_ < source_.size() && source_[position_] == character) {
            ++position_;
            return true;
        }
        return false;
    }

    void literal(std::string_view expected) {
        if (source_.substr(position_, expected.size()) != expected) {
            fail("invalid JSON literal");
        }
        position_ += expected.size();
    }

    static int hex(char character) {
        if (character >= '0' && character <= '9') return character - '0';
        if (character >= 'a' && character <= 'f') return 10 + character - 'a';
        if (character >= 'A' && character <= 'F') return 10 + character - 'A';
        return -1;
    }

    std::string parse_string() {
        whitespace();
        if (take() != '"') fail("expected JSON string");
        std::string result;
        while (position_ < source_.size()) {
            const unsigned char character = static_cast<unsigned char>(take());
            if (character == '"') return result;
            if (character < 0x20) fail("control character in JSON string");
            if (character != '\\') {
                result.push_back(static_cast<char>(character));
                continue;
            }
            const char escaped = take();
            switch (escaped) {
                case '"': result.push_back('"'); break;
                case '\\': result.push_back('\\'); break;
                case '/': result.push_back('/'); break;
                case 'b': result.push_back('\b'); break;
                case 'f': result.push_back('\f'); break;
                case 'n': result.push_back('\n'); break;
                case 'r': result.push_back('\r'); break;
                case 't': result.push_back('\t'); break;
                case 'u': {
                    unsigned value = 0;
                    for (int index = 0; index < 4; ++index) {
                        const int digit = hex(take());
                        if (digit < 0) fail("invalid JSON unicode escape");
                        value = (value << 4U) | static_cast<unsigned>(digit);
                    }
                    if (value > 0x7fU) fail("non-ASCII JSON escape is unsupported by package ABI v0");
                    result.push_back(static_cast<char>(value));
                    break;
                }
                default: fail("invalid JSON escape");
            }
        }
        fail("unterminated JSON string");
    }

    Value parse_number() {
        whitespace();
        const std::size_t begin = position_;
        if (position_ < source_.size() && source_[position_] == '-') ++position_;
        if (position_ >= source_.size() || !std::isdigit(static_cast<unsigned char>(source_[position_]))) {
            fail("invalid JSON number");
        }
        if (source_[position_] == '0') {
            ++position_;
            if (position_ < source_.size() && std::isdigit(static_cast<unsigned char>(source_[position_]))) {
                fail("leading zero in JSON number");
            }
        } else {
            while (position_ < source_.size() && std::isdigit(static_cast<unsigned char>(source_[position_]))) ++position_;
        }
        if (position_ < source_.size() && (source_[position_] == '.' || source_[position_] == 'e' || source_[position_] == 'E')) {
            fail("package ABI v0 admits integer JSON numbers only");
        }
        std::int64_t result{};
        const auto parsed = std::from_chars(source_.data() + begin, source_.data() + position_, result);
        if (parsed.ec != std::errc{} || parsed.ptr != source_.data() + position_) fail("JSON integer out of range");
        Value value;
        value.kind = Value::Kind::integer;
        value.integer = result;
        return value;
    }

    Value parse_array() {
        Value value;
        value.kind = Value::Kind::array;
        if (take() != '[') fail("expected array");
        whitespace();
        if (consume(']')) return value;
        for (;;) {
            value.array.push_back(parse_value());
            if (consume(']')) return value;
            if (!consume(',')) fail("expected comma in array");
        }
    }

    Value parse_object() {
        Value value;
        value.kind = Value::Kind::object;
        if (take() != '{') fail("expected object");
        whitespace();
        if (consume('}')) return value;
        for (;;) {
            const std::string key = parse_string();
            if (!consume(':')) fail("expected colon in object");
            auto inserted = value.object.emplace(key, parse_value());
            if (!inserted.second) fail("duplicate JSON object member");
            if (consume('}')) return value;
            if (!consume(',')) fail("expected comma in object");
        }
    }

    Value parse_value() {
        whitespace();
        if (position_ >= source_.size()) fail("missing JSON value");
        const char character = source_[position_];
        if (character == '{') return parse_object();
        if (character == '[') return parse_array();
        if (character == '"') {
            Value value;
            value.kind = Value::Kind::string;
            value.string = parse_string();
            return value;
        }
        if (character == '-' || std::isdigit(static_cast<unsigned char>(character))) return parse_number();
        if (character == 't' || character == 'f') {
            Value value;
            value.kind = Value::Kind::boolean;
            value.boolean = character == 't';
            literal(value.boolean ? "true" : "false");
            return value;
        }
        if (character == 'n') {
            literal("null");
            return {};
        }
        fail("invalid JSON value");
    }

    std::string_view source_;
    std::size_t position_{};
};

const Value& member(const Value& object, std::string_view key) {
    if (object.kind != Value::Kind::object) throw JsonError("expected JSON object");
    const auto found = object.object.find(std::string(key));
    if (found == object.object.end()) throw JsonError("missing member " + std::string(key));
    return found->second;
}

void only_keys(const Value& object, std::initializer_list<std::string_view> expected) {
    if (object.kind != Value::Kind::object) throw JsonError("expected JSON object");
    std::set<std::string> keys;
    for (const auto value : expected) keys.emplace(value);
    for (const auto& item : object.object) {
        if (keys.count(item.first) == 0) throw JsonError("unexpected member " + item.first);
    }
    if (object.object.size() != keys.size()) throw JsonError("object member set is incomplete");
}

const std::string& string(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::string) throw JsonError(std::string(name) + " must be a string");
    return value.string;
}

bool boolean(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::boolean) throw JsonError(std::string(name) + " must be a boolean");
    return value.boolean;
}

bool is_content_hash(std::string_view value) noexcept {
    if (value.size() != 71 || value.substr(0, 7) != "sha256:") return false;
    return std::all_of(value.begin() + 7, value.end(), [](unsigned char character) {
        return (character >= '0' && character <= '9') || (character >= 'a' && character <= 'f');
    });
}

bool is_raw_sha256(std::string_view value) noexcept {
    if (value.size() != 64) return false;
    return std::all_of(value.begin(), value.end(), [](unsigned char character) {
        return (character >= '0' && character <= '9') || (character >= 'a' && character <= 'f');
    });
}

bool exact_reference(
    const Value& value,
    std::string_view id_field,
    std::string_view expected_id,
    std::uint32_t expected_revision
) {
    if (value.kind != Value::Kind::object || value.object.size() != 3
        || value.object.count(std::string(id_field)) != 1
        || value.object.count("revision") != 1 || value.object.count("content_hash") != 1) {
        return false;
    }
    const Value& identifier = value.object.at(std::string(id_field));
    const Value& revision = value.object.at("revision");
    const Value& hash = value.object.at("content_hash");
    return identifier.kind == Value::Kind::string && identifier.string == expected_id
        && revision.kind == Value::Kind::integer
        && revision.integer == static_cast<std::int64_t>(expected_revision)
        && hash.kind == Value::Kind::string && is_content_hash(hash.string);
}

bool project_reference(const Value& value) {
    if (value.kind != Value::Kind::object || value.object.size() != 3
        || value.object.count("project_id") != 1 || value.object.count("revision") != 1
        || value.object.count("content_hash") != 1) {
        return false;
    }
    const Value& identifier = value.object.at("project_id");
    const Value& revision = value.object.at("revision");
    const Value& hash = value.object.at("content_hash");
    return identifier.kind == Value::Kind::string
        && identifier.string.rfind("schuss-project-", 0) == 0
        && revision.kind == Value::Kind::integer && revision.integer >= 1
        && hash.kind == Value::Kind::string && is_content_hash(hash.string);
}

std::string package_record_digest_input(std::string_view json, std::string_view embedded_hash) {
    std::string canonical(json);
    if (!canonical.empty() && canonical.back() == '\n') canonical.pop_back();
    const std::string marker = "\"content_hash\":\"" + std::string(embedded_hash) + "\"";
    std::size_t selected = std::string::npos;
    std::size_t begin = 0;
    while ((begin = canonical.find(marker, begin)) != std::string::npos) {
        const auto after = begin + marker.size();
        if (canonical.compare(after, 24, ",\"control_period_frames\"") == 0) {
            if (selected != std::string::npos) throw JsonError("duplicate root content hash");
            selected = begin;
        }
        begin = after;
    }
    if (selected == std::string::npos) throw JsonError("root content hash is not canonical");
    canonical.erase(selected, marker.size() + 1U);
    return canonical;
}

std::uint32_t unsigned_integer(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::integer || value.integer < 0 || value.integer > std::numeric_limits<std::uint32_t>::max()) {
        throw JsonError(std::string(name) + " must be a uint32");
    }
    return static_cast<std::uint32_t>(value.integer);
}

std::int32_t signed_integer(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::integer || value.integer < std::numeric_limits<std::int32_t>::min() || value.integer > std::numeric_limits<std::int32_t>::max()) {
        throw JsonError(std::string(name) + " must be an int32");
    }
    return static_cast<std::int32_t>(value.integer);
}

const Value::Array& array(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::array) throw JsonError(std::string(name) + " must be an array");
    return value.array;
}

Role role(std::string_view value) {
    if (value == "saw") return Role::saw;
    if (value == "pwm") return Role::pwm;
    if (value == "soft") return Role::soft;
    if (value == "smooth") return Role::smooth;
    if (value == "crossfade") return Role::crossfade;
    if (value == "vca") return Role::vca;
    if (value == "output") return Role::output;
    throw JsonError("unknown node role");
}

constexpr std::array<std::string_view, kNodeCount> kRoleNames{
    "saw", "pwm", "soft", "smooth", "crossfade", "vca", "output"
};
constexpr std::array<std::string_view, kNodeCount> kNodeIds{
    "graph-node-000001", "graph-node-000002", "graph-node-000003",
    "graph-node-000005", "graph-node-000006", "graph-node-000007",
    "graph-node-000008"
};
constexpr std::array<std::string_view, kNodeCount> kFactoryNames{
    "schuss.rt.saw-q27-v0", "schuss.rt.pwm-q27-v0", "schuss.rt.soft-q27-v0",
    "schuss.rt.smooth-q27-v0", "schuss.rt.crossfade-q27-v0", "schuss.rt.vca-q27-v0",
    "schuss.rt.output-q27-v0"
};
constexpr std::array<std::uint8_t, kNodeCount> kInputCounts{0, 0, 1, 0, 2, 2, 2};
constexpr std::array<std::uint8_t, kNodeCount> kOutputCounts{1, 1, 1, 1, 1, 1, 2};
constexpr std::array<std::uint32_t, kNodeCount> kStateSizes{16, 16, 0, 8, 0, 8, 0};
constexpr std::array<std::string_view, kNodeCount> kContractIds{
    "schuss-component-contract-000012", "schuss-component-contract-000013",
    "schuss-component-contract-000016", "schuss-component-contract-000015",
    "schuss-component-contract-000003", "schuss-component-contract-000020",
    "schuss-component-contract-000009"
};
constexpr std::array<std::string_view, kNodeCount> kBindingIds{
    "schuss-implementation-000162", "schuss-implementation-000163",
    "schuss-implementation-000164", "schuss-implementation-000165",
    "schuss-implementation-000166", "schuss-implementation-000167",
    "schuss-implementation-000168"
};
constexpr std::array<std::uint8_t, kNodeCount> kParameterCounts{1, 2, 0, 2, 1, 0, 0};
constexpr std::array<std::array<std::string_view, 2>, kNodeCount> kParameterFacets{{
    {{"component-parameter-000001", ""}},
    {{"component-parameter-000001", "component-port-000002"}},
    {{"", ""}},
    {{"component-parameter-000001", "component-port-000001"}},
    {{"component-port-000003", ""}},
    {{"", ""}},
    {{"", ""}},
}};

Result failure(ErrorCode code, std::string diagnostic) {
    return {code, std::move(diagnostic)};
}

}  // namespace

Result parse_package(
    std::string_view json,
    std::string_view expected_content_hash,
    PreparedPackage& destination
) {
    try {
        const Value root = Parser(json).parse();
        only_keys(root, {
            "schema_version", "canonical_profile", "derived", "authoritative", "content_hash",
            "runtime_abi", "engine_protocol_abi", "numeric_profile", "project_reference",
            "graph_reference", "instrument_reference", "host_build_request_reference",
            "compute_target_reference", "backend_reference", "semantic_profile_reference",
            "source_plan_sha256", "sample_rate_hz", "max_block_frames", "control_period_frames",
            "block_policy", "input_channels", "output_channels", "latency_frames", "tail_frames",
            "seed", "memory_plan", "nodes", "connections", "schedule", "outputs", "event_contract",
            "exclusions"
        });
        if (string(member(root, "schema_version"), "schema_version") != kPackageSchema) {
            return failure(ErrorCode::package_schema_unsupported, "HOST_PACKAGE_SCHEMA_UNSUPPORTED");
        }
        PreparedPackage parsed;
        parsed.content_hash = string(member(root, "content_hash"), "content_hash");
        if (!is_content_hash(parsed.content_hash)) {
            return failure(ErrorCode::package_hash_mismatch, "HOST_PACKAGE_HASH_INVALID");
        }
        const auto digest_input = package_record_digest_input(json, parsed.content_hash);
        if ("sha256:" + sha256_hex(digest_input) != parsed.content_hash
            || (!expected_content_hash.empty() && parsed.content_hash != expected_content_hash)) {
            return failure(ErrorCode::package_hash_mismatch, "HOST_PACKAGE_HASH_MISMATCH");
        }
        if (string(member(root, "canonical_profile"), "canonical_profile") != "schuss-canonical-json-v1"
            || !boolean(member(root, "derived"), "derived")
            || boolean(member(root, "authoritative"), "authoritative")
            || string(member(root, "engine_protocol_abi"), "engine_protocol_abi") != "schuss-audio-engine-protocol-v0"
            || string(member(root, "block_policy"), "block_policy") != "bounded-variable-with-final-partial") {
            return failure(ErrorCode::package_shape_invalid, "HOST_PACKAGE_BOUNDARY_INVALID");
        }
        if (string(member(root, "runtime_abi"), "runtime_abi") != kRuntimeAbi) {
            return failure(ErrorCode::runtime_abi_mismatch, "HOST_RUNTIME_ABI_MISMATCH");
        }
        if (string(member(root, "numeric_profile"), "numeric_profile") != kNumericProfile) {
            return failure(ErrorCode::numeric_profile_unsupported, "HOST_NUMERIC_PROFILE_UNSUPPORTED");
        }
        if (unsigned_integer(member(root, "sample_rate_hz"), "sample_rate_hz") != kSampleRate
            || unsigned_integer(member(root, "max_block_frames"), "max_block_frames") != kMaximumBlockFrames
            || unsigned_integer(member(root, "control_period_frames"), "control_period_frames") != 16
            || unsigned_integer(member(root, "input_channels"), "input_channels") != 0
            || unsigned_integer(member(root, "output_channels"), "output_channels") != 2
            || unsigned_integer(member(root, "latency_frames"), "latency_frames") != 0
            || unsigned_integer(member(root, "tail_frames"), "tail_frames") != 0
            || unsigned_integer(member(root, "seed"), "seed") != 0) {
            return failure(ErrorCode::package_shape_invalid, "HOST_PACKAGE_FIXED_PROFILE_MISMATCH");
        }
        if (!project_reference(member(root, "project_reference"))
            || !exact_reference(member(root, "graph_reference"), "graph_id", "schuss-graph-000006", 1)
            || !exact_reference(member(root, "instrument_reference"), "instrument_id", "schuss-instrument-000005", 1)
            || !exact_reference(member(root, "host_build_request_reference"), "build_request_id", "schuss-build-request-000006", 1)
            || !exact_reference(member(root, "compute_target_reference"), "compute_target_id", "schuss-compute-target-000002", 1)
            || !exact_reference(member(root, "backend_reference"), "backend_id", "schuss-backend-000003", 1)
            || !is_raw_sha256(string(member(root, "source_plan_sha256"), "source_plan_sha256"))) {
            return failure(ErrorCode::package_shape_invalid, "HOST_PACKAGE_REFERENCE_INVALID");
        }
        const Value& profile = member(root, "semantic_profile_reference");
        only_keys(profile, {"profile_id", "version", "content_hash"});
        if (string(member(profile, "profile_id"), "profile_id") != "schuss-semantic-profile-000001"
            || unsigned_integer(member(profile, "version"), "profile version") != 1
            || !is_content_hash(string(member(profile, "content_hash"), "profile content hash"))) {
            return failure(ErrorCode::package_shape_invalid, "HOST_SEMANTIC_PROFILE_REFERENCE_INVALID");
        }

        const Value& memory = member(root, "memory_plan");
        only_keys(memory, {"state_bytes", "buffer_count", "buffer_frames", "buffer_bytes", "event_capacity"});
        parsed.state_bytes = unsigned_integer(member(memory, "state_bytes"), "state_bytes");
        parsed.buffer_count = unsigned_integer(member(memory, "buffer_count"), "buffer_count");
        parsed.buffer_frames = unsigned_integer(member(memory, "buffer_frames"), "buffer_frames");
        parsed.event_capacity = unsigned_integer(member(memory, "event_capacity"), "event_capacity");
        const std::uint32_t buffer_bytes = unsigned_integer(member(memory, "buffer_bytes"), "buffer_bytes");
        if (parsed.state_bytes != 48) {
            return failure(ErrorCode::state_plan_invalid, "HOST_STATE_PLAN_INVALID");
        }
        if (parsed.buffer_count != 8 || parsed.buffer_frames != kMaximumBlockFrames
            || buffer_bytes != parsed.buffer_count * parsed.buffer_frames * sizeof(std::int32_t)) {
            return failure(ErrorCode::buffer_plan_invalid, "HOST_MEMORY_PLAN_INVALID");
        }
        if (parsed.event_capacity != 1024) {
            return failure(ErrorCode::event_contract_invalid, "HOST_EVENT_CAPACITY_INVALID");
        }

        const auto& node_values = array(member(root, "nodes"), "nodes");
        if (node_values.size() != kNodeCount) return failure(ErrorCode::package_shape_invalid, "HOST_NODE_COUNT_INVALID");
        std::map<std::string, std::uint8_t> node_indices;
        std::vector<std::pair<std::uint32_t, std::uint32_t>> state_intervals;
        for (std::size_t index = 0; index < node_values.size(); ++index) {
            const Value& value = node_values[index];
            only_keys(value, {"node_id", "role", "contract_reference", "binding_reference", "factory_id", "input_buffers", "output_buffers", "parameters", "state_offset_bytes", "state_size_bytes"});
            Node node;
            node.node_id = string(member(value, "node_id"), "node_id");
            if (node.node_id != kNodeIds[index]) {
                return failure(ErrorCode::unknown_node, "HOST_NODE_ID_UNKNOWN");
            }
            if (!node_indices.emplace(node.node_id, static_cast<std::uint8_t>(index)).second) {
                return failure(ErrorCode::package_shape_invalid, "HOST_NODE_ID_DUPLICATE");
            }
            const std::string& role_name = string(member(value, "role"), "role");
            node.role = role(role_name);
            if (role_name != kRoleNames[index]) return failure(ErrorCode::schedule_invalid, "HOST_NODE_ROLE_ORDER_INVALID");
            node.factory_id = string(member(value, "factory_id"), "factory_id");
            if (node.factory_id != kFactoryNames[index]) return failure(ErrorCode::unknown_factory, "HOST_FACTORY_UNKNOWN");
            if (!exact_reference(member(value, "contract_reference"), "component_contract_id", kContractIds[index], 1)
                || !exact_reference(member(value, "binding_reference"), "implementation_id", kBindingIds[index], 2)) {
                return failure(ErrorCode::package_shape_invalid, "HOST_NODE_REFERENCE_INVALID");
            }

            const auto& inputs = array(member(value, "input_buffers"), "input_buffers");
            const auto& outputs = array(member(value, "output_buffers"), "output_buffers");
            if (inputs.size() != kInputCounts[index] || outputs.size() != kOutputCounts[index]) {
                return failure(ErrorCode::port_contract_invalid, "HOST_PORT_ARITY_INVALID");
            }
            node.input_count = static_cast<std::uint8_t>(inputs.size());
            node.output_count = static_cast<std::uint8_t>(outputs.size());
            for (std::size_t item = 0; item < inputs.size(); ++item) {
                const auto buffer = unsigned_integer(inputs[item], "input buffer");
                if (buffer >= parsed.buffer_count) return failure(ErrorCode::buffer_plan_invalid, "HOST_INPUT_BUFFER_INVALID");
                node.input_buffers[item] = static_cast<std::uint8_t>(buffer);
            }
            for (std::size_t item = 0; item < outputs.size(); ++item) {
                const auto buffer = unsigned_integer(outputs[item], "output buffer");
                if (buffer >= parsed.buffer_count) return failure(ErrorCode::buffer_plan_invalid, "HOST_OUTPUT_BUFFER_INVALID");
                node.output_buffers[item] = static_cast<std::uint8_t>(buffer);
            }

            const auto& parameters = array(member(value, "parameters"), "parameters");
            if (parameters.size() != kParameterCounts[index]
                || parameters.size() > node.parameters.size()) {
                return failure(ErrorCode::port_contract_invalid, "HOST_PARAMETER_COUNT_INVALID");
            }
            std::set<std::string> parameter_facets;
            node.parameter_count = static_cast<std::uint8_t>(parameters.size());
            for (std::size_t item = 0; item < parameters.size(); ++item) {
                only_keys(parameters[item], {"facet_id", "value_q"});
                node.parameters[item].facet_id = string(member(parameters[item], "facet_id"), "facet_id");
                node.parameters[item].value_q = signed_integer(member(parameters[item], "value_q"), "value_q");
                if (node.parameters[item].facet_id != kParameterFacets[index][item]
                    || !parameter_facets.emplace(node.parameters[item].facet_id).second) {
                    return failure(ErrorCode::port_contract_invalid, "HOST_PARAMETER_FACET_INVALID");
                }
            }
            node.state_offset_bytes = unsigned_integer(member(value, "state_offset_bytes"), "state_offset_bytes");
            node.state_size_bytes = unsigned_integer(member(value, "state_size_bytes"), "state_size_bytes");
            const std::uint32_t expected_offset = index == 0
                ? 0U
                : parsed.nodes[index - 1U].state_offset_bytes + parsed.nodes[index - 1U].state_size_bytes;
            if (node.state_size_bytes != kStateSizes[index] || node.state_offset_bytes != expected_offset
                || node.state_offset_bytes + node.state_size_bytes > parsed.state_bytes) {
                return failure(ErrorCode::state_plan_invalid, "HOST_STATE_BOUNDS_INVALID");
            }
            if (node.state_size_bytes > 0) state_intervals.emplace_back(node.state_offset_bytes, node.state_offset_bytes + node.state_size_bytes);
            parsed.nodes[index] = std::move(node);
        }
        std::sort(state_intervals.begin(), state_intervals.end());
        for (std::size_t index = 1; index < state_intervals.size(); ++index) {
            if (state_intervals[index].first < state_intervals[index - 1].second) {
                return failure(ErrorCode::state_plan_invalid, "HOST_STATE_OVERLAP");
            }
        }
        const auto& final_node = parsed.nodes.back();
        if (final_node.state_offset_bytes + final_node.state_size_bytes != parsed.state_bytes) {
            return failure(ErrorCode::state_plan_invalid, "HOST_STATE_PLAN_NOT_EXACT");
        }

        const auto& schedule = array(member(root, "schedule"), "schedule");
        if (schedule.size() != kNodeCount) return failure(ErrorCode::schedule_invalid, "HOST_SCHEDULE_COUNT_INVALID");
        std::set<std::uint8_t> scheduled;
        for (std::size_t index = 0; index < schedule.size(); ++index) {
            const auto found = node_indices.find(string(schedule[index], "schedule node"));
            if (found == node_indices.end() || !scheduled.emplace(found->second).second || found->second != index) {
                return failure(ErrorCode::schedule_invalid, "HOST_SCHEDULE_INVALID");
            }
            parsed.schedule[index] = found->second;
        }

        const auto& connections = array(member(root, "connections"), "connections");
        if (connections.size() != 7) return failure(ErrorCode::package_shape_invalid, "HOST_CONNECTION_COUNT_INVALID");
        std::set<std::string> connection_ids;
        std::set<std::string> connection_signatures;
        for (const Value& connection : connections) {
            only_keys(connection, {"connection_id", "source", "destination", "buffer_index"});
            const Value& source = member(connection, "source");
            const Value& destination_value = member(connection, "destination");
            only_keys(source, {"node_id", "facet_id"});
            only_keys(destination_value, {"node_id", "facet_id"});
            const auto source_node = node_indices.find(string(member(source, "node_id"), "source node"));
            const auto destination_node = node_indices.find(string(member(destination_value, "node_id"), "destination node"));
            const auto& source_facet = string(member(source, "facet_id"), "source facet");
            const auto& destination_facet = string(member(destination_value, "facet_id"), "destination facet");
            const auto buffer = unsigned_integer(member(connection, "buffer_index"), "connection buffer");
            if (!connection_ids.emplace(string(member(connection, "connection_id"), "connection_id")).second) {
                return failure(ErrorCode::port_contract_invalid, "HOST_CONNECTION_ID_DUPLICATE");
            }
            if (source_node == node_indices.end() || destination_node == node_indices.end()) {
                return failure(ErrorCode::port_contract_invalid, "HOST_CONNECTION_NODE_UNKNOWN");
            }
            if (source_node->second >= destination_node->second) return failure(ErrorCode::cycle_detected, "HOST_GRAPH_CYCLE_OR_BACK_EDGE");
            const Node& source_definition = parsed.nodes[source_node->second];
            const Node& destination_definition = parsed.nodes[destination_node->second];
            if (std::find(source_definition.output_buffers.begin(), source_definition.output_buffers.begin() + source_definition.output_count, buffer) == source_definition.output_buffers.begin() + source_definition.output_count
                || std::find(destination_definition.input_buffers.begin(), destination_definition.input_buffers.begin() + destination_definition.input_count, buffer) == destination_definition.input_buffers.begin() + destination_definition.input_count) {
                return failure(ErrorCode::port_contract_invalid, "HOST_CONNECTION_BUFFER_MISMATCH");
            }
            connection_signatures.emplace(
                std::to_string(source_node->second) + ":" + source_facet + ":"
                + std::to_string(destination_node->second) + ":" + destination_facet + ":"
                + std::to_string(buffer)
            );
        }
        const std::set<std::string> expected_connections{
            "0:component-port-000002:2:component-port-000001:0",
            "1:component-port-000003:4:component-port-000001:1",
            "2:component-port-000002:4:component-port-000002:2",
            "3:component-port-000002:5:component-port-000001:3",
            "4:component-port-000004:5:component-port-000002:4",
            "5:component-port-000003:6:component-port-000001:5",
            "5:component-port-000003:6:component-port-000002:5",
        };
        if (connection_signatures != expected_connections) {
            return failure(ErrorCode::port_contract_invalid, "HOST_CONNECTION_PROFILE_INVALID");
        }

        const Value& outputs = member(root, "outputs");
        only_keys(outputs, {"left_buffer", "right_buffer"});
        const auto left_buffer = unsigned_integer(member(outputs, "left_buffer"), "left_buffer");
        const auto right_buffer = unsigned_integer(member(outputs, "right_buffer"), "right_buffer");
        if (left_buffer != 6 || right_buffer != 7
            || left_buffer >= parsed.buffer_count || right_buffer >= parsed.buffer_count
            || left_buffer > std::numeric_limits<std::uint8_t>::max()
            || right_buffer > std::numeric_limits<std::uint8_t>::max()) {
            return failure(ErrorCode::buffer_plan_invalid, "HOST_FINAL_OUTPUT_BUFFER_INVALID");
        }
        parsed.left_buffer = static_cast<std::uint8_t>(left_buffer);
        parsed.right_buffer = static_cast<std::uint8_t>(right_buffer);

        const Value& event = member(root, "event_contract");
        only_keys(event, {"capacity", "ordering", "accepted_kinds", "overflow_policy"});
        const auto capacity = unsigned_integer(member(event, "capacity"), "event capacity");
        const auto& kinds = array(member(event, "accepted_kinds"), "accepted_kinds");
        std::set<std::string> kind_names;
        for (const auto& kind : kinds) kind_names.emplace(string(kind, "event kind"));
        if (capacity != parsed.event_capacity || capacity == 0 || capacity > 4096
            || string(member(event, "ordering"), "ordering") != "frame-offset-then-sequence"
            || string(member(event, "overflow_policy"), "overflow_policy") != "drop-newest-and-count"
            || kind_names != std::set<std::string>{"midi-message", "parameter-q27"}) {
            return failure(ErrorCode::event_contract_invalid, "HOST_EVENT_CONTRACT_INVALID");
        }
        const auto& exclusions = array(member(root, "exclusions"), "exclusions");
        std::set<std::string> exclusion_names;
        for (const auto& exclusion : exclusions) exclusion_names.emplace(string(exclusion, "exclusion"));
        const std::set<std::string> expected_exclusions{
            "JUCE dependency in schuss_rt", "Ksoloti equivalence claim", "dynamic graph mutation",
            "implicit device access", "reverb", "runtime parsing on the audio callback"
        };
        if (exclusion_names != expected_exclusions || exclusions.size() != expected_exclusions.size()) {
            return failure(ErrorCode::package_shape_invalid, "HOST_PACKAGE_EXCLUSIONS_INVALID");
        }
        destination = std::move(parsed);
        return {};
    } catch (const JsonError& error) {
        return failure(ErrorCode::json_invalid, std::string("HOST_PACKAGE_JSON_INVALID: ") + error.what());
    } catch (const std::exception& error) {
        return failure(ErrorCode::package_shape_invalid, std::string("HOST_PACKAGE_INVALID: ") + error.what());
    }
}

}  // namespace schuss::rt
