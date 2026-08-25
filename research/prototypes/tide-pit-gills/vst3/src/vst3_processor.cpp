#include "tidepit/vst3_processor.hpp"

#include <juce_data_structures/juce_data_structures.h>

#include <algorithm>
#include <charconv>
#include <cmath>
#include <limits>
#include <locale>
#include <memory>
#include <sstream>
#include <string>

namespace tidepit {
namespace {

juce::String juceString(std::string_view text)
{
    return juce::String::fromUTF8(text.data(), static_cast<int>(text.size()));
}

constexpr int kMaximumStateBytes = 1024 * 1024;
const juce::Identifier kStateType{"TIDE_PIT_VST3_STATE"};
const juce::Identifier kParametersType{"PARAMETERS"};
const juce::Identifier kParameterType{"PARAMETER"};

template <typename Integer>
[[nodiscard]] bool parseInteger(const juce::var& value, Integer& result) noexcept {
    const auto text = value.toString().toStdString();
    if (text.empty()) return false;
    Integer candidate{};
    const auto parsed = std::from_chars(
        text.data(), text.data() + text.size(), candidate);
    if (parsed.ec != std::errc{} || parsed.ptr != text.data() + text.size()) {
        return false;
    }
    result = candidate;
    return true;
}

[[nodiscard]] bool parseReal(const juce::var& value, double& result) {
    const auto text = value.toString().toStdString();
    if (text.empty()) return false;
    std::istringstream stream{text};
    stream.imbue(std::locale::classic());
    stream >> std::noskipws >> result;
    return stream && stream.peek() == std::char_traits<char>::eof();
}

[[nodiscard]] std::size_t modeParameterIndex(SemanticAction action) noexcept {
    switch (action) {
        case SemanticAction::source_next: return kVst3SourceIndex;
        case SemanticAction::lock_toggle: return kVst3LockIndex;
        case SemanticAction::effect_next: return kVst3EffectIndex;
        case SemanticAction::target_next: return kVst3TargetIndex;
        case SemanticAction::scale_next: return kVst3ScaleIndex;
        default: return kVst3ParameterCount;
    }
}

}  // namespace

class AtomicVst3Parameter final : public juce::AudioProcessorParameterWithID {
public:
    AtomicVst3Parameter(
        std::size_t index,
        const Vst3ParameterDescriptor& descriptor,
        std::atomic<std::uint64_t>& revision)
        : juce::AudioProcessorParameterWithID(
              juce::ParameterID{juceString(descriptor.id), 1},
              juceString(descriptor.name),
              juce::AudioProcessorParameterWithIDAttributes{}
                  .withLabel(juceString(descriptor.unit))
                  .withCategory(juce::AudioProcessorParameter::genericParameter)
                  .withAutomatable(true)
                  .withMeta(false)),
          index_(index),
          descriptor_(descriptor),
          revision_(revision),
          value_(vst3DefaultNormalized(descriptor)) {}

    [[nodiscard]] float getValue() const override {
        return value_.load(std::memory_order_acquire);
    }

    void setValue(float new_value) override {
        if (!std::isfinite(new_value)) return;
        const auto accepted = vst3NormalizePhysical(
            descriptor_, vst3DenormalizeParameter(descriptor_, new_value));
        const auto previous = value_.exchange(accepted, std::memory_order_acq_rel);
        if (previous != accepted) {
            revision_.fetch_add(1U, std::memory_order_release);
        }
    }

    [[nodiscard]] float getDefaultValue() const override {
        return vst3DefaultNormalized(descriptor_);
    }

    [[nodiscard]] int getNumSteps() const override {
        return descriptor_.step_count == 0U
            ? juce::AudioProcessorParameter::getDefaultNumParameterSteps()
            : static_cast<int>(descriptor_.step_count);
    }

    [[nodiscard]] bool isDiscrete() const override {
        return descriptor_.step_count > 1U;
    }

    [[nodiscard]] bool isBoolean() const override {
        return descriptor_.step_count == 2U;
    }

