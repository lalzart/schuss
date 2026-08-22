cmake_minimum_required(VERSION 3.22)

project(wirefall_r02_prototype VERSION 0.2.0 LANGUAGES C CXX)

option(WIREFALL_R02_ENABLE_SANITIZERS "Enable address and undefined behavior sanitizers" OFF)
option(WIREFALL_R02_ENABLE_JUCE "Configure the authenticated JUCE standalone target" OFF)
set(WIREFALL_R02_JUCE_SOURCE_DIR "" CACHE PATH "Operator-authenticated extracted JUCE 8.0.15 source directory")

set(WIREFALL_R02_INSTRUMENT_LAB
    "${CMAKE_CURRENT_SOURCE_DIR}/../../prototype_support/instrument_lab")
add_subdirectory(
    "${WIREFALL_R02_INSTRUMENT_LAB}"
    "${CMAKE_CURRENT_BINARY_DIR}/instrument_lab"
    EXCLUDE_FROM_ALL
)

add_library(wirefall_r02_core STATIC
    core/WirefallR02Core.cpp
)
target_include_directories(wirefall_r02_core PUBLIC core)
target_link_libraries(wirefall_r02_core PUBLIC SchussInstrumentLab::Core)
target_compile_features(wirefall_r02_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(wirefall_r02_core)

if(WIREFALL_R02_ENABLE_SANITIZERS)
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
        target_compile_options(wirefall_r02_core PUBLIC
            -fno-omit-frame-pointer -fsanitize=address,undefined)
        target_link_options(wirefall_r02_core PUBLIC
            -fno-omit-frame-pointer -fsanitize=address,undefined)
    else()
        message(FATAL_ERROR "Wirefall revision 0.2 sanitizers require Clang or GNU")
    endif()
endif()

add_executable(wirefall_r02_render render/main.cpp)
target_link_libraries(wirefall_r02_render PRIVATE wirefall_r02_core)
target_compile_features(wirefall_r02_render PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(wirefall_r02_render)

enable_testing()
add_executable(wirefall_r02_core_tests tests/core_tests.cpp)
target_link_libraries(wirefall_r02_core_tests PRIVATE wirefall_r02_core)
target_compile_features(wirefall_r02_core_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(wirefall_r02_core_tests)
add_test(NAME wirefall_r02_core_tests COMMAND wirefall_r02_core_tests)

if(WIREFALL_R02_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${WIREFALL_R02_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH OFF
    )

    juce_add_gui_app(wirefall-r02-instrument
        PRODUCT_NAME "Wirefall 0.2"
        COMPANY_NAME "Schuss"
        BUNDLE_ID "dev.schuss.wirefall-r02.prototype"
    )
    target_sources(wirefall-r02-instrument PRIVATE standalone/Main.cpp)
    target_link_libraries(wirefall-r02-instrument PRIVATE
        wirefall_r02_core
        juce::juce_audio_basics
        juce::juce_audio_devices
        juce::juce_core
        juce::juce_events
        juce::juce_graphics
        juce::juce_gui_basics
    )
    target_compile_features(wirefall-r02-instrument PRIVATE cxx_std_17)
    target_compile_definitions(wirefall-r02-instrument PRIVATE
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0
    )
    schuss_instrument_lab_enable_warnings(wirefall-r02-instrument)
endif()
