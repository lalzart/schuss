package org.schuss.legacy.ksoloti;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * Prerequisite-only proof that a later compiler bridge can receive every
 * environment identity explicitly without consulting mutable preferences.
 *
 * <p>This class does not load a patch, resolve an object, generate source,
 * invoke an ARM tool, or access a device.</p>
 */
public final class ExplicitCompileEnvironmentSmoke {
    private static final String[] REQUIRED_KEYS = {
        "compute-target",
        "device",
        "encoding",
        "firmware-bin",
        "firmware-link-elf",
        "flash",
        "gui",
        "java-classpath",
        "locale",
        "object-registry",
        "preferences",
        "source-capsule",
        "target-triple",
        "toolchain",
        "upload"
    };
    private static final Pattern LOCATOR = Pattern.compile("sha256/[0-9a-f]{64}");

    private ExplicitCompileEnvironmentSmoke() {
    }

    public static void main(String[] arguments) {
        Map<String, String> values = parse(arguments);
        require(values, "compute-target", "ksoloti-core");
        require(values, "target-triple", "arm-none-eabi");
        require(values, "locale", "C");
        require(values, "encoding", "UTF-8");
        for (String key : new String[] {"device", "flash", "gui", "preferences", "upload"}) {
            require(values, key, "disabled");
        }
        for (String key : new String[] {
                "firmware-bin", "firmware-link-elf", "java-classpath",
                "object-registry", "source-capsule", "toolchain"}) {
            if (!LOCATOR.matcher(values.get(key)).matches()) {
                fail("invalid content-addressed locator for " + key);
            }
        }

        StringBuilder result = new StringBuilder();
        result.append("{\"canonical_profile\":\"schuss-canonical-json-v1\",\"configuration\":{");
        for (int index = 0; index < REQUIRED_KEYS.length; index++) {
            if (index > 0) {
                result.append(',');
            }
            String key = REQUIRED_KEYS[index];
            result.append(quote(key)).append(':').append(quote(values.get(key)));
        }
        result.append("},\"schema_version\":\"explicit-compile-environment-smoke-v0\",\"status\":\"passed\"}");
        System.out.println(result);
    }

    private static Map<String, String> parse(String[] arguments) {
        Map<String, String> values = new LinkedHashMap<>();
        for (String argument : arguments) {
            if (!argument.startsWith("--") || argument.indexOf('=') < 3) {
                fail("arguments must use --key=value");
            }
            int separator = argument.indexOf('=');
            String key = argument.substring(2, separator);
            String value = argument.substring(separator + 1);
            if (values.put(key, value) != null) {
                fail("duplicate key " + key);
            }
        }
        for (String key : REQUIRED_KEYS) {
            if (!values.containsKey(key) || values.get(key).isEmpty()) {
                fail("missing key " + key);
            }
        }
        if (values.size() != REQUIRED_KEYS.length) {
            fail("unknown configuration key");
        }
        return values;
    }

    private static void require(Map<String, String> values, String key, String expected) {
        if (!expected.equals(values.get(key))) {
            fail(key + " must equal " + expected);
        }
    }

    private static String quote(String value) {
        return "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }

    private static void fail(String message) {
        throw new IllegalArgumentException(message);
    }
}
