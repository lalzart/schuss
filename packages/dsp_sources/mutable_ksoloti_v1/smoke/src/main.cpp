#include "braids/resources.h"
#include "clouds/dsp/grain.h"
#include "clouds/resources.h"
#include "stmlib/dsp/units.h"

#include <cstdint>

int main() {
    clouds::Grain grain;
    grain.Init();
    volatile float pitch_ratio = stmlib::SemitonesToRatio(0.0f);
    volatile std::int32_t resource_probe =
        static_cast<std::int32_t>(braids::lut_resonator_coefficient[0])
        + static_cast<std::int32_t>(clouds::lut_ulaw[0]);
    static_cast<void>(pitch_ratio);
    static_cast<void>(resource_probe);
    return 0;
}
