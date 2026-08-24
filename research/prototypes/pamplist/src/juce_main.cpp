#include "schuss/pamplist/control_map.hpp"
#include "schuss/pamplist/control_snapshot.hpp"
#include "schuss/pamplist/core.hpp"

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
#include <mutex>

namespace {

namespace pam = schuss::pamplist;

constexpr int kRequestedBlockFrames = 128;
constexpr float kQ27ToFloat = 1.0F / 134217728.0F;

const std::array<juce::Colour, pam::kLaneCount> kLaneColours{{
    juce::Colour{0xffff6b5f},
    juce::Colour{0xffff9f43},
    juce::Colour{0xffffcf56},
    juce::Colour{0xff69d28f},
    juce::Colour{0xff4fc3d7},
    juce::Colour{0xff5f8ff5},
    juce::Colour{0xffa779e9},
    juce::Colour{0xffef78b5},
}};

class AudioEngine final
    : public juce::AudioIODeviceCallback,
      public juce::MidiInputCallback {
public:
    AudioEngine()
        : pending_controls_(pam::defaultControls()),
          callback_controls_(pending_controls_) {
        controls_mailbox_.publish(pending_controls_);
        accepted_mailbox_.publish(core_.snapshot());
    }

    ~AudioEngine() override {
        closeMidiInput();
        stopAudio();
    }

    [[nodiscard]] bool audioActive() const noexcept {
        return audio_ready_.load(std::memory_order_acquire);
    }

    juce::String startAudio() {
        if (audioActive()) return "Audio is already active";
        auto error = device_manager_.initialiseWithDefaultDevices(0, 2);
        if (error.isNotEmpty()) return "Audio output unavailable: " + error;
        auto setup = device_manager_.getAudioDeviceSetup();
        setup.sampleRate = static_cast<double>(pam::kSampleRateHz);
        setup.bufferSize = kRequestedBlockFrames;
        error = device_manager_.setAudioDeviceSetup(setup, true);
        if (error.isNotEmpty()) {
            device_manager_.closeAudioDevice();
            return "48 kHz stereo setup unavailable: " + error;
        }
        auto* device = device_manager_.getCurrentAudioDevice();
        if (device == nullptr
            || device->getCurrentSampleRate() != static_cast<double>(pam::kSampleRateHz)
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples()
                > static_cast<int>(pam::kMaximumHostBlockFrames)) {
            device_manager_.closeAudioDevice();
            return "Pamplist requires 48 kHz stereo and blocks no larger than 512";
        }
        callback_block_frames_.store(
            static_cast<std::uint32_t>(device->getCurrentBufferSizeSamples()),
            std::memory_order_release);
        device_manager_.addAudioCallback(this);
        return "Audio requested; accepted controls apply at the next 16-frame quantum";
    }

    void stopAudio() {
        device_manager_.removeAudioCallback(this);
        device_manager_.closeAudioDevice();
        audio_ready_.store(false, std::memory_order_release);
    }

    [[nodiscard]] juce::Array<juce::MidiDeviceInfo> availableMidiInputs() const {
        return juce::MidiInput::getAvailableDevices();
    }

    [[nodiscard]] const juce::String& selectedMidiIdentifier() const noexcept {
        return selected_midi_identifier_;
    }

    juce::String selectMidiInput(const juce::MidiDeviceInfo& device) {
        closeMidiInput();
        if (device.identifier.isEmpty()) return "MIDI input disabled";
        device_manager_.setMidiInputDeviceEnabled(device.identifier, true);
        if (!device_manager_.isMidiInputDeviceEnabled(device.identifier)) {
            return "Could not open MIDI input: " + device.name;
        }
        device_manager_.addMidiInputDeviceCallback(device.identifier, this);
        selected_midi_identifier_ = device.identifier;
        selected_midi_name_ = device.name;
        received_midi_.store(0U, std::memory_order_release);
        mapped_midi_.store(0U, std::memory_order_release);
        return "Physical MIDI input active: " + device.name;
    }

    juce::String disableMidiInput() {
        closeMidiInput();
        return "MIDI input disabled";
    }

    void updateControls(const std::function<void(pam::Controls&)>& update) {
        const std::lock_guard<std::mutex> lock(control_mutex_);
        update(pending_controls_);
        pending_controls_ = pam::sanitizeControls(pending_controls_);
        controls_mailbox_.publish(pending_controls_);
        pending_revision_.fetch_add(1U, std::memory_order_release);
    }

    pam::MappingResult submitGuiCc(int cc, int value) {
        const std::lock_guard<std::mutex> lock(control_mutex_);
        auto result = controller_.handleCc(
            pending_controls_, pam::launchControlMidiChannel(), cc, value);
        if (result.dispatches()) {
            pending_controls_ = pam::sanitizeControls(pending_controls_);
            controls_mailbox_.publish(pending_controls_);
            pending_revision_.fetch_add(1U, std::memory_order_release);
        }
        gui_injections_.fetch_add(1U, std::memory_order_relaxed);
        last_input_kind_.store(1, std::memory_order_relaxed);
        last_channel_.store(pam::launchControlMidiChannel(), std::memory_order_relaxed);
        last_cc_.store(cc, std::memory_order_relaxed);
        last_value_.store(value, std::memory_order_relaxed);
        return result;
    }

    [[nodiscard]] pam::Snapshot acceptedSnapshot() const noexcept {
        return accepted_mailbox_.load(last_ui_snapshot_);
    }

    [[nodiscard]] juce::String statusText() const {
        const auto snapshot = acceptedSnapshot();
        juce::String text = audioActive() ? "AUDIO 48K ON" : "AUDIO OFF";
        text += "  |  BLOCK "
            + juce::String(callback_block_frames_.load(std::memory_order_acquire));
        text += "  |  FRAME " + juce::String(snapshot.absolute_frame);
        text += "  |  LANE "
            + juce::String(static_cast<int>(snapshot.accepted.selected_lane) + 1);
        text += "  |  ENGINE "
            + juce::String(static_cast<int>(snapshot.resolved_engine));
        text += "  |  TRIG "
            + juce::String(snapshot.diagnostics.trigger_count);
        if (selected_midi_identifier_.isEmpty()) {
            text += "  |  NO PHYSICAL MIDI";
        } else {
            text += "  |  MIDI " + selected_midi_name_ + " "
                + juce::String(mapped_midi_.load(std::memory_order_acquire))
                + "/" + juce::String(received_midi_.load(std::memory_order_acquire));
        }
        const auto last_kind = last_input_kind_.load(std::memory_order_acquire);
        if (last_kind != 0) {
            text += last_kind == 1 ? "  |  GUI INJECT" : "  |  PHYSICAL RX";
            text += " CH" + juce::String(last_channel_.load(std::memory_order_acquire))
                + " CC" + juce::String(last_cc_.load(std::memory_order_acquire))
                + "=" + juce::String(last_value_.load(std::memory_order_acquire));
        }
        if (stream_failures_.load(std::memory_order_acquire) != 0U) {
            text += "  |  STREAM ERR "
                + juce::String(stream_failures_.load(std::memory_order_acquire));
        }
        return text;
    }

    void handleIncomingMidiMessage(
        juce::MidiInput*,
        const juce::MidiMessage& message) override {
        received_midi_.fetch_add(1U, std::memory_order_relaxed);
        if (!message.isController()) return;
        const auto channel = message.getChannel();
        const auto cc = message.getControllerNumber();
        const auto value = message.getControllerValue();
        {
            const std::lock_guard<std::mutex> lock(control_mutex_);
            const auto result = controller_.handleCc(
                pending_controls_, channel, cc, value);
            if (result.dispatches()) {
                pending_controls_ = pam::sanitizeControls(pending_controls_);
                controls_mailbox_.publish(pending_controls_);
                pending_revision_.fetch_add(1U, std::memory_order_release);
            }
            if (result.accepted()) {
                mapped_midi_.fetch_add(1U, std::memory_order_relaxed);
            }
        }
        last_input_kind_.store(2, std::memory_order_relaxed);
        last_channel_.store(channel, std::memory_order_relaxed);
        last_cc_.store(cc, std::memory_order_relaxed);
        last_value_.store(value, std::memory_order_relaxed);
    }

    void audioDeviceAboutToStart(juce::AudioIODevice* device) override {
        audio_ready_.store(false, std::memory_order_release);
        core_.reset();
        callback_controls_ = controls_mailbox_.load(callback_controls_);
        if (device == nullptr
            || device->getCurrentSampleRate() != static_cast<double>(pam::kSampleRateHz)
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples()
                > static_cast<int>(pam::kMaximumHostBlockFrames)) {
            return;
        }
        callback_block_frames_.store(
            static_cast<std::uint32_t>(device->getCurrentBufferSizeSamples()),
            std::memory_order_release);
        audio_ready_.store(true, std::memory_order_release);
    }

    void audioDeviceStopped() override {
        audio_ready_.store(false, std::memory_order_release);
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
            || outputs == nullptr
            || output_channels < 2
            || outputs[0] == nullptr
            || outputs[1] == nullptr
            || frames < 1
            || frames > static_cast<int>(pam::kMaximumHostBlockFrames)) {
            return;
        }
        callback_controls_ = controls_mailbox_.load(callback_controls_);
        pam::ProcessReport report{};
        const auto ok = core_.process(
            callback_controls_,
            main_q27_.data(),
            auxiliary_q27_.data(),
            static_cast<std::size_t>(frames),
            &report);
        if (!ok) {
            stream_failures_.fetch_add(1U, std::memory_order_relaxed);
            return;
        }
        for (int frame = 0; frame < frames; ++frame) {
            outputs[0][frame] = static_cast<float>(main_q27_[frame]) * kQ27ToFloat;
            outputs[1][frame] = static_cast<float>(auxiliary_q27_[frame]) * kQ27ToFloat;
        }
        accepted_mailbox_.publish(report.snapshot);
        accepted_revision_.store(
            report.snapshot.accepted_sequence, std::memory_order_release);
    }

private:
    void closeMidiInput() {
        if (selected_midi_identifier_.isEmpty()) return;
        device_manager_.removeMidiInputDeviceCallback(selected_midi_identifier_, this);
        device_manager_.setMidiInputDeviceEnabled(selected_midi_identifier_, false);
        selected_midi_identifier_.clear();
        selected_midi_name_.clear();
    }

