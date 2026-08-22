#include "WirefallR02Core.h"

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <memory>

namespace {

using wirefall::r02::ActionId;
using wirefall::r02::ControlId;

constexpr std::size_t kControlCount = wirefall::r02::kControlDescriptors.size();

class AudioEngine final : public juce::AudioIODeviceCallback {
public:
    AudioEngine() {
        for (const auto& item : wirefall::r02::kControlDescriptors) {
            desired_[static_cast<std::size_t>(item.id)].store(item.default_value, std::memory_order_relaxed);
            accepted_[static_cast<std::size_t>(item.id)].store(item.default_value, std::memory_order_relaxed);
        }
    }

    ~AudioEngine() override {
        manager_.removeAudioCallback(this);
        manager_.closeAudioDevice();
    }

    juce::String start() {
        auto error = manager_.initialiseWithDefaultDevices(0, 2);
        if (error.isNotEmpty()) return "Audio output unavailable: " + error;
        auto setup = manager_.getAudioDeviceSetup();
        setup.sampleRate = 48000.0;
        setup.bufferSize = 128;
        error = manager_.setAudioDeviceSetup(setup, true);
        if (error.isNotEmpty()) {
            manager_.closeAudioDevice();
            return "48 kHz setup unavailable: " + error;
        }
        manager_.addAudioCallback(this);
        return ready_.load(std::memory_order_acquire)
            ? "48 kHz stereo output active"
            : "Audio callback has not accepted the device configuration";
    }

    void setControl(ControlId id, double value) noexcept {
        const auto index = static_cast<std::size_t>(id);
        if (index < desired_.size()) desired_[index].store(value, std::memory_order_release);
    }

    void setOpen(bool held) noexcept {
        desired_open_.store(held, std::memory_order_release);
    }

    void request(ActionId id) noexcept {
        if (id == ActionId::unsupported) return;
        const auto bit = std::uint32_t{1} << static_cast<std::uint32_t>(id);
        requested_actions_.fetch_or(bit, std::memory_order_release);
    }

    [[nodiscard]] double accepted(ControlId id) const noexcept {
        const auto index = static_cast<std::size_t>(id);
        return index < accepted_.size() ? accepted_[index].load(std::memory_order_acquire) : 0.0;
    }

    [[nodiscard]] bool acceptedOpen() const noexcept {
        return accepted_open_.load(std::memory_order_acquire);
    }

    [[nodiscard]] bool acceptedPanic() const noexcept {
        return accepted_panic_.load(std::memory_order_acquire);
    }

    [[nodiscard]] juce::String status() const {
        if (!ready_.load(std::memory_order_acquire)) return "Audio output inactive";
        if (accepted_panic_.load(std::memory_order_acquire)) return "PANIC latched";
        return "ENERGY / BREAK / PULSE / TICK ready";
    }

    void audioDeviceAboutToStart(juce::AudioIODevice* device) override {
        ready_.store(false, std::memory_order_release);
        core_ = std::make_unique<wirefall::r02::Core>();
        if (device == nullptr || !core_->prepare(device->getCurrentSampleRate())) {
            core_.reset();
            return;
        }
        open_applied_ = false;
        publishAccepted();
        ready_.store(true, std::memory_order_release);
    }

    void audioDeviceStopped() override {
        ready_.store(false, std::memory_order_release);
        core_.reset();
    }

    void audioDeviceIOCallbackWithContext(
        const float* const*,
        int,
        float* const* outputs,
        int output_channel_count,
        int frames,
        const juce::AudioIODeviceCallbackContext&
    ) override {
        clear(outputs, output_channel_count, frames);
        if (!ready_.load(std::memory_order_acquire) || core_ == nullptr || outputs == nullptr
            || output_channel_count < 2 || outputs[0] == nullptr || outputs[1] == nullptr
            || frames <= 0) {
            return;
        }
        applyRequestedState();
        int position = 0;
        while (position < frames) {
            const auto count = static_cast<std::uint32_t>(std::min(
                frames - position, static_cast<int>(wirefall::r02::kMaximumBlockFrames)));
            core_->process(left_.data(), right_.data(), count);
            std::copy_n(left_.data(), count, outputs[0] + position);
            std::copy_n(right_.data(), count, outputs[1] + position);
            position += static_cast<int>(count);
        }
        publishAccepted();
    }

private:
    static void clear(float* const* outputs, int channels, int frames) noexcept {
        if (outputs == nullptr || frames <= 0) return;
        for (int channel = 0; channel < channels; ++channel) {
            if (outputs[channel] != nullptr) std::fill_n(outputs[channel], frames, 0.0f);
        }
    }

