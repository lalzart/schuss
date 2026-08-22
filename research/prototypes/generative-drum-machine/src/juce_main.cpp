#include "schuss/generative_drum_machine/control_map.hpp"
#include "schuss/generative_drum_machine/control_snapshot.hpp"
#include "schuss/generative_drum_machine/core.hpp"
#include "schuss/generative_drum_machine/ui_model.hpp"

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <mutex>

namespace {

namespace gdm = schuss::generative_drum_machine;

constexpr int kRequestedBlockFrames = 128;
constexpr int kMaximumBlockFrames = 512;
constexpr float kQ27ToFloat = 1.0f / 134217728.0f;

const std::array<juce::Colour, gdm::kLogicalLaneCount> kLaneColours{{
    juce::Colour{0xffff694d},
    juce::Colour{0xffff9f43},
    juce::Colour{0xffffd166},
    juce::Colour{0xff5dd9c1},
    juce::Colour{0xff58a6ff},
    juce::Colour{0xffb388ff},
}};

class StreamingInstrumentAudioEngine final
    : public juce::AudioIODeviceCallback,
      public juce::MidiInputCallback {
public:
    StreamingInstrumentAudioEngine()
        : controls_(gdm::desktopAuditionControls()) {
        static_assert(std::atomic<std::uint64_t>::is_always_lock_free);
        static_assert(std::atomic<std::uint32_t>::is_always_lock_free);
        for (auto& activity : lane_activity_epochs_) {
            activity.store(0U, std::memory_order_relaxed);
        }
        published_controls_.publish(controls_);
        callback_controls_ = controls_;
    }

    ~StreamingInstrumentAudioEngine() override {
        closeMidiInput();
        device_manager_.removeAudioCallback(this);
        device_manager_.closeAudioDevice();
    }

    juce::String start() {
        auto error = device_manager_.initialiseWithDefaultDevices(0, 2);
        if (error.isNotEmpty()) return "Audio output unavailable: " + error;
        auto setup = device_manager_.getAudioDeviceSetup();
        setup.sampleRate = static_cast<double>(gdm::kSampleRateHz);
        setup.bufferSize = kRequestedBlockFrames;
        error = device_manager_.setAudioDeviceSetup(setup, true);
        if (error.isNotEmpty()) {
            device_manager_.closeAudioDevice();
            return "48 kHz stereo setup unavailable: " + error;
        }
        auto* device = device_manager_.getCurrentAudioDevice();
        if (device == nullptr
            || device->getCurrentSampleRate() != static_cast<double>(gdm::kSampleRateHz)
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples() > kMaximumBlockFrames) {
            device_manager_.closeAudioDevice();
            return "Generative Drums requires 48 kHz stereo output and blocks up to 512";
        }
        callback_block_frames_.store(
            static_cast<std::uint32_t>(device->getCurrentBufferSizeSamples()),
            std::memory_order_release);
        device_manager_.addAudioCallback(this);
        return "48 kHz streaming output active | controls apply next block";
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
        received_midi_messages_.store(0U, std::memory_order_release);
        mapped_midi_messages_.store(0U, std::memory_order_release);
        last_midi_channel_.store(0, std::memory_order_release);
        last_midi_cc_.store(-1, std::memory_order_release);
        last_midi_value_.store(-1, std::memory_order_release);
        return "MIDI input active: " + device.name;
    }

    juce::String disableMidiInput() {
        closeMidiInput();
        return "MIDI input disabled";
    }

    [[nodiscard]] gdm::Controls controlsSnapshot() const {
        const std::lock_guard<std::mutex> lock(control_mutex_);
        return controls_;
    }

    [[nodiscard]] std::uint32_t pendingFillCount() const noexcept {
        return fill_request_sequence_.load(std::memory_order_acquire)
                == consumed_fill_sequence_.load(std::memory_order_acquire)
            ? 0U
            : 1U;
    }

    [[nodiscard]] int preparedFillPhrase() const noexcept { return -1; }
    [[nodiscard]] int activeFillPhrase() const noexcept { return -1; }

    [[nodiscard]] double phraseProgress() const noexcept {
        return static_cast<double>(cycle_progress_u15_.load(std::memory_order_acquire))
            / 32767.0;
    }

    [[nodiscard]] std::uint64_t laneActivityEpoch(std::size_t lane) const noexcept {
        return lane < lane_activity_epochs_.size()
            ? lane_activity_epochs_[lane].load(std::memory_order_acquire)
            : 0U;
    }

    [[nodiscard]] juce::String statusText() const {
        juce::String status = audio_ready_.load(std::memory_order_acquire)
            ? "AUDIO 48K / STREAM"
            : "AUDIO WAIT";
        status += "  |  CYCLE "
            + juce::String(cycle_index_.load(std::memory_order_acquire) + 1U);
        const auto controls = controlsSnapshot();
        const auto rhythm = gdm::rhythmPresetInfo(controls.rhythm_preset);
        status += "  |  " + juce::String{rhythm.name}
            + " " + juce::String{rhythm.meter_numerator}
            + "/" + juce::String{rhythm.note_value_denominator};
        if (controls.voice_shaping
            && controls.selected_voice_lane < gdm::kLogicalLaneCount) {
            status += "  |  VOICE "
                + juce::String(controls.selected_voice_lane + 1U)
                + " "
                + juce::String{gdm::laneName(
                    static_cast<gdm::Lane>(controls.selected_voice_lane))}.toUpperCase();
        }
        status += "  |  BLOCK "
            + juce::String(callback_block_frames_.load(std::memory_order_acquire))
            + " / PEAK "
            + juce::String(callback_peak_permille_.load(std::memory_order_acquire) / 10.0, 1)
            + "%";
        if (stream_failures_.load(std::memory_order_acquire) != 0U) {
            status += "  |  STREAM ERR "
                + juce::String(stream_failures_.load(std::memory_order_acquire));
        }
        if (selected_midi_input_identifier_.isEmpty()) {
            status += "  |  NO MIDI INPUT";
        } else {
            status += "  |  MIDI " + selected_midi_input_name_;
            status += " "
                + juce::String(mapped_midi_messages_.load(std::memory_order_acquire))
                + "/"
                + juce::String(received_midi_messages_.load(std::memory_order_acquire));
            const auto cc = last_midi_cc_.load(std::memory_order_acquire);
            if (cc >= 0) {
                status += "  |  CH"
                    + juce::String(last_midi_channel_.load(std::memory_order_acquire))
                    + " CC" + juce::String(cc)
                    + "=" + juce::String(last_midi_value_.load(std::memory_order_acquire));
            }
        }
        return status;
    }

    gdm::MappingResult submitCc(
        std::uint8_t channel,
        std::uint8_t cc,
        std::uint8_t value) {
        auto mapping = gdm::mapMidiCc(channel, cc, value);
        if (!mapping.dispatchesSemantic()) return mapping;
        bool fill_queued = false;
        {
            const std::lock_guard<std::mutex> lock(control_mutex_);
            if (!gdm::applyMapping(controls_, fill_queued, mapping)) {
                if (cc >= 28U && cc <= 33U
                    && mapping.status == gdm::MappingStatus::accepted_continuous) {
                    mapping.status = gdm::MappingStatus::inactive_mode;
                }
                return mapping;
            }
            published_controls_.publish(controls_);
        }
        if (fill_queued) {
            fill_request_sequence_.fetch_add(1U, std::memory_order_release);
        }
        return mapping;
    }

    bool selectRhythm(std::uint8_t rhythm_preset) {
        const std::lock_guard<std::mutex> lock(control_mutex_);
        if (!gdm::selectRhythmPreset(controls_, rhythm_preset)) return false;
        published_controls_.publish(controls_);
        return true;
    }

    void handleIncomingMidiMessage(
        juce::MidiInput*,
        const juce::MidiMessage& message) override {
        received_midi_messages_.fetch_add(1U, std::memory_order_relaxed);
        if (!message.isController()) return;
        last_midi_channel_.store(message.getChannel(), std::memory_order_relaxed);
        last_midi_cc_.store(message.getControllerNumber(), std::memory_order_relaxed);
        last_midi_value_.store(message.getControllerValue(), std::memory_order_relaxed);
        const auto mapped = submitCc(
            static_cast<std::uint8_t>(message.getChannel()),
            static_cast<std::uint8_t>(message.getControllerNumber()),
            static_cast<std::uint8_t>(message.getControllerValue()));
        if (mapped.accepted()) {
            mapped_midi_messages_.fetch_add(1U, std::memory_order_relaxed);
        }
    }

    void audioDeviceAboutToStart(juce::AudioIODevice* device) override {
        audio_ready_.store(false, std::memory_order_release);
        stream_.reset(1396918357U);
        callback_controls_ = published_controls_.load(callback_controls_);
        cycle_index_.store(0U, std::memory_order_release);
        cycle_progress_u15_.store(0U, std::memory_order_release);
        callback_peak_permille_.store(0U, std::memory_order_release);
        if (device == nullptr
            || device->getCurrentSampleRate() != static_cast<double>(gdm::kSampleRateHz)
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples() > kMaximumBlockFrames) {
            return;
        }
        callback_block_frames_.store(
            static_cast<std::uint32_t>(device->getCurrentBufferSizeSamples()),
            std::memory_order_release);
        audio_ready_.store(true, std::memory_order_release);
    }

    void audioDeviceStopped() override {
        audio_ready_.store(false, std::memory_order_release);
        cycle_index_.store(0U, std::memory_order_release);
        cycle_progress_u15_.store(0U, std::memory_order_release);
    }

    void audioDeviceIOCallbackWithContext(
        const float* const*,
        int,
        float* const* output_channels,
        int output_channel_count,
        int frames,
        const juce::AudioIODeviceCallbackContext&) override {
        clearOutputs(output_channels, output_channel_count, frames);
        if (!audio_ready_.load(std::memory_order_acquire)
            || output_channels == nullptr
            || output_channel_count < 2
            || output_channels[0] == nullptr
            || output_channels[1] == nullptr
            || frames < 1
            || frames > kMaximumBlockFrames) {
            return;
        }
        const auto ticks_start = juce::Time::getHighResolutionTicks();
        callback_controls_ = published_controls_.load(callback_controls_);
        const auto fill_sequence = fill_request_sequence_.load(std::memory_order_acquire);
        gdm::StreamingProcessReport report{};
        const auto ok = stream_.process(
            callback_controls_,
            fill_sequence,
            callback_left_.data(),
            callback_right_.data(),
            static_cast<std::size_t>(frames),
            &report);
        if (!ok) {
            stream_failures_.fetch_add(1U, std::memory_order_relaxed);
            return;
        }
        consumed_fill_sequence_.store(fill_sequence, std::memory_order_release);
        for (int frame = 0; frame < frames; ++frame) {
            output_channels[0][frame] = static_cast<float>(callback_left_[frame]) * kQ27ToFloat;
            output_channels[1][frame] = static_cast<float>(callback_right_[frame]) * kQ27ToFloat;
        }
        for (std::size_t index = 0U; index < report.hit_count; ++index) {
            const auto lane = static_cast<std::size_t>(report.hits[index].lane);
            if (lane < lane_activity_epochs_.size()) {
                lane_activity_epochs_[lane].fetch_add(1U, std::memory_order_relaxed);
            }
        }
        cycle_index_.store(report.cycle_index, std::memory_order_release);
        cycle_progress_u15_.store(report.cycle_progress_u15, std::memory_order_release);
        const auto ticks_elapsed = static_cast<std::uint64_t>(
            juce::Time::getHighResolutionTicks() - ticks_start);
        const auto ticks_per_second = static_cast<std::uint64_t>(
            juce::Time::getHighResolutionTicksPerSecond());
        const auto permille = ticks_per_second == 0U
            ? 0U
            : static_cast<std::uint32_t>(std::min<std::uint64_t>(
                  99999U,
                  ticks_elapsed * gdm::kSampleRateHz * 1000U
                      / (ticks_per_second * static_cast<std::uint64_t>(frames))));
        auto peak = callback_peak_permille_.load(std::memory_order_relaxed);
        while (peak < permille
               && !callback_peak_permille_.compare_exchange_weak(
                   peak, permille, std::memory_order_relaxed)) {
        }
    }

private:
    void closeMidiInput() {
        if (selected_midi_input_identifier_.isEmpty()) return;
        device_manager_.removeMidiInputDeviceCallback(
            selected_midi_input_identifier_, this);
        device_manager_.setMidiInputDeviceEnabled(
            selected_midi_input_identifier_, false);
        selected_midi_input_identifier_.clear();
        selected_midi_input_name_.clear();
    }

    static void clearOutputs(
        float* const* outputs,
        int output_channel_count,
        int frames) noexcept {
        if (outputs == nullptr || frames <= 0) return;
        for (int channel = 0; channel < output_channel_count; ++channel) {
            if (outputs[channel] != nullptr) {
                std::fill_n(outputs[channel], frames, 0.0f);
            }
        }
    }

    juce::AudioDeviceManager device_manager_;
    mutable std::mutex control_mutex_;
    gdm::Controls controls_{};
    gdm::AtomicControlSnapshot published_controls_{};
    gdm::Controls callback_controls_{};
    gdm::StreamingEngine stream_{1396918357U};
    std::array<std::int32_t, gdm::kMaximumStreamingBlockFrames> callback_left_{};
    std::array<std::int32_t, gdm::kMaximumStreamingBlockFrames> callback_right_{};
    std::atomic<bool> audio_ready_{false};
    std::atomic<std::uint64_t> fill_request_sequence_{0U};
    std::atomic<std::uint64_t> consumed_fill_sequence_{0U};
    std::atomic<std::uint32_t> cycle_index_{0U};
    std::atomic<std::uint16_t> cycle_progress_u15_{0U};
    std::atomic<std::uint32_t> callback_block_frames_{0U};
    std::atomic<std::uint32_t> callback_peak_permille_{0U};
    std::atomic<std::uint64_t> stream_failures_{0U};
    std::array<std::atomic<std::uint64_t>, gdm::kLogicalLaneCount>
        lane_activity_epochs_{};
    juce::String selected_midi_input_identifier_;
    juce::String selected_midi_input_name_;
    std::atomic<std::uint64_t> received_midi_messages_{0U};
    std::atomic<std::uint64_t> mapped_midi_messages_{0U};
    std::atomic<int> last_midi_channel_{0};
    std::atomic<int> last_midi_cc_{-1};
    std::atomic<int> last_midi_value_{-1};
};

class DrumLookAndFeel final : public juce::LookAndFeel_V4 {
public:
    DrumLookAndFeel() {
        setColour(juce::Slider::textBoxTextColourId, juce::Colour{0xffe9edf4});
        setColour(juce::Slider::textBoxBackgroundColourId, juce::Colour{0xff11151b});
        setColour(juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
        setColour(juce::ComboBox::backgroundColourId, juce::Colour{0xff171d25});
        setColour(juce::ComboBox::textColourId, juce::Colour{0xffd8dee9});
        setColour(juce::ComboBox::outlineColourId, juce::Colour{0xff313a46});
        setColour(juce::PopupMenu::backgroundColourId, juce::Colour{0xff171d25});
        setColour(juce::PopupMenu::textColourId, juce::Colour{0xffd8dee9});
    }

    void drawRotarySlider(
        juce::Graphics& graphics,
        int x,
        int y,
        int width,
        int height,
        float position,
        float start_angle,
        float end_angle,
        juce::Slider& slider) override {
        const auto radius = static_cast<float>(std::min(width, height)) * 0.38f;
        const auto centre = juce::Point<float>{
            static_cast<float>(x) + static_cast<float>(width) * 0.5f,
            static_cast<float>(y) + static_cast<float>(height) * 0.46f};
        const auto line_width = std::max(3.0f, radius * 0.12f);
        juce::Rectangle<float> arc_bounds{
            centre.x - radius,
            centre.y - radius,
            radius * 2.0f,
            radius * 2.0f};

        juce::Path background;
        background.addCentredArc(
            centre.x, centre.y, radius, radius, 0.0f,
            start_angle, end_angle, true);
        graphics.setColour(juce::Colour{0xff303844});
        graphics.strokePath(
            background,
            juce::PathStrokeType{line_width, juce::PathStrokeType::curved,
                                 juce::PathStrokeType::rounded});

        const auto angle = start_angle + position * (end_angle - start_angle);
        juce::Path value_arc;
        value_arc.addCentredArc(
            centre.x, centre.y, radius, radius, 0.0f,
            start_angle, angle, true);
        const auto accent = slider.findColour(juce::Slider::rotarySliderFillColourId);
        graphics.setColour(accent.withAlpha(0.22f));
        graphics.strokePath(
            value_arc,
            juce::PathStrokeType{line_width + 5.0f, juce::PathStrokeType::curved,
                                 juce::PathStrokeType::rounded});
        graphics.setColour(accent);
        graphics.strokePath(
            value_arc,
            juce::PathStrokeType{line_width, juce::PathStrokeType::curved,
                                 juce::PathStrokeType::rounded});

        graphics.setColour(juce::Colour{0xff10141a});
        graphics.fillEllipse(arc_bounds.reduced(line_width * 0.9f));
        const auto pointer_length = radius * 0.54f;
        const auto pointer = juce::Point<float>{
            centre.x + std::sin(angle) * pointer_length,
            centre.y - std::cos(angle) * pointer_length};
        graphics.setColour(accent.brighter(0.18f));
        graphics.drawLine({centre, pointer}, std::max(2.0f, radius * 0.07f));
        graphics.fillEllipse(pointer.x - 2.2f, pointer.y - 2.2f, 4.4f, 4.4f);
    }

    void drawButtonBackground(
        juce::Graphics& graphics,
        juce::Button& button,
        const juce::Colour& background,
        bool highlighted,
        bool down) override {
        auto colour = background;
        if (highlighted) colour = colour.brighter(0.10f);
        if (down) colour = colour.brighter(0.22f);
        graphics.setColour(colour);
        graphics.fillRoundedRectangle(button.getLocalBounds().toFloat(), 7.0f);
        graphics.setColour(juce::Colour{0x553f4a59});
        graphics.drawRoundedRectangle(
            button.getLocalBounds().toFloat().reduced(0.5f), 7.0f, 1.0f);
    }
};

class MainComponent final
    : public juce::Component,
      private juce::Timer {
public:
    MainComponent() {
        setLookAndFeel(&look_and_feel_);
        configureLabel(title_, "SCHUSS / GENERATIVE DRUMS", 25.0f, juce::Colour{0xfff0f3f7});
        title_.setFont(juce::FontOptions(25.0f, juce::Font::bold));
        addAndMakeVisible(title_);
        configureLabel(
            subtitle_,
            "SIX AUTHORED LANES  /  FOUR POOLED BRAIDS VOICES  /  RATIONAL TIME",
            11.0f,
            juce::Colour{0xff7f8b9a});
        addAndMakeVisible(subtitle_);
        configureLabel(status_, "INITIALIZING", 11.0f, juce::Colour{0xff9eabba});
        status_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(status_);

        configureLabel(midi_label_, "MIDI INPUT", 10.0f, juce::Colour{0xff7f8b9a});
        addAndMakeVisible(midi_label_);
        midi_selector_.onChange = [this] { applySelectedMidiInput(); };
        addAndMakeVisible(midi_selector_);
        refresh_midi_.setButtonText("REFRESH");
        refresh_midi_.setColour(juce::TextButton::buttonColourId, juce::Colour{0xff222a35});
        refresh_midi_.setColour(juce::TextButton::textColourOffId, juce::Colour{0xffc5ced9});
        refresh_midi_.onClick = [this] { refreshMidiInputs(false); };
        addAndMakeVisible(refresh_midi_);

        configureLabel(rhythm_label_, "RHYTHM", 10.0f, juce::Colour{0xff7f8b9a});
        addAndMakeVisible(rhythm_label_);
        for (std::uint8_t index = 0U; index < gdm::kRhythmPresetCount; ++index) {
            rhythm_selector_.addItem(gdm::rhythmLabel(index), index + 1);
        }
        rhythm_selector_.onChange = [this] {
            const auto index = rhythm_selector_.getSelectedItemIndex();
            if (index >= 0) {
                static_cast<void>(engine_.selectRhythm(static_cast<std::uint8_t>(index)));
            }
        };
        addAndMakeVisible(rhythm_selector_);
        configureLabel(
            rhythm_detail_, "", 10.0f, juce::Colour{0xff8391a2});
        rhythm_detail_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(rhythm_detail_);

        for (std::size_t lane = 0; lane < lane_knobs_.size(); ++lane) {
            lane_knobs_[lane] = makeKnob(
                gdm::kLaneUiControls[lane].id,
                gdm::kLaneUiControls[lane].cc,
                kLaneColours[lane]);
            addAndMakeVisible(*lane_knobs_[lane]);
            shape_lane_buttons_[lane].setButtonText(
                juce::String(static_cast<int>(lane + 1U)) + " SELECT");
            shape_lane_buttons_[lane].setColour(
                juce::TextButton::buttonColourId, juce::Colour{0xff222a35});
            shape_lane_buttons_[lane].setColour(
                juce::TextButton::textColourOffId, kLaneColours[lane]);
            shape_lane_buttons_[lane].onClick = [this, lane] {
                const auto cc = static_cast<std::uint8_t>(40U + lane);
                static_cast<void>(engine_.submitCc(16U, cc, 127U));
                static_cast<void>(engine_.submitCc(16U, cc, 0U));
            };
            addAndMakeVisible(shape_lane_buttons_[lane]);
        }
        for (std::size_t index = 0; index < global_knobs_.size(); ++index) {
            global_knobs_[index] = makeKnob(
                gdm::kGlobalUiControls[index].id,
                gdm::kGlobalUiControls[index].cc,
                index == 0U ? juce::Colour{0xffff6b8a}
                    : index == 1U ? juce::Colour{0xff5eead4}
                                  : juce::Colour{0xff8fb8ff});
            addAndMakeVisible(*global_knobs_[index]);
            configureLabel(
                global_labels_[index],
                juce::String{gdm::kGlobalUiControls[index].label.data(),
                             gdm::kGlobalUiControls[index].label.size()},
                11.0f,
                juce::Colour{0xffc7d0dc});
            global_labels_[index].setJustificationType(juce::Justification::centred);
            addAndMakeVisible(global_labels_[index]);
        }

        fill_.setButtonText("FILL");
        fill_.setColour(juce::TextButton::buttonColourId, juce::Colour{0xffd94f70});
        fill_.setColour(juce::TextButton::textColourOffId, juce::Colour{0xffffffff});
        fill_.onStateChange = [this] {
            const auto down = fill_.isDown();
            if (down == fill_down_) return;
            fill_down_ = down;
            static_cast<void>(engine_.submitCc(16U, 46U, down ? 127U : 0U));
        };
        addAndMakeVisible(fill_);

        configureLabel(
            fill_caption_, "IMMEDIATE / ONE BAR", 10.0f, juce::Colour{0xff7f8b9a});
        fill_caption_.setJustificationType(juce::Justification::centred);
        addAndMakeVisible(fill_caption_);

        configureLabel(
            shape_title_, "VOICE SHAPER / SELECT A LANE", 11.0f,
            juce::Colour{0xff8995a6});
        shape_title_.setFont(juce::FontOptions(11.0f, juce::Font::bold));
        addAndMakeVisible(shape_title_);
        for (std::size_t index = 0; index < shape_knobs_.size(); ++index) {
            const auto& descriptor = gdm::kShapeUiControls[index];
            shape_knobs_[index] = makeKnob(
                descriptor.id,
                descriptor.cc,
                juce::Colour{0xffc792ea});
            addAndMakeVisible(*shape_knobs_[index]);
            configureLabel(
                shape_labels_[index],
                juce::String{descriptor.label.data(), descriptor.label.size()},
                10.0f,
                juce::Colour{0xffb9c3d0});
            shape_labels_[index].setJustificationType(juce::Justification::centred);
            addAndMakeVisible(shape_labels_[index]);
        }

        const auto controls = engine_.controlsSnapshot();
        updateKnobs(controls);
        status_.setText(engine_.start(), juce::dontSendNotification);
        refreshMidiInputs(true);
        startTimerHz(30);
        setSize(1180, 900);
    }

    ~MainComponent() override {
        stopTimer();
        setLookAndFeel(nullptr);
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff0d1117});
        juce::ColourGradient wash{
            juce::Colour{0x222a4f78}, 0.0f, 0.0f,
            juce::Colour{0x0011161e}, static_cast<float>(getWidth()),
            static_cast<float>(getHeight()), false};
        graphics.setGradientFill(wash);
        graphics.fillRect(getLocalBounds());

