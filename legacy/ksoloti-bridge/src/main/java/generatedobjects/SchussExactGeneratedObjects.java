package generatedobjects;

import axoloti.object.AxoObject;

/** Narrow package-level access to the exact generated definitions used by Task 011C. */
public final class SchussExactGeneratedObjects {
    private SchussExactGeneratedObjects() {
    }

    public static AxoObject create(String key) {
        Definition definition = switch (key) {
            case "lfo-square" -> new Definition("lfo", "square", Lfo.CreateSquare());
            case "logic-counter" -> new Definition(
                    "logic", "counter", GeneratedObjects.Create_counter());
            case "osc-sine" -> new Definition("osc", "sine", Osc.CreateSRateSineOsc4());
            case "mix-xfade-mixed" -> new Definition(
                    "mix", "xfade", Mixer.Create_xfadeTilde());
            case "filter-multimode-svf-m" -> new Definition(
                    "filter", "multimode svf m", Filter.Create_svf_multimode_tilde());
            case "audio-out-stereo" -> new Definition(
                    "audio", "out stereo", Io.CreateDACTilde());
            default -> throw new IllegalArgumentException(
                    "unsupported exact generated-object key: " + key);
        };
        // Apply the same deterministic transformation used before the legacy
        // serializer writes a factory .axo: UUID derivation, placeholder-to-C
        // names, dependency normalization, and single-facet label handling.
        gentools.PostProcessObject(
                definition.object(), definition.category(), definition.fileName());
        return definition.object();
    }

    private record Definition(String category, String fileName, AxoObject object) {
    }
}
