package org.schuss.legacy.ksoloti;

import axoloti.MainFrame;
import axoloti.Patch;
import axoloti.SchussPatchAccess;
import axoloti.inlets.Inlet;
import axoloti.object.AxoObject;
import axoloti.object.AxoObjectAbstract;
import axoloti.object.AxoObjectFile;
import axoloti.object.AxoObjectInstanceAbstract;
import axoloti.object.AxoObjectInstanceZombie;
import axoloti.object.AxoObjects;
import axoloti.object.SchussObjectAccess;
import axoloti.outlets.Outlet;
import axoloti.utils.AxoFileLibrary;
import axoloti.utils.AxolotiLibrary;
import axoloti.utils.Preferences;
import generatedobjects.SchussGeneratedCapture;
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
import java.util.Set;
import org.simpleframework.xml.Serializer;
import org.simpleframework.xml.core.Persister;
import org.simpleframework.xml.stream.Format;

/**
 * Headless, exact-slice AXP-to-C++ bridge for the Task 009 Blend proof.
 *
 * <p>This class deliberately registers four exact object definitions in memory.
 * It performs no ambient catalog scan, preference load, GUI presentation, device
 * lookup, upload, flash, compilation, or firmware action.</p>
 */
public final class ExactSliceBridge {
    private static final String XFADE_UUID =
            "375dc91d218e96cdc9cbc7e92adb48f705ef701a";
    private static final String INLET_A_UUID =
            "b577fe41e0a6bc7b5502ce33cb8a3129e2e28ee5";
    private static final String INLET_F_UUID =
            "5c585d2dcd9c05631e345ac09626a22a639d7c13";
    private static final String OUTLET_A_UUID =
            "abd8c5fd3b0524a6630f65cad6dc27f6c58e2a3e";
    private static final Set<String> EXPECTED_UUIDS =
            Set.of(XFADE_UUID, INLET_A_UUID, INLET_F_UUID, OUTLET_A_UUID);

    private ExactSliceBridge() {
    }

