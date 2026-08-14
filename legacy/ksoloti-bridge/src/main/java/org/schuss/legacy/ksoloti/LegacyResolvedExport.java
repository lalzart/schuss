package org.schuss.legacy.ksoloti;

import axoloti.MainFrame;
import axoloti.Modulator;
import axoloti.SchussPatchAccess;
import axoloti.displays.Display;
import axoloti.inlets.Inlet;
import axoloti.object.AxoObject;
import axoloti.object.AxoObjectAbstract;
import axoloti.object.AxoObjectComment;
import axoloti.object.AxoObjectFile;
import axoloti.object.AxoObjectHyperlink;
import axoloti.object.AxoObjectTreeNode;
import axoloti.object.AxoObjectUnloaded;
import axoloti.object.AxoObjects;
import axoloti.object.SchussObjectAccess;
import axoloti.outlets.Outlet;
import axoloti.parameters.Parameter;
import axoloti.attributedefinition.AxoAttribute;
import axoloti.sd.SDFileReference;
import axoloti.utils.AxoFileLibrary;
import axoloti.utils.Preferences;
import generatedobjects.SchussGeneratedCapture;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.lang.annotation.Annotation;
import java.lang.reflect.AnnotatedElement;
import java.lang.reflect.Array;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import javax.xml.parsers.DocumentBuilderFactory;
import org.simpleframework.xml.Serializer;
import org.simpleframework.xml.core.Persister;
import org.simpleframework.xml.stream.Format;
import org.w3c.dom.Element;
import org.w3c.dom.NamedNodeMap;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;

final class LegacyResolvedExport {
    private static final Set<String> SUPPORTED_INLET_TYPES = Set.of(
            "axoloti.inlets.InletBool32",
            "axoloti.inlets.InletBool32Rising",
            "axoloti.inlets.InletBool32RisingFalling",
            "axoloti.inlets.InletCharPtr32",
            "axoloti.inlets.InletFrac32",
            "axoloti.inlets.InletFrac32Bipolar",
            "axoloti.inlets.InletFrac32Buffer",
            "axoloti.inlets.InletFrac32BufferBipolar",
            "axoloti.inlets.InletFrac32BufferPos",
            "axoloti.inlets.InletFrac32Pos",
            "axoloti.inlets.InletInt32",
            "axoloti.inlets.InletInt32Bipolar",
            "axoloti.inlets.InletInt32Pos");
    private static final Set<String> SUPPORTED_OUTLET_TYPES = Set.of(
            "axoloti.outlets.OutletBool32",
            "axoloti.outlets.OutletBool32Pulse",
            "axoloti.outlets.OutletCharPtr32",
            "axoloti.outlets.OutletFrac32",
            "axoloti.outlets.OutletFrac32Bipolar",
            "axoloti.outlets.OutletFrac32Buffer",
            "axoloti.outlets.OutletFrac32BufferBipolar",
            "axoloti.outlets.OutletFrac32BufferPos",
            "axoloti.outlets.OutletFrac32Pos",
            "axoloti.outlets.OutletInt32",
            "axoloti.outlets.OutletInt32Bipolar",
            "axoloti.outlets.OutletInt32Pos");
    private static final Set<String> SUPPORTED_PARAMETER_TYPES = Set.of(
            "axoloti.parameters.Parameter4LevelX16",
            "axoloti.parameters.ParameterBin1",
            "axoloti.parameters.ParameterBin1Momentary",
            "axoloti.parameters.ParameterBin8",
            "axoloti.parameters.ParameterBin12",
            "axoloti.parameters.ParameterBin16",
            "axoloti.parameters.ParameterBin32",
            "axoloti.parameters.ParameterFrac32SMap",
            "axoloti.parameters.ParameterFrac32SMapKDTimeExp",
            "axoloti.parameters.ParameterFrac32SMapKLineTimeExp",
            "axoloti.parameters.ParameterFrac32SMapKLineTimeExp2",
            "axoloti.parameters.ParameterFrac32SMapKPitch",
            "axoloti.parameters.ParameterFrac32SMapLFOPitch",
            "axoloti.parameters.ParameterFrac32SMapPitch",
            "axoloti.parameters.ParameterFrac32SMapRatio",
            "axoloti.parameters.ParameterFrac32SMapVSlider",
            "axoloti.parameters.ParameterFrac32UMap",
            "axoloti.parameters.ParameterFrac32UMapFilterQ",
            "axoloti.parameters.ParameterFrac32UMapFreq",
            "axoloti.parameters.ParameterFrac32UMapGain",
            "axoloti.parameters.ParameterFrac32UMapGain16",
            "axoloti.parameters.ParameterFrac32UMapGainSquare",
            "axoloti.parameters.ParameterFrac32UMapKDecayTime",
            "axoloti.parameters.ParameterFrac32UMapKDecayTimeReverse",
            "axoloti.parameters.ParameterFrac32UMapKLineTimeReverse",
            "axoloti.parameters.ParameterFrac32UMapRatio",
            "axoloti.parameters.ParameterFrac32UMapVSlider",
            "axoloti.parameters.ParameterInt32Box",
            "axoloti.parameters.ParameterInt32BoxSmall",
            "axoloti.parameters.ParameterInt32HRadio",
            "axoloti.parameters.ParameterInt32VRadio");
    private static final Set<String> SUPPORTED_ATTRIBUTE_TYPES = Set.of(
            "axoloti.attributedefinition.AxoAttributeComboBox",
            "axoloti.attributedefinition.AxoAttributeInt32",
            "axoloti.attributedefinition.AxoAttributeObjRef",
            "axoloti.attributedefinition.AxoAttributeSDFile",
            "axoloti.attributedefinition.AxoAttributeSpinner",
            "axoloti.attributedefinition.AxoAttributeTablename",
            "axoloti.attributedefinition.AxoAttributeTextEditor");
    private static final Set<String> SUPPORTED_DISPLAY_TYPES = Set.of(
            "axoloti.displays.DisplayBool32",
            "axoloti.displays.DisplayBool32Red",
            "axoloti.displays.DisplayBool32Yellow",
            "axoloti.displays.DisplayFrac4ByteVBar",
            "axoloti.displays.DisplayFrac4UByteVBar",
            "axoloti.displays.DisplayFrac4UByteVBarDB",
            "axoloti.displays.DisplayFrac8S128VBar",
            "axoloti.displays.DisplayFrac8S128XY",
            "axoloti.displays.DisplayFrac8U128VBar",
            "axoloti.displays.DisplayFrac32SChart",
            "axoloti.displays.DisplayFrac32SDial",
            "axoloti.displays.DisplayFrac32UChart",
            "axoloti.displays.DisplayFrac32UDial",
            "axoloti.displays.DisplayFrac32VBar",
            "axoloti.displays.DisplayFrac32VBarDB",
            "axoloti.displays.DisplayFrac32VU",
            "axoloti.displays.DisplayFrac32VUHorizontal",
            "axoloti.displays.DisplayInt8HexLabel",
            "axoloti.displays.DisplayInt32Bar16",
            "axoloti.displays.DisplayInt32Bar32",
            "axoloti.displays.DisplayInt32HexLabel",
            "axoloti.displays.DisplayInt32Label",
            "axoloti.displays.DisplayNoteLabel",
            "axoloti.displays.DisplayVScale");
    private static final Set<String> SUPPORTED_LEGACY_PROPERTIES = Set.of(
            "CEntries", "DefaultValue", "MaxValue", "MenuEntries", "MinValue", "SumBuffer");

    private static final Comparator<File> LEGACY_FILE_ORDER = (left, right) -> {
        String leftName = left.getName();
        String rightName = right.getName();
        if (leftName.startsWith(rightName)) {
            return 1;
        }
        if (rightName.startsWith(leftName)) {
            return -1;
        }
        return leftName.compareTo(rightName);
    };

    private final ResolvedInventoryExporter.Config config;
    private final Serializer serializer = new Persister(new Format(2));
    private final List<ObjectVariant> variants = new ArrayList<>();
    private final List<Issue> issues = new ArrayList<>();
    private final IdentityHashMap<AxoObjectAbstract, Integer> variantByActual = new IdentityHashMap<>();
    private AxoObjects registry;