    static void clearOutputs(
        float* const* outputs,
        int channels,
        int frames) noexcept {
        if (outputs == nullptr || frames <= 0) return;
        for (int channel = 0; channel < channels; ++channel) {
            if (outputs[channel] != nullptr) {
                std::fill_n(outputs[channel], frames, 0.0F);
            }
        }
    }

    juce::AudioDeviceManager device_manager_;
    mutable std::mutex control_mutex_;
    pam::Controls pending_controls_{};
    pam::Controls callback_controls_{};
    pam::AtomicControlSnapshot controls_mailbox_{};
    mutable pam::AtomicAcceptedSnapshot accepted_mailbox_{};
    mutable pam::Snapshot last_ui_snapshot_{};
    pam::ControllerAdapter controller_{};
    pam::Core core_{};
    std::array<std::int32_t, pam::kMaximumHostBlockFrames> main_q27_{};
    std::array<std::int32_t, pam::kMaximumHostBlockFrames> auxiliary_q27_{};
    std::atomic<bool> audio_ready_{false};
    std::atomic<std::uint32_t> callback_block_frames_{0U};
    std::atomic<std::uint64_t> stream_failures_{0U};
    std::atomic<std::uint64_t> pending_revision_{0U};
    std::atomic<std::uint64_t> accepted_revision_{0U};
    juce::String selected_midi_identifier_;
    juce::String selected_midi_name_;
    std::atomic<std::uint64_t> received_midi_{0U};
    std::atomic<std::uint64_t> mapped_midi_{0U};
    std::atomic<std::uint64_t> gui_injections_{0U};
    std::atomic<int> last_input_kind_{0};
    std::atomic<int> last_channel_{0};
    std::atomic<int> last_cc_{-1};
    std::atomic<int> last_value_{-1};
};

