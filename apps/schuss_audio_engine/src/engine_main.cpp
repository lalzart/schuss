#include "schuss_rt/runtime.hpp"
#include "schuss_rt/runtime_replacement.hpp"
#include "schuss_rt/runtime_v1.hpp"
#include "midi_ingress.hpp"

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_core/juce_core.h>
#include <juce_events/juce_events.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <memory>
#include <optional>
#include <sstream>
#include <thread>
#include <string>
#include <string_view>
#include <vector>

namespace {

enum class RuntimeVersion : std::uint8_t { none, v0, v1 };

constexpr std::string_view kProtocolV0 = "schuss-audio-engine-protocol-v0";
constexpr std::string_view kProtocolV1 = "schuss-audio-engine-protocol-v1";

std::string escaped(std::string_view value) {
    std::string result;
    for (const unsigned char character : value) {
        switch (character) {
            case '"': result += "\\\""; break;
            case '\\': result += "\\\\"; break;
            case '\n': result += "\\n"; break;
            case '\r': result += "\\r"; break;
            case '\t': result += "\\t"; break;
            default:
                if (character >= 0x20U) result.push_back(static_cast<char>(character));
        }
    }
    return result;
}

std::optional<std::string> text_member(const std::string& json, std::string_view key) {
    const std::string marker = "\"" + std::string(key) + "\":\"";
    const auto begin = json.find(marker);
    if (begin == std::string::npos) return std::nullopt;
    std::string result;
    bool escaped_character = false;
    for (std::size_t index = begin + marker.size(); index < json.size(); ++index) {
        const char character = json[index];
        if (escaped_character) {
            switch (character) {
                case 'n': result.push_back('\n'); break;
                case 'r': result.push_back('\r'); break;
                case 't': result.push_back('\t'); break;
                default: result.push_back(character); break;
            }
            escaped_character = false;
        } else if (character == '\\') {
            escaped_character = true;
        } else if (character == '"') {
            return result;
        } else {
            result.push_back(character);
        }
    }
    return std::nullopt;
}

std::optional<std::uint32_t> integer_member(const std::string& json, std::string_view key) {
    const std::string marker = "\"" + std::string(key) + "\":";
    const auto begin = json.find(marker);
    if (begin == std::string::npos) return std::nullopt;
    std::uint64_t value = 0;
    std::size_t index = begin + marker.size();
    const std::size_t digit_begin = index;
    while (index < json.size() && json[index] >= '0' && json[index] <= '9') {
        value = value * 10U + static_cast<unsigned>(json[index] - '0');
        if (value > std::numeric_limits<std::uint32_t>::max()) return std::nullopt;
        ++index;
    }
    if (index == digit_begin) return std::nullopt;
    return static_cast<std::uint32_t>(value);
}

std::string read_text(const std::string& path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("ENGINE_PACKAGE_READ_FAILED");
    return {std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>()};
}

std::string response(
    const std::string& message_id,
    std::string_view protocol,
    std::string_view status,
    std::string value,
    std::string diagnostics = "[]"
) {
    return "{\"diagnostics\":" + diagnostics + ",\"message_id\":\"" + escaped(message_id)
        + "\",\"protocol_abi\":\"" + std::string(protocol) + "\",\"status\":\""
        + std::string(status) + "\",\"value\":" + std::move(value) + "}";
}

std::string failure(
    const std::string& message_id,
    std::string_view protocol,
    std::string_view code,
    std::string_view message
) {
    return response(
        message_id,
        protocol,
        "failed",
        "null",
        "[{\"code\":\"" + std::string(code) + "\",\"message\":\"" + escaped(message)
            + "\",\"severity\":\"error\"}]"
    );
}

class HeadlessEngine final : public juce::AudioIODeviceCallback, public juce::MidiInputCallback {
public:
    ~HeadlessEngine() override { static_cast<void>(stop_unchecked()); }

