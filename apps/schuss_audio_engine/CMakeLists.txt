cmake_minimum_required(VERSION 3.22)
project(schuss_audio_engine VERSION 0.1.0 LANGUAGES C CXX)

option(SCHUSS_ENABLE_JUCE "Build the pinned headless JUCE device engine" OFF)
option(SCHUSS_ENGINE_BUILD_TESTS "Build the JUCE-free engine queue tests" ON)

set(SCHUSS_RT_BUILD_TESTS OFF CACHE BOOL "" FORCE)
add_subdirectory(../../packages/schuss_rt schuss_rt)

add_executable(schuss-offline-render
    src/offline_main.cpp
)
target_link_libraries(schuss-offline-render PRIVATE schuss_rt)
target_compile_features(schuss-offline-render PRIVATE cxx_std_17)
target_compile_options(schuss-offline-render PRIVATE
    $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
)

if(SCHUSS_ENGINE_BUILD_TESTS)
    enable_testing()
    add_executable(schuss_midi_ingress_tests tests/midi_ingress_tests.cpp)
    target_include_directories(schuss_midi_ingress_tests PRIVATE src)
    target_compile_features(schuss_midi_ingress_tests PRIVATE cxx_std_17)
    target_compile_options(schuss_midi_ingress_tests PRIVATE
        $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
    )
    add_test(NAME schuss_midi_ingress_tests COMMAND schuss_midi_ingress_tests)
endif()

if(SCHUSS_ENABLE_JUCE)
    include(FetchContent)
    FetchContent_Declare(
        JUCE
        URL https://github.com/juce-framework/JUCE/archive/91ad83ae34a81e0833b1a2b0866f54846370ae53.tar.gz
        URL_HASH SHA256=04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70
        DOWNLOAD_EXTRACT_TIMESTAMP FALSE
    )
    FetchContent_MakeAvailable(JUCE)
    add_executable(schuss-audio-engine
        src/engine_main.cpp
    )
    target_link_libraries(schuss-audio-engine PRIVATE
        schuss_rt
        juce::juce_audio_basics
        juce::juce_audio_devices
        juce::juce_core
        juce::juce_events
    )
    target_compile_features(schuss-audio-engine PRIVATE cxx_std_17)
    target_compile_options(schuss-audio-engine PRIVATE
        $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
    )
    target_compile_definitions(schuss-audio-engine PRIVATE
        JUCE_DISPLAY_SPLASH_SCREEN=0
        JUCE_REPORT_APP_USAGE=0
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0
    )
endif()