        graphics.setColour(juce::Colour{0xff252d38});
        graphics.drawLine(22.0f, 66.0f, static_cast<float>(getWidth() - 22), 66.0f, 1.0f);

        for (std::size_t lane = 0; lane < lane_cards_.size(); ++lane) {
            const auto bounds = lane_cards_[lane].toFloat();
            const auto accent = kLaneColours[lane];
            const bool selected = displayed_controls_.voice_shaping
                && displayed_controls_.selected_voice_lane == lane;
            graphics.setColour(juce::Colour{0xff151b23});
            graphics.fillRoundedRectangle(bounds, 10.0f);
            graphics.setColour(accent.withAlpha(
                (selected ? 0.72f : 0.22f) + lane_glow_[lane] * 0.24f));
            graphics.drawRoundedRectangle(
                bounds.reduced(0.5f), 10.0f,
                (selected ? 3.0f : 1.5f) + lane_glow_[lane] * 2.0f);
            graphics.setColour(accent.withAlpha(0.12f + lane_glow_[lane] * 0.30f));
            auto stripe = bounds;
            graphics.fillRoundedRectangle(stripe.removeFromTop(5.0f), 3.0f);

            auto text = lane_cards_[lane].reduced(13).removeFromTop(52);
            graphics.setColour(juce::Colour{0xffedf1f6});
            graphics.setFont(juce::FontOptions(15.0f, juce::Font::bold));
            graphics.drawText(
                juce::String{gdm::kLaneUiControls[lane].label.data(),
                             gdm::kLaneUiControls[lane].label.size()},
                text.removeFromTop(24),
                juce::Justification::centredLeft);
            graphics.setColour(accent.withAlpha(0.78f));
            graphics.setFont(juce::FontOptions(10.0f));
            const auto model = gdm::modelName(static_cast<gdm::Lane>(lane));
            graphics.drawText(
                "VOICE RECIPE / " + juce::String{model.data(), model.size()},
                text.removeFromTop(19),
                juce::Justification::centredLeft);
            graphics.setColour(accent.withAlpha(0.25f + lane_glow_[lane] * 0.75f));
            graphics.fillEllipse(
                static_cast<float>(lane_cards_[lane].getRight() - 24),
                static_cast<float>(lane_cards_[lane].getY() + 18),
                8.0f,
                8.0f);
        }