    std::string inspect_devices() {
        juce::AudioDeviceManager probe;
        device_types_.clear(true);
        probe.createAudioDeviceTypes(device_types_);
        std::vector<std::string> audio;
        for (auto* type : device_types_) {
            type->scanForDevices();
            for (const auto& name : type->getDeviceNames(false)) {
                audio.push_back("{\"device_type\":\"" + escaped(type->getTypeName().toStdString())
                    + "\",\"name\":\"" + escaped(name.toStdString()) + "\"}");
            }
        }
        std::sort(audio.begin(), audio.end());
        std::vector<std::string> midi;
        for (const auto& device : juce::MidiInput::getAvailableDevices()) {
            midi.push_back("{\"identifier\":\"" + escaped(device.identifier.toStdString())
                + "\",\"name\":\"" + escaped(device.name.toStdString()) + "\"}");
        }
        std::sort(midi.begin(), midi.end());
        return "{\"audio_devices\":[" + joined(audio) + "],\"midi_inputs\":[" + joined(midi) + "]}";
    }

    std::string prepare(
        RuntimeVersion version,
        const std::string& path,
        const std::string& expected_hash
    ) {
        if (active_.load(std::memory_order_acquire)) throw std::runtime_error("ENGINE_SESSION_ACTIVE");
        if (version == RuntimeVersion::v0) {
            v1_slot_.clear_after_callback_stopped();
            schuss::rt::PreparedPackage package;
            const auto parsed = schuss::rt::parse_package(
                read_text(path), expected_hash, package
            );
            if (!parsed) throw std::runtime_error(parsed.diagnostic);
            const auto result = runtime_v0_.prepare(package);
            if (!result) throw std::runtime_error(result.diagnostic);
            package_hash_v0_ = package.content_hash;
        } else if (version == RuntimeVersion::v1) {
            v1_slot_.clear_after_callback_stopped();
            schuss::rt::v1::PreparedPackage package;
            const auto parsed = schuss::rt::v1::parse_package(
                read_text(path), expected_hash, package
            );
            if (!parsed) throw std::runtime_error(parsed.diagnostic);
            auto runtime = std::make_unique<schuss::rt::v1::Runtime>();
            const auto prepared = runtime->prepare(package);
            if (!prepared) throw std::runtime_error(prepared.diagnostic);
            const auto installed = v1_slot_.install_initial(
                std::move(runtime), package.content_hash
            );
            if (!installed) throw std::runtime_error(installed.code);
        } else {
            throw std::runtime_error("ENGINE_PROTOCOL_NOT_NEGOTIATED");
        }
        runtime_version_ = version;
        prepared_.store(true, std::memory_order_release);
        return "{\"package_content_hash\":\"" + escaped(package_hash())
            + "\",\"runtime_abi\":\"" + std::string(runtime_abi()) + "\"}";
    }

    std::string start(
        RuntimeVersion version,
        std::uint32_t sample_rate,
        std::uint32_t block_frames
    ) {
        if (!prepared_.load(std::memory_order_acquire)) throw std::runtime_error("ENGINE_PACKAGE_NOT_PREPARED");
        if (runtime_version_ != version) throw std::runtime_error("ENGINE_SESSION_ABI_MISMATCH");
        if (active_.load(std::memory_order_acquire)) throw std::runtime_error("ENGINE_SESSION_ALREADY_ACTIVE");
        if (sample_rate != 48000 || block_frames == 0 || block_frames > 512) throw std::runtime_error("ENGINE_CONFIGURATION_UNSUPPORTED");

        const auto initial = devices_.initialiseWithDefaultDevices(0, 2);
        if (initial.isNotEmpty()) throw std::runtime_error("ENGINE_AUDIO_OPEN_FAILED: " + initial.toStdString());
        auto setup = devices_.getAudioDeviceSetup();
        setup.sampleRate = static_cast<double>(sample_rate);
        setup.bufferSize = static_cast<int>(block_frames);
        const auto configured = devices_.setAudioDeviceSetup(setup, true);
        if (configured.isNotEmpty()) {
            devices_.closeAudioDevice();
            throw std::runtime_error("ENGINE_AUDIO_CONFIGURE_FAILED: " + configured.toStdString());
        }
        auto* device = devices_.getCurrentAudioDevice();
        if (device == nullptr || static_cast<std::uint32_t>(device->getCurrentSampleRate()) != sample_rate
            || device->getCurrentBufferSizeSamples() < 1 || device->getCurrentBufferSizeSamples() > 512) {
            devices_.closeAudioDevice();
            throw std::runtime_error("ENGINE_AUDIO_CONFIGURATION_NOT_EXACT");
        }
        active_sample_rate_ = static_cast<std::uint32_t>(device->getCurrentSampleRate());
        active_block_frames_ = static_cast<std::uint32_t>(device->getCurrentBufferSizeSamples());
        active_device_name_ = device->getName().toStdString();
        if (runtime_version_ == RuntimeVersion::v0) {
            runtime_v0_.reset();
        } else {
            auto* runtime = v1_slot_.active();
            if (runtime == nullptr) throw std::runtime_error("ENGINE_PACKAGE_NOT_PREPARED");
            runtime->reset();
        }
        midi_ingress_.reset();
        midi_sequence_.store(0, std::memory_order_relaxed);
        maximum_callback_us_.store(0, std::memory_order_relaxed);
        xruns_.store(0, std::memory_order_relaxed);
        device_disconnects_.store(0, std::memory_order_relaxed);
        active_.store(true, std::memory_order_release);
        devices_.addAudioCallback(this);
        for (const auto& info : juce::MidiInput::getAvailableDevices()) {
            auto input = juce::MidiInput::openDevice(info.identifier, this);
            if (input) {
                input->start();
                midi_inputs_.push_back(std::move(input));
                break;
            }
        }
        return session_value();
    }

