#include "schuss_rt/runtime_v1.hpp"
#include "schuss_rt/sha256.hpp"

#include <algorithm>
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

namespace schuss::rt::v1 {
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
        if (position_ != source_.size()) fail("trailing JSON data");
        return value;
    }

private:
    [[noreturn]] void fail(const char* message) const {
        throw JsonError(std::string(message) + " at byte " + std::to_string(position_));
    }

    void whitespace() {
        while (position_ < source_.size()) {
            const unsigned char character = static_cast<unsigned char>(source_[position_]);
            if (character != ' ' && character != '\n' && character != '\r'
                && character != '\t') {
                break;
            }
            ++position_;
        }
    }

    char take() {
        if (position_ >= source_.size()) fail("unexpected end of JSON");
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
            if (character < 0x20U) fail("control character in JSON string");
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
                    if (value > 0x7fU) fail("non-ASCII JSON escape is unsupported");
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
        if (position_ >= source_.size()
            || !std::isdigit(static_cast<unsigned char>(source_[position_]))) {
            fail("invalid JSON number");
        }
        if (source_[position_] == '0') {
            ++position_;
            if (position_ < source_.size()
                && std::isdigit(static_cast<unsigned char>(source_[position_]))) {
                fail("leading zero in JSON number");
            }
        } else {
            while (position_ < source_.size()
                && std::isdigit(static_cast<unsigned char>(source_[position_]))) {
                ++position_;
            }
        }
        if (position_ < source_.size()
            && (source_[position_] == '.' || source_[position_] == 'e'
                || source_[position_] == 'E')) {
            fail("package ABI v1 admits integer JSON numbers only");
        }
        std::int64_t result{};
        const auto parsed = std::from_chars(
            source_.data() + begin, source_.data() + position_, result
        );
        if (parsed.ec != std::errc{} || parsed.ptr != source_.data() + position_) {
            fail("JSON integer out of range");
        }
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
            if (!value.object.emplace(key, parse_value()).second) {
                fail("duplicate JSON object member");
            }
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
        if (character == '-' || std::isdigit(static_cast<unsigned char>(character))) {
            return parse_number();
        }
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
    if (found == object.object.end()) {
        throw JsonError("missing member " + std::string(key));
    }
    return found->second;
}

void only_keys(const Value& object, std::initializer_list<std::string_view> expected) {
    if (object.kind != Value::Kind::object) throw JsonError("expected JSON object");
    std::set<std::string> keys;
    for (const auto value : expected) keys.emplace(value);
    if (object.object.size() != keys.size()) throw JsonError("object member set is incomplete");
    for (const auto& item : object.object) {
        if (keys.count(item.first) == 0) {
            throw JsonError("unexpected member " + item.first);
        }
    }
}

const std::string& string(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::string) {
        throw JsonError(std::string(name) + " must be a string");
    }
    return value.string;
}

bool boolean(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::boolean) {
        throw JsonError(std::string(name) + " must be a boolean");
    }
    return value.boolean;
}

const Value::Array& array(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::array) {
        throw JsonError(std::string(name) + " must be an array");
    }
    return value.array;
}

std::uint32_t unsigned_integer(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::integer || value.integer < 0
        || value.integer > std::numeric_limits<std::uint32_t>::max()) {
        throw JsonError(std::string(name) + " must be a uint32");
    }
    return static_cast<std::uint32_t>(value.integer);
}

std::int32_t signed_integer(const Value& value, std::string_view name) {
    if (value.kind != Value::Kind::integer
        || value.integer < std::numeric_limits<std::int32_t>::min()
        || value.integer > std::numeric_limits<std::int32_t>::max()) {
        throw JsonError(std::string(name) + " must be an int32");
    }
    return static_cast<std::int32_t>(value.integer);
}

bool is_content_hash(std::string_view value) noexcept {
    if (value.size() != 71 || value.substr(0, 7) != "sha256:") return false;
    return std::all_of(value.begin() + 7, value.end(), [](unsigned char character) {
        return (character >= '0' && character <= '9')
            || (character >= 'a' && character <= 'f');
    });
}