        graphics.setColour(juce::Colour{0xff141a22});
        graphics.fillRoundedRectangle(global_panel_.toFloat(), 10.0f);
        graphics.setColour(juce::Colour{0xff2a3441});
        graphics.drawRoundedRectangle(global_panel_.toFloat().reduced(0.5f), 10.0f, 1.0f);
        graphics.setColour(juce::Colour{0xff758294});
        graphics.setFont(juce::FontOptions(10.0f, juce::Font::bold));
        graphics.drawText(
            "STREAMING PERFORMANCE",
            global_panel_.reduced(14).removeFromTop(18),
            juce::Justification::centredLeft);

        graphics.setColour(juce::Colour{0xff1d2631});
        graphics.fillRoundedRectangle(progress_bounds_.toFloat(), 4.0f);
        auto progress = progress_bounds_.toFloat();
        progress.setWidth(progress.getWidth() * static_cast<float>(cycle_progress_));
        if (progress.getWidth() > 0.5f) {
            juce::ColourGradient progress_gradient{
                juce::Colour{0xffff6b8a}, progress.getX(), progress.getY(),
                juce::Colour{0xff58a6ff}, progress.getRight(), progress.getY(), false};
            graphics.setGradientFill(progress_gradient);
            graphics.fillRoundedRectangle(progress, 4.0f);
        }
        graphics.setColour(juce::Colour{0xff6f7b8a});
        graphics.setFont(juce::FontOptions(9.0f));
        graphics.drawText(
            "CYCLE POSITION",
            progress_bounds_.translated(0, -18),
            juce::Justification::centredLeft);

