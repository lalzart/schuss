package org.schuss.legacy.ksoloti;

import axoloti.inlets.Inlet;
import axoloti.object.AxoObject;
import axoloti.object.AxoObjectAbstract;
import axoloti.outlets.Outlet;
import axoloti.utils.AxoFileLibrary;
import axoloti.utils.AxolotiLibrary;
import axoloti.utils.Preferences;
import generatedobjects.SchussGeneratedCapture;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Exercises the real pinned generated-object path with memory-only preferences.
 *
 * <p>The probe deliberately stops before graph loading, patch generation, ARM
 * compilation, device access, upload, or flash. The serializer interception
 * captures the legacy registry emission in memory and verifies that the
 * factory object tree is byte-identical before and after the call.</p>
 */
public final class ExplicitLegacyIsolationProbe {
    private static final String MIXER_SOURCE_SHA256 =
            "385f6fc76607a0bf858307a21bd9c6627028ad89ca9db374808ffa5dba289261";
    private static final String EXPECTED_K_RATE =
            "   int32_t ccompl = ((128<<20)-inlet_c);\n";
    private static final String EXPECTED_S_RATE =
            "   {\n"
            + "      int64_t a = (int64_t)inlet_i2 * inlet_c;\n"
            + "      a += (int64_t)inlet_i1 * ccompl;\n"
            + "      outlet_o= a>>27;\n"
            + "   }\n";

    private ExplicitLegacyIsolationProbe() {
    }

    public static void main(String[] arguments) throws Exception {
        if (!Boolean.parseBoolean(System.getProperty("java.awt.headless"))) {
            fail("java.awt.headless must be true");
        }
        Map<String, Path> roots = parseRoots(arguments);
        Path factoryRoot = roots.get("factory-root");
        Path patcherRoot = roots.get("patcher-root");
        Path objectsRoot = factoryRoot.resolve("objects");
        if (!Files.isDirectory(objectsRoot)) {
            fail("factory root does not contain objects");
        }
        Path mixerSource = patcherRoot.resolve("src/main/java/generatedobjects/Mixer.java");
        requireEquals("Mixer.java SHA-256", MIXER_SOURCE_SHA256, sha256File(mixerSource));

        String before = treeFingerprint(objectsRoot);
        Preferences preferences = new Preferences();
        preferences.updateLibrary(
                AxolotiLibrary.AXOLOTI_FACTORY_ID,
                new AxoFileLibrary(
                        AxolotiLibrary.AXOLOTI_FACTORY_ID,
                        AxoFileLibrary.TYPE,
                        factoryRoot.toString(),
                        true));
        Preferences.setInstance(preferences);
        if (Preferences.getInstance() != preferences) {
            fail("memory-only preferences singleton identity changed");
        }

        List<SchussGeneratedCapture.Emission> emissions =
                SchussGeneratedCapture.capture("generatedobjects.Mixer", factoryRoot);
        SchussGeneratedCapture.Emission target = selectTarget(emissions);
        if (!(target.object() instanceof AxoObject object)) {
            fail("target emission is not an AxoObject");
            return;
        }
        verifyObject(object);

        if (Preferences.getInstance() != preferences) {
            fail("legacy generator replaced the memory-only preferences singleton");
        }
        String after = treeFingerprint(objectsRoot);
        requireEquals("factory object tree fingerprint", before, after);

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("canonical_profile", "schuss-canonical-json-v1");
        result.put("factory_tree_unchanged", true);
        result.put("generator_class", target.providerClass());
        result.put("inlets", ioSummary(object.inlets));
        result.put("memory_only_preferences_preserved", true);
        result.put("object_id", object.id);
        result.put("outlets", ioSummary(object.outlets));
        result.put("output_path", target.outputPath());
        result.put("parameter_count", object.params.size());
        result.put("attribute_count", object.attributes.size());
        result.put("k_rate_sha256", sha256Text(object.sKRateCode));
        result.put("s_rate_sha256", sha256Text(object.sSRateCode));
        result.put("schema_version", "explicit-legacy-isolation-probe-v0");
        result.put("status", "passed");
        System.out.println(StableJson.stringify(result));
    }