    void applyRequestedState() noexcept {
        for (const auto& item : wirefall::r02::kControlDescriptors) {
            const auto index = static_cast<std::size_t>(item.id);
            core_->setControlValue(item.id, desired_[index].load(std::memory_order_acquire));
        }
        const bool desired_open = desired_open_.load(std::memory_order_acquire);
        if (desired_open != open_applied_) {
            core_->triggerAction(desired_open ? ActionId::open_press : ActionId::open_release);
            open_applied_ = desired_open;
        }
        auto mask = requested_actions_.exchange(0, std::memory_order_acq_rel);
        for (std::uint32_t raw = 0; raw < static_cast<std::uint32_t>(ActionId::unsupported); ++raw) {
            const auto bit = std::uint32_t{1} << raw;
            if ((mask & bit) != 0) core_->triggerAction(static_cast<ActionId>(raw));
        }
    }

    void publishAccepted() noexcept {
        if (core_ == nullptr) return;
        const auto snapshot = core_->snapshot();
        for (std::size_t index = 0; index < accepted_.size(); ++index) {
            accepted_[index].store(snapshot.accepted_controls[index], std::memory_order_release);
        }
        accepted_open_.store(snapshot.open_held, std::memory_order_release);
        const bool panic_active = snapshot.transition == wirefall::r02::TransitionState::panic_down
            || snapshot.transition == wirefall::r02::TransitionState::panic_latched;
        accepted_panic_.store(panic_active, std::memory_order_release);
    }

    juce::AudioDeviceManager manager_;
    std::unique_ptr<wirefall::r02::Core> core_;
    std::array<float, wirefall::r02::kMaximumBlockFrames> left_{};
    std::array<float, wirefall::r02::kMaximumBlockFrames> right_{};
    std::array<std::atomic<double>, kControlCount> desired_{};
    std::array<std::atomic<double>, kControlCount> accepted_{};
    std::atomic<std::uint32_t> requested_actions_{0};
    std::atomic<bool> desired_open_{false};
    std::atomic<bool> accepted_open_{false};
    std::atomic<bool> accepted_panic_{false};
    std::atomic<bool> ready_{false};
    bool open_applied_{};
};

class MainComponent final : public juce::Component, private juce::Timer {
public:
    MainComponent() {
        title_.setText("WIREFALL 0.2", juce::dontSendNotification);
        title_.setFont(juce::FontOptions(25.0f, juce::Font::bold));
        title_.setColour(juce::Label::textColourId, juce::Colour(0xffef6c4d));
        addAndMakeVisible(title_);
        subtitle_.setText("ENERGY is the instrument. BREAK / PULSE / TICK interrupt it.", juce::dontSendNotification);
        subtitle_.setColour(juce::Label::textColourId, juce::Colour(0xffaeb8c2));
        addAndMakeVisible(subtitle_);

        for (std::size_t index = 0; index < knobs_.size(); ++index) {
            const auto& item = wirefall::r02::kControlDescriptors[index];
            auto slider = std::make_unique<juce::Slider>();
            slider->setName(juce::String(item.name.data(), item.name.size()));
            slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, index == 0 ? 76 : 62, 20);
            slider->setRange(item.minimum, item.maximum, item.stepped ? 1.0 : 0.001);
            slider->setValue(item.default_value, juce::dontSendNotification);
            slider->setDoubleClickReturnValue(true, item.default_value);
            slider->setColour(juce::Slider::rotarySliderFillColourId,
                index == 0 ? juce::Colour(0xffff5b35) : juce::Colour(0xffe0a142));
            slider->setColour(juce::Slider::rotarySliderOutlineColourId, juce::Colour(0xff303a43));
            slider->setColour(juce::Slider::textBoxTextColourId, juce::Colour(0xffe8edf2));
            slider->setColour(juce::Slider::textBoxBackgroundColourId, juce::Colour(0xff151a1e));
            slider->onValueChange = [this, index] {
                engine_.setControl(wirefall::r02::kControlDescriptors[index].id, knobs_[index]->getValue());
            };
            addAndMakeVisible(*slider);
            knobs_[index] = std::move(slider);

            auto label = std::make_unique<juce::Label>();
            label->setText(juce::String(item.name.data(), item.name.size()), juce::dontSendNotification);
            label->setJustificationType(juce::Justification::centred);
            label->setFont(juce::FontOptions(index == 0 ? 15.0f : 12.0f, juce::Font::bold));
            label->setColour(juce::Label::textColourId,
                index == 0 ? juce::Colour(0xffff8a68) : juce::Colour(0xffd3dbe2));
            addAndMakeVisible(*label);
            labels_[index] = std::move(label);
        }

