#include "tidepit/juce_midi_adapter.hpp"
#include "tidepit/ui_model.hpp"

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <memory>
#include <string>

namespace {

constexpr int kRequestedBlockFrames = 128;
constexpr std::size_t kUiMailboxCapacity = 8;
constexpr std::size_t kScopeMailboxCapacity = 4;

struct UiFrame {
    tidepit::Snapshot snapshot{};
    tidepit::Diagnostics core_diagnostics{};
    tidepit::MidiAdapterDiagnostics midi_diagnostics{};
    std::uint64_t host_event_drops{};
};

template <typename Value, std::size_t Capacity>
class SpscMailbox final {
public:
    static_assert(Capacity >= 2U);

    void reset() noexcept {
        read_.store(0, std::memory_order_relaxed);
        write_.store(0, std::memory_order_relaxed);
    }

    bool publish(const Value& value) noexcept {
        const auto write = write_.load(std::memory_order_relaxed);
        const auto next = increment(write);
        if (next == read_.load(std::memory_order_acquire)) return false;
        values_[write] = value;
        write_.store(next, std::memory_order_release);
        return true;
    }

    bool consumeLatest(Value& value) noexcept {
        auto read = read_.load(std::memory_order_relaxed);
        const auto write = write_.load(std::memory_order_acquire);
        if (read == write) return false;
        while (read != write) {
            value = values_[read];
            read = increment(read);
        }
        read_.store(read, std::memory_order_release);
        return true;
    }

private:
    static constexpr std::size_t increment(std::size_t value) noexcept {
        return (value + 1U) % Capacity;
    }

