#include "layerwell/core.hpp"
#include "layerwell/launch_control_3.hpp"
#include "layerwell/state_snapshot.hpp"

#include "schuss/instrument_lab/bounded_midi.hpp"

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>

namespace {

constexpr int kRequestedBlockFrames = 128;
constexpr int kUiRefreshHz = 15;

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
        if (audio_ready_.load(std::memory_order_acquire)) {
            return "Audio already active";
        }
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
        return "Audio requested; callback state will report readiness";
    }

    void stopAudio() {
        audio_ready_.store(false, std::memory_order_release);
        device_manager_.removeAudioCallback(this);
        device_manager_.closeAudioDevice();
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

    void injectCc(int channel, int controller, int value) {
        if (!audio_ready_.load(std::memory_order_acquire)) return;
        auto message = juce::MidiMessage::controllerEvent(channel, controller, value);
        message.setTimeStamp(juce::Time::getMillisecondCounterHiRes() * 0.001);
        collector_.addMessageToQueue(message);
    }

    void injectMixerAction(int controller) {
        injectCc(7, 30, 1);
        injectCc(1, controller, 127);
        injectCc(1, controller, 0);
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
        juce::String result = audio_ready_.load(std::memory_order_acquire)
            ? "AUDIO 48K ACTIVE"
            : "AUDIO STOPPED";
        result += "  |  BLOCK "
            + juce::String(callback_block_frames_.load(std::memory_order_acquire));
        result += "  |  LOOP " + juce::String(snapshot.loop_length_frames);
        result += "  |  PHASE " + juce::String(snapshot.phase_frames);
        result += "  |  EVENTS " + juce::String(snapshot.diagnostics.accepted_events)
            + "/" + juce::String(snapshot.diagnostics.dropped_events);
        result += "  |  LIMIT " + juce::String(snapshot.diagnostics.limited_samples);
        if (selected_input_identifier_.isEmpty()) result += "  |  MIDI IN OFF";
        else result += "  |  IN " + selected_input_name_;
        if (selected_output_identifier_.isEmpty()) result += "  |  MIDI OUT OFF";
        else result += "  |  OUT " + selected_output_name_;
        result += "  |  RX "
            + juce::String(received_midi_.load(std::memory_order_acquire));
        result += " / MAP "
            + juce::String(mapped_midi_.load(std::memory_order_acquire));
        if (unsupported_callbacks_.load(std::memory_order_acquire) != 0U) {
            result += "  |  UNSUPPORTED CALLBACK "
                + juce::String(unsupported_callbacks_.load(std::memory_order_acquire));
        }
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
        if (!audio_ready_.load(std::memory_order_acquire)
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

        midi_block_.clear();
        collector_.removeNextBlockOfMessages(midi_block_, frames);
        std::array<layerwell::Event, layerwell::kMaximumEvents + 1U> events{};
        std::size_t event_count = 0U;
        for (const auto metadata : midi_block_) {
            const auto sequence = ingress_sequence_.next();
            const auto result = input_adapter_.parse(
                metadata.data,
                metadata.numBytes > 0
                    ? static_cast<std::size_t>(metadata.numBytes)
                    : 0U,
                schuss::instrument_lab::clampSampleOffset(
                    metadata.samplePosition,
                    static_cast<std::uint32_t>(frames)),
                sequence);
            if (!result.has_event) continue;
            mapped_midi_.fetch_add(1U, std::memory_order_relaxed);
            if (event_count < events.size()) events[event_count++] = result.event;
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
                std::fill_n(outputs[channel], frames, 0.0f);
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
    std::atomic<std::uint64_t> unsupported_callbacks_{0U};
};

class MainComponent final
    : public juce::Component,
      private juce::Timer {
public:
    MainComponent() {
        setOpaque(true);
        title_.setText("LAYERWELL", juce::dontSendNotification);
        title_.setFont(juce::FontOptions(28.0f, juce::Font::bold));
        title_.setColour(juce::Label::textColourId, juce::Colour{0xff67e8d0});
        addAndMakeVisible(title_);

        subtitle_.setText(
            "two resident sources  |  three source-only layers  |  regular Launch Control 3 DAW mode",
            juce::dontSendNotification);
        subtitle_.setColour(juce::Label::textColourId, juce::Colour{0xffa9b3bd});
        addAndMakeVisible(subtitle_);

        start_audio_.setButtonText("Start 48 kHz Audio");
        start_audio_.onClick = [this] {
            status_.setText(engine_.startAudio(), juce::dontSendNotification);
        };
        addAndMakeVisible(start_audio_);

        refresh_midi_.setButtonText("Refresh MIDI");
        refresh_midi_.onClick = [this] { refreshMidi(); };
        addAndMakeVisible(refresh_midi_);
        input_.onChange = [this] { selectInput(); };
        output_.onChange = [this] { selectOutput(); };
        addAndMakeVisible(input_);
        addAndMakeVisible(output_);

        previous_source_.setButtonText("Previous Source");
        next_source_.setButtonText("Next Source");
        previous_source_.onClick = [this] { engine_.injectCc(1, 106, 127); };
        next_source_.onClick = [this] { engine_.injectCc(1, 107, 127); };
        addAndMakeVisible(previous_source_);
        addAndMakeVisible(next_source_);
        source_.setFont(juce::FontOptions(22.0f, juce::Font::bold));
        source_.setJustificationType(juce::Justification::centred);
        source_.setColour(juce::Label::textColourId, juce::Colour{0xfff2f5f7});
        addAndMakeVisible(source_);

        for (std::size_t layer = 0U; layer < layer_buttons_.size(); ++layer) {
            layer_buttons_[layer].setButtonText("Layer " + juce::String(layer + 1U));
            layer_buttons_[layer].onClick = [this, layer] {
                engine_.injectMixerAction(37 + static_cast<int>(layer));
            };
            mute_buttons_[layer].setButtonText("Mute");
            mute_buttons_[layer].onClick = [this, layer] {
                engine_.injectMixerAction(40 + static_cast<int>(layer));
            };
            addAndMakeVisible(layer_buttons_[layer]);
            addAndMakeVisible(mute_buttons_[layer]);
        }
        capture_.setButtonText("Capture / Arm / Cancel");
        capture_.onClick = [this] { engine_.injectMixerAction(43); };
        monitor_.setButtonText("Source Monitor");
        monitor_.onClick = [this] { engine_.injectMixerAction(44); };
        addAndMakeVisible(capture_);
        addAndMakeVisible(monitor_);

        status_.setText(
            "App built successfully; audio and MIDI remain closed until explicitly selected",
            juce::dontSendNotification);
        status_.setColour(juce::Label::textColourId, juce::Colour{0xffa9b3bd});
        status_.setJustificationType(juce::Justification::centredLeft);
        addAndMakeVisible(status_);

        refreshMidi();
        setSize(920, 440);
        startTimerHz(kUiRefreshHz);
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff101417});
        graphics.setColour(juce::Colour{0xff242b30});
        graphics.fillRoundedRectangle(
            getLocalBounds().reduced(18).toFloat(), 12.0f);
    }

    void resized() override {
        auto bounds = getLocalBounds().reduced(28);
        title_.setBounds(bounds.removeFromTop(38));
        subtitle_.setBounds(bounds.removeFromTop(28));
        bounds.removeFromTop(10);
        auto setup = bounds.removeFromTop(34);
        start_audio_.setBounds(setup.removeFromLeft(170));
        setup.removeFromLeft(8);
        input_.setBounds(setup.removeFromLeft(210));
        setup.removeFromLeft(8);
        output_.setBounds(setup.removeFromLeft(210));
        setup.removeFromLeft(8);
        refresh_midi_.setBounds(setup.removeFromLeft(130));
        bounds.removeFromTop(18);

        auto source_row = bounds.removeFromTop(52);
        previous_source_.setBounds(source_row.removeFromLeft(160));
        next_source_.setBounds(source_row.removeFromRight(160));
        source_.setBounds(source_row.reduced(12, 0));
        bounds.removeFromTop(20);

        auto layers = bounds.removeFromTop(92);
        const auto card_width = layers.getWidth() / 3;
        for (std::size_t layer = 0U; layer < layer_buttons_.size(); ++layer) {
            auto card = layers.removeFromLeft(card_width).reduced(8);
            layer_buttons_[layer].setBounds(card.removeFromTop(44));
            card.removeFromTop(6);
            mute_buttons_[layer].setBounds(card.removeFromTop(32));
        }
        bounds.removeFromTop(14);
        auto actions = bounds.removeFromTop(42);
        capture_.setBounds(actions.removeFromLeft(260));
        actions.removeFromLeft(12);
        monitor_.setBounds(actions.removeFromLeft(180));
        bounds.removeFromTop(16);
        status_.setBounds(bounds.removeFromTop(54));
    }

private:
    void timerCallback() override {
        const auto snapshot = engine_.acceptedSnapshot();
        source_.setText(
            layerwell::sourceName(snapshot.selected_source),
            juce::dontSendNotification);
        for (std::size_t layer = 0U; layer < layer_buttons_.size(); ++layer) {
            const auto selected = snapshot.selected_layer == layer;
            layer_buttons_[layer].setColour(
                juce::TextButton::buttonColourId,
                selected ? juce::Colour{0xff177f73} : juce::Colour{0xff353d43});
            mute_buttons_[layer].setColour(
                juce::TextButton::buttonColourId,
                snapshot.layers[layer].muted
                    ? juce::Colour{0xff8f3028}
                    : juce::Colour{0xff353d43});
            layer_buttons_[layer].setButtonText(
                "Layer " + juce::String(layer + 1U)
                + (snapshot.layers[layer].occupied ? "  READY" : "  EMPTY"));
        }
        capture_.setButtonText(
            "Capture  |  " + juce::String{
                layerwell::captureStateName(snapshot.capture_state)});
        monitor_.setToggleState(snapshot.monitor_enabled, juce::dontSendNotification);
        status_.setText(
            engine_.diagnosticsText(), juce::dontSendNotification);
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
        if (index >= 0 && index < inputs_.size()) {
            status_.setText(
                engine_.selectMidiInput(inputs_[index]),
                juce::dontSendNotification);
        } else {
            status_.setText(
                engine_.selectMidiInput(juce::MidiDeviceInfo{}),
                juce::dontSendNotification);
        }
    }

    void selectOutput() {
        const auto index = output_.getSelectedId() - 2;
        if (index >= 0 && index < outputs_.size()) {
            status_.setText(
                engine_.selectMidiOutput(outputs_[index]),
                juce::dontSendNotification);
        } else {
            status_.setText(
                engine_.selectMidiOutput(juce::MidiDeviceInfo{}),
                juce::dontSendNotification);
        }
    }

    LayerwellEngine engine_{};
    juce::Array<juce::MidiDeviceInfo> inputs_{};
    juce::Array<juce::MidiDeviceInfo> outputs_{};
    juce::Label title_{};
    juce::Label subtitle_{};
    juce::Label source_{};
    juce::Label status_{};
    juce::TextButton start_audio_{};
    juce::TextButton refresh_midi_{};
    juce::ComboBox input_{};
    juce::ComboBox output_{};
    juce::TextButton previous_source_{};
    juce::TextButton next_source_{};
    std::array<juce::TextButton, layerwell::kLayerCount> layer_buttons_{};
    std::array<juce::TextButton, layerwell::kLayerCount> mute_buttons_{};
    juce::TextButton capture_{};
    juce::ToggleButton monitor_{};
};

class LayerwellApplication final : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "Layerwell"; }
    const juce::String getApplicationVersion() override { return "0.1.0"; }
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
                juce::Colour{0xff101417},
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
