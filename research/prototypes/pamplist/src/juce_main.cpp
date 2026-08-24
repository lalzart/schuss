#include "schuss/pamplist/control_map.hpp"
#include "schuss/pamplist/control_snapshot.hpp"
#include "schuss/pamplist/core.hpp"
#include "schuss/pamplist/ui_model.hpp"

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
}};
constexpr juce::uint32 kGlobalColourArgb = 0xffef78b5;

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
        const auto selected_page = std::min<std::size_t>(
            snapshot.accepted.selected_page, pam::kGlobalPageIndex);
        if (selected_page < pam::kLaneCount) {
            text += "  |  LANE "
                + juce::String(static_cast<int>(selected_page) + 1);
            text += snapshot.accepted.lane_control_mode
                    == pam::LaneControlMode::voice
                ? "  |  VOICE"
                : "  |  MOTION";
            const auto base_model = snapshot.accepted.voices[selected_page].engine;
            const auto resolved_model = snapshot.resolved_engines[selected_page];
            text += "  |  MODEL " + juce::String(static_cast<int>(base_model))
                + " " + juce::String(pam::modelName(base_model));
            text += "  |  NOW " + juce::String(static_cast<int>(resolved_model))
                + " " + juce::String(pam::modelName(resolved_model));
        } else {
            text += "  |  GLOBAL"
                "  |  COHERE "
                + juce::String(snapshot.accepted.cohesion.cohere, 2)
                + "  |  FX CLEAR "
                + juce::String(snapshot.diagnostics.effect_clear_count);
        }
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

class SurfaceSlider final : public juce::Slider {
public:
    void setBinaryPresentation(bool binary) noexcept {
        binary_presentation_ = binary;
    }

    [[nodiscard]] bool userGestureActive() const noexcept {
        return binary_mouse_down_ || isMouseButtonDown(true);
    }

    void mouseDown(const juce::MouseEvent& event) override {
        if (!binary_presentation_) {
            juce::Slider::mouseDown(event);
            return;
        }
        if (!isEnabled() || event.mods.isPopupMenu()) return;
        binary_mouse_down_ = true;
        setValue(
            getValue() >= 0.5 ? 0.0 : 1.0,
            juce::sendNotificationSync);
    }

    void mouseDrag(const juce::MouseEvent& event) override {
        if (!binary_presentation_) juce::Slider::mouseDrag(event);
    }

    void mouseUp(const juce::MouseEvent& event) override {
        if (!binary_presentation_) {
            juce::Slider::mouseUp(event);
            return;
        }
        binary_mouse_down_ = false;
    }

private:
    bool binary_presentation_{};
    bool binary_mouse_down_{};
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
            "seven independent 24-model voices / page eight is one shared, clearable resonant body",
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

        for (std::size_t column = 0; column < pam::kSurfaceColumnCount; ++column) {
            configureSurfaceSlot(pam::SurfaceRow::top, column);
            configureSurfaceSlot(pam::SurfaceRow::bottom, column);
        }

        top_group_.setText("VOICE SHAPE - direct lane sound");
        top_group_.setColour(
            juce::GroupComponent::outlineColourId, juce::Colour{0xff46515e});
        top_group_.setColour(
            juce::GroupComponent::textColourId, juce::Colour{0xffd5dce5});
        addAndMakeVisible(top_group_);
        top_group_.toBack();
        bottom_group_.setText("SEQUENCER - timing, pattern, and motion shape");
        bottom_group_.setColour(
            juce::GroupComponent::outlineColourId, juce::Colour{0xff46515e});
        bottom_group_.setColour(
            juce::GroupComponent::textColourId, juce::Colour{0xffd5dce5});
        addAndMakeVisible(bottom_group_);
        bottom_group_.toBack();