    LegacyResolvedExport(ResolvedInventoryExporter.Config config) {
        this.config = config;
    }

    void run() throws Exception {
        installMemoryOnlyPreferences();
        loadRegistryAndCatalog();
        captureAndJoinGenerators();
        emitCandidateIssues();

        List<Map<String, Object>> objectRecords = new ArrayList<>();
        for (ObjectVariant variant : variants) {
            objectRecords.add(objectRecord(variant));
        }

        GraphRecordExporter.Result graphExport = GraphRecordExporter.export(config.sources(), graphCatalogLookup());
        List<Map<String, Object>> graphRecords = graphExport.graphs();
        List<Map<String, Object>> issueRecords = new ArrayList<>();
        for (Issue issue : issues) {
            issueRecords.add(issue.toMap(0));
        }
        issueRecords.addAll(graphExport.issues());
        issueRecords.sort(LegacyResolvedExport::compareIssueRecords);
        for (int index = 0; index < issueRecords.size(); index++) {
            issueRecords.get(index).put("issue_index", index);
        }

        Path resolved = config.outputDirectory().resolve("resolved");
        Files.createDirectories(resolved);
        ResolvedInventoryExporter.writeJsonl(resolved.resolve("objects.jsonl"), objectRecords);
        ResolvedInventoryExporter.writeJsonl(resolved.resolve("graphs.jsonl"), graphRecords);
        ResolvedInventoryExporter.writeJsonl(resolved.resolve("issues.jsonl"), issueRecords);
    }

    private GraphRecordExporter.CatalogLookup graphCatalogLookup() {
        return new GraphRecordExporter.CatalogLookup() {
            @Override
            public List<Integer> candidatesByUuid(String uuid) {
                List<Integer> result = new ArrayList<>();
                for (ObjectVariant variant : variants) {
                    boolean matchesSource = java.util.Objects.equals(variant.sourceUuid, uuid);
                    boolean matchesSentinel = "unloaded".equals(uuid)
                            && variant.object instanceof AxoObjectUnloaded;
                    if (variant.originProvider == null && (matchesSource || matchesSentinel)) {
                        result.add(variant.variantIndex);
                    }
                }
                return List.copyOf(result);
            }

            @Override
            public List<Integer> candidatesByName(String legacyId) {
                List<Integer> result = new ArrayList<>();
                for (AxoObjectAbstract actual : registry.ObjectList) {
                    if (!java.util.Objects.equals(actual.id, legacyId)) {
                        continue;
                    }
                    Integer variantIndex = variantForActualWithFileFallback(actual);
                    if (variantIndex != null && !result.contains(variantIndex)) {
                        result.add(variantIndex);
                    }
                }
                return List.copyOf(result);
            }

            @Override
            public List<Integer> candidatesByFile(Path absoluteAxo) {
                Path normalized = absoluteAxo.toAbsolutePath().normalize();
                for (ObjectVariant variant : variants) {
                    if (variant.originProvider == null && variant.definitionIndex == 0
                            && variant.absolutePath.equals(normalized)) {
                        return List.of(variant.variantIndex);
                    }
                }
                return List.of();
            }

            @Override
            public Integer variantForActual(AxoObjectAbstract actual) {
                return variantByActual.get(actual);
            }
        };
    }

    private Integer variantForActualWithFileFallback(AxoObjectAbstract actual) {
        Integer direct = variantByActual.get(actual);
        if (direct != null) {
            return direct;
        }
        if (actual == null || actual.sObjFilePath == null) {
            return null;
        }
        Path absolute;
        try {
            absolute = Path.of(actual.sObjFilePath).toAbsolutePath().normalize();
        } catch (RuntimeException exception) {
            return null;
        }
        for (ObjectVariant variant : variants) {
            if (variant.originProvider == null
                    && variant.absolutePath.equals(absolute)
                    && java.util.Objects.equals(variant.legacyId, actual.id)) {
                return variant.variantIndex;
            }
        }
        return null;
    }

    private void installMemoryOnlyPreferences() {
        Preferences preferences = new Preferences();
        for (ResolvedInventoryExporter.Source source : config.sources()) {
            if (Files.isDirectory(source.root().resolve("objects"))) {
                preferences.updateLibrary(
                        source.id(),
                        new AxoFileLibrary(source.id(), AxoFileLibrary.TYPE, source.root().toString(), true));
            }
        }
        Preferences.setInstance(preferences);
        SchussPatchAccess.initializeSynonyms();
    }

    private void loadRegistryAndCatalog() {
        registry = new AxoObjects();
        List<AxoObjectAbstract> actualOccurrences = new ArrayList<>();
        Set<AxoObjectAbstract> seenActual = java.util.Collections.newSetFromMap(new IdentityHashMap<>());

        for (ResolvedInventoryExporter.Source source : config.sources()) {
            Path objectsRoot = source.root().resolve("objects");
            if (!Files.isDirectory(objectsRoot)) {
                continue;
            }
            scanCatalogFolder(source, objectsRoot, objectsRoot.toFile(), "");
            try {
                AxoObjectTreeNode tree = registry.LoadAxoObjectsFromFolder(objectsRoot.toFile(), "");
                registry.ObjectTree.SubNodes.put(source.id(), tree);
                collectTreeObjects(tree, actualOccurrences, seenActual);
            } catch (RuntimeException exception) {
                issues.add(Issue.global(
                        "error",
                        "catalog-load",
                        "LEGACY_CATALOG_LOAD_FAILED",
                        source,
                        "objects",
                        "Legacy synchronous folder loading failed for this source."));
            }
        }
        MainFrame.axoObjects = registry;
        matchActualOccurrences(actualOccurrences);
    }

    private void scanCatalogFolder(
            ResolvedInventoryExporter.Source source,
            Path objectsRoot,
            File folder,
            String prefix) {
        File[] entries = folder.listFiles();
        if (entries == null) {
            issues.add(Issue.global(
                    "error",
                    "catalog-load",
                    "OBJECT_DIRECTORY_UNREADABLE",
                    source,
                    portable(source, folder.toPath()),
                    "Object directory could not be enumerated."));
            return;
        }
        Arrays.sort(entries, LEGACY_FILE_ORDER);
        for (File entry : entries) {
            if (entry.isDirectory()) {
                String childPrefix = prefix.isEmpty() ? entry.getName() : prefix + "/" + entry.getName();
                scanCatalogFolder(source, objectsRoot, entry, childPrefix);
            } else if (entry.getName().endsWith(".axo")) {
                scanObjectFile(source, objectsRoot, entry.toPath(), prefix);
            } else if (entry.getName().endsWith(".axs")) {
                String base = entry.getName().substring(0, entry.getName().length() - 4);
                String legacyId = prefix.isEmpty() ? base : prefix + "/" + base;
                AxoObjectUnloaded placeholder = new AxoObjectUnloaded(legacyId, entry);
                variants.add(ObjectVariant.file(
                        variants.size(), source, portable(source, entry.toPath()), entry.toPath(), sha256(entry.toPath()),
                        0, placeholder, null, legacyId, base, "subpatch_catalog_placeholder"));
            }
        }
    }

