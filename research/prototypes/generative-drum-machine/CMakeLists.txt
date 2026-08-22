cmake_minimum_required(VERSION 3.22)

project(schuss_generative_drum_machine_prototype VERSION 0.3.0 LANGUAGES C CXX)

option(GDM_ENABLE_JUCE "Build the authenticated-JUCE standalone audition UI" OFF)
set(GDM_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 source tree")
option(GDM_ALLOW_JUCE_FETCH "Fetch the exact pinned JUCE archive" OFF)
enable_testing()

set(GDM_INSTRUMENT_LAB
    "${CMAKE_CURRENT_SOURCE_DIR}/../../prototype_support/instrument_lab")
add_subdirectory("${GDM_INSTRUMENT_LAB}"
    "${CMAKE_CURRENT_BINARY_DIR}/instrument_lab" EXCLUDE_FROM_ALL)

set(GDM_MUTABLE_BRAIDS_ADAPTER
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../packages/dsp_adapters/mutable_braids_v1")
add_subdirectory("${GDM_MUTABLE_BRAIDS_ADAPTER}"
    "${CMAKE_CURRENT_BINARY_DIR}/mutable_braids_v1")

add_library(generative_drum_machine_core STATIC
    src/control_map.cpp
    src/core.cpp)
target_include_directories(generative_drum_machine_core
    PUBLIC include
    PRIVATE generated)
target_link_libraries(generative_drum_machine_core
    PUBLIC SchussInstrumentLab::Core
    PRIVATE SchussMutableBraidsV1::Core)
target_compile_features(generative_drum_machine_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(generative_drum_machine_core)

add_library(generative_drum_machine_ui_support STATIC
    src/ui_model.cpp)
target_include_directories(generative_drum_machine_ui_support PUBLIC include)
target_link_libraries(generative_drum_machine_ui_support
    PUBLIC generative_drum_machine_core)
target_compile_features(generative_drum_machine_ui_support PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(generative_drum_machine_ui_support)

add_executable(generative-drum-machine-render src/render.cpp)
target_link_libraries(generative-drum-machine-render PRIVATE generative_drum_machine_core)
target_compile_features(generative-drum-machine-render PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(generative-drum-machine-render)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
find_package(Threads REQUIRED)

add_executable(generative_drum_machine_tests tests/core_tests.cpp)
target_link_libraries(generative_drum_machine_tests PRIVATE generative_drum_machine_core)
target_compile_features(generative_drum_machine_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(generative_drum_machine_tests)
add_test(NAME generative_drum_machine_tests COMMAND generative_drum_machine_tests)

add_executable(generative_drum_machine_control_map_tests tests/control_map_tests.cpp)
target_link_libraries(generative_drum_machine_control_map_tests PRIVATE generative_drum_machine_core)
target_compile_features(generative_drum_machine_control_map_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(generative_drum_machine_control_map_tests)
add_test(
    NAME generative_drum_machine_control_map_tests
    COMMAND generative_drum_machine_control_map_tests)

add_executable(generative_drum_machine_control_snapshot_tests
    tests/control_snapshot_tests.cpp)
target_link_libraries(generative_drum_machine_control_snapshot_tests
    PRIVATE generative_drum_machine_core Threads::Threads)
target_compile_features(generative_drum_machine_control_snapshot_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(generative_drum_machine_control_snapshot_tests)
add_test(
    NAME generative_drum_machine_control_snapshot_tests
    COMMAND generative_drum_machine_control_snapshot_tests)

add_executable(generative_drum_machine_ui_model_tests tests/ui_model_tests.cpp)
target_link_libraries(generative_drum_machine_ui_model_tests
    PRIVATE generative_drum_machine_ui_support)
target_compile_features(generative_drum_machine_ui_model_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(generative_drum_machine_ui_model_tests)
add_test(
    NAME generative_drum_machine_ui_model_tests
    COMMAND generative_drum_machine_ui_model_tests)

add_executable(generative_drum_machine_realtime_benchmark tests/realtime_benchmark.cpp)
target_link_libraries(generative_drum_machine_realtime_benchmark
    PRIVATE generative_drum_machine_core)
target_compile_features(generative_drum_machine_realtime_benchmark PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(generative_drum_machine_realtime_benchmark)

add_test(
    NAME generative_drum_machine_fixture_freshness
    COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/tools/generate_fixture.py" --check)
add_test(
    NAME generative_drum_machine_control_descriptor_freshness
    COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/tools/generate_control_descriptors.py" --check)
add_test(
    NAME generative_drum_machine_source_dependencies_freshness
    COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/../../../tools/instrument_lab/generate_task038_source_dependencies.py"
            --check)

if(GDM_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${GDM_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH "${GDM_ALLOW_JUCE_FETCH}")

    juce_add_gui_app(schuss-generative-drums
        PRODUCT_NAME "Schuss Generative Drums"
        COMPANY_NAME "Schuss"
        BUNDLE_ID "dev.schuss.generative-drums.prototype")
    target_sources(schuss-generative-drums PRIVATE src/juce_main.cpp)
    target_link_libraries(schuss-generative-drums PRIVATE
        generative_drum_machine_ui_support
        juce::juce_audio_basics
        juce::juce_audio_devices
        juce::juce_core
        juce::juce_events
        juce::juce_gui_basics)
    target_compile_features(schuss-generative-drums PRIVATE cxx_std_17)
    target_compile_definitions(schuss-generative-drums PRIVATE
        JUCE_REPORT_APP_USAGE=0
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0)
    schuss_instrument_lab_enable_warnings(schuss-generative-drums)
endif()
