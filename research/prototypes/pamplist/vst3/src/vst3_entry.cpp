#include "schuss/pamplist/vst3_processor.hpp"

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() {
    return new schuss::pamplist::Vst3Processor{};
}
