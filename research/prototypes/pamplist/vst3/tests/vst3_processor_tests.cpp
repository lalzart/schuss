#include "schuss/pamplist/vst3_processor.hpp"

#include <juce_gui_basics/juce_gui_basics.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace pam = schuss::pamplist;

namespace {

constexpr float kQ27ToFloat = 1.0F / 134217728.0F;

[[noreturn]] void fail(const std::string& message) {
    throw std::runtime_error{message};
}

void expect(bool condition, const std::string& message) {
    if (!condition) fail(message);
}

void setPhysical(
    pam::Vst3ProgramState& program,
    std::string_view id,
    float physical) {
    const auto index = pam::vst3ParameterIndexForId(id);
    expect(index.has_value(), "unknown test parameter " + std::string{id});
    const auto& descriptor = pam::vst3ParameterDescriptors()[*index];
    program.normalized[*index] = pam::vst3NormalizePhysical(descriptor, physical);
}

[[nodiscard]] pam::Vst3ProgramState enabledProgram() {
    auto program = pam::defaultVst3ProgramState();
    setPhysical(program, "pamp.lane1.rate", 8.0F);
    setPhysical(program, "pamp.lane1.phase", 0.0F);
    setPhysical(program, "pamp.lane1.shape", 1.0F);
    setPhysical(program, "pamp.lane1.hits", 16.0F);
    setPhysical(program, "pamp.lane1.chance", 1.0F);
    setPhysical(program, "pamp.lane1.depth", 1.0F);
    setPhysical(program, "pamp.lane1.motion.trigger", 1.0F);
    setPhysical(program, "pamp.lane1.voice.model", 21.0F);
    setPhysical(program, "pamp.lane1.voice.pitch", 36.0F);
    setPhysical(program, "pamp.lane1.voice.level", 0.22F);
    setPhysical(program, "pamp.master", 0.65F);
    setPhysical(program, "pamp.run", 1.0F);
    return program;
}

[[nodiscard]] bool sameProgram(
    const pam::Vst3ProgramState& left,
    const pam::Vst3ProgramState& right) {
    return left.normalized == right.normalized
        && left.seed == right.seed
        && left.selected_page == right.selected_page
        && left.lane_control_mode == right.lane_control_mode;
}

struct DirectRender final {
    std::vector<float> left;
    std::vector<float> right;
    pam::Snapshot snapshot{};
};

void renderDirectRange(
    pam::Core& core,
    const pam::Controls& controls,
    int start,
    int frames,
    DirectRender& output) {
    std::array<std::int32_t, pam::kMaximumHostBlockFrames> main{};
    std::array<std::int32_t, pam::kMaximumHostBlockFrames> auxiliary{};
    int offset = 0;
    while (offset < frames) {
        const auto chunk = std::min<int>(
            frames - offset,
            static_cast<int>(pam::kMaximumHostBlockFrames));
        pam::ProcessReport report{};
        expect(core.process(
                controls,
                main.data(),
                auxiliary.data(),
                static_cast<std::size_t>(chunk),
                &report),
            "direct Core rejected comparator range");
        for (int frame = 0; frame < chunk; ++frame) {
            output.left[static_cast<std::size_t>(start + offset + frame)]
                = static_cast<float>(main[frame]) * kQ27ToFloat;
            output.right[static_cast<std::size_t>(start + offset + frame)]
                = static_cast<float>(auxiliary[frame]) * kQ27ToFloat;
        }
        output.snapshot = report.snapshot;
        offset += chunk;
    }
}

[[nodiscard]] DirectRender renderDirect(
    const pam::Vst3ProgramState& program,
    int frames,
    const std::vector<std::pair<int, juce::MidiMessage>>& events = {}) {
    DirectRender output{
        std::vector<float>(static_cast<std::size_t>(frames), 0.0F),
        std::vector<float>(static_cast<std::size_t>(frames), 0.0F),
        {},
    };
    pam::Core core;
    pam::ControllerAdapter controller;
    auto controls = pam::vst3ControlsFromProgram(program);
    int cursor = 0;
    for (const auto& [raw_position, message] : events) {
        const auto position = std::clamp(raw_position, cursor, frames);
        renderDirectRange(core, controls, cursor, position - cursor, output);
        cursor = position;
        if (message.isController()) {
            static_cast<void>(controller.handleCc(
                controls,
                message.getChannel(),
                message.getControllerNumber(),
                message.getControllerValue()));
            controls = pam::sanitizeControls(controls);
        }
    }
    renderDirectRange(core, controls, cursor, frames - cursor, output);
    return output;
}

[[nodiscard]] juce::AudioBuffer<float> renderProcessor(
    pam::Vst3Processor& processor,
    int frames,
    const std::vector<std::pair<int, juce::MidiMessage>>& events = {}) {
    juce::AudioBuffer<float> buffer{2, frames};
    buffer.clear();
    juce::MidiBuffer midi;
    for (const auto& [position, message] : events) midi.addEvent(message, position);
    processor.processBlock(buffer, midi);
    expect(midi.isEmpty(), "processor leaked consumed MIDI to output");
    return buffer;
}

void expectBufferEquals(
    const juce::AudioBuffer<float>& actual,
    const DirectRender& expected,
    const std::string& message) {
    expect(actual.getNumSamples() == static_cast<int>(expected.left.size())
            && actual.getNumChannels() >= 2,
        message + " shape mismatch");
    for (int frame = 0; frame < actual.getNumSamples(); ++frame) {
        if (actual.getSample(0, frame)
                != expected.left[static_cast<std::size_t>(frame)]
            || actual.getSample(1, frame)
                != expected.right[static_cast<std::size_t>(frame)]) {
            fail(message + " sample mismatch at frame " + std::to_string(frame));
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
    pam::Vst3Processor processor;
    expect(processor.applyProgramState(enabledProgram()),
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
        std::vector<std::pair<int, juce::MidiMessage>> events;
        if (event_host_frame >= origin
            && event_host_frame < origin + frames) {
            events.emplace_back(
                event_host_frame - origin,
                juce::MidiMessage::controllerEvent(16, 29, 64));
        }
        const auto block = renderProcessor(processor, frames, events);
        for (int frame = 0; frame < frames; ++frame) {
            result.push_back(block.getSample(0, frame));
            result.push_back(block.getSample(1, frame));
        }
        origin += frames;
    }
    expect(processor.processFailureCount() == 0U,
        "partition fixture reported a processing failure");
    return result;
}

void testIdentityParametersAndLayout() {
    pam::Vst3Processor processor;
    expect(processor.getName() == "Pamplist", "processor name drift");
    expect(processor.acceptsMidi() && !processor.producesMidi()
            && !processor.isMidiEffect(),
        "MIDI capability drift");
    expect(processor.getTotalNumInputChannels() == 0
            && processor.getTotalNumOutputChannels() == 2,
        "default bus layout is not zero-input stereo-output");
    expect(processor.getParameters().size()
            == static_cast<int>(pam::kVst3ParameterCount),
        "host parameter count drift");
    for (std::size_t index = 0; index < pam::kVst3ParameterCount; ++index) {
        const auto* parameter = dynamic_cast<juce::AudioProcessorParameterWithID*>(
            processor.getParameters()[static_cast<int>(index)]);
        expect(parameter != nullptr, "parameter lacks stable ID type");
        expect(parameter->getParameterID()
                == juce::String{pam::vst3ParameterDescriptors()[index].id},
            "host parameter ID/order mismatch");
    }

    auto invalid = processor.getBusesLayout();
    invalid.getChannelSet(false, 0) = juce::AudioChannelSet::mono();
    expect(!processor.isBusesLayoutSupported(invalid),
        "mono output layout accepted");
    expect(processor.isBusesLayoutSupported(processor.getBusesLayout()),
        "default layout rejected");
}

void testDirectParityAndLargeBlocks() {
    for (const int frames : {1, 16, 64, 128, 512, 513, 2048, 4096}) {
        auto program = enabledProgram();
        pam::Vst3Processor processor;
        expect(processor.applyProgramState(program), "program application failed");
        processor.prepareToPlay(48000.0, frames);
        const auto actual = renderProcessor(processor, frames);
        const auto expected = renderDirect(program, frames);
        expectBufferEquals(actual, expected,
            "direct parity block " + std::to_string(frames));
        if (frames >= 512) {
            expect(energy(actual) > 0.0, "enabled fixture remained silent");
        }
        const auto snapshot = processor.acceptedSnapshot();
        expect(snapshot.absolute_frame == static_cast<std::uint64_t>(frames)
                && snapshot.absolute_frame == expected.snapshot.absolute_frame
                && snapshot.diagnostics.trigger_count
                    == expected.snapshot.diagnostics.trigger_count,
            "accepted direct trace mismatch");
        expect(processor.processFailureCount() == 0U,
            "processor reported a direct-parity failure");
    }
}

void testTimestampedMidiParity() {
    auto program = pam::defaultVst3ProgramState();
    program.selected_page = 0U;
    program.lane_control_mode = pam::LaneControlMode::motion;
    setPhysical(program, "pamp.lane1.hits", 16.0F);
    setPhysical(program, "pamp.lane1.voice.model", 21.0F);
    setPhysical(program, "pamp.lane1.voice.pitch", 36.0F);
    setPhysical(program, "pamp.lane1.voice.level", 0.25F);
    const std::vector<std::pair<int, juce::MidiMessage>> events{
        {31, juce::MidiMessage::controllerEvent(16, 20, 127)},
        {79, juce::MidiMessage::controllerEvent(16, 35, 127)},
        {257, juce::MidiMessage::controllerEvent(16, 29, 64)},
        {511, juce::MidiMessage::controllerEvent(16, 32, 3)},
        {700, juce::MidiMessage::controllerEvent(1, 35, 0)},
    };

    pam::Vst3Processor processor;
    expect(processor.applyProgramState(program), "MIDI program application failed");
    processor.prepareToPlay(48000.0, 1024);
    const auto actual = renderProcessor(processor, 1024, events);
    const auto expected = renderDirect(program, 1024, events);
    expectBufferEquals(actual, expected, "timestamped MIDI parity");
    expect(processor.receivedMidiCount() == events.size()
            && processor.mappedMidiCount() == events.size() - 1U,
        "MIDI receipt/mapping diagnostics mismatch");
    const auto controls = processor.requestedControls();
    expect(controls.lanes[0].routes[0] == 1.0F
            && controls.lanes[0].amplitude == 1.0F
            && controls.lanes[0].phase_u7 == 64U,
        "MIDI changes did not persist into host parameters");

    auto action_program = enabledProgram();
    action_program.lane_control_mode = pam::LaneControlMode::motion;
    setPhysical(action_program, "pamp.global.cohere", 0.8F);
    const std::vector<std::pair<int, juce::MidiMessage>> action_events{
        {97, juce::MidiMessage::controllerEvent(16, 47, 127)},
        {101, juce::MidiMessage::controllerEvent(16, 47, 0)},
        {211, juce::MidiMessage::controllerEvent(16, 47, 127)},
        {217, juce::MidiMessage::controllerEvent(16, 47, 0)},
        {389, juce::MidiMessage::controllerEvent(16, 40, 127)},
        {397, juce::MidiMessage::controllerEvent(16, 40, 0)},
        {613, juce::MidiMessage::controllerEvent(16, 40, 127)},
        {619, juce::MidiMessage::controllerEvent(16, 40, 0)},
    };
    pam::Vst3Processor actions;
    expect(actions.applyProgramState(action_program),
        "MIDI action program application failed");
    actions.prepareToPlay(48000.0, 1024);
    const auto action_audio = renderProcessor(actions, 1024, action_events);
    const auto action_direct = renderDirect(action_program, 1024, action_events);
    expectBufferEquals(action_audio, action_direct,
        "timestamped page/mode/Clear MIDI parity");
    const auto action_snapshot = actions.acceptedSnapshot();
    expect(action_snapshot.diagnostics.effect_clear_count == 1U
            && action_snapshot.accepted.selected_page == 0U
            && action_snapshot.accepted.lane_control_mode
                == pam::LaneControlMode::voice,
        "timestamped page/mode/Clear actions did not resolve once");
}

void testStateRoundTripClearExclusionAndRejection() {
    auto program = enabledProgram();
    program.seed = UINT32_C(0xf1234567);
    program.selected_page = pam::kGlobalPageIndex;
    program.lane_control_mode = pam::LaneControlMode::motion;
    setPhysical(program, "pamp.global.cohere", 0.8F);
    setPhysical(program, "pamp.global.tail", 0.9F);

    pam::Vst3Processor source;
    expect(source.applyProgramState(program), "state source program failed");
    source.prepareToPlay(48000.0, 256);
    static_cast<void>(renderProcessor(source, 256));
    source.requestClear();
    static_cast<void>(renderProcessor(source, 256));
    expect(source.acceptedSnapshot().diagnostics.effect_clear_count == 1U,
        "source Clear was not accepted once");

    juce::MemoryBlock state;
    source.getStateInformation(state);
    expect(state.getSize() > 0U, "serialized state is empty");

    pam::Vst3Processor restored;
    restored.setStateInformation(state.getData(), static_cast<int>(state.getSize()));
    expect(restored.acceptedStateCount() == 1U
            && restored.rejectedStateCount() == 0U,
        "valid state transaction was not accepted exactly once");
    expect(sameProgram(source.programState(), restored.programState()),
        "state program round-trip mismatch");
    restored.prepareToPlay(48000.0, 256);
    const auto restored_audio = renderProcessor(restored, 256);
    const auto fresh = renderDirect(restored.programState(), 256);
    expectBufferEquals(restored_audio, fresh, "fresh state recall comparator");
    expect(restored.acceptedSnapshot().diagnostics.effect_clear_count == 0U,
        "state recall replayed Clear");

    const auto before = restored.programState();
    restored.setStateInformation(state.getData(), static_cast<int>(state.getSize() / 2U));
    expect(restored.rejectedStateCount() == 1U
            && sameProgram(before, restored.programState()),
        "truncated state partially mutated the program");

    const auto serialized_tree = juce::ValueTree::fromXml(juce::String::fromUTF8(
        static_cast<const char*>(state.getData()),
        static_cast<int>(state.getSize())));
    expect(serialized_tree.isValid(),
        "serialized XML state did not parse in fixture");
    std::uint64_t expected_rejections = 1U;
    const auto rejectTree = [&](juce::ValueTree candidate, const char* message) {
        const auto xml = candidate.toXmlString();
        juce::MemoryBlock bytes;
        bytes.append(xml.toRawUTF8(), xml.getNumBytesAsUTF8());
        restored.setStateInformation(
            bytes.getData(), static_cast<int>(bytes.getSize()));
        ++expected_rejections;
        expect(restored.rejectedStateCount() == expected_rejections
                && sameProgram(before, restored.programState()),
            message);
    };

    auto duplicate = serialized_tree.createCopy();
    auto values = duplicate.getChild(0);
    values.getChild(1).setProperty(
        "id", values.getChild(0).getProperty("id"), nullptr);
    rejectTree(duplicate, "duplicate-ID state partially mutated the program");

    auto wrong_version = serialized_tree.createCopy();
    wrong_version.setProperty("schemaVersion", 2, nullptr);
    rejectTree(wrong_version,
        "wrong-version state partially mutated the program");

    auto missing = serialized_tree.createCopy();
    missing.getChild(0).removeChild(0, nullptr);
    rejectTree(missing, "missing-parameter state partially mutated the program");

    auto missing_id = serialized_tree.createCopy();
    missing_id.getChild(0).getChild(0).removeProperty("id", nullptr);
    rejectTree(missing_id, "missing-ID state partially mutated the program");

    auto non_finite = serialized_tree.createCopy();
    non_finite.getChild(0).getChild(0).setProperty("value", "nan", nullptr);
    rejectTree(non_finite, "non-finite state partially mutated the program");

    auto out_of_range = serialized_tree.createCopy();
    out_of_range.getChild(0).getChild(0).setProperty("value", "1.1", nullptr);
    rejectTree(out_of_range,
        "out-of-range state partially mutated the program");

    juce::MemoryBlock oversized(1024U * 1024U + 1U, true);
    restored.setStateInformation(
        oversized.getData(), static_cast<int>(oversized.getSize()));
    ++expected_rejections;
    expect(restored.rejectedStateCount() == expected_rejections
            && sameProgram(before, restored.programState()),
        "oversized state partially mutated the program");
}

void testSupportedRatesAndMultiInstanceIsolation() {
    auto program = enabledProgram();
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
        pam::Vst3Processor supported;
        expect(supported.applyProgramState(program),
            "supported-rate program failed");
        supported.prepareToPlay(rate.sample_rate, 4096);
        expect(supported.preparedForAudio()
                && supported.getLatencySamples() == rate.latency,
            "supported host rate or latency was rejected");
        const auto output = renderProcessor(supported, 4096);
        expect(energy(output) > 0.0
                && supported.processFailureCount() == 0U,
            "supported host rate did not produce bounded signal");
    }

    const auto contiguous = renderPartitioned(96000.0, 12000, {511}, 777);
    const auto awkward = renderPartitioned(
        96000.0, 12000, {1, 127, 16, 509, 3, 257}, 777);
    expect(contiguous == awkward,
        "96 kHz render changed with host callback partitioning");

    pam::Vst3Processor unsupported;
    expect(unsupported.applyProgramState(program),
        "unsupported-rate program failed");
    unsupported.prepareToPlay(48001.0, 128);
    const auto unsupported_output = renderProcessor(unsupported, 128);
    expect(energy(unsupported_output) == 0.0
            && !unsupported.preparedForAudio()
            && unsupported.getLatencySamples() == 0,
        "unsupported sample rate did not fail to exact silence");

    pam::Vst3Processor oversized;
    expect(oversized.applyProgramState(program),
        "oversized-block program failed");
    oversized.prepareToPlay(44100.0, 8192);
    const auto oversized_output = renderProcessor(oversized, 8193);
    expect(energy(oversized_output) == 0.0
            && oversized.preparedForAudio()
            && oversized.processFailureCount() == 1U,
        "oversized resampled callback did not fail closed");

    pam::Vst3Processor invalid_layout;
    expect(invalid_layout.applyProgramState(program),
        "invalid-layout program failed");
    invalid_layout.prepareToPlay(48000.0, 128);
    juce::AudioBuffer<float> mono{1, 128};
    for (int frame = 0; frame < mono.getNumSamples(); ++frame) {
        mono.setSample(0, frame, 1.0F);
    }
    juce::MidiBuffer no_midi;
    invalid_layout.processBlock(mono, no_midi);
    expect(mono.getMagnitude(0, mono.getNumSamples()) == 0.0F,
        "invalid runtime channel shape did not fail to exact silence");

    pam::Vst3Processor left;
    pam::Vst3Processor right;
    expect(left.applyProgramState(program) && right.applyProgramState(program),
        "multi-instance program failed");
    left.prepareToPlay(48000.0, 1024);
    right.prepareToPlay(48000.0, 1024);
    const auto left_first = renderProcessor(left, 1024);
    const auto right_first = renderProcessor(right, 1024);
    for (int frame = 0; frame < 1024; ++frame) {
        expect(left_first.getSample(0, frame) == right_first.getSample(0, frame)
                && left_first.getSample(1, frame) == right_first.getSample(1, frame),
            "identical instances diverged");
    }
    const auto right_before = right.programState();
    left.setParameterPhysical(
        *pam::vst3ParameterIndexForId("pamp.lane1.voice.pitch"), 72.0F, false);
    left.setSelectedPage(5U);
    left.requestClear();
    static_cast<void>(renderProcessor(left, 256));
    expect(sameProgram(right_before, right.programState()),
        "instance A mutation leaked into instance B");
}

void testUnattachedEditorLifetime() {
    pam::Vst3Processor processor;
    processor.prepareToPlay(48000.0, 128);
    std::unique_ptr<juce::AudioProcessorEditor> editor{processor.createEditor()};
    expect(editor != nullptr && editor->getWidth() >= 1080
            && editor->getHeight() >= 730,
        "source-faithful editor did not construct at a bounded size");
    expect(!editor->isShowing(), "unattached editor unexpectedly opened a window");
    editor.reset();
}

}  // namespace

int main() {
    juce::ScopedJuceInitialiser_GUI gui;
    try {
        testIdentityParametersAndLayout();
        testDirectParityAndLargeBlocks();
        testTimestampedMidiParity();
        testStateRoundTripClearExclusionAndRejection();
        testSupportedRatesAndMultiInstanceIsolation();
        testUnattachedEditorLifetime();
    } catch (const std::exception& error) {
        std::cerr << "pamplist_vst3_processor_tests: " << error.what() << '\n';
        return 1;
    }
    std::cout << "pamplist_vst3_processor_tests: PASS\n";
    return 0;
}
