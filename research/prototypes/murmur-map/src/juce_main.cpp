#include "schuss/murmur_map/control_map.hpp"
#include "schuss/murmur_map/core.hpp"
#include "schuss/murmur_map/realtime_exchange.hpp"
#include "schuss/murmur_map/ui_model.hpp"

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
#include <string>

namespace mm = schuss::murmur_map;

namespace {

constexpr int kRequestedBlockFrames = 128;
constexpr int kUiTimerHz = 30;
constexpr std::size_t kUiCommandCapacity = 256U;

class InstrumentAudioEngine final
    : public juce::AudioIODeviceCallback,
      public juce::MidiInputCallback {
public:
    InstrumentAudioEngine() {
        collector_.ensureStorageAllocated(4096);
        midi_block_.ensureSize(4096);
        publishPresentation();
    }

    ~InstrumentAudioEngine() override { stop(); }

    [[nodiscard]] juce::String start() {
        stop();
        auto error = device_manager_.initialiseWithDefaultDevices(0, 2);
        if (error.isNotEmpty()) return "Audio output unavailable: " + error;
        auto setup = device_manager_.getAudioDeviceSetup();
        setup.sampleRate = mm::kSampleRateHz;
        setup.bufferSize = kRequestedBlockFrames;
        error = device_manager_.setAudioDeviceSetup(setup, true);
        if (error.isNotEmpty()) {
            device_manager_.closeAudioDevice();
            return "48 kHz stereo setup unavailable: " + error;
        }
        auto* device = device_manager_.getCurrentAudioDevice();
        if (device == nullptr
            || device->getCurrentSampleRate() != mm::kSampleRateHz
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples() > static_cast<int>(mm::kMaximumBlockFrames)) {
            device_manager_.closeAudioDevice();
            return "Murmur Map requires 48 kHz stereo and blocks no larger than 512";
        }
        device_manager_.addAudioCallback(this);
        return ready_.load(std::memory_order_acquire)
            ? "48 kHz output active; select a MIDI input"
            : "Audio callback did not accept the requested configuration";
    }

    void stop() {
        closeMidiInput();
        device_manager_.removeAudioCallback(this);
        device_manager_.closeAudioDevice();
        ready_.store(false, std::memory_order_release);
    }

    [[nodiscard]] bool ready() const noexcept {
        return ready_.load(std::memory_order_acquire);
    }

    [[nodiscard]] juce::Array<juce::MidiDeviceInfo> availableMidiInputs() const {
        return juce::MidiInput::getAvailableDevices();
    }

    [[nodiscard]] const juce::String& selectedMidiInputIdentifier() const noexcept {
        return selected_midi_input_identifier_;
    }

    [[nodiscard]] juce::String selectMidiInput(const juce::MidiDeviceInfo& device) {
        closeMidiInput();
        if (device.identifier.isEmpty()) return "MIDI input disabled";
        device_manager_.setMidiInputDeviceEnabled(device.identifier, true);
        if (!device_manager_.isMidiInputDeviceEnabled(device.identifier)) {
            return "Could not open MIDI input: " + device.name;
        }
        device_manager_.addMidiInputDeviceCallback(device.identifier, this);
        selected_midi_input_identifier_ = device.identifier;
        selected_midi_input_name_ = device.name;
        midi_receive_count_.store(0U, std::memory_order_release);
        midi_ignored_count_.store(0U, std::memory_order_release);
        return "MIDI input active: " + device.name;
    }

    [[nodiscard]] juce::String disableMidiInput() {
        closeMidiInput();
        return "MIDI input disabled";
    }

    [[nodiscard]] juce::String endpointStatus() const {
        if (!ready()) return "Audio output is stopped";
        if (selected_midi_input_identifier_.isEmpty()) return "48 kHz output active | no MIDI input selected";
        if (!device_manager_.isMidiInputDeviceEnabled(selected_midi_input_identifier_)) {
            return "MIDI input disconnected: " + selected_midi_input_name_;
        }
        return "MIDI input active: " + selected_midi_input_name_;
    }

    [[nodiscard]] bool queueUiCommand(const mm::UiCommand& command) noexcept {
        if (ui_commands_.push(command)) return true;
        ui_command_drop_count_.fetch_add(1U, std::memory_order_relaxed);
        return false;
    }

    [[nodiscard]] mm::PresentationSnapshot presentation() const noexcept {
        return presentation_mailbox_.load(last_presentation_);
    }

    void handleIncomingMidiMessage(
        juce::MidiInput*,
        const juce::MidiMessage& message) override {
        midi_receive_count_.fetch_add(1U, std::memory_order_relaxed);
        if (message.isController()) {
            last_midi_channel_.store(static_cast<std::uint8_t>(message.getChannel()), std::memory_order_relaxed);
            last_midi_cc_.store(static_cast<std::uint8_t>(message.getControllerNumber()), std::memory_order_relaxed);
            last_midi_value_.store(static_cast<std::uint8_t>(message.getControllerValue()), std::memory_order_relaxed);
        }
        collector_.handleIncomingMidiMessage(nullptr, message);
    }

    void audioDeviceAboutToStart(juce::AudioIODevice* device) override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
        controller_state_ = mm::defaultControllerState();
        actions_ = {};
        locked_ = false;
        prior_memory_u15_ = controller_state_.controls.memory_u15;
        midi_block_.clear();
        if (device == nullptr
            || device->getCurrentSampleRate() != mm::kSampleRateHz
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples() > static_cast<int>(mm::kMaximumBlockFrames)) {
            return;
        }
        collector_.reset(mm::kSampleRateHz);
        core_ = std::make_unique<mm::Core>();
        publishPresentation();
        ready_.store(true, std::memory_order_release);
    }

