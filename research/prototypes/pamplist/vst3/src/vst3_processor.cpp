#include "schuss/pamplist/vst3_processor.hpp"

#include <juce_data_structures/juce_data_structures.h>

#include <algorithm>
#include <charconv>
#include <cmath>
#include <limits>
#include <locale>
#include <memory>
#include <sstream>
#include <string>

namespace schuss::pamplist {
namespace {

constexpr float kQ27ToFloat = 1.0F / 134217728.0F;
constexpr int kMaximumStateBytes = 1024 * 1024;
const juce::Identifier kStateType{"PAMPLIST_VST3_STATE"};
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

}  // namespace

class AtomicVst3Parameter final : public juce::AudioProcessorParameterWithID {
public:
    AtomicVst3Parameter(
        std::size_t index,
        const Vst3ParameterDescriptor& descriptor,
        std::atomic<std::uint64_t>& revision)
        : juce::AudioProcessorParameterWithID(
              juce::ParameterID{descriptor.id, 1},
              descriptor.name,
              juce::AudioProcessorParameterWithIDAttributes{}
                  .withLabel(descriptor.unit)
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
        auto result = juce::String{vst3FormatParameter(
            descriptor_, normalized_value)};
        return maximum_string_length > 0
            ? result.substring(0, maximum_string_length)
            : result;
    }

