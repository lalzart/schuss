#pragma once

#include "tidepit/juce_midi_adapter.hpp"
#include "tidepit/ui_model.hpp"
#include "tidepit/vst3_model.hpp"
#include "schuss/instrument_lab/fixed_rate_resampler.hpp"

#include <juce_audio_processors/juce_audio_processors.h>

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>

namespace tidepit {

template <typename Value>
class AtomicVst3Snapshot final {
public:
    [[nodiscard]] static constexpr bool lockFreeContract() noexcept {
        return std::atomic<std::uint32_t>::is_always_lock_free;
    }

    void publish(const Value& value) noexcept {
        const auto active = active_slot_.load(std::memory_order_seq_cst);
        const auto reader = reader_slot_.load(std::memory_order_seq_cst);
        auto target = kNoReader;
        for (std::uint32_t candidate = 0U; candidate < kSlotCount; ++candidate) {
            if (candidate != active && candidate != reader) {
                target = candidate;
                break;
            }
        }
        if (target == kNoReader) return;
        slots_[target] = value;
        active_slot_.store(target, std::memory_order_seq_cst);
    }

    [[nodiscard]] Value load(Value fallback) const noexcept {
        for (int attempt = 0; attempt < 4; ++attempt) {
            const auto slot = active_slot_.load(std::memory_order_seq_cst);
            reader_slot_.store(slot, std::memory_order_seq_cst);
            if (active_slot_.load(std::memory_order_seq_cst) != slot) {
                reader_slot_.store(kNoReader, std::memory_order_seq_cst);
                continue;
            }
            const auto value = slots_[slot];
            reader_slot_.store(kNoReader, std::memory_order_seq_cst);
            return value;
        }
        return fallback;
    }

private:
    static constexpr std::uint32_t kSlotCount = 3U;
    static constexpr std::uint32_t kNoReader = kSlotCount;
    std::array<Value, kSlotCount> slots_{};
    std::atomic<std::uint32_t> active_slot_{0U};
    mutable std::atomic<std::uint32_t> reader_slot_{kNoReader};
};

struct Vst3UiFrame final {
    Snapshot snapshot{};
    Diagnostics core_diagnostics{};
    MidiAdapterDiagnostics midi_diagnostics{};
    std::uint64_t bridge_event_drops{};
    std::uint64_t processor_event_drops{};
};

class AtomicVst3Parameter;

class Vst3Processor final : public juce::AudioProcessor {
public:
    Vst3Processor();
    ~Vst3Processor() override;

    [[nodiscard]] const juce::String getName() const override;
    void prepareToPlay(double sample_rate, int maximum_expected_samples) override;
    void releaseResources() override;
    [[nodiscard]] bool isBusesLayoutSupported(
        const BusesLayout& layouts) const override;
    void processBlock(
        juce::AudioBuffer<float>& buffer,
        juce::MidiBuffer& midi_messages) override;

    [[nodiscard]] bool hasEditor() const override;
    [[nodiscard]] juce::AudioProcessorEditor* createEditor() override;
    [[nodiscard]] double getTailLengthSeconds() const override;
    [[nodiscard]] bool acceptsMidi() const override;
    [[nodiscard]] bool producesMidi() const override;
    [[nodiscard]] bool isMidiEffect() const override;

    [[nodiscard]] int getNumPrograms() override;
    [[nodiscard]] int getCurrentProgram() override;
    void setCurrentProgram(int index) override;
    [[nodiscard]] const juce::String getProgramName(int index) override;
    void changeProgramName(int index, const juce::String& name) override;

    void getStateInformation(juce::MemoryBlock& destination_data) override;
    void setStateInformation(const void* data, int size_in_bytes) override;

    [[nodiscard]] Vst3ProgramState programState() const noexcept;
    [[nodiscard]] Controls requestedControls() const noexcept;
    [[nodiscard]] Vst3UiFrame uiFrame() const noexcept;
    [[nodiscard]] Snapshot acceptedSnapshot() const noexcept;
    [[nodiscard]] ScopeFrame latestScope() const noexcept;
    [[nodiscard]] float parameterNormalized(std::size_t index) const noexcept;
    [[nodiscard]] float parameterPhysical(std::size_t index) const noexcept;

    void beginParameterGesture(std::size_t index);
    void setParameterPhysical(
        std::size_t index,
        float physical,
        bool notify_host = true);
    void endParameterGesture(std::size_t index);
    void requestAction(SemanticAction action) noexcept;
    [[nodiscard]] bool applyProgramState(
        const Vst3ProgramState& program) noexcept;