    [[nodiscard]] juce::String getText(
        float normalized_value,
        int maximum_string_length) const override {
        auto result = juce::String{
            vst3FormatParameter(descriptor_, normalized_value)};
        return maximum_string_length > 0
            ? result.substring(0, maximum_string_length)
            : result;
    }

    [[nodiscard]] float getValueForText(const juce::String& source) const override {
        const auto text = source.trim();
        if (descriptor_.step_count > 1U) {
            for (std::uint32_t step = 0U; step < descriptor_.step_count; ++step) {
                const auto normalized = descriptor_.step_count == 1U
                    ? 0.0F
                    : static_cast<float>(step)
                        / static_cast<float>(descriptor_.step_count - 1U);
                if (text.equalsIgnoreCase(
                        juce::String{vst3FormatParameter(descriptor_, normalized)})) {
                    return normalized;
                }
            }
        }
        auto physical = text.getFloatValue();
        if (descriptor_.presentation == Vst3Presentation::unit_percent) {
            physical *= 0.01F;
        }
        return vst3NormalizePhysical(descriptor_, physical);
    }

    [[nodiscard]] std::size_t index() const noexcept { return index_; }

private:
    const std::size_t index_;
    const Vst3ParameterDescriptor& descriptor_;
    std::atomic<std::uint64_t>& revision_;
    std::atomic<float> value_{};
};

Vst3Processor::Vst3Processor()
    : juce::AudioProcessor(
          BusesProperties{}.withOutput(
              "Output", juce::AudioChannelSet::stereo(), true)),
      last_audio_program_(defaultVst3ProgramState()),
      projected_modes_(vst3DiscreteFromProgram(last_audio_program_)) {
    const auto& descriptors = vst3ParameterDescriptors();
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        auto parameter = std::make_unique<AtomicVst3Parameter>(
            index, descriptors[index], parameter_revision_);
        parameters_[index] = parameter.get();
        addParameter(parameter.release());
    }
    publishUiFrame();
    scope_mailbox_.publish(ScopeFrame{});
}

Vst3Processor::~Vst3Processor() = default;

const juce::String Vst3Processor::getName() const { return "Tide Pit"; }

void Vst3Processor::prepareToPlay(
    double sample_rate,
    int maximum_expected_samples) {
    prepared_sample_rate_.store(
        sample_rate > 0.0 && std::isfinite(sample_rate)
            ? static_cast<std::uint32_t>(std::llround(sample_rate))
            : 0U,
        std::memory_order_release);
    last_block_frames_.store(
        maximum_expected_samples > 0
            ? static_cast<std::uint32_t>(maximum_expected_samples)
            : 0U,
        std::memory_order_release);

    const auto mutate_barrier = mutate_request_generation_.load(
        std::memory_order_acquire);
    const auto freeze_barrier = freeze_request_generation_.load(
        std::memory_order_acquire);
    reset_mutate_barrier_.store(mutate_barrier, std::memory_order_release);
    reset_freeze_barrier_.store(freeze_barrier, std::memory_order_release);
    const auto request = reset_request_generation_.fetch_add(
        1U, std::memory_order_acq_rel) + 1U;

    const bool converter_ready = resampler_.prepare(sample_rate);
    const bool supported = converter_ready
        && isBusesLayoutSupported(getBusesLayout());
    const auto latency = supported ? resampler_.latencyHostFrames() : 0U;
    prepared_latency_frames_.store(latency, std::memory_order_release);
    setLatencySamples(static_cast<int>(latency));
    const bool ready = supported && resetCore(mutate_barrier, freeze_barrier);
    applied_reset_generation_ = request;
    prepared_.store(ready, std::memory_order_release);
    if (!ready && supported) {
        process_failures_.fetch_add(1U, std::memory_order_relaxed);
    }
}

