cmake_minimum_required(VERSION 3.22)
project(instrument_lab_smoke VERSION 0.1.0 LANGUAGES C CXX)

set(SCHUSS_INSTRUMENT_LAB_ROOT "" CACHE PATH "Instrument Lab source root")
if(NOT SCHUSS_INSTRUMENT_LAB_ROOT)
    message(FATAL_ERROR "SCHUSS_INSTRUMENT_LAB_ROOT is required")
endif()
add_subdirectory("${SCHUSS_INSTRUMENT_LAB_ROOT}" instrument_lab EXCLUDE_FROM_ALL)

option(INSTRUMENT_LAB_SMOKE_ENABLE_JUCE "Build authenticated JUCE probe" OFF)
set(INSTRUMENT_LAB_SMOKE_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 tree")

add_library(instrument_lab_smoke_core STATIC src/smoke_adapter.cpp)
target_include_directories(instrument_lab_smoke_core PUBLIC include)
target_link_libraries(instrument_lab_smoke_core PUBLIC SchussInstrumentLab::Core)
target_compile_features(instrument_lab_smoke_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(instrument_lab_smoke_core)

enable_testing()
add_executable(instrument_lab_smoke_tests tests/smoke_tests.cpp)
target_link_libraries(instrument_lab_smoke_tests PRIVATE instrument_lab_smoke_core)
target_compile_features(instrument_lab_smoke_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(instrument_lab_smoke_tests)
schuss_instrument_lab_register_test(instrument_lab_smoke_tests instrument_lab_smoke_tests)

if(INSTRUMENT_LAB_SMOKE_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${INSTRUMENT_LAB_SMOKE_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH OFF)
    add_executable(instrument_lab_smoke_juce_probe src/juce_probe.cpp)
    target_link_libraries(instrument_lab_smoke_juce_probe PRIVATE juce::juce_core)
    target_compile_features(instrument_lab_smoke_juce_probe PRIVATE cxx_std_17)
    target_compile_definitions(instrument_lab_smoke_juce_probe PRIVATE JUCE_USE_CURL=0 JUCE_WEB_BROWSER=0)
    schuss_instrument_lab_enable_warnings(instrument_lab_smoke_juce_probe)
    schuss_instrument_lab_register_test(
        instrument_lab_smoke_juce_probe instrument_lab_smoke_juce_probe)
endif()
