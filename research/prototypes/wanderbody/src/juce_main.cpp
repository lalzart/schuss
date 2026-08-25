#include "wanderbody/control_surface.hpp"
#include "wanderbody/core.hpp"

#include <juce_audio_utils/juce_audio_utils.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

namespace wb = wanderbody;

namespace {

constexpr int kUiTimerHz = 30;
constexpr std::size_t kContinuousControlCount = 15U;
constexpr std::array<std::size_t, kContinuousControlCount> kDescriptorIndices{{
    0U, 1U, 2U, 3U, 5U, 7U, 8U, 9U, 10U, 11U, 12U, 13U, 14U, 15U, 16U,
}};

template <typename Value, std::size_t Capacity>
class SpscQueue final {
    static_assert(Capacity >= 2U);

public:
    [[nodiscard]] bool push(const Value& value) noexcept {
        const auto write = write_.load(std::memory_order_relaxed);
        const auto next = (write + 1U) % Capacity;
        if (next == read_.load(std::memory_order_acquire)) return false;
        values_[write] = value;
        write_.store(next, std::memory_order_release);
        return true;
    }

    [[nodiscard]] bool popLatest(Value& value) noexcept {
        auto read = read_.load(std::memory_order_relaxed);
        const auto write = write_.load(std::memory_order_acquire);
        if (read == write) return false;
        while (read != write) {
            value = values_[read];
            read = (read + 1U) % Capacity;
        }
        read_.store(read, std::memory_order_release);
        return true;
    }

private:
    std::array<Value, Capacity> values_{};
    std::atomic<std::size_t> write_{0U};
    std::atomic<std::size_t> read_{0U};
};

class AtomicControls final {
public:
    AtomicControls() noexcept { store(wb::defaultControls()); }

    void setContinuous(std::size_t index, double value) noexcept {
        if (index < continuous_.size()) {
            continuous_[index].store(std::clamp(value, 0.0, 1.0), std::memory_order_release);
        }
    }

    void setMotion(wb::MotionMode value) noexcept {
        motion_.store(static_cast<std::uint8_t>(value), std::memory_order_release);
    }

    void setRecurrence(wb::RecurrenceMode value) noexcept {
        recurrence_.store(static_cast<std::uint8_t>(value), std::memory_order_release);
    }

    void store(const wb::Controls& controls) noexcept {
        const std::array<double, kContinuousControlCount> values{{
            controls.external,
            controls.internal,
            controls.anchor,
            controls.field,
            controls.wander,
            controls.mutation,
            controls.fragment,
            controls.energy,
            controls.body,
            controls.structure,
            controls.brightness,
            controls.damping,
            controls.position,
            controls.dry,
            controls.memory,
        }};
        for (std::size_t index = 0U; index < values.size(); ++index) {
            continuous_[index].store(values[index], std::memory_order_release);
        }
        setMotion(controls.motion);
        setRecurrence(controls.recurrence);
    }

    [[nodiscard]] wb::Controls load() const noexcept {
        wb::Controls result{};
        std::array<double, kContinuousControlCount> values{};
        for (std::size_t index = 0U; index < values.size(); ++index) {
            values[index] = continuous_[index].load(std::memory_order_acquire);
        }
        result.external = values[0];
        result.internal = values[1];
        result.anchor = values[2];
        result.field = values[3];
        result.wander = values[4];
        result.mutation = values[5];
        result.fragment = values[6];
        result.energy = values[7];
        result.body = values[8];
        result.structure = values[9];
        result.brightness = values[10];
        result.damping = values[11];
        result.position = values[12];
        result.dry = values[13];
        result.memory = values[14];
        result.motion = static_cast<wb::MotionMode>(motion_.load(std::memory_order_acquire));
        result.recurrence = static_cast<wb::RecurrenceMode>(
            recurrence_.load(std::memory_order_acquire));
        return result;
    }

private:
    std::array<std::atomic<double>, kContinuousControlCount> continuous_{};
    std::atomic<std::uint8_t> motion_{static_cast<std::uint8_t>(wb::MotionMode::hover)};
    std::atomic<std::uint8_t> recurrence_{
        static_cast<std::uint8_t>(wb::RecurrenceMode::fresh)};
};

class InstrumentAudioEngine final : public juce::AudioIODeviceCallback {
public:
    InstrumentAudioEngine() = default;
    ~InstrumentAudioEngine() override { stop(); }