        graphics.setColour(juce::Colour{0xff141a22});
        graphics.fillRoundedRectangle(shape_panel_.toFloat(), 10.0f);
        graphics.setColour(displayed_controls_.voice_shaping
            ? kLaneColours[displayed_controls_.selected_voice_lane].withAlpha(0.72f)
            : juce::Colour{0xff2a3441});
        graphics.drawRoundedRectangle(
            shape_panel_.toFloat().reduced(0.5f), 10.0f,
            displayed_controls_.voice_shaping ? 2.0f : 1.0f);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(22);
        auto header = area.removeFromTop(44);
        title_.setBounds(header.removeFromLeft(390));
        status_.setBounds(header.removeFromRight(620));
        subtitle_.setBounds(header);
        area.removeFromTop(12);

        auto midi = area.removeFromTop(32);
        midi_label_.setBounds(midi.removeFromLeft(74));
        midi_selector_.setBounds(midi.removeFromLeft(270));
        midi.removeFromLeft(8);
        refresh_midi_.setBounds(midi.removeFromLeft(82));
        midi.removeFromLeft(24);
        rhythm_label_.setBounds(midi.removeFromLeft(66));
        rhythm_selector_.setBounds(midi.removeFromLeft(250));
        rhythm_detail_.setBounds(area.removeFromTop(24));
        area.removeFromTop(8);

