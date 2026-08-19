#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace schuss::rt {

std::string sha256_hex(std::string_view bytes);
std::string sha256_hex(const std::vector<std::uint8_t>& bytes);

}  // namespace schuss::rt
