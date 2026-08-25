cmake_minimum_required(VERSION 3.22)

project(schuss_pamplist_vst3 VERSION 0.6.0 LANGUAGES C CXX)

enable_testing()

set(PAMPLIST_VST3_ROOT "${CMAKE_CURRENT_LIST_DIR}/..")
set(PAMPLIST_JUCE_SOURCE_DIR "" CACHE PATH "Authenticated JUCE 8.0.15 source tree")
option(PAMPLIST_ALLOW_JUCE_FETCH "Fetch JUCE instead of using authenticated local bytes" OFF)

# Keep the accepted standalone target and its retained receipt outside this
# adapter build. The parent contributes only the frozen portable Core targets.
set(PAMPLIST_ENABLE_JUCE OFF CACHE BOOL "Build Pamplist standalone" FORCE)
add_subdirectory(
    "${PAMPLIST_VST3_ROOT}"
    "${CMAKE_CURRENT_BINARY_DIR}/pamplist-core")

schuss_instrument_lab_add_authenticated_juce(
    SOURCE_DIR "${PAMPLIST_JUCE_SOURCE_DIR}"
    BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/juce"
    ALLOW_FETCH "${PAMPLIST_ALLOW_JUCE_FETCH}")

add_library(pamplist_vst3_model STATIC src/vst3_model.cpp)
target_include_directories(pamplist_vst3_model PUBLIC
    include
    "${PAMPLIST_VST3_ROOT}/include")
target_link_libraries(pamplist_vst3_model PUBLIC pamplist_core)
target_compile_features(pamplist_vst3_model PUBLIC cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist_vst3_model)
schuss_instrument_lab_enable_sanitizers(
    pamplist_vst3_model ${PAMPLIST_ENABLE_SANITIZERS})

add_library(pamplist_vst3_impl STATIC
    src/vst3_editor.cpp
    src/vst3_processor.cpp)
set_target_properties(pamplist_vst3_impl PROPERTIES
    POSITION_INDEPENDENT_CODE ON)
target_include_directories(pamplist_vst3_impl PUBLIC
    include
    "${PAMPLIST_VST3_ROOT}/include")
target_link_libraries(pamplist_vst3_impl PUBLIC
    pamplist_vst3_model
    juce::juce_audio_processors
    juce::juce_data_structures
    juce::juce_gui_basics)
target_compile_features(pamplist_vst3_impl PUBLIC cxx_std_17)
target_compile_definitions(pamplist_vst3_impl PUBLIC
    JUCE_REPORT_APP_USAGE=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_WEB_BROWSER=0)
schuss_instrument_lab_enable_warnings(pamplist_vst3_impl)
schuss_instrument_lab_enable_sanitizers(
    pamplist_vst3_impl ${PAMPLIST_ENABLE_SANITIZERS})

juce_add_plugin(pamplist-vst3
    PRODUCT_NAME "Pamplist"
    COMPANY_NAME "Schuss"
    BUNDLE_ID "dev.schuss.pamplist.vst3.local"
    PLUGIN_MANUFACTURER_CODE Schs
    PLUGIN_CODE Pamp
    FORMATS VST3
    VST3_CATEGORIES Instrument Synth
    IS_SYNTH TRUE
    NEEDS_MIDI_INPUT TRUE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    COPY_PLUGIN_AFTER_BUILD FALSE)
target_sources(pamplist-vst3 PRIVATE src/vst3_entry.cpp)
target_link_libraries(pamplist-vst3 PRIVATE
    pamplist_vst3_impl
    juce::juce_audio_plugin_client)
target_compile_features(pamplist-vst3 PRIVATE cxx_std_17)
target_compile_definitions(pamplist-vst3 PRIVATE
    JUCE_REPORT_APP_USAGE=0
    JUCE_USE_CURL=0
    JUCE_VST3_CAN_REPLACE_VST2=0
    JUCE_VST3_EMULATE_MIDI_CC_WITH_PARAMETERS=1
    JUCE_WEB_BROWSER=0)
target_compile_definitions(pamplist-vst3_VST3 PRIVATE
    JUCE_VST3_EMULATE_MIDI_CC_WITH_PARAMETERS=1)
schuss_instrument_lab_enable_warnings(pamplist-vst3)
if(APPLE)
    add_custom_command(TARGET pamplist-vst3_VST3 POST_BUILD
        COMMAND /usr/bin/codesign --force --deep --sign -
            "$<TARGET_BUNDLE_DIR:pamplist-vst3_VST3>"
        COMMENT "Re-sealing Pamplist.vst3 after VST3 module metadata generation"
        VERBATIM)
endif()

add_executable(pamplist-vst3-model-tests tests/vst3_model_tests.cpp)
target_link_libraries(pamplist-vst3-model-tests PRIVATE pamplist_vst3_model)
target_compile_features(pamplist-vst3-model-tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist-vst3-model-tests)
schuss_instrument_lab_enable_sanitizers(
    pamplist-vst3-model-tests ${PAMPLIST_ENABLE_SANITIZERS})
add_test(NAME pamplist_vst3_model_tests COMMAND pamplist-vst3-model-tests)

add_executable(pamplist-vst3-processor-tests
    tests/vst3_processor_tests.cpp)
target_link_libraries(pamplist-vst3-processor-tests PRIVATE
    pamplist_vst3_impl)
target_compile_features(pamplist-vst3-processor-tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist-vst3-processor-tests)
schuss_instrument_lab_enable_sanitizers(
    pamplist-vst3-processor-tests ${PAMPLIST_ENABLE_SANITIZERS})
add_test(
    NAME pamplist_vst3_processor_tests
    COMMAND pamplist-vst3-processor-tests)

add_executable(pamplist-vst3-allocation-tests
    tests/vst3_allocation_tests.cpp)
target_link_libraries(pamplist-vst3-allocation-tests PRIVATE
    pamplist_vst3_impl)
target_compile_features(pamplist-vst3-allocation-tests PRIVATE cxx_std_17)
schuss_instrument_lab_enable_warnings(pamplist-vst3-allocation-tests)
add_test(
    NAME pamplist_vst3_allocation_tests
    COMMAND pamplist-vst3-allocation-tests)

add_executable(pamplist-vst3-module-tests
    tests/vst3_module_tests.cpp)
target_link_libraries(pamplist-vst3-module-tests PRIVATE
    pamplist_vst3_model
    juce::juce_audio_processors
    juce::juce_gui_basics)
target_compile_features(pamplist-vst3-module-tests PRIVATE cxx_std_17)
target_compile_definitions(pamplist-vst3-module-tests PRIVATE
    JUCE_PLUGINHOST_VST3=1
    JUCE_REPORT_APP_USAGE=0
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0)
schuss_instrument_lab_enable_warnings(pamplist-vst3-module-tests)
add_dependencies(pamplist-vst3-module-tests pamplist-vst3_VST3)
add_test(
    NAME pamplist_vst3_module_tests
    COMMAND pamplist-vst3-module-tests
        "$<TARGET_BUNDLE_DIR:pamplist-vst3_VST3>")
