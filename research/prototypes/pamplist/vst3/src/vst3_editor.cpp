#include "schuss/pamplist/activity_model.hpp"
#include "schuss/pamplist/vst3_processor.hpp"

#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string_view>

namespace schuss::pamplist {
namespace {

const std::array<juce::Colour, kLaneCount> kLaneColours{{
    juce::Colour{0xffff6b5f},
    juce::Colour{0xffff9f43},
    juce::Colour{0xffffcf56},
    juce::Colour{0xff69d28f},
    juce::Colour{0xff4fc3d7},
    juce::Colour{0xff5f8ff5},
    juce::Colour{0xffa779e9},
}};
constexpr juce::uint32 kGlobalColourArgb = 0xffef78b5;

class PamplistVst3LookAndFeel final : public juce::LookAndFeel_V4 {
public:
    PamplistVst3LookAndFeel() {
        setColour(juce::Slider::textBoxTextColourId, juce::Colour{0xffe8ecf1});
        setColour(juce::Slider::textBoxBackgroundColourId, juce::Colour{0xff151a20});
        setColour(juce::Slider::textBoxOutlineColourId, juce::Colours::transparentBlack);
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
        if (onDragStart) onDragStart();
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
        if (!binary_mouse_down_) return;
        binary_mouse_down_ = false;
        if (onDragEnd) onDragEnd();
    }

private:
    bool binary_presentation_{};
    bool binary_mouse_down_{};
};

class ImpactHistoryComponent final : public juce::Component {
public:
    ImpactHistoryComponent() { setInterceptsMouseClicks(false, false); }

    void pushSnapshot(const Snapshot& snapshot) {
        selected_lane_ = snapshot.accepted.selected_page < kLaneCount
            ? static_cast<int>(snapshot.accepted.selected_page)
            : -1;
        const auto sample = reducer_.reduce(snapshot);
        if (sample.rebased) history_.clear();
        if (sample.frame_count != 0U) history_.push(sample);
        repaint();
    }

    void reset() noexcept {
        reducer_.reset();
        history_.clear();
        selected_lane_ = -1;
    }

    void paint(juce::Graphics& graphics) override {
        auto bounds = getLocalBounds().toFloat();
        graphics.setColour(juce::Colour{0xff121820});
        graphics.fillRoundedRectangle(bounds, 5.0F);
        graphics.setColour(juce::Colour{0xff3a4552});
        graphics.drawRoundedRectangle(bounds.reduced(0.5F), 5.0F, 1.0F);

        auto content = bounds.reduced(10.0F, 6.0F);
        const auto header = content.removeFromTop(18.0F);
        graphics.setFont(juce::FontOptions{11.0F, juce::Font::bold});
        graphics.setColour(juce::Colour{0xffd5dce5});
        graphics.drawText(
            "IMPACT TRAILS  /  9.6 SEC",
            header.toNearestInt(),
            juce::Justification::centredLeft,
            false);
        graphics.setFont(juce::FontOptions{10.0F});
        graphics.setColour(juce::Colour{0xff8492a3});
        graphics.drawText(
            "BRIGHT = ENERGY   SPARK = TRIGGER   PINK = COHESION   LINE = CLEAR",
            header.toNearestInt(),
            juce::Justification::centredRight,
            false);
        content.removeFromTop(3.0F);

        constexpr float label_width = 48.0F;
        auto labels = content.removeFromLeft(label_width);
        auto plot = content;
        const auto row_height = plot.getHeight() / static_cast<float>(kLaneCount);
        for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
            const auto row = juce::Rectangle<float>{
                plot.getX(),
                plot.getY() + static_cast<float>(lane) * row_height,
                plot.getWidth(),
                row_height};
            if (selected_lane_ == static_cast<int>(lane)) {
                graphics.setColour(kLaneColours[lane].withAlpha(0.08F));
                graphics.fillRect(row);
            }
            graphics.setColour(juce::Colour{0xff27313b});
            graphics.drawHorizontalLine(
                juce::roundToInt(row.getBottom()), row.getX(), row.getRight());
            graphics.setColour(kLaneColours[lane].withAlpha(
                selected_lane_ == static_cast<int>(lane) ? 1.0F : 0.72F));
            graphics.setFont(juce::FontOptions{
                10.0F,
                selected_lane_ == static_cast<int>(lane)
                    ? juce::Font::bold
                    : juce::Font::plain});
            graphics.drawText(
                "LANE " + juce::String{static_cast<int>(lane) + 1},
                juce::Rectangle<float>{
                    labels.getX(), row.getY(), labels.getWidth() - 5.0F, row.getHeight()}
                    .toNearestInt(),
                juce::Justification::centredRight,
                false);
        }

