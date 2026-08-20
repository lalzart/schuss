cmake_minimum_required(VERSION 3.22)
project(schuss_instrument_lab VERSION 0.1.0 LANGUAGES CXX)

option(
    SCHUSS_INSTRUMENT_LAB_BUILD_TESTS
    "Build Instrument Lab focused tests"
    ${PROJECT_IS_TOP_LEVEL}
)

add_library(schuss_instrument_lab STATIC
    src/renderer_artifacts.cpp
)
add_library(SchussInstrumentLab::Core ALIAS schuss_instrument_lab)
target_include_directories(schuss_instrument_lab PUBLIC include)
target_compile_features(schuss_instrument_lab PUBLIC cxx_std_17)

include(cmake/SchussInstrumentLab.cmake)
schuss_instrument_lab_enable_warnings(schuss_instrument_lab)

if(SCHUSS_INSTRUMENT_LAB_BUILD_TESTS)
    enable_testing()
    add_executable(instrument_lab_core_tests tests/core_tests.cpp)
    target_link_libraries(instrument_lab_core_tests PRIVATE
        SchussInstrumentLab::Core)
    target_compile_features(instrument_lab_core_tests PRIVATE cxx_std_17)
    schuss_instrument_lab_enable_warnings(instrument_lab_core_tests)
    add_test(NAME instrument_lab_core_tests COMMAND instrument_lab_core_tests)
endif()
