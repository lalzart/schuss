#include "tidepit/vst3_processor.hpp"

#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <iostream>
#include <limits>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

juce::String juceString(std::string_view text)
{
    return juce::String::fromUTF8(text.data(), static_cast<int>(text.size()));
}

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error(message);
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

void setPhysical(
    tidepit::Vst3ProgramState& program,
    std::size_t index,
    float physical) {
    const auto& descriptor = tidepit::vst3ParameterDescriptors()[index];
    program.normalized[index] = tidepit::vst3NormalizePhysical(
        descriptor, physical);
}

[[nodiscard]] tidepit::Vst3ProgramState denseProgram() {
    auto program = tidepit::defaultVst3ProgramState();
    setPhysical(program, 0U, 0.73F);
    setPhysical(program, 1U, 0.17F);
    setPhysical(program, 2U, 0.91F);
    setPhysical(program, 3U, 0.42F);
    setPhysical(program, tidepit::kVst3RateIndex, 0.82F);
    setPhysical(program, tidepit::kVst3MemoryIndex, 0.66F);
    setPhysical(program, tidepit::kVst3MaterialIndex, 0.27F);
    setPhysical(program, tidepit::kVst3PositionIndex, 0.84F);
    setPhysical(program, tidepit::kVst3FxAIndex, 0.14F);
    setPhysical(program, tidepit::kVst3FxBIndex, 0.88F);
    setPhysical(program, tidepit::kVst3RootIndex, 67.0F);
    setPhysical(program, tidepit::kVst3SourceIndex, 2.0F);
    setPhysical(program, tidepit::kVst3LockIndex, 1.0F);
    setPhysical(program, tidepit::kVst3EffectIndex, 1.0F);
    setPhysical(program, tidepit::kVst3TargetIndex, 1.0F);
    setPhysical(program, tidepit::kVst3ScaleIndex, 2.0F);
    return program;
}

[[nodiscard]] bool sameProgram(
    const tidepit::Vst3ProgramState& left,
    const tidepit::Vst3ProgramState& right) noexcept {
    return left.normalized == right.normalized;
}

void appendProgramEvents(
    const tidepit::Vst3ProgramState& program,
    std::vector<tidepit::SemanticEvent>& events,
    std::uint64_t& sequence) {
    const auto defaults = tidepit::defaultVst3ProgramState();
    const auto& descriptors = tidepit::vst3ParameterDescriptors();
    constexpr std::array<tidepit::SemanticAction, 11U> continuous{{
        tidepit::SemanticAction::set_stage_1,
        tidepit::SemanticAction::set_stage_2,
        tidepit::SemanticAction::set_stage_3,
        tidepit::SemanticAction::set_stage_4,
        tidepit::SemanticAction::set_rate,
        tidepit::SemanticAction::set_memory,
        tidepit::SemanticAction::set_material,
        tidepit::SemanticAction::set_position,
        tidepit::SemanticAction::set_fx_a,
        tidepit::SemanticAction::set_fx_b,
        tidepit::SemanticAction::set_root,
    }};
    for (std::size_t index = 0; index < continuous.size(); ++index) {
        if (program.normalized[index] == defaults.normalized[index]) continue;
        events.push_back({
            0U,
            sequence++,
            continuous[index],
            tidepit::vst3DenormalizeParameter(
                descriptors[index], program.normalized[index]),
        });
    }
    const auto modes = tidepit::vst3DiscreteFromProgram(program);
    for (int step = 0; step < static_cast<int>(modes.source); ++step) {
        events.push_back({0U, sequence++, tidepit::SemanticAction::source_next, 0.0});
    }
    if (modes.locked) {
        events.push_back({0U, sequence++, tidepit::SemanticAction::lock_toggle, 0.0});
    }
    for (int step = 0; step < static_cast<int>(modes.effect); ++step) {
        events.push_back({0U, sequence++, tidepit::SemanticAction::effect_next, 0.0});
    }
    for (int step = 0; step < static_cast<int>(modes.target); ++step) {
        events.push_back({0U, sequence++, tidepit::SemanticAction::target_next, 0.0});
    }
    for (int step = 0; step < static_cast<int>(modes.scale); ++step) {
        events.push_back({0U, sequence++, tidepit::SemanticAction::scale_next, 0.0});
    }
}

