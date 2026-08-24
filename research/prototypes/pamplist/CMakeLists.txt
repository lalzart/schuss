cmake_minimum_required(VERSION 3.22)

project(schuss_pamplist_prototype VERSION 0.5.0 LANGUAGES C CXX)

option(PAMPLIST_ENABLE_JUCE "Build the authenticated-JUCE standalone UI" OFF)
set(PAMPLIST_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 source tree")
option(PAMPLIST_ALLOW_JUCE_FETCH "Fetch JUCE instead of using authenticated local bytes" OFF)
set(PAMPLIST_PATCHER_ROOT "" CACHE PATH "Configured locked patcher checkout")
option(PAMPLIST_ENABLE_SANITIZERS "Build Pamplist tests with ASan and UBSan" OFF)

enable_testing()
find_package(Python3 COMPONENTS Interpreter REQUIRED)
find_package(Threads REQUIRED)

set(PAMPLIST_INSTRUMENT_LAB
    "${CMAKE_CURRENT_SOURCE_DIR}/../../prototype_support/instrument_lab")
add_subdirectory(
    "${PAMPLIST_INSTRUMENT_LAB}"
    "${CMAKE_CURRENT_BINARY_DIR}/instrument_lab"
    EXCLUDE_FROM_ALL)

set(PAMPLIST_SOURCE_VERIFIER
    "${CMAKE_CURRENT_SOURCE_DIR}/tests/verify_source_authority.py")
if(NOT PAMPLIST_PATCHER_ROOT)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${PAMPLIST_SOURCE_VERIFIER}"
            --print-source-root
        RESULT_VARIABLE PAMPLIST_SOURCE_ROOT_RESULT
        OUTPUT_VARIABLE PAMPLIST_PATCHER_ROOT
        ERROR_VARIABLE PAMPLIST_SOURCE_ROOT_ERROR
        OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(NOT PAMPLIST_SOURCE_ROOT_RESULT EQUAL 0)
        message(FATAL_ERROR
            "Pamplist configured source prerequisite failed: ${PAMPLIST_SOURCE_ROOT_ERROR}")
    endif()
endif()
cmake_path(ABSOLUTE_PATH PAMPLIST_PATCHER_ROOT NORMALIZE)
execute_process(
    COMMAND "${Python3_EXECUTABLE}" "${PAMPLIST_SOURCE_VERIFIER}"
        --source-root "${PAMPLIST_PATCHER_ROOT}"
    RESULT_VARIABLE PAMPLIST_SOURCE_RESULT
    OUTPUT_VARIABLE PAMPLIST_SOURCE_OUTPUT
    ERROR_VARIABLE PAMPLIST_SOURCE_ERROR)
if(NOT PAMPLIST_SOURCE_RESULT EQUAL 0)
    message(FATAL_ERROR
        "Pamplist source authentication failed: ${PAMPLIST_SOURCE_OUTPUT}${PAMPLIST_SOURCE_ERROR}")
endif()
set(PAMPLIST_SYNTHESIS_DIR
    "${PAMPLIST_PATCHER_ROOT}/ai/sdk/ksoloti-extended/objects/extended/synthesis")

add_library(pamplist_macro_voice STATIC src/macro_voice.cpp)
target_include_directories(pamplist_macro_voice
    PUBLIC include
    SYSTEM PRIVATE "${PAMPLIST_SYNTHESIS_DIR}")
target_compile_features(pamplist_macro_voice PUBLIC cxx_std_17)
if(CMAKE_CXX_COMPILER_ID MATCHES "AppleClang|Clang|GNU")
    # The authenticated source compiles byte-authentically; upstream warnings
    # are not rewritten or promoted into project-authored warning policy.
    target_compile_options(pamplist_macro_voice PRIVATE -w)
endif()
schuss_instrument_lab_enable_sanitizers(
    pamplist_macro_voice ${PAMPLIST_ENABLE_SANITIZERS})

add_library(pamplist_core STATIC
    src/control_map.cpp
    src/core.cpp
    src/ui_model.cpp)
target_include_directories(pamplist_core PUBLIC include)
target_link_libraries(pamplist_core
    PUBLIC SchussInstrumentLab::Core
    PRIVATE pamplist_macro_voice)
target_compile_features(pamplist_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist_core)
schuss_instrument_lab_enable_sanitizers(
    pamplist_core ${PAMPLIST_ENABLE_SANITIZERS})

add_executable(pamplist-render src/render.cpp)
target_link_libraries(pamplist-render PRIVATE pamplist_core)
target_compile_features(pamplist-render PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist-render)
schuss_instrument_lab_enable_sanitizers(
    pamplist-render ${PAMPLIST_ENABLE_SANITIZERS})

add_executable(pamplist_core_tests tests/core_tests.cpp)
target_link_libraries(pamplist_core_tests PRIVATE pamplist_core)
target_compile_features(pamplist_core_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist_core_tests)
schuss_instrument_lab_enable_sanitizers(
    pamplist_core_tests ${PAMPLIST_ENABLE_SANITIZERS})
add_test(NAME pamplist_core_tests COMMAND pamplist_core_tests)

add_executable(pamplist_control_map_tests tests/control_map_tests.cpp)
target_link_libraries(pamplist_control_map_tests PRIVATE pamplist_core)
target_compile_features(pamplist_control_map_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist_control_map_tests)
schuss_instrument_lab_enable_sanitizers(
    pamplist_control_map_tests ${PAMPLIST_ENABLE_SANITIZERS})
add_test(NAME pamplist_control_map_tests COMMAND pamplist_control_map_tests)

add_executable(pamplist_ui_model_tests tests/ui_model_tests.cpp)
target_link_libraries(pamplist_ui_model_tests PRIVATE pamplist_core)
target_compile_features(pamplist_ui_model_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist_ui_model_tests)
schuss_instrument_lab_enable_sanitizers(
    pamplist_ui_model_tests ${PAMPLIST_ENABLE_SANITIZERS})
add_test(NAME pamplist_ui_model_tests COMMAND pamplist_ui_model_tests)

add_executable(pamplist_snapshot_tests tests/snapshot_tests.cpp)
target_link_libraries(pamplist_snapshot_tests PRIVATE pamplist_core Threads::Threads)
target_compile_features(pamplist_snapshot_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist_snapshot_tests)
schuss_instrument_lab_enable_sanitizers(
    pamplist_snapshot_tests ${PAMPLIST_ENABLE_SANITIZERS})
add_test(NAME pamplist_snapshot_tests COMMAND pamplist_snapshot_tests)

add_executable(pamplist_allocation_tests tests/allocation_tests.cpp)
target_link_libraries(pamplist_allocation_tests PRIVATE pamplist_core)
target_compile_features(pamplist_allocation_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist_allocation_tests)
schuss_instrument_lab_enable_sanitizers(
    pamplist_allocation_tests ${PAMPLIST_ENABLE_SANITIZERS})
add_test(NAME pamplist_allocation_tests COMMAND pamplist_allocation_tests)

if(PAMPLIST_ENABLE_JUCE)
    schuss_instrument_lab_add_authenticated_juce(
        SOURCE_DIR "${PAMPLIST_JUCE_SOURCE_DIR}"
        BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
        ALLOW_FETCH "${PAMPLIST_ALLOW_JUCE_FETCH}")

    juce_add_gui_app(pamplist
        PRODUCT_NAME "Pamplist"
        COMPANY_NAME "Schuss"
        BUNDLE_ID "dev.schuss.pamplist.prototype")
    target_sources(pamplist PRIVATE src/juce_main.cpp)
    target_link_libraries(pamplist PRIVATE
        pamplist_core
        juce::juce_audio_basics
        juce::juce_audio_devices
        juce::juce_core
        juce::juce_events
        juce::juce_gui_basics)
    target_compile_features(pamplist PRIVATE cxx_std_17)
    target_compile_definitions(pamplist PRIVATE
        JUCE_REPORT_APP_USAGE=0
        JUCE_USE_CURL=0
        JUCE_WEB_BROWSER=0)
    schuss_instrument_lab_enable_warnings(pamplist)
endif()
