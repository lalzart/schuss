include_guard(GLOBAL)

cmake_path(GET CMAKE_CURRENT_LIST_DIR PARENT_PATH _mutable_stmlib_v1_root)
cmake_path(ABSOLUTE_PATH _mutable_stmlib_v1_root NORMALIZE)
set(_mutable_stmlib_v1_validator
    "${CMAKE_CURRENT_LIST_DIR}/../../../../tools/source_packages/validate_source_package.py")
set(_mutable_stmlib_v1_manifest
    "ee35268d95d661a9be2ff5f3e8ff0c6d89f06c4b0337ceaacbb7ec8ba51426bb")
find_package(Python3 COMPONENTS Interpreter REQUIRED)

execute_process(
    COMMAND "${Python3_EXECUTABLE}" "${_mutable_stmlib_v1_validator}"
        "${_mutable_stmlib_v1_root}"
        --expected-package-id mutable-stmlib-v1
        --expected-package-revision 1
        --expected-closure-manifest-sha256 "${_mutable_stmlib_v1_manifest}"
    RESULT_VARIABLE _mutable_stmlib_v1_result
    OUTPUT_VARIABLE _mutable_stmlib_v1_output
    ERROR_VARIABLE _mutable_stmlib_v1_error)
if(NOT _mutable_stmlib_v1_result EQUAL 0)
    message(FATAL_ERROR "stmlib source package validation failed: ${_mutable_stmlib_v1_output}${_mutable_stmlib_v1_error}")
endif()

if(NOT TARGET mutable_stmlib_v1_headers)
    add_library(mutable_stmlib_v1_headers INTERFACE)
    target_include_directories(mutable_stmlib_v1_headers SYSTEM INTERFACE
        "${_mutable_stmlib_v1_root}/upstream")
    add_library(MutableStmlibV1::Headers ALIAS mutable_stmlib_v1_headers)
endif()

function(mutable_stmlib_v1_resolve_components output_variable)
    set(_command "${Python3_EXECUTABLE}" "${_mutable_stmlib_v1_validator}"
        "${_mutable_stmlib_v1_root}"
        --expected-package-id mutable-stmlib-v1
        --expected-package-revision 1
        --expected-closure-manifest-sha256 "${_mutable_stmlib_v1_manifest}")
    foreach(_component IN LISTS ARGN)
        list(APPEND _command --print-component-paths "${_component}")
    endforeach()
    execute_process(COMMAND ${_command} RESULT_VARIABLE _result
        OUTPUT_VARIABLE _paths ERROR_VARIABLE _error OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(NOT _result EQUAL 0)
        message(FATAL_ERROR "stmlib component resolution failed: ${_paths}${_error}")
    endif()
    string(REPLACE "\n" ";" _relative_paths "${_paths}")
    set(_resolved)
    foreach(_relative IN LISTS _relative_paths)
        list(APPEND _resolved "${_mutable_stmlib_v1_root}/upstream/${_relative}")
    endforeach()
    set("${output_variable}" "${_resolved}" PARENT_SCOPE)
endfunction()