struct DirectRender final {
    std::vector<float> left;
    std::vector<float> right;
    tidepit::Snapshot snapshot{};
    tidepit::Diagnostics diagnostics{};
};

[[nodiscard]] DirectRender renderDirect(
    const tidepit::Vst3ProgramState& program,
    int frames,
    const juce::MidiBuffer* midi = nullptr) {
    DirectRender output{
        std::vector<float>(static_cast<std::size_t>(frames), 0.0F),
        std::vector<float>(static_cast<std::size_t>(frames), 0.0F),
        {},
        {},
    };
    tidepit::Core core;
    expect(core.prepare(
            tidepit::kReferenceSampleRate,
            tidepit::kReferenceQuantumFrames),
        "direct Core preparation failed");
    tidepit::Q27HostBridge bridge;
    bridge.reset();
    std::vector<tidepit::SemanticEvent> events;
    std::uint64_t sequence = 0U;
    appendProgramEvents(program, events, sequence);
    tidepit::JuceMidiAdapter adapter;
    if (midi != nullptr) {
        const auto adapted = adapter.adapt(
            *midi, static_cast<std::uint32_t>(frames));
        for (std::size_t index = 0; index < adapted.event_count; ++index) {
            auto event = adapted.events[index];
            event.ingress_sequence = sequence++;
            events.push_back(event);
        }
    }
    bridge.process(
        core,
        output.left.data(),
        output.right.data(),
        static_cast<std::uint32_t>(frames),
        events.data(),
        events.size());
    output.snapshot = core.snapshot();
    output.diagnostics = core.diagnostics();
    return output;
}

[[nodiscard]] juce::AudioBuffer<float> renderProcessor(
    tidepit::Vst3Processor& processor,
    int frames,
    const juce::MidiBuffer* source_midi = nullptr) {
    juce::AudioBuffer<float> buffer{2, frames};
    for (int channel = 0; channel < 2; ++channel) {
        for (int frame = 0; frame < frames; ++frame) {
            buffer.setSample(channel, frame, 1.0F);
        }
    }
    juce::MidiBuffer midi;
    if (source_midi != nullptr) {
        for (const auto metadata : *source_midi) {
            midi.addEvent(metadata.getMessage(), metadata.samplePosition);
        }
    }
    processor.processBlock(buffer, midi);
    expect(midi.isEmpty(), "processor leaked consumed MIDI");
    return buffer;
}

void expectBufferEquals(
    const juce::AudioBuffer<float>& actual,
    const DirectRender& expected,
    const std::string& message) {
    expect(actual.getNumChannels() >= 2
            && actual.getNumSamples() == static_cast<int>(expected.left.size()),
        message + " shape mismatch");
    for (int frame = 0; frame < actual.getNumSamples(); ++frame) {
        if (actual.getSample(0, frame)
                != expected.left[static_cast<std::size_t>(frame)]
            || actual.getSample(1, frame)
                != expected.right[static_cast<std::size_t>(frame)]) {
            fail(message + " sample mismatch at " + std::to_string(frame));
        }
    }
}

[[nodiscard]] double energy(const juce::AudioBuffer<float>& buffer) {
    double result = 0.0;
    for (int channel = 0; channel < std::min(2, buffer.getNumChannels()); ++channel) {
        for (int frame = 0; frame < buffer.getNumSamples(); ++frame) {
            const auto sample = static_cast<double>(buffer.getSample(channel, frame));
            expect(std::isfinite(sample) && sample >= -1.0 && sample <= 1.0,
                "processor emitted invalid PCM");
            result += sample * sample;
        }
    }
    return result;
}

