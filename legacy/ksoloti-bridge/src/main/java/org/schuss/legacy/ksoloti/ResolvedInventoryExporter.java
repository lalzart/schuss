package org.schuss.legacy.ksoloti;

import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** Synchronous entry point for the Schuss-owned Ksoloti resolved inventory. */
public final class ResolvedInventoryExporter {
    private ResolvedInventoryExporter() {
    }

    public static void main(String[] args) {
        try {
            Config config = Config.parse(args);
            if (!java.awt.GraphicsEnvironment.isHeadless()) {
                throw new IllegalArgumentException("Run with -Djava.awt.headless=true");
            }
            export(config);
        } catch (Exception exception) {
            System.err.println("resolved inventory export failed: " + exception.getMessage());
            System.exit(2);
        }
    }

    private static void export(Config config) throws Exception {
        new LegacyResolvedExport(config).run();
    }

    static void writeJsonl(Path path, List<? extends Map<String, Object>> records) throws IOException {
        try (BufferedWriter writer = Files.newBufferedWriter(
                path,
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING,
                StandardOpenOption.WRITE)) {
            for (Map<String, Object> record : records) {
                StableJson.write(record, writer);
                writer.write('\n');
            }
        }
    }

    record Source(String id, Path root) {
    }

    record Config(Path outputDirectory, List<Source> sources, List<String> generatorClasses) {
        static Config parse(String[] args) throws IOException {
            Path output = null;
            List<Source> sources = new ArrayList<>();
            List<String> generators = new ArrayList<>();
            for (int index = 0; index < args.length; index++) {
                String option = args[index];
                if (index + 1 >= args.length) {
                    throw new IllegalArgumentException("Missing value for " + option);
                }
                String value = args[++index];
                switch (option) {
                    case "--output-dir" -> output = Path.of(value).toAbsolutePath().normalize();
                    case "--source" -> sources.add(parseSource(value));
                    case "--generator-class" -> generators.add(value);
                    default -> throw new IllegalArgumentException("Unknown option: " + option);
                }
            }
            if (output == null) {
                throw new IllegalArgumentException("--output-dir is required");
            }
            if (sources.isEmpty()) {
                throw new IllegalArgumentException("At least one --source ID=ROOT is required");
            }
            output = canonicalDestination(output);
            Set<String> sourceIds = new HashSet<>();
            Set<Path> sourceRoots = new HashSet<>();
            for (Source source : sources) {
                if (!sourceIds.add(source.id())) {
                    throw new IllegalArgumentException("Duplicate source ID: " + source.id());
                }
                if (!sourceRoots.add(source.root())) {
                    throw new IllegalArgumentException("Multiple source IDs resolve to the same root");
                }
                if (output.startsWith(source.root()) || source.root().startsWith(output)) {
                    throw new IllegalArgumentException("Output directory must not overlap a source root");
                }
            }
            Set<String> generatorNames = new HashSet<>();
            for (String generator : generators) {
                if (!generator.matches("[A-Za-z_$][A-Za-z0-9_$]*(?:\\.[A-Za-z_$][A-Za-z0-9_$]*)*")) {
                    throw new IllegalArgumentException("Invalid generator class name");
                }
                if (!generatorNames.add(generator)) {
                    throw new IllegalArgumentException("Duplicate generator class: " + generator);
                }
            }
            if (Files.exists(output) && !Files.isDirectory(output)) {
                throw new IllegalArgumentException("Output path is not a directory");
            }
            return new Config(output, List.copyOf(sources), List.copyOf(generators));
        }

        private static Path canonicalDestination(Path requested) throws IOException {
            Path absolute = requested.toAbsolutePath().normalize();
            Path existing = absolute;
            while (existing != null && !Files.exists(existing)) {
                existing = existing.getParent();
            }
            if (existing == null) {
                throw new IllegalArgumentException("Output directory has no existing ancestor");
            }
            Path realExisting = existing.toRealPath();
            return realExisting.resolve(existing.relativize(absolute)).normalize();
        }

        private static Source parseSource(String value) throws IOException {
            int separator = value.indexOf('=');
            if (separator <= 0 || separator == value.length() - 1) {
                throw new IllegalArgumentException("--source must be ID=ROOT");
            }
            String id = value.substring(0, separator);
            if (!id.matches("[a-z0-9]+(?:-[a-z0-9]+)*")) {
                throw new IllegalArgumentException("Invalid source ID: " + id);
            }
            Path root = Path.of(value.substring(separator + 1)).toRealPath();
            if (!Files.isDirectory(root)) {
                throw new IllegalArgumentException("Source root is not a directory: " + id);
            }
            return new Source(id, root);
        }
    }
}