    void audioDeviceStopped() override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
        midi_block_.clear();
        publishPresentation();
    }

    void audioDeviceIOCallbackWithContext(
        const float* const*,
        int,
        float* const* output_channels,
        int output_channel_count,
        int frames,
        const juce::AudioIODeviceCallbackContext&) override {
        clearOutputs(output_channels, output_channel_count, frames);
        if (!ready() || core_ == nullptr || output_channels == nullptr
            || output_channel_count < 2 || output_channels[0] == nullptr
            || output_channels[1] == nullptr || frames < 1
            || frames > static_cast<int>(mm::kMaximumBlockFrames)) {
            return;
        }

        midi_block_.clear();
        collector_.removeNextBlockOfMessages(midi_block_, frames);
        for (const auto metadata : midi_block_) {
            const auto message = metadata.getMessage();
            if (!message.isController()) {
                midi_ignored_count_.fetch_add(1U, std::memory_order_relaxed);
                continue;
            }
            const auto mapped = mm::mapMidiCc(
                static_cast<std::uint8_t>(message.getChannel()),
                static_cast<std::uint8_t>(message.getControllerNumber()),
                static_cast<std::uint8_t>(message.getControllerValue()));
            last_mapping_status_.store(
                static_cast<std::uint8_t>(mapped.status), std::memory_order_relaxed);
            const auto applied = mm::applyMapping(controller_state_, mapped);
            if (!mapped.accepted() || !applied.handled) {
                midi_ignored_count_.fetch_add(1U, std::memory_order_relaxed);
            }
            if (mapped.id == mm::ControlId::memory && applied.controls_changed) {
                locked_ = controller_state_.controls.memory_u15 == 32767U;
                if (!locked_) prior_memory_u15_ = controller_state_.controls.memory_u15;
            }
        }

        mm::UiCommand command{};
        while (ui_commands_.pop(command)) {
            static_cast<void>(mm::applyUiCommand(
                controller_state_, actions_, locked_, prior_memory_u15_, command));
        }

        mm::ProcessReport report{};
        static_cast<void>(core_->process(
            controller_state_.controls,
            actions_,
            left_.data(),
            right_.data(),
            static_cast<std::size_t>(frames),
            &report));
        std::copy_n(left_.data(), frames, output_channels[0]);
        std::copy_n(right_.data(), frames, output_channels[1]);
        publishPresentation();
    }

