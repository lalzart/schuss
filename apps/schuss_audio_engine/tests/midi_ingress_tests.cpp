#include "midi_ingress.hpp"

#include <cstdlib>
#include <iostream>

namespace {

void expect(bool condition, const char* message) {
    if (!condition) {
        std::cerr << message << '\n';
        std::exit(1);
    }
}

schuss::engine::StampedMidi message(std::uint64_t sequence) {
    schuss::engine::StampedMidi value;
    value.timestamp_ns = sequence * 100U;
    value.sequence = sequence;
    value.bytes = {0x90U, 60U, 100U};
    value.size = 3;
    return value;
}

}  // namespace

int main() {
    schuss::engine::MidiIngressQueue<4> queue;
    for (std::uint64_t sequence = 0; sequence < 4; ++sequence) {
        expect(queue.enqueue(message(sequence)), "queue rejected an in-bound message");
    }
    expect(!queue.enqueue(message(4)), "queue did not reject bounded overflow");
    expect(queue.overflows() == 1, "queue overflow metric mismatch");
    for (std::uint64_t sequence = 0; sequence < 4; ++sequence) {
        schuss::engine::StampedMidi actual;
        expect(queue.pop(actual), "queue lost an accepted message");
        expect(actual.sequence == sequence, "queue changed arrival ordering");
        expect(actual.timestamp_ns == sequence * 100U, "queue changed a timestamp");
    }
    schuss::engine::StampedMidi empty;
    expect(!queue.pop(empty), "queue produced an extra message");
    auto invalid = message(5);
    invalid.size = 0;
    expect(!queue.enqueue(invalid), "queue accepted an invalid MIDI size");
    queue.reset();
    expect(queue.overflows() == 0, "queue reset did not clear telemetry");
    expect(queue.enqueue(message(6)), "queue reset did not restore capacity");
    std::cout << "schuss_midi_ingress_tests: passed\n";
    return 0;
}