    [[nodiscard]] bool preparedForAudio() const noexcept;
    [[nodiscard]] juce::String statusText() const;
    [[nodiscard]] std::uint64_t processFailureCount() const noexcept;
    [[nodiscard]] std::uint64_t acceptedStateCount() const noexcept;
    [[nodiscard]] std::uint64_t rejectedStateCount() const noexcept;
    [[nodiscard]] std::uint64_t processorEventDropCount() const noexcept;

private:
    [[nodiscard]] Vst3ProgramState captureCoherentProgram(
        Vst3ProgramState fallback) const noexcept;
    [[nodiscard]] bool resetCore(
        std::uint64_t mutate_barrier,
        std::uint64_t freeze_barrier) noexcept;
    void applyPendingReset() noexcept;
    [[nodiscard]] bool appendEvent(
        SemanticAction action,
        double value,
        std::uint32_t sample_offset) noexcept;
    void appendProgramEvents(
        const Vst3ProgramState& desired,
        Vst3ProgramState& applied) noexcept;
    void appendOneShotEvents() noexcept;
    void appendMidiEvents(
        const juce::MidiBuffer& midi_messages,
        std::uint32_t block_frames,
        Vst3ProgramState& applied) noexcept;
    void enqueueResampledEvents(
        const schuss::instrument_lab::FixedRateStereoResampler::BlockPlan&
            plan) noexcept;
    void collectResampledEvents(
        const schuss::instrument_lab::FixedRateStereoResampler::BlockPlan&
            plan) noexcept;
    void syncParameterFromAudio(
        std::size_t index,
        float normalized) noexcept;
    void publishUiFrame() noexcept;
    [[nodiscard]] bool parseState(
        const juce::ValueTree& root,
        Vst3ProgramState& program) const;

    std::array<AtomicVst3Parameter*, kVst3ParameterCount> parameters_{};
    std::atomic<std::uint64_t> parameter_revision_{0U};
    std::atomic<std::uint64_t> state_transaction_sequence_{0U};
    std::atomic<std::uint64_t> reset_request_generation_{0U};
    std::atomic<std::uint64_t> reset_mutate_barrier_{0U};
    std::atomic<std::uint64_t> reset_freeze_barrier_{0U};
    std::atomic<std::uint64_t> mutate_request_generation_{0U};
    std::atomic<std::uint64_t> freeze_request_generation_{0U};

    struct PendingResampledEvent final {
        std::uint64_t absolute_source_frame{};
        std::uint64_t ingress_sequence{};
        SemanticAction action{SemanticAction::set_stage_1};
        double value{};
    };

    Core core_{};
    JuceMidiAdapter midi_adapter_{};
    schuss::instrument_lab::FixedRateStereoResampler resampler_{};
    ParameterizedQ27HostBridge bridge_{};
    ScopeAccumulator scope_accumulator_{};
    AtomicVst3Snapshot<Vst3UiFrame> ui_mailbox_{};
    AtomicVst3Snapshot<ScopeFrame> scope_mailbox_{};
    mutable Vst3UiFrame last_reader_ui_{};
    mutable ScopeFrame last_reader_scope_{};
    std::array<SemanticEvent, kMaximumSemanticEvents> events_{};
    std::array<PendingResampledEvent, kMaximumPendingHostEvents>
        pending_resampled_events_{};
    std::size_t event_count_{};
    std::size_t pending_resampled_event_count_{};
    std::uint64_t ingress_sequence_{};
    Vst3ProgramState last_audio_program_{};
    Vst3DiscreteState projected_modes_{};
    std::uint64_t applied_reset_generation_{};
    std::uint64_t applied_mutate_generation_{};
    std::uint64_t applied_freeze_generation_{};

    std::atomic<bool> prepared_{false};
    std::atomic<std::uint32_t> prepared_sample_rate_{0U};
    std::atomic<std::uint32_t> prepared_latency_frames_{0U};
    std::atomic<std::uint32_t> last_block_frames_{0U};
    std::atomic<std::uint64_t> process_failures_{0U};
    std::atomic<std::uint64_t> accepted_states_{0U};
    std::atomic<std::uint64_t> rejected_states_{0U};
    std::atomic<std::uint64_t> processor_event_drops_{0U};

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(Vst3Processor)
};

[[nodiscard]] juce::AudioProcessorEditor* createTidePitVst3Editor(
    Vst3Processor& processor);

}  // namespace tidepit