    std::string inspect(RuntimeVersion version) const {
        require_version(version);
        return session_value();
    }

    std::string stop(RuntimeVersion version) {
        require_version(version);
        return stop_unchecked();
    }

private:
    std::string stop_unchecked() {
        const bool was_active = active_.exchange(false, std::memory_order_acq_rel);
        for (auto& input : midi_inputs_) input->stop();
        midi_inputs_.clear();
        if (was_active) devices_.removeAudioCallback(this);
        devices_.closeAudioDevice();
        settle_replacement_after_callback();
        return session_value();
    }

public:

    std::string prepare_replacement(
        std::uint64_t expected_generation,
        const std::string& expected_active_hash,
        const std::string& path,
        const std::string& expected_successor_hash
    ) {
        require_active_v1();
        schuss::rt::v1::PreparedPackage package;
        const auto parsed = schuss::rt::v1::parse_package(
            read_text(path), expected_successor_hash, package
        );
        if (!parsed) throw std::runtime_error(parsed.diagnostic);
        auto runtime = std::make_unique<schuss::rt::v1::Runtime>();
        const auto prepared = runtime->prepare(package);
        if (!prepared) throw std::runtime_error(prepared.diagnostic);
        runtime->reset();
        const auto retained = v1_slot_.prepare_successor(
            std::move(runtime),
            package.content_hash,
            expected_generation,
            expected_active_hash
        );
        if (!retained) throw std::runtime_error(retained.code);
        return "{\"active_package_content_hash\":\"" + escaped(v1_slot_.active_hash())
            + "\",\"engine_generation\":" + std::to_string(v1_slot_.generation())
            + ",\"pending_package_content_hash\":\"" + escaped(v1_slot_.pending_hash())
            + "\",\"runtime_abi\":\"schuss-rt-abi-v1\"}";
    }

    std::string activate_replacement(
        std::uint64_t expected_generation,
        const std::string& expected_active_hash,
        const std::string& expected_successor_hash
    ) {
        require_active_v1();
        const auto requested = v1_slot_.request_activation(
            expected_generation,
            expected_active_hash,
            expected_successor_hash
        );
        if (!requested) throw std::runtime_error(requested.code);

        const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(2);
        while (!v1_slot_.activation_observed()
            && active_.load(std::memory_order_acquire)
            && std::chrono::steady_clock::now() < deadline) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        if (!v1_slot_.activation_observed()) {
            const auto cancelled = v1_slot_.cancel_pending();
            if (!cancelled && v1_slot_.activation_observed()) {
                return complete_replacement();
            }
            throw std::runtime_error("HOST_V1_REPLACEMENT_ACTIVATION_TIMEOUT");
        }
        return complete_replacement();
    }