private:
    static void clearOutputs(float* const* outputs, int channels, int frames) noexcept {
        if (outputs == nullptr || frames <= 0) return;
        for (int channel = 0; channel < channels; ++channel) {
            if (outputs[channel] != nullptr) std::fill_n(outputs[channel], frames, 0.0F);
        }
    }

    void publishPresentation() noexcept {
        mm::PresentationSnapshot snapshot{};
        snapshot.core = core_ == nullptr ? mm::Snapshot{} : core_->snapshot();
        if (core_ == nullptr) snapshot.core.accepted_controls = controller_state_.controls;
        snapshot.editor = controller_state_.editor;
        snapshot.midi_receive_count = midi_receive_count_.load(std::memory_order_relaxed);
        snapshot.midi_ignored_count = midi_ignored_count_.load(std::memory_order_relaxed);
        snapshot.last_midi_channel = last_midi_channel_.load(std::memory_order_relaxed);
        snapshot.last_midi_cc = last_midi_cc_.load(std::memory_order_relaxed);
        snapshot.last_midi_value = last_midi_value_.load(std::memory_order_relaxed);
        snapshot.last_mapping_status = static_cast<mm::MappingStatus>(
            last_mapping_status_.load(std::memory_order_relaxed));
        snapshot.ui_command_drop_count = ui_command_drop_count_.load(std::memory_order_relaxed);
        last_presentation_ = snapshot;
        presentation_mailbox_.publish(snapshot);
    }

    void closeMidiInput() {
        if (selected_midi_input_identifier_.isNotEmpty()) {
            device_manager_.removeMidiInputDeviceCallback(selected_midi_input_identifier_, this);
            device_manager_.setMidiInputDeviceEnabled(selected_midi_input_identifier_, false);
        }
        selected_midi_input_identifier_.clear();
        selected_midi_input_name_.clear();
    }

    juce::AudioDeviceManager device_manager_{};
    juce::MidiMessageCollector collector_{};
    juce::MidiBuffer midi_block_{};
    std::unique_ptr<mm::Core> core_{};
    mm::ControllerState controller_state_{mm::defaultControllerState()};
    mm::ActionSequences actions_{};
    bool locked_{};
    std::uint16_t prior_memory_u15_{controller_state_.controls.memory_u15};
    mm::SpscQueue<mm::UiCommand, kUiCommandCapacity> ui_commands_{};
    mutable mm::SnapshotMailbox<mm::PresentationSnapshot> presentation_mailbox_{};
    mutable mm::PresentationSnapshot last_presentation_{};
    std::array<float, mm::kMaximumBlockFrames> left_{};
    std::array<float, mm::kMaximumBlockFrames> right_{};
    std::atomic<bool> ready_{false};
    std::atomic<std::uint64_t> midi_receive_count_{0U};
    std::atomic<std::uint64_t> midi_ignored_count_{0U};
    std::atomic<std::uint64_t> ui_command_drop_count_{0U};
    std::atomic<std::uint8_t> last_midi_channel_{0U};
    std::atomic<std::uint8_t> last_midi_cc_{0U};
    std::atomic<std::uint8_t> last_midi_value_{0U};
    std::atomic<std::uint8_t> last_mapping_status_{
        static_cast<std::uint8_t>(mm::MappingStatus::unknown_controller)};
    juce::String selected_midi_input_identifier_{};
    juce::String selected_midi_input_name_{};
};

class MapView final : public juce::Component {
public:
    std::function<void(std::uint16_t, std::uint16_t)> onDraftPosition;

    void setSnapshot(const mm::PresentationSnapshot& snapshot) {
        snapshot_ = snapshot;
        repaint();
    }

    void paint(juce::Graphics& graphics) override {
        auto area = getLocalBounds().toFloat().reduced(12.0F);
        graphics.setColour(juce::Colour(0xff15191d));
        graphics.fillRoundedRectangle(area, 12.0F);
        graphics.setColour(juce::Colour(0xff303840));
        graphics.drawRoundedRectangle(area, 12.0F, 1.0F);
        const auto field = area.reduced(28.0F, 42.0F);
        graphics.setColour(juce::Colour(0xff22292f));
        for (int index = 1; index < 4; ++index) {
            const float x = field.getX() + field.getWidth() * index / 4.0F;
            const float y = field.getY() + field.getHeight() * index / 4.0F;
            graphics.drawVerticalLine(static_cast<int>(x), field.getY(), field.getBottom());
            graphics.drawHorizontalLine(static_cast<int>(y), field.getX(), field.getRight());
        }

        const auto& controls = snapshot_.core.accepted_controls;
        const auto pointForId = [&](std::uint32_t id) {
            for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
                const auto& waypoint = controls.waypoints[index];
                if (waypoint.id == id) return toPoint(field, waypoint.x_u15, waypoint.y_u15);
            }
            return field.getCentre();
        };
        if (snapshot_.core.route_trace_count > 1U) {
            juce::Path path;
            path.startNewSubPath(pointForId(snapshot_.core.route_trace_ids[0]));
            for (std::size_t index = 1U; index < snapshot_.core.route_trace_count; ++index) {
                path.lineTo(pointForId(snapshot_.core.route_trace_ids[index]));
            }
            graphics.setColour(juce::Colour(0x6657c8c0));
            graphics.strokePath(path, juce::PathStrokeType(2.0F));
        }