    [[nodiscard]] juce::AudioDeviceManager& deviceManager() noexcept {
        return device_manager_;
    }

    void setContinuous(std::size_t index, double value) noexcept {
        controls_.setContinuous(index, value);
    }

    void setMotion(wb::MotionMode value) noexcept { controls_.setMotion(value); }
    void setRecurrence(wb::RecurrenceMode value) noexcept { controls_.setRecurrence(value); }

    void triggerFreeze() noexcept { freeze_.fetch_add(1U, std::memory_order_acq_rel); }
    void triggerClear() noexcept { clear_.fetch_add(1U, std::memory_order_acq_rel); }
    void triggerReset() noexcept { reset_.fetch_add(1U, std::memory_order_acq_rel); }
    void triggerPanic() noexcept { panic_.fetch_add(1U, std::memory_order_acq_rel); }

    [[nodiscard]] juce::String start() {
        stop();
        auto error = device_manager_.initialiseWithDefaultDevices(2, 2);
        if (error.isNotEmpty()) return "Audio input/output unavailable: " + error;
        auto* device = device_manager_.getCurrentAudioDevice();
        if (device == nullptr
            || device->getCurrentSampleRate() < 8000.0
            || device->getCurrentSampleRate() > 192000.0
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples() > static_cast<int>(wb::kMaximumBlockFrames)) {
            device_manager_.closeAudioDevice();
            return "Wanderbody requires 8-192 kHz and blocks no larger than 2048 frames";
        }
        device_manager_.addAudioCallback(this);
        return ready_.load(std::memory_order_acquire)
            ? "Audio active: " + device->getName()
            : "The audio callback did not accept the selected configuration";
    }

    void stop() {
        device_manager_.removeAudioCallback(this);
        device_manager_.closeAudioDevice();
        ready_.store(false, std::memory_order_release);
    }

    [[nodiscard]] bool ready() const noexcept {
        return ready_.load(std::memory_order_acquire);
    }

    [[nodiscard]] bool popLatestSnapshot(wb::Snapshot& snapshot) noexcept {
        return snapshots_.popLatest(snapshot);
    }

    [[nodiscard]] std::uint64_t snapshotDropCount() const noexcept {
        return snapshot_drop_count_.load(std::memory_order_acquire);
    }

    [[nodiscard]] double cpuUsage() const noexcept { return device_manager_.getCpuUsage(); }
    [[nodiscard]] int xrunCount() const noexcept { return device_manager_.getXRunCount(); }

    void audioDeviceAboutToStart(juce::AudioIODevice* device) override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
        audio_actions_ = {};
        if (device == nullptr
            || device->getCurrentSampleRate() < 8000.0
            || device->getCurrentSampleRate() > 192000.0
            || device->getCurrentBufferSizeSamples() < 1
            || device->getCurrentBufferSizeSamples() > static_cast<int>(wb::kMaximumBlockFrames)) {
            return;
        }
        auto core = std::make_unique<wb::Core>();
        if (!core->prepare(device->getCurrentSampleRate(), wb::kMaximumBlockFrames)) return;
        core_ = std::move(core);
        publishSnapshot();
        ready_.store(true, std::memory_order_release);
    }

    void audioDeviceStopped() override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
    }

    void audioDeviceIOCallbackWithContext(
        const float* const* input_channels,
        int input_channel_count,
        float* const* output_channels,
        int output_channel_count,
        int frames,
        const juce::AudioIODeviceCallbackContext&) override {
        clearOutputs(output_channels, output_channel_count, frames);
        if (!ready() || core_ == nullptr || output_channels == nullptr
            || output_channel_count < 2 || output_channels[0] == nullptr
            || output_channels[1] == nullptr || frames < 1
            || frames > static_cast<int>(wb::kMaximumBlockFrames)) {
            return;
        }
        const auto actions = loadActions();
        const bool reset_requested = actions.reset > audio_actions_.reset;
        const float* input_left = input_channels != nullptr && input_channel_count > 0
            ? input_channels[0] : nullptr;
        const float* input_right = input_channels != nullptr && input_channel_count > 1
            ? input_channels[1] : nullptr;
        const auto report = core_->process(
            controls_.load(),
            actions,
            input_left,
            input_right,
            output_channels[0],
            output_channels[1],
            static_cast<std::uint32_t>(frames));
        audio_actions_ = actions;
        if (report.diagnostic != wb::DiagnosticCode::none) {
            clearOutputs(output_channels, output_channel_count, frames);
        }
        const auto accepted = core_->snapshot();
        if (reset_requested) controls_.store(accepted.accepted_controls);
        publishSnapshot(accepted);
    }

