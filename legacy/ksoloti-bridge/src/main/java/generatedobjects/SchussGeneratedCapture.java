package generatedobjects;

import axoloti.object.AxoObjectAbstract;
import axoloti.object.AxoObjectFile;
import java.io.File;
import java.io.OutputStream;
import java.io.PrintStream;
import java.io.Writer;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import org.simpleframework.xml.Serializer;
import org.simpleframework.xml.core.Persister;
import org.simpleframework.xml.stream.Format;
import org.simpleframework.xml.stream.OutputNode;

/**
 * Intercepts the legacy generated-object serializer so provider emissions can be
 * observed without creating or changing .axo files.
 */
public final class SchussGeneratedCapture {
    public record Emission(
            String outputPath,
            String providerClass,
            int emissionIndex,
            int definitionIndex,
            AxoObjectAbstract object) {
    }

    private SchussGeneratedCapture() {
    }

    public static List<Emission> capture(String generatorClass, Path factoryRoot) throws Exception {
        Path objectsRoot = factoryRoot.resolve("objects").toAbsolutePath().normalize();
        if (!Files.isDirectory(objectsRoot)) {
            throw new IllegalArgumentException("Generator capture requires a factory objects directory");
        }
        Set<String> directoriesBefore = directorySnapshot(objectsRoot);
        Serializer previous = gentools.serializer;
        CaptureSerializer capture = new CaptureSerializer(objectsRoot);
        PrintStream previousOut = System.out;
        try {
            gentools.serializer = capture;
            System.setOut(new PrintStream(OutputStream.nullOutputStream(), true, java.nio.charset.StandardCharsets.UTF_8));
            invokeGenerator(generatorClass);
        } finally {
            System.setOut(previousOut);
            gentools.serializer = previous;
        }
        Set<String> directoriesAfter = directorySnapshot(objectsRoot);
        if (!directoriesBefore.equals(directoriesAfter)) {
            throw new IllegalStateException("Legacy generator changed the factory directory set despite serializer interception");
        }
        return List.copyOf(capture.emissions);
    }

    private static void invokeGenerator(String generatorClass) throws Exception {
        Class<?> type = Class.forName(generatorClass);
        Method method;
        try {
            method = type.getDeclaredMethod("WriteAxoObjects");
        } catch (NoSuchMethodException missingWriteMethod) {
            method = type.getDeclaredMethod("GenerateAll");
        }
        method.setAccessible(true);
        try {
            method.invoke(null);
        } catch (InvocationTargetException invocation) {
            Throwable cause = invocation.getCause();
            if (cause instanceof Exception exception) {
                throw exception;
            }
            if (cause instanceof Error error) {
                throw error;
            }
            throw invocation;
        }
    }

    private static Set<String> directorySnapshot(Path root) throws Exception {
        Set<String> result = new LinkedHashSet<>();
        try (var paths = Files.walk(root)) {
            paths.filter(Files::isDirectory)
                    .map(root::relativize)
                    .map(Path::toString)
                    .map(value -> value.replace(File.separatorChar, '/'))
                    .sorted()
                    .forEach(result::add);
        }
        return result;
    }

    private static final class CaptureSerializer extends Persister {
        private final Path objectsRoot;
        private final List<Emission> emissions = new ArrayList<>();
        private int writeCallIndex;

        CaptureSerializer(Path objectsRoot) {
            super(new Format(2));
            this.objectsRoot = objectsRoot;
        }

        @Override
        public void write(Object source, File destination) {
            if (!(source instanceof AxoObjectFile objectFile)) {
                throw new IllegalStateException("Unexpected generated serialization type: " + source.getClass().getName());
            }
            Path target = destination.toPath().toAbsolutePath().normalize();
            if (!target.startsWith(objectsRoot)) {
                throw new IllegalStateException("Generated target escaped factory objects root");
            }
            String outputPath = objectsRoot.getParent().relativize(target).toString().replace(File.separatorChar, '/');
            String provider = providerClass();
            int emissionIndex = writeCallIndex++;
            for (int definitionIndex = 0; definitionIndex < objectFile.objs.size(); definitionIndex++) {
                emissions.add(new Emission(
                        outputPath,
                        provider,
                        emissionIndex,
                        definitionIndex,
                        objectFile.objs.get(definitionIndex)));
            }
        }

        @Override
        public void write(Object source, OutputStream destination) {
            // The legacy writer uses this only for its on-disk equality check.
            // Leaving the stream empty forces the subsequent File overload,
            // where the emission is captured without touching the destination.
        }

        @Override
        public void write(Object source, Writer destination) {
            throw new IllegalStateException("Unexpected generated Writer serialization");
        }

        @Override
        public void write(Object source, OutputNode destination) {
            throw new IllegalStateException("Unexpected generated OutputNode serialization");
        }

        private static String providerClass() {
            return StackWalker.getInstance(StackWalker.Option.RETAIN_CLASS_REFERENCE).walk(frames -> frames
                    .map(StackWalker.StackFrame::getClassName)
                    .filter(name -> name.startsWith("generatedobjects."))
                    .filter(name -> !name.equals(gentools.class.getName()))
                    .filter(name -> !name.startsWith(SchussGeneratedCapture.class.getName()))
                    .findFirst()
                    .orElse("generatedobjects.GeneratedObjects"));
        }
    }
}
