#include "WirefallR02Core.h"

#include "schuss/instrument_lab/renderer_artifacts.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <locale>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

namespace fs = std::filesystem;
using wirefall::r02::ActionId;
using wirefall::r02::ControlId;
using wirefall::r02::Event;
using wirefall::r02::EventKind;

struct ScheduledEvent {
    std::uint64_t frame{};
    Event event{};
};

struct Condition {
    std::string id;
    std::uint64_t duration_frames{1152000};
    bool comparator{};
    std::vector<ScheduledEvent> events;
};

struct Options {
    std::string condition;
    fs::path output;
    std::uint32_t block_frames{64};
};

ScheduledEvent set(std::uint64_t frame, std::uint64_t sequence, ControlId id, double value) {
    Event event{};
    event.ingress_sequence = sequence;
    event.kind = EventKind::set_control;
    event.control = id;
    event.value = value;
    return {frame, event};
}

ScheduledEvent ramp(
    std::uint64_t frame,
    std::uint64_t end_frame,
    std::uint64_t sequence,
    ControlId id,
    double value,
    double end_value
) {
    Event event{};
    event.ingress_sequence = sequence;
    event.kind = EventKind::linear_control;
    event.control = id;
    event.value = value;
    event.end_value = end_value;
    event.duration_frames = end_frame - frame;
    return {frame, event};
}

std::vector<ScheduledEvent> interruptEvents(double tick) {
    std::vector<ScheduledEvent> events;
    std::uint64_t sequence = 1;
    events.push_back(set(0, sequence++, ControlId::energy, 0.68));
    events.push_back(set(0, sequence++, ControlId::tick, tick));
    events.push_back(set(0, sequence++, ControlId::pulse, 2));
    events.push_back(set(0, sequence++, ControlId::break_depth, 0.0));
    constexpr std::array<std::uint64_t, 4> bases{{0, 192000, 384000, 576000}};
    constexpr std::array<double, 4> rates{{2, 3, 5, 7}};
    for (std::size_t index = 0; index < bases.size(); ++index) {
        if (index != 0) events.push_back(set(bases[index], sequence++, ControlId::pulse, rates[index]));
        if (index != 0) events.push_back(set(bases[index], sequence++, ControlId::break_depth, 0.0));
        events.push_back(set(bases[index] + 48000, sequence++, ControlId::break_depth, 0.5));
        events.push_back(set(bases[index] + 96000, sequence++, ControlId::break_depth, 1.0));
    }
    events.push_back(set(768000, sequence++, ControlId::pulse, 2));
    events.push_back(set(768000, sequence++, ControlId::break_depth, 1.0));
    events.push_back(set(864000, sequence++, ControlId::pulse, 3));
    events.push_back(set(960000, sequence++, ControlId::pulse, 5));
    events.push_back(set(1056000, sequence++, ControlId::pulse, 7));
    std::stable_sort(events.begin(), events.end(), [](const auto& left, const auto& right) {
        if (left.frame != right.frame) return left.frame < right.frame;
        return left.event.ingress_sequence < right.event.ingress_sequence;
    });
    return events;
}

Condition makeCondition(std::string_view id) {
    Condition result{};
    result.id = std::string(id);
    if (id == "R02_ENERGY") {
        result.events = {
            set(0, 1, ControlId::pulse, 0),
            set(0, 2, ControlId::energy, 0.10),
            set(96000, 3, ControlId::energy, 0.30),
            set(192000, 4, ControlId::energy, 0.50),
            set(288000, 5, ControlId::energy, 0.70),
            set(384000, 6, ControlId::energy, 0.90),
            ramp(480000, 960000, 7, ControlId::energy, 0.05, 0.95),
            set(960000, 8, ControlId::energy, 0.95),
        };
    } else if (id == "R02_SILENCE") {
        result.events = interruptEvents(0.0);
    } else if (id == "R02_TICK") {
        result.events = interruptEvents(0.85);
    } else if (id == "R02_CMP_TREMOLO") {
        result.events = interruptEvents(0.0);
        result.comparator = true;
    } else {
        throw std::runtime_error("unknown condition: " + std::string(id));
    }
    return result;
}

std::string controlName(ControlId id) {
    const auto raw = static_cast<std::size_t>(id);
    if (raw >= wirefall::r02::kControlDescriptors.size()) return "NONE";
    return std::string(wirefall::r02::kControlDescriptors[raw].name);
}

std::string actionName(ActionId id) {
    switch (id) {
        case ActionId::open_press: return "OPEN_PRESS";
        case ActionId::open_release: return "OPEN_RELEASE";
        case ActionId::tick_preview: return "TICK_PREVIEW";
        case ActionId::downbeat: return "DOWNBEAT";
        case ActionId::panic_press: return "PANIC_PRESS";
        case ActionId::panic_release: return "PANIC_RELEASE";
        case ActionId::reset: return "RESET";
        case ActionId::unsupported: return "UNSUPPORTED";
    }
    return "UNSUPPORTED";
}