    private void scanObjectFile(
            ResolvedInventoryExporter.Source source,
            Path objectsRoot,
            Path file,
            String prefix) {
        String path = portable(source, file);
        String hash;
        try {
            hash = sha256(file);
        } catch (RuntimeException exception) {
            issues.add(Issue.global("error", "catalog-load", "OBJECT_HASH_FAILED", source, path,
                    "Object file could not be hashed."));
            return;
        }
        AxoObjectFile objectFile;
        try {
            objectFile = serializer.read(AxoObjectFile.class, file.toFile());
        } catch (Exception strictFailure) {
            try {
                objectFile = serializer.read(AxoObjectFile.class, file.toFile(), false);
                issues.add(Issue.global("warning", "catalog-load", "OBJECT_PARSE_RELAXED", source, path,
                        "Strict object parsing failed; relaxed legacy parsing succeeded."));
            } catch (Exception relaxedFailure) {
                issues.add(Issue.global("error", "catalog-load", "OBJECT_PARSE_FAILED", source, path,
                        "Strict and relaxed legacy object parsing both failed."));
                return;
            }
        }
        if (objectFile.objs == null || objectFile.objs.isEmpty()) {
            issues.add(Issue.global("warning", "catalog-load", "OBJECT_FILE_ZERO_DEFINITIONS", source, path,
                    "Object file contains no definitions."));
            return;
        }
        for (int definitionIndex = 0; definitionIndex < objectFile.objs.size(); definitionIndex++) {
            AxoObjectAbstract object = objectFile.objs.get(definitionIndex);
            String sourceUuid = SchussObjectAccess.sourceUuid(object);
            String legacyId = prefix.isEmpty() ? object.id : prefix + "/" + object.id;
            String shortId = shortId(legacyId);
            String kind = legacyKind(object);
            ObjectVariant variant = ObjectVariant.file(
                    variants.size(), source, path, file, hash, definitionIndex, object,
                    sourceUuid, legacyId, shortId, kind);
            if (kind.equals("unsupported")) {
                variant.partial = true;
                issues.add(Issue.object("warning", "object-export", "UNSUPPORTED_OBJECT_DEFINITION",
                        variant, "Object definition class is not represented by the locked legacy union."));
            }
            variants.add(variant);
        }
    }

    private static void collectTreeObjects(
            AxoObjectTreeNode tree,
            List<AxoObjectAbstract> result,
            Set<AxoObjectAbstract> seen) {
        for (AxoObjectAbstract object : tree.Objects) {
            if (seen.add(object)) {
                result.add(object);
            }
        }
        for (AxoObjectTreeNode child : tree.SubNodes.values()) {
            collectTreeObjects(child, result, seen);
        }
    }

    private void matchActualOccurrences(List<AxoObjectAbstract> actualOccurrences) {
        Map<String, ArrayDeque<AxoObjectAbstract>> actualByKey = new HashMap<>();
        for (AxoObjectAbstract actual : actualOccurrences) {
            String key = actualKey(actual.sObjFilePath, actual.id, actual.getClass().getName());
            actualByKey.computeIfAbsent(key, ignored -> new ArrayDeque<>()).add(actual);
        }
        for (ObjectVariant variant : variants) {
            String key = actualKey(variant.absolutePath.toString(), variant.legacyId, variant.object.getClass().getName());
            ArrayDeque<AxoObjectAbstract> candidates = actualByKey.get(key);
            if (candidates == null || candidates.isEmpty()) {
                variant.partial = true;
                issues.add(Issue.object("error", "reconcile", "CATALOG_VARIANT_NOT_OBSERVED_BY_LEGACY_LOADER",
                        variant, "Direct definition occurrence was not observed in the synchronous legacy loader tree."));
                continue;
            }
            variant.actual = candidates.removeFirst();
            int legacyIndex = identityIndex(registry.ObjectList, variant.actual);
            variant.legacyObjectListIndex = legacyIndex < 0 ? null : legacyIndex;
            variantByActual.put(variant.actual, variant.variantIndex);
        }
    }

    private void emitCandidateIssues() {
        Map<String, List<Integer>> names = new TreeMap<>();
        Map<String, List<Integer>> explicitUuids = new TreeMap<>();
        for (ObjectVariant variant : variants) {
            if (variant.originProvider != null) {
                continue;
            }
            names.computeIfAbsent(variant.legacyId, ignored -> new ArrayList<>()).add(variant.variantIndex);
            if (variant.sourceUuid != null && !variant.sourceUuid.equals("unloaded")) {
                explicitUuids.computeIfAbsent(variant.sourceUuid, ignored -> new ArrayList<>()).add(variant.variantIndex);
            }
        }
        for (Map.Entry<String, List<Integer>> entry : names.entrySet()) {
            if (entry.getValue().size() > 1) {
                ObjectVariant first = variants.get(entry.getValue().get(0));
                issues.add(Issue.objectGroup("info", "catalog-load", "OVERLOADED_NAME_CANDIDATES", first,
                        "Multiple ordered catalog variants share one legacy object ID.", entry.getValue()));
            }
        }
        for (Map.Entry<String, List<Integer>> entry : explicitUuids.entrySet()) {
            if (entry.getValue().size() > 1) {
                ObjectVariant first = variants.get(entry.getValue().get(0));
                issues.add(Issue.objectGroup("error", "catalog-load", "DUPLICATE_UUID_CANDIDATES", first,
                        "Multiple ordered catalog variants carry the same explicit UUID.", entry.getValue()));
            }
        }
        emitCollapseIssues();
    }

    private void captureAndJoinGenerators() {
        if (config.generatorClasses().isEmpty()) {
            return;
        }
        ResolvedInventoryExporter.Source factory = config.sources().stream()
                .filter(source -> source.id().equals("axoloti-factory"))
                .findFirst()
                .orElse(null);
        if (factory == null || !Files.isDirectory(factory.root().resolve("objects"))) {
            issues.add(Issue.global("error", "source-config", "GENERATED_FACTORY_SOURCE_MISSING", null, null,
                    "Generated-object capture requires the enabled axoloti-factory source."));
            return;
        }
        for (String generatorClass : config.generatorClasses()) {
            List<SchussGeneratedCapture.Emission> emissions;
            try {
                emissions = SchussGeneratedCapture.capture(generatorClass, factory.root());
            } catch (Exception exception) {
                issues.add(Issue.global("error", "object-export", "GENERATED_CAPTURE_FAILED", factory, null,
                        "Legacy generated-object provider capture failed closed."));
                continue;
            }
            reconcileEmissions(factory, emissions);
        }
    }

    private void reconcileEmissions(
            ResolvedInventoryExporter.Source factory,
            List<SchussGeneratedCapture.Emission> emissions) {
        Map<String, TreeMap<Integer, List<SchussGeneratedCapture.Emission>>> byPath = new TreeMap<>();
        for (SchussGeneratedCapture.Emission emission : emissions) {
            byPath.computeIfAbsent(emission.outputPath(), ignored -> new TreeMap<>())
                    .computeIfAbsent(emission.emissionIndex(), ignored -> new ArrayList<>())
                    .add(emission);
        }
        for (Map.Entry<String, TreeMap<Integer, List<SchussGeneratedCapture.Emission>>> pathEntry : byPath.entrySet()) {
            String outputPath = pathEntry.getKey();
            TreeMap<Integer, List<SchussGeneratedCapture.Emission>> calls = pathEntry.getValue();
            if (calls.size() > 1) {
                Set<String> payloads = new LinkedHashSet<>();
                for (List<SchussGeneratedCapture.Emission> call : calls.values()) {
                    payloads.add(callFingerprint(call));
                }
                String code = payloads.size() == 1
                        ? "GENERATED_OUTPUT_REPEATED_IDENTICAL"
                        : "GENERATED_OUTPUT_REDEFINED";
                issues.add(Issue.global("warning", "reconcile", code, factory, outputPath,
                        payloads.size() == 1
                                ? "Generated provider repeated an identical output path; only the final write call is effective."
                                : "Generated provider redefined an output path; only the final write call is effective."));
            }
            List<SchussGeneratedCapture.Emission> effective = calls.lastEntry().getValue().stream()
                    .sorted(Comparator.comparingInt(SchussGeneratedCapture.Emission::definitionIndex))
                    .toList();
            List<ObjectVariant> targets = variants.stream()
                    .filter(variant -> variant.source.id().equals(factory.id()) && variant.path.equals(outputPath))
                    .sorted(Comparator.comparingInt(variant -> variant.definitionIndex))
                    .toList();
            boolean countMatches = effective.size() == targets.size();
            if (!countMatches) {
                issues.add(Issue.global("error", "reconcile", "GENERATED_DEFINITION_COUNT_MISMATCH", factory,
                        outputPath, "Effective generated definition count differs from the pinned factory file."));
            }
            for (SchussGeneratedCapture.Emission emission : effective) {
                ProviderRef provider = providerRef(emission);
                if (provider == null) {
                    issues.add(Issue.global("error", "reconcile", "GENERATED_PROVIDER_SOURCE_MISSING", factory,
                            outputPath, "Captured provider class could not be traced to a pinned Java source."));
                    continue;
                }
                ObjectVariant target = targets.stream()
                        .filter(variant -> variant.definitionIndex == emission.definitionIndex())
                        .findFirst()
                        .orElse(null);
                SchussObjectAccess.restoreUuid(emission.object(), null);
                boolean exact = countMatches && target != null
                        && canonicalObjectFingerprint(target.object).equals(canonicalObjectFingerprint(emission.object()));
                if (exact) {
                    target.generatedBy = provider;
                } else {
                    ObjectVariant providerOnly = ObjectVariant.provider(
                            variants.size(), factory, provider, outputPath, factory.root().resolve(outputPath),
                            emission.definitionIndex(), emission.object(), generatedLegacyId(outputPath, emission.object().id));
                    providerOnly.partial = true;
                    variants.add(providerOnly);
                    Issue issue = Issue.object("error", "reconcile", "GENERATED_EMISSION_UNMATCHED", providerOnly,
                            target == null
                                    ? "Captured generated definition has no exact pinned path-and-ordinal target."
                                    : "Captured generated definition differs from its pinned path-and-ordinal target after UUID normalization.");
                    if (target != null) {
                        issue.candidateVariantIndexes.add(target.variantIndex);
                    }
                    issues.add(issue);
                }
            }
        }
    }