bool is_raw_hash(std::string_view value) noexcept {
    if (value.size() != 64) return false;
    return std::all_of(value.begin(), value.end(), [](unsigned char character) {
        return (character >= '0' && character <= '9')
            || (character >= 'a' && character <= 'f');
    });
}

bool stable_id(std::string_view value, std::string_view prefix) noexcept {
    if (value.size() != prefix.size() + 6 || value.substr(0, prefix.size()) != prefix) {
        return false;
    }
    return std::all_of(value.begin() + static_cast<std::ptrdiff_t>(prefix.size()), value.end(), [](unsigned char character) {
        return character >= '0' && character <= '9';
    });
}

bool exact_reference(
    const Value& value,
    std::string_view id_field,
    std::string_view prefix,
    std::string_view exact_id,
    std::uint32_t exact_revision,
    std::string_view exact_hash = {}
) {
    if (value.kind != Value::Kind::object || value.object.size() != 3
        || value.object.count(std::string(id_field)) != 1
        || value.object.count("revision") != 1
        || value.object.count("content_hash") != 1) {
        return false;
    }
    const auto& identifier = value.object.at(std::string(id_field));
    const auto& revision = value.object.at("revision");
    const auto& hash = value.object.at("content_hash");
    return identifier.kind == Value::Kind::string
        && stable_id(identifier.string, prefix)
        && (exact_id.empty() || identifier.string == exact_id)
        && revision.kind == Value::Kind::integer
        && (
            (exact_revision == 0 && revision.integer >= 1)
            || revision.integer == static_cast<std::int64_t>(exact_revision)
        )
        && hash.kind == Value::Kind::string && is_content_hash(hash.string)
        && (exact_hash.empty() || hash.string == exact_hash);
}

