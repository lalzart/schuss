include_guard(GLOBAL)

cmake_path(GET CMAKE_CURRENT_LIST_DIR PARENT_PATH _mutable_ksoloti_v1_package_root)
cmake_path(ABSOLUTE_PATH _mutable_ksoloti_v1_package_root NORMALIZE)

set(_mutable_ksoloti_v1_validator
    "${CMAKE_CURRENT_LIST_DIR}/../../../../tools/source_packages/validate_source_package.py")
set(_mutable_ksoloti_v1_closure_manifest
    "0903f25038f0116422a8512b15f1c3531e7b22371da8ad393b130a16d821508f")

find_package(Python3 COMPONENTS Interpreter REQUIRED)

function(_mutable_ksoloti_v1_validate)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${_mutable_ksoloti_v1_validator}"
            "${_mutable_ksoloti_v1_package_root}"
            --expected-package-id mutable-ksoloti-v1
            --expected-package-revision 1
            --expected-closure-manifest-sha256 "${_mutable_ksoloti_v1_closure_manifest}"
        RESULT_VARIABLE _mutable_ksoloti_v1_result
        OUTPUT_VARIABLE _mutable_ksoloti_v1_output
        ERROR_VARIABLE _mutable_ksoloti_v1_error)
    if(NOT _mutable_ksoloti_v1_result EQUAL 0)
        string(STRIP "${_mutable_ksoloti_v1_output}${_mutable_ksoloti_v1_error}"
            _mutable_ksoloti_v1_diagnostic)
        message(FATAL_ERROR
            "Mutable/Ksoloti source package validation failed: ${_mutable_ksoloti_v1_diagnostic}")
    endif()
endfunction()

_mutable_ksoloti_v1_validate()

if(NOT TARGET mutable_ksoloti_v1_headers)
    add_library(mutable_ksoloti_v1_headers INTERFACE)
    target_include_directories(mutable_ksoloti_v1_headers SYSTEM INTERFACE
        "${_mutable_ksoloti_v1_package_root}/upstream/firmware/mutable_instruments")
    add_library(MutableKsolotiV1::Headers ALIAS mutable_ksoloti_v1_headers)
endif()

function(mutable_ksoloti_v1_resolve_components output_variable)
    if(ARGC LESS 2)
        message(FATAL_ERROR
            "mutable_ksoloti_v1_resolve_components requires at least one component")
    endif()

    set(_mutable_ksoloti_v1_command
        "${Python3_EXECUTABLE}"
        "${_mutable_ksoloti_v1_validator}"
        "${_mutable_ksoloti_v1_package_root}"
        --expected-package-id mutable-ksoloti-v1
        --expected-package-revision 1
        --expected-closure-manifest-sha256 "${_mutable_ksoloti_v1_closure_manifest}")
    foreach(_mutable_ksoloti_v1_component IN LISTS ARGN)
        list(APPEND _mutable_ksoloti_v1_command
            --print-component-paths "${_mutable_ksoloti_v1_component}")
    endforeach()

    execute_process(
        COMMAND ${_mutable_ksoloti_v1_command}
        RESULT_VARIABLE _mutable_ksoloti_v1_result
        OUTPUT_VARIABLE _mutable_ksoloti_v1_paths
        ERROR_VARIABLE _mutable_ksoloti_v1_error
        OUTPUT_STRIP_TRAILING_WHITESPACE)
    if(NOT _mutable_ksoloti_v1_result EQUAL 0)
        string(STRIP "${_mutable_ksoloti_v1_paths}${_mutable_ksoloti_v1_error}"
            _mutable_ksoloti_v1_diagnostic)
        message(FATAL_ERROR
            "Mutable/Ksoloti component resolution failed: ${_mutable_ksoloti_v1_diagnostic}")
    endif()

    string(REPLACE "\n" ";" _mutable_ksoloti_v1_relative_paths
        "${_mutable_ksoloti_v1_paths}")
    set(_mutable_ksoloti_v1_resolved_paths)
    foreach(_mutable_ksoloti_v1_relative IN LISTS _mutable_ksoloti_v1_relative_paths)
        list(APPEND _mutable_ksoloti_v1_resolved_paths
            "${_mutable_ksoloti_v1_package_root}/upstream/${_mutable_ksoloti_v1_relative}")
    endforeach()
    set("${output_variable}" "${_mutable_ksoloti_v1_resolved_paths}" PARENT_SCOPE)
endfunction()
