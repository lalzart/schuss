cmake_minimum_required(VERSION 3.22)
project(tide_pit_gills_prototype VERSION 0.1.0 LANGUAGES C CXX)

option(TIDE_PIT_ENABLE_JUCE "Build the pinned-JUCE renderer and standalone" OFF)
set(TIDE_PIT_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 tree")
option(TIDE_PIT_ALLOW_JUCE_FETCH "Fetch the exact pinned JUCE archive" OFF)
option(TIDE_PIT_ENABLE_SANITIZERS "Enable ASan and UBSan" OFF)

set(TIDE_PIT_JUCE_COMMIT "91ad83ae34a81e0833b1a2b0866f54846370ae53")
set(TIDE_PIT_JUCE_ARCHIVE_SHA256 "04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70")
set(TIDE_PIT_EXPERIMENT_SHA256 "f8baac381d1e83f2e5db6ee4b56988299d5ae7b3e5b1b2ff4bcdfd1a0459c9fd")
set(TIDE_PIT_MUTABLE_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}/third_party/ksoloti/firmware/mutable_instruments")
find_package(Python3 COMPONENTS Interpreter REQUIRED)

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

function(tide_pit_enable_warnings target)
    target_compile_options(${target} PRIVATE
        $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>)
endfunction()

function(tide_pit_enable_sanitizers target)
    if(TIDE_PIT_ENABLE_SANITIZERS
       AND CMAKE_CXX_COMPILER_ID MATCHES "AppleClang|Clang|GNU")
        target_compile_options(${target} PRIVATE -fsanitize=address,undefined)
        target_link_options(${target} PRIVATE -fsanitize=address,undefined)
    endif()
endfunction()

add_library(tide_pit_mutable STATIC
    third_party/ksoloti/firmware/mutable_instruments/braids/braids_resources.cpp
    third_party/ksoloti/firmware/mutable_instruments/clouds/clouds_resources.cpp
    third_party/ksoloti/firmware/mutable_instruments/stmlib/dsp/units.cpp)
target_include_directories(tide_pit_mutable SYSTEM PUBLIC "${TIDE_PIT_MUTABLE_ROOT}")
target_compile_features(tide_pit_mutable PUBLIC cxx_std_17)
tide_pit_enable_sanitizers(tide_pit_mutable)
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
target_link_libraries(tide_pit_core PUBLIC tide_pit_mutable)
target_compile_features(tide_pit_core PUBLIC cxx_std_17)
target_compile_definitions(tide_pit_core PRIVATE BUFSIZE=16 TEST=1)
tide_pit_enable_warnings(tide_pit_core)
tide_pit_enable_sanitizers(tide_pit_core)
if(APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    target_compile_options(tide_pit_core PRIVATE $<$<CONFIG:Release>:-O2>)
endif()

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
    tide_pit_enable_warnings(${test_target})
    tide_pit_enable_sanitizers(${test_target})
    add_test(NAME ${test_target} COMMAND ${test_target})
endforeach()
if(APPLE AND CMAKE_CXX_COMPILER_ID STREQUAL "AppleClang")
    target_compile_options(tide_pit_reference_golden PRIVATE $<$<CONFIG:Release>:-O2>)
endif()

if(TIDE_PIT_ENABLE_JUCE)
    if(TIDE_PIT_JUCE_SOURCE_DIR)
        cmake_path(ABSOLUTE_PATH TIDE_PIT_JUCE_SOURCE_DIR NORMALIZE
            OUTPUT_VARIABLE tide_pit_juce_source)
        if(NOT EXISTS "${tide_pit_juce_source}/CMakeLists.txt"
           OR NOT EXISTS "${tide_pit_juce_source}/modules/juce_core/juce_core.h")
            message(FATAL_ERROR "TIDE_PIT_JUCE_SOURCE_DIR is not a JUCE tree")
        endif()
        file(READ
            "${tide_pit_juce_source}/modules/juce_core/system/juce_StandardHeader.h"
            tide_pit_juce_version_header)
        if(NOT tide_pit_juce_version_header MATCHES "JUCE_MAJOR_VERSION[ \t]+8"
           OR NOT tide_pit_juce_version_header MATCHES "JUCE_MINOR_VERSION[ \t]+0"
           OR NOT tide_pit_juce_version_header MATCHES "JUCE_BUILDNUMBER[ \t]+15")
            message(FATAL_ERROR
                "TIDE_PIT_JUCE_SOURCE_DIR must be JUCE 8.0.15; operator must authenticate bytes")
        endif()
        add_subdirectory("${tide_pit_juce_source}"
            "${CMAKE_CURRENT_BINARY_DIR}/juce" EXCLUDE_FROM_ALL)
    elseif(TIDE_PIT_ALLOW_JUCE_FETCH)
        include(FetchContent)
        FetchContent_Declare(JUCE
            URL "https://github.com/juce-framework/JUCE/archive/${TIDE_PIT_JUCE_COMMIT}.tar.gz"
            URL_HASH "SHA256=${TIDE_PIT_JUCE_ARCHIVE_SHA256}"
            DOWNLOAD_EXTRACT_TIMESTAMP FALSE)
        FetchContent_MakeAvailable(JUCE)
    else()
        message(FATAL_ERROR
            "TIDE_PIT_ENABLE_JUCE requires TIDE_PIT_JUCE_SOURCE_DIR or TIDE_PIT_ALLOW_JUCE_FETCH=ON")
    endif()

    add_library(tide_pit_juce_adapter STATIC src/juce_midi_adapter.cpp)
    target_include_directories(tide_pit_juce_adapter PUBLIC include)
    target_link_libraries(tide_pit_juce_adapter PUBLIC
        tide_pit_core juce::juce_audio_basics)
    target_compile_features(tide_pit_juce_adapter PUBLIC cxx_std_17)
    tide_pit_enable_warnings(tide_pit_juce_adapter)
    tide_pit_enable_sanitizers(tide_pit_juce_adapter)

    add_executable(tide_pit_juce_adapter_tests tests/juce_midi_adapter_tests.cpp)
    target_link_libraries(tide_pit_juce_adapter_tests PRIVATE tide_pit_juce_adapter)
    target_compile_features(tide_pit_juce_adapter_tests PRIVATE cxx_std_17)
    tide_pit_enable_warnings(tide_pit_juce_adapter_tests)
    tide_pit_enable_sanitizers(tide_pit_juce_adapter_tests)
    add_test(NAME tide_pit_juce_adapter_tests COMMAND tide_pit_juce_adapter_tests)

    add_executable(tide-pit-render src/render.cpp)
    target_link_libraries(tide-pit-render PRIVATE tide_pit_core
        juce::juce_audio_formats juce::juce_core juce::juce_cryptography)
    target_compile_features(tide-pit-render PRIVATE cxx_std_17)
    target_compile_definitions(tide-pit-render PRIVATE
        TIDE_PIT_EXPERIMENT_PATH="${CMAKE_CURRENT_SOURCE_DIR}/experiment.json"
        TIDE_PIT_EXPERIMENT_SHA256="${TIDE_PIT_EXPERIMENT_SHA256}"
        JUCE_USE_CURL=0 JUCE_WEB_BROWSER=0)
    tide_pit_enable_warnings(tide-pit-render)
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
        juce::juce_audio_basics juce::juce_audio_devices juce::juce_core
        juce::juce_events juce::juce_gui_basics)
    target_compile_features(tide-pit-gills-instrument PRIVATE cxx_std_17)
    target_compile_definitions(tide-pit-gills-instrument PRIVATE
        JUCE_REPORT_APP_USAGE=0 JUCE_USE_CURL=0 JUCE_WEB_BROWSER=0)
    tide_pit_enable_warnings(tide-pit-gills-instrument)
endif()
