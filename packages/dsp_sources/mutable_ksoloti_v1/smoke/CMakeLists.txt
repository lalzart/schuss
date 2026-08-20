cmake_minimum_required(VERSION 3.22)
project(mutable_ksoloti_v1_smoke LANGUAGES CXX)

set(MUTABLE_KSOLOTI_V1_SMOKE_COMPONENTS
    "braids-resources;clouds-resources;stmlib-units-source"
    CACHE STRING "Closed source-package component groups used by the smoke consumer")

include("${CMAKE_CURRENT_LIST_DIR}/../cmake/MutableKsolotiSource.cmake")
mutable_ksoloti_v1_resolve_components(
    mutable_ksoloti_v1_smoke_sources
    ${MUTABLE_KSOLOTI_V1_SMOKE_COMPONENTS})

add_executable(mutable_ksoloti_v1_smoke
    src/main.cpp
    ${mutable_ksoloti_v1_smoke_sources})
target_link_libraries(mutable_ksoloti_v1_smoke PRIVATE MutableKsolotiV1::Headers)
target_compile_features(mutable_ksoloti_v1_smoke PRIVATE cxx_std_17)

enable_testing()
add_test(NAME mutable_ksoloti_v1_smoke COMMAND mutable_ksoloti_v1_smoke)
