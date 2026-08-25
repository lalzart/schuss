#include "layerwell/core.hpp"
#include "layerwell/launch_control_3.hpp"
#include "layerwell/state_snapshot.hpp"

#include "schuss/instrument_lab/bounded_midi.hpp"
#include "schuss/pamplist/ui_model.hpp"
#include "tidepit/control_map.hpp"
#include "tidepit/ui_model.hpp"

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <string_view>

namespace {

namespace pam = schuss::pamplist;

constexpr int kRequestedBlockFrames = 128;
constexpr int kUiRefreshHz = 20;
constexpr std::size_t kGuiEventCapacity = 256U;

juce::String text(std::string_view value) {
    return juce::String::fromUTF8(value.data(), static_cast<int>(value.size()));
}

template <std::size_t Capacity>
class GuiEventQueue final {
public:
    static_assert(Capacity > 1U);

    bool push(const layerwell::Event& event) noexcept {
        const auto write = write_.load(std::memory_order_relaxed);
        const auto next = (write + 1U) % Capacity;
        if (next == read_.load(std::memory_order_acquire)) return false;
        events_[write] = event;
        write_.store(next, std::memory_order_release);
        return true;
    }

    bool pop(layerwell::Event& event) noexcept {
        const auto read = read_.load(std::memory_order_relaxed);
        if (read == write_.load(std::memory_order_acquire)) return false;
        event = events_[read];
        read_.store((read + 1U) % Capacity, std::memory_order_release);
        return true;
    }