private:
    static void clearOutputs(float* const* outputs, int channels, int frames) noexcept {
        if (outputs == nullptr || frames <= 0) return;
        for (int channel = 0; channel < channels; ++channel) {
            if (outputs[channel] != nullptr) std::fill_n(outputs[channel], frames, 0.0F);
        }
    }

    [[nodiscard]] wb::ActionSequences loadActions() const noexcept {
        wb::ActionSequences result{};
        result.freeze = freeze_.load(std::memory_order_acquire);
        result.clear = clear_.load(std::memory_order_acquire);
        result.reset = reset_.load(std::memory_order_acquire);
        result.panic = panic_.load(std::memory_order_acquire);
        return result;
    }

    void publishSnapshot() noexcept {
        publishSnapshot(core_ == nullptr ? wb::Snapshot{} : core_->snapshot());
    }

    void publishSnapshot(const wb::Snapshot& snapshot) noexcept {
        if (!snapshots_.push(snapshot)) {
            snapshot_drop_count_.fetch_add(1U, std::memory_order_relaxed);
        }
    }

    juce::AudioDeviceManager device_manager_{};
    std::unique_ptr<wb::Core> core_{};
    AtomicControls controls_{};
    wb::ActionSequences audio_actions_{};
    SpscQueue<wb::Snapshot, 8U> snapshots_{};
    std::atomic<bool> ready_{false};
    std::atomic<std::uint64_t> freeze_{0U};
    std::atomic<std::uint64_t> clear_{0U};
    std::atomic<std::uint64_t> reset_{0U};
    std::atomic<std::uint64_t> panic_{0U};
    std::atomic<std::uint64_t> snapshot_drop_count_{0U};
};

class MemoryView final : public juce::Component {
public:
    void setSnapshot(const wb::Snapshot& snapshot) {
        snapshot_ = snapshot;
        repaint();
    }

    void paint(juce::Graphics& graphics) override {
        const auto bounds = getLocalBounds().toFloat().reduced(1.0F);
        graphics.setColour(juce::Colour(0xff111820));
        graphics.fillRoundedRectangle(bounds, 10.0F);
        graphics.setColour(juce::Colour(0xff33414d));
        graphics.drawRoundedRectangle(bounds, 10.0F, 1.0F);
        auto graph = bounds.reduced(16.0F, 28.0F);
        const float center = graph.getCentreY();
        juce::Path path;
        for (std::size_t index = 0U; index < snapshot_.capture_scope.size(); ++index) {
            const float x = graph.getX() + graph.getWidth()
                * static_cast<float>(index) / static_cast<float>(snapshot_.capture_scope.size() - 1U);
            const float y = center - snapshot_.capture_scope[index] * graph.getHeight() * 0.42F;
            if (index == 0U) path.startNewSubPath(x, y);
            else path.lineTo(x, y);
        }
        graphics.setColour(juce::Colour(0xff62d7c5));
        graphics.strokePath(path, juce::PathStrokeType(1.5F));

        const auto& controls = snapshot_.accepted_controls;
        const float field = static_cast<float>(0.01 + 0.47 * controls.field);
        const float anchor = static_cast<float>(controls.anchor);
        const float left = graph.getX() + graph.getWidth() * std::clamp(anchor - field, 0.0F, 1.0F);
        const float right = graph.getX() + graph.getWidth() * std::clamp(anchor + field, 0.0F, 1.0F);
        graphics.setColour(juce::Colour(0x335ac9b8));
        graphics.fillRect(juce::Rectangle<float>(left, graph.getY(), right - left, graph.getHeight()));
        graphics.setColour(juce::Colour(0xffffca6a));
        graphics.drawVerticalLine(
            static_cast<int>(graph.getX() + graph.getWidth() * anchor),
            graph.getY(),
            graph.getBottom());
        graphics.setColour(juce::Colour(0xffe9f0f4));
        for (std::size_t index = 0U; index < snapshot_.active_head_positions.size(); ++index) {
            if (index >= snapshot_.active_voice_count) break;
            const float x = graph.getX() + graph.getWidth()
                * static_cast<float>(snapshot_.active_head_positions[index]);
            graphics.fillEllipse(x - 3.0F, graph.getBottom() - 7.0F, 6.0F, 6.0F);
        }
        graphics.setFont(13.0F);
        graphics.drawText(
            "RECENT MEMORY  " + juce::String(snapshot_.capture_valid_frames) + " frames",
            bounds.toNearestInt().removeFromTop(24).reduced(12, 0),
            juce::Justification::centredLeft);
    }

private:
    wb::Snapshot snapshot_{};
};