        for (std::size_t index = 0U; index < controls.waypoint_count; ++index) {
            const auto& waypoint = controls.waypoints[index];
            const auto point = toPoint(field, waypoint.x_u15, waypoint.y_u15);
            const bool selected = index == snapshot_.editor.selected_waypoint;
            graphics.setColour(selected ? juce::Colour(0xffe4bd65) : juce::Colour(0xff7d8992));
            graphics.fillEllipse(point.x - 9.0F, point.y - 9.0F, 18.0F, 18.0F);
            if (index == controls.home_index) {
                graphics.setColour(juce::Colour(0xfff1eee7));
                graphics.drawEllipse(point.x - 14.0F, point.y - 14.0F, 28.0F, 28.0F, 2.0F);
            }
            graphics.setColour(juce::Colour(0xff111417));
            graphics.setFont(11.0F);
            graphics.drawText(
                juce::String::charToString(static_cast<juce::juce_wchar>('A' + index)),
                juce::Rectangle<float>(point.x - 8.0F, point.y - 8.0F, 16.0F, 16.0F),
                juce::Justification::centred);
        }
        if (snapshot_.editor.dirty) {
            const auto draft = toPoint(
                field, snapshot_.editor.draft_x_u15, snapshot_.editor.draft_y_u15);
            graphics.setColour(juce::Colour(0xffe4bd65));
            graphics.drawEllipse(draft.x - 13.0F, draft.y - 13.0F, 26.0F, 26.0F, 2.0F);
        }
        const auto route = toPoint(
            field, snapshot_.core.route_x_u15, snapshot_.core.route_y_u15);
        graphics.setColour(juce::Colour(0xff65d0c8));
        graphics.fillEllipse(route.x - 5.0F, route.y - 5.0F, 10.0F, 10.0F);

        graphics.setColour(juce::Colour(0xffd7dde1));
        graphics.setFont(14.0F);
        graphics.drawText("AUTHORED SOUND MAP", area.removeFromTop(28.0F), juce::Justification::centredLeft);
        graphics.setColour(juce::Colour(0xff7f8a92));
        graphics.setFont(12.0F);
        graphics.drawText("Drag the selected waypoint; Capture commits the draft.",
            area.removeFromBottom(24.0F), juce::Justification::centredLeft);
    }

    void mouseDown(const juce::MouseEvent& event) override { updateDraft(event.position); }
    void mouseDrag(const juce::MouseEvent& event) override { updateDraft(event.position); }

private:
    [[nodiscard]] static juce::Point<float> toPoint(
        juce::Rectangle<float> field,
        std::uint16_t x,
        std::uint16_t y) {
        return {
            field.getX() + field.getWidth() * static_cast<float>(x) / 32767.0F,
            field.getBottom() - field.getHeight() * static_cast<float>(y) / 32767.0F};
    }

    void updateDraft(juce::Point<float> point) {
        if (!isEnabled() || !onDraftPosition) return;
        auto field = getLocalBounds().toFloat().reduced(12.0F).reduced(28.0F, 42.0F);
        const float normalized_x = juce::jlimit(0.0F, 1.0F, (point.x - field.getX()) / field.getWidth());
        const float normalized_y = juce::jlimit(0.0F, 1.0F, (field.getBottom() - point.y) / field.getHeight());
        onDraftPosition(
            static_cast<std::uint16_t>(std::lround(normalized_x * 32767.0F)),
            static_cast<std::uint16_t>(std::lround(normalized_y * 32767.0F)));
    }

    mm::PresentationSnapshot snapshot_{};
};