        const auto count = history_.size();
        const auto slot_width = plot.getWidth()
            / static_cast<float>(kImpactHistoryCapacity);
        const auto first_slot = kImpactHistoryCapacity - count;
        for (std::size_t index = 0; index < count; ++index) {
            const auto sample = history_.oldest(index);
            const auto x = plot.getX()
                + static_cast<float>(first_slot + index) * slot_width;
            const auto column_width = std::max(1.0F, slot_width + 0.25F);
            if (sample.cohesion_level > 0.0F) {
                graphics.setColour(juce::Colour{kGlobalColourArgb}.withAlpha(
                    0.025F + 0.16F * sample.cohesion_level));
                graphics.fillRect(juce::Rectangle<float>{
                    x, plot.getY(), column_width, plot.getHeight()});
            }
            if (sample.effect_cleared) {
                graphics.setColour(juce::Colour{kGlobalColourArgb}.withAlpha(0.95F));
                graphics.fillRect(juce::Rectangle<float>{
                    x, plot.getY(), 1.5F, plot.getHeight()});
            }
            for (std::size_t lane = 0; lane < kLaneCount; ++lane) {
                const auto level = juce::jlimit(
                    0.0F, 1.0F, sample.lane_levels[lane]);
                const auto row_y = plot.getY()
                    + static_cast<float>(lane) * row_height;
                const auto centre_y = row_y + row_height * 0.5F;
                if (level > 0.0F) {
                    const auto height = std::max(
                        1.0F, level * (row_height - 3.0F));
                    graphics.setColour(kLaneColours[lane].withAlpha(
                        0.18F + 0.78F * level));
                    graphics.fillRect(juce::Rectangle<float>{
                        x, centre_y - height * 0.5F, column_width, height});
                }
                if ((sample.trigger_mask & (1U << lane)) != 0U) {
                    const auto radius = 1.8F + 0.55F * static_cast<float>(
                        std::min<std::uint64_t>(sample.trigger_deltas[lane], 3U));
                    graphics.setColour(kLaneColours[lane].brighter(0.45F));
                    graphics.fillEllipse(
                        x + column_width * 0.5F - radius,
                        centre_y - radius,
                        radius * 2.0F,
                        radius * 2.0F);
                }
            }
        }
    }

private:
    ActivityReducer reducer_{};
    ImpactHistory history_{};
    int selected_lane_{-1};
};

class PamplistVst3Editor final
    : public juce::AudioProcessorEditor,
      private juce::Timer {
public:
    explicit PamplistVst3Editor(Vst3Processor& processor)
        : juce::AudioProcessorEditor(processor), processor_(processor) {
        setLookAndFeel(&look_and_feel_);

        title_.setText("PAMPLIST", juce::dontSendNotification);
        title_.setFont(juce::FontOptions{27.0F, juce::Font::bold});
        title_.setColour(juce::Label::textColourId, juce::Colour{0xffffcf56});
        addAndMakeVisible(title_);
        subtitle_.setText(
            "VST3 / seven independent 24-model voices / page eight is one shared, clearable resonant body",
            juce::dontSendNotification);
        subtitle_.setColour(juce::Label::textColourId, juce::Colour{0xff9ca7b5});
        addAndMakeVisible(subtitle_);
        status_.setColour(juce::Label::textColourId, juce::Colour{0xff91a0b3});
        status_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(status_);

        running_button_.setButtonText("RUN");
        running_button_.setClickingTogglesState(true);
        running_button_.onClick = [this] {
            processor_.beginParameterGesture(kVst3RunParameterIndex);
            processor_.setParameterPhysical(
                kVst3RunParameterIndex,
                running_button_.getToggleState() ? 1.0F : 0.0F);
            processor_.endParameterGesture(kVst3RunParameterIndex);
        };
        addAndMakeVisible(running_button_);

        clear_fx_button_.setButtonText("CLEAR FX");
        clear_fx_button_.setColour(
            juce::TextButton::buttonColourId, juce::Colour{0xff492f4a});
        clear_fx_button_.setColour(
            juce::TextButton::buttonOnColourId, juce::Colour{kGlobalColourArgb});
        clear_fx_button_.setTooltip(
            "Clears only the shared cohesion body's retained tail. Lane clocks, patterns, voices, and dry voice tails continue. Clear is never stored in the Live Set.");
        clear_fx_button_.onClick = [this] {
            processor_.requestClear();
            clear_pending_ = true;
            updateClearFeedback();
        };
        addAndMakeVisible(clear_fx_button_);

        engine_banner_.setFont(juce::FontOptions{13.0F, juce::Font::bold});
        engine_banner_.setColour(
            juce::Label::textColourId, juce::Colour{0xffffcf56});
        engine_banner_.setJustificationType(juce::Justification::centredRight);
        addAndMakeVisible(engine_banner_);

        for (std::size_t page = 0; page < page_buttons_.size(); ++page) {
            auto button = std::make_unique<juce::TextButton>(
                page < kLaneCount
                    ? "LANE " + juce::String{static_cast<int>(page + 1U)}
                    : "GLOBAL");
            button->setColour(
                juce::TextButton::buttonOnColourId,
                page < kLaneCount
                    ? kLaneColours[page]
                    : juce::Colour{kGlobalColourArgb});
            button->setColour(
                juce::TextButton::buttonColourId, juce::Colour{0xff252c35});
            button->onClick = [this, page] {
                processor_.setSelectedPage(static_cast<std::uint8_t>(page));
            };
            addAndMakeVisible(*button);
            page_buttons_[page] = std::move(button);
        }

        voice_mode_button_.setButtonText("VOICE");
        voice_mode_button_.setColour(
            juce::TextButton::buttonColourId, juce::Colour{0xff252c35});
        voice_mode_button_.setColour(
            juce::TextButton::buttonOnColourId, juce::Colour{0xff4fc3d7});
        voice_mode_button_.onClick = [this] {
            processor_.setLaneControlMode(LaneControlMode::voice);
        };
        addAndMakeVisible(voice_mode_button_);
        motion_mode_button_.setButtonText("MOTION");
        motion_mode_button_.setColour(
            juce::TextButton::buttonColourId, juce::Colour{0xff252c35});
        motion_mode_button_.setColour(
            juce::TextButton::buttonOnColourId, juce::Colour{0xffff9f43});
        motion_mode_button_.onClick = [this] {
            processor_.setLaneControlMode(LaneControlMode::motion);
        };
        addAndMakeVisible(motion_mode_button_);

        surface_guide_.setColour(
            juce::Label::textColourId, juce::Colour{0xff9ca7b5});
        surface_guide_.setJustificationType(juce::Justification::centredLeft);
        surface_guide_.setFont(juce::FontOptions{12.0F});
        addAndMakeVisible(surface_guide_);

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

        for (std::size_t column = 0; column < kSurfaceColumnCount; ++column) {
            configureSurfaceSlot(SurfaceRow::top, column);
            configureSurfaceSlot(SurfaceRow::bottom, column);
        }
        addAndMakeVisible(impact_history_);

        const auto initial_snapshot = processor_.acceptedSnapshot();
        projectAcceptedState(initial_snapshot);
        impact_history_.pushSnapshot(initial_snapshot);
        updateEnabledState();
        status_.setText(processor_.statusText(), juce::dontSendNotification);
        startTimerHz(20);
        setResizable(true, true);
        setResizeLimits(1080, 730, 1680, 1040);
        setSize(1280, 800);
    }

    ~PamplistVst3Editor() override {
        endOutstandingGestures();
        setLookAndFeel(nullptr);
    }

    void paint(juce::Graphics& graphics) override {
        graphics.fillAll(juce::Colour{0xff101419});
        graphics.setColour(juce::Colour{0xff2b333d});
        graphics.drawRoundedRectangle(
            getLocalBounds().toFloat().reduced(8.5F), 6.0F, 1.0F);
        graphics.setColour(juce::Colour{0xff202730});
        graphics.fillRoundedRectangle(
            juce::Rectangle<float>{
                18.0F,
                102.0F,
                static_cast<float>(getWidth() - 36),
                static_cast<float>(getHeight() - 126)},
            6.0F);
    }

    void resized() override {
        auto area = getLocalBounds().reduced(18);
        auto header = area.removeFromTop(42);
        title_.setBounds(header.removeFromLeft(180));
        status_.setBounds(header.removeFromRight(std::min(720, header.getWidth())));
        subtitle_.setBounds(header);
        area.removeFromTop(6);

        auto performance = area.removeFromTop(34);
        running_button_.setBounds(performance.removeFromLeft(72));
        performance.removeFromLeft(12);
        clear_fx_button_.setBounds(performance.removeFromLeft(92));
        performance.removeFromLeft(12);
        engine_banner_.setBounds(performance);
        area.removeFromTop(8);

        auto pages = area.removeFromTop(42);
        for (std::size_t page = 0; page < page_buttons_.size(); ++page) {
            const auto remaining = static_cast<int>(page_buttons_.size() - page);
            page_buttons_[page]->setBounds(
                pages.removeFromLeft(pages.getWidth() / remaining).reduced(4));
        }
        area.removeFromTop(5);

        impact_history_.setBounds(area.removeFromTop(145));
        area.removeFromTop(5);

        auto context = area.removeFromTop(32);
        voice_mode_button_.setBounds(context.removeFromLeft(86).reduced(2));
        motion_mode_button_.setBounds(context.removeFromLeft(94).reduced(2));
        context.removeFromLeft(10);
        surface_guide_.setBounds(context);
        area.removeFromTop(5);

        const auto row_height = std::max(180, (area.getHeight() - 5) / 2);
        auto top = area.removeFromTop(std::min(row_height, area.getHeight()));
        top_group_.setBounds(top);
        layoutSurfaceRow(top.reduced(10, 22), top_sliders_, top_labels_);
        if (area.getHeight() > 5) area.removeFromTop(5);
        auto bottom = area;
        bottom_group_.setBounds(bottom);
        layoutSurfaceRow(bottom.reduced(10, 22), bottom_sliders_, bottom_labels_);
    }

private:
    static juce::String text(std::string_view value) {
        return juce::String::fromUTF8(value.data(), static_cast<int>(value.size()));
    }

    static juce::String formatSurfaceValue(
        PresentationKind presentation,
        double value) {
        switch (presentation) {
            case PresentationKind::model: {
                const auto model = static_cast<std::uint8_t>(
                    juce::jlimit(0, 23, juce::roundToInt(value)));
                return juce::String{static_cast<int>(model)}.paddedLeft('0', 2)
                    + " " + juce::String{modelName(model)}.toUpperCase();
            }
            case PresentationKind::note:
                return juce::String{value, std::floor(value) == value ? 0 : 2};
            case PresentationKind::unit_percent:
            case PresentationKind::chance:
            case PresentationKind::depth:
                return juce::String{juce::roundToInt(value * 100.0)} + "%";
            case PresentationKind::signed_percent:
                if (std::abs(value) < 0.0005) return "DIRECT";
                return (value > 0.0 ? "+" : "")
                    + juce::String{juce::roundToInt(value * 100.0)} + "%";
            case PresentationKind::trigger_switch:
                return value >= 0.5 ? "ON" : "OFF";
            case PresentationKind::rate: {
                const auto index = static_cast<std::size_t>(
                    juce::jlimit(0, 15, juce::roundToInt(value)));
                const auto& rate = rateTable()[index];
                return juce::String{static_cast<int>(rate.numerator)} + "/"
                    + juce::String{static_cast<int>(rate.denominator)};
            }
            case PresentationKind::phase:
                return juce::String{juce::roundToInt(value)} + "/127";
            case PresentationKind::shape:
                return juce::String{shapeName(static_cast<Shape>(
                    juce::jlimit(0, 7, juce::roundToInt(value))))}.toUpperCase();
            case PresentationKind::hits:
                return juce::String{juce::roundToInt(value)} + "/16";
            case PresentationKind::rotation:
                return "STEP " + juce::String{juce::roundToInt(value)};
            case PresentationKind::repeat:
                return value < 0.5
                    ? juce::String{"FREE"}
                    : "x" + juce::String{juce::roundToInt(value)};
            case PresentationKind::bpm:
                return juce::String{value, 2} + " BPM";
            case PresentationKind::disabled:
                return "-";
        }
        return "?";
    }

    static void layoutSurfaceRow(
        juce::Rectangle<int> area,
        const std::array<std::unique_ptr<SurfaceSlider>, kSurfaceColumnCount>& sliders,
        const std::array<std::unique_ptr<juce::Label>, kSurfaceColumnCount>& labels) {
        for (std::size_t column = 0; column < kSurfaceColumnCount; ++column) {
            const auto remaining = static_cast<int>(kSurfaceColumnCount - column);
            auto cell = area.removeFromLeft(area.getWidth() / remaining).reduced(5);
            labels[column]->setBounds(cell.removeFromTop(22));
            sliders[column]->setBounds(cell);
        }
    }

    std::optional<std::size_t>& gestureIndex(
        SurfaceRow row,
        std::size_t column) noexcept {
        return row == SurfaceRow::top
            ? top_gesture_indices_[column]
            : bottom_gesture_indices_[column];
    }

    SurfaceSlider& surfaceSlider(SurfaceRow row, std::size_t column) noexcept {
        return *(row == SurfaceRow::top
            ? top_sliders_[column]
            : bottom_sliders_[column]);
    }

    void beginSurfaceGesture(SurfaceRow row, std::size_t column) {
        auto& gesture = gestureIndex(row, column);
        if (gesture.has_value()) return;
        gesture = vst3ParameterIndexForSurface(
            processor_.requestedControls(), row, column);
        if (gesture.has_value()) processor_.beginParameterGesture(*gesture);
    }

    void changeSurfaceValue(SurfaceRow row, std::size_t column) {
        auto& gesture = gestureIndex(row, column);
        const bool one_shot = !gesture.has_value();
        if (one_shot) beginSurfaceGesture(row, column);
        if (gesture.has_value()) {
            processor_.setParameterPhysical(
                *gesture,
                static_cast<float>(surfaceSlider(row, column).getValue()));
        }
        if (one_shot) endSurfaceGesture(row, column);
    }

    void endSurfaceGesture(SurfaceRow row, std::size_t column) {
        auto& gesture = gestureIndex(row, column);
        if (gesture.has_value()) processor_.endParameterGesture(*gesture);
        gesture.reset();
    }

    void endOutstandingGestures() {
        for (std::size_t column = 0; column < kSurfaceColumnCount; ++column) {
            endSurfaceGesture(SurfaceRow::top, column);
            endSurfaceGesture(SurfaceRow::bottom, column);
        }
    }

    void configureSurfaceSlot(SurfaceRow row, std::size_t column) {
        auto& sliders = row == SurfaceRow::top ? top_sliders_ : bottom_sliders_;
        auto& labels = row == SurfaceRow::top ? top_labels_ : bottom_labels_;
        auto slider = std::make_unique<SurfaceSlider>();
        slider->setSliderStyle(juce::Slider::RotaryHorizontalVerticalDrag);
        slider->setTextBoxStyle(juce::Slider::TextBoxBelow, false, 128, 20);
        slider->setRange(0.0, 1.0, 0.001);
        slider->setColour(
            juce::Slider::rotarySliderFillColourId, juce::Colour{0xff4fc3d7});
        slider->onDragStart = [this, row, column] {
            beginSurfaceGesture(row, column);
        };
        slider->onValueChange = [this, row, column] {
            changeSurfaceValue(row, column);
        };
        slider->onDragEnd = [this, row, column] {
            endSurfaceGesture(row, column);
        };
        addAndMakeVisible(*slider);
        sliders[column] = std::move(slider);

        auto label = std::make_unique<juce::Label>();
        label->setText("-", juce::dontSendNotification);
        label->setJustificationType(juce::Justification::centred);
        label->setFont(juce::FontOptions{11.0F, juce::Font::bold});
        label->setColour(juce::Label::textColourId, juce::Colour{0xffc7ced7});
        addAndMakeVisible(*label);
        labels[column] = std::move(label);
    }

    void projectSlot(
        SurfaceSlider& slider,
        juce::Label& label,
        const SurfaceSlot& slot,
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
            presentation == PresentationKind::trigger_switch);
        if (!slider.userGestureActive()) {
            slider.setValue(slot.value, juce::dontSendNotification);
        }
        slider.setColour(juce::Slider::rotarySliderFillColourId, colour);
        const bool enabled = processor_.preparedForAudio() && slot.enabled;
        slider.setEnabled(enabled);
        slider.setAlpha(slot.enabled ? 1.0F : 0.32F);
        label.setAlpha(slot.enabled ? 1.0F : 0.42F);
    }

