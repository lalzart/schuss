cmake_minimum_required(VERSION 3.22)

project(layerwell_prototype VERSION 0.1.0 LANGUAGES C CXX)

option(LAYERWELL_ENABLE_JUCE "Build the authenticated-JUCE standalone" OFF)
set(LAYERWELL_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 source tree")
option(LAYERWELL_ALLOW_JUCE_FETCH "Fetch JUCE rather than use authenticated local source" OFF)
option(LAYERWELL_ENABLE_SANITIZERS "Enable ASan and UBSan" OFF)

enable_testing()
find_package(Python3 COMPONENTS Interpreter REQUIRED)
find_package(Threads REQUIRED)

set(TIDE_PIT_ENABLE_JUCE OFF CACHE BOOL "" FORCE)
add_subdirectory(
    "${CMAKE_CURRENT_SOURCE_DIR}/../tide-pit-gills"
    "${CMAKE_CURRENT_BINARY_DIR}/tide-pit-gills"
    EXCLUDE_FROM_ALL)

# The two exact Mutable closures export overlapping braids/stmlib namespace
# symbols. Keep both source projects byte-for-byte unchanged and make the
# isolation a private property of Layerwell's Tide Pit target instances.
target_compile_definitions(tide_pit_mutable PRIVATE
    braids=tidepit_private_braids
    stmlib=tidepit_private_stmlib)
target_compile_definitions(tide_pit_core PRIVATE
    braids=tidepit_private_braids
    stmlib=tidepit_private_stmlib)

# Tide Pit's unchanged project owns the one Instrument Lab subdirectory in this
# parent graph. Recreate only the Generative Drums public Core target from its
# exact declared source list so its unchanged standalone CMake never attempts a
# second Instrument Lab subdirectory or registers unrelated child tests.
set(MUTABLE_BRAIDS_V1_BUILD_TESTS OFF CACHE BOOL "" FORCE)
add_subdirectory(
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../packages/dsp_adapters/mutable_braids_v1"
    "${CMAKE_CURRENT_BINARY_DIR}/mutable_braids_v1"
    EXCLUDE_FROM_ALL)
set(LAYERWELL_GDM_SOURCE
    "${CMAKE_CURRENT_SOURCE_DIR}/../generative-drum-machine")
add_library(generative_drum_machine_core STATIC
    "${LAYERWELL_GDM_SOURCE}/src/control_map.cpp"
    "${LAYERWELL_GDM_SOURCE}/src/core.cpp")
target_include_directories(generative_drum_machine_core
    PUBLIC "${LAYERWELL_GDM_SOURCE}/include"
    PRIVATE "${LAYERWELL_GDM_SOURCE}/generated")
target_link_libraries(generative_drum_machine_core
    PUBLIC SchussInstrumentLab::Core
    PRIVATE SchussMutableBraidsV1::Core)
target_compile_features(generative_drum_machine_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(generative_drum_machine_core)

add_executable(layerwell_source_link_gate tests/source_link_gate.cpp)
target_link_libraries(layerwell_source_link_gate PRIVATE
    generative_drum_machine_core
    tide_pit_core)
target_compile_features(layerwell_source_link_gate PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(layerwell_source_link_gate)
add_test(NAME layerwell_source_link_gate COMMAND layerwell_source_link_gate)

add_library(layerwell_core STATIC
    src/core.cpp
    src/source_adapters.cpp)
target_include_directories(layerwell_core PUBLIC include)
target_link_libraries(layerwell_core PUBLIC
    generative_drum_machine_core
    tide_pit_core
    SchussInstrumentLab::Core)
target_compile_features(layerwell_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(layerwell_core)
schuss_instrument_lab_enable_sanitizers(
    layerwell_core ${LAYERWELL_ENABLE_SANITIZERS})

foreach(test_target IN ITEMS layerwell_core_tests layerwell_source_adapter_tests)
    if(test_target STREQUAL "layerwell_core_tests")
        set(test_source tests/core_tests.cpp)
    else()
        set(test_source tests/source_adapter_tests.cpp)
    endif()
    add_executable(${test_target} ${test_source})
    target_link_libraries(${test_target} PRIVATE layerwell_core)
    target_compile_features(${test_target} PRIVATE cxx_std_17)
    schuss_instrument_lab_enable_warnings(${test_target})
    schuss_instrument_lab_enable_sanitizers(
        ${test_target} ${LAYERWELL_ENABLE_SANITIZERS})
    add_test(NAME ${test_target} COMMAND ${test_target})
endforeach()

add_library(layerwell_controller STATIC src/launch_control_3.cpp)
target_include_directories(layerwell_controller PUBLIC include)
target_link_libraries(layerwell_controller PUBLIC layerwell_core)
target_compile_features(layerwell_controller PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(layerwell_controller)
schuss_instrument_lab_enable_sanitizers(
    layerwell_controller ${LAYERWELL_ENABLE_SANITIZERS})

add_executable(layerwell_controller_tests tests/controller_tests.cpp)
target_link_libraries(layerwell_controller_tests PRIVATE layerwell_controller)
target_compile_features(layerwell_controller_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(layerwell_controller_tests)
schuss_instrument_lab_enable_sanitizers(
    layerwell_controller_tests ${LAYERWELL_ENABLE_SANITIZERS})
add_test(NAME layerwell_controller_tests COMMAND layerwell_controller_tests)

add_executable(layerwell_snapshot_tests tests/snapshot_tests.cpp)
target_link_libraries(layerwell_snapshot_tests PRIVATE
    layerwell_core Threads::Threads)
target_compile_features(layerwell_snapshot_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(layerwell_snapshot_tests)
schuss_instrument_lab_enable_sanitizers(
    layerwell_snapshot_tests ${LAYERWELL_ENABLE_SANITIZERS})
add_test(NAME layerwell_snapshot_tests COMMAND layerwell_snapshot_tests)

add_executable(layerwell_allocation_tests tests/allocation_tests.cpp)
target_link_libraries(layerwell_allocation_tests PRIVATE layerwell_core)
target_compile_features(layerwell_allocation_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(layerwell_allocation_tests)
schuss_instrument_lab_enable_sanitizers(
    layerwell_allocation_tests ${LAYERWELL_ENABLE_SANITIZERS})
add_test(NAME layerwell_allocation_tests COMMAND layerwell_allocation_tests)

add_executable(layerwell-render src/render.cpp)
target_link_libraries(layerwell-render PRIVATE layerwell_controller)
target_compile_features(layerwell-render PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(layerwell-render)
schuss_instrument_lab_enable_sanitizers(
    layerwell-render ${LAYERWELL_ENABLE_SANITIZERS})

if(LAYERWELL_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${LAYERWELL_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH "${LAYERWELL_ALLOW_JUCE_FETCH}")

    juce_add_gui_app(layerwell-instrument
        PRODUCT_NAME "Layerwell"
        COMPANY_NAME "Schuss"
        BUNDLE_ID "dev.schuss.layerwell.prototype")
    target_sources(layerwell-instrument PRIVATE src/juce_main.cpp)
    target_link_libraries(layerwell-instrument PRIVATE
        layerwell_controller
        juce::juce_audio_basics
        juce::juce_audio_devices
        juce::juce_core
        juce::juce_events
        juce::juce_gui_basics)
    target_compile_features(layerwell-instrument PRIVATE cxx_std_17)
    target_compile_definitions(layerwell-instrument PRIVATE
        JUCE_REPORT_APP_USAGE=0
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0)
    schuss_instrument_lab_enable_warnings(layerwell-instrument)
endif()
