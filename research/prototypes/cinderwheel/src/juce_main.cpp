#include "cinderwheel/juce_midi_adapter.hpp"

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

namespace {

constexpr int kRequestedBlockFrames = 128;
constexpr std::size_t kMaximumWakeEventsPerBlock = 16;

class InstrumentAudioEngine final
    : public juce::AudioIODeviceCallback,
      public juce::MidiInputCallback {
public:
    InstrumentAudioEngine() {
        collector_.ensureStorageAllocated(4096);
        midi_block_.ensureSize(4096);
        clearPhysicalEncoderValues();
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
        setup.sampleRate = cinderwheel::kReferenceSampleRate;
        setup.bufferSize = kRequestedBlockFrames;
        error = device_manager_.setAudioDeviceSetup(setup, true);
        if (error.isNotEmpty()) {
            device_manager_.closeAudioDevice();
            return "48 kHz stereo setup unavailable: " + error;
        }

        auto* device = device_manager_.getCurrentAudioDevice();
        if (device == nullptr
            || device->getCurrentSampleRate() != cinderwheel::kReferenceSampleRate
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples()
                > static_cast<int>(cinderwheel::kMaximumBlockFrames)) {
            device_manager_.closeAudioDevice();
            return "Cinderwheel requires 48 kHz stereo output and blocks no larger than 512";
        }

        device_manager_.addAudioCallback(this);
        return ready_.load(std::memory_order_acquire)
            ? "48 kHz output active; select a MIDI input"
            : "Audio callback did not accept the device configuration";
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
        last_midi_channel_.store(0, std::memory_order_release);
        last_midi_cc_.store(-1, std::memory_order_release);
        last_midi_value_.store(-1, std::memory_order_release);
        clearPhysicalEncoderValues();
        return "MIDI input active: " + device.name;
    }

    juce::String disableMidiInput() {
        closeMidiInput();
        return "MIDI input disabled";
    }

    [[nodiscard]] juce::String statusText() const {
        if (!ready_.load(std::memory_order_acquire)) return "Audio output unavailable";
        if (selected_midi_input_identifier_.isEmpty()) {
            return "48 kHz output active | no MIDI input selected";
        }
        if (!device_manager_.isMidiInputDeviceEnabled(selected_midi_input_identifier_)) {
            return "MIDI input disconnected: " + selected_midi_input_name_;
        }

        juce::String status = "MIDI: " + selected_midi_input_name_
            + " | received "
            + juce::String(received_midi_messages_.load(std::memory_order_acquire));
        const auto controller = last_midi_cc_.load(std::memory_order_acquire);
        if (controller >= 0) {
            status += " | last ch "
                + juce::String(last_midi_channel_.load(std::memory_order_acquire))
                + " CC" + juce::String(controller)
                + "=" + juce::String(last_midi_value_.load(std::memory_order_acquire));
        }
        return status;
    }

    [[nodiscard]] int physicalEncoderValue(std::size_t index) const noexcept {
        if (index >= physical_encoder_values_.size()) return -1;
        return physical_encoder_values_[index].load(std::memory_order_acquire);
    }

    void injectCc(std::uint8_t controller, std::uint8_t value) {
        if (!ready_.load(std::memory_order_acquire)) return;
        auto message = juce::MidiMessage::controllerEvent(16, controller, value);
        message.setTimeStamp(juce::Time::getMillisecondCounterHiRes() * 0.001);
        collector_.addMessageToQueue(message);
    }

    void handleIncomingMidiMessage(
        juce::MidiInput*,
        const juce::MidiMessage& message
    ) override {
        received_midi_messages_.fetch_add(1, std::memory_order_relaxed);
        if (message.isController()) {
            last_midi_channel_.store(message.getChannel(), std::memory_order_relaxed);
            last_midi_cc_.store(message.getControllerNumber(), std::memory_order_relaxed);
            last_midi_value_.store(message.getControllerValue(), std::memory_order_relaxed);
            if (message.getChannel() == 16) {
                for (std::size_t index = 0;
                     index < cinderwheel::kLaunchControl3Encoders.size();
                     ++index) {
                    if (message.getControllerNumber()
                        == cinderwheel::kLaunchControl3Encoders[index].cc) {
                        physical_encoder_values_[index].store(
                            message.getControllerValue(),
                            std::memory_order_release
                        );
                        break;
                    }
                }
            }
        }
        collector_.handleIncomingMidiMessage(nullptr, message);
    }

    void audioDeviceAboutToStart(juce::AudioIODevice* device) override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
        midi_adapter_.reset();
        midi_block_.clear();
        if (device == nullptr
            || device->getCurrentSampleRate() != cinderwheel::kReferenceSampleRate
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples()
                > static_cast<int>(cinderwheel::kMaximumBlockFrames)) {
            return;
        }
        collector_.reset(cinderwheel::kReferenceSampleRate);
        auto core = std::make_unique<cinderwheel::Core>();
        if (!core->prepare(
                cinderwheel::kReferenceSampleRate,
                cinderwheel::kMaximumBlockFrames)) {
            return;
        }
        core_ = std::move(core);
        ready_.store(true, std::memory_order_release);
    }