[[nodiscard]] std::vector<float> renderPartitioned(
    double sample_rate,
    int total_frames,
    const std::vector<int>& partitions,
    int event_host_frame) {
    expect(!partitions.empty(), "empty partition fixture");
    tidepit::Vst3Processor processor;
    expect(processor.applyProgramState(denseProgram()),
        "partition fixture program failed");
    processor.prepareToPlay(
        sample_rate,
        *std::max_element(partitions.begin(), partitions.end()));
    expect(processor.preparedForAudio(), "partition fixture did not prepare");

    std::vector<float> result;
    result.reserve(static_cast<std::size_t>(total_frames) * 2U);
    int origin = 0;
    std::size_t partition_index = 0U;
    while (origin < total_frames) {
        const auto frames = std::min(
            partitions[partition_index++ % partitions.size()],
            total_frames - origin);
        juce::MidiBuffer midi;
        if (event_host_frame >= origin
            && event_host_frame < origin + frames) {
            midi.addEvent(
                juce::MidiMessage::controllerEvent(16, 29, 64),
                event_host_frame - origin);
        }
        const auto block = renderProcessor(processor, frames, &midi);
        for (int frame = 0; frame < frames; ++frame) {
            result.push_back(block.getSample(0, frame));
            result.push_back(block.getSample(1, frame));
        }
        origin += frames;
    }
    expect(processor.processFailureCount() == 0U
            && processor.processorEventDropCount() == 0U,
        "partition fixture reported a processing or event failure");
    return result;
}

void testIdentityParametersAndLayout() {
    tidepit::Vst3Processor processor;
    expect(processor.getName() == "Tide Pit", "processor name drift");
    expect(processor.acceptsMidi() && !processor.producesMidi()
            && !processor.isMidiEffect(),
        "MIDI capability drift");
    expect(processor.getTotalNumInputChannels() == 0
            && processor.getTotalNumOutputChannels() == 2,
        "default bus layout is not zero-input stereo-output");
    expect(processor.getParameters().size()
            == static_cast<int>(tidepit::kVst3ParameterCount),
        "direct processor parameter count drift");
    for (std::size_t index = 0; index < tidepit::kVst3ParameterCount; ++index) {
        const auto* parameter = dynamic_cast<juce::AudioProcessorParameterWithID*>(
            processor.getParameters()[static_cast<int>(index)]);
        expect(parameter != nullptr, "parameter lacks stable ID type");
        expect(parameter->getParameterID()
                == juceString(tidepit::vst3ParameterDescriptors()[index].id),
            "host parameter ID/order mismatch");
    }

    auto invalid = processor.getBusesLayout();
    invalid.getChannelSet(false, 0) = juce::AudioChannelSet::mono();
    expect(!processor.isBusesLayoutSupported(invalid), "mono output accepted");
    expect(processor.isBusesLayoutSupported(processor.getBusesLayout()),
        "default layout rejected");
}

void testDirectParityAndHostBlocks() {
    const auto program = denseProgram();
    for (const int frames : {1, 16, 64, 128, 511, 512, 513, 2048, 4096}) {
        tidepit::Vst3Processor processor;
        expect(processor.applyProgramState(program), "program application failed");
        processor.prepareToPlay(48000.0, frames);
        const auto actual = renderProcessor(processor, frames);
        const auto expected = renderDirect(program, frames);
        expectBufferEquals(actual, expected,
            "direct parity block " + std::to_string(frames));
        if (frames >= 2048) {
            expect(energy(actual) > 0.0, "dense fixture remained silent");
        }
        const auto snapshot = processor.acceptedSnapshot();
        expect(snapshot.absolute_sample == expected.snapshot.absolute_sample,
            "direct accepted absolute sample mismatch");
        expect(processor.processFailureCount() == 0U,
            "processor reported a parity failure");
    }
}

void testTimestampedRawMidiParityAndParameterSync() {
    juce::MidiBuffer midi;
    midi.addEvent(juce::MidiMessage::controllerEvent(16, 20, 127), 31);
    midi.addEvent(juce::MidiMessage::controllerEvent(16, 30, 0), 79);
    midi.addEvent(juce::MidiMessage::controllerEvent(16, 40, 127), 257);
    midi.addEvent(juce::MidiMessage::controllerEvent(16, 40, 0), 261);
    midi.addEvent(juce::MidiMessage::controllerEvent(16, 41, 127), 511);
    midi.addEvent(juce::MidiMessage::controllerEvent(16, 41, 0), 513);
    midi.addEvent(juce::MidiMessage::controllerEvent(1, 21, 127), 700);
    midi.addEvent(juce::MidiMessage::controllerEvent(16, 35, 99), 800);

    const auto program = tidepit::defaultVst3ProgramState();
    tidepit::Vst3Processor processor;
    processor.prepareToPlay(48000.0, 1024);
    const auto actual = renderProcessor(processor, 1024, &midi);
    const auto expected = renderDirect(program, 1024, &midi);
    expectBufferEquals(actual, expected, "timestamped raw MIDI parity");
    expect(processor.parameterPhysical(0U) == 1.0F
            && processor.parameterPhysical(tidepit::kVst3RootIndex) == 36.0F
            && processor.parameterPhysical(tidepit::kVst3SourceIndex) == 1.0F,
        "raw MIDI did not update persistent host parameters");
    const auto frame = processor.uiFrame();
    expect(frame.midi_diagnostics.raw_messages == 8U
            && frame.midi_diagnostics.accepted_messages == 6U
            && frame.midi_diagnostics.ignored_channels == 1U
            && frame.midi_diagnostics.unassigned_controllers == 1U,
        "raw MIDI diagnostics drift");
    expect(frame.core_diagnostics.manual_mutations == 1U,
        "raw Mutate was not accepted exactly once");
}

