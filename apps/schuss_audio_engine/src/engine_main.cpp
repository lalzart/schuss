#include "schuss_rt/runtime.hpp"
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
#include <string>
#include <string_view>
#include <vector>

namespace {

constexpr std::string_view kProtocol = "schuss-audio-engine-protocol-v0";

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
    std::string_view status,
    std::string value,
    std::string diagnostics = "[]"
) {
    return "{\"diagnostics\":" + diagnostics + ",\"message_id\":\"" + escaped(message_id)
        + "\",\"protocol_abi\":\"" + std::string(kProtocol) + "\",\"status\":\""
        + std::string(status) + "\",\"value\":" + std::move(value) + "}";
}

std::string failure(const std::string& message_id, std::string_view code, std::string_view message) {
    return response(
        message_id,
        "failed",
        "null",
        "[{\"code\":\"" + std::string(code) + "\",\"message\":\"" + escaped(message)
            + "\",\"severity\":\"error\"}]"
    );
}

class HeadlessEngine final : public juce::AudioIODeviceCallback, public juce::MidiInputCallback {
public:
    ~HeadlessEngine() override { stop(); }

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

    std::string prepare(const std::string& path, const std::string& expected_hash) {
        if (active_.load(std::memory_order_acquire)) throw std::runtime_error("ENGINE_SESSION_ACTIVE");
        schuss::rt::PreparedPackage package;
        const auto parsed = schuss::rt::parse_package(read_text(path), expected_hash, package);
        if (!parsed) throw std::runtime_error(parsed.diagnostic);
        const auto result = runtime_.prepare(package);
        if (!result) throw std::runtime_error(result.diagnostic);
        package_hash_ = package.content_hash;
        prepared_.store(true, std::memory_order_release);
        return "{\"package_content_hash\":\"" + escaped(package_hash_)
            + "\",\"runtime_abi\":\"schuss-rt-abi-v0\"}";
    }

    std::string start(std::uint32_t sample_rate, std::uint32_t block_frames) {
        if (!prepared_.load(std::memory_order_acquire)) throw std::runtime_error("ENGINE_PACKAGE_NOT_PREPARED");
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
        runtime_.reset();
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

    std::string inspect() const { return session_value(); }

    std::string stop() {
        const bool was_active = active_.exchange(false, std::memory_order_acq_rel);
        for (auto& input : midi_inputs_) input->stop();
        midi_inputs_.clear();
        if (was_active) devices_.removeAudioCallback(this);
        devices_.closeAudioDevice();
        return session_value();
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
            runtime_.enqueue(event);
        }
        const auto processed = runtime_.process(
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

    std::string session_value() const {
        const auto metrics = runtime_.metrics();
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
            + ",\"package_content_hash\":\"" + escaped(package_hash_) + "\",\"processed_frames\":"
            + std::to_string(metrics.processed_frames) + ",\"queue_overflows\":"
            + std::to_string(metrics.queue_overflows + midi_ingress_.overflows()) + ",\"sample_rate_hz\":"
            + std::to_string(active_sample_rate_) + ",\"xruns\":"
            + std::to_string(xruns_.load(std::memory_order_relaxed)) + "}";
    }

    juce::AudioDeviceManager devices_;
    juce::OwnedArray<juce::AudioIODeviceType> device_types_;
    std::vector<std::unique_ptr<juce::MidiInput>> midi_inputs_;
    schuss::engine::MidiIngressQueue<1024> midi_ingress_;
    schuss::rt::Runtime runtime_;
    std::array<std::int32_t, 512> left_{};
    std::array<std::int32_t, 512> right_{};
    std::atomic<bool> prepared_{false};
    std::atomic<bool> active_{false};
    std::atomic<std::uint64_t> midi_sequence_{0};
    std::atomic<std::uint64_t> maximum_callback_us_{0};
    std::atomic<std::uint64_t> xruns_{0};
    std::atomic<std::uint64_t> device_disconnects_{0};
    std::string package_hash_;
    std::string active_device_name_;
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
        try {
            if (text_member(line, "schema_version") != "host-engine-protocol-v0"
                || text_member(line, "protocol_abi") != kProtocol) {
                std::cout << failure(message_id, "ENGINE_PROTOCOL_ABI_MISMATCH", "protocol or schema ABI mismatch") << std::endl;
                continue;
            }
            const auto type = text_member(line, "message_type");
            if (!type) throw std::runtime_error("ENGINE_MESSAGE_TYPE_MISSING");
            std::string value;
            bool shutdown = false;
            if (*type == "hello") {
                if (text_member(line, "runtime_abi") != schuss::rt::kRuntimeAbi
                    || text_member(line, "package_schema_version") != schuss::rt::kPackageSchema) {
                    throw std::runtime_error("ENGINE_HANDSHAKE_ABI_MISMATCH");
                }
                value = "{\"package_schema_version\":\"host-runtime-package-v0\",\"runtime_abi\":\"schuss-rt-abi-v0\"}";
            } else if (*type == "devices.inspect") {
                value = engine.inspect_devices();
            } else if (*type == "package.prepare") {
                const auto path = text_member(line, "package_path");
                const auto hash = text_member(line, "package_content_hash");
                if (!path || !hash) throw std::runtime_error("ENGINE_PACKAGE_REQUEST_INVALID");
                value = engine.prepare(*path, *hash);
            } else if (*type == "session.start") {
                const auto sample_rate = integer_member(line, "sample_rate_hz");
                const auto block = integer_member(line, "block_frames");
                if (!sample_rate || !block) throw std::runtime_error("ENGINE_SESSION_REQUEST_INVALID");
                value = engine.start(*sample_rate, *block);
            } else if (*type == "session.inspect") {
                value = engine.inspect();
            } else if (*type == "session.stop") {
                value = engine.stop();
            } else if (*type == "shutdown") {
                value = engine.stop();
                shutdown = true;
            } else {
                throw std::runtime_error("ENGINE_MESSAGE_TYPE_UNSUPPORTED");
            }
            std::cout << response(message_id, "success", value) << std::endl;
            if (shutdown) break;
        } catch (const std::exception& error) {
            std::cout << failure(message_id, "ENGINE_OPERATION_FAILED", error.what()) << std::endl;
        }
    }
    return 0;
}