    void projectAcceptedState(const Snapshot& snapshot) {
        observeClearCount(snapshot.diagnostics.effect_clear_count);
        const auto selected_page = std::min<std::size_t>(
            snapshot.accepted.selected_page, kGlobalPageIndex);
        const bool global = selected_page == kGlobalPageIndex;
        current_surface_ = surfaceModel(snapshot);
        for (std::size_t page = 0; page < page_buttons_.size(); ++page) {
            page_buttons_[page]->setToggleState(
                page == selected_page, juce::dontSendNotification);
        }
        running_button_.setToggleState(
            snapshot.accepted.running, juce::dontSendNotification);
        voice_mode_button_.setVisible(!global);
        motion_mode_button_.setVisible(!global);
        voice_mode_button_.setToggleState(
            !global && snapshot.accepted.lane_control_mode == LaneControlMode::voice,
            juce::dontSendNotification);
        motion_mode_button_.setToggleState(
            !global && snapshot.accepted.lane_control_mode == LaneControlMode::motion,
            juce::dontSendNotification);
        clear_fx_button_.setVisible(global);
        top_group_.setText(text(current_surface_.top_group));
        bottom_group_.setText(text(current_surface_.bottom_group));
        surface_guide_.setText(text(current_surface_.guide), juce::dontSendNotification);

        const auto colour = global
            ? juce::Colour{kGlobalColourArgb}
            : kLaneColours[selected_page];
        for (std::size_t column = 0; column < kSurfaceColumnCount; ++column) {
            projectSlot(
                *top_sliders_[column], *top_labels_[column],
                current_surface_.top[column], colour);
            projectSlot(
                *bottom_sliders_[column], *bottom_labels_[column],
                current_surface_.bottom[column], colour);
        }

        if (global) {
            const auto& effect = snapshot.accepted.cohesion;
            engine_banner_.setText(
                "GLOBAL PERFORMANCE  /  COHERE "
                    + juce::String{effect.cohere, 2}
                    + "  /  FX CLEARS "
                    + juce::String{snapshot.diagnostics.effect_clear_count}
                    + "  /  CLEAR IS NOT STORED",
                juce::dontSendNotification);
            return;
        }
        const auto& voice = snapshot.accepted.voices[selected_page];
        const auto resolved_model = snapshot.resolved_engines[selected_page];
        const auto context = snapshot.accepted.lane_control_mode
                == LaneControlMode::voice
            ? "VOICE"
            : "MOTION";
        engine_banner_.setText(
            "LANE " + juce::String{static_cast<int>(selected_page) + 1}
                + "  /  " + context
                + "  /  MODEL "
                + juce::String{static_cast<int>(voice.engine)}.paddedLeft('0', 2)
                + " " + juce::String{modelName(voice.engine)}.toUpperCase()
                + "  /  NOW "
                + juce::String{static_cast<int>(resolved_model)}.paddedLeft('0', 2)
                + " " + juce::String{modelName(resolved_model)}.toUpperCase(),
            juce::dontSendNotification);
    }

