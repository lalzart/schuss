package axoloti.object;

/** Narrow package-level access used by the isolated Schuss compatibility bridge. */
public final class SchussObjectAccess {
    private SchussObjectAccess() {
    }

    public static String sourceUuid(AxoObjectAbstract object) {
        return object.uuid;
    }

    public static void restoreUuid(AxoObjectAbstract object, String value) {
        object.uuid = value;
    }

    /** Register one already-authenticated object without scanning ambient search paths. */
    public static void registerExact(AxoObjects registry, AxoObjectAbstract object) {
        String uuid = object.getUUID();
        if (uuid == null || uuid.isEmpty()) {
            throw new IllegalArgumentException("legacy object has no stable UUID");
        }
        if (registry.ObjectUUIDMap.containsKey(uuid)) {
            throw new IllegalArgumentException("duplicate legacy object UUID");
        }
        registry.ObjectList.add(object);
        registry.ObjectUUIDMap.put(uuid, object);
    }
}