    std::array<Value, Capacity> values_{};
    std::atomic<std::size_t> read_{0};
    std::atomic<std::size_t> write_{0};
};

class InstrumentAudioEngine final
    : public juce::AudioIODeviceCallback,
      public juce::MidiInputCallback {
public:
    InstrumentAudioEngine() {
        collector_.ensureStorageAllocated(16384);
        midi_block_.ensureSize(16384);
    }

    ~InstrumentAudioEngine() override {
        closeMidiInput();
        device_manager_.removeAudioCallback(this);
        device_manager_.closeAudioDevice();
    }

    juce::String start() {
        auto error = device_manager_.initialiseWithDefaultDevices(0, 2);
        if (error.isNotEmpty()) return "Audio output unavailable: " + error;

        auto setup = device_manager_.getAudioDeviceSetup();
        setup.sampleRate = tidepit::kReferenceSampleRate;
        setup.bufferSize = kRequestedBlockFrames;
        error = device_manager_.setAudioDeviceSetup(setup, true);
        if (error.isNotEmpty()) {
            device_manager_.closeAudioDevice();
            return "48 kHz stereo setup unavailable: " + error;
        }
        auto* device = device_manager_.getCurrentAudioDevice();
        if (device == nullptr
            || device->getCurrentSampleRate() != tidepit::kReferenceSampleRate
            || device->getCurrentBufferSizeSamples() < 1) {
            device_manager_.closeAudioDevice();
            return "Tide Pit requires an exact 48 kHz stereo output";
        }

        device_manager_.addAudioCallback(this);
        return ready_.load(std::memory_order_acquire)
            ? "48 kHz output active; select a MIDI input"
            : "Audio callback rejected the device configuration";
    }

    [[nodiscard]] juce::Array<juce::MidiDeviceInfo> availableMidiInputs() const {
        return juce::MidiInput::getAvailableDevices();
    }

    [[nodiscard]] const juce::String& selectedMidiInputIdentifier() const noexcept {
        return selected_midi_input_identifier_;
    }

    juce::String selectMidiInput(const juce::MidiDeviceInfo& device) {
        closeMidiInput();
        if (device.identifier.isEmpty()) return "MIDI input disabled";
        device_manager_.setMidiInputDeviceEnabled(device.identifier, true);
        if (!device_manager_.isMidiInputDeviceEnabled(device.identifier)) {
            return "Could not open MIDI input: " + device.name;
        }
        device_manager_.addMidiInputDeviceCallback(device.identifier, this);
        selected_midi_input_identifier_ = device.identifier;
        selected_midi_input_name_ = device.name;
        received_midi_messages_.store(0, std::memory_order_release);
        return "MIDI input active: " + device.name;
    }

    juce::String disableMidiInput() {
        closeMidiInput();
        return "MIDI input disabled";
    }

    [[nodiscard]] juce::String statusText(const UiFrame& frame) const {
        if (!ready_.load(std::memory_order_acquire)) return "Audio output unavailable";
        juce::String status = selected_midi_input_identifier_.isEmpty()
            ? "48 kHz | no MIDI input selected"
            : "MIDI: " + selected_midi_input_name_;
        status += " | raw "
            + juce::String(received_midi_messages_.load(std::memory_order_acquire));
        const auto& midi = frame.midi_diagnostics;
        if (midi.last_accepted_cc >= 0) {
            status += " | accepted ch " + juce::String(midi.last_accepted_channel)
                + " CC" + juce::String(midi.last_accepted_cc)
                + "=" + juce::String(midi.last_accepted_value);
        }
        const auto rejected = midi.malformed_messages + midi.ignored_channels
            + midi.unassigned_controllers + midi.unknown_controllers
            + midi.invalid_values;
        status += " | reject " + juce::String(rejected)
            + " drop " + juce::String(midi.dropped_events + frame.host_event_drops);
        return status;
    }

    void injectCc(std::uint8_t controller, std::uint8_t value) {
        if (!ready_.load(std::memory_order_acquire)) return;
        auto message = juce::MidiMessage::controllerEvent(
            tidepit::launchControlMidiChannel(),
            controller,
            value
        );
        message.setTimeStamp(juce::Time::getMillisecondCounterHiRes() * 0.001);
        collector_.addMessageToQueue(message);
    }

    bool consumeLatestFrame(UiFrame& frame) noexcept {
        return ui_mailbox_.consumeLatest(frame);
    }

    bool consumeLatestScope(tidepit::ScopeFrame& frame) noexcept {
        return scope_mailbox_.consumeLatest(frame);
    }

    void handleIncomingMidiMessage(
        juce::MidiInput*,
        const juce::MidiMessage& message
    ) override {
        received_midi_messages_.fetch_add(1, std::memory_order_relaxed);
        collector_.handleIncomingMidiMessage(nullptr, message);
    }

    void audioDeviceAboutToStart(juce::AudioIODevice* device) override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
        midi_adapter_.reset();
        bridge_.reset();
        ui_mailbox_.reset();
        scope_accumulator_.reset();
        scope_mailbox_.reset();
        midi_block_.clear();
        if (device == nullptr
            || device->getCurrentSampleRate() != tidepit::kReferenceSampleRate
            || device->getCurrentBufferSizeSamples() < 1) {
            return;
        }
        collector_.reset(tidepit::kReferenceSampleRate);
        auto core = std::make_unique<tidepit::Core>();
        if (!core->prepare(
                tidepit::kReferenceSampleRate,
                tidepit::kReferenceQuantumFrames)) {
            return;
        }
        core_ = std::move(core);
        publishUiFrame();
        ready_.store(true, std::memory_order_release);
    }

    void audioDeviceStopped() override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
        scope_accumulator_.reset();
        midi_block_.clear();
    }

    void audioDeviceIOCallbackWithContext(
        const float* const*,
        int,
        float* const* output_channels,
        int output_channel_count,
        int frames,
        const juce::AudioIODeviceCallbackContext&
    ) override {
        clearOutputs(output_channels, output_channel_count, frames);
        if (!ready_.load(std::memory_order_acquire)
            || core_ == nullptr
            || output_channels == nullptr
            || output_channel_count < 2
            || output_channels[0] == nullptr
            || output_channels[1] == nullptr
            || frames < 1) {
            return;
        }

        midi_block_.clear();
        collector_.removeNextBlockOfMessages(midi_block_, frames);
        const auto adapted = midi_adapter_.adapt(
            midi_block_,
            static_cast<std::uint32_t>(frames)
        );
        bridge_.process(
            *core_,
            output_channels[0],
            output_channels[1],
            static_cast<std::uint32_t>(frames),
            adapted.events,
            adapted.event_count
        );
        for (int index = 0; index < frames; ++index) {
            if (const auto* completed = scope_accumulator_.pushSample(
                    output_channels[0][index],
                    output_channels[1][index]);
                completed != nullptr) {
                static_cast<void>(scope_mailbox_.publish(*completed));
            }
        }
        publishUiFrame();
    }

