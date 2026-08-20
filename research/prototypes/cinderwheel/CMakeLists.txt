cmake_minimum_required(VERSION 3.22)

project(cinderwheel_prototype VERSION 0.1.0 LANGUAGES C CXX)

option(
    CINDERWHEEL_ENABLE_JUCE
    "Build the pinned-JUCE renderer and standalone instrument"
    OFF
)
set(
    CINDERWHEEL_JUCE_SOURCE_DIR
    ""
    CACHE PATH
    "Operator-authenticated extracted JUCE 8.0.15 source directory"
)
option(
    CINDERWHEEL_ALLOW_JUCE_FETCH
    "Allow CMake to fetch the exact pinned JUCE archive"
    OFF
)

set(CINDERWHEEL_INSTRUMENT_LAB
    "${CMAKE_CURRENT_SOURCE_DIR}/../../prototype_support/instrument_lab")
add_subdirectory("${CINDERWHEEL_INSTRUMENT_LAB}"
    "${CMAKE_CURRENT_BINARY_DIR}/instrument_lab" EXCLUDE_FROM_ALL)

add_library(cinderwheel_core STATIC
    src/control_map.cpp
    src/core.cpp
)
target_include_directories(cinderwheel_core PUBLIC include)
target_link_libraries(cinderwheel_core PUBLIC SchussInstrumentLab::Core)
target_compile_features(cinderwheel_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(cinderwheel_core)

add_library(cinderwheel_ui_model STATIC src/ui_model.cpp)
target_include_directories(cinderwheel_ui_model PUBLIC include)
target_link_libraries(cinderwheel_ui_model PUBLIC cinderwheel_core)
target_compile_features(cinderwheel_ui_model PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(cinderwheel_ui_model)

enable_testing()
add_executable(cinderwheel_core_tests
    tests/core_tests.cpp
)
target_link_libraries(cinderwheel_core_tests PRIVATE cinderwheel_core)
target_compile_features(cinderwheel_core_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(cinderwheel_core_tests)
add_test(NAME cinderwheel_core_tests COMMAND cinderwheel_core_tests)

add_executable(cinderwheel_ui_model_tests tests/ui_model_tests.cpp)
target_link_libraries(cinderwheel_ui_model_tests PRIVATE cinderwheel_ui_model)
target_compile_features(cinderwheel_ui_model_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(cinderwheel_ui_model_tests)
add_test(NAME cinderwheel_ui_model_tests COMMAND cinderwheel_ui_model_tests)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(
    NAME cinderwheel_mapping_fixture
    COMMAND
        "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/validate_mapping.py"
)

if(CINDERWHEEL_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${CINDERWHEEL_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH "${CINDERWHEEL_ALLOW_JUCE_FETCH}")

    add_library(cinderwheel_juce_adapter STATIC
        src/juce_midi_adapter.cpp
    )
    target_include_directories(cinderwheel_juce_adapter PUBLIC include)
    target_link_libraries(cinderwheel_juce_adapter PUBLIC
        cinderwheel_core
        juce::juce_audio_basics
    )
    target_compile_features(cinderwheel_juce_adapter PUBLIC cxx_std_17)
    schuss_instrument_lab_enable_warnings(cinderwheel_juce_adapter)

    add_executable(cinderwheel_juce_adapter_tests
        tests/juce_midi_adapter_tests.cpp
    )
    target_link_libraries(cinderwheel_juce_adapter_tests PRIVATE
        cinderwheel_juce_adapter
    )
    target_compile_features(cinderwheel_juce_adapter_tests PRIVATE cxx_std_17)
    schuss_instrument_lab_enable_warnings(cinderwheel_juce_adapter_tests)
    add_test(
        NAME cinderwheel_juce_adapter_tests
        COMMAND cinderwheel_juce_adapter_tests
    )

    add_executable(cinderwheel-render
        src/render.cpp
    )
    target_link_libraries(cinderwheel-render PRIVATE
        cinderwheel_core
        juce::juce_audio_formats
        juce::juce_core
    )
    target_compile_features(cinderwheel-render PRIVATE cxx_std_17)
    target_compile_definitions(cinderwheel-render PRIVATE
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0
    )
    schuss_instrument_lab_enable_warnings(cinderwheel-render)
    add_test(
        NAME cinderwheel_render_matrix
        COMMAND
            "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/validate_render_matrix.py"
            "$<TARGET_FILE:cinderwheel-render>"
    )
    set_tests_properties(cinderwheel_render_matrix PROPERTIES LABELS "native;render")

    juce_add_gui_app(cinderwheel-instrument
        PRODUCT_NAME "Cinderwheel"
        COMPANY_NAME "Schuss"
        BUNDLE_ID "dev.schuss.cinderwheel.prototype"
    )
    target_sources(cinderwheel-instrument PRIVATE
        src/juce_main.cpp
    )
    target_link_libraries(cinderwheel-instrument PRIVATE
        cinderwheel_juce_adapter
        cinderwheel_ui_model
        juce::juce_audio_basics
        juce::juce_audio_devices
        juce::juce_core
        juce::juce_events
        juce::juce_gui_basics
    )
    target_compile_features(cinderwheel-instrument PRIVATE cxx_std_17)
    target_compile_definitions(cinderwheel-instrument PRIVATE
        JUCE_REPORT_APP_USAGE=0
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0
    )
    schuss_instrument_lab_enable_warnings(cinderwheel-instrument)
endif()