        open_.setButtonText("OPEN");
        open_.onStateChange = [this] { engine_.setOpen(open_.isDown()); };
        tick_preview_.setButtonText("TICK PREVIEW");
        tick_preview_.onClick = [this] { engine_.request(ActionId::tick_preview); };
        downbeat_.setButtonText("DOWNBEAT");
        downbeat_.onClick = [this] { engine_.request(ActionId::downbeat); };
        panic_.setButtonText("PANIC");
        panic_.setClickingTogglesState(true);
        panic_.onClick = [this] {
            engine_.request(panic_.getToggleState() ? ActionId::panic_press : ActionId::panic_release);
        };
        reset_.setButtonText("RESET (encoder hold)");
        reset_.onClick = [this] { engine_.request(ActionId::reset); };
        for (auto* button : {&open_, &tick_preview_, &downbeat_, &panic_, &reset_}) {
            button->setColour(juce::TextButton::buttonColourId, juce::Colour(0xff28323a));
            button->setColour(juce::TextButton::buttonOnColourId, juce::Colour(0xffef6c4d));
            button->setColour(juce::TextButton::textColourOffId, juce::Colour(0xffe8edf2));
            addAndMakeVisible(*button);
        }

        status_.setText(engine_.start(), juce::dontSendNotification);
        status_.setColour(juce::Label::textColourId, juce::Colour(0xff8396a7));
        status_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(status_);
        startTimerHz(20);
        setSize(1120, 650);
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour(0xff101519));
        graphics.setColour(juce::Colour(0xff263038));
        graphics.drawLine(18.0f, 62.0f, static_cast<float>(getWidth() - 18), 62.0f, 1.0f);
        graphics.setColour(juce::Colour(0xffef6c4d).withAlpha(0.16f));
        graphics.fillRoundedRectangle(18.0f, 82.0f, 266.0f, 300.0f, 8.0f);
        graphics.setColour(juce::Colour(0xff36424b));
        graphics.drawRoundedRectangle(getLocalBounds().toFloat().reduced(8.5f), 5.0f, 1.0f);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(20);
        auto header = area.removeFromTop(38);
        title_.setBounds(header.removeFromLeft(210));
        status_.setBounds(header.removeFromRight(310));
        subtitle_.setBounds(header);
        area.removeFromTop(24);

        auto energy_area = area.removeFromLeft(270).reduced(16, 8);
        labels_[0]->setBounds(energy_area.removeFromTop(28));
        knobs_[0]->setBounds(energy_area.removeFromTop(230));
        energy_area.removeFromTop(10);
        open_.setBounds(energy_area.removeFromTop(42));

        area.removeFromLeft(14);
        auto performance = area.removeFromTop(260);
        for (std::size_t index = 1; index <= 3; ++index) {
            const int cells_left = static_cast<int>(4U - index);
            auto cell = performance.removeFromLeft(performance.getWidth() / cells_left).reduced(8);
            labels_[index]->setBounds(cell.removeFromTop(24));
            knobs_[index]->setBounds(cell);
        }
        auto settings = area.removeFromTop(224);
        for (std::size_t index = 4; index < knobs_.size(); ++index) {
            const int cells_left = static_cast<int>(knobs_.size() - index);
            auto cell = settings.removeFromLeft(settings.getWidth() / cells_left).reduced(5);
            labels_[index]->setBounds(cell.removeFromTop(22));
            knobs_[index]->setBounds(cell);
        }
        area.removeFromTop(8);
        auto buttons = area.removeFromTop(48);
        tick_preview_.setBounds(buttons.removeFromLeft(132).reduced(4));
        downbeat_.setBounds(buttons.removeFromLeft(118).reduced(4));
        panic_.setBounds(buttons.removeFromLeft(98).reduced(4));
        reset_.setBounds(buttons.removeFromLeft(176).reduced(4));
    }

private:
    void timerCallback() override {
        for (std::size_t index = 0; index < knobs_.size(); ++index) {
            const auto value = engine_.accepted(wirefall::r02::kControlDescriptors[index].id);
            if (std::abs(knobs_[index]->getValue() - value) > 0.0005) {
                knobs_[index]->setValue(value, juce::dontSendNotification);
            }
        }
        open_.setToggleState(engine_.acceptedOpen(), juce::dontSendNotification);
        panic_.setToggleState(engine_.acceptedPanic(), juce::dontSendNotification);
        status_.setText(engine_.status(), juce::dontSendNotification);
    }

    AudioEngine engine_;
    juce::Label title_;
    juce::Label subtitle_;
    juce::Label status_;
    std::array<std::unique_ptr<juce::Slider>, kControlCount> knobs_;
    std::array<std::unique_ptr<juce::Label>, kControlCount> labels_;
    juce::TextButton open_;
    juce::TextButton tick_preview_;
    juce::TextButton downbeat_;
    juce::TextButton panic_;
    juce::TextButton reset_;
};

class MainWindow final : public juce::DocumentWindow {
public:
    MainWindow()
        : juce::DocumentWindow(
              "Wirefall 0.2",
              juce::Colour(0xff101519),
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

class WirefallApplication final : public juce::JUCEApplication {
public:
    const juce::String getApplicationName() override { return "Wirefall 0.2"; }
    const juce::String getApplicationVersion() override { return "0.2.0"; }
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

START_JUCE_APPLICATION(WirefallApplication)