class MainComponent final
    : public juce::Component,
      private juce::Timer,
      private juce::Slider::Listener,
      private juce::ComboBox::Listener,
      private juce::Button::Listener {
public:
    MainComponent()
        : device_selector_(engine_.deviceManager(), 0, 2, 0, 2, true, false, true, false) {
        const auto defaults = wb::defaultControls();
        const std::array<double, kContinuousControlCount> values{{
            defaults.external, defaults.internal, defaults.anchor, defaults.field,
            defaults.wander, defaults.mutation, defaults.fragment, defaults.energy,
            defaults.body, defaults.structure, defaults.brightness, defaults.damping,
            defaults.position, defaults.dry, defaults.memory,
        }};
        const auto& descriptors = wb::controlDescriptors();
        for (std::size_t index = 0U; index < sliders_.size(); ++index) {
            auto& slider = sliders_[index];
            slider.setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            slider.setTextBoxStyle(juce::Slider::TextBoxBelow, false, 66, 18);
            slider.setRange(0.0, 1.0, 0.001);
            slider.setValue(values[index], juce::dontSendNotification);
            const auto label = std::string(descriptors[descriptorIndex(index)].label);
            slider.setName(juce::String(label));
            slider.addListener(this);
            addAndMakeVisible(slider);
            labels_[index].setText(juce::String(label), juce::dontSendNotification);
            labels_[index].setJustificationType(juce::Justification::centred);
            labels_[index].setInterceptsMouseClicks(false, false);
            addAndMakeVisible(labels_[index]);
        }

        motion_.addItem("Hover", 1);
        motion_.addItem("Drunk", 2);
        motion_.setSelectedId(1, juce::dontSendNotification);
        motion_.addListener(this);
        recurrence_.addItem("Fresh", 1);
        recurrence_.addItem("Locked", 2);
        recurrence_.addItem("Shuffled", 3);
        recurrence_.addItem("Mutated", 4);
        recurrence_.setSelectedId(1, juce::dontSendNotification);
        recurrence_.addListener(this);
        addAndMakeVisible(motion_);
        addAndMakeVisible(recurrence_);

        configureButton(start_, "Start Audio");
        configureButton(freeze_, "Freeze");
        configureButton(clear_, "Clear");
        configureButton(reset_, "Reset");
        configureButton(panic_, "Panic");
        addAndMakeVisible(memory_);
        addAndMakeVisible(device_selector_);
        status_.setColour(juce::Label::textColourId, juce::Colour(0xffb7c5cf));
        status_.setJustificationType(juce::Justification::centredLeft);
        status_.setText(
            "Stopped. Audio and MIDI endpoints are untouched until Start Audio or device settings are used.",
            juce::dontSendNotification);
        addAndMakeVisible(status_);
        setSize(1260, 820);
        startTimerHz(kUiTimerHz);
    }

    ~MainComponent() override {
        stopTimer();
        for (auto& slider : sliders_) slider.removeListener(this);
        motion_.removeListener(this);
        recurrence_.removeListener(this);
        for (auto* button : {&start_, &freeze_, &clear_, &reset_, &panic_}) {
            button->removeListener(this);
        }
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour(0xff0b1015));
        graphics.setColour(juce::Colour(0xffedf4f7));
        graphics.setFont(juce::FontOptions(28.0F, juce::Font::bold));
        graphics.drawText("WANDERBODY 0.1", 22, 12, 430, 36, juce::Justification::centredLeft);
        graphics.setColour(juce::Colour(0xff738795));
        graphics.setFont(13.0F);
        graphics.drawText(
            "hover · wander · remember · embody   |   noncanonical standalone prototype",
            24, 47, 720, 22, juce::Justification::centredLeft);
        graphics.drawVerticalLine(895, 82.0F, static_cast<float>(getHeight() - 18));
        graphics.drawText("DEVICE SETTINGS", 915, 52, 300, 22, juce::Justification::centredLeft);
    }

    void resized() override {
        auto left = getLocalBounds().withTrimmedTop(78).withTrimmedRight(365).reduced(18, 0);
        auto transport = left.removeFromTop(34);
        start_.setBounds(transport.removeFromLeft(118));
        transport.removeFromLeft(8);
        freeze_.setBounds(transport.removeFromLeft(92));
        transport.removeFromLeft(6);
        clear_.setBounds(transport.removeFromLeft(82));
        transport.removeFromLeft(6);
        reset_.setBounds(transport.removeFromLeft(82));
        transport.removeFromLeft(6);
        panic_.setBounds(transport.removeFromLeft(82));
        motion_.setBounds(transport.removeFromLeft(112).reduced(4, 0));
        recurrence_.setBounds(transport.removeFromLeft(132).reduced(4, 0));
        left.removeFromTop(10);
        memory_.setBounds(left.removeFromTop(180));
        left.removeFromTop(8);
        status_.setBounds(left.removeFromTop(36));
        left.removeFromTop(4);
        const int columns = 5;
        const int rows = 3;
        const int cell_width = left.getWidth() / columns;
        const int cell_height = left.getHeight() / rows;
        for (std::size_t index = 0U; index < sliders_.size(); ++index) {
            const int column = static_cast<int>(index % static_cast<std::size_t>(columns));
            const int row = static_cast<int>(index / static_cast<std::size_t>(columns));
            auto cell = juce::Rectangle<int>(
                left.getX() + column * cell_width,
                left.getY() + row * cell_height,
                cell_width,
                cell_height).reduced(4);
            labels_[index].setBounds(cell.removeFromTop(20));
            sliders_[index].setBounds(cell);
        }
        device_selector_.setBounds(juce::Rectangle<int>(910, 78, 330, getHeight() - 96));
    }