    void reset() noexcept {
        read_.store(0U, std::memory_order_release);
        write_.store(0U, std::memory_order_release);
    }

private:
    std::array<layerwell::Event, Capacity> events_{};
    std::atomic<std::size_t> read_{0U};
    std::atomic<std::size_t> write_{0U};
};

class LayerwellEngine final
    : public juce::AudioIODeviceCallback,
      public juce::MidiInputCallback {
public:
    LayerwellEngine() {
        collector_.ensureStorageAllocated(8192);
        midi_block_.ensureSize(8192);
        accepted_state_.publish(layerwell::Snapshot{});
    }

    ~LayerwellEngine() override {
        closeMidiInput();
        closeMidiOutput();
        stopAudio();
    }

    juce::String startAudio() {
        if (audioActive()) return "Audio already active";
        auto error = device_manager_.initialiseWithDefaultDevices(0, 2);
        if (error.isNotEmpty()) return "Audio output unavailable: " + error;
        auto setup = device_manager_.getAudioDeviceSetup();
        setup.sampleRate = layerwell::kSampleRate;
        setup.bufferSize = kRequestedBlockFrames;
        error = device_manager_.setAudioDeviceSetup(setup, true);
        if (error.isNotEmpty()) {
            device_manager_.closeAudioDevice();
            return "48 kHz stereo setup unavailable: " + error;
        }
        auto* device = device_manager_.getCurrentAudioDevice();
        if (device == nullptr
            || device->getCurrentSampleRate() != layerwell::kSampleRate
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples()
                > static_cast<int>(layerwell::kMaximumBlockFrames)
            || device->getCurrentBufferSizeSamples()
                % static_cast<int>(layerwell::kSourceQuantumFrames) != 0) {
            device_manager_.closeAudioDevice();
            return "Layerwell requires 48 kHz stereo and a 16-frame-multiple block up to 512";
        }
        device_manager_.addAudioCallback(this);
        return "Audio requested; accepted callback state will report readiness";
    }

    void stopAudio() {
        audio_ready_.store(false, std::memory_order_release);
        device_manager_.removeAudioCallback(this);
        device_manager_.closeAudioDevice();
    }

    [[nodiscard]] bool audioActive() const noexcept {
        return audio_ready_.load(std::memory_order_acquire);
    }

    [[nodiscard]] juce::Array<juce::MidiDeviceInfo> availableMidiInputs() const {
        return juce::MidiInput::getAvailableDevices();
    }

    [[nodiscard]] juce::Array<juce::MidiDeviceInfo> availableMidiOutputs() const {
        return juce::MidiOutput::getAvailableDevices();
    }

    juce::String selectMidiInput(const juce::MidiDeviceInfo& device) {
        closeMidiInput();
        if (device.identifier.isEmpty()) return "MIDI input disabled";
        device_manager_.setMidiInputDeviceEnabled(device.identifier, true);
        if (!device_manager_.isMidiInputDeviceEnabled(device.identifier)) {
            return "Could not open MIDI input: " + device.name;
        }
        device_manager_.addMidiInputDeviceCallback(device.identifier, this);
        selected_input_identifier_ = device.identifier;
        selected_input_name_ = device.name;
        return "MIDI input active: " + device.name;
    }

    juce::String selectMidiOutput(const juce::MidiDeviceInfo& device) {
        closeMidiOutput();
        if (device.identifier.isEmpty()) return "MIDI output disabled";
        midi_output_ = juce::MidiOutput::openDevice(device.identifier);
        if (midi_output_ == nullptr) return "Could not open MIDI output: " + device.name;
        selected_output_identifier_ = device.identifier;
        selected_output_name_ = device.name;
        feedback_adapter_.reset();
        sendBatch(feedback_adapter_.connectionMessages(acceptedSnapshot()));
        last_feedback_sequence_ = 0U;
        return "LC3 DAW output active: " + device.name;
    }

    bool submitEvent(
        layerwell::EventKind kind,
        std::uint8_t index = 0U,
        double value = 0.0) noexcept {
        if (!audioActive()) return false;
        const layerwell::Event event{0U, 0U, kind, index, value};
        if (gui_events_.push(event)) return true;
        gui_events_dropped_.fetch_add(1U, std::memory_order_relaxed);
        return false;
    }

    [[nodiscard]] layerwell::Snapshot acceptedSnapshot() const noexcept {
        last_ui_snapshot_ = accepted_state_.load(last_ui_snapshot_);
        return last_ui_snapshot_;
    }

    void pumpFeedback() {
        if (midi_output_ == nullptr) return;
        const auto snapshot = acceptedSnapshot();
        if (snapshot.diagnostics.snapshot_sequence == last_feedback_sequence_) return;
        sendBatch(feedback_adapter_.stateSyncMessages(snapshot));
        last_feedback_sequence_ = snapshot.diagnostics.snapshot_sequence;
    }

    [[nodiscard]] juce::String diagnosticsText() const {
        const auto snapshot = acceptedSnapshot();
        juce::String result = audioActive() ? "AUDIO 48K ACTIVE" : "AUDIO STOPPED";
        result += "  |  BLOCK "
            + juce::String(callback_block_frames_.load(std::memory_order_acquire));
        result += "  |  LOOP " + juce::String(snapshot.loop_length_frames);
        result += "  |  PHASE " + juce::String(snapshot.phase_frames);
        result += "  |  TRIM " + juce::String(snapshot.trim_start_frames)
            + "-" + juce::String(snapshot.trim_end_frames)
            + (snapshot.trim_available ? " READY" : " LOCK");
        result += "  |  EVENTS " + juce::String(snapshot.diagnostics.accepted_events)
            + "/" + juce::String(snapshot.diagnostics.dropped_events);
        result += "  |  RX "
            + juce::String(received_midi_.load(std::memory_order_acquire));
        result += " / MAP "
            + juce::String(mapped_midi_.load(std::memory_order_acquire));
        if (gui_events_dropped_.load(std::memory_order_acquire) != 0U) {
            result += "  |  GUI DROP "
                + juce::String(gui_events_dropped_.load(std::memory_order_acquire));
        }
        if (selected_input_identifier_.isEmpty()) result += "  |  MIDI IN OFF";
        else result += "  |  IN " + selected_input_name_;
        if (selected_output_identifier_.isEmpty()) result += "  |  MIDI OUT OFF";
        else result += "  |  OUT " + selected_output_name_;
        return result;
    }

    void handleIncomingMidiMessage(
        juce::MidiInput*,
        const juce::MidiMessage& message) override {
        received_midi_.fetch_add(1U, std::memory_order_relaxed);
        collector_.handleIncomingMidiMessage(nullptr, message);
    }

    void audioDeviceAboutToStart(juce::AudioIODevice* device) override {
        audio_ready_.store(false, std::memory_order_release);
        input_adapter_.reset();
        ingress_sequence_.reset();
        gui_events_.reset();
        core_.reset();
        if (device == nullptr
            || device->getCurrentSampleRate() != layerwell::kSampleRate
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples()
                > static_cast<int>(layerwell::kMaximumBlockFrames)
            || device->getCurrentBufferSizeSamples()
                % static_cast<int>(layerwell::kSourceQuantumFrames) != 0) {
            return;
        }
        collector_.reset(layerwell::kSampleRate);
        auto next = std::make_unique<layerwell::Core>();
        if (!next->prepare()) return;
        core_ = std::move(next);
        callback_block_frames_.store(
            static_cast<std::uint32_t>(device->getCurrentBufferSizeSamples()),
            std::memory_order_release);
        accepted_state_.publish(core_->snapshot());
        audio_ready_.store(true, std::memory_order_release);
    }

    void audioDeviceStopped() override {
        audio_ready_.store(false, std::memory_order_release);
        core_.reset();
        accepted_state_.publish(layerwell::Snapshot{});
    }

    void audioDeviceIOCallbackWithContext(
        const float* const*,
        int,
        float* const* outputs,
        int output_channels,
        int frames,
        const juce::AudioIODeviceCallbackContext&) override {
        clearOutputs(outputs, output_channels, frames);
        if (!audioActive()
            || core_ == nullptr
            || outputs == nullptr
            || output_channels < 2
            || outputs[0] == nullptr
            || outputs[1] == nullptr
            || frames <= 0
            || frames > static_cast<int>(layerwell::kMaximumBlockFrames)
            || frames % static_cast<int>(layerwell::kSourceQuantumFrames) != 0) {
            unsupported_callbacks_.fetch_add(1U, std::memory_order_relaxed);
            return;
        }

        std::array<layerwell::Event, layerwell::kMaximumEvents> events{};
        std::size_t event_count = 0U;
        layerwell::Event gui_event{};
        while (gui_events_.pop(gui_event)) {
            gui_event.sample_offset = 0U;
            gui_event.ingress_sequence = ingress_sequence_.next();
            if (event_count < events.size()) {
                events[event_count++] = gui_event;
            } else {
                gui_events_dropped_.fetch_add(1U, std::memory_order_relaxed);
            }
        }

        midi_block_.clear();
        collector_.removeNextBlockOfMessages(midi_block_, frames);
        for (const auto metadata : midi_block_) {
            const auto result = input_adapter_.parse(
                metadata.data,
                metadata.numBytes > 0
                    ? static_cast<std::size_t>(metadata.numBytes)
                    : 0U,
                schuss::instrument_lab::clampSampleOffset(
                    metadata.samplePosition,
                    static_cast<std::uint32_t>(frames)),
                ingress_sequence_.next());
            if (!result.has_event) continue;
            mapped_midi_.fetch_add(1U, std::memory_order_relaxed);
            if (event_count < events.size()) {
                events[event_count++] = result.event;
            } else {
                gui_events_dropped_.fetch_add(1U, std::memory_order_relaxed);
            }
        }

        core_->process(
            outputs[0], outputs[1], static_cast<std::uint32_t>(frames),
            events.data(), event_count);
        accepted_state_.publish(core_->snapshot());
    }

private:
    void closeMidiInput() {
        if (selected_input_identifier_.isEmpty()) return;
        device_manager_.removeMidiInputDeviceCallback(
            selected_input_identifier_, this);
        device_manager_.setMidiInputDeviceEnabled(
            selected_input_identifier_, false);
        selected_input_identifier_.clear();
        selected_input_name_.clear();
    }

    void closeMidiOutput() {
        if (midi_output_ != nullptr) {
            sendBatch(feedback_adapter_.endpointChangeCleanupMessages());
        }
        midi_output_.reset();
        selected_output_identifier_.clear();
        selected_output_name_.clear();
    }

    void sendBatch(const layerwell::MidiBatch& batch) {
        if (midi_output_ == nullptr) return;
        for (std::size_t index = 0U; index < batch.count; ++index) {
            const auto& source = batch.messages[index];
            midi_output_->sendMessageNow(juce::MidiMessage(
                source.bytes.data(), source.size));
        }
    }

    static void clearOutputs(
        float* const* outputs,
        int output_channels,
        int frames) noexcept {
        if (outputs == nullptr || frames <= 0) return;
        for (int channel = 0; channel < output_channels; ++channel) {
            if (outputs[channel] != nullptr) {
                std::fill_n(outputs[channel], frames, 0.0F);
            }
        }
    }

    juce::AudioDeviceManager device_manager_{};
    juce::MidiMessageCollector collector_{};
    juce::MidiBuffer midi_block_{};
    std::unique_ptr<juce::MidiOutput> midi_output_{};
    std::unique_ptr<layerwell::Core> core_{};
    layerwell::LaunchControl3Adapter input_adapter_{};
    layerwell::LaunchControl3Adapter feedback_adapter_{};
    schuss::instrument_lab::IngressSequence ingress_sequence_{};
    GuiEventQueue<kGuiEventCapacity> gui_events_{};
    layerwell::AtomicSnapshot accepted_state_{};
    mutable layerwell::Snapshot last_ui_snapshot_{};
    juce::String selected_input_identifier_{};
    juce::String selected_input_name_{};
    juce::String selected_output_identifier_{};
    juce::String selected_output_name_{};
    std::uint64_t last_feedback_sequence_{};
    std::atomic<bool> audio_ready_{false};
    std::atomic<std::uint32_t> callback_block_frames_{0U};
    std::atomic<std::uint64_t> received_midi_{0U};
    std::atomic<std::uint64_t> mapped_midi_{0U};
    std::atomic<std::uint64_t> gui_events_dropped_{0U};
    std::atomic<std::uint64_t> unsupported_callbacks_{0U};
};

using Dispatch = std::function<bool(layerwell::EventKind, std::uint8_t, double)>;

class TideScopeComponent final : public juce::Component {
public:
    void setSnapshot(const layerwell::TideScopeSnapshot& snapshot) {
        snapshot_ = snapshot;
        repaint();
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff0a1114});
        auto bounds = getLocalBounds().toFloat().reduced(5.0F);
        graphics.setColour(juce::Colour{0xff26383e});
        graphics.drawRoundedRectangle(bounds, 4.0F, 1.0F);
        if (snapshot_.sample_count < 2U) return;
        drawChannel(graphics, bounds, snapshot_.left, juce::Colour{0xff67e8d0});
        drawChannel(graphics, bounds, snapshot_.right, juce::Colour{0xffe7b75b});
    }