class PamplistLookAndFeel final : public juce::LookAndFeel_V4 {
public:
    PamplistLookAndFeel() {
        setColour(juce::Slider::textBoxTextColourId, juce::Colour{0xffe8ecf1});
        setColour(juce::Slider::textBoxBackgroundColourId, juce::Colour{0xff151a20});
        setColour(juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
        setColour(juce::ComboBox::backgroundColourId, juce::Colour{0xff151a20});
        setColour(juce::ComboBox::textColourId, juce::Colour{0xffe8ecf1});
        setColour(juce::ComboBox::outlineColourId, juce::Colour{0xff39414c});
        setColour(juce::PopupMenu::backgroundColourId, juce::Colour{0xff151a20});
        setColour(juce::PopupMenu::textColourId, juce::Colour{0xffe8ecf1});
    }
};

class MainComponent final
    : public juce::Component,
      private juce::Timer {
public:
    MainComponent() {
        setLookAndFeel(&look_and_feel_);
        title_.setText("PAMPLIST", juce::dontSendNotification);
        title_.setFont(juce::FontOptions{27.0F, juce::Font::bold});
        title_.setColour(juce::Label::textColourId, juce::Colour{0xffffcf56});
        addAndMakeVisible(title_);
        subtitle_.setText(
            "eight clocked lanes / one 24-engine macro voice / main L + aux R",
            juce::dontSendNotification);
        subtitle_.setColour(juce::Label::textColourId, juce::Colour{0xff9ca7b5});
        addAndMakeVisible(subtitle_);

        audio_button_.setButtonText("Start audio");
        audio_button_.onClick = [this] {
            if (engine_.audioActive()) {
                engine_.stopAudio();
                status_.setText("Audio stopped", juce::dontSendNotification);
            } else {
                status_.setText(engine_.startAudio(), juce::dontSendNotification);
            }
            updateEnabledState();
        };
        addAndMakeVisible(audio_button_);

        refresh_midi_button_.setButtonText("Refresh MIDI");
        refresh_midi_button_.onClick = [this] { refreshMidiInputs(); };
        addAndMakeVisible(refresh_midi_button_);
        midi_selector_.addItem("No MIDI input", 1);
        midi_selector_.setSelectedItemIndex(0, juce::dontSendNotification);
        midi_selector_.onChange = [this] { applyMidiSelection(); };
        addAndMakeVisible(midi_selector_);

        running_button_.setButtonText("RUN");
        running_button_.setClickingTogglesState(true);
        running_button_.setToggleState(true, juce::dontSendNotification);
        running_button_.onClick = [this] {
            engine_.updateControls([this](pam::Controls& controls) {
                controls.running = running_button_.getToggleState();
            });
        };
        addAndMakeVisible(running_button_);

        configureGlobalSlider(0U, "BPM", 20.0, 300.0, 1.0, 120.0,
            [](pam::Controls& controls, double value) {
                controls.tempo_milli_bpm = static_cast<std::uint32_t>(
                    std::lround(value * 1000.0));
            });
        configureGlobalSlider(1U, "ENGINE", 0.0, 23.0, 1.0, 0.0,
            [](pam::Controls& controls, double value) {
                controls.engine = static_cast<std::uint8_t>(std::lround(value));
            });
        configureGlobalSlider(2U, "NOTE", 24.0, 96.0, 0.01, 48.0,
            [](pam::Controls& controls, double value) { controls.note = static_cast<float>(value); });
        configureGlobalSlider(3U, "HARM", 0.0, 1.0, 0.001, 0.5,
            [](pam::Controls& controls, double value) { controls.harmonics = static_cast<float>(value); });
        configureGlobalSlider(4U, "TIMBRE", 0.0, 1.0, 0.001, 0.5,
            [](pam::Controls& controls, double value) { controls.timbre = static_cast<float>(value); });
        configureGlobalSlider(5U, "MORPH", 0.0, 1.0, 0.001, 0.5,
            [](pam::Controls& controls, double value) { controls.morph = static_cast<float>(value); });
        configureGlobalSlider(6U, "DECAY", 0.0, 1.0, 0.001, 0.5,
            [](pam::Controls& controls, double value) { controls.decay = static_cast<float>(value); });
        configureGlobalSlider(7U, "LEVEL", 0.0, 1.0, 0.001, 0.8,
            [](pam::Controls& controls, double value) { controls.source_level = static_cast<float>(value); });
        configureGlobalSlider(8U, "MASTER", 0.0, 1.0, 0.001, 0.65,
            [](pam::Controls& controls, double value) { controls.master_gain = static_cast<float>(value); });

        for (std::size_t lane = 0; lane < lane_buttons_.size(); ++lane) {
            auto button = std::make_unique<juce::TextButton>(
                "LANE " + juce::String(static_cast<int>(lane + 1U)));
            button->setColour(juce::TextButton::buttonOnColourId, kLaneColours[lane]);
            button->setColour(juce::TextButton::buttonColourId, juce::Colour{0xff252c35});
            button->onClick = [this, lane] {
                static_cast<void>(engine_.submitGuiCc(
                    40 + static_cast<int>(lane), 127));
                static_cast<void>(engine_.submitGuiCc(
                    40 + static_cast<int>(lane), 0));
            };
            addAndMakeVisible(*button);
            lane_buttons_[lane] = std::move(button);
        }

        const std::array<const char*, 16> names{{
            "TRIGGER", "PITCH", "MODEL", "HARMONICS",
            "TIMBRE", "MORPH", "DECAY", "LEVEL",
            "RATE", "PHASE", "SHAPE", "HITS",
            "ROTATE", "PROB", "REPEAT", "AMP",
        }};
        for (std::size_t index = 0; index < lane_sliders_.size(); ++index) {
            auto slider = std::make_unique<juce::Slider>();
            slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, 48, 18);
            slider->setRange(0.0, 127.0, 1.0);
            slider->setValue(index == 0U ? 127.0 : (index < 8U ? 64.0 : 0.0),
                juce::dontSendNotification);
            slider->setColour(
                juce::Slider::rotarySliderFillColourId, juce::Colour{0xffffcf56});
            slider->onValueChange = [this, index] {
                static_cast<void>(engine_.submitGuiCc(
                    20 + static_cast<int>(index),
                    juce::roundToInt(lane_sliders_[index]->getValue())));
            };
            addAndMakeVisible(*slider);
            lane_sliders_[index] = std::move(slider);

            auto label = std::make_unique<juce::Label>();
            label->setText(names[index], juce::dontSendNotification);
            label->setJustificationType(juce::Justification::centred);
            label->setFont(juce::FontOptions{11.0F, juce::Font::bold});
            label->setColour(juce::Label::textColourId, juce::Colour{0xffc7ced7});
            addAndMakeVisible(*label);
            lane_labels_[index] = std::move(label);
        }

        status_.setText(
            "Build-only prototype: press Start audio explicitly; refresh/select MIDI explicitly",
            juce::dontSendNotification);
        status_.setColour(juce::Label::textColourId, juce::Colour{0xff91a0b3});
        status_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(status_);

        updateEnabledState();
        startTimerHz(20);
        setSize(1280, 730);
    }

