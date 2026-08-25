#include "tidepit/vst3_processor.hpp"

juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter() {
    return new tidepit::Vst3Processor();
}