        auto lanes = area.removeFromTop(300);
        for (std::size_t lane = 0; lane < lane_cards_.size(); ++lane) {
            const auto remaining = static_cast<int>(lane_cards_.size() - lane);
            auto cell = lanes.removeFromLeft(lanes.getWidth() / remaining).reduced(6, 0);
            lane_cards_[lane] = cell;
            auto lane_content = cell.reduced(18).withTrimmedTop(64);
            shape_lane_buttons_[lane].setBounds(lane_content.removeFromBottom(30));
            lane_content.removeFromBottom(6);
            lane_knobs_[lane]->setBounds(lane_content);
        }
        area.removeFromTop(14);

        global_panel_ = area.removeFromTop(160);
        auto globals = global_panel_.reduced(18).withTrimmedTop(24);
        for (std::size_t index = 0; index < global_knobs_.size(); ++index) {
            auto cell = globals.removeFromLeft(160).reduced(8, 0);
            global_labels_[index].setBounds(cell.removeFromTop(20));
            global_knobs_[index]->setBounds(cell);
        }
        globals.removeFromLeft(12);
        auto fill_area = globals.removeFromLeft(150).reduced(12, 10);
        fill_caption_.setBounds(fill_area.removeFromTop(20));
        fill_.setBounds(fill_area.reduced(8, 12));
        progress_bounds_ = globals.reduced(18, 45);
        area.removeFromTop(14);

