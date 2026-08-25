cmake_minimum_required(VERSION 3.22)

project(murmur_map_prototype VERSION 0.1.0 LANGUAGES C CXX)

option(MURMUR_MAP_ENABLE_JUCE "Build the authenticated JUCE standalone" OFF)
set(MURMUR_MAP_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 source tree")
option(MURMUR_MAP_ALLOW_JUCE_FETCH "Fetch the exact pinned JUCE archive" OFF)

enable_testing()

set(MURMUR_MAP_INSTRUMENT_LAB
    "${CMAKE_CURRENT_SOURCE_DIR}/../../prototype_support/instrument_lab")
add_subdirectory("${MURMUR_MAP_INSTRUMENT_LAB}"
    "${CMAKE_CURRENT_BINARY_DIR}/instrument_lab" EXCLUDE_FROM_ALL)

set(MURMUR_MAP_MUTABLE_BRAIDS_ADAPTER
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../packages/dsp_adapters/mutable_braids_v1")
add_subdirectory("${MURMUR_MAP_MUTABLE_BRAIDS_ADAPTER}"
    "${CMAKE_CURRENT_BINARY_DIR}/mutable_braids_v1")

add_library(murmur_map_core STATIC
    src/control_map.cpp
    src/core.cpp)
target_include_directories(murmur_map_core PUBLIC include)
target_link_libraries(murmur_map_core
    PUBLIC SchussInstrumentLab::Core
    PRIVATE SchussMutableBraidsV1::Core)
target_compile_features(murmur_map_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(murmur_map_core)

add_library(murmur_map_ui_support STATIC src/ui_model.cpp)
target_include_directories(murmur_map_ui_support PUBLIC include)
target_link_libraries(murmur_map_ui_support PUBLIC murmur_map_core)
target_compile_features(murmur_map_ui_support PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(murmur_map_ui_support)

add_executable(murmur-map-render src/render.cpp)
target_link_libraries(murmur-map-render PRIVATE murmur_map_core)
target_compile_features(murmur-map-render PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(murmur-map-render)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
find_package(Threads REQUIRED)

add_executable(murmur_map_core_tests tests/core_tests.cpp)
target_link_libraries(murmur_map_core_tests PRIVATE murmur_map_core)
target_compile_features(murmur_map_core_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(murmur_map_core_tests)
add_test(NAME murmur_map_core_tests COMMAND murmur_map_core_tests)

add_executable(murmur_map_control_map_tests tests/control_map_tests.cpp)
target_link_libraries(murmur_map_control_map_tests PRIVATE murmur_map_core)
target_compile_features(murmur_map_control_map_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(murmur_map_control_map_tests)
add_test(NAME murmur_map_control_map_tests COMMAND murmur_map_control_map_tests)

add_executable(murmur_map_exchange_tests tests/realtime_exchange_tests.cpp)
target_link_libraries(murmur_map_exchange_tests PRIVATE murmur_map_core Threads::Threads)
target_compile_features(murmur_map_exchange_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(murmur_map_exchange_tests)
add_test(NAME murmur_map_exchange_tests COMMAND murmur_map_exchange_tests)

add_executable(murmur_map_ui_model_tests tests/ui_model_tests.cpp)
target_link_libraries(murmur_map_ui_model_tests PRIVATE murmur_map_ui_support)
target_compile_features(murmur_map_ui_model_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(murmur_map_ui_model_tests)
add_test(NAME murmur_map_ui_model_tests COMMAND murmur_map_ui_model_tests)

add_test(NAME murmur_map_source_authorities
    COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/verify_source_authorities.py")

if(MURMUR_MAP_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${MURMUR_MAP_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH "${MURMUR_MAP_ALLOW_JUCE_FETCH}")

    juce_add_gui_app(murmur-map
        PRODUCT_NAME "Murmur Map"
        COMPANY_NAME "Schuss"
        BUNDLE_ID "dev.schuss.murmur-map.prototype")
    target_sources(murmur-map PRIVATE src/juce_main.cpp)
    target_link_libraries(murmur-map PRIVATE
        murmur_map_ui_support
        juce::juce_audio_basics
        juce::juce_audio_devices
        juce::juce_core
        juce::juce_events
        juce::juce_gui_basics)
    target_compile_features(murmur-map PRIVATE cxx_std_17)
    target_compile_definitions(murmur-map PRIVATE
        JUCE_REPORT_APP_USAGE=0
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0)
    schuss_instrument_lab_enable_warnings(murmur-map)
endif()