void testPersistentModeReconciliation() {
    const auto program = denseProgram();
    tidepit::Vst3Processor processor;
    expect(processor.applyProgramState(program), "mode program rejected");
    processor.prepareToPlay(48000.0, 4096);
    int remaining = 40000;
    while (remaining > 0) {
        const auto frames = std::min(4096, remaining);
        static_cast<void>(renderProcessor(processor, frames));
        remaining -= frames;
    }
    const auto snapshot = processor.acceptedSnapshot();
    expect(snapshot.source == tidepit::SourceMode::fold
            && snapshot.locked
            && snapshot.effect == tidepit::EffectMode::filter
            && snapshot.target == tidepit::WaveTarget::body
            && snapshot.scale == tidepit::ScaleMode::dorian,
        "persistent desired modes did not settle through source gestures");
}

void testOneShotsStateRecallAndTransactionalRejection() {
    tidepit::Vst3Processor source;
    source.prepareToPlay(48000.0, 4096);
    source.requestAction(tidepit::SemanticAction::mutate);
    source.requestAction(tidepit::SemanticAction::capture_toggle);
    int remaining = 30000;
    while (remaining > 0) {
        const auto frames = std::min(4096, remaining);
        static_cast<void>(renderProcessor(source, frames));
        remaining -= frames;
    }
    expect(source.acceptedSnapshot().captured,
        "Freeze one-shot did not reach accepted captured state");
    expect(source.uiFrame().core_diagnostics.manual_mutations == 1U,
        "Mutate one-shot did not resolve exactly once");

    juce::MemoryBlock state;
    source.getStateInformation(state);
    expect(state.getSize() > 0U, "serialized state is empty");
    tidepit::Vst3Processor restored;
    restored.setStateInformation(state.getData(), static_cast<int>(state.getSize()));
    expect(restored.acceptedStateCount() == 1U
            && restored.rejectedStateCount() == 0U,
        "valid state transaction was not accepted once");
    restored.prepareToPlay(48000.0, 256);
    static_cast<void>(renderProcessor(restored, 256));
    const auto fresh = restored.uiFrame();
    expect(!fresh.snapshot.captured
            && fresh.core_diagnostics.manual_mutations == 0U,
        "state recall replayed Freeze or Mutate");
    expect(sameProgram(source.programState(), restored.programState()),
        "state program round-trip mismatch");

    const auto before = restored.programState();
    restored.setStateInformation(state.getData(), static_cast<int>(state.getSize() / 2U));
    expect(restored.rejectedStateCount() == 1U
            && sameProgram(before, restored.programState()),
        "truncated state partially mutated the program");

    const auto tree = juce::ValueTree::fromXml(juce::String::fromUTF8(
        static_cast<const char*>(state.getData()),
        static_cast<int>(state.getSize())));
    expect(tree.isValid(), "serialized XML state did not parse in fixture");
    std::uint64_t expected_rejections = 1U;
    const auto rejectTree = [&](juce::ValueTree candidate, const char* message) {
        const auto xml = candidate.toXmlString();
        juce::MemoryBlock bytes;
        bytes.append(xml.toRawUTF8(), xml.getNumBytesAsUTF8());
        restored.setStateInformation(bytes.getData(), static_cast<int>(bytes.getSize()));
        ++expected_rejections;
        expect(restored.rejectedStateCount() == expected_rejections
                && sameProgram(before, restored.programState()),
            message);
    };

    auto duplicate = tree.createCopy();
    auto values = duplicate.getChild(0);
    values.getChild(1).setProperty(
        "id", values.getChild(0).getProperty("id"), nullptr);
    rejectTree(duplicate, "duplicate-ID state partially mutated the program");

    auto wrong_version = tree.createCopy();
    wrong_version.setProperty("schemaVersion", 2, nullptr);
    rejectTree(wrong_version, "wrong-version state partially mutated the program");

    auto missing = tree.createCopy();
    missing.getChild(0).removeChild(0, nullptr);
    rejectTree(missing, "missing-parameter state partially mutated the program");

    auto non_finite = tree.createCopy();
    non_finite.getChild(0).getChild(0).setProperty("value", "nan", nullptr);
    rejectTree(non_finite, "non-finite state partially mutated the program");

    auto out_of_range = tree.createCopy();
    out_of_range.getChild(0).getChild(0).setProperty("value", "1.1", nullptr);
    rejectTree(out_of_range, "out-of-range state partially mutated the program");

    auto off_grid = tree.createCopy();
    off_grid.getChild(0).getChild(static_cast<int>(tidepit::kVst3SourceIndex))
        .setProperty("value", "0.2", nullptr);
    rejectTree(off_grid, "off-grid discrete state partially mutated the program");

    juce::MemoryBlock oversized(1024U * 1024U + 1U, true);
    restored.setStateInformation(
        oversized.getData(), static_cast<int>(oversized.getSize()));
    ++expected_rejections;
    expect(restored.rejectedStateCount() == expected_rejections
            && sameProgram(before, restored.programState()),
        "oversized state partially mutated the program");
}