private:
    void publishUiFrame() noexcept {
        if (core_ == nullptr) return;
        const UiFrame frame{
            core_->snapshot(),
            core_->diagnostics(),
            midi_adapter_.diagnostics(),
            bridge_.adapter().droppedEvents(),
        };
        static_cast<void>(ui_mailbox_.publish(frame));
    }

    void closeMidiInput() {
        if (selected_midi_input_identifier_.isEmpty()) return;
        device_manager_.removeMidiInputDeviceCallback(
            selected_midi_input_identifier_,
            this
        );
        device_manager_.setMidiInputDeviceEnabled(
            selected_midi_input_identifier_,
            false
        );
        selected_midi_input_identifier_.clear();
        selected_midi_input_name_.clear();
    }

    static void clearOutputs(
        float* const* outputs,
        int output_channel_count,
        int frames
    ) noexcept {
        if (outputs == nullptr || frames <= 0) return;
        for (int channel = 0; channel < output_channel_count; ++channel) {
            if (outputs[channel] != nullptr) {
                std::fill_n(outputs[channel], frames, 0.0f);
            }
        }
    }

    juce::AudioDeviceManager device_manager_;
    juce::MidiMessageCollector collector_;
    juce::MidiBuffer midi_block_;
    tidepit::JuceMidiAdapter midi_adapter_;
    tidepit::ParameterizedQ27HostBridge bridge_;
    SpscMailbox<UiFrame, kUiMailboxCapacity> ui_mailbox_;
    tidepit::ScopeAccumulator scope_accumulator_;
    SpscMailbox<tidepit::ScopeFrame, kScopeMailboxCapacity> scope_mailbox_;
    std::unique_ptr<tidepit::Core> core_;
    std::atomic<bool> ready_{false};
    std::atomic<std::uint64_t> received_midi_messages_{0};
    juce::String selected_midi_input_identifier_;
    juce::String selected_midi_input_name_;
};

std::uint8_t midiForRoot(std::int32_t root) noexcept {
    std::uint8_t best = 0;
    auto best_distance = std::numeric_limits<std::int32_t>::max();
    for (std::uint16_t value = 0; value < 128U; ++value) {
        const auto distance = std::abs(
            tidepit::rootNoteFromMidi(static_cast<std::uint8_t>(value)) - root
        );
        if (distance < best_distance) {
            best_distance = distance;
            best = static_cast<std::uint8_t>(value);
        }
    }
    return best;
}

double valueForControl(tidepit::ControlId id, const tidepit::Snapshot& snapshot) noexcept {
    using Id = tidepit::ControlId;
    switch (id) {
        case Id::set_stage_1: return snapshot.controls.stages[0];
        case Id::set_stage_2: return snapshot.controls.stages[1];
        case Id::set_stage_3: return snapshot.controls.stages[2];
        case Id::set_stage_4: return snapshot.controls.stages[3];
        case Id::set_rate: return snapshot.controls.rate;
        case Id::set_memory: return snapshot.controls.memory;
        case Id::set_material: return snapshot.controls.material;
        case Id::set_position: return snapshot.controls.position;
        case Id::set_fx_a: return snapshot.effective_fx_a;
        case Id::set_fx_b: return snapshot.effective_fx_b;
        case Id::set_root: return snapshot.controls.root_note;
        default: return 0.0;
    }
}

class OscilloscopeComponent final : public juce::Component {
public:
    OscilloscopeComponent() {
        setName("Stereo output oscilloscope");
        setInterceptsMouseClicks(false, false);
    }

    void setFrame(const tidepit::ScopeFrame& frame) {
        if (frame.generation == frame_.generation) return;
        frame_ = frame;
        repaint();
    }

