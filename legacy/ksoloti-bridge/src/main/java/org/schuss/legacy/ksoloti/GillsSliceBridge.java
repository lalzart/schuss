package org.schuss.legacy.ksoloti;

import axoloti.MainFrame;
import axoloti.Patch;
import axoloti.SchussPatchAccess;
import axoloti.displays.Display;
import axoloti.inlets.Inlet;
import axoloti.object.AxoObject;
import axoloti.object.AxoObjectAbstract;
import axoloti.object.AxoObjectFile;
import axoloti.object.AxoObjectInstanceAbstract;
import axoloti.object.AxoObjectInstanceZombie;
import axoloti.object.AxoObjects;
import axoloti.object.SchussObjectAccess;
import axoloti.outlets.Outlet;
import axoloti.parameters.Parameter;
import axoloti.utils.AxoFileLibrary;
import axoloti.utils.AxolotiLibrary;
import axoloti.utils.Preferences;
import generatedobjects.SchussExactGeneratedObjects;
import java.io.OutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.simpleframework.xml.Serializer;
import org.simpleframework.xml.core.Persister;
import org.simpleframework.xml.stream.Format;

/**
 * Headless AXP-to-C++ bridge for only the exact Task 011C Gills slice.
 *
 * <p>The registry contains eight authenticated definitions. It performs no
 * ambient catalog scan, GUI presentation, device lookup, upload, flash,
 * compilation, or firmware action.</p>
 */
public final class GillsSliceBridge {
    private static final String LFO_UUID =
            "de6909eb64db13af5b43f979a4c130024b3a4793";
    private static final String COUNTER_UUID =
            "7a141ba82230e54e5f5cd12da5dbe5a74ba854a5";
    private static final String SEQUENCER_UUID =
            "aa0848ea71ef03f595a32f0c14bff9cab097294701";
    private static final String SINE_UUID =
            "6e094045cca76a9dbf7ebfa72e44e4700d2b3ba";
    private static final String XFADE_UUID =
            "375dc91d218e96cdc9cbc7e92adb48f705ef701a";
    private static final String FILTER_UUID =
            "71d5f8b2131b691d591a9a9ee28771309f8938d";
    private static final String OUTPUT_UUID =
            "a1ca7a567f535acc21055669829101d3ee7f0189";
    private static final String INLET_F_UUID =
            "5c585d2dcd9c05631e345ac09626a22a639d7c13";
    private static final Set<String> EXPECTED_UUIDS = Set.of(
            LFO_UUID, COUNTER_UUID, SEQUENCER_UUID, SINE_UUID,
            XFADE_UUID, FILTER_UUID, OUTPUT_UUID, INLET_F_UUID);

    private GillsSliceBridge() {
    }