void Vst3Processor::releaseResources() {
    prepared_.store(false, std::memory_order_release);
    resampler_.release();
    prepared_latency_frames_.store(0U, std::memory_order_release);
    setLatencySamples(0);
    reset_mutate_barrier_.store(
        mutate_request_generation_.load(std::memory_order_acquire),
        std::memory_order_release);
    reset_freeze_barrier_.store(
        freeze_request_generation_.load(std::memory_order_acquire),
        std::memory_order_release);
    reset_request_generation_.fetch_add(1U, std::memory_order_release);
}

bool Vst3Processor::isBusesLayoutSupported(const BusesLayout& layouts) const {
    return layouts.getMainInputChannelSet().isDisabled()
        && layouts.getMainOutputChannelSet() == juce::AudioChannelSet::stereo();
}

void Vst3Processor::processBlock(
    juce::AudioBuffer<float>& buffer,
    juce::MidiBuffer& midi_messages) {
    juce::ScopedNoDenormals no_denormals;
    buffer.clear();
    const auto frame_count = buffer.getNumSamples();
    last_block_frames_.store(
        frame_count > 0 ? static_cast<std::uint32_t>(frame_count) : 0U,
        std::memory_order_relaxed);
    if (!prepared_.load(std::memory_order_acquire)
        || frame_count <= 0
        || buffer.getNumChannels() < 2) {
        midi_messages.clear();
        return;
    }

    applyPendingReset();
    if (!prepared_.load(std::memory_order_acquire)) {
        midi_messages.clear();
        return;
    }

    schuss::instrument_lab::FixedRateStereoResampler::BlockPlan resampled_plan{};
    const auto resampled = !resampler_.bypassed();
    if (resampled && !resampler_.beginBlock(
            static_cast<std::uint32_t>(frame_count), resampled_plan)) {
        process_failures_.fetch_add(1U, std::memory_order_relaxed);
        publishUiFrame();
        midi_messages.clear();
        return;
    }

    event_count_ = 0U;
    const auto desired = captureCoherentProgram(last_audio_program_);
    auto applied = last_audio_program_;
    appendProgramEvents(desired, applied);
    appendOneShotEvents();
    appendMidiEvents(
        midi_messages,
        static_cast<std::uint32_t>(frame_count),
        applied);

    if (!resampled) {
        bridge_.process(
            core_,
            buffer.getWritePointer(0),
            buffer.getWritePointer(1),
            static_cast<std::uint32_t>(frame_count),
            events_.data(),
            event_count_);
    } else {
        enqueueResampledEvents(resampled_plan);
        if (resampled_plan.source_frames != 0U) {
            collectResampledEvents(resampled_plan);
            bridge_.process(
                core_,
                resampler_.sourceLeft(),
                resampler_.sourceRight(),
                resampled_plan.source_frames,
                events_.data(),
                event_count_);
        }
        if (!resampler_.finishBlock(
                buffer.getWritePointer(0),
                buffer.getWritePointer(1),
                static_cast<std::uint32_t>(frame_count))) {
            process_failures_.fetch_add(1U, std::memory_order_relaxed);
        }
    }
    last_audio_program_ = applied;

    for (int frame = 0; frame < frame_count; ++frame) {
        if (const auto* completed = scope_accumulator_.pushSample(
                buffer.getSample(0, frame),
                buffer.getSample(1, frame));
            completed != nullptr) {
            scope_mailbox_.publish(*completed);
        }
    }
    publishUiFrame();
    midi_messages.clear();
}

bool Vst3Processor::hasEditor() const { return true; }

juce::AudioProcessorEditor* Vst3Processor::createEditor() {
    return createTidePitVst3Editor(*this);
}

double Vst3Processor::getTailLengthSeconds() const { return 0.0; }
bool Vst3Processor::acceptsMidi() const { return true; }
bool Vst3Processor::producesMidi() const { return false; }
bool Vst3Processor::isMidiEffect() const { return false; }

int Vst3Processor::getNumPrograms() { return 1; }
int Vst3Processor::getCurrentProgram() { return 0; }
void Vst3Processor::setCurrentProgram(int) {}
const juce::String Vst3Processor::getProgramName(int) { return {}; }
void Vst3Processor::changeProgramName(int, const juce::String&) {}