    void updateEnabledState() {
        const auto active = processor_.preparedForAudio();
        running_button_.setEnabled(active);
        for (auto& button : page_buttons_) button->setEnabled(active);
        for (std::size_t column = 0; column < kSurfaceColumnCount; ++column) {
            top_sliders_[column]->setEnabled(
                active && current_surface_.top[column].enabled);
            bottom_sliders_[column]->setEnabled(
                active && current_surface_.bottom[column].enabled);
        }
        const auto lane_context = current_surface_.context != SurfaceContext::global;
        voice_mode_button_.setEnabled(active && lane_context);
        motion_mode_button_.setEnabled(active && lane_context);
        clear_fx_button_.setEnabled(
            active && current_surface_.context == SurfaceContext::global);
    }

    void observeClearCount(std::uint64_t count) {
        if (!clear_count_initialized_) {
            last_clear_count_ = count;
            clear_count_initialized_ = true;
            return;
        }
        if (count > last_clear_count_) {
            clear_feedback_ticks_ = 16;
            clear_pending_ = false;
        } else if (count < last_clear_count_) {
            clear_feedback_ticks_ = 0;
            clear_pending_ = false;
            impact_history_.reset();
        }
        last_clear_count_ = count;
        updateClearFeedback();
    }

    void updateClearFeedback() {
        if (clear_feedback_ticks_ > 0) {
            clear_fx_button_.setButtonText("CLEARED");
        } else if (clear_pending_) {
            clear_fx_button_.setButtonText("CLEARING");
        } else {
            clear_fx_button_.setButtonText("CLEAR FX");
        }
    }