private:
    static void drawChannel(
        juce::Graphics& graphics,
        juce::Rectangle<float> bounds,
        const std::array<float, layerwell::kTideScopeSamples>& samples,
        juce::Colour colour) {
        juce::Path path;
        const auto centre = bounds.getCentreY();
        for (std::size_t index = 0U; index < samples.size(); ++index) {
            const auto x = bounds.getX() + bounds.getWidth()
                * static_cast<float>(index) / static_cast<float>(samples.size() - 1U);
            const auto y = centre - juce::jlimit(-1.0F, 1.0F, samples[index])
                * bounds.getHeight() * 0.44F;
            if (index == 0U) path.startNewSubPath(x, y);
            else path.lineTo(x, y);
        }
        graphics.setColour(colour.withAlpha(0.82F));
        graphics.strokePath(path, juce::PathStrokeType{1.25F});
    }

    layerwell::TideScopeSnapshot snapshot_{};
};

class TidePanel final : public juce::Component {
public:
    explicit TidePanel(Dispatch dispatch) : dispatch_(std::move(dispatch)) {
        title_.setText("TIDE PIT", juce::dontSendNotification);
        title_.setFont(juce::FontOptions{22.0F, juce::Font::bold});
        title_.setColour(juce::Label::textColourId, juce::Colour{0xff67e8d0});
        addAndMakeVisible(title_);
        mode_.setColour(juce::Label::textColourId, juce::Colour{0xffe7b75b});
        mode_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(mode_);
        for (std::size_t slot = 0U; slot < encoders_.size(); ++slot) {
            auto& slider = encoders_[slot];
            slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            slider.setTextBoxStyle(juce::Slider::TextBoxBelow, false, 64, 17);
            slider.setRange(0.0, 127.0, 1.0);
            slider.setColour(
                juce::Slider::rotarySliderFillColourId, juce::Colour{0xff67e8d0});
            slider.onValueChange = [this, slot] {
                if (!updating_) {
                    dispatch_(layerwell::EventKind::source_encoder_absolute,
                        static_cast<std::uint8_t>(slot), encoders_[slot].getValue());
                }
            };
            addAndMakeVisible(slider);
            labels_[slot].setJustificationType(juce::Justification::centred);
            labels_[slot].setFont(juce::FontOptions{11.0F, juce::Font::bold});
            labels_[slot].setColour(
                juce::Label::textColourId, juce::Colour{0xffc7d0d6});
            addAndMakeVisible(labels_[slot]);
        }
        for (std::size_t slot = 0U; slot < buttons_.size(); ++slot) {
            buttons_[slot].onClick = [this, slot] {
                dispatch_(layerwell::EventKind::source_button,
                    static_cast<std::uint8_t>(slot), 127.0);
                dispatch_(layerwell::EventKind::source_button,
                    static_cast<std::uint8_t>(slot), 0.0);
            };
            addAndMakeVisible(buttons_[slot]);
        }
        for (auto& line : display_lines_) {
            line.setFont(juce::FontOptions{13.0F});
            line.setColour(juce::Label::textColourId, juce::Colour{0xffd8e2e7});
            addAndMakeVisible(line);
        }
        addAndMakeVisible(scope_);
    }