void Vst3Processor::getStateInformation(juce::MemoryBlock& destination_data) {
    const auto program = programState();
    juce::ValueTree root{kStateType};
    root.setProperty("schema", juce::String{kVst3StateSchema.data()}, nullptr);
    root.setProperty(
        "schemaVersion", static_cast<int>(kVst3StateSchemaVersion), nullptr);
    root.setProperty(
        "parameterContract",
        juce::String{std::to_string(vst3ParameterContractFingerprint())},
        nullptr);

    juce::ValueTree parameter_values{kParametersType};
    const auto& descriptors = vst3ParameterDescriptors();
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        juce::ValueTree parameter{kParameterType};
        parameter.setProperty(
            "id", juceString(descriptors[index].id), nullptr);
        parameter.setProperty(
            "value", static_cast<double>(program.normalized[index]), nullptr);
        parameter_values.addChild(parameter, -1, nullptr);
    }
    root.addChild(parameter_values, -1, nullptr);

    const auto serialized = root.toXmlString();
    destination_data.reset();
    destination_data.append(
        serialized.toRawUTF8(), serialized.getNumBytesAsUTF8());
}

void Vst3Processor::setStateInformation(const void* data, int size_in_bytes) {
    if (data == nullptr || size_in_bytes <= 0
        || size_in_bytes > kMaximumStateBytes) {
        rejected_states_.fetch_add(1U, std::memory_order_relaxed);
        return;
    }
    const auto serialized = juce::String::fromUTF8(
        static_cast<const char*>(data), size_in_bytes);
    if (serialized.getNumBytesAsUTF8()
        != static_cast<std::size_t>(size_in_bytes)) {
        rejected_states_.fetch_add(1U, std::memory_order_relaxed);
        return;
    }
    const auto root = juce::ValueTree::fromXml(serialized);
    auto candidate = defaultVst3ProgramState();
    if (!parseState(root, candidate) || !applyProgramState(candidate)) {
        rejected_states_.fetch_add(1U, std::memory_order_relaxed);
    }
}

Vst3ProgramState Vst3Processor::programState() const noexcept {
    return captureCoherentProgram(defaultVst3ProgramState());
}

Controls Vst3Processor::requestedControls() const noexcept {
    return vst3ControlsFromProgram(programState());
}

Vst3UiFrame Vst3Processor::uiFrame() const noexcept {
    last_reader_ui_ = ui_mailbox_.load(last_reader_ui_);
    return last_reader_ui_;
}

Snapshot Vst3Processor::acceptedSnapshot() const noexcept {
    return uiFrame().snapshot;
}

ScopeFrame Vst3Processor::latestScope() const noexcept {
    last_reader_scope_ = scope_mailbox_.load(last_reader_scope_);
    return last_reader_scope_;
}

float Vst3Processor::parameterNormalized(std::size_t index) const noexcept {
    return index < parameters_.size() && parameters_[index] != nullptr
        ? parameters_[index]->getValue()
        : 0.0F;
}

float Vst3Processor::parameterPhysical(std::size_t index) const noexcept {
    const auto& descriptors = vst3ParameterDescriptors();
    return index < descriptors.size()
        ? vst3DenormalizeParameter(descriptors[index], parameterNormalized(index))
        : 0.0F;
}

void Vst3Processor::beginParameterGesture(std::size_t index) {
    if (index < parameters_.size() && parameters_[index] != nullptr) {
        parameters_[index]->beginChangeGesture();
    }
}

void Vst3Processor::setParameterPhysical(
    std::size_t index,
    float physical,
    bool notify_host) {
    const auto& descriptors = vst3ParameterDescriptors();
    if (index >= descriptors.size() || parameters_[index] == nullptr
        || !std::isfinite(physical)) {
        return;
    }
    const auto normalized = vst3NormalizePhysical(descriptors[index], physical);
    if (notify_host) {
        parameters_[index]->setValueNotifyingHost(normalized);
    } else {
        parameters_[index]->setValue(normalized);
    }
}