class MainComponent final : public juce::Component, private juce::Timer {
public:
    MainComponent() {
        setOpaque(true);
        title_.setText("MURMUR MAP", juce::dontSendNotification);
        title_.setFont(juce::FontOptions{30.0F, juce::Font::bold});
        title_.setColour(juce::Label::textColourId, juce::Colour(0xfff0eee8));
        subtitle_.setText("Steer a remembered route through authored sound places", juce::dontSendNotification);
        subtitle_.setColour(juce::Label::textColourId, juce::Colour(0xff89949b));
        addAndMakeVisible(title_); addAndMakeVisible(subtitle_);

        configureSliders();
        configureButtons();
        map_view_.onDraftPosition = [this](std::uint16_t x, std::uint16_t y) {
            queue({mm::UiCommandKind::set_draft_position, x, y, nextSequence()});
        };
        addAndMakeVisible(map_view_);

        start_audio_.setButtonText("START AUDIO");
        start_audio_.onClick = [this] {
            status_.setText(engine_.start(), juce::dontSendNotification);
            refreshMidiInputs(true);
        };
        refresh_midi_.setButtonText("REFRESH MIDI");
        refresh_midi_.onClick = [this] { refreshMidiInputs(false); };
        midi_inputs_.onChange = [this] { openSelectedMidiInput(); };
        addAndMakeVisible(start_audio_); addAndMakeVisible(refresh_midi_); addAndMakeVisible(midi_inputs_);

        status_.setColour(juce::Label::textColourId, juce::Colour(0xffb7c0c6));
        global_status_.setColour(juce::Label::textColourId, juce::Colour(0xff65d0c8));
        editor_status_.setColour(juce::Label::textColourId, juce::Colour(0xffe4bd65));
        diagnostics_.setColour(juce::Label::textColourId, juce::Colour(0xff7f8a92));
        for (auto* label : {&status_, &global_status_, &editor_status_, &diagnostics_}) {
            addAndMakeVisible(*label);
        }
        status_.setText("Audio output is stopped", juce::dontSendNotification);
        setSize(1320, 860);
        startTimerHz(kUiTimerHz);
    }

    void paint(juce::Graphics& graphics) override { graphics.fillAll(juce::Colour(0xff101316)); }

    void resized() override {
        auto bounds = getLocalBounds().reduced(18);
        auto header = bounds.removeFromTop(58);
        title_.setBounds(header.removeFromLeft(250));
        subtitle_.setBounds(header);
        auto footer = bounds.removeFromBottom(98);
        auto endpoint = footer.removeFromTop(32);
        start_audio_.setBounds(endpoint.removeFromLeft(130).reduced(2));
        refresh_midi_.setBounds(endpoint.removeFromLeft(130).reduced(2));
        midi_inputs_.setBounds(endpoint.removeFromLeft(360).reduced(2));
        status_.setBounds(endpoint.reduced(6, 0));
        global_status_.setBounds(footer.removeFromTop(22));
        editor_status_.setBounds(footer.removeFromTop(22));
        diagnostics_.setBounds(footer.removeFromTop(22));

        auto map_area = bounds.removeFromLeft(590);
        map_view_.setBounds(map_area.reduced(0, 6));
        auto controls = bounds.reduced(14, 4);
        controls.removeFromTop(18);
        layoutSliderRow(controls.removeFromTop(155), 0U);
        controls.removeFromTop(20);
        layoutSliderRow(controls.removeFromTop(155), 8U);
        controls.removeFromTop(24);
        auto waypoint_row = controls.removeFromTop(38);
        for (auto& button : waypoint_buttons_) button.setBounds(waypoint_row.removeFromLeft(78).reduced(3));
        waypoint_row.removeFromLeft(12);
        for (auto& button : lane_buttons_) button.setBounds(waypoint_row.removeFromLeft(88).reduced(3));
        auto action_row = controls.removeFromTop(44);
        for (auto* button : {&capture_, &home_here_, &run_, &lock_}) {
            button->setBounds(action_row.removeFromLeft(120).reduced(3));
        }
        auto utility_row = controls.removeFromTop(44);
        scale_.setBounds(utility_row.removeFromLeft(220).reduced(3));
        for (auto* button : {&reseed_, &panic_, &reset_}) {
            button->setBounds(utility_row.removeFromLeft(110).reduced(3));
        }
    }

private:
    void configureSliders() {
        const auto top_labels = mm::launchControlTopLabels();
        const auto bottom_labels = mm::launchControlBottomLabels();
        const std::array<double, 16> minima{{30000, 250, 0, 2, 0, 0, 0, 0, -24, 0, 0, 0, 40, -60000, -32767, 24}};
        const std::array<double, 16> maxima{{240000, 8000, 32767, 32, 32767, 32767, 32767, 32767, 24, 32767, 32767, 32767, 4000, -6000, 32767, 84}};
        for (std::size_t index = 0U; index < sliders_.size(); ++index) {
            auto& slider = sliders_[index];
            slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            slider.setTextBoxStyle(juce::Slider::TextBoxBelow, false, 76, 20);
            slider.setRange(minima[index], maxima[index], 1.0);
            slider.setColour(juce::Slider::rotarySliderFillColourId,
                index < 8U ? juce::Colour(0xff65d0c8) : juce::Colour(0xffe4bd65));
            slider.setColour(juce::Slider::rotarySliderOutlineColourId, juce::Colour(0xff303840));
            slider.onValueChange = [this, index] { sliderChanged(index); };
            labels_[index].setText(index < 8U ? top_labels[index] : bottom_labels[index - 8U],
                juce::dontSendNotification);
            labels_[index].setJustificationType(juce::Justification::centred);
            labels_[index].setColour(juce::Label::textColourId, juce::Colour(0xff9aa4aa));
            addAndMakeVisible(slider); addAndMakeVisible(labels_[index]);
        }
    }