    std::string cancel_replacement(
        std::uint64_t expected_generation,
        const std::string& expected_active_hash,
        const std::string& expected_successor_hash
    ) {
        require_v1();
        if (v1_slot_.generation() != expected_generation) {
            throw std::runtime_error("HOST_V1_REPLACEMENT_GENERATION_STALE");
        }
        if (v1_slot_.active_hash() != expected_active_hash) {
            throw std::runtime_error("HOST_V1_REPLACEMENT_ACTIVE_HASH_STALE");
        }
        if (v1_slot_.pending_hash() != expected_successor_hash) {
            throw std::runtime_error("HOST_V1_REPLACEMENT_SUCCESSOR_HASH_STALE");
        }
        const auto cancelled = v1_slot_.cancel_pending();
        if (!cancelled) throw std::runtime_error(cancelled.code);
        return "{\"active_package_content_hash\":\"" + escaped(v1_slot_.active_hash())
            + "\",\"engine_generation\":" + std::to_string(v1_slot_.generation())
            + ",\"pending\":false}";
    }

    void audioDeviceIOCallbackWithContext(
        const float* const*, int, float* const* output_channel_data,
        int output_channels, int frames,
        const juce::AudioIODeviceCallbackContext&
    ) override {
        const auto begin = std::chrono::steady_clock::now();
        if (!active_.load(std::memory_order_acquire) || frames < 1 || frames > 512) {
            for (int channel = 0; channel < output_channels; ++channel) {
                if (output_channel_data[channel] != nullptr) std::fill_n(output_channel_data[channel], std::max(frames, 0), 0.0F);
            }
            if (frames > 512) xruns_.fetch_add(1, std::memory_order_relaxed);
            return;
        }
        const auto block_start_ns = static_cast<std::uint64_t>(
            juce::Time::getMillisecondCounterHiRes() * 1000000.0
        );
        schuss::rt::v1::Runtime* runtime_v1 = nullptr;
        if (runtime_version_ == RuntimeVersion::v1) {
            runtime_v1 = v1_slot_.begin_block();
            if (runtime_v1 == nullptr) {
                for (int channel = 0; channel < output_channels; ++channel) {
                    if (output_channel_data[channel] != nullptr) {
                        std::fill_n(output_channel_data[channel], frames, 0.0F);
                    }
                }
                xruns_.fetch_add(1, std::memory_order_relaxed);
                return;
            }
        }
        schuss::engine::StampedMidi incoming;
        while (midi_ingress_.pop(incoming)) {
            schuss::rt::Event event;
            event.kind = schuss::rt::EventKind::midi_message;
            event.sequence = incoming.sequence;
            const auto delta_ns = incoming.timestamp_ns > block_start_ns
                ? incoming.timestamp_ns - block_start_ns
                : 0U;
            const auto offset = delta_ns > std::numeric_limits<std::uint64_t>::max() / active_sample_rate_
                ? static_cast<std::uint64_t>(frames - 1)
                : (delta_ns * active_sample_rate_) / 1000000000U;
            event.frame_offset = static_cast<std::uint32_t>(
                std::min<std::uint64_t>(offset, static_cast<std::uint64_t>(frames - 1))
            );
            event.midi = incoming.bytes;
            event.midi_size = incoming.size;
            if (runtime_v1 != nullptr) {
                runtime_v1->enqueue(event);
            } else {
                runtime_v0_.enqueue(event);
            }
        }
        const auto processed = runtime_v1 != nullptr
            ? runtime_v1->process(
                left_.data(), right_.data(), static_cast<std::uint32_t>(frames)
            )
            : runtime_v0_.process(
                left_.data(), right_.data(), static_cast<std::uint32_t>(frames)
            );
        constexpr float scale = 1.0F / static_cast<float>(1 << 27);
        for (int channel = 0; channel < output_channels; ++channel) {
            float* output = output_channel_data[channel];
            if (output == nullptr) continue;
            const auto& source = channel == 0 ? left_ : right_;
            if (!processed) {
                std::fill_n(output, frames, 0.0F);
            } else {
                for (int frame = 0; frame < frames; ++frame) output[frame] = static_cast<float>(source[static_cast<std::size_t>(frame)]) * scale;
            }
        }
        const auto elapsed_count = std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::steady_clock::now() - begin
        ).count();
        const auto elapsed = elapsed_count > 0
            ? static_cast<std::uint64_t>(elapsed_count)
            : std::uint64_t{0};
        auto observed = maximum_callback_us_.load(std::memory_order_relaxed);
        while (elapsed > observed
            && !maximum_callback_us_.compare_exchange_weak(
                observed, elapsed, std::memory_order_relaxed
            )) {}
    }