    void audioDeviceStopped() override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
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
            || frames < 1
            || frames > static_cast<int>(cinderwheel::kMaximumBlockFrames)) {
            return;
        }

        midi_block_.clear();
        collector_.removeNextBlockOfMessages(midi_block_, frames);
        const auto adapted = midi_adapter_.adapt(
            midi_block_,
            static_cast<std::uint32_t>(frames),
            *core_
        );

        std::array<cinderwheel::WakeEvent, kMaximumWakeEventsPerBlock> wake_events{};
        const auto report = core_->process(
            left_.data(),
            right_.data(),
            static_cast<std::uint32_t>(frames),
            adapted.events,
            adapted.event_count,
            wake_events.data(),
            wake_events.size()
        );
        static_cast<void>(report);
        std::copy_n(left_.data(), frames, output_channels[0]);
        std::copy_n(right_.data(), frames, output_channels[1]);
    }

private:
    void clearPhysicalEncoderValues() noexcept {
        for (auto& value : physical_encoder_values_) {
            value.store(-1, std::memory_order_relaxed);
        }
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
            if (outputs[channel] != nullptr) std::fill_n(outputs[channel], frames, 0.0f);
        }
    }

    juce::AudioDeviceManager device_manager_;
    juce::MidiMessageCollector collector_;
    juce::MidiBuffer midi_block_;
    cinderwheel::JuceMidiAdapter midi_adapter_;
    std::unique_ptr<cinderwheel::Core> core_;
    std::array<float, cinderwheel::kMaximumBlockFrames> left_{};
    std::array<float, cinderwheel::kMaximumBlockFrames> right_{};
    std::atomic<bool> ready_{false};
    juce::String selected_midi_input_identifier_;
    juce::String selected_midi_input_name_;
    std::atomic<std::uint64_t> received_midi_messages_{0};
    std::atomic<int> last_midi_channel_{0};
    std::atomic<int> last_midi_cc_{-1};
    std::atomic<int> last_midi_value_{-1};
    std::array<
        std::atomic<int>,
        cinderwheel::kLaunchControl3Encoders.size()
    > physical_encoder_values_;
};