        voice_mode_button_.setButtonText("VOICE");
        voice_mode_button_.setColour(
            juce::TextButton::buttonColourId, juce::Colour{0xff252c35});
        voice_mode_button_.setColour(
            juce::TextButton::buttonOnColourId, juce::Colour{0xff4fc3d7});
        voice_mode_button_.onClick = [this] {
            engine_.updateControls([](pam::Controls& controls) {
                if (controls.selected_page < pam::kLaneCount) {
                    controls.lane_control_mode = pam::LaneControlMode::voice;
                }
            });
        };
        addAndMakeVisible(voice_mode_button_);
        motion_mode_button_.setButtonText("MOTION");
        motion_mode_button_.setColour(
            juce::TextButton::buttonColourId, juce::Colour{0xff252c35});
        motion_mode_button_.setColour(
            juce::TextButton::buttonOnColourId, juce::Colour{0xffff9f43});
        motion_mode_button_.onClick = [this] {
            engine_.updateControls([](pam::Controls& controls) {
                if (controls.selected_page < pam::kLaneCount) {
                    controls.lane_control_mode = pam::LaneControlMode::motion;
                }
            });
        };
        addAndMakeVisible(motion_mode_button_);

        surface_guide_.setColour(
            juce::Label::textColourId, juce::Colour{0xff9ca7b5});
        surface_guide_.setJustificationType(juce::Justification::centredLeft);
        surface_guide_.setFont(juce::FontOptions{12.0F});
        addAndMakeVisible(surface_guide_);

        engine_banner_.setText(
            "LANE 1  /  MODEL 00 VIRTUAL ANALOG VCF  /  NOW 00 VIRTUAL ANALOG VCF",
            juce::dontSendNotification);
        engine_banner_.setFont(juce::FontOptions{13.0F, juce::Font::bold});
        engine_banner_.setColour(
            juce::Label::textColourId, juce::Colour{0xffffcf56});
        engine_banner_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(engine_banner_);

        for (std::size_t page = 0; page < page_buttons_.size(); ++page) {
            auto button = std::make_unique<juce::TextButton>(
                page < pam::kLaneCount
                    ? "LANE " + juce::String(static_cast<int>(page + 1U))
                    : "GLOBAL / CLEAR");
            button->setColour(
                juce::TextButton::buttonOnColourId,
                page < pam::kLaneCount
                    ? kLaneColours[page]
                    : juce::Colour{kGlobalColourArgb});
            button->setColour(juce::TextButton::buttonColourId, juce::Colour{0xff252c35});
            button->onClick = [this, page] {
                static_cast<void>(engine_.submitGuiCc(
                    40 + static_cast<int>(page), 127));
                static_cast<void>(engine_.submitGuiCc(
                    40 + static_cast<int>(page), 0));
            };
            addAndMakeVisible(*button);
            page_buttons_[page] = std::move(button);
        }

        clear_fx_button_.setButtonText("CLEAR FX");
        clear_fx_button_.setColour(
            juce::TextButton::buttonColourId, juce::Colour{0xff492f4a});
        clear_fx_button_.setColour(
            juce::TextButton::buttonOnColourId, juce::Colour{kGlobalColourArgb});
        clear_fx_button_.onClick = [this] {
            engine_.updateControls([](pam::Controls& controls) {
                ++controls.effect_clear_generation;
            });
        };
        addAndMakeVisible(clear_fx_button_);

        status_.setText(
            "Build-only prototype: press Start audio explicitly; refresh/select MIDI explicitly",
            juce::dontSendNotification);
        status_.setColour(juce::Label::textColourId, juce::Colour{0xff91a0b3});
        status_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(status_);