    void audioDeviceAboutToStart(juce::AudioIODevice*) override {}
    void audioDeviceStopped() override {
        if (active_.exchange(false, std::memory_order_acq_rel)) {
            device_disconnects_.fetch_add(1, std::memory_order_relaxed);
        }
    }
    void audioDeviceError(const juce::String&) override {
        xruns_.fetch_add(1, std::memory_order_relaxed);
        device_disconnects_.fetch_add(1, std::memory_order_relaxed);
        active_.store(false, std::memory_order_release);
    }

    void handleIncomingMidiMessage(juce::MidiInput*, const juce::MidiMessage& message) override {
        const int size = message.getRawDataSize();
        schuss::engine::StampedMidi incoming;
        incoming.timestamp_ns = static_cast<std::uint64_t>(
            message.getTimeStamp() * 1000000000.0
        );
        incoming.sequence = midi_sequence_.fetch_add(1, std::memory_order_relaxed);
        incoming.size = size >= 1 && size <= 3 ? static_cast<std::uint8_t>(size) : 0U;
        for (std::uint8_t index = 0; index < incoming.size; ++index) {
            incoming.bytes[index] = message.getRawData()[index];
        }
        midi_ingress_.enqueue(incoming);
    }

private:
    static std::string joined(const std::vector<std::string>& values) {
        std::string result;
        for (std::size_t index = 0; index < values.size(); ++index) {
            if (index) result.push_back(',');
            result += values[index];
        }
        return result;
    }

    void require_v1() const {
        if (runtime_version_ != RuntimeVersion::v1
            || !prepared_.load(std::memory_order_acquire)
            || v1_slot_.active() == nullptr) {
            throw std::runtime_error("ENGINE_V1_SESSION_REQUIRED");
        }
    }

    void require_version(RuntimeVersion version) const {
        if (runtime_version_ != version) {
            throw std::runtime_error("ENGINE_SESSION_ABI_MISMATCH");
        }
    }

    void require_active_v1() const {
        require_v1();
        if (!active_.load(std::memory_order_acquire)) {
            throw std::runtime_error("ENGINE_SESSION_NOT_ACTIVE");
        }
    }

    std::string_view runtime_abi() const noexcept {
        return runtime_version_ == RuntimeVersion::v1
            ? schuss::rt::v1::kRuntimeAbi
            : schuss::rt::kRuntimeAbi;
    }

    const std::string& package_hash() const noexcept {
        return runtime_version_ == RuntimeVersion::v1
            ? v1_slot_.active_hash()
            : package_hash_v0_;
    }

    std::string complete_replacement() {
        schuss::rt::v1::ReplacementTelemetry telemetry;
        const auto completed = v1_slot_.complete_activation(telemetry);
        if (!completed) throw std::runtime_error(completed.code);
        return "{\"active\":true,\"activation_boundary\":\""
            + std::string(telemetry.activation_boundary)
            + "\",\"engine_generation\":"
            + std::to_string(telemetry.activation_generation)
            + ",\"old_package_content_hash\":\""
            + escaped(telemetry.old_package_content_hash)
            + "\",\"package_content_hash\":\""
            + escaped(telemetry.new_package_content_hash)
            + "\",\"reset_state\":true,\"retired_runtime_reclaimed_off_callback\":true}";
    }

    void settle_replacement_after_callback() {
        if (runtime_version_ != RuntimeVersion::v1 || !v1_slot_.has_pending()) return;
        if (v1_slot_.activation_observed()) {
            schuss::rt::v1::ReplacementTelemetry telemetry;
            static_cast<void>(v1_slot_.complete_activation(telemetry));
            return;
        }
        static_cast<void>(v1_slot_.cancel_pending());
    }