    public static void main(String[] arguments) throws Exception {
        if (!Boolean.parseBoolean(System.getProperty("java.awt.headless"))) {
            fail("java.awt.headless must be true");
        }
        java.util.logging.Logger rootLogger = java.util.logging.Logger.getLogger("");
        rootLogger.setLevel(java.util.logging.Level.OFF);
        for (java.util.logging.Handler handler : rootLogger.getHandlers()) {
            handler.setLevel(java.util.logging.Level.OFF);
        }

        Map<String, Path> values = parseArguments(arguments);
        Path axp = values.get("axp");
        Path output = values.get("output");
        Path factoryRoot = values.get("factory-root");
        Path contribRoot = values.get("contrib-root");
        Path patcherRoot = values.get("patcher-root");
        Path runtimeRoot = values.get("runtime-root");
        if (!Files.isRegularFile(axp) || Files.exists(output)) {
            fail("AXP must exist and generated-source output must not exist");
        }
        if (!Files.isDirectory(factoryRoot.resolve("objects"))
                || !Files.isRegularFile(contribRoot.resolve(
                        "objects/drj/seq/stepseq_16_pitch.axo"))
                || !Files.isRegularFile(patcherRoot.resolve(
                        "src/main/java/axoloti/Patch.java"))) {
            fail("pinned source roots are incomplete");
        }
        if (!Files.isRegularFile(runtimeRoot.resolve("build/ksoloti.bin"))) {
            fail("authenticated firmware runtime is incomplete");
        }

        byte[] axpBytes = Files.readAllBytes(axp);
        String axpSha256 = sha256(axpBytes);
        System.setProperty("axoloti.deterministic_source_sha256", axpSha256);
        System.setProperty("file.encoding", "UTF-8");
        System.setProperty("axoloti_home", patcherRoot.toString());
        System.setProperty("axoloti_firmware", runtimeRoot.toString());
        System.setProperty("axoloti_link_firmware", runtimeRoot.toString());

        Preferences preferences = new Preferences();
        preferences.setControllerEnabled(false);
        preferences.setControllerObject("");
        preferences.setFirmwareMode("Ksoloti Core");
        preferences.updateLibrary(
                AxolotiLibrary.AXOLOTI_FACTORY_ID,
                new AxoFileLibrary(
                        AxolotiLibrary.AXOLOTI_FACTORY_ID,
                        AxoFileLibrary.TYPE,
                        factoryRoot.toString(),
                        true));
        Preferences.setInstance(preferences);

        PrintStream originalOut = System.out;
        PrintStream originalErr = System.err;
        String generated;
        List<List<String>> resolved;
        try {
            System.setOut(new PrintStream(
                    OutputStream.nullOutputStream(), true, StandardCharsets.UTF_8));
            System.setErr(new PrintStream(
                    OutputStream.nullOutputStream(), true, StandardCharsets.UTF_8));
            AxoObjects registry = exactRegistry(factoryRoot, contribRoot);
            MainFrame.axoObjects = registry;
            SchussPatchAccess.initializeSynonyms();

            Serializer serializer = new Persister(new Format(2));
            Patch patch = serializer.read(Patch.class, axp.toFile());
            patch.setFileNamePath("task011c/four-step-dual-sine.axp");
            patch.PostContructor();
            resolved = verifyResolvedPatch(patch);
            generated = SchussPatchAccess.generateCode(patch);
        } finally {
            System.setOut(originalOut);
            System.setErr(originalErr);
        }
        if (containsLocalPath(generated, values.values())) {
            fail("generated source contains a local execution path");
        }
        byte[] generatedBytes = generated.getBytes(StandardCharsets.UTF_8);
        Files.write(output, generatedBytes);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("canonical_profile", "schuss-canonical-json-v1");
        result.put("schema_version", "task011c-gills-slice-bridge-result-v0");
        result.put("status", "success");
        result.put("axp_sha256", axpSha256);
        result.put("generated_cpp_sha256", sha256(generatedBytes));
        result.put("generated_cpp_byte_length", generatedBytes.length);
        result.put("headless", true);
        result.put("ambient_discovery", false);
        result.put("controller_enabled", false);
        result.put("registered_object_count", EXPECTED_UUIDS.size());
        result.put("resolved_instance_count", resolved.size());
        result.put("resolved_objects", resolved);
        result.put("device_actions", "unreachable");
        System.out.println(StableJson.stringify(result));
    }

    private static AxoObjects exactRegistry(Path factoryRoot, Path contribRoot)
            throws Exception {
        List<AxoObjectAbstract> selected = new ArrayList<>();
        selected.add(generatedFactory(
                factoryRoot, "lfo-square", "objects/lfo/square.axo",
                "square", 0, LFO_UUID));
        selected.add(generatedFactory(
                factoryRoot, "logic-counter", "objects/logic/counter.axo",
                "counter", 0, COUNTER_UUID));
        selected.add(loadExact(
                contribRoot.resolve("objects/drj/seq/stepseq_16_pitch.axo"),
                "stepseq_4_pitch", 0, SEQUENCER_UUID));
        selected.add(generatedFactory(
                factoryRoot, "osc-sine", "objects/osc/sine.axo",
                "sine", 0, SINE_UUID));
        selected.add(generatedFactory(
                factoryRoot, "mix-xfade-mixed", "objects/mix/xfade.axo",
                "xfade", 2, XFADE_UUID));
        selected.add(generatedFactory(
                factoryRoot, "filter-multimode-svf-m",
                "objects/filter/multimode svf m.axo",
                "multimode svf m", 0, FILTER_UUID));
        selected.add(generatedFactory(
                factoryRoot, "audio-out-stereo", "objects/audio/out stereo.axo",
                "out stereo", 0, OUTPUT_UUID));
        selected.add(loadExact(
                factoryRoot.resolve("objects/patch/inlet f.axo"),
                "inlet f", 0, INLET_F_UUID));

        AxoObjects result = new AxoObjects();
        for (AxoObjectAbstract object : selected) {
            SchussObjectAccess.registerExact(result, object);
        }
        return result;
    }

    private static AxoObjectAbstract generatedFactory(
            Path factoryRoot,
            String generatedKey,
            String relativePath,
            String objectId,
            int definitionIndex,
            String expectedUuid) throws Exception {
        AxoObject generated = SchussExactGeneratedObjects.create(generatedKey);
        AxoObjectAbstract loaded = loadExact(
                factoryRoot.resolve(relativePath), objectId, definitionIndex,
                expectedUuid);
        if (!(loaded instanceof AxoObject)) {
            fail("pinned generated factory class mismatch: " + objectId);
        }
        AxoObject factory = (AxoObject) loaded;
        List<String> generatedShape = semanticShape(generated);
        List<String> factoryShape = semanticShape(factory);
        if (!generatedShape.equals(factoryShape)) {
            int limit = Math.min(generatedShape.size(), factoryShape.size());
            int first = 0;
            while (first < limit
                    && generatedShape.get(first).equals(factoryShape.get(first))) {
                first++;
            }
            fail("pinned generated factory definition mismatch: " + objectId
                    + " at " + first
                    + " generated=" + (first < generatedShape.size()
                            ? generatedShape.get(first) : "<absent>")
                    + " factory=" + (first < factoryShape.size()
                            ? factoryShape.get(first) : "<absent>"));
        }
        return loaded;
    }

