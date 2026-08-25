#include "tidepit/vst3_model.hpp"

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <iostream>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <utility>

#if !JUCE_PLUGINHOST_VST3
#error "Tide Pit module tests require the JUCE VST3 host"
#endif

namespace {

juce::String juceString(std::string_view text)
{
    return juce::String::fromUTF8(text.data(), static_cast<int>(text.size()));
}

constexpr std::size_t kVst3BypassParameterCount = 1U;
constexpr std::size_t kVst3MidiControllerParameterCount = 16U * 130U;

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error{message};
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

[[nodiscard]] juce::AudioProcessorParameter& parameterAt(
    juce::AudioProcessor& processor,
    std::size_t index) {
    expect(index < static_cast<std::size_t>(processor.getParameters().size()),
        "parameter index outside hosted surface");
    auto* parameter = processor.getParameters()[static_cast<int>(index)];
    expect(parameter != nullptr, "host returned a null parameter");
    return *parameter;
}

void setPhysical(
    juce::AudioProcessor& processor,
    std::string_view id,
    float physical) {
    const auto index = tidepit::vst3ParameterIndexForId(id);
    expect(index.has_value(), "unknown fixture parameter " + std::string{id});
    const auto& descriptor = tidepit::vst3ParameterDescriptors()[*index];
    parameterAt(processor, *index).setValue(
        tidepit::vst3NormalizePhysical(descriptor, physical));
}

void configureAudibleProgram(juce::AudioProcessor& processor) {
    setPhysical(processor, "tide.stage1", 0.73F);
    setPhysical(processor, "tide.stage2", 0.17F);
    setPhysical(processor, "tide.stage3", 0.91F);
    setPhysical(processor, "tide.stage4", 0.42F);
    setPhysical(processor, "tide.rate", 0.82F);
    setPhysical(processor, "tide.memory", 0.66F);
    setPhysical(processor, "tide.material", 0.27F);
    setPhysical(processor, "tide.position", 0.84F);
    setPhysical(processor, "tide.fx-a", 0.14F);
    setPhysical(processor, "tide.fx-b", 0.88F);
    setPhysical(processor, "tide.root", 67.0F);
    setPhysical(processor, "tide.source", 2.0F);
    setPhysical(processor, "tide.lock", 1.0F);
    setPhysical(processor, "tide.effect", 1.0F);
    setPhysical(processor, "tide.target", 1.0F);
    setPhysical(processor, "tide.scale", 2.0F);
}

[[nodiscard]] double processAndCompare(
    juce::AudioPluginInstance& left,
    juce::AudioPluginInstance& right) {
    double total_energy = 0.0;
    for (int block_index = 0; block_index < 12; ++block_index) {
        juce::AudioBuffer<float> left_buffer{2, 512};
        juce::AudioBuffer<float> right_buffer{2, 512};
        left_buffer.clear();
        right_buffer.clear();
        juce::MidiBuffer left_midi;
        juce::MidiBuffer right_midi;
        if (block_index == 1) {
            const auto message = juce::MidiMessage::controllerEvent(16, 29, 64);
            left_midi.addEvent(message, 137);
            right_midi.addEvent(message, 137);
        }
        left.processBlock(left_buffer, left_midi);
        right.processBlock(right_buffer, right_midi);
        expect(left_midi.isEmpty() && right_midi.isEmpty(),
            "hosted instrument leaked MIDI output");
        for (int channel = 0; channel < 2; ++channel) {
            for (int frame = 0; frame < 512; ++frame) {
                const auto left_sample = left_buffer.getSample(channel, frame);
                const auto right_sample = right_buffer.getSample(channel, frame);
                expect(std::isfinite(left_sample)
                        && left_sample >= -1.0F && left_sample <= 1.0F,
                    "hosted module emitted invalid PCM");
                expect(left_sample == right_sample,
                    "state-twin VST3 modules diverged at block "
                        + std::to_string(block_index)
                        + " frame " + std::to_string(frame));
                total_energy += static_cast<double>(left_sample) * left_sample;
            }
        }
    }
    return total_energy;
}

void run(const juce::File& bundle) {
    expect(bundle.isDirectory(), "VST3 bundle path does not exist");

    juce::VST3PluginFormat format;
    expect(format.fileMightContainThisPluginType(bundle.getFullPathName()),
        "JUCE did not recognize the bundle as a possible VST3");
    juce::OwnedArray<juce::PluginDescription> descriptions;
    format.findAllTypesForFile(descriptions, bundle.getFullPathName());
    expect(descriptions.size() == 1,
        "bundle did not expose exactly one VST3 class");
    const auto& description = *descriptions[0];
    expect(description.name == "Tide Pit"
            && description.manufacturerName == "Schuss"
            && description.pluginFormatName == "VST3",
        "scanned identity drift");
    expect(description.isInstrument,
        "scanned VST3 class was not marked as an instrument");

    const auto instantiate = [&](double sample_rate) {
        juce::String error;
        auto instance = format.createInstanceFromDescription(
            description, sample_rate, 512, error);
        expect(instance != nullptr,
            "VST3 instantiation failed: " + error.toStdString());
        return instance;
    };

    auto left = instantiate(48000.0);
    expect(left->getName() == "Tide Pit"
            && left->getTotalNumInputChannels() == 0
            && left->getTotalNumOutputChannels() == 2
            && left->acceptsMidi() && !left->producesMidi(),
        "instantiated processor contract drift");
    expect(left->getParameters().size()
            == static_cast<int>(tidepit::kVst3ParameterCount
                + kVst3BypassParameterCount
                + kVst3MidiControllerParameterCount),
        "instantiated host parameter/service count drift");

    std::set<std::string> exported_ids;
    const auto& descriptors = tidepit::vst3ParameterDescriptors();
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        auto& parameter = parameterAt(*left, index);
        expect(parameter.getName(256) == juceString(descriptors[index].name),
            "instantiated parameter order/name drift at index "
                + std::to_string(index));
        const auto* identified =
            dynamic_cast<juce::HostedAudioProcessorParameter*>(&parameter);
        expect(identified != nullptr, "hosted parameter has no stable ID");
        const auto id = identified->getParameterID().toStdString();
        expect(!id.empty() && exported_ids.insert(id).second,
            "hosted parameter ID is empty or duplicated");
    }
    auto& bypass = parameterAt(*left, tidepit::kVst3ParameterCount);
    expect(&bypass == left->getBypassParameter()
            && bypass.getName(256) == "Bypass",
        "VST3 wrapper bypass parameter drift");
    for (std::size_t index = tidepit::kVst3ParameterCount + 1U;
         index < static_cast<std::size_t>(left->getParameters().size());
         ++index) {
        auto& parameter = parameterAt(*left, index);
        expect(!parameter.isAutomatable()
                && parameter.getName(256).startsWith("MIDI CC "),
            "VST3 MIDI-controller service parameter drift");
    }