    void applySnapshot(const layerwell::Snapshot& snapshot) {
        updating_ = true;
        const auto& tide = snapshot.source_panel.tide_pit;
        for (std::size_t slot = 0U; slot < encoders_.size(); ++slot) {
            labels_[slot].setText(text(snapshot.source_encoder_labels[slot]),
                juce::dontSendNotification);
            encoders_[slot].setValue(
                snapshot.source_encoder_values[slot], juce::dontSendNotification);
            encoders_[slot].setEnabled(
                snapshot.prepared && snapshot.source_encoder_assigned[slot]);
            encoders_[slot].setTooltip(text(snapshot.source_encoder_tooltips[slot]));
        }
        const auto& descriptors = tidepit::buttonDescriptors();
        for (std::size_t slot = 0U; slot < buttons_.size(); ++slot) {
            const auto presentation = tidepit::buttonPresentation(
                descriptors[slot].id, tide);
            buttons_[slot].setButtonText(
                text(presentation.label) + "\n" + text(presentation.state));
            buttons_[slot].setToggleState(
                presentation.latched_active, juce::dontSendNotification);
            buttons_[slot].setEnabled(
                snapshot.prepared && snapshot.source_button_assigned[slot]);
        }
        for (std::size_t line = 0U; line < display_lines_.size(); ++line) {
            display_lines_[line].setText(
                juce::String::fromUTF8(tide.display_lines[line].data(), 21),
                juce::dontSendNotification);
        }
        mode_.setText(
            juce::String{"SOURCE "} + tidepit::sourceName(tide.source)
                + "  /  SCALE " + tidepit::scaleName(tide.scale)
                + "  /  FX " + tidepit::effectName(tide.effect)
                + "  /  TARGET " + tidepit::targetName(tide.target),
            juce::dontSendNotification);
        scope_.setSnapshot(snapshot.source_panel.tide_scope);
        updating_ = false;
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff101a1d});
        graphics.setColour(juce::Colour{0xff294047});
        graphics.drawRoundedRectangle(
            getLocalBounds().toFloat().reduced(2.0F), 8.0F, 1.0F);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(12);
        auto header = area.removeFromTop(28);
        title_.setBounds(header.removeFromLeft(180));
        mode_.setBounds(header);
        auto monitor = area.removeFromTop(100);
        auto display = monitor.removeFromLeft(430).reduced(3);
        for (auto& line : display_lines_) {
            line.setBounds(display.removeFromTop(23));
        }
        scope_.setBounds(monitor.reduced(3));
        area.removeFromTop(5);
        for (std::size_t row = 0U; row < 2U; ++row) {
            auto cells = area.removeFromTop(125);
            for (std::size_t column = 0U; column < 8U; ++column) {
                const auto slot = row * 8U + column;
                auto cell = cells.removeFromLeft(cells.getWidth()
                    / static_cast<int>(8U - column)).reduced(3);
                labels_[slot].setBounds(cell.removeFromTop(18));
                encoders_[slot].setBounds(cell);
            }
        }
        area.removeFromTop(4);
        auto buttons = area.removeFromTop(48);
        for (std::size_t slot = 0U; slot < buttons_.size(); ++slot) {
            buttons_[slot].setBounds(buttons.removeFromLeft(buttons.getWidth()
                / static_cast<int>(buttons_.size() - slot)).reduced(3));
        }
    }

private:
    Dispatch dispatch_;
    juce::Label title_{};
    juce::Label mode_{};
    std::array<juce::Slider, 16> encoders_{};
    std::array<juce::Label, 16> labels_{};
    std::array<juce::TextButton, 8> buttons_{};
    std::array<juce::Label, 4> display_lines_{};
    TideScopeComponent scope_{};
    bool updating_{};
};

class PamplistImpactComponent final : public juce::Component {
public:
    void setSnapshot(const layerwell::PamplistImpactHistorySnapshot& snapshot) {
        snapshot_ = snapshot;
        repaint();
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff11161c});
        auto bounds = getLocalBounds().toFloat().reduced(5.0F);
        graphics.setColour(juce::Colour{0xff333e49});
        graphics.drawRoundedRectangle(bounds, 4.0F, 1.0F);
        if (snapshot_.sample_count == 0U) return;
        constexpr std::array<juce::uint32, 7> colours{{
            0xff4fc3d7, 0xffff9f43, 0xff9d79d6, 0xff6fca75,
            0xffffcf56, 0xffef78b5, 0xff73a6ff,
        }};
        const auto column_width = bounds.getWidth()
            / static_cast<float>(layerwell::kPamplistImpactHistorySamples);
        for (std::size_t sample = 0U; sample < snapshot_.sample_count; ++sample) {
            const auto x = bounds.getX() + static_cast<float>(sample) * column_width;
            for (std::size_t lane = 0U; lane < 7U; ++lane) {
                const auto level = juce::jlimit(
                    0.0F, 1.0F, snapshot_.samples[sample].lane_levels[lane]);
                const auto band = bounds.getHeight() / 7.0F;
                const auto bottom = bounds.getY() + band * static_cast<float>(lane + 1U);
                graphics.setColour(juce::Colour{colours[lane]}.withAlpha(0.32F + level * 0.68F));
                graphics.fillRect(juce::Rectangle<float>{
                    x, bottom - band * level, std::max(1.0F, column_width), band * level});
            }
        }
    }

private:
    layerwell::PamplistImpactHistorySnapshot snapshot_{};
};

