#include "tidepit/vst3_processor.hpp"

#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <memory>

namespace tidepit {
namespace {

juce::String juceString(std::string_view text)
{
    return juce::String::fromUTF8(text.data(), static_cast<int>(text.size()));
}

constexpr std::array<ControlId, 7U> kButtonControls{{
    ControlId::source_next,
    ControlId::mutate,
    ControlId::lock_toggle,
    ControlId::capture_toggle,
    ControlId::effect_next,
    ControlId::target_next,
    ControlId::scale_next,
}};

[[nodiscard]] float acceptedControlValue(
    std::size_t index,
    const Snapshot& snapshot) noexcept {
    if (index < 4U) return snapshot.controls.stages[index];
    switch (index) {
        case kVst3RateIndex: return snapshot.controls.rate;
        case kVst3MemoryIndex: return snapshot.controls.memory;
        case kVst3MaterialIndex: return snapshot.controls.material;
        case kVst3PositionIndex: return snapshot.controls.position;
        case kVst3FxAIndex: return snapshot.effective_fx_a;
        case kVst3FxBIndex: return snapshot.effective_fx_b;
        case kVst3RootIndex: return static_cast<float>(snapshot.controls.root_note);
        default: return 0.0F;
    }
}

[[nodiscard]] std::size_t parameterForButton(ControlId id) noexcept {
    switch (id) {
        case ControlId::source_next: return kVst3SourceIndex;
        case ControlId::lock_toggle: return kVst3LockIndex;
        case ControlId::effect_next: return kVst3EffectIndex;
        case ControlId::target_next: return kVst3TargetIndex;
        case ControlId::scale_next: return kVst3ScaleIndex;
        default: return kVst3ParameterCount;
    }
}

class ScopeComponent final : public juce::Component {
public:
    ScopeComponent() {
        setName("Tide Pit stereo output oscilloscope");
        setInterceptsMouseClicks(false, false);
    }

    void setFrame(const ScopeFrame& frame) {
        if (frame.generation == frame_.generation) return;
        frame_ = frame;
        repaint();
    }

    void paint(juce::Graphics& graphics) override {
        const auto bounds = getLocalBounds().toFloat();
        graphics.setColour(juce::Colour{0xff181d1f});
        graphics.fillRect(bounds);
        graphics.setColour(juce::Colour{0xff3a4448});
        graphics.drawRect(bounds.reduced(0.5F), 1.0F);

        auto header = bounds.reduced(8.0F, 4.0F).removeFromTop(18.0F);
        graphics.setFont(juce::FontOptions{11.0F, juce::Font::bold});
        graphics.setColour(juce::Colour{0xffd9dee1});
        graphics.drawText(
            "STEREO OUTPUT SCOPE",
            header,
            juce::Justification::centredLeft);
        if (frame_.sample_count > 1U) {
            graphics.setColour(juce::Colour{0xff89969c});
            graphics.drawText(
                "L " + peakText(frame_.peak_left)
                    + "   R " + peakText(frame_.peak_right),
                header,
                juce::Justification::centredRight);
        }

        auto plot = bounds.reduced(8.0F, 5.0F);
        plot.removeFromTop(20.0F);
        graphics.setColour(juce::Colour{0xff2c3437});
        graphics.drawHorizontalLine(
            juce::roundToInt(plot.getCentreY()), plot.getX(), plot.getRight());
        if (frame_.sample_count < 2U) {
            graphics.setColour(juce::Colour{0xff687177});
            graphics.drawText(
                "waiting for supported host audio",
                plot,
                juce::Justification::centred);
            return;
        }
        drawWaveform(graphics, plot, frame_.left, juce::Colour{0xffe7b75b});
        drawWaveform(graphics, plot, frame_.right, juce::Colour{0xff6fa9bd});
    }

private:
    [[nodiscard]] static juce::String peakText(float peak) {
        return peak <= 0.000001F
            ? juce::String{"-inf dB"}
            : juce::String{20.0F * std::log10(peak), 1} + " dB";
    }

    void drawWaveform(
        juce::Graphics& graphics,
        juce::Rectangle<float> plot,
        const std::array<float, kScopeFrameSamples>& samples,
        juce::Colour colour) const {
        juce::Path path;
        const auto pixel_width = std::max(2, juce::roundToInt(plot.getWidth()));
        for (int pixel = 0; pixel < pixel_width; ++pixel) {
            const auto normalized = static_cast<float>(pixel)
                / static_cast<float>(pixel_width - 1);
            const auto index = std::min(
                frame_.sample_count - 1U,
                static_cast<std::size_t>(normalized
                    * static_cast<float>(frame_.sample_count - 1U)));
            const auto x = plot.getX() + normalized * plot.getWidth();
            const auto y = plot.getCentreY()
                - std::clamp(samples[index], -1.0F, 1.0F)
                    * plot.getHeight() * 0.46F;
            if (pixel == 0) path.startNewSubPath(x, y);
            else path.lineTo(x, y);
        }
        graphics.setColour(colour.withAlpha(0.86F));
        graphics.strokePath(path, juce::PathStrokeType{1.25F});
    }

