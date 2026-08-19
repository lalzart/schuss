cmake_minimum_required(VERSION 3.22)
project(schuss_rt VERSION 0.1.0 LANGUAGES CXX)

option(SCHUSS_RT_BUILD_TESTS "Build the schuss_rt unit tests" ON)

add_library(schuss_rt STATIC
    src/package_parser.cpp
    src/runtime.cpp
    src/sha256.cpp
)
target_include_directories(schuss_rt PUBLIC include)
target_compile_features(schuss_rt PUBLIC cxx_std_17)
target_compile_options(schuss_rt PRIVATE
    $<$<CXX_COMPILER_ID:AppleClang,Clang,GNU>:-Wall;-Wextra;-Wpedantic;-Werror>
)

if(SCHUSS_RT_BUILD_TESTS)
    enable_testing()
    add_executable(schuss_rt_tests tests/runtime_tests.cpp)
    target_link_libraries(schuss_rt_tests PRIVATE schuss_rt)
    target_compile_features(schuss_rt_tests PRIVATE cxx_std_17)
    target_compile_definitions(schuss_rt_tests PRIVATE
        SCHUSS_RT_FIXTURE_PATH="${CMAKE_CURRENT_SOURCE_DIR}/../../fixtures/task031/reference-host-package.json"
    )
    add_test(NAME schuss_rt_tests COMMAND schuss_rt_tests)
endif()