class PamplistPanel final : public juce::Component {
public:
    explicit PamplistPanel(Dispatch dispatch) : dispatch_(std::move(dispatch)) {
        title_.setText("PAMPLIST", juce::dontSendNotification);
        title_.setFont(juce::FontOptions{22.0F, juce::Font::bold});
        title_.setColour(juce::Label::textColourId, juce::Colour{0xffffcf56});
        addAndMakeVisible(title_);
        run_.setButtonText("RUN");
        run_.onClick = [this] {
            dispatch_(layerwell::EventKind::source_toggle_run, 0U, 0.0);
        };
        voice_.setButtonText("VOICE");
        voice_.onClick = [this] {
            dispatch_(layerwell::EventKind::source_set_context, 0U, 0.0);
        };
        motion_.setButtonText("MOTION");
        motion_.onClick = [this] {
            dispatch_(layerwell::EventKind::source_set_context, 1U, 0.0);
        };
        clear_.setButtonText("CLEAR FX");
        clear_.setTooltip(
            "Clears only the shared cohesion body's retained tail; lane clocks, patterns, voices, and dry voice tails continue.");
        clear_.onClick = [this] {
            dispatch_(layerwell::EventKind::source_clear_effect, 0U, 0.0);
        };
        addAndMakeVisible(run_);
        addAndMakeVisible(voice_);
        addAndMakeVisible(motion_);
        addAndMakeVisible(clear_);
        guide_.setColour(juce::Label::textColourId, juce::Colour{0xff9ca7b5});
        guide_.setFont(juce::FontOptions{11.5F});
        addAndMakeVisible(guide_);
        for (std::size_t page = 0U; page < pages_.size(); ++page) {
            pages_[page].setButtonText(page < 7U
                ? "LANE " + juce::String(static_cast<int>(page + 1U))
                : "GLOBAL / CLEAR");
            pages_[page].onClick = [this, page] {
                dispatch_(layerwell::EventKind::source_button,
                    static_cast<std::uint8_t>(page), 127.0);
                dispatch_(layerwell::EventKind::source_button,
                    static_cast<std::uint8_t>(page), 0.0);
            };
            addAndMakeVisible(pages_[page]);
        }
        top_group_.setColour(
            juce::GroupComponent::outlineColourId, juce::Colour{0xff46515e});
        bottom_group_.setColour(
            juce::GroupComponent::outlineColourId, juce::Colour{0xff46515e});
        addAndMakeVisible(top_group_);
        addAndMakeVisible(bottom_group_);
        top_group_.toBack();
        bottom_group_.toBack();
        for (std::size_t slot = 0U; slot < sliders_.size(); ++slot) {
            sliders_[slot].setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            sliders_[slot].setTextBoxStyle(juce::Slider::TextBoxBelow, false, 80, 17);
            sliders_[slot].setColour(
                juce::Slider::rotarySliderFillColourId,
                slot < 8U ? juce::Colour{0xff4fc3d7} : juce::Colour{0xffff9f43});
            sliders_[slot].onValueChange = [this, slot] {
                if (!updating_) {
                    dispatch_(layerwell::EventKind::source_surface_value,
                        static_cast<std::uint8_t>(slot), sliders_[slot].getValue());
                }
            };
            addAndMakeVisible(sliders_[slot]);
            labels_[slot].setJustificationType(juce::Justification::centred);
            labels_[slot].setFont(juce::FontOptions{11.0F, juce::Font::bold});
            labels_[slot].setColour(
                juce::Label::textColourId, juce::Colour{0xffd5dce5});
            addAndMakeVisible(labels_[slot]);
        }
        addAndMakeVisible(impact_);
    }

    void applySnapshot(const layerwell::Snapshot& snapshot) {
        updating_ = true;
        const auto& accepted = snapshot.source_panel.pamplist;
        const auto surface = pam::surfaceModel(accepted);
        run_.setButtonText(accepted.accepted.running ? "RUNNING" : "STOPPED");
        run_.setToggleState(accepted.accepted.running, juce::dontSendNotification);
        run_.setEnabled(snapshot.prepared);
        const auto lane_context = accepted.accepted.selected_page < pam::kLaneCount;
        voice_.setEnabled(snapshot.prepared && lane_context);
        motion_.setEnabled(snapshot.prepared && lane_context);
        voice_.setToggleState(
            lane_context && accepted.accepted.lane_control_mode
                == pam::LaneControlMode::voice,
            juce::dontSendNotification);
        motion_.setToggleState(
            lane_context && accepted.accepted.lane_control_mode
                == pam::LaneControlMode::motion,
            juce::dontSendNotification);
        clear_.setEnabled(
            snapshot.prepared && accepted.accepted.selected_page == pam::kGlobalPageIndex);
        clear_.setButtonText("CLEAR FX  "
            + juce::String(accepted.diagnostics.effect_clear_count));
        for (std::size_t page = 0U; page < pages_.size(); ++page) {
            pages_[page].setToggleState(
                accepted.accepted.selected_page == page,
                juce::dontSendNotification);
            pages_[page].setEnabled(snapshot.prepared);
        }
        top_group_.setText(text(surface.top_group));
        bottom_group_.setText(text(surface.bottom_group));
        guide_.setText(text(surface.guide), juce::dontSendNotification);
        for (std::size_t slot = 0U; slot < sliders_.size(); ++slot) {
            const auto& model = slot < 8U
                ? surface.top[slot]
                : surface.bottom[slot - 8U];
            const auto interval = model.interval > 0.0 ? model.interval : 0.001;
            sliders_[slot].setRange(model.minimum, model.maximum, interval);
            sliders_[slot].setValue(model.value, juce::dontSendNotification);
            sliders_[slot].setEnabled(snapshot.prepared && model.enabled);
            sliders_[slot].setTooltip(text(model.tooltip));
            labels_[slot].setText(text(model.label), juce::dontSendNotification);
        }
        impact_.setSnapshot(snapshot.source_panel.pamplist_impact);
        updating_ = false;
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff101419});
        graphics.setColour(juce::Colour{0xff343c46});
        graphics.drawRoundedRectangle(
            getLocalBounds().toFloat().reduced(2.0F), 8.0F, 1.0F);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(10);
        auto header = area.removeFromTop(30);
        title_.setBounds(header.removeFromLeft(150));
        run_.setBounds(header.removeFromLeft(86).reduced(2));
        voice_.setBounds(header.removeFromLeft(76).reduced(2));
        motion_.setBounds(header.removeFromLeft(84).reduced(2));
        clear_.setBounds(header.removeFromLeft(110).reduced(2));
        guide_.setBounds(header.reduced(5, 0));
        auto page_row = area.removeFromTop(36);
        for (std::size_t page = 0U; page < pages_.size(); ++page) {
            pages_[page].setBounds(page_row.removeFromLeft(page_row.getWidth()
                / static_cast<int>(pages_.size() - page)).reduced(3));
        }
        impact_.setBounds(area.removeFromTop(72).reduced(3));
        area.removeFromTop(3);
        auto top = area.removeFromTop(145);
        top_group_.setBounds(top);
        layoutRow(top.reduced(8, 20), 0U);
        area.removeFromTop(3);
        auto bottom = area.removeFromTop(145);
        bottom_group_.setBounds(bottom);
        layoutRow(bottom.reduced(8, 20), 8U);
    }