class MainComponent final
    : public juce::Component,
      private juce::Timer {
public:
    MainComponent() {
        title_.setText("CINDERWHEEL", juce::dontSendNotification);
        title_.setFont(juce::FontOptions(24.0f, juce::Font::bold));
        title_.setColour(juce::Label::textColourId, juce::Colour(0xffff7043));
        addAndMakeVisible(title_);

        subtitle_.setText(
            "regular Launch Control 3 layout | MIDI ch 16 | CC20-35 / CC40-47",
            juce::dontSendNotification
        );
        subtitle_.setColour(juce::Label::textColourId, juce::Colour(0xffaeb4bd));
        addAndMakeVisible(subtitle_);

        midi_input_label_.setText("MIDI input", juce::dontSendNotification);
        midi_input_label_.setColour(juce::Label::textColourId, juce::Colour(0xffd6dbe2));
        addAndMakeVisible(midi_input_label_);

        midi_input_selector_.onChange = [this] { applySelectedMidiInput(); };
        addAndMakeVisible(midi_input_selector_);

        refresh_midi_button_.setButtonText("Refresh MIDI");
        refresh_midi_button_.onClick = [this] { refreshMidiInputs(false); };
        addAndMakeVisible(refresh_midi_button_);

        for (std::size_t index = 0; index < encoders_.size(); ++index) {
            const auto& descriptor = cinderwheel::kLaunchControl3Encoders[index];
            auto slider = std::make_unique<juce::Slider>();
            slider->setName(juce::String(descriptor.oled_label.data(), descriptor.oled_label.size()));
            slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, 48, 18);
            slider->setRange(0.0, 127.0, 1.0);
            slider->setValue(
                static_cast<double>(juce::roundToInt(descriptor.default_normalized * 127.0)),
                juce::dontSendNotification
            );
            slider->setDoubleClickReturnValue(
                true,
                static_cast<double>(juce::roundToInt(descriptor.default_normalized * 127.0))
            );
            slider->setColour(juce::Slider::rotarySliderFillColourId, juce::Colour(0xffff7043));
            slider->setColour(juce::Slider::rotarySliderOutlineColourId, juce::Colour(0xff343a43));
            slider->setColour(juce::Slider::textBoxTextColourId, juce::Colour(0xffe8edf3));
            slider->setColour(juce::Slider::textBoxBackgroundColourId, juce::Colour(0xff171a1f));
            slider->onValueChange = [this, index] {
                engine_.injectCc(
                    cinderwheel::kLaunchControl3Encoders[index].cc,
                    static_cast<std::uint8_t>(juce::roundToInt(encoders_[index]->getValue()))
                );
            };
            addAndMakeVisible(*slider);
            encoders_[index] = std::move(slider);

            auto label = std::make_unique<juce::Label>();
            label->setText(
                juce::String(descriptor.oled_label.data(), descriptor.oled_label.size()),
                juce::dontSendNotification
            );
            label->setJustificationType(juce::Justification::centred);
            label->setColour(juce::Label::textColourId, juce::Colour(0xffd6dbe2));
            label->setFont(juce::FontOptions(12.0f, juce::Font::bold));
            addAndMakeVisible(*label);
            encoder_labels_[index] = std::move(label);
        }

        for (std::size_t index = 0; index < buttons_.size(); ++index) {
            const auto& descriptor = cinderwheel::kLaunchControl3Buttons[index];
            auto button = std::make_unique<juce::TextButton>(
                juce::String(descriptor.oled_label.data(), descriptor.oled_label.size())
            );
            button->setColour(juce::TextButton::buttonColourId, juce::Colour(0xff2b3038));
            button->setColour(juce::TextButton::buttonOnColourId, juce::Colour(0xffff7043));
            button->setColour(juce::TextButton::textColourOffId, juce::Colour(0xffe8edf3));
            button->setColour(juce::TextButton::textColourOnId, juce::Colour(0xff111318));
            button->onStateChange = [this, index] {
                const bool down = buttons_[index]->isDown();
                if (down == button_edges_[index]) return;
                button_edges_[index] = down;
                engine_.injectCc(
                    cinderwheel::kLaunchControl3Buttons[index].cc,
                    static_cast<std::uint8_t>(down ? 127 : 0)
                );
            };
            addAndMakeVisible(*button);
            buttons_[index] = std::move(button);
        }

        status_.setText(engine_.start(), juce::dontSendNotification);
        status_.setColour(juce::Label::textColourId, juce::Colour(0xff8fa3b8));
        status_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(status_);

        refreshMidiInputs(true);
        startTimerHz(30);
        setSize(1120, 540);
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour(0xff111318));
        graphics.setColour(juce::Colour(0xff242931));
        graphics.drawLine(16.0f, 56.0f, static_cast<float>(getWidth() - 16), 56.0f, 1.0f);
        graphics.drawRoundedRectangle(
            getLocalBounds().toFloat().reduced(8.5f),
            4.0f,
            1.0f
        );
    }

    void resized() override {
        auto area = getLocalBounds().reduced(18);
        auto header = area.removeFromTop(42);
        title_.setBounds(header.removeFromLeft(190));
        status_.setBounds(header.removeFromRight(520));
        subtitle_.setBounds(header);
        area.removeFromTop(6);

        auto midi_row = area.removeFromTop(32);
        midi_input_label_.setBounds(midi_row.removeFromLeft(76));
        midi_input_selector_.setBounds(midi_row.removeFromLeft(330));
        midi_row.removeFromLeft(8);
        refresh_midi_button_.setBounds(midi_row.removeFromLeft(112));
        area.removeFromTop(8);

        const int encoder_row_height = 154;
        for (std::size_t row = 0; row < 2; ++row) {
            auto row_area = area.removeFromTop(encoder_row_height);
            for (std::size_t column = 0; column < 8; ++column) {
                const std::size_t index = row * 8U + column;
                const int columns_left = static_cast<int>(8U - column);
                auto cell = row_area.removeFromLeft(row_area.getWidth() / columns_left).reduced(5);
                encoder_labels_[index]->setBounds(cell.removeFromTop(20));
                encoders_[index]->setBounds(cell);
            }
        }

        area.removeFromTop(8);
        auto button_row = area.removeFromTop(66);
        for (std::size_t column = 0; column < buttons_.size(); ++column) {
            const int columns_left = static_cast<int>(buttons_.size() - column);
            auto cell = button_row.removeFromLeft(button_row.getWidth() / columns_left).reduced(7, 5);
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
        midi_input_selector_.setSelectedItemIndex(
            selected_item,
            juce::sendNotificationSync
        );
        status_.setText(engine_.statusText(), juce::dontSendNotification);
    }

    void applySelectedMidiInput() {
        const auto index = midi_input_selector_.getSelectedItemIndex() - 1;
        const auto result = index >= 0 && index < midi_inputs_.size()
            ? engine_.selectMidiInput(midi_inputs_.getReference(index))
            : engine_.disableMidiInput();
        status_.setText(result, juce::dontSendNotification);
    }

    void timerCallback() override {
        for (std::size_t index = 0; index < encoders_.size(); ++index) {
            const auto value = engine_.physicalEncoderValue(index);
            if (value >= 0
                && encoders_[index] != nullptr
                && juce::roundToInt(encoders_[index]->getValue()) != value) {
                encoders_[index]->setValue(
                    static_cast<double>(value),
                    juce::dontSendNotification
                );
            }
        }

        if (++status_timer_ticks_ >= 8) {
            status_timer_ticks_ = 0;
            status_.setText(engine_.statusText(), juce::dontSendNotification);
        }
    }

    InstrumentAudioEngine engine_;
    juce::Label title_;
    juce::Label subtitle_;
    juce::Label status_;
    juce::Label midi_input_label_;
    juce::ComboBox midi_input_selector_;
    juce::TextButton refresh_midi_button_;
    juce::Array<juce::MidiDeviceInfo> midi_inputs_;
    std::array<std::unique_ptr<juce::Slider>, 16> encoders_;
    std::array<std::unique_ptr<juce::Label>, 16> encoder_labels_;
    std::array<std::unique_ptr<juce::TextButton>, 8> buttons_;
    std::array<bool, 8> button_edges_{};
    int status_timer_ticks_{};
};

class MainWindow final : public juce::DocumentWindow {
public:
    MainWindow()
        : juce::DocumentWindow(
              "Cinderwheel",
              juce::Colour(0xff111318),
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

class CinderwheelApplication final : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "Cinderwheel"; }
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

START_JUCE_APPLICATION(CinderwheelApplication)
