package axoloti.object;

/** Narrow package-level access that observes source UUID state without generating one. */
public final class SchussObjectAccess {
    private SchussObjectAccess() {
    }

    public static String sourceUuid(AxoObjectAbstract object) {
        return object.uuid;
    }

    public static void restoreUuid(AxoObjectAbstract object, String value) {
        object.uuid = value;
    }
}