    void paint(juce::Graphics& graphics) override {
        const auto bounds = getLocalBounds().toFloat();
        graphics.setColour(juce::Colour(0xff181d1f));
        graphics.fillRect(bounds);
        graphics.setColour(juce::Colour(0xff3a4448));
        graphics.drawRect(bounds.reduced(0.5f), 1.0f);

        auto header = bounds.reduced(8.0f, 4.0f).removeFromTop(18.0f);
        graphics.setFont(juce::FontOptions(11.0f, juce::Font::bold));
        graphics.setColour(juce::Colour(0xffd9dee1));
        graphics.drawText("STEREO OUTPUT SCOPE", header, juce::Justification::centredLeft);

        if (frame_.sample_count > 1) {
            const auto peaks = "L " + peakText(frame_.peak_left)
                + "   R " + peakText(frame_.peak_right);
            graphics.setColour(juce::Colour(0xff89969c));
            graphics.drawText(peaks, header, juce::Justification::centredRight);
        }

        auto plot = bounds.reduced(8.0f, 5.0f);
        plot.removeFromTop(20.0f);
        graphics.setColour(juce::Colour(0xff2c3437));
        graphics.drawHorizontalLine(
            juce::roundToInt(plot.getCentreY()),
            plot.getX(),
            plot.getRight()
        );
        for (int division = 1; division < 4; ++division) {
            const auto x = plot.getX()
                + plot.getWidth() * static_cast<float>(division) / 4.0f;
            graphics.drawVerticalLine(
                juce::roundToInt(x),
                plot.getY(),
                plot.getBottom()
            );
        }

        if (frame_.sample_count < 2) {
            graphics.setColour(juce::Colour(0xff687177));
            graphics.drawText(
                "waiting for 48 kHz audio",
                plot,
                juce::Justification::centred
            );
            return;
        }

        drawWaveform(graphics, plot, frame_.left, juce::Colour(0xffe7b75b));
        drawWaveform(graphics, plot, frame_.right, juce::Colour(0xff6fa9bd));
    }

private:
    static juce::String peakText(float peak) {
        if (peak <= 0.000001f) return "-inf dB";
        return juce::String(20.0f * std::log10(peak), 1) + " dB";
    }

    void drawWaveform(
        juce::Graphics& graphics,
        juce::Rectangle<float> plot,
        const std::array<float, tidepit::kScopeFrameSamples>& samples,
        juce::Colour colour
    ) const {
        juce::Path path;
        const auto width = std::max(1.0f, plot.getWidth() - 1.0f);
        const auto amplitude = plot.getHeight() * 0.46f;
        for (int pixel = 0; pixel < juce::roundToInt(plot.getWidth()); ++pixel) {
            const auto normalized_x = static_cast<float>(pixel) / width;
            const auto index = std::min(
                frame_.sample_count - 1,
                static_cast<std::size_t>(normalized_x
                    * static_cast<float>(frame_.sample_count - 1))
            );
            const auto x = plot.getX() + static_cast<float>(pixel);
            const auto y = plot.getCentreY()
                - std::clamp(samples[index], -1.0f, 1.0f) * amplitude;
            if (pixel == 0) {
                path.startNewSubPath(x, y);
            } else {
                path.lineTo(x, y);
            }
        }
        graphics.setColour(colour.withAlpha(0.86f));
        graphics.strokePath(path, juce::PathStrokeType(1.25f));
    }

    tidepit::ScopeFrame frame_{};
};