private:
    static constexpr std::size_t descriptorIndex(std::size_t continuous_index) noexcept {
        return kDescriptorIndices[continuous_index];
    }

    void configureButton(juce::TextButton& button, const juce::String& text) {
        button.setButtonText(text);
        button.addListener(this);
        addAndMakeVisible(button);
    }

    void sliderValueChanged(juce::Slider* changed) override {
        for (std::size_t index = 0U; index < sliders_.size(); ++index) {
            if (changed == &sliders_[index]) {
                engine_.setContinuous(index, changed->getValue());
                return;
            }
        }
    }

    void comboBoxChanged(juce::ComboBox* changed) override {
        if (changed == &motion_) {
            engine_.setMotion(motion_.getSelectedId() == 2
                ? wb::MotionMode::drunk : wb::MotionMode::hover);
        } else if (changed == &recurrence_) {
            engine_.setRecurrence(static_cast<wb::RecurrenceMode>(
                std::clamp(recurrence_.getSelectedId() - 1, 0, 3)));
        }
    }

    void buttonClicked(juce::Button* changed) override {
        if (changed == &start_) {
            if (engine_.ready()) {
                engine_.stop();
                start_.setButtonText("Start Audio");
                status_.setText("Audio stopped", juce::dontSendNotification);
            } else {
                const auto result = engine_.start();
                start_.setButtonText(engine_.ready() ? "Stop Audio" : "Start Audio");
                status_.setText(result, juce::dontSendNotification);
            }
        } else if (changed == &freeze_) {
            engine_.triggerFreeze();
        } else if (changed == &clear_) {
            engine_.triggerClear();
        } else if (changed == &reset_) {
            engine_.triggerReset();
        } else if (changed == &panic_) {
            engine_.triggerPanic();
        }
    }

    void timerCallback() override {
        wb::Snapshot snapshot{};
        if (engine_.popLatestSnapshot(snapshot)) {
            latest_ = snapshot;
            syncAcceptedState();
        }
        if (engine_.ready()) {
            status_.setText(
                "accepted: " + juce::String(wb::motionName(latest_.motion))
                + " / " + wb::recurrenceName(latest_.recurrence)
                + "  | history " + juce::String(latest_.history_count)
                + "  | voices " + juce::String(latest_.active_voice_count)
                + "  | decisions " + juce::String(latest_.diagnostics.decision_count)
                + "  | xruns " + juce::String(engine_.xrunCount())
                + "  | cpu " + juce::String(engine_.cpuUsage() * 100.0, 1) + "%"
                + "  | snapshot drops " + juce::String(engine_.snapshotDropCount()),
                juce::dontSendNotification);
        }
    }

    void syncAcceptedState() {
        const auto& controls = latest_.accepted_controls;
        const std::array<double, kContinuousControlCount> values{{
            controls.external, controls.internal, controls.anchor, controls.field,
            controls.wander, controls.mutation, controls.fragment, controls.energy,
            controls.body, controls.structure, controls.brightness, controls.damping,
            controls.position, controls.dry, controls.memory,
        }};
        for (std::size_t index = 0U; index < sliders_.size(); ++index) {
            sliders_[index].setValue(values[index], juce::dontSendNotification);
        }
        motion_.setSelectedId(
            controls.motion == wb::MotionMode::drunk ? 2 : 1,
            juce::dontSendNotification);
        recurrence_.setSelectedId(
            static_cast<int>(controls.recurrence) + 1,
            juce::dontSendNotification);
        freeze_.setButtonText(latest_.frozen ? "Unfreeze" : "Freeze");
        memory_.setSnapshot(latest_);
    }

    InstrumentAudioEngine engine_{};
    juce::AudioDeviceSelectorComponent device_selector_;
    std::array<juce::Slider, kContinuousControlCount> sliders_{};
    std::array<juce::Label, kContinuousControlCount> labels_{};
    juce::ComboBox motion_{};
    juce::ComboBox recurrence_{};
    juce::TextButton start_{};
    juce::TextButton freeze_{};
    juce::TextButton clear_{};
    juce::TextButton reset_{};
    juce::TextButton panic_{};
    juce::Label status_{};
    MemoryView memory_{};
    wb::Snapshot latest_{};
};