private:
    void layoutRow(juce::Rectangle<int> area, std::size_t first) {
        for (std::size_t column = 0U; column < 8U; ++column) {
            auto cell = area.removeFromLeft(area.getWidth()
                / static_cast<int>(8U - column)).reduced(3);
            labels_[first + column].setBounds(cell.removeFromTop(18));
            sliders_[first + column].setBounds(cell);
        }
    }

    Dispatch dispatch_;
    juce::Label title_{};
    juce::Label guide_{};
    juce::TextButton run_{};
    juce::TextButton voice_{};
    juce::TextButton motion_{};
    juce::TextButton clear_{};
    std::array<juce::TextButton, 8> pages_{};
    std::array<juce::Slider, 16> sliders_{};
    std::array<juce::Label, 16> labels_{};
    juce::GroupComponent top_group_{};
    juce::GroupComponent bottom_group_{};
    PamplistImpactComponent impact_{};
    bool updating_{};
};

class MainComponent final
    : public juce::Component,
      private juce::Timer {
public:
    MainComponent()
        : tide_panel_([this](auto kind, auto index, auto value) {
              return engine_.submitEvent(kind, index, value);
          }),
          pamplist_panel_([this](auto kind, auto index, auto value) {
              return engine_.submitEvent(kind, index, value);
          }) {
        setOpaque(true);
        title_.setText("LAYERWELL", juce::dontSendNotification);
        title_.setFont(juce::FontOptions{26.0F, juce::Font::bold});
        title_.setColour(juce::Label::textColourId, juce::Colour{0xff67e8d0});
        addAndMakeVisible(title_);
        subtitle_.setText(
            "Tide Pit + Pamplist  /  one embedded workspace  /  three source-only layers",
            juce::dontSendNotification);
        subtitle_.setColour(juce::Label::textColourId, juce::Colour{0xffa9b3bd});
        addAndMakeVisible(subtitle_);

        audio_.setButtonText("Start 48 kHz audio");
        audio_.onClick = [this] {
            if (engine_.audioActive()) {
                engine_.stopAudio();
                status_.setText("Audio stopped", juce::dontSendNotification);
            } else {
                status_.setText(engine_.startAudio(), juce::dontSendNotification);
            }
        };
        refresh_midi_.setButtonText("Refresh MIDI");
        refresh_midi_.onClick = [this] { refreshMidi(); };
        input_.onChange = [this] { selectInput(); };
        output_.onChange = [this] { selectOutput(); };
        addAndMakeVisible(audio_);
        addAndMakeVisible(refresh_midi_);
        addAndMakeVisible(input_);
        addAndMakeVisible(output_);

        previous_source_.setButtonText("< SOURCE");
        next_source_.setButtonText("SOURCE >");
        tide_tab_.setButtonText("TIDE PIT");
        pamplist_tab_.setButtonText("PAMPLIST");
        previous_source_.onClick = [this] {
            engine_.submitEvent(layerwell::EventKind::source_previous);
        };
        next_source_.onClick = [this] {
            engine_.submitEvent(layerwell::EventKind::source_next);
        };
        tide_tab_.onClick = [this] {
            engine_.submitEvent(layerwell::EventKind::select_source, 0U);
        };
        pamplist_tab_.onClick = [this] {
            engine_.submitEvent(layerwell::EventKind::select_source, 1U);
        };
        addAndMakeVisible(previous_source_);
        addAndMakeVisible(next_source_);
        addAndMakeVisible(tide_tab_);
        addAndMakeVisible(pamplist_tab_);
        addAndMakeVisible(tide_panel_);
        addAndMakeVisible(pamplist_panel_);

        for (std::size_t layer = 0U; layer < layer_select_.size(); ++layer) {
            layer_select_[layer].onClick = [this, layer] {
                engine_.submitEvent(layerwell::EventKind::select_layer,
                    static_cast<std::uint8_t>(layer));
            };
            layer_mute_[layer].setButtonText("MUTE");
            layer_mute_[layer].onClick = [this, layer] {
                engine_.submitEvent(layerwell::EventKind::toggle_layer_mute,
                    static_cast<std::uint8_t>(layer));
            };
            configureLinear(level_[layer], 0.0, 1.0, 0.001, [this, layer] {
                if (!updating_) engine_.submitEvent(
                    layerwell::EventKind::set_layer_level,
                    static_cast<std::uint8_t>(layer), level_[layer].getValue());
            });
            configureLinear(pan_[layer], -1.0, 1.0, 0.001, [this, layer] {
                if (!updating_) engine_.submitEvent(
                    layerwell::EventKind::set_layer_pan,
                    static_cast<std::uint8_t>(layer), pan_[layer].getValue());
            });
            addAndMakeVisible(layer_select_[layer]);
            addAndMakeVisible(layer_mute_[layer]);
            addAndMakeVisible(level_[layer]);
            addAndMakeVisible(pan_[layer]);
        }
        capture_.setButtonText("CAPTURE / ARM / CANCEL");
        capture_.onClick = [this] {
            engine_.submitEvent(layerwell::EventKind::capture_press);
        };
        monitor_toggle_.setButtonText("SOURCE MONITOR");
        monitor_toggle_.onClick = [this] {
            engine_.submitEvent(layerwell::EventKind::toggle_monitor);
        };
        clear_layer_.setButtonText("CLEAR SELECTED");
        clear_layer_.onClick = [this] {
            engine_.submitEvent(layerwell::EventKind::clear_selected_layer);
        };
        reset_trim_.setButtonText("RESET TRIM");
        reset_trim_.onClick = [this] {
            engine_.submitEvent(layerwell::EventKind::reset_trim);
        };
        addAndMakeVisible(capture_);
        addAndMakeVisible(monitor_toggle_);
        addAndMakeVisible(clear_layer_);
        addAndMakeVisible(reset_trim_);

        configureLinear(trim_start_, 0.0, 1.0, 1.0, [this] {
            if (!updating_) engine_.submitEvent(
                layerwell::EventKind::set_trim_start, 0U, trim_start_.getValue());
        });
        configureLinear(trim_end_, 0.0, 1.0, 1.0, [this] {
            if (!updating_) engine_.submitEvent(
                layerwell::EventKind::set_trim_end, 0U, trim_end_.getValue());
        });
        configureLinear(monitor_gain_, 0.0, 1.0, 0.001, [this] {
            if (!updating_) engine_.submitEvent(
                layerwell::EventKind::set_monitor_level, 0U, monitor_gain_.getValue());
        });
        configureLinear(master_, 0.0, 1.0, 0.001, [this] {
            if (!updating_) engine_.submitEvent(
                layerwell::EventKind::set_master_level, 0U, master_.getValue());
        });
        addAndMakeVisible(trim_start_);
        addAndMakeVisible(trim_end_);
        addAndMakeVisible(monitor_gain_);
        addAndMakeVisible(master_);
        trim_label_.setColour(juce::Label::textColourId, juce::Colour{0xffd5dce5});
        trim_label_.setFont(juce::FontOptions{12.0F, juce::Font::bold});
        addAndMakeVisible(trim_label_);
        status_.setText(
            "Built prototype: audio and MIDI remain closed until explicitly selected",
            juce::dontSendNotification);
        status_.setColour(juce::Label::textColourId, juce::Colour{0xff91a0b3});
        addAndMakeVisible(status_);

        refreshMidi();
        setSize(1320, 900);
        startTimerHz(kUiRefreshHz);
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff0b0f12});
        graphics.setColour(juce::Colour{0xff202930});
        graphics.fillRoundedRectangle(sampler_bounds_.toFloat(), 8.0F);
        graphics.setColour(juce::Colour{0xff46515e});
        graphics.drawRoundedRectangle(sampler_bounds_.toFloat(), 8.0F, 1.0F);
        graphics.setColour(juce::Colour{0xffa9b3bd});
        graphics.setFont(juce::FontOptions{12.0F, juce::Font::bold});
        auto sampler_title = sampler_bounds_;
        graphics.drawText("PERMANENT SAMPLER STRIP", sampler_title.removeFromTop(20),
            juce::Justification::centredLeft, false);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(14);
        auto header = area.removeFromTop(34);
        title_.setBounds(header.removeFromLeft(180));
        subtitle_.setBounds(header);
        auto lifecycle = area.removeFromTop(34);
        audio_.setBounds(lifecycle.removeFromLeft(150));
        lifecycle.removeFromLeft(6);
        input_.setBounds(lifecycle.removeFromLeft(260));
        lifecycle.removeFromLeft(6);
        output_.setBounds(lifecycle.removeFromLeft(260));
        lifecycle.removeFromLeft(6);
        refresh_midi_.setBounds(lifecycle.removeFromLeft(120));
        area.removeFromTop(5);
        auto sources = area.removeFromTop(38);
        previous_source_.setBounds(sources.removeFromLeft(110).reduced(2));
        tide_tab_.setBounds(sources.removeFromLeft(180).reduced(2));
        pamplist_tab_.setBounds(sources.removeFromLeft(180).reduced(2));
        next_source_.setBounds(sources.removeFromLeft(110).reduced(2));
        area.removeFromTop(5);
        status_.setBounds(area.removeFromBottom(28));
        area.removeFromBottom(5);
        sampler_bounds_ = area.removeFromBottom(220);
        layoutSampler(sampler_bounds_.reduced(10, 22));
        area.removeFromBottom(6);
        tide_panel_.setBounds(area);
        pamplist_panel_.setBounds(area);
    }