    ScopeFrame frame_{};
};

class TidePitVst3Editor final
    : public juce::AudioProcessorEditor,
      private juce::Timer {
public:
    explicit TidePitVst3Editor(Vst3Processor& processor)
        : juce::AudioProcessorEditor(processor), processor_(processor) {
        title_.setText("TIDE PIT", juce::dontSendNotification);
        title_.setFont(juce::FontOptions{24.0F, juce::Font::bold});
        title_.setColour(juce::Label::textColourId, juce::Colour{0xffe7b75b});
        addAndMakeVisible(title_);

        subtitle_.setText(
            "exact 48 kHz / 16-frame Core | internal host SRC | accepted-state view",
            juce::dontSendNotification);
        subtitle_.setColour(
            juce::Label::textColourId, juce::Colour{0xff9ca7ad});
        addAndMakeVisible(subtitle_);

        status_.setColour(
            juce::Label::textColourId, juce::Colour{0xff89a2b2});
        status_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(status_);

        mode_state_.setColour(
            juce::Label::textColourId, juce::Colour{0xffe7b75b});
        mode_state_.setFont(juce::FontOptions{13.0F, juce::Font::bold});
        addAndMakeVisible(mode_state_);
        for (auto& line : display_lines_) {
            line.setColour(
                juce::Label::textColourId, juce::Colour{0xffd7ddd9});
            line.setColour(
                juce::Label::backgroundColourId, juce::Colour{0xff181d1f});
            line.setFont(juce::FontOptions{
                juce::Font::getDefaultMonospacedFontName(),
                14.0F,
                juce::Font::plain});
            line.setJustificationType(juce::Justification::centredLeft);
            addAndMakeVisible(line);
        }
        addAndMakeVisible(scope_);

        const auto& descriptors = vst3ParameterDescriptors();
        for (std::size_t index = 0; index < knobs_.size(); ++index) {
            auto slider = std::make_unique<juce::Slider>();
            slider->setName(juceString(descriptors[index].name));
            slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
            slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, 62, 18);
            slider->setRange(
                descriptors[index].minimum,
                descriptors[index].maximum,
                descriptors[index].step_count > 1U ? 1.0 : 0.001);
            slider->setValue(
                descriptors[index].default_physical,
                juce::dontSendNotification);
            slider->setDoubleClickReturnValue(
                true, descriptors[index].default_physical);
            slider->setColour(
                juce::Slider::rotarySliderFillColourId,
                juce::Colour{0xffe7b75b});
            slider->setColour(
                juce::Slider::rotarySliderOutlineColourId,
                juce::Colour{0xff394247});
            slider->setColour(
                juce::Slider::textBoxTextColourId,
                juce::Colour{0xffedf1f2});
            slider->setColour(
                juce::Slider::textBoxBackgroundColourId,
                juce::Colour{0xff15191b});
            slider->onDragStart = [this, index] {
                processor_.beginParameterGesture(index);
            };
            slider->onValueChange = [this, index] {
                processor_.setParameterPhysical(
                    index,
                    static_cast<float>(knobs_[index]->getValue()),
                    true);
            };
            slider->onDragEnd = [this, index] {
                processor_.endParameterGesture(index);
            };
            addAndMakeVisible(*slider);
            knobs_[index] = std::move(slider);

            auto label = std::make_unique<juce::Label>();
            label->setText(
                juceString(descriptors[index].name), juce::dontSendNotification);
            label->setJustificationType(juce::Justification::centred);
            label->setColour(
                juce::Label::textColourId, juce::Colour{0xffd9dee1});
            label->setFont(juce::FontOptions{11.0F, juce::Font::bold});
            addAndMakeVisible(*label);
            knob_labels_[index] = std::move(label);
        }

        for (std::size_t index = 0; index < buttons_.size(); ++index) {
            const auto descriptor = buttonDescriptors()[index];
            auto button = std::make_unique<juce::TextButton>(
                juceString(descriptor.label));
            button->setColour(
                juce::TextButton::buttonColourId, juce::Colour{0xff293135});
            button->setColour(
                juce::TextButton::buttonOnColourId, juce::Colour{0xffe7b75b});
            button->setColour(
                juce::TextButton::textColourOffId, juce::Colour{0xffedf1f2});
            button->setColour(
                juce::TextButton::textColourOnId, juce::Colour{0xff15191b});
            button->setClickingTogglesState(false);
            button->onClick = [this, index] { activateButton(index); };
            addAndMakeVisible(*button);
            buttons_[index] = std::move(button);
        }

        updateFromProcessor();
        startTimerHz(30);
        setSize(1080, 650);
    }