std::string package_digest_input(std::string_view json, std::string_view embedded_hash) {
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

Result failure(ErrorCode code, std::string diagnostic) {
    return {code, std::move(diagnostic)};
}

std::uint32_t aligned(std::uint32_t value, std::uint32_t alignment) {
    return ((value + alignment - 1U) / alignment) * alignment;
}

std::size_t factory_index(const FactoryDescriptor* descriptor) {
    return static_cast<std::size_t>(descriptor - factory_registry().data());
}

std::size_t output_facet_index(
    const FactoryDescriptor& descriptor, std::string_view facet
) {
    for (std::size_t index = 0; index < descriptor.output_count; ++index) {
        if (descriptor.outputs[index].facet_id == facet) return index;
    }
    throw JsonError("unknown source output facet");
}

std::size_t input_facet_index(
    const FactoryDescriptor& descriptor, std::string_view facet
) {
    for (std::size_t index = 0; index < descriptor.input_count; ++index) {
        if (descriptor.inputs[index].facet_id == facet) return index;
    }
    throw JsonError("unknown destination input facet");
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
            "schema_version", "canonical_profile", "derived", "authoritative",
            "content_hash", "runtime_abi", "engine_protocol_abi",
            "factory_registry_version", "numeric_profile", "project_reference",
            "graph_reference", "instrument_reference", "host_build_request_reference",
            "compute_target_reference", "backend_reference", "source_plan_sha256",
            "sample_rate_hz", "max_block_frames", "control_period_frames",
            "block_policy", "input_channels", "output_channels", "latency_frames",
            "tail_frames", "seed", "limits", "memory_plan", "nodes", "connections",
            "schedule", "outputs", "event_contract", "exclusions"
        });
        if (string(member(root, "schema_version"), "schema_version") != kPackageSchema) {
            return failure(ErrorCode::package_schema_unsupported, "HOST_V1_PACKAGE_SCHEMA_UNSUPPORTED");
        }
        PreparedPackage parsed;
        parsed.content_hash = string(member(root, "content_hash"), "content_hash");
        if (!is_content_hash(parsed.content_hash)) {
            return failure(ErrorCode::package_hash_mismatch, "HOST_V1_PACKAGE_HASH_INVALID");
        }
        const auto digest_input = package_digest_input(json, parsed.content_hash);
        if ("sha256:" + sha256_hex(digest_input) != parsed.content_hash
            || (!expected_content_hash.empty()
                && expected_content_hash != parsed.content_hash)) {
            return failure(ErrorCode::package_hash_mismatch, "HOST_V1_PACKAGE_HASH_MISMATCH");
        }
        if (string(member(root, "canonical_profile"), "canonical_profile")
                != "schuss-canonical-json-v1"
            || !boolean(member(root, "derived"), "derived")
            || boolean(member(root, "authoritative"), "authoritative")
            || string(member(root, "runtime_abi"), "runtime_abi") != kRuntimeAbi
            || string(member(root, "engine_protocol_abi"), "engine_protocol_abi")
                != kProtocolAbi
            || string(member(root, "factory_registry_version"), "factory_registry_version")
                != kRegistryVersion
            || string(member(root, "numeric_profile"), "numeric_profile")
                != kNumericProfile
            || string(member(root, "block_policy"), "block_policy")
                != "bounded-variable-with-final-partial") {
            return failure(ErrorCode::runtime_abi_mismatch, "HOST_V1_PACKAGE_BOUNDARY_INVALID");
        }
        if (!exact_reference(member(root, "project_reference"), "project_id", "schuss-project-", "", 0)
            || !exact_reference(member(root, "graph_reference"), "graph_id", "schuss-graph-", "", 0)
            || !exact_reference(member(root, "instrument_reference"), "instrument_id", "schuss-instrument-", "", 0)
            || !exact_reference(member(root, "host_build_request_reference"), "build_request_id", "schuss-build-request-", "", 0)
            || !exact_reference(member(root, "compute_target_reference"), "compute_target_id", "schuss-compute-target-", "schuss-compute-target-000002", 1, "sha256:8e66c6e40db0215c69c44852f6838a289342f372379262b87acc4a2bb49bd290")
            || !exact_reference(member(root, "backend_reference"), "backend_id", "schuss-backend-", "schuss-backend-000003", 1, "sha256:c188a702201625cbf32d49976ce54a06194dea89d3815e972e319f4b6199a116")
            || !is_raw_hash(string(member(root, "source_plan_sha256"), "source_plan_sha256"))) {
            return failure(ErrorCode::package_shape_invalid, "HOST_V1_REFERENCE_CLOSURE_INVALID");
        }
        if (unsigned_integer(member(root, "sample_rate_hz"), "sample_rate_hz") != kSampleRate
            || unsigned_integer(member(root, "max_block_frames"), "max_block_frames") != kMaximumBlockFrames
            || unsigned_integer(member(root, "control_period_frames"), "control_period_frames") != 16
            || unsigned_integer(member(root, "input_channels"), "input_channels") != 0
            || unsigned_integer(member(root, "output_channels"), "output_channels") != 2
            || unsigned_integer(member(root, "latency_frames"), "latency_frames") != 0
            || unsigned_integer(member(root, "tail_frames"), "tail_frames") != 0
            || unsigned_integer(member(root, "seed"), "seed") != 0) {
            return failure(ErrorCode::numeric_profile_unsupported, "HOST_V1_NUMERIC_PROFILE_INVALID");
        }

        const Value& limits = member(root, "limits");
        only_keys(limits, {"node_count", "connection_count", "buffer_count", "state_bytes", "parameter_count", "event_count", "schedule_length"});
        if (unsigned_integer(member(limits, "node_count"), "node limit") != kMaximumNodes
            || unsigned_integer(member(limits, "connection_count"), "connection limit") != kMaximumConnections
            || unsigned_integer(member(limits, "buffer_count"), "buffer limit") != kMaximumBuffers
            || unsigned_integer(member(limits, "state_bytes"), "state limit") != kMaximumStateBytes
            || unsigned_integer(member(limits, "parameter_count"), "parameter limit") != kMaximumParameters
            || unsigned_integer(member(limits, "event_count"), "event limit") != kMaximumEvents
            || unsigned_integer(member(limits, "schedule_length"), "schedule limit") != kMaximumNodes) {
            return failure(ErrorCode::package_shape_invalid, "HOST_V1_LIMITS_INVALID");
        }

        const Value& memory = member(root, "memory_plan");
        only_keys(memory, {"state_bytes", "state_alignment_bytes", "buffer_count", "buffer_frames", "buffer_bytes", "parameter_count", "event_capacity"});
        parsed.state_bytes = unsigned_integer(member(memory, "state_bytes"), "state_bytes");
        parsed.buffer_count = unsigned_integer(member(memory, "buffer_count"), "buffer_count");
        parsed.buffer_frames = unsigned_integer(member(memory, "buffer_frames"), "buffer_frames");
        parsed.parameter_count = unsigned_integer(member(memory, "parameter_count"), "parameter_count");
        parsed.event_capacity = unsigned_integer(member(memory, "event_capacity"), "event_capacity");
        const auto buffer_bytes = unsigned_integer(member(memory, "buffer_bytes"), "buffer_bytes");
        if (parsed.state_bytes == 0 || parsed.state_bytes > kMaximumStateBytes
            || unsigned_integer(member(memory, "state_alignment_bytes"), "state alignment") != 16
            || parsed.buffer_count == 0 || parsed.buffer_count > kMaximumBuffers
            || parsed.buffer_frames != kMaximumBlockFrames
            || buffer_bytes != parsed.buffer_count * parsed.buffer_frames * sizeof(std::int32_t)
            || parsed.parameter_count > kMaximumParameters
            || parsed.event_capacity != kMaximumEvents) {
            return failure(ErrorCode::buffer_plan_invalid, "HOST_V1_MEMORY_PLAN_INVALID");
        }

        const auto& node_values = array(member(root, "nodes"), "nodes");
        if (node_values.size() < 2 || node_values.size() > kMaximumNodes) {
            return failure(ErrorCode::package_shape_invalid, "HOST_V1_NODE_COUNT_INVALID");
        }
        parsed.nodes.reserve(node_values.size());
        std::map<std::string, std::uint8_t> node_indices;
        std::uint32_t expected_state = 0;
        std::uint32_t parameter_total = 0;
        std::size_t output_node_count = 0;
        for (std::size_t index = 0; index < node_values.size(); ++index) {
            const Value& value = node_values[index];
            only_keys(value, {"node_id", "role", "contract_reference", "binding_reference", "factory_id", "inputs", "outputs", "parameters", "state_offset_bytes", "state_size_bytes", "state_alignment_bytes"});
            Node node;
            node.node_id = string(member(value, "node_id"), "node_id");
            if (!stable_id(node.node_id, "graph-node-")
                || !node_indices.emplace(node.node_id, static_cast<std::uint8_t>(index)).second) {
                return failure(ErrorCode::unknown_node, "HOST_V1_NODE_ID_INVALID");
            }
            node.factory_id = string(member(value, "factory_id"), "factory_id");
            const FactoryDescriptor* descriptor = find_factory(node.factory_id);
            if (descriptor == nullptr) {
                return failure(ErrorCode::unknown_factory, "HOST_V1_FACTORY_UNKNOWN");
            }
            node.factory_index = static_cast<std::uint8_t>(factory_index(descriptor));
            node.role = descriptor->role;
            if (string(member(value, "role"), "role") != descriptor->role_name
                || !exact_reference(member(value, "contract_reference"), "component_contract_id", "schuss-component-contract-", descriptor->contract_id, 1, descriptor->contract_hash)
                || !exact_reference(member(value, "binding_reference"), "implementation_id", "schuss-implementation-", descriptor->binding_id, 2, descriptor->binding_hash)) {
                return failure(ErrorCode::unknown_factory, "HOST_V1_FACTORY_IDENTITY_MISMATCH");
            }
            node.contract_id = std::string(descriptor->contract_id);
            node.binding_id = std::string(descriptor->binding_id);

            const auto& inputs = array(member(value, "inputs"), "inputs");
            if (inputs.size() != descriptor->input_count) {
                return failure(ErrorCode::port_contract_invalid, "HOST_V1_INPUT_COUNT_INVALID");
            }
            node.input_count = descriptor->input_count;
            for (std::size_t input_index = 0; input_index < inputs.size(); ++input_index) {
                const Value& input = inputs[input_index];
                Input parsed_input;
                parsed_input.facet_id = string(member(input, "facet_id"), "input facet");
                if (parsed_input.facet_id != descriptor->inputs[input_index].facet_id) {
                    return failure(ErrorCode::port_contract_invalid, "HOST_V1_INPUT_FACET_INVALID");
                }
                const auto& source_kind = string(member(input, "source_kind"), "source_kind");
                if (source_kind == "buffer") {
                    only_keys(input, {"facet_id", "source_kind", "buffer_index"});
                    const auto buffer_index = unsigned_integer(member(input, "buffer_index"), "input buffer");
                    if (buffer_index >= parsed.buffer_count || buffer_index > std::numeric_limits<std::uint8_t>::max()) {
                        return failure(ErrorCode::buffer_plan_invalid, "HOST_V1_INPUT_BUFFER_INVALID");
                    }
                    parsed_input.source = InputSource::buffer;
                    parsed_input.buffer_index = static_cast<std::uint8_t>(buffer_index);
                    parsed_input.fractional_bits = descriptor->inputs[input_index].fractional_bits;
                } else if (source_kind == "constant") {
                    only_keys(input, {"facet_id", "source_kind", "value_q", "fractional_bits"});
                    const auto fractional = unsigned_integer(member(input, "fractional_bits"), "fractional_bits");
                    if (fractional != descriptor->inputs[input_index].fractional_bits) {
                        return failure(ErrorCode::port_contract_invalid, "HOST_V1_INPUT_REPRESENTATION_INVALID");
                    }
                    parsed_input.source = InputSource::constant;
                    parsed_input.value_q = signed_integer(member(input, "value_q"), "constant value");
                    parsed_input.fractional_bits = static_cast<std::uint8_t>(fractional);
                } else {
                    return failure(ErrorCode::port_contract_invalid, "HOST_V1_INPUT_SOURCE_INVALID");
                }
                node.inputs[input_index] = std::move(parsed_input);
            }

            const auto& outputs = array(member(value, "outputs"), "outputs");
            if (outputs.size() != descriptor->output_count) {
                return failure(ErrorCode::port_contract_invalid, "HOST_V1_OUTPUT_COUNT_INVALID");
            }
            node.output_count = descriptor->output_count;
            for (std::size_t output_index = 0; output_index < outputs.size(); ++output_index) {
                const Value& output = outputs[output_index];
                only_keys(output, {"facet_id", "buffer_index"});
                node.outputs[output_index].facet_id = string(member(output, "facet_id"), "output facet");
                const auto buffer_index = unsigned_integer(member(output, "buffer_index"), "output buffer");
                if (node.outputs[output_index].facet_id != descriptor->outputs[output_index].facet_id
                    || buffer_index >= parsed.buffer_count || buffer_index > std::numeric_limits<std::uint8_t>::max()) {
                    return failure(ErrorCode::buffer_plan_invalid, "HOST_V1_OUTPUT_BUFFER_INVALID");
                }
                node.outputs[output_index].buffer_index = static_cast<std::uint8_t>(buffer_index);
            }

            const auto& parameters = array(member(value, "parameters"), "parameters");
            if (parameters.size() != descriptor->parameter_count) {
                return failure(ErrorCode::port_contract_invalid, "HOST_V1_PARAMETER_COUNT_INVALID");
            }
            node.parameter_count = descriptor->parameter_count;
            parameter_total += descriptor->parameter_count;
            for (std::size_t parameter_index = 0; parameter_index < parameters.size(); ++parameter_index) {
                const Value& parameter = parameters[parameter_index];
                only_keys(parameter, {"facet_id", "value_q"});
                node.parameters[parameter_index].facet_id = string(member(parameter, "facet_id"), "parameter facet");
                node.parameters[parameter_index].value_q = signed_integer(member(parameter, "value_q"), "parameter value");
                if (node.parameters[parameter_index].facet_id != descriptor->parameters[parameter_index]) {
                    return failure(ErrorCode::port_contract_invalid, "HOST_V1_PARAMETER_FACET_INVALID");
                }
            }

            node.state_size_bytes = unsigned_integer(member(value, "state_size_bytes"), "state size");
            node.state_alignment_bytes = static_cast<std::uint8_t>(unsigned_integer(member(value, "state_alignment_bytes"), "state alignment"));
            node.state_offset_bytes = unsigned_integer(member(value, "state_offset_bytes"), "state offset");
            expected_state = aligned(expected_state, descriptor->state_alignment_bytes);
            if (node.state_size_bytes != descriptor->state_size_bytes
                || node.state_alignment_bytes != descriptor->state_alignment_bytes
                || node.state_offset_bytes != expected_state
                || node.state_offset_bytes + node.state_size_bytes > parsed.state_bytes) {
                return failure(ErrorCode::state_plan_invalid, "HOST_V1_NODE_STATE_PLAN_INVALID");
            }
            expected_state += node.state_size_bytes;
            if (node.role == Role::output) ++output_node_count;
            parsed.nodes.push_back(std::move(node));
        }
        expected_state = std::max<std::uint32_t>(16, aligned(expected_state, 16));
        if (expected_state != parsed.state_bytes || parameter_total != parsed.parameter_count) {
            return failure(ErrorCode::state_plan_invalid, "HOST_V1_AGGREGATE_PLAN_INVALID");
        }
        if (output_node_count != 1) {
            return failure(ErrorCode::port_contract_invalid, "HOST_V1_STEREO_OUTPUT_COUNT_INVALID");
        }

        const auto& schedule = array(member(root, "schedule"), "schedule");
        if (schedule.size() != parsed.nodes.size()) {
            return failure(ErrorCode::schedule_invalid, "HOST_V1_SCHEDULE_COUNT_INVALID");
        }
        parsed.schedule.reserve(schedule.size());
        for (std::size_t index = 0; index < schedule.size(); ++index) {
            const auto& node_id = string(schedule[index], "schedule node");
            if (node_id != parsed.nodes[index].node_id) {
                return failure(ErrorCode::schedule_invalid, "HOST_V1_NODE_SEQUENCE_NOT_SCHEDULE");
            }
            parsed.schedule.push_back(static_cast<std::uint8_t>(index));
        }

        const auto& connections = array(member(root, "connections"), "connections");
        if (connections.empty() || connections.size() > kMaximumConnections) {
            return failure(ErrorCode::package_shape_invalid, "HOST_V1_CONNECTION_COUNT_INVALID");
        }
        parsed.connection_count = static_cast<std::uint32_t>(connections.size());
        std::set<std::string> connection_ids;
        std::set<std::pair<std::size_t, std::size_t>> driven_inputs;
        std::set<std::pair<std::size_t, std::size_t>> used_outputs;
        std::vector<std::set<std::size_t>> adjacency(parsed.nodes.size());
        std::vector<std::size_t> indegree(parsed.nodes.size(), 0);
        std::map<std::pair<std::size_t, std::size_t>, std::size_t> last_use;
        for (const Value& connection : connections) {
            only_keys(connection, {"connection_id", "source", "destination", "buffer_index"});
            const auto& connection_id = string(member(connection, "connection_id"), "connection_id");
            if (!stable_id(connection_id, "graph-connection-")
                || !connection_ids.emplace(connection_id).second) {
                return failure(ErrorCode::port_contract_invalid, "HOST_V1_CONNECTION_ID_INVALID");
            }
            const Value& source = member(connection, "source");
            const Value& target = member(connection, "destination");
            only_keys(source, {"node_id", "facet_id"});
            only_keys(target, {"node_id", "facet_id"});
            const auto source_node = node_indices.find(string(member(source, "node_id"), "source node"));
            const auto target_node = node_indices.find(string(member(target, "node_id"), "destination node"));
            if (source_node == node_indices.end() || target_node == node_indices.end()) {
                return failure(ErrorCode::unknown_node, "HOST_V1_CONNECTION_NODE_UNKNOWN");
            }
            const std::size_t source_index = source_node->second;
            const std::size_t target_index = target_node->second;
            const auto& source_descriptor = factory_registry()[parsed.nodes[source_index].factory_index];
            const auto& target_descriptor = factory_registry()[parsed.nodes[target_index].factory_index];
            const std::size_t output_index = output_facet_index(source_descriptor, string(member(source, "facet_id"), "source facet"));
            const std::size_t input_index = input_facet_index(target_descriptor, string(member(target, "facet_id"), "destination facet"));
            const auto buffer_index = unsigned_integer(member(connection, "buffer_index"), "connection buffer");
            if (source_descriptor.outputs[output_index].fractional_bits
                    != target_descriptor.inputs[input_index].fractional_bits
                || buffer_index != parsed.nodes[source_index].outputs[output_index].buffer_index
                || parsed.nodes[target_index].inputs[input_index].source != InputSource::buffer
                || buffer_index != parsed.nodes[target_index].inputs[input_index].buffer_index
                || !driven_inputs.emplace(target_index, input_index).second) {
                return failure(ErrorCode::port_contract_invalid, "HOST_V1_CONNECTION_DRIVER_INVALID");
            }
            used_outputs.emplace(source_index, output_index);
            last_use[{source_index, output_index}] = std::max(
                last_use[{source_index, output_index}], target_index
            );
            if (adjacency[source_index].emplace(target_index).second) {
                ++indegree[target_index];
            }
        }
        for (std::size_t node_index = 0; node_index < parsed.nodes.size(); ++node_index) {
            const Node& node = parsed.nodes[node_index];
            for (std::size_t input_index = 0; input_index < node.input_count; ++input_index) {
                const bool connected = driven_inputs.count({node_index, input_index}) != 0;
                if ((node.inputs[input_index].source == InputSource::buffer) != connected) {
                    return failure(ErrorCode::port_contract_invalid, "HOST_V1_INPUT_DRIVER_CLOSURE_INVALID");
                }
            }
            for (std::size_t output_index = 0; output_index < node.output_count; ++output_index) {
                if (used_outputs.count({node_index, output_index}) == 0) {
                    return failure(ErrorCode::port_contract_invalid, "HOST_V1_OUTPUT_DISCONNECTED");
                }
            }
        }

        std::set<std::string> ready;
        for (std::size_t index = 0; index < parsed.nodes.size(); ++index) {
            if (indegree[index] == 0) ready.emplace(parsed.nodes[index].node_id);
        }
        std::vector<std::string> derived_schedule;
        while (!ready.empty()) {
            const std::string node_id = *ready.begin();
            ready.erase(ready.begin());
            derived_schedule.push_back(node_id);
            const std::size_t index = node_indices.at(node_id);
            for (const std::size_t target : adjacency[index]) {
                if (--indegree[target] == 0) ready.emplace(parsed.nodes[target].node_id);
            }
        }
        if (derived_schedule.size() != parsed.nodes.size()) {
            return failure(ErrorCode::cycle_detected, "HOST_V1_GRAPH_CYCLE");
        }
        for (std::size_t index = 0; index < derived_schedule.size(); ++index) {
            if (derived_schedule[index] != parsed.nodes[index].node_id) {
                return failure(ErrorCode::schedule_invalid, "HOST_V1_SCHEDULE_TIE_BREAK_INVALID");
            }
        }

        std::map<std::pair<std::size_t, std::size_t>, std::uint8_t> active_buffers;
        std::set<std::uint8_t> free_buffers;
        std::uint32_t next_buffer = 0;
        for (std::size_t node_index = 0; node_index < parsed.nodes.size(); ++node_index) {
            for (auto iterator = active_buffers.begin(); iterator != active_buffers.end();) {
                if (last_use.at(iterator->first) < node_index) {
                    free_buffers.emplace(iterator->second);
                    iterator = active_buffers.erase(iterator);
                } else {
                    ++iterator;
                }
            }
            const Node& node = parsed.nodes[node_index];
            for (std::size_t output_index = 0; output_index < node.output_count; ++output_index) {
                std::uint8_t expected_buffer{};
                if (!free_buffers.empty()) {
                    expected_buffer = *free_buffers.begin();
                    free_buffers.erase(free_buffers.begin());
                } else {
                    expected_buffer = static_cast<std::uint8_t>(next_buffer++);
                }
                if (node.outputs[output_index].buffer_index != expected_buffer) {
                    return failure(ErrorCode::buffer_plan_invalid, "HOST_V1_BUFFER_REUSE_PLAN_INVALID");
                }
                active_buffers[{node_index, output_index}] = expected_buffer;
            }
        }
        if (next_buffer != parsed.buffer_count) {
            return failure(ErrorCode::buffer_plan_invalid, "HOST_V1_BUFFER_COUNT_NOT_MINIMAL");
        }

        const Value& outputs = member(root, "outputs");
        only_keys(outputs, {"node_id", "left_buffer", "right_buffer"});
        const auto output_node = node_indices.find(string(member(outputs, "node_id"), "output node"));
        const auto left = unsigned_integer(member(outputs, "left_buffer"), "left buffer");
        const auto right = unsigned_integer(member(outputs, "right_buffer"), "right buffer");
        if (output_node == node_indices.end()
            || parsed.nodes[output_node->second].role != Role::output
            || parsed.nodes[output_node->second].input_count != 2
            || parsed.nodes[output_node->second].inputs[0].source != InputSource::buffer
            || parsed.nodes[output_node->second].inputs[1].source != InputSource::buffer
            || left != parsed.nodes[output_node->second].inputs[0].buffer_index
            || right != parsed.nodes[output_node->second].inputs[1].buffer_index
            || left >= parsed.buffer_count || right >= parsed.buffer_count) {
            return failure(ErrorCode::buffer_plan_invalid, "HOST_V1_FINAL_OUTPUT_INVALID");
        }
        parsed.left_buffer = static_cast<std::uint8_t>(left);
        parsed.right_buffer = static_cast<std::uint8_t>(right);

        const Value& event = member(root, "event_contract");
        only_keys(event, {"capacity", "ordering", "accepted_kinds", "overflow_policy"});
        std::set<std::string> event_kinds;
        for (const Value& item : array(member(event, "accepted_kinds"), "accepted kinds")) {
            event_kinds.emplace(string(item, "accepted kind"));
        }
        if (unsigned_integer(member(event, "capacity"), "event capacity") != parsed.event_capacity
            || string(member(event, "ordering"), "event ordering") != "frame-offset-then-sequence"
            || string(member(event, "overflow_policy"), "overflow policy") != "drop-newest-and-count"
            || event_kinds != std::set<std::string>{"midi-message", "parameter-q27"}) {
            return failure(ErrorCode::event_contract_invalid, "HOST_V1_EVENT_CONTRACT_INVALID");
        }
        std::set<std::string> exclusions;
        for (const Value& item : array(member(root, "exclusions"), "exclusions")) {
            exclusions.emplace(string(item, "exclusion"));
        }
        const std::set<std::string> expected_exclusions{
            "JUCE dependency in schuss_rt", "Ksoloti equivalence claim",
            "cycles and implicit delay", "dynamic graph mutation on callback",
            "implicit stream conversion", "state migration during replacement",
            "unsupported factories outside Task 031 seven"
        };
        if (exclusions != expected_exclusions) {
            return failure(ErrorCode::package_shape_invalid, "HOST_V1_EXCLUSIONS_INVALID");
        }
        destination = std::move(parsed);
        return {};
    } catch (const JsonError& error) {
        return failure(ErrorCode::json_invalid, std::string("HOST_V1_PACKAGE_JSON_INVALID: ") + error.what());
    } catch (const std::exception& error) {
        return failure(ErrorCode::package_shape_invalid, std::string("HOST_V1_PACKAGE_INVALID: ") + error.what());
    }
}

}  // namespace schuss::rt::v1