    private ProviderRef providerRef(SchussGeneratedCapture.Emission emission) {
        String relative = "src/main/java/" + emission.providerClass().replace('.', '/') + ".java";
        for (ResolvedInventoryExporter.Source source : config.sources()) {
            Path candidate = source.root().resolve(relative);
            if (Files.isRegularFile(candidate)) {
                return new ProviderRef(
                        source.id(), relative, sha256(candidate), emission.providerClass(), emission.emissionIndex());
            }
        }
        return null;
    }

    private String callFingerprint(List<SchussGeneratedCapture.Emission> emissions) {
        StringBuilder value = new StringBuilder();
        emissions.stream()
                .sorted(Comparator.comparingInt(SchussGeneratedCapture.Emission::definitionIndex))
                .forEach(emission -> value.append(emission.definitionIndex())
                        .append(':').append(canonicalObjectFingerprint(emission.object())).append(';'));
        return sha256(value.toString().getBytes(StandardCharsets.UTF_8));
    }

    private String canonicalObjectFingerprint(AxoObjectAbstract object) {
        String runtimeUuid = SchussObjectAccess.sourceUuid(object);
        try {
            SchussObjectAccess.restoreUuid(object, null);
            AxoObjectFile wrapper = new AxoObjectFile();
            wrapper.objs.add(object);
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            serializer.write(wrapper, output);
            DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
            factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            factory.setExpandEntityReferences(false);
            Element root = factory.newDocumentBuilder()
                    .parse(new ByteArrayInputStream(output.toByteArray()))
                    .getDocumentElement();
            Element definition = firstElement(root);
            if (definition == null) {
                throw new IllegalStateException("Serialized object contained no definition element");
            }
            return sha256(canonicalElement(definition).getBytes(StandardCharsets.UTF_8));
        } catch (Exception exception) {
            throw new IllegalStateException("Unable to canonicalize legacy object model", exception);
        } finally {
            SchussObjectAccess.restoreUuid(object, runtimeUuid);
        }
    }

    private static Element firstElement(Element parent) {
        NodeList children = parent.getChildNodes();
        for (int index = 0; index < children.getLength(); index++) {
            if (children.item(index) instanceof Element element) return element;
        }
        return null;
    }

    private static String canonicalElement(Element element) {
        String tag = element.getTagName();
        TreeMap<String, String> attributes = new TreeMap<>();
        NamedNodeMap rawAttributes = element.getAttributes();
        for (int index = 0; index < rawAttributes.getLength(); index++) {
            Node attribute = rawAttributes.item(index);
            if (!attribute.getNodeName().equals("uuid") && !attribute.getNodeName().equals("sha")) {
                attributes.put(attribute.getNodeName(), attribute.getNodeValue());
            }
        }
        List<Element> childElements = new ArrayList<>();
        StringBuilder text = new StringBuilder();
        NodeList children = element.getChildNodes();
        for (int index = 0; index < children.getLength(); index++) {
            Node child = children.item(index);
            if (child instanceof Element childElement) {
                if (!childElement.getTagName().equals("upgradeSha")) childElements.add(childElement);
            } else if (child.getNodeType() == Node.TEXT_NODE || child.getNodeType() == Node.CDATA_SECTION_NODE) {
                text.append(child.getNodeValue().replace("\r\n", "\n").replace('\r', '\n'));
            }
        }
        if ((tag.equals("includes") || tag.equals("depends")) && childElements.isEmpty()) {
            return "";
        }
        List<String> canonicalChildren = new ArrayList<>();
        for (Element child : childElements) {
            String canonical = canonicalElement(child);
            if (!canonical.isEmpty()) canonicalChildren.add(canonical);
        }
        if (tag.equals("includes") || tag.equals("depends")) {
            canonicalChildren.sort(String::compareTo);
        }
        StringBuilder result = new StringBuilder();
        appendFramed(result, "tag", tag);
        for (Map.Entry<String, String> attribute : attributes.entrySet()) {
            appendFramed(result, "attribute", attribute.getKey());
            appendFramed(result, "value", attribute.getValue());
        }
        if (childElements.isEmpty()) {
            appendFramed(result, "text", text.toString());
        }
        for (String child : canonicalChildren) appendFramed(result, "child", child);
        return result.toString();
    }

    private static void appendFramed(StringBuilder output, String kind, String value) {
        output.append(kind).append('[').append(value.length()).append(']').append(value);
    }

    private static String generatedLegacyId(String outputPath, String objectId) {
        String withoutObjects = outputPath.startsWith("objects/") ? outputPath.substring(8) : outputPath;
        int slash = withoutObjects.lastIndexOf('/');
        String prefix = slash < 0 ? "" : withoutObjects.substring(0, slash);
        return prefix.isEmpty() ? objectId : prefix + "/" + objectId;
    }

    private void emitCollapseIssues() {
        List<SimulatedSurvivor> survivors = new ArrayList<>();
        Map<Integer, List<Integer>> collapsedBySurvivor = new LinkedHashMap<>();
        for (ObjectVariant variant : variants) {
            if (variant.originProvider != null) {
                continue;
            }
            String preUuid = variant.sourceUuid;
            SimulatedSurvivor matched = null;
            for (SimulatedSurvivor survivor : survivors) {
                if (legacyEquals(survivor.runtimeUuid, survivor.path, preUuid, variant.absolutePath.toString())) {
                    matched = survivor;
                    break;
                }
            }
            if (matched == null) {
                survivors.add(new SimulatedSurvivor(
                        variant.variantIndex,
                        postLoadUuid(variant),
                        variant.absolutePath.toString()));
            } else {
                collapsedBySurvivor.computeIfAbsent(matched.variantIndex, ignored -> new ArrayList<>())
                        .add(variant.variantIndex);
            }
        }
        for (Map.Entry<Integer, List<Integer>> entry : collapsedBySurvivor.entrySet()) {
            List<Integer> indexes = new ArrayList<>();
            indexes.add(entry.getKey());
            indexes.addAll(entry.getValue());
            ObjectVariant survivor = variants.get(entry.getKey());
            Issue issue = Issue.objectGroup("warning", "reconcile", "LEGACY_OBJECT_LIST_COLLAPSE", survivor,
                    "Legacy equality omitted later definition occurrences from ObjectList.", indexes);
            issue.facts.add(fact("legacy_object_list_index", "integer", survivor.legacyObjectListIndex));
            issues.add(issue);
        }
    }

