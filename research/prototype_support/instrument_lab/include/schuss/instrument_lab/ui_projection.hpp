#pragma once

#include <array>
#include <cstddef>

namespace schuss::instrument_lab {

template <typename Descriptor, std::size_t Count, typename Snapshot, typename Projector>
[[nodiscard]] std::array<double, Count> projectControlValues(
    const std::array<Descriptor, Count>& descriptors,
    const Snapshot& snapshot,
    Projector projector
) noexcept(noexcept(projector(descriptors[0], snapshot))) {
    std::array<double, Count> result{};
    for (std::size_t index = 0; index < Count; ++index) {
        result[index] = projector(descriptors[index], snapshot);
    }
    return result;
}

}  // namespace schuss::instrument_lab