        shape_panel_ = area.removeFromTop(190);
        auto shape_area = shape_panel_.reduced(18).withTrimmedTop(26);
        shape_title_.setBounds(
            shape_panel_.reduced(18).removeFromTop(22));
        for (std::size_t index = 0; index < shape_knobs_.size(); ++index) {
            const auto remaining = static_cast<int>(shape_knobs_.size() - index);
            auto cell = shape_area.removeFromLeft(shape_area.getWidth() / remaining).reduced(6, 0);
            shape_labels_[index].setBounds(cell.removeFromTop(20));
            shape_knobs_[index]->setBounds(cell);
        }
    }

private:
    static void configureLabel(
        juce::Label& label,
        const juce::String& text,
        float size,
        juce::Colour colour) {
        label.setText(text, juce::dontSendNotification);
        label.setFont(juce::FontOptions(size));
        label.setColour(juce::Label::textColourId, colour);
        label.setInterceptsMouseClicks(false, false);
    }

    std::unique_ptr<juce::Slider> makeKnob(
        gdm::ControlId id,
        std::uint8_t cc,
        juce::Colour accent) {
        auto slider = std::make_unique<juce::Slider>();
        slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, 92, 22);
        slider->setRange(0.0, 127.0, 1.0);
        slider->setRotaryParameters(
            juce::MathConstants<float>::pi * 1.25f,
            juce::MathConstants<float>::pi * 2.75f,
            true);
        slider->setColour(juce::Slider::rotarySliderFillColourId, accent);
        slider->textFromValueFunction = [id, cc](double value) {
            gdm::Controls controls{};
            if (cc >= 28U && cc <= 33U) {
                controls.voice_shaping = true;
                controls.selected_voice_lane = 0U;
            }
            bool fill = false;
            const auto mapping = gdm::mapMidiCc(
                16U, cc, static_cast<std::uint8_t>(juce::roundToInt(value)));
            static_cast<void>(gdm::applyMapping(controls, fill, mapping));
            return juce::String{gdm::formatAcceptedValue(id, controls)};
        };
        slider->onValueChange = [this, cc, pointer = slider.get()] {
            static_cast<void>(engine_.submitCc(
                16U,
                cc,
                static_cast<std::uint8_t>(juce::roundToInt(pointer->getValue()))));
        };
        return slider;
    }

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
        midi_selector_.clear(juce::dontSendNotification);
        midi_selector_.addItem("No MIDI input", 1);

        int selected_item = 0;
        int preferred_item = 0;
        int preferred_rank = 0;
        for (int index = 0; index < midi_inputs_.size(); ++index) {
            const auto& input = midi_inputs_.getReference(index);
            midi_selector_.addItem(input.name, index + 2);
            if (input.identifier == previous_identifier) selected_item = index + 1;
            const auto rank = preferenceRank(input);
            if (rank > preferred_rank) {
                preferred_rank = rank;
                preferred_item = index + 1;
            }
        }
        if (selected_item == 0 && select_preferred) selected_item = preferred_item;
        midi_selector_.setSelectedItemIndex(selected_item, juce::sendNotificationSync);
    }

    void applySelectedMidiInput() {
        const auto index = midi_selector_.getSelectedItemIndex() - 1;
        const auto result = index >= 0 && index < midi_inputs_.size()
            ? engine_.selectMidiInput(midi_inputs_.getReference(index))
            : engine_.disableMidiInput();
        status_.setText(result, juce::dontSendNotification);
    }

    void updateKnobs(const gdm::Controls& controls) {
        displayed_controls_ = controls;
        for (std::size_t lane = 0; lane < lane_knobs_.size(); ++lane) {
            lane_knobs_[lane]->setValue(
                gdm::midiValueForAcceptedState(gdm::kLaneUiControls[lane].id, controls),
                juce::dontSendNotification);
        }
        for (std::size_t index = 0; index < global_knobs_.size(); ++index) {
            global_knobs_[index]->setValue(
                gdm::midiValueForAcceptedState(gdm::kGlobalUiControls[index].id, controls),
                juce::dontSendNotification);
        }
        rhythm_selector_.setSelectedItemIndex(
            controls.rhythm_preset,
            juce::dontSendNotification);
        const auto rhythm = gdm::rhythmPresetInfo(controls.rhythm_preset);
        rhythm_detail_.setText(
            juce::String{rhythm.family} + "  /  "
                + juce::String{rhythm.grouping}
                + "  /  INDEPENDENT STUDY",
            juce::dontSendNotification);
        for (std::size_t lane = 0; lane < shape_lane_buttons_.size(); ++lane) {
            const bool selected = controls.voice_shaping
                && controls.selected_voice_lane == lane;
            const auto number = juce::String(static_cast<int>(lane + 1U));
            shape_lane_buttons_[lane].setButtonText(
                number + (selected ? " ACTIVE" : " SELECT"));
            shape_lane_buttons_[lane].setColour(
                juce::TextButton::buttonColourId,
                selected ? kLaneColours[lane].withAlpha(0.32f)
                         : juce::Colour{0xff222a35});
        }
        for (std::size_t index = 0; index < shape_knobs_.size(); ++index) {
            shape_knobs_[index]->setValue(
                gdm::midiValueForAcceptedState(
                    gdm::kShapeUiControls[index].id, controls),
                juce::dontSendNotification);
            shape_knobs_[index]->setEnabled(controls.voice_shaping);
            shape_labels_[index].setEnabled(controls.voice_shaping);
        }
        if (controls.voice_shaping
            && controls.selected_voice_lane < gdm::kLogicalLaneCount) {
            shape_title_.setText(
                "VOICE SHAPER / "
                    + juce::String{gdm::laneName(
                        static_cast<gdm::Lane>(controls.selected_voice_lane))}.toUpperCase(),
                juce::dontSendNotification);
            shape_title_.setColour(
                juce::Label::textColourId,
                kLaneColours[controls.selected_voice_lane]);
        } else {
            shape_title_.setText(
                "VOICE SHAPER / SELECT A LANE",
                juce::dontSendNotification);
            shape_title_.setColour(
                juce::Label::textColourId,
                juce::Colour{0xff8995a6});
        }
    }

    void timerCallback() override {
        updateKnobs(engine_.controlsSnapshot());
        cycle_progress_ = engine_.phraseProgress();
        for (std::size_t lane = 0; lane < lane_glow_.size(); ++lane) {
            const auto epoch = engine_.laneActivityEpoch(lane);
            if (epoch != last_lane_activity_epochs_[lane]) {
                last_lane_activity_epochs_[lane] = epoch;
                lane_glow_[lane] = 1.0f;
            } else {
                lane_glow_[lane] *= 0.82f;
            }
        }
        const auto fills = engine_.pendingFillCount();
        if (fills != 0U) {
            fill_.setButtonText("FILL QUEUED " + juce::String(fills));
        } else if (engine_.preparedFillPhrase() >= 0) {
            fill_.setButtonText("FILL READY");
        } else if (engine_.activeFillPhrase() >= 0) {
            fill_.setButtonText("FILL PLAYING");
        } else {
            fill_.setButtonText("FILL");
        }
        if (++status_ticks_ >= 5) {
            status_ticks_ = 0;
            status_.setText(engine_.statusText(), juce::dontSendNotification);
        }
        repaint();
    }

    DrumLookAndFeel look_and_feel_;
    StreamingInstrumentAudioEngine engine_;
    juce::Label title_;
    juce::Label subtitle_;
    juce::Label status_;
    juce::Label midi_label_;
    juce::ComboBox midi_selector_;
    juce::TextButton refresh_midi_;
    juce::Array<juce::MidiDeviceInfo> midi_inputs_;
    juce::Label rhythm_label_;
    juce::ComboBox rhythm_selector_;
    juce::Label rhythm_detail_;
    std::array<std::unique_ptr<juce::Slider>, gdm::kLogicalLaneCount> lane_knobs_;
    std::array<juce::TextButton, gdm::kLogicalLaneCount> shape_lane_buttons_;
    std::array<std::unique_ptr<juce::Slider>, 3> global_knobs_;
    std::array<juce::Label, 3> global_labels_;
    juce::TextButton fill_;
    juce::Label fill_caption_;
    juce::Label shape_title_;
    std::array<std::unique_ptr<juce::Slider>, 6> shape_knobs_;
    std::array<juce::Label, 6> shape_labels_;
    std::array<juce::Rectangle<int>, gdm::kLogicalLaneCount> lane_cards_;
    juce::Rectangle<int> global_panel_;
    juce::Rectangle<int> shape_panel_;
    juce::Rectangle<int> progress_bounds_;
    gdm::Controls displayed_controls_{};
    std::array<float, gdm::kLogicalLaneCount> lane_glow_{};
    std::array<std::uint64_t, gdm::kLogicalLaneCount> last_lane_activity_epochs_{};
    double cycle_progress_{};
    bool fill_down_{};
    int status_ticks_{};
};

class MainWindow final : public juce::DocumentWindow {
public:
    MainWindow()
        : juce::DocumentWindow(
              "Schuss Generative Drums",
              juce::Colour{0xff0d1117},
              juce::DocumentWindow::closeButton) {
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

class GenerativeDrumsApplication final : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "Schuss Generative Drums"; }
    const juce::String getApplicationVersion() override { return "0.4.0"; }
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

START_JUCE_APPLICATION(GenerativeDrumsApplication)