    [[nodiscard]] float getValueForText(const juce::String& source) const override {
        const auto text = source.trim();
        if (descriptor_.presentation == PresentationKind::trigger_switch) {
            if (text.equalsIgnoreCase("on") || text.equalsIgnoreCase("true")
                || text.equalsIgnoreCase("run")) {
                return 1.0F;
            }
            if (text.equalsIgnoreCase("off") || text.equalsIgnoreCase("false")
                || text.equalsIgnoreCase("stop")) {
                return 0.0F;
            }
        }
        if (descriptor_.presentation == PresentationKind::rate) {
            for (std::size_t index = 0; index < rateTable().size(); ++index) {
                const auto& rate = rateTable()[index];
                const auto label = juce::String{static_cast<int>(rate.numerator)}
                    + "/" + juce::String{static_cast<int>(rate.denominator)};
                if (text == label) {
                    return vst3NormalizePhysical(
                        descriptor_, static_cast<float>(index));
                }
            }
        }
        auto physical = text.getFloatValue();
        if (descriptor_.presentation == PresentationKind::unit_percent
            || descriptor_.presentation == PresentationKind::chance
            || descriptor_.presentation == PresentationKind::depth
            || descriptor_.presentation == PresentationKind::signed_percent) {
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
      last_audio_program_(defaultVst3ProgramState()) {
    const auto& descriptors = vst3ParameterDescriptors();
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        auto parameter = std::make_unique<AtomicVst3Parameter>(
            index, descriptors[index], parameter_revision_);
        parameters_[index] = parameter.get();
        addParameter(parameter.release());
    }
    last_reader_snapshot_ = core_.snapshot();
    accepted_mailbox_.publish(last_reader_snapshot_);
}

Vst3Processor::~Vst3Processor() = default;

const juce::String Vst3Processor::getName() const { return "Pamplist"; }

void Vst3Processor::prepareToPlay(
    double sample_rate,
    int maximum_expected_samples) {
    const bool converter_ready = resampler_.prepare(sample_rate);
    const bool supported = converter_ready
        && isBusesLayoutSupported(getBusesLayout());
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
    reset_clear_barrier_.store(
        clear_request_generation_.load(std::memory_order_acquire),
        std::memory_order_release);
    reset_request_generation_.fetch_add(1U, std::memory_order_release);
    const auto latency = supported ? resampler_.latencyHostFrames() : 0U;
    prepared_latency_frames_.store(latency, std::memory_order_release);
    setLatencySamples(static_cast<int>(latency));
    prepared_.store(supported, std::memory_order_release);
}

void Vst3Processor::releaseResources() {
    prepared_.store(false, std::memory_order_release);
    core_.panic();
    resampler_.release();
    prepared_latency_frames_.store(0U, std::memory_order_release);
    setLatencySamples(0);
    reset_clear_barrier_.store(
        clear_request_generation_.load(std::memory_order_acquire),
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
    schuss::instrument_lab::FixedRateStereoResampler::BlockPlan resampled_plan{};
    const auto resampled = !resampler_.bypassed();
    if (resampled && !resampler_.beginBlock(
            static_cast<std::uint32_t>(frame_count), resampled_plan)) {
        process_failures_.fetch_add(1U, std::memory_order_relaxed);
        midi_messages.clear();
        return;
    }
    auto program = captureCoherentProgram(last_audio_program_);
    auto controls = vst3ControlsFromProgram(program, effect_clear_generation_);
    applyPendingClear(controls);

    bool midi_changed = false;
    int rendered_through = 0;
    std::uint32_t rendered_source = 0U;
    for (const auto metadata : midi_messages) {
        const auto position = std::clamp(
            metadata.samplePosition, rendered_through, frame_count);
        if (resampled) {
            const auto source_position = resampler_.sourceOffsetForHostOffset(
                static_cast<std::uint32_t>(position));
            if (source_position > rendered_source) {
                static_cast<void>(renderSourceRange(
                    resampler_.sourceLeft(),
                    resampler_.sourceRight(),
                    rendered_source,
                    source_position - rendered_source,
                    controls));
                rendered_source = source_position;
            }
            rendered_through = position;
        } else if (position > rendered_through) {
            static_cast<void>(renderRange(
                buffer, rendered_through, position - rendered_through, controls));
            rendered_through = position;
        }

        received_midi_.fetch_add(1U, std::memory_order_relaxed);
        const auto message = metadata.getMessage();
        if (!message.isController()) continue;
        const auto result = controller_.handleCc(
            controls,
            message.getChannel(),
            message.getControllerNumber(),
            message.getControllerValue());
        if (result.accepted()) {
            mapped_midi_.fetch_add(1U, std::memory_order_relaxed);
        }
        if (result.dispatches()) {
            controls = sanitizeControls(controls);
            midi_changed = true;
        }
    }
    if (resampled && rendered_source < resampled_plan.source_frames) {
        static_cast<void>(renderSourceRange(
            resampler_.sourceLeft(),
            resampler_.sourceRight(),
            rendered_source,
            resampled_plan.source_frames - rendered_source,
            controls));
    } else if (!resampled && rendered_through < frame_count) {
        static_cast<void>(renderRange(
            buffer, rendered_through, frame_count - rendered_through, controls));
    }
    if (resampled && !resampler_.finishBlock(
            buffer.getWritePointer(0),
            buffer.getWritePointer(1),
            static_cast<std::uint32_t>(frame_count))) {
        process_failures_.fetch_add(1U, std::memory_order_relaxed);
    }
    midi_messages.clear();

    effect_clear_generation_ = controls.effect_clear_generation;
    last_audio_program_ = vst3ProgramFromControls(controls);
    if (midi_changed) syncParametersFromControls(controls);
}

bool Vst3Processor::hasEditor() const { return true; }

juce::AudioProcessorEditor* Vst3Processor::createEditor() {
    return createPamplistVst3Editor(*this);
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
    root.setProperty("seed", static_cast<juce::int64>(program.seed), nullptr);
    root.setProperty("page", static_cast<int>(program.selected_page), nullptr);
    root.setProperty(
        "mode", static_cast<int>(program.lane_control_mode), nullptr);

    juce::ValueTree parameter_values{kParametersType};
    const auto& descriptors = vst3ParameterDescriptors();
    for (std::size_t index = 0; index < descriptors.size(); ++index) {
        juce::ValueTree parameter{kParameterType};
        parameter.setProperty(
            "id", juce::String{descriptors[index].id}, nullptr);
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

Snapshot Vst3Processor::acceptedSnapshot() const noexcept {
    last_reader_snapshot_ = accepted_mailbox_.load(last_reader_snapshot_);
    return last_reader_snapshot_;
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

bool Vst3Processor::setSurfacePhysical(
    SurfaceRow row,
    std::size_t column,
    float physical,
    bool notify_host) {
    const auto controls = requestedControls();
    const auto index = vst3ParameterIndexForSurface(controls, row, column);
    if (!index.has_value()) return false;
    setParameterPhysical(*index, physical, notify_host);
    return true;
}

void Vst3Processor::setSelectedPage(std::uint8_t page) noexcept {
    if (page >= kPageCount) return;
    const auto previous = selected_page_.exchange(page, std::memory_order_acq_rel);
    if (previous != page) parameter_revision_.fetch_add(1U, std::memory_order_release);
}

void Vst3Processor::setLaneControlMode(LaneControlMode mode) noexcept {
    if (mode != LaneControlMode::voice && mode != LaneControlMode::motion) return;
    const auto value = static_cast<std::uint8_t>(mode);
    const auto previous = lane_mode_.exchange(value, std::memory_order_acq_rel);
    if (previous != value) parameter_revision_.fetch_add(1U, std::memory_order_release);
}

void Vst3Processor::requestClear() noexcept {
    clear_request_generation_.fetch_add(1U, std::memory_order_release);
}

bool Vst3Processor::applyProgramState(const Vst3ProgramState& program) noexcept {
    if (!validVst3ProgramState(program)) return false;
    state_transaction_sequence_.fetch_add(1U, std::memory_order_acq_rel);
    for (std::size_t index = 0; index < parameters_.size(); ++index) {
        parameters_[index]->setValue(program.normalized[index]);
    }
    seed_.store(program.seed, std::memory_order_relaxed);
    selected_page_.store(program.selected_page, std::memory_order_relaxed);
    lane_mode_.store(
        static_cast<std::uint8_t>(program.lane_control_mode),
        std::memory_order_relaxed);
    parameter_revision_.fetch_add(1U, std::memory_order_release);
    state_transaction_sequence_.fetch_add(1U, std::memory_order_release);
    reset_clear_barrier_.store(
        clear_request_generation_.load(std::memory_order_acquire),
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
    juce::String result = preparedForAudio()
        ? juce::String{"VST3 READY  |  48 KHZ CORE  |  "}
            + (host_rate == kSampleRateHz ? "BYPASS" : "SRC")
        : juce::String{"SILENT - UNSUPPORTED HOST RATE OR LAYOUT"};
    result += "  |  HOST "
        + juce::String{static_cast<int>(host_rate)}
        + " HZ";
    result += "  |  LATENCY "
        + juce::String{static_cast<int>(prepared_latency_frames_.load(
            std::memory_order_acquire))};
    result += "  |  BLOCK "
        + juce::String{static_cast<int>(last_block_frames_.load(
            std::memory_order_acquire))};
    const auto snapshot = acceptedSnapshot();
    result += "  |  FRAME " + juce::String{snapshot.absolute_frame};
    result += "  |  TRIG " + juce::String{snapshot.diagnostics.trigger_count};
    result += "  |  MIDI "
        + juce::String{mappedMidiCount()} + "/"
        + juce::String{receivedMidiCount()};
    if (processFailureCount() != 0U) {
        result += "  |  PROCESS ERR " + juce::String{processFailureCount()};
    }
    if (rejectedStateCount() != 0U) {
        result += "  |  STATE REJECT " + juce::String{rejectedStateCount()};
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

std::uint64_t Vst3Processor::receivedMidiCount() const noexcept {
    return received_midi_.load(std::memory_order_acquire);
}

std::uint64_t Vst3Processor::mappedMidiCount() const noexcept {
    return mapped_midi_.load(std::memory_order_acquire);
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
        candidate.seed = seed_.load(std::memory_order_acquire);
        candidate.selected_page = selected_page_.load(std::memory_order_acquire);
        candidate.lane_control_mode = static_cast<LaneControlMode>(
            lane_mode_.load(std::memory_order_acquire));
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

void Vst3Processor::publishFreshSnapshot() noexcept {
    accepted_mailbox_.publish(core_.snapshot());
}

void Vst3Processor::applyPendingReset() noexcept {
    const auto requested = reset_request_generation_.load(std::memory_order_acquire);
    if (requested == applied_reset_generation_) return;
    core_.reset();
    controller_.reset();
    resampler_.reset();
    effect_clear_generation_ = 0U;
    applied_clear_request_generation_ = reset_clear_barrier_.load(
        std::memory_order_acquire);
    applied_reset_generation_ = requested;
    last_audio_program_ = captureCoherentProgram(last_audio_program_);
    publishFreshSnapshot();
}

void Vst3Processor::applyPendingClear(Controls& controls) noexcept {
    const auto requested = clear_request_generation_.load(std::memory_order_acquire);
    if (requested != applied_clear_request_generation_) {
        ++effect_clear_generation_;
        applied_clear_request_generation_ = requested;
    }
    controls.effect_clear_generation = effect_clear_generation_;
}

void Vst3Processor::syncParametersFromControls(const Controls& controls) noexcept {
    const auto program = vst3ProgramFromControls(controls);
    for (std::size_t index = 0; index < parameters_.size(); ++index) {
        parameters_[index]->setValue(program.normalized[index]);
    }
    seed_.store(program.seed, std::memory_order_relaxed);
    selected_page_.store(program.selected_page, std::memory_order_relaxed);
    lane_mode_.store(
        static_cast<std::uint8_t>(program.lane_control_mode),
        std::memory_order_relaxed);
    parameter_revision_.fetch_add(1U, std::memory_order_release);
}

bool Vst3Processor::renderRange(
    juce::AudioBuffer<float>& buffer,
    int start_frame,
    int frame_count,
    const Controls& controls) noexcept {
    bool success = true;
    int offset = 0;
    while (offset < frame_count) {
        const auto chunk = std::min<int>(
            frame_count - offset,
            static_cast<int>(kMaximumHostBlockFrames));
        ProcessReport report{};
        if (!core_.process(
                controls,
                main_q27_.data(),
                auxiliary_q27_.data(),
                static_cast<std::size_t>(chunk),
                &report)) {
            process_failures_.fetch_add(1U, std::memory_order_relaxed);
            success = false;
            offset += chunk;
            continue;
        }
        auto* left = buffer.getWritePointer(0, start_frame + offset);
        auto* right = buffer.getWritePointer(1, start_frame + offset);
        for (int frame = 0; frame < chunk; ++frame) {
            left[frame] = static_cast<float>(main_q27_[frame]) * kQ27ToFloat;
            right[frame] = static_cast<float>(auxiliary_q27_[frame]) * kQ27ToFloat;
        }
        accepted_mailbox_.publish(report.snapshot);
        offset += chunk;
    }
    return success;
}

bool Vst3Processor::renderSourceRange(
    float* left,
    float* right,
    std::uint32_t start_frame,
    std::uint32_t frame_count,
    const Controls& controls
) noexcept {
    bool success = true;
    std::uint32_t offset = 0U;
    while (offset < frame_count) {
        const auto chunk = std::min<std::uint32_t>(
            frame_count - offset,
            static_cast<std::uint32_t>(kMaximumHostBlockFrames));
        ProcessReport report{};
        if (!core_.process(
                controls,
                main_q27_.data(),
                auxiliary_q27_.data(),
                static_cast<std::size_t>(chunk),
                &report)) {
            process_failures_.fetch_add(1U, std::memory_order_relaxed);
            success = false;
            offset += chunk;
            continue;
        }
        for (std::uint32_t frame = 0U; frame < chunk; ++frame) {
            left[start_frame + offset + frame]
                = static_cast<float>(main_q27_[frame]) * kQ27ToFloat;
            right[start_frame + offset + frame]
                = static_cast<float>(auxiliary_q27_[frame]) * kQ27ToFloat;
        }
        accepted_mailbox_.publish(report.snapshot);
        offset += chunk;
    }
    return success;
}

bool Vst3Processor::parseState(
    const juce::ValueTree& root,
    Vst3ProgramState& program) const {
    std::int64_t schema_version = 0;
    if (!root.isValid() || root.getType() != kStateType
        || root.getNumProperties() != 6
        || root.getNumChildren() != 1
        || root.getProperty("schema").toString()
            != juce::String{kVst3StateSchema.data()}
        || !parseInteger(root.getProperty("schemaVersion"), schema_version)
        || schema_version
            != static_cast<int>(kVst3StateSchemaVersion)
        || root.getProperty("parameterContract").toString()
            != juce::String{std::to_string(vst3ParameterContractFingerprint())}) {
        return false;
    }

    const auto seed_value = root.getProperty("seed");
    const auto page_value = root.getProperty("page");
    const auto mode_value = root.getProperty("mode");
    std::int64_t seed = 0;
    int page = 0;
    int mode = 0;
    if (!parseInteger(seed_value, seed)
        || !parseInteger(page_value, page)
        || !parseInteger(mode_value, mode)) {
        return false;
    }
    if (seed < 0
        || static_cast<std::uint64_t>(seed)
            > std::numeric_limits<std::uint32_t>::max()
        || page < 0 || page >= static_cast<int>(kPageCount)
        || (mode != static_cast<int>(LaneControlMode::voice)
            && mode != static_cast<int>(LaneControlMode::motion))) {
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
        const auto value = child.getProperty("value");
        double normalized = 0.0;
        if (!index.has_value() || seen[*index]
            || !parseReal(value, normalized)) {
            return false;
        }
        if (!std::isfinite(normalized) || normalized < 0.0 || normalized > 1.0) {
            return false;
        }
        candidate.normalized[*index] = static_cast<float>(normalized);
        seen[*index] = true;
    }
    if (!std::all_of(seen.begin(), seen.end(), [](bool value) { return value; })) {
        return false;
    }
    candidate.seed = static_cast<std::uint32_t>(seed);
    candidate.selected_page = static_cast<std::uint8_t>(page);
    candidate.lane_control_mode = static_cast<LaneControlMode>(mode);
    if (!validVst3ProgramState(candidate)) return false;
    program = candidate;
    return true;
}

}  // namespace schuss::pamplist