    configureAudibleProgram(*left);
    juce::MemoryBlock state;
    left->getStateInformation(state);
    expect(state.getSize() > 0U, "hosted VST3 returned empty state");

    auto right = instantiate(48000.0);
    right->setStateInformation(state.getData(), static_cast<int>(state.getSize()));
    expect(right->getParameters().size() == left->getParameters().size(),
        "state twin parameter count drift");
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        expect(parameterAt(*left, index).getValue()
                == parameterAt(*right, index).getValue(),
            "hosted state round-trip mismatch at index "
                + std::to_string(index));
    }

    left->setNonRealtime(true);
    right->setNonRealtime(true);
    left->prepareToPlay(48000.0, 512);
    right->prepareToPlay(48000.0, 512);
    expect(processAndCompare(*left, *right) > 0.0,
        "hosted audible fixture remained silent");

    for (const auto& [sample_rate, latency] : {
             std::pair{44100.0, 60},
             std::pair{96000.0, 130}}) {
        auto resampled_left = instantiate(sample_rate);
        auto resampled_right = instantiate(sample_rate);
        resampled_left->setStateInformation(
            state.getData(), static_cast<int>(state.getSize()));
        resampled_right->setStateInformation(
            state.getData(), static_cast<int>(state.getSize()));
        resampled_left->setNonRealtime(true);
        resampled_right->setNonRealtime(true);
        resampled_left->prepareToPlay(sample_rate, 512);
        resampled_right->prepareToPlay(sample_rate, 512);
        expect(resampled_left->getLatencySamples() == latency
                && resampled_right->getLatencySamples() == latency,
            "hosted resampling latency drift");
        expect(processAndCompare(*resampled_left, *resampled_right) > 0.0,
            "hosted resampled fixture remained silent");
        resampled_left->releaseResources();
        resampled_right->releaseResources();
    }

    std::unique_ptr<juce::AudioProcessorEditor> editor{
        left->createEditorAndMakeActive()};
    expect(editor != nullptr && editor->getWidth() == 1080
            && editor->getHeight() == 650 && !editor->isShowing(),
        "hosted editor did not construct unattached at the bounded size");
    editor.reset();
    left->releaseResources();
    right->releaseResources();
}

}  // namespace

int main(int argc, char** argv) {
    juce::ScopedJuceInitialiser_GUI gui;
    try {
        expect(argc == 2, "expected one VST3 bundle path argument");
        run(juce::File{juce::String::fromUTF8(argv[1])});
    } catch (const std::exception& error) {
        std::cerr << "tide_pit_vst3_module_tests: " << error.what() << '\n';
        return 1;
    }
    std::cout << "tide_pit_vst3_module_tests: PASS\n";
    return 0;
}