void Vst3Processor::endParameterGesture(std::size_t index) {
    if (index < parameters_.size() && parameters_[index] != nullptr) {
        parameters_[index]->endChangeGesture();
    }
}

void Vst3Processor::requestAction(SemanticAction action) noexcept {
    if (action == SemanticAction::mutate) {
        mutate_request_generation_.fetch_add(1U, std::memory_order_release);
    } else if (action == SemanticAction::capture_toggle) {
        freeze_request_generation_.fetch_add(1U, std::memory_order_release);
    }
}

bool Vst3Processor::applyProgramState(
    const Vst3ProgramState& program) noexcept {
    if (!validVst3ProgramState(program)) return false;
    state_transaction_sequence_.fetch_add(1U, std::memory_order_acq_rel);
    for (std::size_t index = 0; index < parameters_.size(); ++index) {
        parameters_[index]->setValue(program.normalized[index]);
    }
    parameter_revision_.fetch_add(1U, std::memory_order_release);
    state_transaction_sequence_.fetch_add(1U, std::memory_order_release);

    reset_mutate_barrier_.store(
        mutate_request_generation_.load(std::memory_order_acquire),
        std::memory_order_release);
    reset_freeze_barrier_.store(
        freeze_request_generation_.load(std::memory_order_acquire),
        std::memory_order_release);
    reset_request_generation_.fetch_add(1U, std::memory_order_release);
    accepted_states_.fetch_add(1U, std::memory_order_relaxed);
    return true;
}

bool Vst3Processor::preparedForAudio() const noexcept {
    return prepared_.load(std::memory_order_acquire);
}

juce::String Vst3Processor::statusText() const {
    const auto host_rate = prepared_sample_rate_.load(std::memory_order_acquire);
    auto result = preparedForAudio()
        ? juce::String{"VST3 READY | 48 KHZ CORE | "}
            + (host_rate == kReferenceSampleRate ? "BYPASS" : "SRC")
        : juce::String{"SILENT - UNSUPPORTED HOST RATE OR LAYOUT"};
    result += " | HOST "
        + juce::String{static_cast<int>(host_rate)}
        + " HZ";
    result += " | LATENCY "
        + juce::String{static_cast<int>(prepared_latency_frames_.load(
            std::memory_order_acquire))};
    result += " | BLOCK "
        + juce::String{static_cast<int>(last_block_frames_.load(
            std::memory_order_acquire))};
    const auto frame = uiFrame();
    result += " | SAMPLE " + juce::String{frame.snapshot.absolute_sample};
    result += " | MIDI "
        + juce::String{frame.midi_diagnostics.accepted_messages}
        + "/" + juce::String{frame.midi_diagnostics.raw_messages};
    const auto drops = frame.bridge_event_drops + frame.processor_event_drops
        + frame.midi_diagnostics.dropped_events;
    if (drops != 0U) result += " | DROP " + juce::String{drops};
    if (processFailureCount() != 0U) {
        result += " | PROCESS ERR " + juce::String{processFailureCount()};
    }
    if (rejectedStateCount() != 0U) {
        result += " | STATE REJECT " + juce::String{rejectedStateCount()};
    }
    return result;
}

std::uint64_t Vst3Processor::processFailureCount() const noexcept {
    return process_failures_.load(std::memory_order_acquire);
}

std::uint64_t Vst3Processor::acceptedStateCount() const noexcept {
    return accepted_states_.load(std::memory_order_acquire);
}

std::uint64_t Vst3Processor::rejectedStateCount() const noexcept {
    return rejected_states_.load(std::memory_order_acquire);
}

std::uint64_t Vst3Processor::processorEventDropCount() const noexcept {
    return processor_event_drops_.load(std::memory_order_acquire);
}