    public static void main(String[] arguments) throws Exception {
        if (!Boolean.parseBoolean(System.getProperty("java.awt.headless"))) {
            fail("java.awt.headless must be true");
        }
        java.util.logging.Logger rootLogger =
                java.util.logging.Logger.getLogger("");
        rootLogger.setLevel(java.util.logging.Level.OFF);
        for (java.util.logging.Handler handler : rootLogger.getHandlers()) {
            handler.setLevel(java.util.logging.Level.OFF);
        }
        Map<String, Path> values = parseArguments(arguments);
        Path axp = values.get("axp");
        Path output = values.get("output");
        Path factoryRoot = values.get("factory-root");
        Path patcherRoot = values.get("patcher-root");
        Path runtimeRoot = values.get("runtime-root");
        if (!Files.isRegularFile(axp) || Files.exists(output)) {
            fail("AXP must exist and generated-source output must not exist");
        }
        if (!Files.isDirectory(factoryRoot.resolve("objects"))
                || !Files.isRegularFile(patcherRoot.resolve("src/main/java/axoloti/Patch.java"))) {
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
            AxoObjects registry = exactRegistry(factoryRoot);
            MainFrame.axoObjects = registry;
            SchussPatchAccess.initializeSynonyms();

            Serializer serializer = new Persister(new Format(2));
            Patch patch = serializer.read(Patch.class, axp.toFile());
            patch.setFileNamePath("task009/blend.axp");
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
        result.put("schema_version", "task009-exact-slice-bridge-result-v0");
        result.put("status", "success");
        result.put("axp_sha256", axpSha256);
        result.put("generated_cpp_sha256", sha256(generatedBytes));
        result.put("generated_cpp_byte_length", generatedBytes.length);
        result.put("headless", true);
        result.put("ambient_discovery", false);
        result.put("controller_enabled", false);
        result.put("registered_object_count", EXPECTED_UUIDS.size());
        result.put("resolved_objects", resolved);
        result.put("device_actions", "unreachable");
        System.out.println(StableJson.stringify(result));
    }

    private static AxoObjects exactRegistry(Path factoryRoot) throws Exception {
        List<SchussGeneratedCapture.Emission> mixer =
                SchussGeneratedCapture.capture("generatedobjects.Mixer", factoryRoot);
        AxoObjectAbstract generatedMixed = selectGeneratedMixed(mixer);
        AxoObjectAbstract factoryMixed = loadExact(
                factoryRoot.resolve("objects/mix/xfade.axo"), "xfade", XFADE_UUID);
        if (!(generatedMixed instanceof AxoObject generated)
                || !(factoryMixed instanceof AxoObject factory)
                || !ioShape(generated).equals(ioShape(factory))
                || !java.util.Objects.equals(generated.sKRateCode, factory.sKRateCode)
                || !java.util.Objects.equals(generated.sSRateCode, factory.sSRateCode)) {
            fail("pinned factory xfade differs from the captured generated definition");
        }
        List<AxoObjectAbstract> selected = List.of(
                factoryMixed,
                loadExact(factoryRoot.resolve("objects/patch/inlet a.axo"), "inlet a", INLET_A_UUID),
                loadExact(factoryRoot.resolve("objects/patch/inlet f.axo"), "inlet f", INLET_F_UUID),
                loadExact(factoryRoot.resolve("objects/patch/outlet a.axo"), "outlet a", OUTLET_A_UUID));
        AxoObjects result = new AxoObjects();
        for (AxoObjectAbstract object : selected) {
            SchussObjectAccess.registerExact(result, object);
        }
        return result;
    }

    private static AxoObjectAbstract selectGeneratedMixed(
            List<SchussGeneratedCapture.Emission> emissions) {
        List<AxoObjectAbstract> matches = emissions.stream()
                .map(SchussGeneratedCapture.Emission::object)
                .filter(object -> "xfade".equals(object.id))
                .filter(object -> ioShape(object).equals(
                        "in:i1:frac32buffer,in:i2:frac32buffer,in:c:frac32.positive,out:o:frac32buffer"))
                .toList();
        if (matches.size() != 1) {
            fail("captured generated mixed-rate xfade did not resolve uniquely");
        }
        return matches.get(0);
    }

    private static AxoObjectAbstract loadExact(
            Path file, String objectId, String expectedUuid) throws Exception {
        Serializer serializer = new Persister(new Format(2));
        AxoObjectFile values = serializer.read(AxoObjectFile.class, file.toFile());
        List<AxoObjectAbstract> matches = values.objs.stream()
                .filter(object -> objectId.equals(object.id))
                .filter(object -> expectedUuid.equals(object.getUUID()))
                .toList();
        if (matches.size() != 1) {
            fail("pinned factory object did not resolve uniquely: " + objectId);
        }
        return matches.get(0);
    }

    private static String ioShape(AxoObjectAbstract object) {
        if (!(object instanceof AxoObject concrete)) {
            return object.getClass().getName();
        }
        List<String> values = new ArrayList<>();
        for (Object inlet : concrete.inlets) {
            values.add(inlet instanceof Inlet value
                    ? "in:" + value.getName() + ":" + value.getTypeName()
                    : "in:unknown");
        }
        for (Object outlet : concrete.outlets) {
            values.add(outlet instanceof Outlet value
                    ? "out:" + value.getName() + ":" + value.getTypeName()
                    : "out:unknown");
        }
        return String.join(",", values);
    }

    private static List<List<String>> verifyResolvedPatch(Patch patch) {
        List<List<String>> resolved = new ArrayList<>();
        List<AxoObjectInstanceAbstract> instances =
                SchussPatchAccess.objectInstances(patch);
        if (instances.size() != 5) {
            fail("exact slice must contain five explicit legacy objects");
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
                "axp", "output", "factory-root", "patcher-root", "runtime-root");
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
            fail("exactly five bridge arguments are required");
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