    void configureButtons() {
        for (std::size_t index = 0U; index < waypoint_buttons_.size(); ++index) {
            waypoint_buttons_[index].setButtonText(
                "WAYPOINT " + juce::String::charToString(
                    static_cast<juce::juce_wchar>('A' + index)));
            waypoint_buttons_[index].onClick = [this, index] {
                queue({mm::UiCommandKind::select_waypoint, static_cast<std::int32_t>(index), 0, nextSequence()});
            };
            addAndMakeVisible(waypoint_buttons_[index]);
        }
        const std::array<juce::String, 3> lane_names{{"ANCHOR", "THREAD", "SPARK"}};
        for (std::size_t index = 0U; index < lane_buttons_.size(); ++index) {
            lane_buttons_[index].setButtonText(lane_names[index]);
            lane_buttons_[index].onClick = [this, index] {
                queue({mm::UiCommandKind::select_lane, static_cast<std::int32_t>(index), 0, nextSequence()});
            };
            addAndMakeVisible(lane_buttons_[index]);
        }
        capture_.setButtonText("CAPTURE");
        capture_.onClick = [this] { queue({mm::UiCommandKind::capture, 0, 0, nextSequence()}); };
        home_here_.setButtonText("HOME HERE");
        home_here_.onClick = [this] {
            queue({mm::UiCommandKind::set_home_index,
                static_cast<std::int32_t>(presentation_.editor.selected_waypoint), 0, nextSequence()});
        };
        run_.setButtonText("RUN"); run_.setClickingTogglesState(true);
        run_.onClick = [this] { queue({mm::UiCommandKind::set_run, run_.getToggleState() ? 1 : 0, 0, nextSequence()}); };
        lock_.setButtonText("LOCK"); lock_.setClickingTogglesState(true);
        lock_.onClick = [this] { queue({mm::UiCommandKind::set_lock, lock_.getToggleState() ? 1 : 0, 0, nextSequence()}); };
        reseed_.setButtonText("RESEED");
        reseed_.onClick = [this] {
            ++reseed_count_;
            queue({mm::UiCommandKind::reseed, 0, 0, mm::kDefaultSeed + reseed_count_});
        };
        panic_.setButtonText("PANIC");
        panic_.onClick = [this] { queue({mm::UiCommandKind::panic, 0, 0, nextSequence()}); };
        reset_.setButtonText("RESET");
        reset_.onClick = [this] { queue({mm::UiCommandKind::reset, 0, 0, nextSequence()}); };
        for (auto* button : {&capture_, &home_here_, &run_, &lock_, &reseed_, &panic_, &reset_}) {
            addAndMakeVisible(*button);
        }
        const std::array<const char*, 9> scales{{
            "Chromatic", "Major", "Natural Minor", "Dorian", "Mixolydian",
            "Major Pentatonic", "Minor Pentatonic", "Whole Tone", "Octatonic H-W"}};
        for (std::size_t index = 0U; index < scales.size(); ++index) {
            scale_.addItem(scales[index], static_cast<int>(index + 1U));
        }
        scale_.onChange = [this] {
            queue({mm::UiCommandKind::set_scale, scale_.getSelectedId() - 1, 0, nextSequence()});
        };
        addAndMakeVisible(scale_);
    }