Vst3ProgramState Vst3Processor::captureCoherentProgram(
    Vst3ProgramState fallback) const noexcept {
    for (int attempt = 0; attempt < 6; ++attempt) {
        const auto transaction_before = state_transaction_sequence_.load(
            std::memory_order_acquire);
        if ((transaction_before & 1U) != 0U) continue;
        const auto revision_before = parameter_revision_.load(
            std::memory_order_acquire);
        Vst3ProgramState candidate{};
        for (std::size_t index = 0; index < parameters_.size(); ++index) {
            candidate.normalized[index] = parameters_[index]->getValue();
        }
        const auto revision_after = parameter_revision_.load(
            std::memory_order_acquire);
        const auto transaction_after = state_transaction_sequence_.load(
            std::memory_order_acquire);
        if (transaction_before == transaction_after
            && (transaction_after & 1U) == 0U
            && revision_before == revision_after
            && validVst3ProgramState(candidate)) {
            return candidate;
        }
    }
    return validVst3ProgramState(fallback)
        ? fallback
        : defaultVst3ProgramState();
}

bool Vst3Processor::resetCore(
    std::uint64_t mutate_barrier,
    std::uint64_t freeze_barrier) noexcept {
    midi_adapter_.reset();
    resampler_.reset();
    bridge_.reset();
    scope_accumulator_.reset();
    scope_mailbox_.publish(ScopeFrame{});
    event_count_ = 0U;
    pending_resampled_event_count_ = 0U;
    ingress_sequence_ = 0U;
    last_audio_program_ = defaultVst3ProgramState();
    projected_modes_ = vst3DiscreteFromProgram(last_audio_program_);
    applied_mutate_generation_ = mutate_barrier;
    applied_freeze_generation_ = freeze_barrier;
    const auto ready = core_.prepare(
        kReferenceSampleRate, kReferenceQuantumFrames);
    publishUiFrame();
    return ready;
}

void Vst3Processor::applyPendingReset() noexcept {
    const auto requested = reset_request_generation_.load(std::memory_order_acquire);
    if (requested == applied_reset_generation_) return;
    const auto ready = resetCore(
        reset_mutate_barrier_.load(std::memory_order_acquire),
        reset_freeze_barrier_.load(std::memory_order_acquire));
    applied_reset_generation_ = requested;
    prepared_.store(ready, std::memory_order_release);
    if (!ready) process_failures_.fetch_add(1U, std::memory_order_relaxed);
}

bool Vst3Processor::appendEvent(
    SemanticAction action,
    double value,
    std::uint32_t sample_offset) noexcept {
    if (event_count_ == events_.size()) {
        processor_event_drops_.fetch_add(1U, std::memory_order_relaxed);
        return false;
    }
    events_[event_count_++] = {
        sample_offset,
        ingress_sequence_++,
        action,
        value,
    };
    return true;
}