    ~MainComponent() override { setLookAndFeel(nullptr); }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff101419});
        graphics.setColour(juce::Colour{0xff2b333d});
        graphics.drawRoundedRectangle(
            getLocalBounds().toFloat().reduced(8.5F), 6.0F, 1.0F);
        graphics.setColour(juce::Colour{0xff202730});
        graphics.fillRoundedRectangle(
            juce::Rectangle<float>{18.0F, 178.0F,
                static_cast<float>(getWidth() - 36), 482.0F}, 6.0F);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(18);
        auto header = area.removeFromTop(42);
        title_.setBounds(header.removeFromLeft(180));
        status_.setBounds(header.removeFromRight(720));
        subtitle_.setBounds(header);
        area.removeFromTop(6);

        auto lifecycle = area.removeFromTop(34);
        audio_button_.setBounds(lifecycle.removeFromLeft(112));
        lifecycle.removeFromLeft(8);
        refresh_midi_button_.setBounds(lifecycle.removeFromLeft(112));
        lifecycle.removeFromLeft(8);
        midi_selector_.setBounds(lifecycle.removeFromLeft(340));
        lifecycle.removeFromLeft(14);
        running_button_.setBounds(lifecycle.removeFromLeft(72));
        area.removeFromTop(8);

        auto globals = area.removeFromTop(98);
        for (std::size_t index = 0; index < global_sliders_.size(); ++index) {
            const auto remaining = static_cast<int>(global_sliders_.size() - index);
            auto cell = globals.removeFromLeft(globals.getWidth() / remaining).reduced(3);
            global_labels_[index]->setBounds(cell.removeFromTop(18));
            global_sliders_[index]->setBounds(cell);
        }
        area.removeFromTop(8);

        auto lanes = area.removeFromTop(42);
        for (std::size_t lane = 0; lane < lane_buttons_.size(); ++lane) {
            const auto remaining = static_cast<int>(lane_buttons_.size() - lane);
            lane_buttons_[lane]->setBounds(
                lanes.removeFromLeft(lanes.getWidth() / remaining).reduced(4));
        }
        area.removeFromTop(8);

        for (std::size_t row = 0; row < 2U; ++row) {
            auto row_area = area.removeFromTop(176);
            for (std::size_t column = 0; column < 8U; ++column) {
                const auto index = row * 8U + column;
                const auto remaining = static_cast<int>(8U - column);
                auto cell = row_area.removeFromLeft(
                    row_area.getWidth() / remaining).reduced(5);
                lane_labels_[index]->setBounds(cell.removeFromTop(20));
                lane_sliders_[index]->setBounds(cell);
            }
        }
    }

