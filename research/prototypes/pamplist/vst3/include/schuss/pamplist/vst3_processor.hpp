#pragma once

#include "schuss/pamplist/control_map.hpp"
#include "schuss/pamplist/control_snapshot.hpp"
#include "schuss/pamplist/vst3_model.hpp"
#include "schuss/instrument_lab/fixed_rate_resampler.hpp"

#include <juce_audio_processors/juce_audio_processors.h>

#include <array>
#include <atomic>
#include <cstddef>
#include <cstdint>
#include <optional>

namespace schuss::pamplist {

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
    [[nodiscard]] Snapshot acceptedSnapshot() const noexcept;
    [[nodiscard]] float parameterNormalized(std::size_t index) const noexcept;
    [[nodiscard]] float parameterPhysical(std::size_t index) const noexcept;

    void beginParameterGesture(std::size_t index);
    void setParameterPhysical(
        std::size_t index,
        float physical,
        bool notify_host = true);
    void endParameterGesture(std::size_t index);
    [[nodiscard]] bool setSurfacePhysical(
        SurfaceRow row,
        std::size_t column,
        float physical,
        bool notify_host = true);

    void setSelectedPage(std::uint8_t page) noexcept;
    void setLaneControlMode(LaneControlMode mode) noexcept;
    void requestClear() noexcept;
    [[nodiscard]] bool applyProgramState(const Vst3ProgramState& program) noexcept;

    [[nodiscard]] bool preparedForAudio() const noexcept;
    [[nodiscard]] juce::String statusText() const;
    [[nodiscard]] std::uint64_t processFailureCount() const noexcept;
    [[nodiscard]] std::uint64_t acceptedStateCount() const noexcept;
    [[nodiscard]] std::uint64_t rejectedStateCount() const noexcept;
    [[nodiscard]] std::uint64_t receivedMidiCount() const noexcept;
    [[nodiscard]] std::uint64_t mappedMidiCount() const noexcept;

private:
    [[nodiscard]] Vst3ProgramState captureCoherentProgram(
        Vst3ProgramState fallback) const noexcept;
    void publishFreshSnapshot() noexcept;
    void applyPendingReset() noexcept;
    void applyPendingClear(Controls& controls) noexcept;
    void syncParametersFromControls(const Controls& controls) noexcept;
    [[nodiscard]] bool renderRange(
        juce::AudioBuffer<float>& buffer,
        int start_frame,
        int frame_count,
        const Controls& controls) noexcept;
    [[nodiscard]] bool renderSourceRange(
        float* left,
        float* right,
        std::uint32_t start_frame,
        std::uint32_t frame_count,
        const Controls& controls) noexcept;
    [[nodiscard]] bool parseState(
        const juce::ValueTree& root,
        Vst3ProgramState& program) const;

    std::array<AtomicVst3Parameter*, kVst3ParameterCount> parameters_{};
    std::atomic<std::uint64_t> parameter_revision_{0U};
    std::atomic<std::uint64_t> state_transaction_sequence_{0U};
    std::atomic<std::uint32_t> seed_{kDefaultSeed};
    std::atomic<std::uint8_t> selected_page_{0U};
    std::atomic<std::uint8_t> lane_mode_{
        static_cast<std::uint8_t>(LaneControlMode::voice)};
    std::atomic<std::uint64_t> reset_request_generation_{1U};
    std::atomic<std::uint64_t> reset_clear_barrier_{0U};
    std::atomic<std::uint64_t> clear_request_generation_{0U};

    Core core_{};
    ControllerAdapter controller_{};
    schuss::instrument_lab::FixedRateStereoResampler resampler_{};
    std::array<std::int32_t, kMaximumHostBlockFrames> main_q27_{};
    std::array<std::int32_t, kMaximumHostBlockFrames> auxiliary_q27_{};
    AtomicAcceptedSnapshot accepted_mailbox_{};
    mutable Snapshot last_reader_snapshot_{};
    Vst3ProgramState last_audio_program_{};
    std::uint64_t applied_reset_generation_{};
    std::uint64_t applied_clear_request_generation_{};
    std::uint32_t effect_clear_generation_{};

    std::atomic<bool> prepared_{false};
    std::atomic<std::uint32_t> prepared_sample_rate_{0U};
    std::atomic<std::uint32_t> prepared_latency_frames_{0U};
    std::atomic<std::uint32_t> last_block_frames_{0U};
    std::atomic<std::uint64_t> process_failures_{0U};
    std::atomic<std::uint64_t> accepted_states_{0U};
    std::atomic<std::uint64_t> rejected_states_{0U};
    std::atomic<std::uint64_t> received_midi_{0U};
    std::atomic<std::uint64_t> mapped_midi_{0U};

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(Vst3Processor)
};

[[nodiscard]] juce::AudioProcessorEditor* createPamplistVst3Editor(
    Vst3Processor& processor);

}  // namespace schuss::pamplist
