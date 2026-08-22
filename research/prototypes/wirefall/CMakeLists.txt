cmake_minimum_required(VERSION 3.22)

project(wirefall_prototype VERSION 0.1.0 LANGUAGES CXX)

option(WIREFALL_ENABLE_SANITIZERS "Enable address and undefined behavior sanitizers" OFF)

set(WIREFALL_INSTRUMENT_LAB
    "${CMAKE_CURRENT_SOURCE_DIR}/../../prototype_support/instrument_lab")
add_subdirectory(
    "${WIREFALL_INSTRUMENT_LAB}"
    "${CMAKE_CURRENT_BINARY_DIR}/instrument_lab"
    EXCLUDE_FROM_ALL
)

find_package(Python3 COMPONENTS Interpreter REQUIRED)

add_custom_target(wirefall_generated_fixtures_check
    COMMAND
        "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tools/generate_fixtures.py"
        --repo-root "${CMAKE_CURRENT_SOURCE_DIR}/../../.."
        --check
    VERBATIM
)

add_library(wirefall_core STATIC src/core.cpp)
add_dependencies(wirefall_core wirefall_generated_fixtures_check)
target_include_directories(wirefall_core PUBLIC
    include
    generated/include
)
target_link_libraries(wirefall_core PUBLIC SchussInstrumentLab::Core)
target_compile_features(wirefall_core PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(wirefall_core)

if(WIREFALL_ENABLE_SANITIZERS)
    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
        target_compile_options(wirefall_core PUBLIC
            -fno-omit-frame-pointer
            -fsanitize=address,undefined
        )
        target_link_options(wirefall_core PUBLIC
            -fno-omit-frame-pointer
            -fsanitize=address,undefined
        )
    else()
        message(FATAL_ERROR "Wirefall sanitizers require Clang or GNU")
    endif()
endif()

add_executable(wirefall_render src/render.cpp)
target_link_libraries(wirefall_render PRIVATE wirefall_core)
target_compile_features(wirefall_render PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(wirefall_render)

enable_testing()

add_executable(wirefall_core_tests tests/core_tests.cpp)
target_link_libraries(wirefall_core_tests PRIVATE wirefall_core)
target_compile_features(wirefall_core_tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(wirefall_core_tests)
add_test(NAME wirefall_core_tests COMMAND wirefall_core_tests)

add_test(
    NAME wirefall_contract_fixtures
    COMMAND
        "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/validate_contract_fixtures.py"
        --repo-root "${CMAKE_CURRENT_SOURCE_DIR}/../../.."
)

add_test(
    NAME wirefall_render_matrix
    COMMAND
        "${Python3_EXECUTABLE}"
        "${CMAKE_CURRENT_SOURCE_DIR}/tests/validate_render_matrix.py"
        --renderer "$<TARGET_FILE:wirefall_render>"
        --contract "${CMAKE_CURRENT_SOURCE_DIR}/contract/experiment.json"
        --output "${CMAKE_CURRENT_BINARY_DIR}/validated-renders"
)
set_tests_properties(wirefall_render_matrix PROPERTIES LABELS "native;render;host-signal")
