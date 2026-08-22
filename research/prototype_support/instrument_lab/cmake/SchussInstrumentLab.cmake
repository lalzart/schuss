include_guard(GLOBAL)

include(CMakeParseArguments)

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
    find_package(Python3 COMPONENTS Interpreter REQUIRED)
    set(_schuss_instrument_lab_repo_root
        "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../../../..")
    cmake_path(ABSOLUTE_PATH _schuss_instrument_lab_repo_root NORMALIZE)
    set(_schuss_instrument_lab_juce_validator
        "${_schuss_instrument_lab_repo_root}/tools/source_packages/validate_juce_source_tree.py")

    foreach(_field archive_url archive_sha256)
        execute_process(
            COMMAND "${Python3_EXECUTABLE}" "${_schuss_instrument_lab_juce_validator}"
                --repo-root "${_schuss_instrument_lab_repo_root}"
                --print-field "${_field}"
            RESULT_VARIABLE _authority_result
            OUTPUT_VARIABLE _authority_value
            ERROR_VARIABLE _authority_error
            OUTPUT_STRIP_TRAILING_WHITESPACE)
        if(NOT _authority_result EQUAL 0)
            message(FATAL_ERROR
                "Instrument Lab JUCE source-release authority failed: ${_authority_error}")
        endif()
        set("_instrument_lab_juce_${_field}" "${_authority_value}")
    endforeach()

    if(ARG_SOURCE_DIR)
        cmake_path(ABSOLUTE_PATH ARG_SOURCE_DIR NORMALIZE
            OUTPUT_VARIABLE instrument_lab_juce_source)
        if(NOT EXISTS "${instrument_lab_juce_source}/CMakeLists.txt"
           OR NOT EXISTS
              "${instrument_lab_juce_source}/modules/juce_core/juce_core.h")
            message(FATAL_ERROR "Instrument Lab JUCE source is not a JUCE tree")
        endif()
        execute_process(
            COMMAND "${Python3_EXECUTABLE}" "${_schuss_instrument_lab_juce_validator}"
                --repo-root "${_schuss_instrument_lab_repo_root}"
                --source-tree "${instrument_lab_juce_source}"
                --check
            RESULT_VARIABLE _tree_result
            OUTPUT_VARIABLE _tree_output
            ERROR_VARIABLE _tree_error)
        if(NOT _tree_result EQUAL 0)
            message(FATAL_ERROR
                "Instrument Lab JUCE tree authentication failed: ${_tree_output}${_tree_error}")
        endif()
        add_subdirectory("${instrument_lab_juce_source}" "${ARG_BINARY_DIR}"
            EXCLUDE_FROM_ALL)
    elseif(ARG_ALLOW_FETCH)
        include(FetchContent)
        FetchContent_Declare(JUCE
            URL "${_instrument_lab_juce_archive_url}"
            URL_HASH "SHA256=${_instrument_lab_juce_archive_sha256}"
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