    private static Map<String, Path> parseRoots(String[] arguments) {
        Map<String, Path> result = new LinkedHashMap<>();
        for (String argument : arguments) {
            if (!argument.startsWith("--") || !argument.contains("=")) {
                fail("root arguments must use --key=value");
            }
            int separator = argument.indexOf('=');
            String key = argument.substring(2, separator);
            if (!key.equals("factory-root") && !key.equals("patcher-root")) {
                fail("unknown root argument");
            }
            Path root = Path.of(argument.substring(separator + 1)).toAbsolutePath().normalize();
            if (!Files.isDirectory(root) || result.put(key, root) != null) {
                fail("root argument is missing, duplicated, or not a directory");
            }
        }
        if (result.size() != 2) {
            fail("--factory-root and --patcher-root are required");
        }
        return result;
    }

    private static SchussGeneratedCapture.Emission selectTarget(
            List<SchussGeneratedCapture.Emission> emissions) {
        List<SchussGeneratedCapture.Emission> matches = emissions.stream()
                .filter(emission -> emission.outputPath().equals("objects/mix/xfade.axo"))
                .filter(emission -> emission.providerClass().equals("generatedobjects.Mixer"))
                .filter(emission -> emission.definitionIndex() == 2)
                .toList();
        if (matches.size() != 1) {
            fail("expected exactly one generated mix/xfade definition 2 emission");
        }
        return matches.get(0);
    }

    private static void verifyObject(AxoObject object) {
        requireEquals("object id", "xfade", object.id);
        requireIo(object.inlets, List.of(
                List.of("i1", "frac32buffer"),
                List.of("i2", "frac32buffer"),
                List.of("c", "frac32.positive")));
        requireIo(object.outlets, List.of(List.of("o", "frac32buffer")));
        if (!object.params.isEmpty() || !object.attributes.isEmpty()) {
            fail("target object unexpectedly has parameters or attributes");
        }
        requireEquals("K-rate code", EXPECTED_K_RATE, object.sKRateCode);
        requireEquals("S-rate code", EXPECTED_S_RATE, object.sSRateCode);
    }

    private static void requireIo(List<?> actual, List<List<String>> expected) {
        if (!ioSummary(actual).equals(expected)) {
            fail("legacy inlet/outlet signature changed");
        }
    }

    private static List<List<String>> ioSummary(List<?> values) {
        List<List<String>> result = new ArrayList<>();
        for (Object value : values) {
            if (value instanceof Inlet inlet) {
                result.add(List.of(inlet.getName(), inlet.getTypeName()));
            } else if (value instanceof Outlet outlet) {
                result.add(List.of(outlet.getName(), outlet.getTypeName()));
            } else {
                fail("unexpected inlet/outlet value type");
            }
        }
        return List.copyOf(result);
    }

    private static String treeFingerprint(Path root) throws IOException {
        MessageDigest digest = sha256();
        try (var paths = Files.walk(root)) {
            for (Path path : paths.filter(Files::isRegularFile)
                    .sorted((left, right) -> root.relativize(left).toString()
                            .compareTo(root.relativize(right).toString()))
                    .toList()) {
                digest.update(root.relativize(path).toString().replace('\\', '/').getBytes(StandardCharsets.UTF_8));
                digest.update((byte) 0);
                digest.update(Files.readAllBytes(path));
                digest.update((byte) 0);
            }
        }
        return HexFormat.of().formatHex(digest.digest());
    }

    private static String sha256File(Path path) throws IOException {
        return HexFormat.of().formatHex(sha256().digest(Files.readAllBytes(path)));
    }

    private static String sha256Text(String value) {
        return HexFormat.of().formatHex(sha256().digest(value.getBytes(StandardCharsets.UTF_8)));
    }

    private static MessageDigest sha256() {
        try {
            return MessageDigest.getInstance("SHA-256");
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }

    private static void requireEquals(String label, Object expected, Object actual) {
        if (!expected.equals(actual)) {
            if (expected instanceof String expectedText && actual instanceof String actualText) {
                fail(label + " changed: expected sha256/" + sha256Text(expectedText)
                        + ", observed sha256/" + sha256Text(actualText));
            }
            fail(label + " changed");
        }
    }

    private static void fail(String message) {
        throw new IllegalStateException(message);
    }
}