    private static boolean legacyEquals(String leftUuid, String leftPath, String rightUuid, String rightPath) {
        boolean leftValid = leftUuid != null && !leftUuid.equals("unloaded");
        boolean rightValid = rightUuid != null && !rightUuid.equals("unloaded");
        if (leftValid && rightValid) {
            return leftUuid.equals(rightUuid);
        }
        return leftPath.equals(rightPath);
    }

    private static String postLoadUuid(ObjectVariant variant) {
        if (variant.sourceUuid != null) {
            return variant.sourceUuid;
        }
        if (variant.object instanceof AxoObjectUnloaded) {
            return "unloaded";
        }
        if (variant.object instanceof AxoObjectComment || variant.object instanceof AxoObjectHyperlink) {
            return null;
        }
        return "generated:" + variant.variantIndex;
    }

    private Map<String, Object> objectRecord(ObjectVariant variant) {
        // Facet extraction is fail-closed and may mark the variant partial, so
        // observe its final status only after all facets have been inspected.
        Map<String, Object> facetRecords = facets(variant);
        Map<String, Object> record = map();
        record.put("schema_version", "legacy-resolved-object-v0");
        record.put("variant_index", variant.variantIndex);
        record.put("legacy_object_list_index", variant.legacyObjectListIndex);
        record.put("legacy_kind", variant.legacyKind);
        record.put("legacy_class", variant.object.getClass().getName());
        record.put("legacy_id", variant.legacyId);
        record.put("legacy_short_id", variant.shortId);
        record.put("export_status", variant.partial ? "partial" : "complete");
        record.put("origin", fileOrigin(variant));
        record.put("uuid", uuidObservation(variant));
        record.put("metadata", metadata(variant.object));
        record.put("facets", facetRecords);
        return record;
    }

    private static Map<String, Object> fileOrigin(ObjectVariant variant) {
        Map<String, Object> origin = map();
        if (variant.originProvider != null) {
            origin.put("kind", "provider");
            origin.put("provider", variant.originProvider.toMap());
            return origin;
        }
        origin.put("kind", "file");
        origin.put("source_id", variant.source.id());
        origin.put("path", variant.path);
        origin.put("sha256", variant.sha256);
        origin.put("definition_index", variant.definitionIndex);
        origin.put("generated_by", variant.generatedBy == null ? null : variant.generatedBy.toMap());
        return origin;
    }

    private static Map<String, Object> uuidObservation(ObjectVariant variant) {
        Map<String, Object> uuid = map();
        if (variant.sourceUuid != null) {
            uuid.put("source_presence", "present");
            uuid.put("source_value", variant.sourceUuid);
            uuid.put("runtime_kind", "explicit");
            uuid.put("durable_value", variant.sourceUuid);
        } else if (variant.object instanceof AxoObjectUnloaded) {
            uuid.put("source_presence", "absent");
            uuid.put("source_value", null);
            uuid.put("runtime_kind", "sentinel");
            uuid.put("durable_value", "unloaded");
        } else if (variant.object instanceof AxoObjectComment || variant.object instanceof AxoObjectHyperlink) {
            uuid.put("source_presence", "absent");
            uuid.put("source_value", null);
            uuid.put("runtime_kind", "unavailable");
            uuid.put("durable_value", null);
        } else {
            uuid.put("source_presence", "absent");
            uuid.put("source_value", null);
            uuid.put("runtime_kind", "generated-nondeterministic");
            uuid.put("durable_value", null);
        }
        return uuid;
    }

    private static Map<String, Object> metadata(AxoObjectAbstract object) {
        Map<String, Object> metadata = map();
        metadata.put("description", object.sDescription);
        metadata.put("author", object.sAuthor);
        metadata.put("license", object.sLicense);
        metadata.put("help_patch", object instanceof AxoObject normal ? normal.helpPatch : null);
        return metadata;
    }

    private Map<String, Object> facets(ObjectVariant variant) {
        AxoObjectAbstract object = variant.object;
        Map<String, Object> facets = map();
        if (!(object instanceof AxoObject normal)) {
            facets.put("inlets", List.of());
            facets.put("outlets", List.of());
            facets.put("parameters", List.of());
            facets.put("attributes", List.of());
            facets.put("displays", List.of());
            facets.put("modulators", List.of());
            facets.put("includes", List.of());
            facets.put("dependencies", List.of());
            facets.put("file_dependencies", List.of());
            facets.put("code_sections", emptyCodeSections());
            return facets;
        }
        facets.put("inlets", inletFacets(variant, normal.inlets));
        facets.put("outlets", outletFacets(variant, normal.outlets));
        facets.put("parameters", parameterFacets(variant, normal.params));
        facets.put("attributes", attributeFacets(variant, normal.attributes));
        facets.put("displays", displayFacets(variant, normal.displays));
        facets.put("modulators", modulatorFacets(normal.getModulators()));
        facets.put("includes", sortedStrings(normal.includes));
        facets.put("dependencies", sortedStrings(normal.depends));
        facets.put("file_dependencies", fileDependencies(normal.filedepends));
        facets.put("code_sections", codeSections(normal));
        return facets;
    }