class WanderbodyApplication final : public juce::JUCEApplication {
public:
    [[nodiscard]] const juce::String getApplicationName() override { return "Wanderbody 0.1"; }
    [[nodiscard]] const juce::String getApplicationVersion() override { return "0.1"; }
    [[nodiscard]] bool moreThanOneInstanceAllowed() override { return false; }

    void initialise(const juce::String&) override {
        window_ = std::make_unique<MainWindow>(getApplicationName());
    }

    void shutdown() override { window_.reset(); }
    void systemRequestedQuit() override { quit(); }
    void anotherInstanceStarted(const juce::String&) override {}

private:
    class MainWindow final : public juce::DocumentWindow {
    public:
        explicit MainWindow(const juce::String& title)
            : juce::DocumentWindow(
                title,
                juce::Colour(0xff0b1015),
                juce::DocumentWindow::allButtons) {
            setUsingNativeTitleBar(true);
            setContentOwned(new MainComponent(), true);
            setResizable(true, true);
            centreWithSize(getWidth(), getHeight());
            setVisible(true);
        }

        void closeButtonPressed() override {
            juce::JUCEApplication::getInstance()->systemRequestedQuit();
        }
    };

    std::unique_ptr<MainWindow> window_{};
};

}  // namespace

START_JUCE_APPLICATION(WanderbodyApplication)