private:
    static void configureLinear(
        juce::Slider& slider,
        double minimum,
        double maximum,
        double interval,
        std::function<void()> callback) {
        slider.setSliderStyle(juce::Slider::LinearHorizontal);
        slider.setTextBoxStyle(juce::Slider::TextBoxRight, false, 72, 18);
        slider.setRange(minimum, maximum, interval);
        slider.onValueChange = std::move(callback);
    }

    void layoutSampler(juce::Rectangle<int> area) {
        auto left = area.removeFromLeft(760);
        auto cards = left.removeFromTop(118);
        for (std::size_t layer = 0U; layer < 3U; ++layer) {
            auto card = cards.removeFromLeft(cards.getWidth()
                / static_cast<int>(3U - layer)).reduced(4);
            auto buttons = card.removeFromTop(28);
            layer_select_[layer].setBounds(buttons.removeFromLeft(150));
            layer_mute_[layer].setBounds(buttons);
            level_[layer].setBounds(card.removeFromTop(36));
            pan_[layer].setBounds(card.removeFromTop(36));
        }
        auto actions = left.removeFromTop(36);
        capture_.setBounds(actions.removeFromLeft(230).reduced(3));
        monitor_toggle_.setBounds(actions.removeFromLeft(170).reduced(3));
        clear_layer_.setBounds(actions.removeFromLeft(160).reduced(3));

        area.removeFromLeft(8);
        auto trim = area.removeFromLeft(360);
        trim_label_.setBounds(trim.removeFromTop(24));
        trim_start_.setBounds(trim.removeFromTop(38));
        trim_end_.setBounds(trim.removeFromTop(38));
        reset_trim_.setBounds(trim.removeFromTop(30).reduced(3));
        area.removeFromLeft(8);
        monitor_gain_.setBounds(area.removeFromTop(42));
        master_.setBounds(area.removeFromTop(42));
    }

    void timerCallback() override {
        const auto snapshot = engine_.acceptedSnapshot();
        updating_ = true;
        const auto tide_selected = snapshot.selected_source
            == layerwell::SourceId::tide_pit;
        tide_panel_.setVisible(tide_selected);
        pamplist_panel_.setVisible(!tide_selected);
        tide_tab_.setToggleState(tide_selected, juce::dontSendNotification);
        pamplist_tab_.setToggleState(!tide_selected, juce::dontSendNotification);
        tide_tab_.setEnabled(snapshot.prepared);
        pamplist_tab_.setEnabled(snapshot.prepared);
        previous_source_.setEnabled(snapshot.prepared);
        next_source_.setEnabled(snapshot.prepared);
        if (tide_selected) tide_panel_.applySnapshot(snapshot);
        else pamplist_panel_.applySnapshot(snapshot);

        for (std::size_t layer = 0U; layer < 3U; ++layer) {
            const auto& state = snapshot.layers[layer];
            layer_select_[layer].setButtonText(
                "LAYER " + juce::String(static_cast<int>(layer + 1U))
                + (state.occupied
                    ? "  " + juce::String(state.recorded_length_frames)
                        + " @" + juce::String(state.playback_offset_frames)
                    : "  EMPTY"));
            layer_select_[layer].setToggleState(
                snapshot.selected_layer == layer, juce::dontSendNotification);
            layer_mute_[layer].setToggleState(state.muted, juce::dontSendNotification);
            level_[layer].setValue(state.level, juce::dontSendNotification);
            pan_[layer].setValue(state.pan, juce::dontSendNotification);
            layer_select_[layer].setEnabled(snapshot.prepared);
            layer_mute_[layer].setEnabled(snapshot.prepared);
            level_[layer].setEnabled(snapshot.prepared);
            pan_[layer].setEnabled(snapshot.prepared);
        }
        capture_.setButtonText(
            "CAPTURE  /  " + juce::String{layerwell::captureStateName(snapshot.capture_state)});
        capture_.setEnabled(snapshot.prepared);
        monitor_toggle_.setToggleState(
            snapshot.monitor_enabled, juce::dontSendNotification);
        monitor_toggle_.setEnabled(snapshot.prepared);
        clear_layer_.setEnabled(snapshot.prepared
            && snapshot.capture_state == layerwell::CaptureState::idle);

        const auto extent = std::max<std::uint32_t>(snapshot.trim_extent_frames, 1U);
        trim_start_.setRange(0.0, extent, 1.0);
        trim_end_.setRange(0.0, extent, 1.0);
        trim_start_.setValue(snapshot.trim_start_frames, juce::dontSendNotification);
        trim_end_.setValue(snapshot.trim_end_frames, juce::dontSendNotification);
        trim_start_.setEnabled(snapshot.trim_available);
        trim_end_.setEnabled(snapshot.trim_available);
        reset_trim_.setEnabled(snapshot.trim_available);
        const auto milliseconds = static_cast<double>(snapshot.loop_length_frames)
            * 1000.0 / layerwell::kSampleRate;
        trim_label_.setText(
            "TRIM  " + juce::String(snapshot.trim_start_frames)
                + " — " + juce::String(snapshot.trim_end_frames)
                + "  /  " + juce::String(milliseconds, 1) + " ms"
                + (snapshot.trim_available ? "  READY" : "  LOCKED"),
            juce::dontSendNotification);
        monitor_gain_.setValue(snapshot.monitor_level, juce::dontSendNotification);
        master_.setValue(snapshot.master_level, juce::dontSendNotification);
        monitor_gain_.setEnabled(snapshot.prepared);
        master_.setEnabled(snapshot.prepared);
        monitor_gain_.setTooltip("Source monitor level");
        master_.setTooltip("Master output level");
        audio_.setButtonText(engine_.audioActive()
            ? "Stop audio" : "Start 48 kHz audio");
        status_.setText(engine_.diagnosticsText(), juce::dontSendNotification);
        updating_ = false;
        engine_.pumpFeedback();
    }

    void refreshMidi() {
        inputs_ = engine_.availableMidiInputs();
        outputs_ = engine_.availableMidiOutputs();
        input_.clear(juce::dontSendNotification);
        output_.clear(juce::dontSendNotification);
        input_.addItem("MIDI input off", 1);
        output_.addItem("MIDI output off", 1);
        for (int index = 0; index < inputs_.size(); ++index) {
            input_.addItem(inputs_[index].name, index + 2);
        }
        for (int index = 0; index < outputs_.size(); ++index) {
            output_.addItem(outputs_[index].name, index + 2);
        }
        input_.setSelectedId(1, juce::dontSendNotification);
        output_.setSelectedId(1, juce::dontSendNotification);
    }

    void selectInput() {
        const auto index = input_.getSelectedId() - 2;
        status_.setText(
            index >= 0 && index < inputs_.size()
                ? engine_.selectMidiInput(inputs_[index])
                : engine_.selectMidiInput(juce::MidiDeviceInfo{}),
            juce::dontSendNotification);
    }

    void selectOutput() {
        const auto index = output_.getSelectedId() - 2;
        status_.setText(
            index >= 0 && index < outputs_.size()
                ? engine_.selectMidiOutput(outputs_[index])
                : engine_.selectMidiOutput(juce::MidiDeviceInfo{}),
            juce::dontSendNotification);
    }

    LayerwellEngine engine_{};
    juce::Array<juce::MidiDeviceInfo> inputs_{};
    juce::Array<juce::MidiDeviceInfo> outputs_{};
    juce::Label title_{};
    juce::Label subtitle_{};
    juce::Label status_{};
    juce::Label trim_label_{};
    juce::TextButton audio_{};
    juce::TextButton refresh_midi_{};
    juce::ComboBox input_{};
    juce::ComboBox output_{};
    juce::TextButton previous_source_{};
    juce::TextButton next_source_{};
    juce::TextButton tide_tab_{};
    juce::TextButton pamplist_tab_{};
    TidePanel tide_panel_;
    PamplistPanel pamplist_panel_;
    std::array<juce::TextButton, 3> layer_select_{};
    std::array<juce::TextButton, 3> layer_mute_{};
    std::array<juce::Slider, 3> level_{};
    std::array<juce::Slider, 3> pan_{};
    juce::TextButton capture_{};
    juce::TextButton monitor_toggle_{};
    juce::TextButton clear_layer_{};
    juce::TextButton reset_trim_{};
    juce::Slider trim_start_{};
    juce::Slider trim_end_{};
    juce::Slider monitor_gain_{};
    juce::Slider master_{};
    juce::TooltipWindow tooltips_{this, 500};
    juce::Rectangle<int> sampler_bounds_{};
    bool updating_{};
};

class LayerwellApplication final : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "Layerwell"; }
    const juce::String getApplicationVersion() override { return "0.2.0"; }
    bool moreThanOneInstanceAllowed() override { return false; }

    void initialise(const juce::String&) override {
        window_ = std::make_unique<Window>(getApplicationName());
    }

    void shutdown() override { window_.reset(); }
    void systemRequestedQuit() override { quit(); }

private:
    class Window final : public juce::DocumentWindow {
    public:
        explicit Window(const juce::String& name)
            : DocumentWindow(
                  name,
                  juce::Colour{0xff0b0f12},
                  DocumentWindow::allButtons) {
            setUsingNativeTitleBar(true);
            setContentOwned(new MainComponent(), true);
            setResizable(false, false);
            centreWithSize(getWidth(), getHeight());
            setVisible(true);
        }

        void closeButtonPressed() override {
            juce::JUCEApplication::getInstance()->systemRequestedQuit();
        }
    };

    std::unique_ptr<Window> window_{};
};

}  // namespace

START_JUCE_APPLICATION(LayerwellApplication)