    void layoutSliderRow(juce::Rectangle<int> row, std::size_t first) {
        const int width = row.getWidth() / 8;
        for (std::size_t local = 0U; local < 8U; ++local) {
            auto cell = row.removeFromLeft(width);
            labels_[first + local].setBounds(cell.removeFromTop(20));
            sliders_[first + local].setBounds(cell.reduced(2));
        }
    }

    void sliderChanged(std::size_t index) {
        if (refreshing_) return;
        static constexpr std::array<mm::UiCommandKind, 16> commands{{
            mm::UiCommandKind::set_tempo, mm::UiCommandKind::set_travel,
            mm::UiCommandKind::set_memory, mm::UiCommandKind::set_length,
            mm::UiCommandKind::set_roam, mm::UiCommandKind::set_home_probability,
            mm::UiCommandKind::set_radius, mm::UiCommandKind::set_density,
            mm::UiCommandKind::set_draft_interval, mm::UiCommandKind::set_draft_activity,
            mm::UiCommandKind::set_draft_timbre, mm::UiCommandKind::set_draft_color,
            mm::UiCommandKind::set_draft_decay, mm::UiCommandKind::set_draft_level,
            mm::UiCommandKind::set_draft_pan, mm::UiCommandKind::set_root}};
        queue({commands[index], static_cast<std::int32_t>(std::lround(sliders_[index].getValue())), 0, nextSequence()});
    }

    void queue(const mm::UiCommand& command) {
        if (!engine_.queueUiCommand(command)) {
            status_.setText("UI command queue full; input was not accepted", juce::dontSendNotification);
        }
    }

    [[nodiscard]] std::uint64_t nextSequence() noexcept { return ++ui_sequence_; }

    void timerCallback() override {
        presentation_ = engine_.presentation();
        map_view_.setSnapshot(presentation_);
        const bool enabled = engine_.ready();
        map_view_.setEnabled(enabled);
        for (auto& slider : sliders_) slider.setEnabled(enabled);
        for (auto& button : waypoint_buttons_) button.setEnabled(enabled);
        for (auto& button : lane_buttons_) button.setEnabled(enabled);
        for (auto* component : {
                 static_cast<juce::Component*>(&capture_),
                 static_cast<juce::Component*>(&home_here_),
                 static_cast<juce::Component*>(&run_),
                 static_cast<juce::Component*>(&lock_),
                 static_cast<juce::Component*>(&reseed_),
                 static_cast<juce::Component*>(&panic_),
                 static_cast<juce::Component*>(&reset_),
                 static_cast<juce::Component*>(&scale_)}) {
            component->setEnabled(enabled);
        }
        refreshFromAccepted();
        global_status_.setText(mm::formatGlobalStatus(presentation_.core), juce::dontSendNotification);
        editor_status_.setText(mm::formatEditorStatus(presentation_.editor), juce::dontSendNotification);
        diagnostics_.setText(mm::formatDiagnostics(presentation_), juce::dontSendNotification);
        if (enabled) status_.setText(engine_.endpointStatus(), juce::dontSendNotification);
    }

    void refreshFromAccepted() {
        const auto& controls = presentation_.core.accepted_controls;
        const auto& draft = presentation_.editor.draft_lane;
        const std::array<double, 16> values{{
            static_cast<double>(controls.tempo_milli_bpm),
            static_cast<double>(controls.travel_milli_quarters),
            static_cast<double>(controls.memory_u15),
            static_cast<double>(controls.memory_length),
            static_cast<double>(controls.roam_u15),
            static_cast<double>(controls.home_u15),
            static_cast<double>(controls.radius_u15),
            static_cast<double>(controls.density_u15),
            static_cast<double>(draft.interval_semitones),
            static_cast<double>(draft.activity_u15),
            static_cast<double>(draft.timbre_u15),
            static_cast<double>(draft.color_u15),
            static_cast<double>(draft.decay_ms),
            static_cast<double>(draft.level_milli_db),
            static_cast<double>(draft.pan_s15),
            static_cast<double>(controls.root_midi_note)}};
        refreshing_ = true;
        for (std::size_t index = 0U; index < sliders_.size(); ++index) {
            sliders_[index].setValue(values[index], juce::dontSendNotification);
        }
        scale_.setSelectedId(static_cast<int>(controls.scale) + 1, juce::dontSendNotification);
        run_.setToggleState(controls.run, juce::dontSendNotification);
        lock_.setToggleState(controls.memory_u15 == 32767U, juce::dontSendNotification);
        for (std::size_t index = 0U; index < waypoint_buttons_.size(); ++index) {
            waypoint_buttons_[index].setToggleState(
                index == presentation_.editor.selected_waypoint, juce::dontSendNotification);
        }
        for (std::size_t index = 0U; index < lane_buttons_.size(); ++index) {
            lane_buttons_[index].setToggleState(
                index == static_cast<std::size_t>(presentation_.editor.selected_lane),
                juce::dontSendNotification);
        }
        refreshing_ = false;
    }

