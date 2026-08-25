cmake_minimum_required(VERSION 3.22)

project(wanderbody_prototype VERSION 0.1.0 LANGUAGES C CXX)

option(WANDERBODY_ENABLE_SANITIZERS "Enable address and undefined behavior sanitizers" OFF)
option(WANDERBODY_ENABLE_JUCE "Build the authenticated JUCE standalone" OFF)
set(WANDERBODY_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 source tree")
option(WANDERBODY_ALLOW_JUCE_FETCH "Allow the exact pinned JUCE archive fetch" OFF)

set(WANDERBODY_INSTRUMENT_LAB
    "${CMAKE_CURRENT_SOURCE_DIR}/../../prototype_support/instrument_lab")
add_subdirectory(
    "${WANDERBODY_INSTRUMENT_LAB}"
    "${CMAKE_CURRENT_BINARY_DIR}/instrument_lab"
    EXCLUDE_FROM_ALL)

add_library(wanderbody_core STATIC
    src/control_surface.cpp
    src/core.cpp)
target_include_directories(wanderbody_core PUBLIC include)
target_link_libraries(wanderbody_core PUBLIC SchussInstrumentLab::Core)
target_compile_features(wanderbody_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(wanderbody_core)

if(WANDERBODY_ENABLE_SANITIZERS)
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
        target_compile_options(wanderbody_core PUBLIC
            -fno-omit-frame-pointer -fsanitize=address,undefined)
        target_link_options(wanderbody_core PUBLIC
            -fno-omit-frame-pointer -fsanitize=address,undefined)
    else()
        message(FATAL_ERROR "Wanderbody sanitizers require Clang or GNU")
    endif()
endif()

add_executable(wanderbody-render src/render.cpp)
target_link_libraries(wanderbody-render PRIVATE wanderbody_core)
target_compile_features(wanderbody-render PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(wanderbody-render)

enable_testing()

add_executable(wanderbody_core_tests tests/core_tests.cpp)
target_link_libraries(wanderbody_core_tests PRIVATE wanderbody_core)
target_compile_features(wanderbody_core_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(wanderbody_core_tests)
add_test(NAME wanderbody_core_tests COMMAND wanderbody_core_tests)

add_executable(wanderbody_allocation_tests tests/allocation_tests.cpp)
target_link_libraries(wanderbody_allocation_tests PRIVATE wanderbody_core)
target_compile_features(wanderbody_allocation_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(wanderbody_allocation_tests)
add_test(NAME wanderbody_allocation_tests COMMAND wanderbody_allocation_tests)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(
    NAME wanderbody_contract_surface
    COMMAND "${Python3_EXECUTABLE}"
            "${CMAKE_CURRENT_SOURCE_DIR}/tests/verify_contract_surface.py")

if(WANDERBODY_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${WANDERBODY_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH "${WANDERBODY_ALLOW_JUCE_FETCH}")

    juce_add_gui_app(wanderbody-instrument
        PRODUCT_NAME "Wanderbody 0.1"
        COMPANY_NAME "Schuss"
        BUNDLE_ID "dev.schuss.wanderbody.prototype")
    target_sources(wanderbody-instrument PRIVATE src/juce_main.cpp)
    target_link_libraries(wanderbody-instrument PRIVATE
        wanderbody_core
        juce::juce_audio_basics
        juce::juce_audio_devices
        juce::juce_audio_utils
        juce::juce_core
        juce::juce_events
        juce::juce_graphics
        juce::juce_gui_basics)
    target_compile_features(wanderbody-instrument PRIVATE cxx_std_17)
    target_compile_definitions(wanderbody-instrument PRIVATE
        JUCE_REPORT_APP_USAGE=0
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0)
    schuss_instrument_lab_enable_warnings(wanderbody-instrument)
endif()