    std::string session_value() const {
        const auto* runtime_v1 = runtime_version_ == RuntimeVersion::v1
            ? v1_slot_.active()
            : nullptr;
        const auto metrics = runtime_v1 != nullptr
            ? runtime_v1->metrics()
            : runtime_v0_.metrics();
        const auto callback_us = maximum_callback_us_.load(std::memory_order_relaxed);
        const std::uint64_t block_us = active_sample_rate_ == 0 ? 0 : (static_cast<std::uint64_t>(active_block_frames_) * 1000000U) / active_sample_rate_;
        std::ostringstream ratio;
        ratio.setf(std::ios::fixed);
        ratio.precision(6);
        ratio << (block_us == 0 ? 0.0 : static_cast<double>(callback_us) / static_cast<double>(block_us));
        return "{\"active\":" + std::string(active_.load(std::memory_order_acquire) ? "true" : "false")
            + ",\"block_frames\":" + std::to_string(active_block_frames_)
            + ",\"callback_cpu_ratio_max\":\"" + ratio.str() + "\",\"callback_duration_us_max\":"
            + std::to_string(callback_us) + ",\"device_disconnects\":"
            + std::to_string(device_disconnects_.load(std::memory_order_relaxed))
            + ",\"device_name\":\"" + escaped(active_device_name_)
            + "\",\"midi_events_delivered\":" + std::to_string(metrics.events_delivered)
            + ",\"midi_inputs_open\":" + std::to_string(midi_inputs_.size())
            + ",\"package_content_hash\":\"" + escaped(package_hash()) + "\",\"processed_frames\":"
            + std::to_string(metrics.processed_frames) + ",\"queue_overflows\":"
            + std::to_string(metrics.queue_overflows + midi_ingress_.overflows()) + ",\"sample_rate_hz\":"
            + std::to_string(active_sample_rate_) + ",\"xruns\":"
            + std::to_string(xruns_.load(std::memory_order_relaxed))
            + (runtime_version_ == RuntimeVersion::v1
                ? ",\"engine_generation\":" + std::to_string(v1_slot_.generation())
                : std::string{})
            + "}";
    }

    juce::AudioDeviceManager devices_;
    juce::OwnedArray<juce::AudioIODeviceType> device_types_;
    std::vector<std::unique_ptr<juce::MidiInput>> midi_inputs_;
    schuss::engine::MidiIngressQueue<1024> midi_ingress_;
    schuss::rt::Runtime runtime_v0_;
    schuss::rt::v1::RuntimeReplacementSlot v1_slot_;
    std::array<std::int32_t, 512> left_{};
    std::array<std::int32_t, 512> right_{};
    std::atomic<bool> prepared_{false};
    std::atomic<bool> active_{false};
    std::atomic<std::uint64_t> midi_sequence_{0};
    std::atomic<std::uint64_t> maximum_callback_us_{0};
    std::atomic<std::uint64_t> xruns_{0};
    std::atomic<std::uint64_t> device_disconnects_{0};
    std::string package_hash_v0_;
    std::string active_device_name_;
    RuntimeVersion runtime_version_{RuntimeVersion::none};
    std::uint32_t active_sample_rate_{};
    std::uint32_t active_block_frames_{};
};

}  // namespace