    private static AxoObjectAbstract loadExact(
            Path file,
            String objectId,
            int definitionIndex,
            String expectedUuid) throws Exception {
        Serializer serializer = new Persister(new Format(2));
        AxoObjectFile values = serializer.read(AxoObjectFile.class, file.toFile());
        if (definitionIndex < 0 || definitionIndex >= values.objs.size()) {
            fail("pinned definition index is absent: " + objectId);
        }
        AxoObjectAbstract object = values.objs.get(definitionIndex);
        if (!objectId.equals(object.id) || !expectedUuid.equals(object.getUUID())) {
            fail("pinned object identity differs: " + objectId);
        }
        long matches = values.objs.stream()
                .filter(candidate -> objectId.equals(candidate.id))
                .filter(candidate -> expectedUuid.equals(candidate.getUUID()))
                .count();
        if (matches != 1) {
            fail("pinned object did not resolve uniquely: " + objectId);
        }
        return object;
    }

    private static List<String> semanticShape(AxoObject object) {
        List<String> values = new ArrayList<>();
        values.add("id:" + object.id);
        for (Inlet inlet : object.inlets) {
            values.add("in:" + inlet.getName() + ":" + inlet.getTypeName());
        }
        for (Outlet outlet : object.outlets) {
            values.add("out:" + outlet.getName() + ":" + outlet.getTypeName());
        }
        for (Parameter parameter : object.params) {
            values.add("parameter:" + parameter.getName() + ":"
                    + parameter.getClass().getName());
        }
        for (Display display : object.displays) {
            values.add("display:" + display.getName() + ":"
                    + display.getClass().getName());
        }
        values.add("local:" + Objects.toString(object.sLocalData, ""));
        values.add("init:" + Objects.toString(object.sInitCode, ""));
        values.add("krate:" + Objects.toString(object.sKRateCode, ""));
        values.add("srate:" + Objects.toString(object.sSRateCode, ""));
        return List.copyOf(values);
    }

    private static List<List<String>> verifyResolvedPatch(Patch patch) {
        List<List<String>> resolved = new ArrayList<>();
        List<AxoObjectInstanceAbstract> instances =
                SchussPatchAccess.objectInstances(patch);
        if (instances.size() != 9) {
            fail("exact Task 011C slice must contain nine explicit legacy objects");
        }
        for (AxoObjectInstanceAbstract instance : instances) {
            if (instance instanceof AxoObjectInstanceZombie || instance.getType() == null) {
                fail("exact slice contains an unresolved or zombie object");
            }
            if (!EXPECTED_UUIDS.contains(instance.typeUUID)) {
                fail("exact slice resolved an unapproved object UUID");
            }
            resolved.add(List.of(instance.getInstanceName(), instance.typeUUID));
        }
        resolved.sort((left, right) -> left.get(0).compareTo(right.get(0)));
        return List.copyOf(resolved);
    }

    private static boolean containsLocalPath(String value, Iterable<Path> paths) {
        for (Path path : paths) {
            if (value.contains(path.toString())) {
                return true;
            }
        }
        return false;
    }

    private static Map<String, Path> parseArguments(String[] arguments) {
        Set<String> allowed = Set.of(
                "axp", "output", "factory-root", "contrib-root",
                "patcher-root", "runtime-root");
        Map<String, Path> result = new LinkedHashMap<>();
        for (String argument : arguments) {
            if (!argument.startsWith("--") || !argument.contains("=")) {
                fail("arguments must use --key=value");
            }
            int separator = argument.indexOf('=');
            String key = argument.substring(2, separator);
            if (!allowed.contains(key) || result.containsKey(key)) {
                fail("unknown or duplicate argument");
            }
            result.put(key, Path.of(argument.substring(separator + 1))
                    .toAbsolutePath().normalize());
        }
        if (!result.keySet().equals(allowed)) {
            fail("exactly six bridge arguments are required");
        }
        return result;
    }

    private static String sha256(byte[] bytes) throws Exception {
        return HexFormat.of().formatHex(
                MessageDigest.getInstance("SHA-256").digest(bytes));
    }

    private static void fail(String message) {
        throw new IllegalStateException(message);
    }
}