    void timerCallback() override {
        const auto snapshot = processor_.acceptedSnapshot();
        projectAcceptedState(snapshot);
        if (processor_.preparedForAudio()) impact_history_.pushSnapshot(snapshot);
        if (clear_feedback_ticks_ > 0) --clear_feedback_ticks_;
        updateClearFeedback();
        if (++status_ticks_ >= 5) {
            status_ticks_ = 0;
            status_.setText(processor_.statusText(), juce::dontSendNotification);
            updateEnabledState();
        }
    }

    Vst3Processor& processor_;
    PamplistVst3LookAndFeel look_and_feel_{};
    juce::Label title_;
    juce::Label subtitle_;
    juce::Label status_;
    juce::Label engine_banner_;
    juce::Label surface_guide_;
    juce::GroupComponent top_group_;
    juce::GroupComponent bottom_group_;
    ImpactHistoryComponent impact_history_;
    juce::TextButton clear_fx_button_;
    juce::TextButton voice_mode_button_;
    juce::TextButton motion_mode_button_;
    juce::ToggleButton running_button_;
    std::array<std::unique_ptr<juce::TextButton>, kPageCount> page_buttons_;
    std::array<std::unique_ptr<SurfaceSlider>, kSurfaceColumnCount> top_sliders_;
    std::array<std::unique_ptr<juce::Label>, kSurfaceColumnCount> top_labels_;
    std::array<std::unique_ptr<SurfaceSlider>, kSurfaceColumnCount> bottom_sliders_;
    std::array<std::unique_ptr<juce::Label>, kSurfaceColumnCount> bottom_labels_;
    std::array<std::optional<std::size_t>, kSurfaceColumnCount>
        top_gesture_indices_{};
    std::array<std::optional<std::size_t>, kSurfaceColumnCount>
        bottom_gesture_indices_{};
    SurfaceModel current_surface_{};
    std::uint64_t last_clear_count_{};
    bool clear_count_initialized_{};
    bool clear_pending_{};
    int clear_feedback_ticks_{};
    int status_ticks_{};

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(PamplistVst3Editor)
};

}  // namespace

juce::AudioProcessorEditor* createPamplistVst3Editor(Vst3Processor& processor) {
    return new PamplistVst3Editor{processor};
}

}  // namespace schuss::pamplist