    void refreshMidiInputs(bool open_preferred) {
        const auto devices = engine_.availableMidiInputs();
        midi_devices_.clear();
        midi_inputs_.clear(juce::dontSendNotification);
        midi_inputs_.addItem("No MIDI input", 1);
        int preferred = 1;
        for (int index = 0; index < devices.size(); ++index) {
            midi_devices_.add(devices.getReference(index));
            midi_inputs_.addItem(devices.getReference(index).name, index + 2);
            if (devices.getReference(index).name.containsIgnoreCase("Launch Control 3")) {
                preferred = index + 2;
            }
        }
        midi_inputs_.setSelectedId(preferred, juce::dontSendNotification);
        if (open_preferred && preferred > 1) openSelectedMidiInput();
        else status_.setText(
            devices.isEmpty() ? "No MIDI inputs found" : "MIDI inputs refreshed; choose one",
            juce::dontSendNotification);
    }

    void openSelectedMidiInput() {
        const int selected = midi_inputs_.getSelectedId();
        if (selected <= 1) {
            status_.setText(engine_.disableMidiInput(), juce::dontSendNotification);
            return;
        }
        const int index = selected - 2;
        if (index < 0 || index >= midi_devices_.size()) return;
        status_.setText(engine_.selectMidiInput(midi_devices_.getReference(index)), juce::dontSendNotification);
    }

    InstrumentAudioEngine engine_{};
    mm::PresentationSnapshot presentation_{};
    MapView map_view_{};
    juce::Label title_{};
    juce::Label subtitle_{};
    std::array<juce::Slider, 16> sliders_{};
    std::array<juce::Label, 16> labels_{};
    std::array<juce::TextButton, 4> waypoint_buttons_{};
    std::array<juce::TextButton, 3> lane_buttons_{};
    juce::TextButton capture_{};
    juce::TextButton home_here_{};
    juce::TextButton run_{};
    juce::TextButton lock_{};
    juce::TextButton reseed_{};
    juce::TextButton panic_{};
    juce::TextButton reset_{};
    juce::ComboBox scale_{};
    juce::TextButton start_audio_{};
    juce::TextButton refresh_midi_{};
    juce::ComboBox midi_inputs_{};
    juce::Array<juce::MidiDeviceInfo> midi_devices_{};
    juce::Label status_{};
    juce::Label global_status_{};
    juce::Label editor_status_{};
    juce::Label diagnostics_{};
    std::uint64_t ui_sequence_{};
    std::uint64_t reseed_count_{};
    bool refreshing_{};
};

class MainWindow final : public juce::DocumentWindow {
public:
    MainWindow()
        : juce::DocumentWindow(
            "Murmur Map",
            juce::Colour(0xff101316),
            juce::DocumentWindow::allButtons) {
        setUsingNativeTitleBar(true);
        setResizable(true, true);
        setResizeLimits(1120, 720, 1680, 1080);
        setContentOwned(new MainComponent(), true);
        centreWithSize(getWidth(), getHeight());
        setVisible(true);
    }

    void closeButtonPressed() override { juce::JUCEApplication::getInstance()->systemRequestedQuit(); }
};

class MurmurMapApplication final : public juce::JUCEApplication {
public:
    [[nodiscard]] const juce::String getApplicationName() override { return "Murmur Map"; }
    [[nodiscard]] const juce::String getApplicationVersion() override { return "0.1"; }
    bool moreThanOneInstanceAllowed() override { return false; }
    void initialise(const juce::String&) override { window_ = std::make_unique<MainWindow>(); }
    void shutdown() override { window_.reset(); }
    void systemRequestedQuit() override { quit(); }

private:
    std::unique_ptr<MainWindow> window_{};
};

}  // namespace

START_JUCE_APPLICATION(MurmurMapApplication)