void testFreshStateTwinExactSignal() {
    const auto program = denseProgram();
    tidepit::Vst3Processor first;
    expect(first.applyProgramState(program), "state-twin source program rejected");
    juce::MemoryBlock state;
    first.getStateInformation(state);
    tidepit::Vst3Processor second;
    second.setStateInformation(state.getData(), static_cast<int>(state.getSize()));
    first.prepareToPlay(48000.0, 4096);
    second.prepareToPlay(48000.0, 4096);
    for (int block = 0; block < 12; ++block) {
        const auto left = renderProcessor(first, 4096);
        const auto right = renderProcessor(second, 4096);
        for (int channel = 0; channel < 2; ++channel) {
            for (int frame = 0; frame < 4096; ++frame) {
                expect(left.getSample(channel, frame) == right.getSample(channel, frame),
                    "fresh state twins diverged at block " + std::to_string(block));
            }
        }
    }
}

void testSupportedHostRatesAndInstanceIsolation() {
    const auto program = denseProgram();
    struct RateCase final {
        double sample_rate;
        int latency;
    };
    constexpr std::array<RateCase, 7U> rate_cases{{
        {32000.0, 44},
        {44100.0, 60},
        {48000.0, 0},
        {88200.0, 120},
        {96000.0, 130},
        {176400.0, 239},
        {192000.0, 260},
    }};
    for (const auto& rate : rate_cases) {
        tidepit::Vst3Processor supported;
        expect(supported.applyProgramState(program), "supported-rate program failed");
        supported.prepareToPlay(rate.sample_rate, 4096);
        expect(supported.preparedForAudio()
                && supported.getLatencySamples() == rate.latency,
            "supported host rate or latency was rejected");
        const auto output = renderProcessor(supported, 4096);
        expect(energy(output) > 0.0
                && supported.processFailureCount() == 0U,
            "supported host rate did not produce bounded signal");
    }

    const auto contiguous = renderPartitioned(44100.0, 12000, {511}, 777);
    const auto awkward = renderPartitioned(
        44100.0, 12000, {1, 127, 16, 509, 3, 257}, 777);
    expect(contiguous == awkward,
        "44.1 kHz render changed with host callback partitioning");

    tidepit::Vst3Processor unsupported;
    expect(unsupported.applyProgramState(program), "unsupported-rate program failed");
    unsupported.prepareToPlay(48001.0, 128);
    const auto unsupported_output = renderProcessor(unsupported, 128);
    expect(energy(unsupported_output) == 0.0
            && !unsupported.preparedForAudio()
            && unsupported.getLatencySamples() == 0,
        "unsupported sample rate did not fail to exact silence");

    tidepit::Vst3Processor oversized;
    expect(oversized.applyProgramState(program), "oversized-block program failed");
    oversized.prepareToPlay(44100.0, 8192);
    const auto oversized_output = renderProcessor(oversized, 8193);
    expect(energy(oversized_output) == 0.0
            && oversized.preparedForAudio()
            && oversized.processFailureCount() == 1U,
        "oversized resampled callback did not fail closed");

    tidepit::Vst3Processor deferred_event;
    deferred_event.prepareToPlay(192000.0, 1);
    static_cast<void>(renderProcessor(deferred_event, 1));
    juce::MidiBuffer mutate;
    mutate.addEvent(juce::MidiMessage::controllerEvent(16, 41, 127), 0);
    static_cast<void>(renderProcessor(deferred_event, 1, &mutate));
    for (int frame = 0; frame < 80; ++frame) {
        static_cast<void>(renderProcessor(deferred_event, 1));
    }
    const auto deferred_frame = deferred_event.uiFrame();
    expect(deferred_frame.core_diagnostics.manual_mutations == 1U
            && deferred_frame.bridge_event_drops == 0U
            && deferred_event.processorEventDropCount() == 0U,
        "zero-source-frame callback event mismatch: mutations="
            + std::to_string(
                deferred_frame.core_diagnostics.manual_mutations)
            + " bridge_drops="
            + std::to_string(deferred_frame.bridge_event_drops)
            + " processor_drops="
            + std::to_string(deferred_event.processorEventDropCount()));

    tidepit::Vst3Processor invalid_layout;
    invalid_layout.prepareToPlay(48000.0, 128);
    juce::AudioBuffer<float> mono{1, 128};
    for (int frame = 0; frame < 128; ++frame) mono.setSample(0, frame, 1.0F);
    juce::MidiBuffer no_midi;
    invalid_layout.processBlock(mono, no_midi);
    expect(mono.getMagnitude(0, mono.getNumSamples()) == 0.0F,
        "invalid runtime channel shape did not fail to silence");

    tidepit::Vst3Processor left;
    tidepit::Vst3Processor right;
    expect(left.applyProgramState(program) && right.applyProgramState(program),
        "multi-instance program failed");
    left.prepareToPlay(48000.0, 2048);
    right.prepareToPlay(48000.0, 2048);
    const auto left_audio = renderProcessor(left, 2048);
    const auto right_audio = renderProcessor(right, 2048);
    for (int channel = 0; channel < 2; ++channel) {
        for (int frame = 0; frame < 2048; ++frame) {
            expect(left_audio.getSample(channel, frame)
                    == right_audio.getSample(channel, frame),
                "identical instances diverged");
        }
    }
    const auto right_before = right.programState();
    left.requestAction(tidepit::SemanticAction::mutate);
    static_cast<void>(renderProcessor(left, 64));
    static_cast<void>(renderProcessor(right, 64));
    expect(left.uiFrame().core_diagnostics.manual_mutations == 1U
            && right.uiFrame().core_diagnostics.manual_mutations == 0U
            && sameProgram(right_before, right.programState()),
        "instances shared action or program state");
}

void testEditorLifecycle() {
    juce::ScopedJuceInitialiser_GUI gui;
    tidepit::Vst3Processor processor;
    std::unique_ptr<juce::AudioProcessorEditor> editor{processor.createEditor()};
    expect(editor != nullptr
            && editor->getWidth() == 1080
            && editor->getHeight() == 650,
        "unattached editor construction drift");
    editor.reset();
    expect(processor.uiFrame().midi_diagnostics.raw_messages == 0U,
        "editor lifecycle injected MIDI or opened an endpoint");
}

}  // namespace

int main() {
    try {
        testIdentityParametersAndLayout();
        testDirectParityAndHostBlocks();
        testTimestampedRawMidiParityAndParameterSync();
        testPersistentModeReconciliation();
        testOneShotsStateRecallAndTransactionalRejection();
        testFreshStateTwinExactSignal();
        testSupportedHostRatesAndInstanceIsolation();
        testEditorLifecycle();
        std::cout << "Tide Pit VST3 processor checks passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Tide Pit VST3 processor failure: " << error.what() << "\n";
        return 1;
    }
}
