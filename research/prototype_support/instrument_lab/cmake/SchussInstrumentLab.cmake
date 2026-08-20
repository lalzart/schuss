include_guard(GLOBAL)

include(CMakeParseArguments)

set(SCHUSS_INSTRUMENT_LAB_JUCE_COMMIT
    "91ad83ae34a81e0833b1a2b0866f54846370ae53")
set(SCHUSS_INSTRUMENT_LAB_JUCE_ARCHIVE_SHA256
    "04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70")

function(schuss_instrument_lab_enable_warnings target)
    target_compile_options(${target} PRIVATE
        $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>)
endfunction()

function(schuss_instrument_lab_enable_sanitizers target enabled)
    if(enabled AND CMAKE_CXX_COMPILER_ID MATCHES "AppleClang|Clang|GNU")
        target_compile_options(${target} PRIVATE -fsanitize=address,undefined)
        target_link_options(${target} PRIVATE -fsanitize=address,undefined)
    endif()
endfunction()

function(schuss_instrument_lab_add_authenticated_juce)
    set(one_value_args SOURCE_DIR BINARY_DIR ALLOW_FETCH)
    cmake_parse_arguments(ARG "" "${one_value_args}" "" ${ARGN})
    if(NOT ARG_BINARY_DIR)
        message(FATAL_ERROR
            "schuss_instrument_lab_add_authenticated_juce requires BINARY_DIR")
    endif()

    if(ARG_SOURCE_DIR)
        cmake_path(ABSOLUTE_PATH ARG_SOURCE_DIR NORMALIZE
            OUTPUT_VARIABLE instrument_lab_juce_source)
        if(NOT EXISTS "${instrument_lab_juce_source}/CMakeLists.txt"
           OR NOT EXISTS
              "${instrument_lab_juce_source}/modules/juce_core/juce_core.h")
            message(FATAL_ERROR "Instrument Lab JUCE source is not a JUCE tree")
        endif()
        file(READ
            "${instrument_lab_juce_source}/modules/juce_core/system/juce_StandardHeader.h"
            instrument_lab_juce_version_header)
        if(NOT instrument_lab_juce_version_header MATCHES
                "JUCE_MAJOR_VERSION[ \t]+8"
           OR NOT instrument_lab_juce_version_header MATCHES
                "JUCE_MINOR_VERSION[ \t]+0"
           OR NOT instrument_lab_juce_version_header MATCHES
                "JUCE_BUILDNUMBER[ \t]+15")
            message(FATAL_ERROR
                "Instrument Lab requires operator-authenticated JUCE 8.0.15")
        endif()
        add_subdirectory("${instrument_lab_juce_source}" "${ARG_BINARY_DIR}"
            EXCLUDE_FROM_ALL)
    elseif(ARG_ALLOW_FETCH)
        include(FetchContent)
        FetchContent_Declare(JUCE
            URL
              "https://github.com/juce-framework/JUCE/archive/${SCHUSS_INSTRUMENT_LAB_JUCE_COMMIT}.tar.gz"
            URL_HASH
              "SHA256=${SCHUSS_INSTRUMENT_LAB_JUCE_ARCHIVE_SHA256}"
            DOWNLOAD_EXTRACT_TIMESTAMP FALSE)
        FetchContent_MakeAvailable(JUCE)
    else()
        message(FATAL_ERROR
            "Authenticated JUCE source is required; fetching is disabled")
    endif()
endfunction()

function(schuss_instrument_lab_register_test test_name target)
    if(NOT TARGET ${target})
        message(FATAL_ERROR
            "cannot register ${test_name}: target ${target} does not exist")
    endif()
    add_test(NAME ${test_name} COMMAND ${target})
endfunction()
