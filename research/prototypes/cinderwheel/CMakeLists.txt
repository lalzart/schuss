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

set(CINDERWHEEL_JUCE_COMMIT "91ad83ae34a81e0833b1a2b0866f54846370ae53")
set(CINDERWHEEL_JUCE_ARCHIVE_SHA256 "04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70")

function(cinderwheel_enable_warnings target)
    target_compile_options(${target} PRIVATE
        $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
    )
endfunction()

add_library(cinderwheel_core STATIC
    src/control_map.cpp
    src/core.cpp
)
target_include_directories(cinderwheel_core PUBLIC include)
target_compile_features(cinderwheel_core PUBLIC cxx_std_17)
cinderwheel_enable_warnings(cinderwheel_core)

enable_testing()
add_executable(cinderwheel_core_tests
    tests/core_tests.cpp
)
target_link_libraries(cinderwheel_core_tests PRIVATE cinderwheel_core)
target_compile_features(cinderwheel_core_tests PRIVATE cxx_std_17)
cinderwheel_enable_warnings(cinderwheel_core_tests)
add_test(NAME cinderwheel_core_tests COMMAND cinderwheel_core_tests)

find_package(Python3 COMPONENTS Interpreter REQUIRED)
add_test(
    NAME cinderwheel_mapping_fixture
    COMMAND
        "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/validate_mapping.py"
)

if(CINDERWHEEL_ENABLE_JUCE)
    if(CINDERWHEEL_JUCE_SOURCE_DIR)
        cmake_path(
            ABSOLUTE_PATH CINDERWHEEL_JUCE_SOURCE_DIR
            NORMALIZE
            OUTPUT_VARIABLE cinderwheel_juce_source
        )
        if(NOT EXISTS "${cinderwheel_juce_source}/CMakeLists.txt"
            OR NOT EXISTS "${cinderwheel_juce_source}/modules/juce_core/juce_core.h")
            message(FATAL_ERROR
                "CINDERWHEEL_JUCE_SOURCE_DIR is not an extracted JUCE source tree"
            )
        endif()
        file(
            READ
            "${cinderwheel_juce_source}/modules/juce_core/system/juce_StandardHeader.h"
            cinderwheel_juce_version_header
        )
        if(NOT cinderwheel_juce_version_header MATCHES "JUCE_MAJOR_VERSION[ \t]+8"
            OR NOT cinderwheel_juce_version_header MATCHES "JUCE_MINOR_VERSION[ \t]+0"
            OR NOT cinderwheel_juce_version_header MATCHES "JUCE_BUILDNUMBER[ \t]+15")
            message(FATAL_ERROR
                "CINDERWHEEL_JUCE_SOURCE_DIR must identify JUCE 8.0.15 source; "
                "the operator remains responsible for commit/hash authentication"
            )
        endif()
        add_subdirectory(
            "${cinderwheel_juce_source}"
            "${CMAKE_CURRENT_BINARY_DIR}/juce"
            EXCLUDE_FROM_ALL
        )
    elseif(CINDERWHEEL_ALLOW_JUCE_FETCH)
        include(FetchContent)
        FetchContent_Declare(
            JUCE
            URL
                "https://github.com/juce-framework/JUCE/archive/${CINDERWHEEL_JUCE_COMMIT}.tar.gz"
            URL_HASH "SHA256=${CINDERWHEEL_JUCE_ARCHIVE_SHA256}"
            DOWNLOAD_EXTRACT_TIMESTAMP FALSE
        )
        FetchContent_MakeAvailable(JUCE)
    else()
        message(FATAL_ERROR
            "CINDERWHEEL_ENABLE_JUCE requires CINDERWHEEL_JUCE_SOURCE_DIR or "
            "an explicit CINDERWHEEL_ALLOW_JUCE_FETCH=ON"
        )
    endif()

    add_library(cinderwheel_juce_adapter STATIC
        src/juce_midi_adapter.cpp
    )
    target_include_directories(cinderwheel_juce_adapter PUBLIC include)
    target_link_libraries(cinderwheel_juce_adapter PUBLIC
        cinderwheel_core
        juce::juce_audio_basics
    )
    target_compile_features(cinderwheel_juce_adapter PUBLIC cxx_std_17)
    cinderwheel_enable_warnings(cinderwheel_juce_adapter)

    add_executable(cinderwheel_juce_adapter_tests
        tests/juce_midi_adapter_tests.cpp
    )
    target_link_libraries(cinderwheel_juce_adapter_tests PRIVATE
        cinderwheel_juce_adapter
    )
    target_compile_features(cinderwheel_juce_adapter_tests PRIVATE cxx_std_17)
    cinderwheel_enable_warnings(cinderwheel_juce_adapter_tests)
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
    cinderwheel_enable_warnings(cinderwheel-render)
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
    cinderwheel_enable_warnings(cinderwheel-instrument)
endif()