void Vst3Processor::appendProgramEvents(
    const Vst3ProgramState& desired,
    Vst3ProgramState& applied) noexcept {
    constexpr std::array<SemanticAction, 11U> continuous_actions{{
        SemanticAction::set_stage_1,
        SemanticAction::set_stage_2,
        SemanticAction::set_stage_3,
        SemanticAction::set_stage_4,
        SemanticAction::set_rate,
        SemanticAction::set_memory,
        SemanticAction::set_material,
        SemanticAction::set_position,
        SemanticAction::set_fx_a,
        SemanticAction::set_fx_b,
        SemanticAction::set_root,
    }};
    const auto& descriptors = vst3ParameterDescriptors();
    for (std::size_t index = 0; index < continuous_actions.size(); ++index) {
        if (desired.normalized[index] == applied.normalized[index]) continue;
        const auto value = vst3DenormalizeParameter(
            descriptors[index], desired.normalized[index]);
        if (appendEvent(continuous_actions[index], value, 0U)) {
            applied.normalized[index] = desired.normalized[index];
        }
    }

    const auto desired_modes = vst3DiscreteFromProgram(desired);
    const auto scheduleCycle = [this, &applied, &descriptors](
                                   std::size_t parameter_index,
                                   int desired_value,
                                   int& projected_value,
                                   int count,
                                   SemanticAction action) {
        auto remaining = (desired_value - projected_value + count) % count;
        while (remaining-- > 0) {
            if (!appendEvent(action, 0.0, 0U)) break;
            projected_value = (projected_value + 1) % count;
        }
        applied.normalized[parameter_index] = vst3NormalizePhysical(
            descriptors[parameter_index], static_cast<float>(projected_value));
    };

    auto projected_source = static_cast<int>(projected_modes_.source);
    scheduleCycle(
        kVst3SourceIndex,
        static_cast<int>(desired_modes.source),
        projected_source,
        3,
        SemanticAction::source_next);
    projected_modes_.source = static_cast<SourceMode>(projected_source);

    if (desired_modes.locked != projected_modes_.locked
        && appendEvent(SemanticAction::lock_toggle, 0.0, 0U)) {
        projected_modes_.locked = !projected_modes_.locked;
    }
    applied.normalized[kVst3LockIndex] = vst3NormalizePhysical(
        descriptors[kVst3LockIndex], projected_modes_.locked ? 1.0F : 0.0F);

    auto projected_effect = static_cast<int>(projected_modes_.effect);
    scheduleCycle(
        kVst3EffectIndex,
        static_cast<int>(desired_modes.effect),
        projected_effect,
        3,
        SemanticAction::effect_next);
    projected_modes_.effect = static_cast<EffectMode>(projected_effect);

    auto projected_target = static_cast<int>(projected_modes_.target);
    scheduleCycle(
        kVst3TargetIndex,
        static_cast<int>(desired_modes.target),
        projected_target,
        4,
        SemanticAction::target_next);
    projected_modes_.target = static_cast<WaveTarget>(projected_target);

    auto projected_scale = static_cast<int>(projected_modes_.scale);
    scheduleCycle(
        kVst3ScaleIndex,
        static_cast<int>(desired_modes.scale),
        projected_scale,
        4,
        SemanticAction::scale_next);
    projected_modes_.scale = static_cast<ScaleMode>(projected_scale);
}

void Vst3Processor::appendOneShotEvents() noexcept {
    const auto mutate_requested = mutate_request_generation_.load(
        std::memory_order_acquire);
    while (applied_mutate_generation_ != mutate_requested) {
        if (!appendEvent(SemanticAction::mutate, 0.0, 0U)) break;
        ++applied_mutate_generation_;
    }
    const auto freeze_requested = freeze_request_generation_.load(
        std::memory_order_acquire);
    while (applied_freeze_generation_ != freeze_requested) {
        if (!appendEvent(SemanticAction::capture_toggle, 0.0, 0U)) break;
        ++applied_freeze_generation_;
    }
}

void Vst3Processor::appendMidiEvents(
    const juce::MidiBuffer& midi_messages,
    std::uint32_t block_frames,
    Vst3ProgramState& applied) noexcept {
    const auto adapted = midi_adapter_.adapt(midi_messages, block_frames);
    if (adapted.dropped_events != 0U) {
        processor_event_drops_.fetch_add(
            adapted.dropped_events, std::memory_order_relaxed);
    }
    const auto& descriptors = vst3ParameterDescriptors();
    for (std::size_t index = 0; index < adapted.event_count; ++index) {
        const auto& source = adapted.events[index];
        if (!appendEvent(source.action, source.value, source.sample_offset)) continue;
        if (const auto parameter = vst3ParameterIndexForAction(source.action)) {
            const auto normalized = vst3NormalizePhysical(
                descriptors[*parameter], static_cast<float>(source.value));
            applied.normalized[*parameter] = normalized;
            syncParameterFromAudio(*parameter, normalized);
            continue;
        }
        if (vst3CycleProgramForAction(applied, source.action)) {
            projected_modes_ = vst3DiscreteFromProgram(applied);
            const auto parameter = modeParameterIndex(source.action);
            if (parameter < kVst3ParameterCount) {
                syncParameterFromAudio(parameter, applied.normalized[parameter]);
            }
        }
    }
}

