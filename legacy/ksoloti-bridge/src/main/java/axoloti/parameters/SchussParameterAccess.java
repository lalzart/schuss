package axoloti.parameters;

/** Preserves nullable serialized parameter flags that public legacy getters flatten. */
public final class SchussParameterAccess {
    private static final java.lang.reflect.Field ON_PARENT = field("onParent");
    private static final java.lang.reflect.Field FROZEN = field("frozen");
    private static final java.lang.reflect.Field MIDI_CC = field("MidiCC");

    private SchussParameterAccess() {
    }

    public static Boolean onParent(ParameterInstance<?> parameter) {
        return (Boolean) read(ON_PARENT, parameter);
    }

    public static Boolean frozen(ParameterInstance<?> parameter) {
        return (Boolean) read(FROZEN, parameter);
    }

    public static Integer midiCc(ParameterInstance<?> parameter) {
        return (Integer) read(MIDI_CC, parameter);
    }

    private static java.lang.reflect.Field field(String name) {
        try {
            java.lang.reflect.Field field = ParameterInstance.class.getDeclaredField(name);
            field.setAccessible(true);
            return field;
        } catch (ReflectiveOperationException exception) {
            throw new ExceptionInInitializerError(exception);
        }
    }

    private static Object read(java.lang.reflect.Field field, ParameterInstance<?> parameter) {
        try {
            return field.get(parameter);
        } catch (IllegalAccessException exception) {
            throw new IllegalStateException(exception);
        }
    }
}