private:
    using GlobalSetter = std::function<void(pam::Controls&, double)>;

    void configureGlobalSlider(
        std::size_t index,
        const char* label_text,
        double minimum,
        double maximum,
        double interval,
        double value,
        GlobalSetter setter) {
        auto slider = std::make_unique<juce::Slider>();
        slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, 58, 18);
        slider->setRange(minimum, maximum, interval);
        slider->setValue(value, juce::dontSendNotification);
        slider->setColour(
            juce::Slider::rotarySliderFillColourId, juce::Colour{0xff4fc3d7});
        slider->onValueChange = [this, index, setter = std::move(setter)] {
            const auto value_now = global_sliders_[index]->getValue();
            engine_.updateControls([&setter, value_now](pam::Controls& controls) {
                setter(controls, value_now);
            });
        };
        addAndMakeVisible(*slider);
        global_sliders_[index] = std::move(slider);
        auto label = std::make_unique<juce::Label>();
        label->setText(label_text, juce::dontSendNotification);
        label->setJustificationType(juce::Justification::centred);
        label->setFont(juce::FontOptions{11.0F, juce::Font::bold});
        label->setColour(juce::Label::textColourId, juce::Colour{0xffc7ced7});
        addAndMakeVisible(*label);
        global_labels_[index] = std::move(label);
    }

    static int routePresentation(float value) {
        return juce::jlimit(0, 127, juce::roundToInt(
            value <= 0.0F ? 64.0F + value * 64.0F : 64.0F + value * 63.0F));
    }

    static int binPresentation(int value, int bins) {
        return juce::jlimit(0, 127, (value * 128 + 64) / bins);
    }

    static int repeatPresentation(std::uint8_t repeat) {
        if (repeat == 0U) return 0;
        for (int value = 1; value <= 127; ++value) {
            const auto mapped = static_cast<int>(1 + ((value - 1) * 64) / 127);
            if (mapped >= repeat) return value;
        }
        return 127;
    }

    void projectAcceptedState(const pam::Snapshot& snapshot) {
        const auto selected = std::min<std::size_t>(
            snapshot.accepted.selected_lane, pam::kLaneCount - 1U);
        for (std::size_t lane = 0; lane < lane_buttons_.size(); ++lane) {
            lane_buttons_[lane]->setToggleState(lane == selected, juce::dontSendNotification);
        }
        const auto& controls = snapshot.accepted.lanes[selected];
        for (std::size_t destination = 0;
             destination < pam::kDestinationCount;
             ++destination) {
            lane_sliders_[destination]->setValue(
                routePresentation(controls.routes[destination]),
                juce::dontSendNotification);
            lane_sliders_[destination]->setColour(
                juce::Slider::rotarySliderFillColourId, kLaneColours[selected]);
        }
        const std::array<int, 8> values{{
            binPresentation(controls.rate_index, 16),
            controls.phase_u7,
            binPresentation(static_cast<int>(controls.shape), 8),
            juce::roundToInt(static_cast<float>(controls.hits) * 127.0F / 16.0F),
            binPresentation(controls.rotation, 16),
            juce::roundToInt(controls.probability * 127.0F),
            repeatPresentation(controls.repeat),
            juce::roundToInt(controls.amplitude * 127.0F),
        }};
        for (std::size_t index = 0; index < values.size(); ++index) {
            lane_sliders_[8U + index]->setValue(values[index], juce::dontSendNotification);
            lane_sliders_[8U + index]->setColour(
                juce::Slider::rotarySliderFillColourId, kLaneColours[selected]);
        }
    }

    void refreshMidiInputs() {
        const auto prior = engine_.selectedMidiIdentifier();
        midi_inputs_ = engine_.availableMidiInputs();
        midi_selector_.clear(juce::dontSendNotification);
        midi_selector_.addItem("No MIDI input", 1);
        int selected = 0;
        for (int index = 0; index < midi_inputs_.size(); ++index) {
            const auto& input = midi_inputs_.getReference(index);
            midi_selector_.addItem(input.name, index + 2);
            if (input.identifier == prior) selected = index + 1;
        }
        midi_selector_.setSelectedItemIndex(selected, juce::dontSendNotification);
        status_.setText(
            "MIDI list refreshed; select an endpoint explicitly",
            juce::dontSendNotification);
    }

    void applyMidiSelection() {
        const auto index = midi_selector_.getSelectedItemIndex() - 1;
        const auto result = index >= 0 && index < midi_inputs_.size()
            ? engine_.selectMidiInput(midi_inputs_.getReference(index))
            : engine_.disableMidiInput();
        status_.setText(result, juce::dontSendNotification);
    }

    void updateEnabledState() {
        const auto active = engine_.audioActive();
        audio_button_.setButtonText(active ? "Stop audio" : "Start audio");
        running_button_.setEnabled(active);
        for (auto& slider : global_sliders_) slider->setEnabled(active);
        for (auto& button : lane_buttons_) button->setEnabled(active);
        for (auto& slider : lane_sliders_) slider->setEnabled(active);
    }

    void timerCallback() override {
        if (engine_.audioActive()) {
            projectAcceptedState(engine_.acceptedSnapshot());
        }
        if (++status_ticks_ >= 5) {
            status_ticks_ = 0;
            status_.setText(engine_.statusText(), juce::dontSendNotification);
            updateEnabledState();
        }
    }

    PamplistLookAndFeel look_and_feel_{};
    AudioEngine engine_{};
    juce::Label title_;
    juce::Label subtitle_;
    juce::Label status_;
    juce::TextButton audio_button_;
    juce::TextButton refresh_midi_button_;
    juce::ComboBox midi_selector_;
    juce::ToggleButton running_button_;
    juce::Array<juce::MidiDeviceInfo> midi_inputs_;
    std::array<std::unique_ptr<juce::Slider>, 9> global_sliders_;
    std::array<std::unique_ptr<juce::Label>, 9> global_labels_;
    std::array<std::unique_ptr<juce::TextButton>, pam::kLaneCount> lane_buttons_;
    std::array<std::unique_ptr<juce::Slider>, 16> lane_sliders_;
    std::array<std::unique_ptr<juce::Label>, 16> lane_labels_;
    int status_ticks_{};
};

class MainWindow final : public juce::DocumentWindow {
public:
    MainWindow()
        : juce::DocumentWindow(
              "Pamplist",
              juce::Colour{0xff101419},
              juce::DocumentWindow::closeButton) {
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

class PamplistApplication final : public juce::JUCEApplication {
public:
    [[nodiscard]] const juce::String getApplicationName() override {
        return "Pamplist";
    }

    [[nodiscard]] const juce::String getApplicationVersion() override {
        return "0.2.0";
    }

    void initialise(const juce::String&) override {
        main_window_ = std::make_unique<MainWindow>();
    }

    void shutdown() override { main_window_.reset(); }

private:
    std::unique_ptr<MainWindow> main_window_;
};

}  // namespace

START_JUCE_APPLICATION(PamplistApplication)