void Vst3Processor::enqueueResampledEvents(
    const schuss::instrument_lab::FixedRateStereoResampler::BlockPlan& plan
) noexcept {
    for (std::size_t index = 0U; index < event_count_; ++index) {
        if (pending_resampled_event_count_
                == pending_resampled_events_.size()) {
            processor_event_drops_.fetch_add(1U, std::memory_order_relaxed);
            continue;
        }
        const auto& event = events_[index];
        pending_resampled_events_[pending_resampled_event_count_++] = {
            plan.source_frame_start
                + resampler_.sourceOffsetForHostOffset(event.sample_offset),
            event.ingress_sequence,
            event.action,
            event.value,
        };
    }
    event_count_ = 0U;
}

void Vst3Processor::collectResampledEvents(
    const schuss::instrument_lab::FixedRateStereoResampler::BlockPlan& plan
) noexcept {
    event_count_ = 0U;
    std::size_t consumed = 0U;
    while (consumed < pending_resampled_event_count_
           && event_count_ < events_.size()
           && pending_resampled_events_[consumed].absolute_source_frame
                < plan.source_frame_end) {
        const auto& pending = pending_resampled_events_[consumed++];
        const auto relative = pending.absolute_source_frame
                <= plan.source_frame_start
            ? 0U
            : static_cast<std::uint32_t>(
                pending.absolute_source_frame - plan.source_frame_start);
        events_[event_count_++] = {
            relative,
            pending.ingress_sequence,
            pending.action,
            pending.value,
        };
    }
    for (std::size_t index = consumed;
         index < pending_resampled_event_count_;
         ++index) {
        pending_resampled_events_[index - consumed]
            = pending_resampled_events_[index];
    }
    pending_resampled_event_count_ -= consumed;
}

void Vst3Processor::syncParameterFromAudio(
    std::size_t index,
    float normalized) noexcept {
    if (index < parameters_.size() && parameters_[index] != nullptr) {
        parameters_[index]->setValue(normalized);
    }
}

void Vst3Processor::publishUiFrame() noexcept {
    ui_mailbox_.publish({
        core_.snapshot(),
        core_.diagnostics(),
        midi_adapter_.diagnostics(),
        bridge_.adapter().droppedEvents(),
        processor_event_drops_.load(std::memory_order_relaxed),
    });
}

bool Vst3Processor::parseState(
    const juce::ValueTree& root,
    Vst3ProgramState& program) const {
    std::int64_t schema_version = 0;
    if (!root.isValid() || root.getType() != kStateType
        || root.getNumProperties() != 3
        || root.getNumChildren() != 1
        || root.getProperty("schema").toString()
            != juce::String{kVst3StateSchema.data()}
        || !parseInteger(root.getProperty("schemaVersion"), schema_version)
        || schema_version != static_cast<int>(kVst3StateSchemaVersion)
        || root.getProperty("parameterContract").toString()
            != juce::String{std::to_string(vst3ParameterContractFingerprint())}) {
        return false;
    }

    const auto values = root.getChild(0);
    if (values.getType() != kParametersType
        || values.getNumProperties() != 0
        || values.getNumChildren() != static_cast<int>(kVst3ParameterCount)) {
        return false;
    }
    std::array<bool, kVst3ParameterCount> seen{};
    Vst3ProgramState candidate{};
    for (int child_index = 0; child_index < values.getNumChildren(); ++child_index) {
        const auto child = values.getChild(child_index);
        if (child.getType() != kParameterType
            || child.getNumProperties() != 2
            || child.getNumChildren() != 0) {
            return false;
        }
        const auto id = child.getProperty("id").toString().toStdString();
        const auto index = vst3ParameterIndexForId(id);
        double normalized = 0.0;
        if (!index.has_value() || seen[*index]
            || !parseReal(child.getProperty("value"), normalized)
            || !std::isfinite(normalized)
            || normalized < 0.0 || normalized > 1.0) {
            return false;
        }
        candidate.normalized[*index] = static_cast<float>(normalized);
        seen[*index] = true;
    }
    if (!std::all_of(seen.begin(), seen.end(), [](bool value) { return value; })
        || !validVst3ProgramState(candidate)) {
        return false;
    }
    program = candidate;
    return true;
}

}  // namespace tidepit
