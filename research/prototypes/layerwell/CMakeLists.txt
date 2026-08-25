cmake_minimum_required(VERSION 3.22)

project(layerwell_prototype VERSION 0.2.0 LANGUAGES C CXX)

option(LAYERWELL_ENABLE_JUCE "Build the authenticated-JUCE standalone" OFF)
set(LAYERWELL_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 source tree")
option(LAYERWELL_ALLOW_JUCE_FETCH "Fetch JUCE rather than use authenticated local source" OFF)
option(LAYERWELL_ENABLE_SANITIZERS "Enable ASan and UBSan" OFF)
set(PAMPLIST_PATCHER_ROOT "" CACHE PATH "Configured locked patcher checkout")

enable_testing()
find_package(Python3 COMPONENTS Interpreter REQUIRED)
find_package(Threads REQUIRED)

set(TIDE_PIT_ENABLE_JUCE OFF CACHE BOOL "" FORCE)
add_subdirectory(
    "${CMAKE_CURRENT_SOURCE_DIR}/../tide-pit-gills"
    "${CMAKE_CURRENT_BINARY_DIR}/tide-pit-gills"
    EXCLUDE_FROM_ALL)

# Keep Tide Pit's exact upstream namespace isolation private to Layerwell's
# parent graph. The unchanged standalone source project retains its defaults.
target_compile_definitions(tide_pit_mutable PRIVATE
    braids=tidepit_private_braids
    stmlib=tidepit_private_stmlib)
target_compile_definitions(tide_pit_core PRIVATE
    braids=tidepit_private_braids
    stmlib=tidepit_private_stmlib)

# Tide Pit's unchanged project owns the one Instrument Lab subdirectory in this
# parent graph. Authenticate Pamplist's configured source, then recreate only
# Pamplist's exact public targets so its standalone CMake and tests stay out of
# the parent graph and all Pamplist project bytes remain read-only.
set(LAYERWELL_PAMPLIST_SOURCE
    "${CMAKE_CURRENT_SOURCE_DIR}/../pamplist")
set(LAYERWELL_PAMPLIST_SOURCE_VERIFIER
    "${LAYERWELL_PAMPLIST_SOURCE}/tests/verify_source_authority.py")
if(NOT PAMPLIST_PATCHER_ROOT)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${LAYERWELL_PAMPLIST_SOURCE_VERIFIER}"
            --print-source-root
        RESULT_VARIABLE LAYERWELL_PAMPLIST_ROOT_RESULT
        OUTPUT_VARIABLE PAMPLIST_PATCHER_ROOT
        ERROR_VARIABLE LAYERWELL_PAMPLIST_ROOT_ERROR
        OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(NOT LAYERWELL_PAMPLIST_ROOT_RESULT EQUAL 0)
        message(FATAL_ERROR
            "Layerwell Pamplist configured source prerequisite failed: ${LAYERWELL_PAMPLIST_ROOT_ERROR}")
    endif()
endif()
cmake_path(ABSOLUTE_PATH PAMPLIST_PATCHER_ROOT NORMALIZE)
execute_process(
    COMMAND "${Python3_EXECUTABLE}" "${LAYERWELL_PAMPLIST_SOURCE_VERIFIER}"
        --source-root "${PAMPLIST_PATCHER_ROOT}"
    RESULT_VARIABLE LAYERWELL_PAMPLIST_SOURCE_RESULT
    OUTPUT_VARIABLE LAYERWELL_PAMPLIST_SOURCE_OUTPUT
    ERROR_VARIABLE LAYERWELL_PAMPLIST_SOURCE_ERROR)
if(NOT LAYERWELL_PAMPLIST_SOURCE_RESULT EQUAL 0)
    message(FATAL_ERROR
        "Layerwell Pamplist source authentication failed: ${LAYERWELL_PAMPLIST_SOURCE_OUTPUT}${LAYERWELL_PAMPLIST_SOURCE_ERROR}")
endif()
set(LAYERWELL_PAMPLIST_SYNTHESIS_DIR
    "${PAMPLIST_PATCHER_ROOT}/ai/sdk/ksoloti-extended/objects/extended/synthesis")

add_library(pamplist_macro_voice STATIC
    "${LAYERWELL_PAMPLIST_SOURCE}/src/macro_voice.cpp")
target_include_directories(pamplist_macro_voice
    PUBLIC "${LAYERWELL_PAMPLIST_SOURCE}/include"
    SYSTEM PRIVATE "${LAYERWELL_PAMPLIST_SYNTHESIS_DIR}")
target_compile_features(pamplist_macro_voice PUBLIC cxx_std_17)
if(CMAKE_CXX_COMPILER_ID MATCHES "AppleClang|Clang|GNU")
    target_compile_options(pamplist_macro_voice PRIVATE -w)
endif()
schuss_instrument_lab_enable_sanitizers(
    pamplist_macro_voice ${LAYERWELL_ENABLE_SANITIZERS})
if(LAYERWELL_ENABLE_SANITIZERS
        AND CMAKE_CXX_COMPILER_ID MATCHES "AppleClang|Clang")
    # The authenticated wrapper converts signed Q15 samples to Q27 with a
    # signed left shift. Keep its exact bytes and all other ASan/UBSan checks,
    # but exclude that known source-boundary operation from shift-base UBSan.
    target_compile_options(pamplist_macro_voice PRIVATE
        -fno-sanitize=shift-base)
endif()

add_library(pamplist_core STATIC
    "${LAYERWELL_PAMPLIST_SOURCE}/src/activity_model.cpp"
    "${LAYERWELL_PAMPLIST_SOURCE}/src/control_map.cpp"
    "${LAYERWELL_PAMPLIST_SOURCE}/src/core.cpp"
    "${LAYERWELL_PAMPLIST_SOURCE}/src/ui_model.cpp")
target_include_directories(pamplist_core
    PUBLIC "${LAYERWELL_PAMPLIST_SOURCE}/include")
target_link_libraries(pamplist_core
    PUBLIC SchussInstrumentLab::Core
    PRIVATE pamplist_macro_voice)
target_compile_features(pamplist_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist_core)
schuss_instrument_lab_enable_sanitizers(
    pamplist_core ${LAYERWELL_ENABLE_SANITIZERS})

add_executable(layerwell_source_link_gate tests/source_link_gate.cpp)
target_link_libraries(layerwell_source_link_gate PRIVATE
    pamplist_core
    tide_pit_core)
target_compile_features(layerwell_source_link_gate PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(layerwell_source_link_gate)
schuss_instrument_lab_enable_sanitizers(
    layerwell_source_link_gate ${LAYERWELL_ENABLE_SANITIZERS})
add_test(NAME layerwell_source_link_gate COMMAND layerwell_source_link_gate)

add_library(layerwell_core STATIC
    src/core.cpp
    src/source_adapters.cpp)
target_include_directories(layerwell_core PUBLIC include)
target_link_libraries(layerwell_core PUBLIC
    pamplist_core
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
        tide_pit_ui_model
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