        projectAcceptedState(engine_.acceptedSnapshot());
        updateEnabledState();
        startTimerHz(20);
        setSize(1280, 690);
    }

    ~MainComponent() override { setLookAndFeel(nullptr); }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff101419});
        graphics.setColour(juce::Colour{0xff2b333d});
        graphics.drawRoundedRectangle(
            getLocalBounds().toFloat().reduced(8.5F), 6.0F, 1.0F);
        graphics.setColour(juce::Colour{0xff202730});
        graphics.fillRoundedRectangle(
            juce::Rectangle<float>{18.0F, 142.0F,
                static_cast<float>(getWidth() - 36),
                static_cast<float>(getHeight() - 166)}, 6.0F);
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
        lifecycle.removeFromLeft(12);
        clear_fx_button_.setBounds(lifecycle.removeFromLeft(92));
        lifecycle.removeFromLeft(12);
        engine_banner_.setBounds(lifecycle);
        area.removeFromTop(8);

        auto lanes = area.removeFromTop(42);
        for (std::size_t page = 0; page < page_buttons_.size(); ++page) {
            const auto remaining = static_cast<int>(page_buttons_.size() - page);
            page_buttons_[page]->setBounds(
                lanes.removeFromLeft(lanes.getWidth() / remaining).reduced(4));
        }
        area.removeFromTop(5);

        auto context = area.removeFromTop(32);
        voice_mode_button_.setBounds(context.removeFromLeft(86).reduced(2));
        motion_mode_button_.setBounds(context.removeFromLeft(94).reduced(2));
        context.removeFromLeft(10);
        surface_guide_.setBounds(context);
        area.removeFromTop(5);

        auto top = area.removeFromTop(214);
        top_group_.setBounds(top);
        layoutSurfaceRow(
            top.reduced(10, 22), top_sliders_, top_labels_);
        area.removeFromTop(5);
        auto bottom = area.removeFromTop(214);
        bottom_group_.setBounds(bottom);
        layoutSurfaceRow(
            bottom.reduced(10, 22), bottom_sliders_, bottom_labels_);
    }