    private List<Map<String, Object>> inletFacets(ObjectVariant variant, List<Inlet> values) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (values == null) return result;
        for (int index = 0; index < values.size(); index++) {
            Inlet value = values.get(index);
            result.add(facet(variant, "inlet", SUPPORTED_INLET_TYPES, value, index, value.getName(),
                    value.getDescription(), value.noLabel, dataType(value.getDatatype()), null));
        }
        return result;
    }

    private List<Map<String, Object>> outletFacets(ObjectVariant variant, List<Outlet> values) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (values == null) return result;
        for (int index = 0; index < values.size(); index++) {
            Outlet value = values.get(index);
            result.add(facet(variant, "outlet", SUPPORTED_OUTLET_TYPES, value, index, value.getName(),
                    value.getDescription(), value.noLabel, dataType(value.getDatatype()), null));
        }
        return result;
    }

    private List<Map<String, Object>> parameterFacets(ObjectVariant variant, List<Parameter> values) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (values == null) return result;
        for (int index = 0; index < values.size(); index++) {
            Parameter value = values.get(index);
            result.add(facet(variant, "parameter", SUPPORTED_PARAMETER_TYPES, value, index, value.getName(),
                    value.getDescription(), value.noLabel, dataType(value.getDatatype()), null));
        }
        return result;
    }

    private List<Map<String, Object>> attributeFacets(ObjectVariant variant, List<AxoAttribute> values) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (values == null) return result;
        for (int index = 0; index < values.size(); index++) {
            AxoAttribute value = values.get(index);
            result.add(facet(variant, "attribute", SUPPORTED_ATTRIBUTE_TYPES, value, index, value.getName(),
                    value.getDescription(), value.noLabel, null, null));
        }
        return result;
    }

    private List<Map<String, Object>> displayFacets(ObjectVariant variant, List<Display> values) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (values == null) return result;
        for (int index = 0; index < values.size(); index++) {
            Display value = values.get(index);
            result.add(facet(variant, "display", SUPPORTED_DISPLAY_TYPES, value, index, value.getName(),
                    value.getDescription(), value.noLabel, dataType(value.getDatatype()), value.getLength()));
        }
        return result;
    }

    private Map<String, Object> facet(
            ObjectVariant variant, String facetKind, Set<String> supportedTypes, Object subject,
            int index, String name, String description, Boolean noLabel, String dataType, Integer length) {
        String legacyType = subject.getClass().getName();
        Map<String, Object> result = map();
        result.put("index", index);
        result.put("name", name == null ? "" : name);
        result.put("legacy_type", legacyType);
        result.put("description", description);
        result.put("no_label", noLabel);
        result.put("data_type", dataType);
        result.put("length", length);
        if (!supportedTypes.contains(legacyType)) {
            markUnsupportedFacet(variant, "UNSUPPORTED_FACET_TYPE", facetKind, index, legacyType, null,
                    "Legacy facet class is not in the v0 exporter allowlist.");
            result.put("legacy_properties", List.of());
        } else {
            result.put("legacy_properties", legacyProperties(variant, subject, facetKind, index));
        }
        return result;
    }

    private List<Map<String, Object>> legacyProperties(
            ObjectVariant variant, Object subject, String facetKind, int facetIndex) {
        TreeMap<String, Map<String, Object>> properties = new TreeMap<>();
        for (Class<?> type = subject.getClass(); type != null && type != Object.class; type = type.getSuperclass()) {
            Field[] fields = type.getDeclaredFields();
            Arrays.sort(fields, Comparator.comparing(Field::getName));
            for (Field field : fields) {
                if (Modifier.isStatic(field.getModifiers()) || field.isSynthetic()
                        || isStandardFacetProperty(field.getName()) || !isSerialized(field)) {
                    continue;
                }
                String propertyName = serializedName(field, field.getName());
                if (!SUPPORTED_LEGACY_PROPERTIES.contains(propertyName)) {
                    markUnsupportedFacet(variant, "UNSUPPORTED_FACET_PROPERTY", facetKind, facetIndex,
                            subject.getClass().getName(), propertyName,
                            "Serialized facet property is not in the v0 exporter allowlist.");
                    continue;
                }
                try {
                    field.setAccessible(true);
                    Object rawValue = field.get(subject);
                    Map<String, Object> property = property(propertyName, rawValue);
                    if (property != null) {
                        properties.put((String) property.get("name"), property);
                    } else if (rawValue != null) {
                        markUnsupportedFacet(variant, "UNSUPPORTED_FACET_PROPERTY_VALUE", facetKind,
                                facetIndex, subject.getClass().getName(), propertyName,
                                "Serialized facet property value is not representable by the v0 typed allowlist.");
                    }
                } catch (ReflectiveOperationException | RuntimeException exception) {
                    markUnsupportedFacet(variant, "UNREADABLE_FACET_PROPERTY", facetKind, facetIndex,
                            subject.getClass().getName(), propertyName,
                            "Serialized facet property could not be observed through the bridge seam.");
                }
            }
            Method[] methods = type.getDeclaredMethods();
            Arrays.sort(methods, Comparator.comparing(Method::getName));
            for (Method method : methods) {
                if (Modifier.isStatic(method.getModifiers()) || method.isSynthetic()
                        || method.getParameterCount() != 0 || !isSerialized(method)) {
                    continue;
                }
                String propertyName = serializedName(method, method.getName());
                if (!SUPPORTED_LEGACY_PROPERTIES.contains(propertyName)) {
                    markUnsupportedFacet(variant, "UNSUPPORTED_FACET_PROPERTY", facetKind, facetIndex,
                            subject.getClass().getName(), propertyName,
                            "Serialized facet property is not in the v0 exporter allowlist.");
                    continue;
                }
                try {
                    method.setAccessible(true);
                    Object rawValue = method.invoke(subject);
                    Map<String, Object> property = property(propertyName, rawValue);
                    if (property != null) {
                        properties.put((String) property.get("name"), property);
                    } else if (rawValue != null) {
                        markUnsupportedFacet(variant, "UNSUPPORTED_FACET_PROPERTY_VALUE", facetKind,
                                facetIndex, subject.getClass().getName(), propertyName,
                                "Serialized facet property value is not representable by the v0 typed allowlist.");
                    }
                } catch (ReflectiveOperationException | RuntimeException exception) {
                    markUnsupportedFacet(variant, "UNREADABLE_FACET_PROPERTY", facetKind, facetIndex,
                            subject.getClass().getName(), propertyName,
                            "Serialized facet property could not be observed through the bridge seam.");
                }
            }
        }
        return new ArrayList<>(properties.values());
    }

    private void markUnsupportedFacet(
            ObjectVariant variant, String code, String facetKind, int facetIndex,
            String legacyType, String propertyName, String message) {
        variant.partial = true;
        Issue issue = Issue.object("error", "object-export", code, variant, message);
        issue.facts.add(fact("facet_index", "integer", facetIndex));
        issue.facts.add(fact("facet_kind", "string", facetKind));
        issue.facts.add(fact("legacy_type", "string", legacyType));
        if (propertyName != null) {
            issue.facts.add(fact("property_name", "string", propertyName));
        }
        issues.add(issue);
    }

    private static boolean isStandardFacetProperty(String name) {
        return name.equals("name") || name.equals("description") || name.equals("noLabel")
                || name.equals("getName") || name.equals("getDescription") || name.equals("getNoLabel");
    }

    private static boolean isSerialized(AnnotatedElement element) {
        for (Annotation annotation : element.getAnnotations()) {
            if (annotation.annotationType().getPackageName().equals("org.simpleframework.xml")) {
                return true;
            }
        }
        return false;
    }

    private static String serializedName(AnnotatedElement element, String fallback) {
        for (Annotation annotation : element.getAnnotations()) {
            if (!annotation.annotationType().getPackageName().equals("org.simpleframework.xml")) {
                continue;
            }
            try {
                Method name = annotation.annotationType().getMethod("name");
                Object value = name.invoke(annotation);
                if (value instanceof String text && !text.isEmpty()) {
                    return text;
                }
            } catch (ReflectiveOperationException ignored) {
                // Annotation has no serialized name member.
            }
        }
        if (fallback.startsWith("get") && fallback.length() > 3) {
            return Character.toLowerCase(fallback.charAt(3)) + fallback.substring(4);
        }
        return fallback;
    }

    private static Map<String, Object> property(String name, Object value) {
        if (value == null) return null;
        String valueType;
        Object normalized;
        if (value instanceof String text) {
            valueType = "string";
            normalized = text;
        } else if (value instanceof Boolean bool) {
            valueType = "boolean";
            normalized = bool;
        } else if (value instanceof Byte || value instanceof Short || value instanceof Integer || value instanceof Long) {
            valueType = "integer";
            normalized = ((Number) value).longValue();
        } else if (value instanceof Float || value instanceof Double) {
            double number = ((Number) value).doubleValue();
            if (!Double.isFinite(number)) return null;
            valueType = "number";
            normalized = number;
        } else if (value instanceof Enum<?> enumeration) {
            valueType = "string";
            normalized = enumeration.name();
        } else if (value instanceof axoloti.datatypes.Value<?> legacyValue) {
            valueType = value.getClass().getName().contains("Frac32") ? "frac32-raw" : "int32-raw";
            normalized = legacyValue.getRaw();
        } else if (value.getClass().isArray()) {
            List<Object> values = new ArrayList<>();
            for (int index = 0; index < Array.getLength(value); index++) {
                values.add(Array.get(value, index));
            }
            return listProperty(name, values, false);
        } else if (value instanceof Set<?> set) {
            return listProperty(name, new ArrayList<>(set), true);
        } else if (value instanceof List<?> list) {
            return listProperty(name, new ArrayList<>(list), false);
        } else {
            return null;
        }
        Map<String, Object> result = map();
        result.put("name", name);
        result.put("value_type", valueType);
        result.put("value", normalized);
        return result;
    }

    private static Map<String, Object> listProperty(String name, List<?> input, boolean sort) {
        List<Object> values = new ArrayList<>();
        String valueType = input.isEmpty() && (name.equals("MenuEntries") || name.equals("CEntries"))
                ? "string-list"
                : null;
        for (Object item : input) {
            if (item == null && (name.equals("MenuEntries") || name.equals("CEntries"))) {
                if (valueType == null) valueType = "string-list";
                if (!valueType.equals("string-list")) return null;
                values.add("");
            } else if (item instanceof String text) {
                if (valueType == null) valueType = "string-list";
                if (!valueType.equals("string-list")) return null;
                values.add(text);
            } else if (item instanceof Byte || item instanceof Short || item instanceof Integer || item instanceof Long) {
                if (valueType == null) valueType = "integer-list";
                if (!valueType.equals("integer-list")) return null;
                values.add(((Number) item).longValue());
            } else if (item instanceof Float || item instanceof Double) {
                double number = ((Number) item).doubleValue();
                if (!Double.isFinite(number)) return null;
                if (valueType == null) valueType = "number-list";
                if (!valueType.equals("number-list")) return null;
                values.add(number);
            } else {
                return null;
            }
        }
        if (sort) {
            values.sort(Comparator.comparing(Object::toString));
        }
        Map<String, Object> result = map();
        result.put("name", name);
        result.put("value_type", valueType);
        result.put("value", values);
        return result;
    }

    private static List<Map<String, Object>> modulatorFacets(Modulator[] modulators) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (modulators == null) return result;
        for (int index = 0; index < modulators.length; index++) {
            Map<String, Object> value = map();
            value.put("index", index);
            value.put("name", modulators[index].getName());
            result.add(value);
        }
        return result;
    }

    private static List<Map<String, Object>> fileDependencies(List<SDFileReference> values) {
        List<Map<String, Object>> result = new ArrayList<>();
        if (values == null) return result;
        for (int index = 0; index < values.size(); index++) {
            SDFileReference value = values.get(index);
            Map<String, Object> record = map();
            record.put("index", index);
            record.put("local_filename", value.localFilename);
            record.put("target_path", value.targetPath);
            result.add(record);
        }
        return result;
    }

    private static Map<String, Object> codeSections(AxoObject object) {
        Map<String, Object> result = map();
        result.put("declaration", presence(object.sLocalData));
        result.put("init", presence(object.sInitCode));
        result.put("dispose", presence(object.sDisposeCode));
        result.put("control_rate", presence(object.sKRateCode));
        result.put("sample_rate", presence(object.sSRateCode));
        result.put("midi_handler", presence(object.sMidiCode));
        result.put("legacy_midi_cc", presence(object.sMidiCCCode));
        result.put("legacy_midi_note_on", presence(object.sMidiNoteOnCode));
        result.put("legacy_midi_note_off", presence(object.sMidiNoteOffCode));
        result.put("legacy_midi_pitch_bend", presence(object.sMidiPBendCode));
        result.put("legacy_midi_channel_pressure", presence(object.sMidiChannelPressure));
        result.put("legacy_midi_all_notes_off", presence(object.sMidiAllNotesOffCode));
        result.put("legacy_midi_reset_controllers", presence(object.sMidiResetControllersCode));
        return result;
    }

    private static Map<String, Object> emptyCodeSections() {
        AxoObject empty = new AxoObject();
        return codeSections(empty);
    }

    private static String presence(String value) {
        if (value == null) return "absent";
        return value.isEmpty() ? "empty" : "nonempty";
    }

    private static String dataType(Object value) {
        return value == null ? null : value.getClass().getName();
    }

    private static List<String> sortedStrings(Set<String> values) {
        if (values == null) return List.of();
        return values.stream().sorted().toList();
    }

    private List<GraphInput> scanGraphs() {
        List<GraphInput> result = new ArrayList<>();
        for (ResolvedInventoryExporter.Source source : config.sources()) {
            try (var paths = Files.walk(source.root())) {
                paths.filter(Files::isRegularFile)
                        .filter(path -> path.getFileName().toString().endsWith(".axs")
                                || path.getFileName().toString().endsWith(".axp"))
                        .forEach(path -> result.add(new GraphInput(source, portable(source, path), path)));
            } catch (IOException exception) {
                issues.add(Issue.global("error", "graph-load", "GRAPH_SCAN_FAILED", source, null,
                        "Source graph candidates could not be enumerated."));
            }
        }
        result.sort(Comparator.comparing((GraphInput input) -> input.source.id()).thenComparing(input -> input.path));
        return result;
    }

    private static Map<String, Object> failedGraphRecord(int index, GraphInput input) {
        Map<String, Object> record = map();
        record.put("schema_version", "legacy-resolved-graph-v0");
        record.put("graph_index", index);
        Map<String, Object> source = map();
        source.put("source_id", input.source.id());
        source.put("path", input.path);
        source.put("sha256", sha256(input.absolutePath));
        source.put("file_type", input.path.endsWith(".axs") ? "axs" : "axp");
        record.put("source", source);
        record.put("export_status", "failed");
        record.put("instances", List.of());
        record.put("nets", List.of());
        return record;
    }

    private static String legacyKind(AxoObjectAbstract object) {
        if (object instanceof AxoObjectComment) return "comment";
        if (object instanceof AxoObjectHyperlink) return "hyperlink";
        if (object instanceof AxoObjectUnloaded) return "subpatch_catalog_placeholder";
        if (object instanceof AxoObject) return "native_definition";
        return "unsupported";
    }

    private static int identityIndex(List<AxoObjectAbstract> values, AxoObjectAbstract wanted) {
        for (int index = 0; index < values.size(); index++) {
            if (values.get(index) == wanted) return index;
        }
        return -1;
    }

    private static String actualKey(String path, String id, String className) {
        String normalized = path == null ? "" : Path.of(path).toAbsolutePath().normalize().toString();
        return normalized + "\u0000" + id + "\u0000" + className;
    }

    private static String shortId(String id) {
        int slash = id.lastIndexOf('/');
        return slash < 0 ? id : id.substring(slash + 1);
    }

    private static String portable(ResolvedInventoryExporter.Source source, Path path) {
        Path absolute = path.toAbsolutePath().normalize();
        if (!absolute.startsWith(source.root())) {
            throw new IllegalArgumentException("Path escaped source root " + source.id());
        }
        String value = source.root().relativize(absolute).toString().replace(File.separatorChar, '/');
        if (value.isEmpty() || value.startsWith("/") || value.equals("..") || value.startsWith("../")) {
            throw new IllegalArgumentException("Non-portable source-relative path");
        }
        return value;
    }

    private static String sha256(Path path) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (var input = Files.newInputStream(path)) {
                byte[] buffer = new byte[65536];
                int read;
                while ((read = input.read(buffer)) >= 0) {
                    digest.update(buffer, 0, read);
                }
            }
            return java.util.HexFormat.of().formatHex(digest.digest());
        } catch (Exception exception) {
            throw new IllegalStateException("Unable to hash source file", exception);
        }
    }

    private static String sha256(byte[] bytes) {
        try {
            return java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
        } catch (Exception exception) {
            throw new IllegalStateException("Unable to hash bytes", exception);
        }
    }

    private static Map<String, Object> fact(String name, String type, Object value) {
        Map<String, Object> fact = map();
        fact.put("name", name);
        fact.put("value_type", type);
        fact.put("value", value);
        return fact;
    }

    @SuppressWarnings("unchecked")
    private static int compareIssueRecords(Map<String, Object> left, Map<String, Object> right) {
        Map<String, Object> leftLocation = (Map<String, Object>) left.get("location");
        Map<String, Object> rightLocation = (Map<String, Object>) right.get("location");
        for (String field : List.of(
                "source_id", "path", "variant_index", "graph_index", "instance_index",
                "net_index", "endpoint_role", "endpoint_index")) {
            int compared = compareNullableIssueValue(leftLocation.get(field), rightLocation.get(field));
            if (compared != 0) return compared;
        }
        int compared = compareCodePoints((String) left.get("stage"), (String) right.get("stage"));
        if (compared != 0) return compared;
        compared = compareCodePoints((String) left.get("code"), (String) right.get("code"));
        if (compared != 0) return compared;
        compared = compareIntegerLists(
                (List<Integer>) left.get("candidate_variant_indexes"),
                (List<Integer>) right.get("candidate_variant_indexes"));
        if (compared != 0) return compared;
        compared = compareCodePoints(
                StableJson.stringify(left.get("facts")), StableJson.stringify(right.get("facts")));
        if (compared != 0) return compared;
        return compareCodePoints((String) left.get("message"), (String) right.get("message"));
    }

    private static int compareNullableIssueValue(Object left, Object right) {
        if (left == right) return 0;
        if (left == null) return -1;
        if (right == null) return 1;
        if (left instanceof Number leftNumber && right instanceof Number rightNumber) {
            return Long.compare(leftNumber.longValue(), rightNumber.longValue());
        }
        return compareCodePoints(left.toString(), right.toString());
    }

    private static int compareIntegerLists(List<Integer> left, List<Integer> right) {
        int count = Math.min(left.size(), right.size());
        for (int index = 0; index < count; index++) {
            int compared = Integer.compare(left.get(index), right.get(index));
            if (compared != 0) return compared;
        }
        return Integer.compare(left.size(), right.size());
    }

    private static int compareCodePoints(String left, String right) {
        int leftOffset = 0;
        int rightOffset = 0;
        while (leftOffset < left.length() && rightOffset < right.length()) {
            int leftCodePoint = left.codePointAt(leftOffset);
            int rightCodePoint = right.codePointAt(rightOffset);
            int compared = Integer.compare(leftCodePoint, rightCodePoint);
            if (compared != 0) return compared;
            leftOffset += Character.charCount(leftCodePoint);
            rightOffset += Character.charCount(rightCodePoint);
        }
        if (leftOffset < left.length()) return 1;
        if (rightOffset < right.length()) return -1;
        return 0;
    }

    private static Map<String, Object> map() {
        return new LinkedHashMap<>();
    }

    private static final class ObjectVariant {
        final int variantIndex;
        final ResolvedInventoryExporter.Source source;
        final String path;
        final Path absolutePath;
        final String sha256;
        final int definitionIndex;
        final AxoObjectAbstract object;
        final String sourceUuid;
        final String legacyId;
        final String shortId;
        final String legacyKind;
        final ProviderRef originProvider;
        AxoObjectAbstract actual;
        Integer legacyObjectListIndex;
        ProviderRef generatedBy;
        boolean partial;

        private ObjectVariant(
                int variantIndex, ResolvedInventoryExporter.Source source, String path, Path absolutePath,
                String sha256, int definitionIndex, AxoObjectAbstract object, String sourceUuid,
                String legacyId, String shortId, String legacyKind, ProviderRef originProvider) {
            this.variantIndex = variantIndex;
            this.source = source;
            this.path = path;
            this.absolutePath = absolutePath.toAbsolutePath().normalize();
            this.sha256 = sha256;
            this.definitionIndex = definitionIndex;
            this.object = object;
            this.sourceUuid = sourceUuid;
            this.legacyId = legacyId;
            this.shortId = shortId;
            this.legacyKind = legacyKind;
            this.originProvider = originProvider;
        }

        static ObjectVariant file(
                int variantIndex, ResolvedInventoryExporter.Source source, String path, Path absolutePath,
                String sha256, int definitionIndex, AxoObjectAbstract object, String sourceUuid,
                String legacyId, String shortId, String legacyKind) {
            return new ObjectVariant(variantIndex, source, path, absolutePath, sha256, definitionIndex,
                    object, sourceUuid, legacyId, shortId, legacyKind, null);
        }

        static ObjectVariant provider(
                int variantIndex, ResolvedInventoryExporter.Source factory, ProviderRef provider,
                String outputPath, Path absolutePath,
                int definitionIndex, AxoObjectAbstract object, String legacyId) {
            return new ObjectVariant(
                    variantIndex, factory, outputPath, absolutePath, provider.sha256,
                    definitionIndex, object, null, legacyId, shortId(legacyId),
                    object instanceof AxoObject ? "native_definition" : legacyKind(object), provider);
        }
    }

    private record SimulatedSurvivor(int variantIndex, String runtimeUuid, String path) {
    }

    private record GraphInput(ResolvedInventoryExporter.Source source, String path, Path absolutePath) {
    }

    private record ProviderRef(
            String sourceId, String path, String sha256, String providerClass, int emissionIndex) {
        Map<String, Object> toMap() {
            Map<String, Object> value = map();
            value.put("source_id", sourceId);
            value.put("path", path);
            value.put("sha256", sha256);
            value.put("provider_class", providerClass);
            value.put("emission_index", emissionIndex);
            return value;
        }
    }

    private static final class Issue {
        static final Comparator<Issue> ORDER = Comparator
                .comparing((Issue value) -> nullToEmpty(value.sourceId))
                .thenComparing(value -> nullToEmpty(value.path))
                .thenComparingInt(value -> nullToMinusOne(value.variantIndex))
                .thenComparingInt(value -> nullToMinusOne(value.graphIndex))
                .thenComparingInt(value -> nullToMinusOne(value.instanceIndex))
                .thenComparingInt(value -> nullToMinusOne(value.netIndex))
                .thenComparing(value -> nullToEmpty(value.endpointRole))
                .thenComparingInt(value -> nullToMinusOne(value.endpointIndex))
                .thenComparing(value -> value.stage)
                .thenComparing(value -> value.code);

        final String severity;
        final String stage;
        final String code;
        final String kind;
        final String sourceId;
        final String path;
        final Integer variantIndex;
        final Integer graphIndex;
        final Integer instanceIndex;
        final Integer netIndex;
        final String endpointRole;
        final Integer endpointIndex;
        final String message;
        final boolean processingContinued;
        final List<Map<String, Object>> facts = new ArrayList<>();
        final List<Integer> candidateVariantIndexes = new ArrayList<>();

        private Issue(
                String severity, String stage, String code, String kind, String sourceId, String path,
                Integer variantIndex, Integer graphIndex, Integer instanceIndex, Integer netIndex,
                String endpointRole, Integer endpointIndex, String message, boolean processingContinued) {
            this.severity = severity;
            this.stage = stage;
            this.code = code;
            this.kind = kind;
            this.sourceId = sourceId;
            this.path = path;
            this.variantIndex = variantIndex;
            this.graphIndex = graphIndex;
            this.instanceIndex = instanceIndex;
            this.netIndex = netIndex;
            this.endpointRole = endpointRole;
            this.endpointIndex = endpointIndex;
            this.message = message;
            this.processingContinued = processingContinued;
        }

        static Issue global(
                String severity, String stage, String code, ResolvedInventoryExporter.Source source,
                String path, String message) {
            return new Issue(severity, stage, code, "global", source == null ? null : source.id(), path,
                    null, null, null, null, null, null, message, true);
        }

        static Issue object(String severity, String stage, String code, ObjectVariant variant, String message) {
            return new Issue(severity, stage, code, "object", variant.source.id(), variant.path,
                    variant.variantIndex, null, null, null, null, null, message, true);
        }

        static Issue objectGroup(
                String severity, String stage, String code, ObjectVariant variant, String message,
                List<Integer> candidates) {
            Issue issue = object(severity, stage, code, variant, message);
            issue.candidateVariantIndexes.addAll(new LinkedHashSet<>(candidates));
            return issue;
        }

        static Issue graph(
                String severity, String stage, String code, ResolvedInventoryExporter.Source source,
                String path, int graphIndex, String message) {
            return new Issue(severity, stage, code, "graph", source.id(), path,
                    null, graphIndex, null, null, null, null, message, false);
        }

        Map<String, Object> toMap(int issueIndex) {
            Map<String, Object> record = map();
            record.put("schema_version", "legacy-resolved-issue-v0");
            record.put("issue_index", issueIndex);
            record.put("severity", severity);
            record.put("stage", stage);
            record.put("code", code);
            Map<String, Object> location = map();
            location.put("kind", kind);
            location.put("source_id", sourceId);
            location.put("path", path);
            location.put("variant_index", variantIndex);
            location.put("graph_index", graphIndex);
            location.put("instance_index", instanceIndex);
            location.put("net_index", netIndex);
            location.put("endpoint_role", endpointRole);
            location.put("endpoint_index", endpointIndex);
            record.put("location", location);
            record.put("message", message);
            record.put("processing_continued", processingContinued);
            facts.sort(Comparator
                    .comparing((Map<String, Object> value) -> (String) value.get("name"),
                            LegacyResolvedExport::compareCodePoints)
                    .thenComparing(value -> (String) value.get("value_type"),
                            LegacyResolvedExport::compareCodePoints)
                    .thenComparing(StableJson::stringify, LegacyResolvedExport::compareCodePoints));
            record.put("facts", facts);
            candidateVariantIndexes.sort(Integer::compareTo);
            record.put("candidate_variant_indexes", candidateVariantIndexes);
            return record;
        }

        private static String nullToEmpty(String value) {
            return value == null ? "" : value;
        }

        private static int nullToMinusOne(Integer value) {
            return value == null ? -1 : value;
        }
    }
}
