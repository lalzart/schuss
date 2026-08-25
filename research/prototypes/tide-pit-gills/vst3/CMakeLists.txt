cmake_minimum_required(VERSION 3.22)

project(tide_pit_local_vst3 VERSION 0.1.0 LANGUAGES C CXX)

enable_testing()

set(TIDE_PIT_VST3_ROOT "${CMAKE_CURRENT_LIST_DIR}/..")
set(TIDE_PIT_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 source tree")
option(TIDE_PIT_ALLOW_JUCE_FETCH "Fetch JUCE instead of authenticated local bytes" OFF)
option(TIDE_PIT_VST3_ENABLE_SANITIZERS "Enable focused VST3 ASan and UBSan" OFF)

# Import only the frozen portable targets. The retained standalone source and
# build receipt remain outside this isolated host-adapter build.
set(TIDE_PIT_ENABLE_JUCE OFF CACHE BOOL "Build Tide Pit standalone" FORCE)
set(TIDE_PIT_ENABLE_SANITIZERS
    ${TIDE_PIT_VST3_ENABLE_SANITIZERS}
    CACHE BOOL "Enable Tide Pit Core sanitizers" FORCE)
add_subdirectory(
    "${TIDE_PIT_VST3_ROOT}"
    "${CMAKE_CURRENT_BINARY_DIR}/tide-pit-core")

schuss_instrument_lab_add_authenticated_juce(
    SOURCE_DIR "${TIDE_PIT_JUCE_SOURCE_DIR}"
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
    ALLOW_FETCH "${TIDE_PIT_ALLOW_JUCE_FETCH}")

add_library(tide_pit_vst3_model STATIC src/vst3_model.cpp)
target_include_directories(tide_pit_vst3_model PUBLIC
    include
    "${TIDE_PIT_VST3_ROOT}/include")
target_link_libraries(tide_pit_vst3_model PUBLIC tide_pit_core)
target_compile_features(tide_pit_vst3_model PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(tide_pit_vst3_model)
schuss_instrument_lab_enable_sanitizers(
    tide_pit_vst3_model ${TIDE_PIT_VST3_ENABLE_SANITIZERS})

add_library(tide_pit_vst3_adapter STATIC
    "${TIDE_PIT_VST3_ROOT}/src/juce_midi_adapter.cpp")
set_target_properties(tide_pit_vst3_adapter PROPERTIES
    POSITION_INDEPENDENT_CODE ON)
target_include_directories(tide_pit_vst3_adapter PUBLIC
    "${TIDE_PIT_VST3_ROOT}/include")
target_link_libraries(tide_pit_vst3_adapter PUBLIC
    tide_pit_core
    juce::juce_audio_basics)
target_compile_features(tide_pit_vst3_adapter PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(tide_pit_vst3_adapter)
schuss_instrument_lab_enable_sanitizers(
    tide_pit_vst3_adapter ${TIDE_PIT_VST3_ENABLE_SANITIZERS})

add_library(tide_pit_vst3_impl STATIC
    src/vst3_editor.cpp
    src/vst3_processor.cpp)
set_target_properties(tide_pit_vst3_impl PROPERTIES
    POSITION_INDEPENDENT_CODE ON)
target_include_directories(tide_pit_vst3_impl PUBLIC
    include
    "${TIDE_PIT_VST3_ROOT}/include")
target_link_libraries(tide_pit_vst3_impl PUBLIC
    tide_pit_vst3_adapter
    tide_pit_vst3_model
    tide_pit_ui_model
    juce::juce_audio_processors
    juce::juce_data_structures
    juce::juce_gui_basics)
target_compile_features(tide_pit_vst3_impl PUBLIC cxx_std_17)
target_compile_definitions(tide_pit_vst3_impl PUBLIC
    JUCE_REPORT_APP_USAGE=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_WEB_BROWSER=0)
schuss_instrument_lab_enable_warnings(tide_pit_vst3_impl)
schuss_instrument_lab_enable_sanitizers(
    tide_pit_vst3_impl ${TIDE_PIT_VST3_ENABLE_SANITIZERS})

juce_add_plugin(tide-pit-vst3
    PRODUCT_NAME "Tide Pit"
    COMPANY_NAME "Schuss"
    BUNDLE_ID "dev.schuss.tide-pit.vst3.local"
    PLUGIN_MANUFACTURER_CODE Schs
    PLUGIN_CODE TdPt
    FORMATS VST3
    VST3_CATEGORIES Instrument Synth
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE)
target_sources(tide-pit-vst3 PRIVATE src/vst3_entry.cpp)
target_link_libraries(tide-pit-vst3 PRIVATE
    tide_pit_vst3_impl
    juce::juce_audio_plugin_client)
target_compile_features(tide-pit-vst3 PRIVATE cxx_std_17)
target_compile_definitions(tide-pit-vst3 PRIVATE
    JUCE_REPORT_APP_USAGE=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_VST3_EMULATE_MIDI_CC_WITH_PARAMETERS=1
    JUCE_WEB_BROWSER=0)
target_compile_definitions(tide-pit-vst3_VST3 PRIVATE
    JUCE_VST3_EMULATE_MIDI_CC_WITH_PARAMETERS=1)
schuss_instrument_lab_enable_warnings(tide-pit-vst3)
if(APPLE)
    add_custom_command(TARGET tide-pit-vst3_VST3 POST_BUILD
        COMMAND /usr/bin/codesign --force --deep --sign -
            "$<TARGET_BUNDLE_DIR:tide-pit-vst3_VST3>"
        COMMENT "Re-sealing Tide Pit.vst3 after VST3 module metadata generation"
        VERBATIM)
endif()

add_executable(tide-pit-vst3-model-tests tests/vst3_model_tests.cpp)
target_link_libraries(tide-pit-vst3-model-tests PRIVATE tide_pit_vst3_model)
target_compile_features(tide-pit-vst3-model-tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(tide-pit-vst3-model-tests)
schuss_instrument_lab_enable_sanitizers(
    tide-pit-vst3-model-tests ${TIDE_PIT_VST3_ENABLE_SANITIZERS})
add_test(NAME tide_pit_vst3_model_tests COMMAND tide-pit-vst3-model-tests)

add_executable(tide-pit-vst3-processor-tests tests/vst3_processor_tests.cpp)
target_link_libraries(tide-pit-vst3-processor-tests PRIVATE tide_pit_vst3_impl)
target_compile_features(tide-pit-vst3-processor-tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(tide-pit-vst3-processor-tests)
schuss_instrument_lab_enable_sanitizers(
    tide-pit-vst3-processor-tests ${TIDE_PIT_VST3_ENABLE_SANITIZERS})
add_test(NAME tide_pit_vst3_processor_tests COMMAND tide-pit-vst3-processor-tests)

add_executable(tide-pit-vst3-allocation-tests tests/vst3_allocation_tests.cpp)
target_link_libraries(tide-pit-vst3-allocation-tests PRIVATE tide_pit_vst3_impl)
target_compile_features(tide-pit-vst3-allocation-tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(tide-pit-vst3-allocation-tests)
add_test(NAME tide_pit_vst3_allocation_tests COMMAND tide-pit-vst3-allocation-tests)

add_executable(tide-pit-vst3-module-tests tests/vst3_module_tests.cpp)
target_link_libraries(tide-pit-vst3-module-tests PRIVATE
    tide_pit_vst3_model
    juce::juce_audio_processors
    juce::juce_gui_basics)
target_compile_features(tide-pit-vst3-module-tests PRIVATE cxx_std_17)
target_compile_definitions(tide-pit-vst3-module-tests PRIVATE
    JUCE_PLUGINHOST_VST3=1
    JUCE_REPORT_APP_USAGE=0
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0)
schuss_instrument_lab_enable_warnings(tide-pit-vst3-module-tests)
add_dependencies(tide-pit-vst3-module-tests tide-pit-vst3_VST3)
add_test(
    NAME tide_pit_vst3_module_tests
    COMMAND tide-pit-vst3-module-tests
        "$<TARGET_BUNDLE_DIR:tide-pit-vst3_VST3>")