std::string ledgerKindName(wirefall::r02::LedgerKind id) {
    switch (id) {
        case wirefall::r02::LedgerKind::accepted_control: return "accepted_control";
        case wirefall::r02::LedgerKind::accepted_action: return "accepted_action";
        case wirefall::r02::LedgerKind::pulse_onset: return "pulse_onset";
        case wirefall::r02::LedgerKind::reset_boundary: return "reset_boundary";
        case wirefall::r02::LedgerKind::panic_boundary: return "panic_boundary";
    }
    return "invalid";
}

void writeLittle(std::ofstream& stream, std::uint32_t value, std::size_t bytes) {
    for (std::size_t index = 0; index < bytes; ++index) {
        stream.put(static_cast<char>((value >> (8U * index)) & 0xffU));
    }
}

std::int32_t quantize24(float value) {
    const double bounded = std::clamp(static_cast<double>(value), -1.0, 1.0);
    return static_cast<std::int32_t>(std::llround(bounded * 8388607.0));
}

void writeWav(const fs::path& path, const std::vector<float>& left, const std::vector<float>& right) {
    if (left.size() != right.size()) throw std::runtime_error("channel size mismatch");
    const std::uint32_t data_bytes = static_cast<std::uint32_t>(left.size() * 6U);
    std::ofstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("cannot write WAV: " + path.string());
    stream.write("RIFF", 4);
    writeLittle(stream, 36U + data_bytes, 4);
    stream.write("WAVEfmt ", 8);
    writeLittle(stream, 16, 4);
    writeLittle(stream, 1, 2);
    writeLittle(stream, 2, 2);
    writeLittle(stream, 48000, 4);
    writeLittle(stream, 48000U * 6U, 4);
    writeLittle(stream, 6, 2);
    writeLittle(stream, 24, 2);
    stream.write("data", 4);
    writeLittle(stream, data_bytes, 4);
    for (std::size_t index = 0; index < left.size(); ++index) {
        const auto l = static_cast<std::uint32_t>(quantize24(left[index])) & 0x00ffffffU;
        const auto r = static_cast<std::uint32_t>(quantize24(right[index])) & 0x00ffffffU;
        writeLittle(stream, l, 3);
        writeLittle(stream, r, 3);
    }
}

