cmake_minimum_required(VERSION 3.22)
project(tide_pit_gills_prototype VERSION 0.1.0 LANGUAGES C CXX)

option(TIDE_PIT_ENABLE_JUCE "Build the pinned-JUCE renderer and standalone" OFF)
set(TIDE_PIT_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 tree")
option(TIDE_PIT_ALLOW_JUCE_FETCH "Fetch the exact pinned JUCE archive" OFF)
option(TIDE_PIT_ENABLE_SANITIZERS "Enable ASan and UBSan" OFF)

set(TIDE_PIT_EXPERIMENT_SHA256 "f8baac381d1e83f2e5db6ee4b56988299d5ae7b3e5b1b2ff4bcdfd1a0459c9fd")
set(TIDE_PIT_INSTRUMENT_LAB
    "${CMAKE_CURRENT_SOURCE_DIR}/../../prototype_support/instrument_lab")
add_subdirectory("${TIDE_PIT_INSTRUMENT_LAB}"
    "${CMAKE_CURRENT_BINARY_DIR}/instrument_lab" EXCLUDE_FROM_ALL)
set(TIDE_PIT_MUTABLE_PACKAGE
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../packages/dsp_sources/mutable_ksoloti_v1")
find_package(Python3 COMPONENTS Interpreter REQUIRED)
include("${TIDE_PIT_MUTABLE_PACKAGE}/cmake/MutableKsolotiSource.cmake")
mutable_ksoloti_v1_resolve_components(
    TIDE_PIT_MUTABLE_SOURCES
    braids-resources
    clouds-resources
    stmlib-units-source)

set(TIDE_PIT_PORTED_VOICE
    "${CMAKE_CURRENT_BINARY_DIR}/generated_port/tidepit_voice_ported.h")
add_custom_command(
    OUTPUT "${TIDE_PIT_PORTED_VOICE}"
    COMMAND "${Python3_EXECUTABLE}"
      "${CMAKE_CURRENT_SOURCE_DIR}/tools/generate_ported_tidepit_voice.py"
      --source
      "${CMAKE_CURRENT_SOURCE_DIR}/third_party/tidepit/upstream/tidepit_voice.h"
      --output "${TIDE_PIT_PORTED_VOICE}"
    DEPENDS
      "${CMAKE_CURRENT_SOURCE_DIR}/tools/generate_ported_tidepit_voice.py"
      "${CMAKE_CURRENT_SOURCE_DIR}/third_party/tidepit/upstream/tidepit_voice.h"
    VERBATIM)

add_library(tide_pit_mutable STATIC ${TIDE_PIT_MUTABLE_SOURCES})
target_link_libraries(tide_pit_mutable PUBLIC MutableKsolotiV1::Headers)
target_compile_features(tide_pit_mutable PUBLIC cxx_std_17)
schuss_instrument_lab_enable_sanitizers(tide_pit_mutable ${TIDE_PIT_ENABLE_SANITIZERS})
if(APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    # The canonical source oracle was established with every source TU at -O2.
    target_compile_options(tide_pit_mutable PRIVATE $<$<CONFIG:Release>:-O2>)
endif()

add_library(tide_pit_core STATIC
    src/control_map.cpp
    src/core.cpp
    "${TIDE_PIT_PORTED_VOICE}")
target_include_directories(tide_pit_core
    PUBLIC include generated
    PRIVATE
      src/port_overrides
      third_party/tidepit/upstream
      "${CMAKE_CURRENT_BINARY_DIR}/generated_port")
target_link_libraries(tide_pit_core PUBLIC
    tide_pit_mutable SchussInstrumentLab::Core)
target_compile_features(tide_pit_core PUBLIC cxx_std_17)
target_compile_definitions(tide_pit_core PRIVATE BUFSIZE=16 TEST=1)
schuss_instrument_lab_enable_warnings(tide_pit_core)
schuss_instrument_lab_enable_sanitizers(tide_pit_core ${TIDE_PIT_ENABLE_SANITIZERS})
if(APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    target_compile_options(tide_pit_core PRIVATE $<$<CONFIG:Release>:-O2>)
endif()

add_library(tide_pit_ui_model STATIC src/ui_model.cpp)
target_include_directories(tide_pit_ui_model PUBLIC include)
target_link_libraries(tide_pit_ui_model PUBLIC tide_pit_core)
target_compile_features(tide_pit_ui_model PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(tide_pit_ui_model)
schuss_instrument_lab_enable_sanitizers(tide_pit_ui_model ${TIDE_PIT_ENABLE_SANITIZERS})

enable_testing()
add_test(NAME tide_pit_source_lock
    COMMAND "${Python3_EXECUTABLE}"
      "${CMAKE_CURRENT_SOURCE_DIR}/tests/validate_source_lock.py")
add_test(NAME tide_pit_control_map_fixture
    COMMAND "${Python3_EXECUTABLE}"
      "${CMAKE_CURRENT_SOURCE_DIR}/tests/validate_control_map.py")

foreach(test_target IN ITEMS tide_pit_core_tests tide_pit_reference_golden tide_pit_control_map_tests)
    if(test_target STREQUAL "tide_pit_core_tests")
        set(test_source tests/core_tests.cpp)
    elseif(test_target STREQUAL "tide_pit_reference_golden")
        set(test_source tests/reference_golden_tests.cpp)
    else()
        set(test_source tests/control_map_tests.cpp)
    endif()
    add_executable(${test_target} ${test_source})
    target_link_libraries(${test_target} PRIVATE tide_pit_core)
    target_compile_features(${test_target} PRIVATE cxx_std_17)
    schuss_instrument_lab_enable_warnings(${test_target})
    schuss_instrument_lab_enable_sanitizers(${test_target} ${TIDE_PIT_ENABLE_SANITIZERS})
    add_test(NAME ${test_target} COMMAND ${test_target})
endforeach()

add_executable(tide_pit_ui_model_tests tests/ui_model_tests.cpp)
target_link_libraries(tide_pit_ui_model_tests PRIVATE tide_pit_ui_model)
target_compile_features(tide_pit_ui_model_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(tide_pit_ui_model_tests)
schuss_instrument_lab_enable_sanitizers(tide_pit_ui_model_tests ${TIDE_PIT_ENABLE_SANITIZERS})
add_test(NAME tide_pit_ui_model_tests COMMAND tide_pit_ui_model_tests)

if(APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    target_compile_options(tide_pit_reference_golden PRIVATE $<$<CONFIG:Release>:-O2>)
endif()

if(TIDE_PIT_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${TIDE_PIT_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH "${TIDE_PIT_ALLOW_JUCE_FETCH}")

    add_library(tide_pit_juce_adapter STATIC src/juce_midi_adapter.cpp)
    target_include_directories(tide_pit_juce_adapter PUBLIC include)
    target_link_libraries(tide_pit_juce_adapter PUBLIC
        tide_pit_core juce::juce_audio_basics)
    target_compile_features(tide_pit_juce_adapter PUBLIC cxx_std_17)
    schuss_instrument_lab_enable_warnings(tide_pit_juce_adapter)
    schuss_instrument_lab_enable_sanitizers(tide_pit_juce_adapter ${TIDE_PIT_ENABLE_SANITIZERS})

    add_executable(tide_pit_juce_adapter_tests tests/juce_midi_adapter_tests.cpp)
    target_link_libraries(tide_pit_juce_adapter_tests PRIVATE tide_pit_juce_adapter)
    target_compile_features(tide_pit_juce_adapter_tests PRIVATE cxx_std_17)
    schuss_instrument_lab_enable_warnings(tide_pit_juce_adapter_tests)
    schuss_instrument_lab_enable_sanitizers(tide_pit_juce_adapter_tests ${TIDE_PIT_ENABLE_SANITIZERS})
    add_test(NAME tide_pit_juce_adapter_tests COMMAND tide_pit_juce_adapter_tests)

    add_executable(tide-pit-render src/render.cpp)
    target_link_libraries(tide-pit-render PRIVATE tide_pit_core
        juce::juce_audio_formats juce::juce_core juce::juce_cryptography)
    target_compile_features(tide-pit-render PRIVATE cxx_std_17)
    target_compile_definitions(tide-pit-render PRIVATE
        TIDE_PIT_EXPERIMENT_PATH="${CMAKE_CURRENT_SOURCE_DIR}/experiment.json"
        TIDE_PIT_EXPERIMENT_SHA256="${TIDE_PIT_EXPERIMENT_SHA256}"
        JUCE_USE_CURL=0 JUCE_WEB_BROWSER=0)
    schuss_instrument_lab_enable_warnings(tide-pit-render)
    add_test(NAME tide_pit_render_matrix
        COMMAND "${Python3_EXECUTABLE}"
          "${CMAKE_CURRENT_SOURCE_DIR}/tests/validate_render_matrix.py"
          "$<TARGET_FILE:tide-pit-render>")
    set_tests_properties(tide_pit_render_matrix PROPERTIES LABELS "native;render")

    juce_add_gui_app(tide-pit-gills-instrument
        PRODUCT_NAME "Tide Pit Gills"
        COMPANY_NAME "Schuss"
        BUNDLE_ID "dev.schuss.tide-pit-gills.prototype")
    target_sources(tide-pit-gills-instrument PRIVATE src/juce_main.cpp)
    target_link_libraries(tide-pit-gills-instrument PRIVATE tide_pit_juce_adapter
        tide_pit_ui_model
        juce::juce_audio_basics juce::juce_audio_devices juce::juce_core
        juce::juce_events juce::juce_gui_basics)
    target_compile_features(tide-pit-gills-instrument PRIVATE cxx_std_17)
    target_compile_definitions(tide-pit-gills-instrument PRIVATE
        JUCE_REPORT_APP_USAGE=0 JUCE_USE_CURL=0 JUCE_WEB_BROWSER=0)
    schuss_instrument_lab_enable_warnings(tide-pit-gills-instrument)
endif()