class MainComponent final
    : public juce::Component,
      private juce::Timer {
public:
    MainComponent() {
        title_.setText("TIDE PIT - GILLS", juce::dontSendNotification);
        title_.setFont(juce::FontOptions(23.0f, juce::Font::bold));
        title_.setColour(juce::Label::textColourId, juce::Colour(0xffe7b75b));
        addAndMakeVisible(title_);

        subtitle_.setText(
            "exact 48 kHz / 16-frame source | Launch Control 3 ch 16",
            juce::dontSendNotification
        );
        subtitle_.setColour(juce::Label::textColourId, juce::Colour(0xff9ca7ad));
        addAndMakeVisible(subtitle_);

        status_.setColour(juce::Label::textColourId, juce::Colour(0xff89a2b2));
        status_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(status_);

        midi_input_label_.setText("MIDI input", juce::dontSendNotification);
        midi_input_label_.setColour(juce::Label::textColourId, juce::Colour(0xffd9dee1));
        addAndMakeVisible(midi_input_label_);
        midi_input_selector_.onChange = [this] { applySelectedMidiInput(); };
        addAndMakeVisible(midi_input_selector_);
        refresh_midi_button_.setButtonText("Refresh MIDI");
        refresh_midi_button_.onClick = [this] { refreshMidiInputs(false); };
        addAndMakeVisible(refresh_midi_button_);

        mode_state_.setColour(juce::Label::textColourId, juce::Colour(0xffe7b75b));
        mode_state_.setFont(juce::FontOptions(14.0f, juce::Font::bold));
        addAndMakeVisible(mode_state_);
        for (auto& line : display_lines_) {
            line.setColour(juce::Label::textColourId, juce::Colour(0xffd7ddd9));
            line.setColour(juce::Label::backgroundColourId, juce::Colour(0xff181d1f));
            line.setFont(juce::FontOptions(
                juce::Font::getDefaultMonospacedFontName(),
                15.0f,
                juce::Font::plain
            ));
            line.setJustificationType(juce::Justification::centredLeft);
            addAndMakeVisible(line);
        }
        addAndMakeVisible(oscilloscope_);

        const auto& descriptors = tidepit::encoderDescriptors();
        for (std::size_t index = 0; index < encoders_.size(); ++index) {
            const auto& descriptor = descriptors[index];
            auto slider = std::make_unique<juce::Slider>();
            slider->setName(juce::String(descriptor.label.data(), descriptor.label.size()));
            slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, 58, 18);
            if (descriptor.id == tidepit::ControlId::set_root) {
                slider->setRange(36.0, 72.0, 1.0);
            } else {
                slider->setRange(0.0, 1.0, 0.001);
            }
            slider->setValue(descriptor.default_semantic_value, juce::dontSendNotification);
            slider->setDoubleClickReturnValue(true, descriptor.default_semantic_value);
            slider->setColour(juce::Slider::rotarySliderFillColourId, juce::Colour(0xffe7b75b));
            slider->setColour(juce::Slider::rotarySliderOutlineColourId, juce::Colour(0xff394247));
            slider->setColour(juce::Slider::textBoxTextColourId, juce::Colour(0xffedf1f2));
            slider->setColour(juce::Slider::textBoxBackgroundColourId, juce::Colour(0xff15191b));
            slider->setEnabled(descriptor.kind != tidepit::ControlKind::unassigned);
            slider->onValueChange = [this, index] {
                const auto& current = tidepit::encoderDescriptors()[index];
                if (current.kind == tidepit::ControlKind::unassigned) return;
                const auto raw = current.id == tidepit::ControlId::set_root
                    ? midiForRoot(juce::roundToInt(encoders_[index]->getValue()))
                    : static_cast<std::uint8_t>(std::clamp(
                          juce::roundToInt(encoders_[index]->getValue() * 127.0),
                          0,
                          127
                      ));
                engine_.injectCc(current.cc, raw);
            };
            addAndMakeVisible(*slider);
            encoders_[index] = std::move(slider);

            auto label = std::make_unique<juce::Label>();
            label->setText(
                juce::String(descriptor.label.data(), descriptor.label.size()),
                juce::dontSendNotification
            );
            label->setJustificationType(juce::Justification::centred);
            label->setColour(
                juce::Label::textColourId,
                descriptor.kind == tidepit::ControlKind::unassigned
                    ? juce::Colour(0xff687177)
                    : juce::Colour(0xffd9dee1)
            );
            label->setFont(juce::FontOptions(11.0f, juce::Font::bold));
            addAndMakeVisible(*label);
            encoder_labels_[index] = std::move(label);
        }

        const auto& button_descriptors = tidepit::buttonDescriptors();
        for (std::size_t index = 0; index < buttons_.size(); ++index) {
            const auto& descriptor = button_descriptors[index];
            auto button = std::make_unique<juce::TextButton>(
                juce::String(descriptor.label.data(), descriptor.label.size())
            );
            button->setColour(juce::TextButton::buttonColourId, juce::Colour(0xff293135));
            button->setColour(juce::TextButton::buttonOnColourId, juce::Colour(0xffe7b75b));
            button->setColour(juce::TextButton::textColourOffId, juce::Colour(0xffedf1f2));
            button->setColour(juce::TextButton::textColourOnId, juce::Colour(0xff15191b));
            button->setEnabled(descriptor.kind != tidepit::ControlKind::unassigned);
            button->setClickingTogglesState(false);
            button->onStateChange = [this, index] {
                const bool down = buttons_[index]->isDown();
                if (down == button_edges_[index]) return;
                button_edges_[index] = down;
                const auto& current = tidepit::buttonDescriptors()[index];
                engine_.injectCc(
                    current.cc,
                    down ? current.press_value : current.release_value
                );
            };
            addAndMakeVisible(*button);
            buttons_[index] = std::move(button);
        }

        applySnapshot(ui_frame_.snapshot);
        status_.setText(engine_.start(), juce::dontSendNotification);
        refreshMidiInputs(true);
        startTimerHz(30);
        setSize(1180, 650);
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour(0xff111516));
        graphics.setColour(juce::Colour(0xff30383c));
        graphics.drawLine(16.0f, 55.0f, static_cast<float>(getWidth() - 16), 55.0f, 1.0f);
        graphics.drawRect(getLocalBounds().toFloat().reduced(8.5f), 1.0f);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(18);
        auto header = area.removeFromTop(38);
        title_.setBounds(header.removeFromLeft(220));
        status_.setBounds(header.removeFromRight(590));
        subtitle_.setBounds(header);
        area.removeFromTop(7);

        auto midi_row = area.removeFromTop(31);
        midi_input_label_.setBounds(midi_row.removeFromLeft(76));
        midi_input_selector_.setBounds(midi_row.removeFromLeft(330));
        midi_row.removeFromLeft(8);
        refresh_midi_button_.setBounds(midi_row.removeFromLeft(112));
        area.removeFromTop(7);

        mode_state_.setBounds(area.removeFromTop(24));
        auto monitor_area = area.removeFromTop(112);
        auto display_area = monitor_area.removeFromLeft(430).reduced(3, 1);
        for (auto& line : display_lines_) {
            line.setBounds(display_area.removeFromTop(27));
        }
        monitor_area.removeFromLeft(8);
        oscilloscope_.setBounds(monitor_area);
        area.removeFromTop(5);

        constexpr int encoder_row_height = 139;
        for (std::size_t row = 0; row < 2; ++row) {
            auto row_area = area.removeFromTop(encoder_row_height);
            for (std::size_t column = 0; column < 8; ++column) {
                const auto index = row * 8U + column;
                const auto columns_left = static_cast<int>(8U - column);
                auto cell = row_area.removeFromLeft(row_area.getWidth() / columns_left).reduced(4);
                encoder_labels_[index]->setBounds(cell.removeFromTop(18));
                encoders_[index]->setBounds(cell);
            }
        }
        area.removeFromTop(6);
        auto button_row = area.removeFromTop(57);
        for (std::size_t column = 0; column < buttons_.size(); ++column) {
            const auto columns_left = static_cast<int>(buttons_.size() - column);
            auto cell = button_row.removeFromLeft(button_row.getWidth() / columns_left).reduced(6, 4);
            buttons_[column]->setBounds(cell);
        }
    }