int main() {
    juce::ScopedJuceInitialiser_GUI juce_scope;
    HeadlessEngine engine;
    std::string line;
    while (std::getline(std::cin, line)) {
        const auto message_id = text_member(line, "message_id").value_or("engine-message-000000");
        const auto schema = text_member(line, "schema_version");
        const auto protocol = text_member(line, "protocol_abi");
        RuntimeVersion version = RuntimeVersion::none;
        std::string_view response_protocol = kProtocolV0;
        if (schema == "host-engine-protocol-v0" && protocol == kProtocolV0) {
            version = RuntimeVersion::v0;
        } else if (schema == "host-engine-protocol-v1" && protocol == kProtocolV1) {
            version = RuntimeVersion::v1;
            response_protocol = kProtocolV1;
        } else if (protocol == kProtocolV1) {
            response_protocol = kProtocolV1;
        }
        try {
            if (version == RuntimeVersion::none) {
                std::cout << failure(
                    message_id,
                    response_protocol,
                    "ENGINE_PROTOCOL_ABI_MISMATCH",
                    "protocol or schema ABI mismatch"
                ) << std::endl;
                continue;
            }
            const auto type = text_member(line, "message_type");
            if (!type) throw std::runtime_error("ENGINE_MESSAGE_TYPE_MISSING");
            std::string value;
            bool shutdown = false;
            if (*type == "hello") {
                const auto expected_runtime = version == RuntimeVersion::v1
                    ? schuss::rt::v1::kRuntimeAbi
                    : schuss::rt::kRuntimeAbi;
                const auto expected_package = version == RuntimeVersion::v1
                    ? schuss::rt::v1::kPackageSchema
                    : schuss::rt::kPackageSchema;
                if (text_member(line, "runtime_abi") != expected_runtime
                    || text_member(line, "package_schema_version") != expected_package) {
                    throw std::runtime_error("ENGINE_HANDSHAKE_ABI_MISMATCH");
                }
                value = "{\"package_schema_version\":\"" + std::string(expected_package)
                    + "\",\"runtime_abi\":\"" + std::string(expected_runtime) + "\"}";
            } else if (*type == "devices.inspect") {
                value = engine.inspect_devices();
            } else if (*type == "package.prepare") {
                const auto path = text_member(line, "package_path");
                const auto hash = text_member(line, "package_content_hash");
                if (!path || !hash) throw std::runtime_error("ENGINE_PACKAGE_REQUEST_INVALID");
                value = engine.prepare(version, *path, *hash);
            } else if (*type == "session.start") {
                const auto sample_rate = integer_member(line, "sample_rate_hz");
                const auto block = integer_member(line, "block_frames");
                if (!sample_rate || !block) throw std::runtime_error("ENGINE_SESSION_REQUEST_INVALID");
                value = engine.start(version, *sample_rate, *block);
            } else if (*type == "session.inspect") {
                value = engine.inspect(version);
            } else if (*type == "session.stop") {
                value = engine.stop(version);
            } else if (*type == "replacement.prepare" && version == RuntimeVersion::v1) {
                const auto generation = integer_member(line, "expected_engine_generation");
                const auto active_hash = text_member(line, "expected_active_package_content_hash");
                const auto successor_path = text_member(line, "successor_package_path");
                const auto successor_hash = text_member(line, "successor_package_content_hash");
                if (!generation || !active_hash || !successor_path || !successor_hash) {
                    throw std::runtime_error("ENGINE_REPLACEMENT_REQUEST_INVALID");
                }
                value = engine.prepare_replacement(
                    *generation, *active_hash, *successor_path, *successor_hash
                );
            } else if (*type == "replacement.activate" && version == RuntimeVersion::v1) {
                const auto generation = integer_member(line, "expected_engine_generation");
                const auto active_hash = text_member(line, "expected_active_package_content_hash");
                const auto successor_hash = text_member(line, "successor_package_content_hash");
                if (!generation || !active_hash || !successor_hash) {
                    throw std::runtime_error("ENGINE_REPLACEMENT_REQUEST_INVALID");
                }
                value = engine.activate_replacement(
                    *generation, *active_hash, *successor_hash
                );
            } else if (*type == "replacement.cancel" && version == RuntimeVersion::v1) {
                const auto generation = integer_member(line, "expected_engine_generation");
                const auto active_hash = text_member(line, "expected_active_package_content_hash");
                const auto successor_hash = text_member(line, "successor_package_content_hash");
                if (!generation || !active_hash || !successor_hash) {
                    throw std::runtime_error("ENGINE_REPLACEMENT_REQUEST_INVALID");
                }
                value = engine.cancel_replacement(
                    *generation, *active_hash, *successor_hash
                );
            } else if (*type == "shutdown") {
                value = engine.stop(version);
                shutdown = true;
            } else {
                throw std::runtime_error("ENGINE_MESSAGE_TYPE_UNSUPPORTED");
            }
            std::cout << response(
                message_id, response_protocol, "success", value
            ) << std::endl;
            if (shutdown) break;
        } catch (const std::exception& error) {
            std::cout << failure(
                message_id,
                response_protocol,
                "ENGINE_OPERATION_FAILED",
                error.what()
            ) << std::endl;
        }
    }
    return 0;
}