    ~TidePitVst3Editor() override { stopTimer(); }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff111516});
        graphics.setColour(juce::Colour{0xff30383c});
        graphics.drawLine(
            16.0F, 55.0F, static_cast<float>(getWidth() - 16), 55.0F, 1.0F);
        graphics.drawRect(getLocalBounds().toFloat().reduced(8.5F), 1.0F);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(18);
        auto header = area.removeFromTop(38);
        title_.setBounds(header.removeFromLeft(170));
        status_.setBounds(header.removeFromRight(570));
        subtitle_.setBounds(header);
        area.removeFromTop(8);

        mode_state_.setBounds(area.removeFromTop(24));
        auto monitor = area.removeFromTop(116);
        auto display = monitor.removeFromLeft(410).reduced(3, 1);
        for (auto& line : display_lines_) {
            line.setBounds(display.removeFromTop(28));
        }
        monitor.removeFromLeft(8);
        scope_.setBounds(monitor);
        area.removeFromTop(8);

        constexpr int row_height = 136;
        for (std::size_t row = 0; row < 2U; ++row) {
            auto row_area = area.removeFromTop(row_height);
            for (std::size_t column = 0; column < 8U; ++column) {
                const auto index = row * 8U + column;
                if (index >= knobs_.size()) break;
                const auto columns_left = static_cast<int>(8U - column);
                auto cell = row_area.removeFromLeft(
                    row_area.getWidth() / columns_left).reduced(4, 0);
                knob_labels_[index]->setBounds(cell.removeFromTop(20));
                knobs_[index]->setBounds(cell);
            }
        }
        area.removeFromTop(8);
        auto button_row = area.removeFromTop(66);
        for (std::size_t index = 0; index < buttons_.size(); ++index) {
            const auto left = static_cast<int>(buttons_.size() - index);
            buttons_[index]->setBounds(
                button_row.removeFromLeft(button_row.getWidth() / left).reduced(4));
        }
    }

private:
    void timerCallback() override { updateFromProcessor(); }

    void activateButton(std::size_t index) {
        if (index >= kButtonControls.size()) return;
        const auto id = kButtonControls[index];
        if (id == ControlId::mutate) {
            processor_.requestAction(SemanticAction::mutate);
            return;
        }
        if (id == ControlId::capture_toggle) {
            processor_.requestAction(SemanticAction::capture_toggle);
            return;
        }
        const auto parameter = parameterForButton(id);
        if (parameter >= kVst3ParameterCount) return;
        const auto& descriptor = vst3ParameterDescriptors()[parameter];
        const auto current = static_cast<int>(std::lround(
            processor_.parameterPhysical(parameter)));
        const auto count = static_cast<int>(descriptor.step_count);
        const auto next = count > 1 ? (current + 1) % count : current;
        processor_.beginParameterGesture(parameter);
        processor_.setParameterPhysical(
            parameter, static_cast<float>(next), true);
        processor_.endParameterGesture(parameter);
    }

    void updateFromProcessor() {
        const auto frame = processor_.uiFrame();
        const auto& snapshot = frame.snapshot;
        if (frame.core_diagnostics.manual_mutations != last_mutation_count_) {
            last_mutation_count_ = frame.core_diagnostics.manual_mutations;
            mutate_feedback_until_ = juce::Time::getMillisecondCounter() + 500U;
        }

        status_.setText(processor_.statusText(), juce::dontSendNotification);
        mode_state_.setText(
            "SOURCE " + juce::String{sourceName(snapshot.source)}
                + "  |  FX " + juce::String{effectName(snapshot.effect)}
                + "  |  TARGET " + juce::String{targetName(snapshot.target)}
                + "  |  SCALE " + juce::String{scaleName(snapshot.scale)}
                + "  |  STAGE " + juce::String{snapshot.stage + 1U},
            juce::dontSendNotification);
        for (std::size_t line = 0; line < display_lines_.size(); ++line) {
            display_lines_[line].setText(
                juce::String::fromUTF8(
                    snapshot.display_lines[line].data(), 21),
                juce::dontSendNotification);
        }

        for (std::size_t index = 0; index < knobs_.size(); ++index) {
            if (!knobs_[index]->isMouseButtonDown()) {
                knobs_[index]->setValue(
                    acceptedControlValue(index, snapshot),
                    juce::dontSendNotification);
            }
        }

        const bool mutate_feedback =
            juce::Time::getMillisecondCounter() < mutate_feedback_until_;
        for (std::size_t index = 0; index < buttons_.size(); ++index) {
            const auto presentation = buttonPresentation(
                kButtonControls[index], snapshot, mutate_feedback);
            buttons_[index]->setButtonText(
                juceString(presentation.label)
                    + "\n" + juceString(presentation.state));
            buttons_[index]->setToggleState(
                presentation.latched_active, juce::dontSendNotification);
        }
        scope_.setFrame(processor_.latestScope());
    }

    Vst3Processor& processor_;
    juce::Label title_;
    juce::Label subtitle_;
    juce::Label status_;
    juce::Label mode_state_;
    std::array<juce::Label, 4U> display_lines_{};
    ScopeComponent scope_;
    std::array<std::unique_ptr<juce::Slider>, 11U> knobs_{};
    std::array<std::unique_ptr<juce::Label>, 11U> knob_labels_{};
    std::array<std::unique_ptr<juce::TextButton>, 7U> buttons_{};
    std::uint64_t last_mutation_count_{};
    std::uint32_t mutate_feedback_until_{};
};

}  // namespace

juce::AudioProcessorEditor* createTidePitVst3Editor(Vst3Processor& processor) {
    return new TidePitVst3Editor{processor};
}

}  // namespace tidepit