private:
    static int preferenceRank(const juce::MidiDeviceInfo& device) {
        const auto name = device.name.toLowerCase();
        if (name.contains("launch control 3 midi")) return 3;
        if (name.contains("launch control 3") && !name.contains("daw")) return 2;
        if (name.contains("launch control 3")) return 1;
        return 0;
    }

    void refreshMidiInputs(bool select_preferred) {
        const auto previous_identifier = engine_.selectedMidiInputIdentifier();
        midi_inputs_ = engine_.availableMidiInputs();
        midi_input_selector_.clear(juce::dontSendNotification);
        midi_input_selector_.addItem("No MIDI input", 1);
        int selected_item = 0;
        int preferred_item = 0;
        int preferred_rank = 0;
        for (int index = 0; index < midi_inputs_.size(); ++index) {
            const auto& input = midi_inputs_.getReference(index);
            midi_input_selector_.addItem(input.name, index + 2);
            if (input.identifier == previous_identifier) selected_item = index + 1;
            const auto rank = preferenceRank(input);
            if (rank > preferred_rank) {
                preferred_rank = rank;
                preferred_item = index + 1;
            }
        }
        if (selected_item == 0 && select_preferred) selected_item = preferred_item;
        midi_input_selector_.setSelectedItemIndex(selected_item, juce::sendNotificationSync);
    }

    void applySelectedMidiInput() {
        const auto index = midi_input_selector_.getSelectedItemIndex() - 1;
        const auto result = index >= 0 && index < midi_inputs_.size()
            ? engine_.selectMidiInput(midi_inputs_.getReference(index))
            : engine_.disableMidiInput();
        status_.setText(result, juce::dontSendNotification);
    }

    void applySnapshot(const tidepit::Snapshot& snapshot) {
        const auto& descriptors = tidepit::encoderDescriptors();
        for (std::size_t index = 0; index < encoders_.size(); ++index) {
            if (descriptors[index].kind == tidepit::ControlKind::unassigned) continue;
            const auto accepted = valueForControl(descriptors[index].id, snapshot);
            if (std::abs(encoders_[index]->getValue() - accepted) > 0.0001) {
                encoders_[index]->setValue(accepted, juce::dontSendNotification);
            }
        }

        for (std::size_t index = 0; index < display_lines_.size(); ++index) {
            display_lines_[index].setText(
                juce::String::fromUTF8(snapshot.display_lines[index].data(), 21),
                juce::dontSendNotification
            );
        }
        mode_state_.setText(
            "STAGE " + juce::String(static_cast<int>(snapshot.stage) + 1)
                + "   SOURCE " + tidepit::sourceName(snapshot.source)
                + "   SCALE " + tidepit::scaleName(snapshot.scale)
                + "   TARGET " + tidepit::targetName(snapshot.target)
                + "   EFFECT " + tidepit::effectName(snapshot.effect)
                + "   LOCK " + (snapshot.locked ? "ON" : "OFF")
                + "   CAPTURE " + (snapshot.captured ? "ON" : "OFF"),
            juce::dontSendNotification
        );

        applyButtonStates(snapshot);
    }

    void applyButtonStates(const tidepit::Snapshot& snapshot) {
        const auto& descriptors_buttons = tidepit::buttonDescriptors();
        for (std::size_t index = 0; index < buttons_.size(); ++index) {
            const auto presentation = tidepit::buttonPresentation(
                descriptors_buttons[index].id,
                snapshot,
                mutate_feedback_ticks_ > 0
            );
            buttons_[index]->setButtonText(
                juce::String(presentation.label.data(), presentation.label.size())
                    + "  "
                    + juce::String(presentation.state.data(), presentation.state.size())
            );
            buttons_[index]->setToggleState(
                presentation.latched_active,
                juce::dontSendNotification
            );
        }
    }

    void timerCallback() override {
        UiFrame next;
        if (engine_.consumeLatestFrame(next)) {
            if (next.core_diagnostics.manual_mutations
                > ui_frame_.core_diagnostics.manual_mutations) {
                mutate_feedback_ticks_ = 6;
            }
            ui_frame_ = next;
            applySnapshot(ui_frame_.snapshot);
        }
        tidepit::ScopeFrame scope;
        if (engine_.consumeLatestScope(scope)) {
            oscilloscope_.setFrame(scope);
        }
        if (mutate_feedback_ticks_ > 0 && --mutate_feedback_ticks_ == 0) {
            applyButtonStates(ui_frame_.snapshot);
        }
        if (++status_timer_ticks_ >= 8) {
            status_timer_ticks_ = 0;
            status_.setText(engine_.statusText(ui_frame_), juce::dontSendNotification);
        }
    }

    InstrumentAudioEngine engine_;
    UiFrame ui_frame_{};
    juce::Label title_;
    juce::Label subtitle_;
    juce::Label status_;
    juce::Label midi_input_label_;
    juce::ComboBox midi_input_selector_;
    juce::TextButton refresh_midi_button_;
    juce::Array<juce::MidiDeviceInfo> midi_inputs_;
    juce::Label mode_state_;
    std::array<juce::Label, 4> display_lines_;
    OscilloscopeComponent oscilloscope_;
    std::array<std::unique_ptr<juce::Slider>, 16> encoders_;
    std::array<std::unique_ptr<juce::Label>, 16> encoder_labels_;
    std::array<std::unique_ptr<juce::TextButton>, 8> buttons_;
    std::array<bool, 8> button_edges_{};
    int mutate_feedback_ticks_{};
    int status_timer_ticks_{};
};

class MainWindow final : public juce::DocumentWindow {
public:
    MainWindow()
        : juce::DocumentWindow(
              "Tide Pit - Gills",
              juce::Colour(0xff111516),
              juce::DocumentWindow::closeButton
          ) {
        setUsingNativeTitleBar(true);
        setContentOwned(new MainComponent(), true);
        setResizable(false, false);
        centreWithSize(getWidth(), getHeight());
        setVisible(true);
    }

    void closeButtonPressed() override {
        if (auto* application = juce::JUCEApplication::getInstance(); application != nullptr) {
            application->systemRequestedQuit();
        }
    }
};

class TidePitApplication final : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "Tide Pit - Gills"; }
    const juce::String getApplicationVersion() override { return "0.1.0"; }
    bool moreThanOneInstanceAllowed() override { return true; }

    void initialise(const juce::String& command_line) override {
        static_cast<void>(command_line);
        window_ = std::make_unique<MainWindow>();
    }

    void shutdown() override { window_.reset(); }

    void anotherInstanceStarted(const juce::String& command_line) override {
        static_cast<void>(command_line);
    }

private:
    std::unique_ptr<MainWindow> window_;
};

}  // namespace

START_JUCE_APPLICATION(TidePitApplication)