Options parseOptions(int argc, char** argv) {
    Options result{};
    for (int index = 1; index < argc; ++index) {
        const std::string argument = argv[index];
        if (argument == "--condition" && index + 1 < argc) result.condition = argv[++index];
        else if (argument == "--output" && index + 1 < argc) result.output = argv[++index];
        else if (argument == "--block-frames" && index + 1 < argc) {
            result.block_frames = static_cast<std::uint32_t>(std::stoul(argv[++index]));
        } else {
            throw std::runtime_error("unknown or incomplete argument: " + argument);
        }
    }
    if (result.condition.empty() || result.output.empty() || result.block_frames == 0
        || result.block_frames > wirefall::r02::kMaximumBlockFrames) {
        throw std::runtime_error("usage: wirefall_r02_render --condition ID --output DIR --block-frames N");
    }
    return result;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const auto options = parseOptions(argc, argv);
        const auto condition = makeCondition(options.condition);
        fs::create_directories(options.output);
        wirefall::r02::Core core;
        if (!core.prepare(48000.0)) throw std::runtime_error("Core prepare failed");
        std::vector<float> left(condition.duration_frames);
        std::vector<float> right(condition.duration_frames);
        std::vector<wirefall::r02::LedgerEvent> ledger;
        std::uint64_t position = 0;
        std::size_t next_event = 0;
        while (position < condition.duration_frames) {
            const auto count = static_cast<std::uint32_t>(std::min<std::uint64_t>(
                options.block_frames, condition.duration_frames - position));
            std::array<Event, wirefall::r02::kMaximumEventsPerBlock> block_events{};
            std::size_t event_count = 0;
            while (next_event < condition.events.size()
                && condition.events[next_event].frame < position + count) {
                block_events[event_count] = condition.events[next_event].event;
                if (condition.comparator
                    && block_events[event_count].control == ControlId::break_depth) {
                    block_events[event_count].value = 0.0;
                }
                block_events[event_count].sample_offset = static_cast<std::uint32_t>(
                    condition.events[next_event].frame - position);
                ++event_count;
                ++next_event;
            }
            std::array<wirefall::r02::LedgerEvent, 256> rows{};
            const auto report = core.process(
                left.data() + position,
                right.data() + position,
                count,
                block_events.data(),
                event_count,
                rows.data(),
                rows.size());
            if (report.dropped_events != 0 || report.ledger_events_dropped != 0) {
                throw std::runtime_error("normal render dropped an event or ledger row");
            }
            ledger.insert(ledger.end(), rows.begin(), rows.begin()
                + static_cast<std::ptrdiff_t>(report.ledger_events_written));
            position += count;
        }

        if (condition.comparator) {
            double phase = 0.0;
            std::uint8_t rate_index = 2;
            double depth = 0.0;
            std::size_t event_cursor = 0;
            for (std::uint64_t frame = 0; frame < condition.duration_frames; ++frame) {
                while (event_cursor < condition.events.size()
                    && condition.events[event_cursor].frame == frame) {
                    const auto& event = condition.events[event_cursor].event;
                    if (event.control == ControlId::pulse) {
                        rate_index = static_cast<std::uint8_t>(event.value);
                    } else if (event.control == ControlId::break_depth) {
                        depth = event.value;
                    }
                    ++event_cursor;
                }
                const double rate = wirefall::r02::kPulseRatesPerBeat[rate_index] * 2.0;
                const double gain = 1.0 - depth * (0.5 - 0.5 * std::cos(2.0 * 3.14159265358979323846 * phase));
                left[frame] = static_cast<float>(left[frame] * gain);
                right[frame] = static_cast<float>(right[frame] * gain);
                phase += rate / 48000.0;
                if (phase >= 1.0) phase -= std::floor(phase);
            }
        }

        const auto stem = condition.id;
        writeWav(options.output / (stem + ".wav"), left, right);
        std::ofstream csv(options.output / (stem + ".events.csv"), std::ios::binary);
        csv.imbue(std::locale::classic());
        csv << "sample_index,ingress_sequence,kind,control,action,value,pulse_index,pulse_phase\n";
        csv << std::setprecision(17);
        for (const auto& row : ledger) {
            csv << row.sample_index << ',' << row.ingress_sequence << ',' << ledgerKindName(row.kind)
                << ',' << controlName(row.control) << ',' << actionName(row.action) << ','
                << row.value << ',' << static_cast<unsigned>(row.pulse_index) << ','
                << row.pulse_phase << '\n';
        }
        const auto diagnostics = core.diagnostics();
        long double sum_squares = 0.0L;
        long double sum_left = 0.0L;
        long double sum_right = 0.0L;
        double peak = 0.0;
        double max_delta = 0.0;
        for (std::size_t index = 0; index < left.size(); ++index) {
            sum_squares += static_cast<long double>(left[index]) * left[index]
                + static_cast<long double>(right[index]) * right[index];
            sum_left += left[index];
            sum_right += right[index];
            peak = std::max({peak, std::abs(static_cast<double>(left[index])),
                std::abs(static_cast<double>(right[index]))});
            if (index != 0) {
                max_delta = std::max({max_delta,
                    std::abs(static_cast<double>(left[index] - left[index - 1])),
                    std::abs(static_cast<double>(right[index] - right[index - 1]))});
            }
        }
        const double denominator = static_cast<double>(left.size());
        const double rms = std::sqrt(static_cast<double>(sum_squares) / (2.0 * denominator));
        std::ofstream json(options.output / (stem + ".metrics.json"), std::ios::binary);
        json.imbue(std::locale::classic());
        json << std::setprecision(17)
            << "{\n"
            << "  \"abs_peak\": " << peak << ",\n"
            << "  \"block_frames\": " << options.block_frames << ",\n"
            << "  \"channel_dc_mean\": [" << static_cast<double>(sum_left) / denominator
            << ", " << static_cast<double>(sum_right) / denominator << "],\n"
            << "  \"condition\": \"" << stem << "\",\n"
            << "  \"diagnostics\": {\n"
            << "    \"accepted_events\": " << diagnostics.accepted_events << ",\n"
            << "    \"dropped_events\": " << diagnostics.dropped_events << ",\n"
            << "    \"invalid_events\": " << diagnostics.invalid_events << ",\n"
            << "    \"ledger_overflows\": " << diagnostics.ledger_overflows << ",\n"
            << "    \"non_finite_samples\": " << diagnostics.non_finite_samples << ",\n"
            << "    \"pulse_onsets\": " << diagnostics.pulse_onsets << ",\n"
            << "    \"safety_clamps\": " << diagnostics.safety_clamps << "\n"
            << "  },\n"
            << "  \"maximum_adjacent_delta\": " << max_delta << ",\n"
            << "  \"rms\": " << rms << "\n"
            << "}\n";
        std::cout << stem << " rendered at block " << options.block_frames << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "wirefall_r02_render: " << error.what() << '\n';
        return 1;
    }
}
