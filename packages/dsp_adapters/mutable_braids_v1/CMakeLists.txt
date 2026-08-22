cmake_minimum_required(VERSION 3.22)

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
    project(schuss_mutable_braids_v1 LANGUAGES CXX)
    enable_testing()
endif()
option(MUTABLE_BRAIDS_V1_BUILD_TESTS "Build the adapter deterministic test" ON)

include("${CMAKE_CURRENT_LIST_DIR}/../../dsp_sources/mutable_eurorack_braids_v1/cmake/MutableEurorackBraidsSource.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/../../dsp_sources/mutable_stmlib_v1/cmake/MutableStmlibSource.cmake")

mutable_eurorack_braids_v1_resolve_components(
    _mutable_braids_v1_sources
    braids-core-sources
    braids-resources-source)
mutable_stmlib_v1_resolve_components(
    _mutable_braids_v1_stmlib_sources
    stmlib-random-source)

if(NOT TARGET mutable_braids_v1_upstream)
    add_library(mutable_braids_v1_upstream STATIC
        ${_mutable_braids_v1_sources}
        ${_mutable_braids_v1_stmlib_sources})
    target_link_libraries(mutable_braids_v1_upstream PUBLIC
        MutableEurorackBraidsV1::Headers
        MutableStmlibV1::Headers)
    target_compile_features(mutable_braids_v1_upstream PUBLIC cxx_std_17)
    target_compile_options(mutable_braids_v1_upstream PRIVATE
        $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Wno-unused-parameter;-Wno-unused-but-set-variable>)
endif()

if(NOT TARGET mutable_braids_v1)
    add_library(mutable_braids_v1 STATIC src/mutable_braids.cpp)
    target_include_directories(mutable_braids_v1 PUBLIC include)
    target_link_libraries(mutable_braids_v1 PRIVATE mutable_braids_v1_upstream)
    target_compile_features(mutable_braids_v1 PUBLIC cxx_std_17)
    target_compile_options(mutable_braids_v1 PRIVATE
        $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic>)
    add_library(SchussMutableBraidsV1::Core ALIAS mutable_braids_v1)
endif()

if(MUTABLE_BRAIDS_V1_BUILD_TESTS AND NOT TARGET mutable_braids_v1_tests)
    add_executable(mutable_braids_v1_tests tests/mutable_braids_tests.cpp)
    target_link_libraries(mutable_braids_v1_tests PRIVATE mutable_braids_v1)
    target_compile_features(mutable_braids_v1_tests PRIVATE cxx_std_17)
    add_test(NAME mutable_braids_v1_tests COMMAND mutable_braids_v1_tests)
endif()