private:
    static juce::String text(std::string_view value) {
        return juce::String::fromUTF8(
            value.data(), static_cast<int>(value.size()));
    }

    static juce::String formatSurfaceValue(
        pam::PresentationKind presentation,
        double value) {
        switch (presentation) {
            case pam::PresentationKind::model: {
                const auto model = static_cast<std::uint8_t>(
                    juce::jlimit(0, 23, juce::roundToInt(value)));
                return juce::String(static_cast<int>(model)).paddedLeft('0', 2)
                    + " " + juce::String(pam::modelName(model)).toUpperCase();
            }
            case pam::PresentationKind::note:
                return juce::String(value, std::floor(value) == value ? 0 : 1);
            case pam::PresentationKind::unit_percent:
            case pam::PresentationKind::chance:
            case pam::PresentationKind::depth:
                return juce::String(juce::roundToInt(value * 100.0)) + "%";
            case pam::PresentationKind::signed_percent:
                if (std::abs(value) < 0.0005) return "DIRECT";
                return (value > 0.0 ? "+" : "")
                    + juce::String(juce::roundToInt(value * 100.0)) + "%";
            case pam::PresentationKind::trigger_switch:
                return value >= 0.5 ? "ON" : "OFF";
            case pam::PresentationKind::rate: {
                const auto index = static_cast<std::size_t>(
                    juce::jlimit(0, 15, juce::roundToInt(value)));
                const auto& rate = pam::rateTable()[index];
                return juce::String(static_cast<int>(rate.numerator)) + "/"
                    + juce::String(static_cast<int>(rate.denominator));
            }
            case pam::PresentationKind::phase:
                return juce::String(juce::roundToInt(value)) + "/127";
            case pam::PresentationKind::shape:
                return juce::String(pam::shapeName(static_cast<pam::Shape>(
                    juce::jlimit(0, 7, juce::roundToInt(value))))).toUpperCase();
            case pam::PresentationKind::hits:
                return juce::String(juce::roundToInt(value)) + "/16";
            case pam::PresentationKind::rotation:
                return "STEP " + juce::String(juce::roundToInt(value));
            case pam::PresentationKind::repeat:
                return value < 0.5
                    ? juce::String{"FREE"}
                    : "x" + juce::String(juce::roundToInt(value));
            case pam::PresentationKind::bpm:
                return juce::String(juce::roundToInt(value)) + " BPM";
            case pam::PresentationKind::disabled:
                return "-";
        }
        return "?";
    }

    static void layoutSurfaceRow(
        juce::Rectangle<int> area,
        const std::array<std::unique_ptr<SurfaceSlider>, pam::kSurfaceColumnCount>& sliders,
        const std::array<std::unique_ptr<juce::Label>, pam::kSurfaceColumnCount>& labels) {
        for (std::size_t column = 0; column < pam::kSurfaceColumnCount; ++column) {
            const auto remaining = static_cast<int>(
                pam::kSurfaceColumnCount - column);
            auto cell = area.removeFromLeft(area.getWidth() / remaining).reduced(5);
            labels[column]->setBounds(cell.removeFromTop(22));
            sliders[column]->setBounds(cell);
        }
    }

    void configureSurfaceSlot(pam::SurfaceRow row, std::size_t column) {
        auto& sliders = row == pam::SurfaceRow::top
            ? top_sliders_
            : bottom_sliders_;
        auto& labels = row == pam::SurfaceRow::top
            ? top_labels_
            : bottom_labels_;
        auto slider = std::make_unique<SurfaceSlider>();
        slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, 128, 20);
        slider->setRange(0.0, 1.0, 0.001);
        slider->setColour(
            juce::Slider::rotarySliderFillColourId, juce::Colour{0xff4fc3d7});
        slider->onValueChange = [this, row, column] {
            auto& source = row == pam::SurfaceRow::top
                ? top_sliders_
                : bottom_sliders_;
            const auto value = source[column]->getValue();
            engine_.updateControls([row, column, value](pam::Controls& controls) {
                static_cast<void>(pam::applySurfaceValue(
                    controls, row, column, value));
            });
        };
        addAndMakeVisible(*slider);
        sliders[column] = std::move(slider);

        auto label = std::make_unique<juce::Label>();
        label->setText("-", juce::dontSendNotification);
        label->setJustificationType(juce::Justification::centred);
        label->setFont(juce::FontOptions{11.0F, juce::Font::bold});
        label->setColour(
            juce::Label::textColourId, juce::Colour{0xffc7ced7});
        addAndMakeVisible(*label);
        labels[column] = std::move(label);
    }

    void projectSlot(
        SurfaceSlider& slider,
        juce::Label& label,
        const pam::SurfaceSlot& slot,
        juce::Colour colour) {
        label.setText(text(slot.label), juce::dontSendNotification);
        label.setTooltip(text(slot.tooltip));
        slider.setTooltip(text(slot.tooltip));
        slider.setRange(slot.minimum, slot.maximum, slot.interval);
        const auto presentation = slot.presentation;
        slider.textFromValueFunction = [presentation](double value) {
            return formatSurfaceValue(presentation, value);
        };
        slider.setBinaryPresentation(
            presentation == pam::PresentationKind::trigger_switch);
        if (!slider.userGestureActive()) {
            slider.setValue(slot.value, juce::dontSendNotification);
        }
        slider.setColour(juce::Slider::rotarySliderFillColourId, colour);
        slider.setEnabled(engine_.audioActive() && slot.enabled);
        slider.setAlpha(slot.enabled ? 1.0F : 0.32F);
        label.setAlpha(slot.enabled ? 1.0F : 0.42F);
    }

    void projectAcceptedState(const pam::Snapshot& snapshot) {
        const auto selected_page = std::min<std::size_t>(
            snapshot.accepted.selected_page, pam::kGlobalPageIndex);
        const bool global = selected_page == pam::kGlobalPageIndex;
        current_surface_ = pam::surfaceModel(snapshot);
        for (std::size_t page = 0; page < page_buttons_.size(); ++page) {
            page_buttons_[page]->setToggleState(
                page == selected_page, juce::dontSendNotification);
        }
        running_button_.setToggleState(
            snapshot.accepted.running, juce::dontSendNotification);
        voice_mode_button_.setVisible(!global);
        motion_mode_button_.setVisible(!global);
        voice_mode_button_.setToggleState(
            !global && snapshot.accepted.lane_control_mode
                    == pam::LaneControlMode::voice,
            juce::dontSendNotification);
        motion_mode_button_.setToggleState(
            !global && snapshot.accepted.lane_control_mode
                    == pam::LaneControlMode::motion,
            juce::dontSendNotification);
        clear_fx_button_.setVisible(global);
        top_group_.setText(text(current_surface_.top_group));
        bottom_group_.setText(text(current_surface_.bottom_group));
        surface_guide_.setText(
            text(current_surface_.guide), juce::dontSendNotification);

        const auto colour = global
            ? juce::Colour{kGlobalColourArgb}
            : kLaneColours[selected_page];
        for (std::size_t column = 0;
             column < pam::kSurfaceColumnCount;
             ++column) {
            projectSlot(
                *top_sliders_[column],
                *top_labels_[column],
                current_surface_.top[column],
                colour);
            projectSlot(
                *bottom_sliders_[column],
                *bottom_labels_[column],
                current_surface_.bottom[column],
                colour);
        }

        if (global) {
            const auto& effect = snapshot.accepted.cohesion;
            engine_banner_.setText(
                "GLOBAL PERFORMANCE  /  COHERE "
                    + juce::String(effect.cohere, 2)
                    + "  /  FX CLEARS "
                    + juce::String(snapshot.diagnostics.effect_clear_count)
                    + "  /  PRESS GLOBAL AGAIN TO CLEAR",
                juce::dontSendNotification);
            return;
        }
        const auto& voice = snapshot.accepted.voices[selected_page];
        const auto resolved_model = snapshot.resolved_engines[selected_page];
        const auto context = snapshot.accepted.lane_control_mode
                == pam::LaneControlMode::voice
            ? "VOICE"
            : "MOTION";
        engine_banner_.setText(
            "LANE " + juce::String(static_cast<int>(selected_page) + 1)
                + "  /  " + context
                + "  /  MODEL "
                + juce::String(static_cast<int>(voice.engine)).paddedLeft('0', 2)
                + " " + juce::String(pam::modelName(voice.engine)).toUpperCase()
                + "  /  NOW "
                + juce::String(static_cast<int>(resolved_model)).paddedLeft('0', 2)
                + " " + juce::String(pam::modelName(resolved_model)).toUpperCase(),
            juce::dontSendNotification);
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
        for (auto& button : page_buttons_) button->setEnabled(active);
        for (std::size_t column = 0;
             column < pam::kSurfaceColumnCount;
             ++column) {
            top_sliders_[column]->setEnabled(
                active && current_surface_.top[column].enabled);
            bottom_sliders_[column]->setEnabled(
                active && current_surface_.bottom[column].enabled);
        }
        const auto lane_context = current_surface_.context
            != pam::SurfaceContext::global;
        voice_mode_button_.setEnabled(active && lane_context);
        motion_mode_button_.setEnabled(active && lane_context);
        clear_fx_button_.setEnabled(
            active && current_surface_.context == pam::SurfaceContext::global);
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
    juce::Label engine_banner_;
    juce::Label surface_guide_;
    juce::GroupComponent top_group_;
    juce::GroupComponent bottom_group_;
    juce::TextButton audio_button_;
    juce::TextButton refresh_midi_button_;
    juce::TextButton clear_fx_button_;
    juce::TextButton voice_mode_button_;
    juce::TextButton motion_mode_button_;
    juce::ComboBox midi_selector_;
    juce::ToggleButton running_button_;
    juce::Array<juce::MidiDeviceInfo> midi_inputs_;
    std::array<std::unique_ptr<juce::TextButton>, pam::kPageCount> page_buttons_;
    std::array<std::unique_ptr<SurfaceSlider>, pam::kSurfaceColumnCount>
        top_sliders_;
    std::array<std::unique_ptr<juce::Label>, pam::kSurfaceColumnCount>
        top_labels_;
    std::array<std::unique_ptr<SurfaceSlider>, pam::kSurfaceColumnCount>
        bottom_sliders_;
    std::array<std::unique_ptr<juce::Label>, pam::kSurfaceColumnCount>
        bottom_labels_;
    pam::SurfaceModel current_surface_{};
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
        return "0.5.0";
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
