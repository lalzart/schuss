package org.schuss.legacy.ksoloti;

import axoloti.Modulation;
import axoloti.Net;
import axoloti.Patch;
import axoloti.Preset;
import axoloti.SchussPatchAccess;
import axoloti.attribute.AttributeInstance;
import axoloti.attribute.AttributeInstanceInt32;
import axoloti.attribute.AttributeInstanceSpinner;
import axoloti.attribute.AttributeInstanceString;
import axoloti.attribute.AttributeInstanceWavefile;
import axoloti.datatypes.DataType;
import axoloti.datatypes.Value;
import axoloti.datatypes.ValueFrac32;
import axoloti.datatypes.ValueInt32;
import axoloti.inlets.InletInstance;
import axoloti.iolet.IoletAbstract;
import axoloti.object.AxoObjectAbstract;
import axoloti.object.AxoObjectFromPatch;
import axoloti.object.AxoObjectInstance;
import axoloti.object.AxoObjectInstanceAbstract;
import axoloti.object.AxoObjectInstanceComment;
import axoloti.object.AxoObjectInstanceHyperlink;
import axoloti.object.AxoObjectInstancePatcher;
import axoloti.object.AxoObjectInstancePatcherObject;
import axoloti.object.AxoObjectInstanceZombie;
import axoloti.outlets.OutletInstance;
import axoloti.parameters.ParameterInstance;
import axoloti.parameters.ParameterInstanceFrac32;
import axoloti.parameters.SchussParameterAccess;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamConstants;
import javax.xml.stream.XMLStreamReader;
import org.simpleframework.xml.Serializer;
import org.simpleframework.xml.core.Persister;
import org.simpleframework.xml.stream.Format;

/**
 * Exports serialized and post-resolution legacy graph state without invoking a
 * compiler, code generator, device operation, or preference mutation.
 */
final class GraphRecordExporter {
    interface CatalogLookup {
        List<Integer> candidatesByUuid(String uuid);

        List<Integer> candidatesByName(String legacyId);

        List<Integer> candidatesByFile(Path absoluteAxo);

        Integer variantForActual(AxoObjectAbstract actual);
    }

    record Result(List<Map<String, Object>> graphs, List<Map<String, Object>> issues) {
    }

    private static final Set<String> INSTANCE_ELEMENTS = Set.of(
            "obj", "patcher", "patchobj", "comment", "hyperlink", "zombie");
    private static final Set<String> PATCH_METADATA_ELEMENTS = Set.of(
            "nets", "settings", "notes", "windowPos", "helpPatch");

    private final List<ResolvedInventoryExporter.Source> sources;
    private final CatalogLookup catalog;
    private final Serializer serializer = new Persister(new Format(2));
    private final List<Map<String, Object>> issues = new ArrayList<>();
    private int currentGraphRedactions;

    private GraphRecordExporter(
            List<ResolvedInventoryExporter.Source> sources,
            CatalogLookup catalog) {
        this.sources = List.copyOf(sources);
        this.catalog = catalog;
    }

    static Result export(
            List<ResolvedInventoryExporter.Source> sources,
            CatalogLookup catalog) {
        if (sources == null || catalog == null) {
            throw new IllegalArgumentException("sources and catalog lookup are required");
        }
        return new GraphRecordExporter(sources, catalog).run();
    }

    private Result run() {
        List<GraphInput> inputs = scanGraphs();
        List<Map<String, Object>> graphs = new ArrayList<>();
        for (int graphIndex = 0; graphIndex < inputs.size(); graphIndex++) {
            graphs.add(exportGraph(graphIndex, inputs.get(graphIndex)));
        }
        return new Result(List.copyOf(graphs), List.copyOf(issues));
    }

    private List<GraphInput> scanGraphs() {
        List<GraphInput> result = new ArrayList<>();
        for (ResolvedInventoryExporter.Source source : sources) {
            try (var paths = Files.walk(source.root())) {
                paths.filter(path -> Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS))
                        .filter(GraphRecordExporter::isGraphFile)
                        .forEach(path -> result.add(new GraphInput(
                                source,
                                portable(source, path),
                                path.toAbsolutePath().normalize())));
            } catch (IOException | RuntimeException exception) {
                issues.add(issueMap(
                        "error", "graph-load", "GRAPH_SCAN_FAILED", "global",
                        source.id(), null, null, null, null, null, null,
                        "Source graph candidates could not be enumerated.", true, List.of()));
            }
        }
        result.sort(Comparator
                .comparing((GraphInput input) -> input.source().id())
                .thenComparing(GraphInput::path));
        return result;
    }

    private Map<String, Object> exportGraph(int graphIndex, GraphInput input) {
        currentGraphRedactions = 0;
        String hash;
        try {
            hash = sha256(input.absolutePath());
        } catch (RuntimeException exception) {
            throw new IllegalStateException(
                    "Graph source bytes could not be hashed: "
                            + input.source().id() + "/" + input.path(),
                    exception);
        }

        GraphState state = new GraphState(input, graphIndex, hash);
        List<ElementSlot> slots;
        try {
            slots = scanTopLevelElements(input.absolutePath());
        } catch (Exception exception) {
            state.failed = true;
            issues.add(graphIssue(
                    "error", "graph-load", "GRAPH_XML_SCAN_FAILED", input, graphIndex,
                    "Graph XML structure could not be inspected safely.", false));
            emitRedactionIssue(state);
            return failedGraphRecord(graphIndex, input, hash);
        }

        Patch patch;
        try {
            patch = serializer.read(Patch.class, input.absolutePath().toFile());
        } catch (Exception strictFailure) {
            try {
                patch = serializer.read(Patch.class, input.absolutePath().toFile(), false);
                state.partial = true;
                issues.add(graphIssue(
                        "warning", "graph-load", "GRAPH_PARSE_RELAXED", input, graphIndex,
                        "Strict graph parsing failed; relaxed legacy parsing succeeded.", true));
            } catch (Exception relaxedFailure) {
                state.failed = true;
                issues.add(graphIssue(
                        "error", "graph-load", "GRAPH_PARSE_FAILED", input, graphIndex,
                        "Strict and relaxed legacy graph parsing both failed.", false));
                emitRedactionIssue(state);
                return failedGraphRecord(graphIndex, input, hash);
            }
        }

        patch.setFileNamePath(input.absolutePath().toString());
        List<PreInstance> instances = alignAndSnapshotInstances(patch, slots, state);
        List<PreNet> nets = snapshotNets(patch, state);

        boolean postSucceeded = true;
        try {
            patch.PostContructor();
        } catch (RuntimeException | LinkageError | StackOverflowError exception) {
            postSucceeded = false;
            state.failed = true;
            issues.add(graphIssue(
                    "error", "graph-resolve", "GRAPH_POST_CONSTRUCTION_FAILED", input, graphIndex,
                    "Legacy graph post-construction failed; serialized state was retained.", false));
        }

        List<AxoObjectInstanceAbstract> postInstances = postSucceeded
                ? new ArrayList<>(SchussPatchAccess.objectInstances(patch))
                : List.of();
        if (postSucceeded) {
            correlateInstances(instances, postInstances, state);
        }

        List<Map<String, Object>> instanceRecords = new ArrayList<>();
        for (PreInstance instance : instances) {
            instanceRecords.add(instanceRecord(instance, postSucceeded, state));
        }

        List<Map<String, Object>> netRecords = new ArrayList<>();
        for (PreNet net : nets) {
            netRecords.add(netRecord(
                    net, patch, instances, postInstances, postSucceeded, state));
        }

        Map<String, Object> record = map();
        emitRedactionIssue(state);
        record.put("schema_version", "legacy-resolved-graph-v0");
        record.put("graph_index", graphIndex);
        record.put("source", sourceMap(input, hash));
        record.put("export_status", state.failed ? "failed" : state.partial ? "partial" : "complete");
        record.put("instances", instanceRecords);
        record.put("nets", netRecords);
        return record;
    }

    private void emitRedactionIssue(GraphState state) {
        if (currentGraphRedactions == 0) {
            return;
        }
        state.partial = true;
        issues.add(graphIssue(
                "warning", "graph-load", "NONPORTABLE_GRAPH_VALUE_REDACTED",
                state.input, state.graphIndex,
                "One or more absolute serialized values were redacted from durable graph evidence.",
                true));
        currentGraphRedactions = 0;
    }

    private List<PreInstance> alignAndSnapshotInstances(
            Patch patch,
            List<ElementSlot> slots,
            GraphState state) {
        List<AxoObjectInstanceAbstract> loaded = new ArrayList<>(SchussPatchAccess.objectInstances(patch));
        List<PreInstance> result = new ArrayList<>();
        int loadedIndex = 0;
        for (ElementSlot slot : slots) {
            int serializedIndex = result.size();
            if (!INSTANCE_ELEMENTS.contains(slot.elementName())) {
                state.partial = true;
                PreInstance unsupported = PreInstance.unsupported(serializedIndex, slot, this);
                result.add(unsupported);
                issues.add(instanceIssue(
                        "warning", "graph-load", "UNSUPPORTED_GRAPH_ELEMENT", state,
                        serializedIndex,
                        "A direct graph element is not represented by the locked legacy instance union.",
                        true, List.of()));
                continue;
            }
            if (loadedIndex >= loaded.size()) {
                state.partial = true;
                result.add(PreInstance.unsupported(serializedIndex, slot, this));
                issues.add(instanceIssue(
                        "error", "graph-load", "SERIALIZED_INSTANCE_NOT_LOADED", state,
                        serializedIndex,
                        "A serialized instance element was not retained by the legacy deserializer.",
                        true, List.of()));
                continue;
            }
            AxoObjectInstanceAbstract object = loaded.get(loadedIndex++);
            String actualKind = instanceKind(object);
            if (!actualKind.equals(slot.elementName())) {
                state.partial = true;
                issues.add(instanceIssue(
                        "error", "graph-load", "INSTANCE_ELEMENT_ORDER_MISMATCH", state,
                        serializedIndex,
                        "Serialized instance order did not match the legacy deserializer collection.",
                        true, List.of()));
            }
            result.add(snapshotInstance(serializedIndex, actualKind, object, slot, state));
        }
        while (loadedIndex < loaded.size()) {
            int serializedIndex = result.size();
            AxoObjectInstanceAbstract object = loaded.get(loadedIndex++);
            state.partial = true;
            result.add(snapshotInstance(serializedIndex, instanceKind(object), object, null, state));
            issues.add(instanceIssue(
                    "error", "graph-load", "LOADED_INSTANCE_WITHOUT_SERIALIZED_SLOT", state,
                    serializedIndex,
                    "The legacy deserializer produced an instance without a matching serialized slot.",
                    true, List.of()));
        }
        return result;
    }

    private PreInstance snapshotInstance(
            int serializedIndex,
            String kind,
            AxoObjectInstanceAbstract object,
            ElementSlot slot,
            GraphState state) {
        List<ParameterSnapshot> parameters = snapshotParameters(
                safeList(object.getParameterInstances()), state, serializedIndex);
        List<AttributeSnapshot> attributes = snapshotAttributes(
                safeList(object.getAttributeInstances()), state, serializedIndex);
        return new PreInstance(
                serializedIndex,
                kind,
                object,
                object.getInstanceName() == null && slot != null
                        ? sanitize(slot.instanceName())
                        : sanitize(object.getInstanceName()),
                sanitize(object.typeName),
                sanitize(object.typeUUID),
                sanitize(object.typeSHA),
                parameters,
                attributes);
    }

    private List<PreNet> snapshotNets(Patch patch, GraphState state) {
        List<PreNet> result = new ArrayList<>();
        List<Net> loadedNets = patch.nets == null ? List.of() : new ArrayList<>(patch.nets);
        for (int index = 0; index < loadedNets.size(); index++) {
            Net net = loadedNets.get(index);
            try {
                List<EndpointSnapshot> sources = new ArrayList<>();
                List<OutletInstance> sourceValues = safeList(net.GetSource());
                for (int endpointIndex = 0; endpointIndex < sourceValues.size(); endpointIndex++) {
                    OutletInstance<?> endpoint = sourceValues.get(endpointIndex);
                    sources.add(new EndpointSnapshot(
                            endpointIndex,
                            sanitize(serializedObjectName(endpoint)),
                            sanitize(serializedOutletName(endpoint))));
                }
                List<EndpointSnapshot> destinations = new ArrayList<>();
                List<InletInstance> destinationValues = safeList(net.GetDest());
                for (int endpointIndex = 0; endpointIndex < destinationValues.size(); endpointIndex++) {
                    InletInstance<?> endpoint = destinationValues.get(endpointIndex);
                    destinations.add(new EndpointSnapshot(
                            endpointIndex,
                            sanitize(serializedObjectName(endpoint)),
                            sanitize(serializedInletName(endpoint))));
                }
                result.add(new PreNet(index, net, sources, destinations, false));
            } catch (RuntimeException exception) {
                state.partial = true;
                result.add(new PreNet(index, net, List.of(), List.of(), true));
                issues.add(netIssue(
                        "error", "graph-load", "NET_SNAPSHOT_FAILED", state, index,
                        "A serialized net could not be snapshotted safely.", true));
            }
        }
        return result;
    }

    private static String serializedObjectName(IoletAbstract endpoint) {
        if (endpoint.objname != null) {
            return endpoint.objname;
        }
        if (endpoint.name == null) {
            return null;
        }
        int separator = endpoint.name.lastIndexOf(' ');
        return separator < 0 ? null : endpoint.name.substring(0, separator);
    }

    private static String serializedOutletName(OutletInstance<?> endpoint) {
        if (endpoint.outletname != null) {
            return endpoint.outletname;
        }
        return serializedPortName(endpoint.name);
    }

    private static String serializedInletName(InletInstance<?> endpoint) {
        if (endpoint.inletname != null) {
            return endpoint.inletname;
        }
        return serializedPortName(endpoint.name);
    }

    private static String serializedPortName(String combinedName) {
        if (combinedName == null) {
            return null;
        }
        int separator = combinedName.lastIndexOf(' ');
        return separator < 0 ? combinedName : combinedName.substring(separator + 1);
    }

    private void correlateInstances(
            List<PreInstance> preInstances,
            List<AxoObjectInstanceAbstract> postInstances,
            GraphState state) {
        IdentityHashMap<AxoObjectInstanceAbstract, Integer> postIndexes = new IdentityHashMap<>();
        for (int index = 0; index < postInstances.size(); index++) {
            postIndexes.put(postInstances.get(index), index);
        }

        Set<AxoObjectInstanceAbstract> originalObjects =
                java.util.Collections.newSetFromMap(new IdentityHashMap<>());
        List<PreInstance> removed = new ArrayList<>();
        for (PreInstance pre : preInstances) {
            if (pre.original == null) {
                continue;
            }
            originalObjects.add(pre.original);
            Integer postIndex = postIndexes.get(pre.original);
            if (postIndex != null) {
                pre.post = pre.original;
                pre.postIndex = postIndex;
            } else {
                removed.add(pre);
            }
        }

        List<AxoObjectInstanceAbstract> replacements = new ArrayList<>();
        for (AxoObjectInstanceAbstract post : postInstances) {
            if (!originalObjects.contains(post)) {
                replacements.add(post);
            }
        }

        Set<PreInstance> matchedPre = java.util.Collections.newSetFromMap(new IdentityHashMap<>());
        Set<AxoObjectInstanceAbstract> matchedPost =
                java.util.Collections.newSetFromMap(new IdentityHashMap<>());

        for (AxoObjectInstanceAbstract replacement : replacements) {
            if (!(replacement instanceof AxoObjectInstanceZombie)) {
                continue;
            }
            PreInstance pre = firstReplacementMatch(
                    removed, matchedPre, replacement, true);
            if (pre != null) {
                bindReplacement(pre, replacement, postIndexes, matchedPre, matchedPost);
                pre.zombieKind = pre.original instanceof AxoObjectInstanceZombie
                        ? "serialized-hard"
                        : "created-by-resolution";
            }
        }

        for (AxoObjectInstanceAbstract replacement : replacements) {
            if (replacement instanceof AxoObjectInstanceZombie || matchedPost.contains(replacement)) {
                continue;
            }
            PreInstance pre = firstReplacementMatch(
                    removed, matchedPre, replacement, false);
            if (pre != null) {
                bindReplacement(pre, replacement, postIndexes, matchedPre, matchedPost);
            }
        }

        if (matchedPre.size() != removed.size() || matchedPost.size() != replacements.size()) {
            state.partial = true;
            issues.add(graphIssue(
                    "error", "graph-resolve", "POST_INSTANCE_CORRELATION_MISMATCH",
                    state.input, state.graphIndex,
                    "Removed serialized instances and added post-resolution instances did not pair one-to-one.",
                    true));
        }
    }

    private PreInstance firstReplacementMatch(
            List<PreInstance> removed,
            Set<PreInstance> matched,
            AxoObjectInstanceAbstract replacement,
            boolean zombie) {
        String replacementInstanceName = sanitize(replacement.getInstanceName());
        String replacementComponentName = sanitize(replacement.getName());
        for (PreInstance pre : removed) {
            if (matched.contains(pre) || expectsZombie(pre) != zombie) {
                continue;
            }
            if (equalNullable(pre.instanceName, replacementInstanceName)
                    || equalNullable(pre.instanceName, replacementComponentName)) {
                return pre;
            }
        }
        for (PreInstance pre : removed) {
            if (!matched.contains(pre) && expectsZombie(pre) == zombie) {
                return pre;
            }
        }
        return null;
    }

    private static boolean expectsZombie(PreInstance pre) {
        return pre.original instanceof AxoObjectInstanceZombie || pre.original.getType() == null;
    }

    private static void bindReplacement(
            PreInstance pre,
            AxoObjectInstanceAbstract replacement,
            IdentityHashMap<AxoObjectInstanceAbstract, Integer> postIndexes,
            Set<PreInstance> matchedPre,
            Set<AxoObjectInstanceAbstract> matchedPost) {
        pre.post = replacement;
        pre.postIndex = postIndexes.get(replacement);
        matchedPre.add(pre);
        matchedPost.add(replacement);
    }

    private Map<String, Object> instanceRecord(
            PreInstance pre,
            boolean postSucceeded,
            GraphState state) {
        Resolution resolution = resolution(pre, postSucceeded, state);
        Map<String, Object> record = map();
        record.put("serialized_index", pre.serializedIndex);
        record.put("post_resolution_index", pre.postIndex);
        record.put("legacy_element_kind", pre.kind);
        String instanceName = pre.instanceName;
        if (instanceName == null && pre.post != null) {
            instanceName = sanitize(pre.post.getInstanceName());
        }
        record.put("instance_name", instanceName);
        Map<String, Object> requested = map();
        requested.put("name", pre.requestedName);
        requested.put("uuid", pre.requestedUuid);
        requested.put("sha", pre.requestedSha);
        record.put("requested_type", requested);
        record.put("resolution", resolution.toMap());
        record.put("zombie_kind", pre.zombieKind);
        record.put("parameter_values", parameterRecords(pre, postSucceeded, state));
        record.put("attribute_values", attributeRecords(pre, postSucceeded, state));
        return record;
    }

    private Resolution resolution(PreInstance pre, boolean postSucceeded, GraphState state) {
        if (pre.kind.equals("unsupported") || pre.original == null) {
            return Resolution.empty("unsupported", "none");
        }
        if (!postSucceeded) {
            return Resolution.empty("unresolved", "none");
        }

        AxoObjectAbstract actual = pre.post != null
                        && !(pre.post instanceof AxoObjectInstanceZombie)
                ? pre.post.getType()
                : pre.original.getType();
        ResolutionAttempt attempt = resolutionAttempt(pre, actual, state);
        if (!pre.zombieKind.equals("none")) {
            state.partial = true;
            String code = pre.zombieKind.equals("serialized-hard")
                    ? "SERIALIZED_HARD_ZOMBIE"
                    : "INSTANCE_BECAME_ZOMBIE";
            issues.add(instanceIssue(
                    "warning", "graph-resolve", code, state, pre.serializedIndex,
                    pre.zombieKind.equals("serialized-hard")
                            ? "A serialized hard zombie remained non-resolvable by design."
                            : "Legacy post-construction replaced an unresolved instance with a zombie.",
                    true, attempt.candidateIndexes));
            return new Resolution("zombie", attempt.method, attempt.candidates,
                    pre.zombieKind.equals("serialized-hard") ? attempt.selected : null);
        }

        if (pre.kind.equals("comment") || pre.kind.equals("hyperlink")) {
            return Resolution.empty("not_applicable", "none");
        }

        if (actual == null || attempt.selected == null) {
            state.partial = true;
            issues.add(instanceIssue(
                    "error", "graph-resolve", "INSTANCE_RESOLUTION_UNPROVEN", state,
                    pre.serializedIndex,
                    "Legacy instance resolution did not yield a traceable selected target.",
                    true, attempt.candidateIndexes));
            return new Resolution("unresolved", attempt.method, attempt.candidates, null);
        }

        boolean ambiguous = pre.original.isTypeWasAmbiguous() || attempt.candidates.size() > 1;
        if (ambiguous) {
            state.partial = true;
            issues.add(instanceIssue(
                    "warning", "graph-resolve", "AMBIGUOUS_INSTANCE_RESOLUTION", state,
                    pre.serializedIndex,
                    "Multiple ordered targets were eligible; the legacy-selected target was retained explicitly.",
                    true, attempt.candidateIndexes));
        }
        return new Resolution(
                ambiguous ? "ambiguous" : "resolved",
                attempt.method,
                attempt.candidates,
                attempt.selected);
    }

    private ResolutionAttempt resolutionAttempt(
            PreInstance pre,
            AxoObjectAbstract actual,
            GraphState state) {
        List<Integer> uuidCandidates = pre.requestedUuid == null
                ? List.of()
                : candidates(catalog.candidatesByUuid(pre.requestedUuid));
        if (!uuidCandidates.isEmpty()) {
            return catalogAttempt("uuid", uuidCandidates, actual, null, state, pre.serializedIndex);
        }

        if (isRelativeType(pre.requestedName)) {
            Path base = state.input.absolutePath().getParent();
            Path stem = base.resolve(pre.requestedName).normalize();
            Path axo = Path.of(stem.toString() + ".axo").toAbsolutePath().normalize();
            Path axs = Path.of(stem.toString() + ".axs").toAbsolutePath().normalize();

            boolean actualIsAxs = actual instanceof AxoObjectFromPatch
                    || actualPathEndsWith(actual, ".axs");
            if (!actualIsAxs && Files.isRegularFile(axo)) {
                List<Integer> fileCandidates = candidates(catalog.candidatesByFile(axo));
                if (!fileCandidates.isEmpty()) {
                    int firstDefinition = fileCandidates.get(0);
                    return catalogAttempt(
                            "relative-axo", List.of(firstDefinition), actual,
                            firstDefinition, state, pre.serializedIndex);
                }
                return localFileAttempt(
                        "relative-axo", axo, actual, state, pre.serializedIndex);
            }
            if (Files.isRegularFile(axs)) {
                Map<String, Object> target = graphLocalTarget(axs);
                if (target == null) {
                    state.partial = true;
                    issues.add(instanceIssue(
                            "error", "graph-resolve", "RELATIVE_GRAPH_TARGET_UNPINNED", state,
                            pre.serializedIndex,
                            "A relative subpatch resolved outside the configured source roots.",
                            true, List.of()));
                    return new ResolutionAttempt("relative-axs", List.of(), null, List.of());
                }
                return new ResolutionAttempt(
                        "relative-axs", List.of(target), actual == null ? null : target, List.of());
            }
            if (Files.isRegularFile(axo)) {
                List<Integer> fileCandidates = candidates(catalog.candidatesByFile(axo));
                if (!fileCandidates.isEmpty()) {
                    int firstDefinition = fileCandidates.get(0);
                    return catalogAttempt(
                            "relative-axo", List.of(firstDefinition), actual,
                            firstDefinition, state, pre.serializedIndex);
                }
                return localFileAttempt(
                        "relative-axo", axo, actual, state, pre.serializedIndex);
            }
            return new ResolutionAttempt("relative-axs", List.of(), null, List.of());
        }

        List<Integer> nameCandidates = pre.requestedName == null
                ? List.of()
                : candidates(catalog.candidatesByName(pre.requestedName));
        return catalogAttempt("name", nameCandidates, actual, null, state, pre.serializedIndex);
    }

    private ResolutionAttempt localFileAttempt(
            String method,
            Path path,
            AxoObjectAbstract actual,
            GraphState state,
            int instanceIndex) {
        Map<String, Object> target = graphLocalTarget(path);
        if (target == null) {
            state.partial = true;
            issues.add(instanceIssue(
                    "error", "graph-resolve", "RELATIVE_GRAPH_TARGET_UNPINNED", state,
                    instanceIndex,
                    "A relative local file resolved outside the configured source roots.",
                    true, List.of()));
            return new ResolutionAttempt(method, List.of(), null, List.of());
        }
        return new ResolutionAttempt(
                method, List.of(target), actual == null ? null : target, List.of());
    }

    private ResolutionAttempt catalogAttempt(
            String method,
            List<Integer> candidateIndexes,
            AxoObjectAbstract actual,
            Integer selectedFallback,
            GraphState state,
            int instanceIndex) {
        List<Map<String, Object>> candidateRefs = new ArrayList<>();
        for (Integer candidate : candidateIndexes) {
            candidateRefs.add(catalogTarget(candidate));
        }
        Integer selectedIndex = actual == null ? null : catalog.variantForActual(actual);
        if (selectedIndex == null && actual != null) {
            selectedIndex = selectedFallback;
        }
        if (selectedIndex == null && actual instanceof AxoObjectFromPatch && !candidateIndexes.isEmpty()) {
            selectedIndex = candidateIndexes.get(0);
        }
        Map<String, Object> selected = selectedIndex == null ? null : catalogTarget(selectedIndex);
        if (selectedIndex != null && !candidateIndexes.contains(selectedIndex)) {
            state.partial = true;
            candidateRefs.add(selected);
            List<Integer> expanded = new ArrayList<>(candidateIndexes);
            expanded.add(selectedIndex);
            candidateIndexes = List.copyOf(expanded);
            issues.add(instanceIssue(
                    "error", "graph-resolve", "SELECTED_TARGET_OUTSIDE_CANDIDATE_SET", state,
                    instanceIndex,
                    "The observed legacy-selected variant was absent from the independently indexed candidates.",
                    true, candidateIndexes));
        }
        return new ResolutionAttempt(method, List.copyOf(candidateRefs), selected, candidateIndexes);
    }

    private List<Map<String, Object>> parameterRecords(
            PreInstance pre,
            boolean postSucceeded,
            GraphState state) {
        if (pre.kind.equals("unsupported")) {
            return List.of();
        }
        if (!pre.zombieKind.equals("none")) {
            return parameterSnapshotRecords(pre.parameters, "preserved-zombie");
        }
        if (!postSucceeded || pre.post == null) {
            return parameterSnapshotRecords(pre.parameters, "unavailable");
        }

        List<ParameterSnapshot> post = snapshotParameters(
                safeList(pre.post.getParameterInstances()), state, pre.serializedIndex);
        Map<String, ArrayDeque<ParameterSnapshot>> serializedByName = queueParameters(pre.parameters);
        Set<ParameterSnapshot> consumed = java.util.Collections.newSetFromMap(new IdentityHashMap<>());
        List<Map<String, Object>> result = new ArrayList<>();
        for (ParameterSnapshot value : post) {
            ArrayDeque<ParameterSnapshot> matches = serializedByName.get(value.name);
            ParameterSnapshot serialized = matches == null ? null : matches.pollFirst();
            if (serialized != null) {
                consumed.add(serialized);
            }
            result.add(value.toMap(
                    result.size(),
                    value.unsupported ? "unsupported" : serialized == null ? "defaulted" : "serialized"));
        }
        for (ParameterSnapshot serialized : pre.parameters) {
            if (!consumed.contains(serialized)) {
                state.partial = true;
                result.add(serialized.toMap(result.size(), "unsupported"));
                issues.add(instanceIssue(
                        "warning", "graph-resolve", "SERIALIZED_PARAMETER_NOT_PROJECTED", state,
                        pre.serializedIndex,
                        "A serialized parameter did not project onto the resolved instance and was retained explicitly.",
                        true, List.of()));
            }
        }
        return result;
    }

    private List<Map<String, Object>> attributeRecords(
            PreInstance pre,
            boolean postSucceeded,
            GraphState state) {
        if (pre.kind.equals("unsupported")) {
            return List.of();
        }
        if (!pre.zombieKind.equals("none")) {
            return attributeSnapshotRecords(pre.attributes, "preserved-zombie");
        }
        if (!postSucceeded || pre.post == null) {
            return attributeSnapshotRecords(pre.attributes, "unavailable");
        }

        List<AttributeSnapshot> post = snapshotAttributes(
                safeList(pre.post.getAttributeInstances()), state, pre.serializedIndex);
        Map<String, ArrayDeque<AttributeSnapshot>> serializedByName = queueAttributes(pre.attributes);
        Set<AttributeSnapshot> consumed = java.util.Collections.newSetFromMap(new IdentityHashMap<>());
        List<Map<String, Object>> result = new ArrayList<>();
        for (AttributeSnapshot value : post) {
            ArrayDeque<AttributeSnapshot> matches = serializedByName.get(value.name);
            AttributeSnapshot serialized = matches == null ? null : matches.pollFirst();
            if (serialized != null) {
                consumed.add(serialized);
            }
            result.add(value.toMap(
                    result.size(),
                    value.unsupported ? "unsupported" : serialized == null ? "defaulted" : "serialized"));
        }
        for (AttributeSnapshot serialized : pre.attributes) {
            if (!consumed.contains(serialized)) {
                state.partial = true;
                result.add(serialized.toMap(result.size(), "unsupported"));
                issues.add(instanceIssue(
                        "warning", "graph-resolve", "SERIALIZED_ATTRIBUTE_NOT_PROJECTED", state,
                        pre.serializedIndex,
                        "A serialized attribute did not project onto the resolved instance and was retained explicitly.",
                        true, List.of()));
            }
        }
        return result;
    }

    private List<ParameterSnapshot> snapshotParameters(
            List<ParameterInstance> values,
            GraphState state,
            int instanceIndex) {
        List<ParameterSnapshot> result = new ArrayList<>();
        for (ParameterInstance<?> value : values) {
            try {
                NumericSnapshot numeric = numeric(value.getValue());
                boolean unsupported = numeric == null;
                List<PresetSnapshot> presets = new ArrayList<>();
                for (Preset preset : safeList(value.getPresets())) {
                    NumericSnapshot presetValue = numeric(preset.value);
                    if (presetValue == null) {
                        unsupported = true;
                    } else {
                        presets.add(new PresetSnapshot(preset.index, presetValue));
                    }
                }
                List<ModulationSnapshot> modulations = new ArrayList<>();
                if (value instanceof ParameterInstanceFrac32<?> frac32) {
                    List<Modulation> modulationValues = safeList(frac32.getModulators());
                    for (int modulationIndex = 0;
                            modulationIndex < modulationValues.size();
                            modulationIndex++) {
                        Modulation modulation = modulationValues.get(modulationIndex);
                        modulations.add(new ModulationSnapshot(
                                modulationIndex,
                                sanitize(modulation.sourceName),
                                sanitize(modulation.modName),
                                modulation.getValue().getRaw()));
                    }
                }
                result.add(new ParameterSnapshot(
                        sanitize(value.getName()),
                        value.getClass().getName(),
                        numeric,
                        SchussParameterAccess.onParent(value),
                        SchussParameterAccess.frozen(value),
                        SchussParameterAccess.midiCc(value),
                        List.copyOf(presets),
                        List.copyOf(modulations),
                        unsupported));
                if (unsupported) {
                    state.partial = true;
                    issues.add(instanceIssue(
                            "warning", "graph-resolve", "UNSUPPORTED_PARAMETER_VALUE", state,
                            instanceIndex,
                            "A parameter or preset value type is outside the locked numeric value union.",
                            true, List.of()));
                }
            } catch (RuntimeException exception) {
                state.partial = true;
                result.add(ParameterSnapshot.unavailable(
                        value == null ? "" : sanitize(value.getName()),
                        value == null ? "unavailable" : value.getClass().getName()));
                issues.add(instanceIssue(
                        "error", "graph-resolve", "PARAMETER_SNAPSHOT_FAILED", state,
                        instanceIndex,
                        "A parameter value could not be snapshotted safely.",
                        true, List.of()));
            }
        }
        return result;
    }

    private List<AttributeSnapshot> snapshotAttributes(
            List<AttributeInstance> values,
            GraphState state,
            int instanceIndex) {
        List<AttributeSnapshot> result = new ArrayList<>();
        for (AttributeInstance<?> value : values) {
            try {
                AttributePayload payload = attributePayload(value);
                boolean unsupported = payload == null;
                result.add(new AttributeSnapshot(
                        sanitize(value.getName()),
                        value.getClass().getName(),
                        payload,
                        unsupported));
                if (unsupported) {
                    state.partial = true;
                    issues.add(instanceIssue(
                            "warning", "graph-resolve", "UNSUPPORTED_ATTRIBUTE_VALUE", state,
                            instanceIndex,
                            "An attribute value type is outside the locked scalar attribute union.",
                            true, List.of()));
                }
            } catch (RuntimeException exception) {
                state.partial = true;
                result.add(new AttributeSnapshot(
                        value == null ? "" : sanitize(value.getName()),
                        value == null ? "unavailable" : value.getClass().getName(),
                        null,
                        true));
                issues.add(instanceIssue(
                        "error", "graph-resolve", "ATTRIBUTE_SNAPSHOT_FAILED", state,
                        instanceIndex,
                        "An attribute value could not be snapshotted safely.",
                        true, List.of()));
            }
        }
        return result;
    }

    private AttributePayload attributePayload(AttributeInstance<?> value) {
        if (value instanceof AttributeInstanceInt32 integer) {
            return new AttributePayload("int32", integer.getValue());
        }
        if (value instanceof AttributeInstanceSpinner integer) {
            return new AttributePayload("int32", integer.getValue());
        }
        if (value instanceof AttributeInstanceString<?> string) {
            String text = sanitize(string.getString());
            return text == null ? null : new AttributePayload("string", text);
        }
        if (value instanceof AttributeInstanceWavefile wavefile) {
            String text = sanitize(wavefile.getWaveFilename());
            return text == null ? null : new AttributePayload("string", text);
        }
        return null;
    }

    private Map<String, Object> netRecord(
            PreNet pre,
            Patch patch,
            List<PreInstance> preInstances,
            List<AxoObjectInstanceAbstract> postInstances,
            boolean postSucceeded,
            GraphState state) {
        Map<String, Object> record = map();
        record.put("serialized_index", pre.serializedIndex);

        if (pre.unsupported) {
            record.put("post_resolution_index", null);
            record.put("status", "unsupported");
            record.put("sources", List.of());
            record.put("destinations", List.of());
            record.put("resolved_data_type", null);
            return record;
        }

        if (!postSucceeded) {
            record.put("post_resolution_index", null);
            record.put("status", "partial");
            record.put("sources", notEvaluatedEndpoints(pre.sources));
            record.put("destinations", notEvaluatedEndpoints(pre.destinations));
            record.put("resolved_data_type", null);
            return record;
        }

        int postIndex = identityIndex(patch.nets, pre.original);
        if (postIndex >= 0) {
            List<Map<String, Object>> sourceRecords = retainedEndpoints(
                    pre.sources, safeList(pre.original.GetSource()), preInstances, postInstances,
                    "source", pre.serializedIndex, state);
            List<Map<String, Object>> destinationRecords = retainedEndpoints(
                    pre.destinations, safeList(pre.original.GetDest()), preInstances, postInstances,
                    "destination", pre.serializedIndex, state);
            boolean resolved = allResolved(sourceRecords) && allResolved(destinationRecords);
            if (pre.sources.isEmpty() || pre.destinations.isEmpty()) {
                resolved = false;
                state.partial = true;
                issues.add(netIssue(
                        "warning", "graph-resolve", "NET_STRUCTURALLY_INCOMPLETE", state,
                        pre.serializedIndex,
                        "A retained net has no serialized source or no serialized destination.",
                        true));
            }
            String dataType = null;
            try {
                DataType value = pre.original.GetDataType();
                dataType = value == null ? null : value.getClass().getName();
            } catch (RuntimeException exception) {
                resolved = false;
                state.partial = true;
                issues.add(netIssue(
                        "warning", "graph-resolve", "NET_DATA_TYPE_UNAVAILABLE", state,
                        pre.serializedIndex,
                        "The resolved net data type could not be observed safely.",
                        true));
            }
            record.put("post_resolution_index", postIndex);
            record.put("status", resolved ? "resolved" : "partial");
            record.put("sources", sourceRecords);
            record.put("destinations", destinationRecords);
            record.put("resolved_data_type", dataType);
            return record;
        }

        state.partial = true;
        RemovedEndpointResult removed = removedEndpoints(
                pre, preInstances, postInstances, state);
        issues.add(netIssue(
                "warning", "graph-resolve", "NET_REMOVED_DURING_RESOLUTION", state,
                pre.serializedIndex,
                "Legacy post-construction removed a net after endpoint resolution failed.",
                true));
        record.put("post_resolution_index", null);
        record.put("status", "removed");
        record.put("sources", removed.sources);
        record.put("destinations", removed.destinations);
        record.put("resolved_data_type", null);
        return record;
    }

    private List<Map<String, Object>> retainedEndpoints(
            List<EndpointSnapshot> requested,
            List<?> actual,
            List<PreInstance> preInstances,
            List<AxoObjectInstanceAbstract> postInstances,
            String role,
            int netIndex,
            GraphState state) {
        List<Map<String, Object>> result = new ArrayList<>();
        boolean[] consumed = new boolean[actual.size()];
        for (int index = 0; index < requested.size(); index++) {
            EndpointSnapshot endpoint = requested.get(index);
            int actualIndex = findRetainedEndpoint(
                    endpoint, actual, consumed, preInstances, postInstances);
            if (actualIndex < 0) {
                state.partial = true;
                result.add(endpoint.toMap("not_evaluated", null, null));
                issues.add(endpointIssue(
                        "error", "graph-resolve", "RESOLVED_ENDPOINT_CORRELATION_FAILED", state,
                        netIndex, role, index,
                        "A retained net endpoint could not be correlated by instance and port identity.",
                        true));
                continue;
            }
            consumed[actualIndex] = true;
            Object port = actual.get(actualIndex);
            AxoObjectInstanceAbstract object;
            int portIndex;
            if (port instanceof OutletInstance<?> outlet) {
                object = outlet.GetObjectInstance();
                object = canonicalPostObject(object, preInstances, postInstances);
                portIndex = object == null ? -1 : identityIndex(object.getOutletInstances(), outlet);
            } else if (port instanceof InletInstance<?> inlet) {
                object = inlet.GetObjectInstance();
                object = canonicalPostObject(object, preInstances, postInstances);
                portIndex = object == null ? -1 : identityIndex(object.getInletInstances(), inlet);
            } else {
                object = null;
                portIndex = -1;
            }
            int objectIndex = identityIndex(postInstances, object);
            if (objectIndex < 0 || portIndex < 0) {
                state.partial = true;
                result.add(endpoint.toMap("not_evaluated", null, null));
                issues.add(endpointIssue(
                        "error", "graph-resolve", "RESOLVED_ENDPOINT_INDEX_UNAVAILABLE", state,
                        netIndex, role, index,
                        "A retained endpoint could not be indexed in post-resolution graph state.",
                        true));
            } else {
                result.add(endpoint.toMap("resolved", objectIndex, portIndex));
            }
        }
        boolean hasUnconsumed = false;
        for (boolean value : consumed) {
            hasUnconsumed |= !value;
        }
        if (hasUnconsumed) {
            state.partial = true;
            issues.add(netIssue(
                    "error", "graph-resolve", "RESOLVED_ENDPOINT_COUNT_MISMATCH", state,
                    netIndex,
                    "A retained net has more resolved endpoints than serialized endpoints.",
                    true));
        }
        return result;
    }

    private int findRetainedEndpoint(
            EndpointSnapshot requested,
            List<?> actual,
            boolean[] consumed,
            List<PreInstance> preInstances,
            List<AxoObjectInstanceAbstract> postInstances) {
        for (int index = 0; index < actual.size(); index++) {
            if (consumed[index]) {
                continue;
            }
            Object port = actual.get(index);
            AxoObjectInstanceAbstract owner;
            String label;
            if (port instanceof OutletInstance<?> outlet) {
                owner = outlet.GetObjectInstance();
                label = sanitize(outlet.GetLabel());
            } else if (port instanceof InletInstance<?> inlet) {
                owner = inlet.GetObjectInstance();
                label = sanitize(inlet.GetLabel());
            } else {
                continue;
            }
            AxoObjectInstanceAbstract canonical =
                    canonicalPostObject(owner, preInstances, postInstances);
            String serializedName = serializedNameForPost(canonical, preInstances);
            if (equalNullable(requested.instanceName, serializedName)
                    && equalNullable(requested.portName, label)) {
                return index;
            }
        }
        return -1;
    }

    private static AxoObjectInstanceAbstract canonicalPostObject(
            AxoObjectInstanceAbstract owner,
            List<PreInstance> preInstances,
            List<AxoObjectInstanceAbstract> postInstances) {
        if (identityIndex(postInstances, owner) >= 0) {
            return owner;
        }
        for (PreInstance pre : preInstances) {
            if (pre.original == owner) {
                return pre.post;
            }
        }
        return null;
    }

    private String serializedNameForPost(
            AxoObjectInstanceAbstract post,
            List<PreInstance> preInstances) {
        for (PreInstance pre : preInstances) {
            if (pre.post == post || pre.original == post) {
                return pre.instanceName;
            }
        }
        return post == null ? null : sanitize(post.getInstanceName());
    }

    private RemovedEndpointResult removedEndpoints(
            PreNet pre,
            List<PreInstance> preInstances,
            List<AxoObjectInstanceAbstract> postInstances,
            GraphState state) {
        Map<String, AxoObjectInstanceAbstract> firstByName = new LinkedHashMap<>();
        for (PreInstance instance : preInstances) {
            if (instance.instanceName != null && instance.post != null) {
                firstByName.putIfAbsent(instance.instanceName, instance.post);
            }
        }
        for (AxoObjectInstanceAbstract object : postInstances) {
            firstByName.putIfAbsent(sanitize(object.getInstanceName()), object);
        }
        List<Map<String, Object>> sources = new ArrayList<>();
        List<Map<String, Object>> destinations = new ArrayList<>();
        boolean stopped = false;
        for (EndpointSnapshot endpoint : pre.sources) {
            EndpointEvaluation evaluation = stopped
                    ? EndpointEvaluation.notEvaluated()
                    : evaluateEndpoint(endpoint, true, postInstances, firstByName);
            stopped |= !evaluation.status.equals("resolved");
            sources.add(endpoint.toMap(
                    evaluation.status, evaluation.instanceIndex, evaluation.portIndex));
            emitMissingEndpointIssue(evaluation, state, pre.serializedIndex, "source", endpoint.index);
        }
        for (EndpointSnapshot endpoint : pre.destinations) {
            EndpointEvaluation evaluation = stopped
                    ? EndpointEvaluation.notEvaluated()
                    : evaluateEndpoint(endpoint, false, postInstances, firstByName);
            stopped |= !evaluation.status.equals("resolved");
            destinations.add(endpoint.toMap(
                    evaluation.status, evaluation.instanceIndex, evaluation.portIndex));
            emitMissingEndpointIssue(evaluation, state, pre.serializedIndex, "destination", endpoint.index);
        }
        return new RemovedEndpointResult(sources, destinations);
    }

    private EndpointEvaluation evaluateEndpoint(
            EndpointSnapshot endpoint,
            boolean source,
            List<AxoObjectInstanceAbstract> postInstances,
            Map<String, AxoObjectInstanceAbstract> firstByName) {
        AxoObjectInstanceAbstract object = firstByName.get(endpoint.instanceName);
        if (object == null) {
            return new EndpointEvaluation("missing_instance", null, null);
        }
        int objectIndex = identityIndex(postInstances, object);
        if (source) {
            OutletInstance<?> port = findOutlet(object, endpoint.portName);
            if (port == null) {
                return new EndpointEvaluation("missing_port", objectIndex, null);
            }
            return new EndpointEvaluation(
                    "resolved", objectIndex, identityIndex(object.getOutletInstances(), port));
        }
        InletInstance<?> port = findInlet(object, endpoint.portName);
        if (port == null) {
            return new EndpointEvaluation("missing_port", objectIndex, null);
        }
        return new EndpointEvaluation(
                "resolved", objectIndex, identityIndex(object.getInletInstances(), port));
    }

    private void emitMissingEndpointIssue(
            EndpointEvaluation evaluation,
            GraphState state,
            int netIndex,
            String role,
            int endpointIndex) {
        if (evaluation.status.equals("missing_instance")) {
            issues.add(endpointIssue(
                    "warning", "graph-resolve", "NET_ENDPOINT_INSTANCE_MISSING", state,
                    netIndex, role, endpointIndex,
                    "A serialized net endpoint names no post-resolution instance.",
                    true));
        } else if (evaluation.status.equals("missing_port")) {
            issues.add(endpointIssue(
                    "warning", "graph-resolve", "NET_ENDPOINT_PORT_MISSING", state,
                    netIndex, role, endpointIndex,
                    "A serialized net endpoint names no port on the post-resolution instance.",
                    true));
        }
    }

    private static OutletInstance<?> findOutlet(AxoObjectInstanceAbstract object, String name) {
        if (name == null) {
            return null;
        }
        for (OutletInstance<?> outlet : safeList(object.getOutletInstances())) {
            if (equalNullable(name, outlet.GetLabel())) {
                return outlet;
            }
        }
        if (!(object instanceof AxoObjectInstanceZombie)) {
            return object.getOutletInstance(name);
        }
        return null;
    }

    private static InletInstance<?> findInlet(AxoObjectInstanceAbstract object, String name) {
        if (name == null) {
            return null;
        }
        for (InletInstance<?> inlet : safeList(object.getInletInstances())) {
            if (equalNullable(name, inlet.GetLabel())) {
                return inlet;
            }
        }
        if (!(object instanceof AxoObjectInstanceZombie)) {
            return object.getInletInstance(name);
        }
        return null;
    }

    private List<ElementSlot> scanTopLevelElements(Path path) throws Exception {
        XMLInputFactory factory = XMLInputFactory.newFactory();
        setXmlProperty(factory, XMLInputFactory.SUPPORT_DTD, false);
        setXmlProperty(factory, "javax.xml.stream.isSupportingExternalEntities", false);
        List<ElementSlot> result = new ArrayList<>();
        try (InputStream input = Files.newInputStream(path)) {
            XMLStreamReader reader = factory.createXMLStreamReader(input);
            int depth = 0;
            try {
                while (reader.hasNext()) {
                    int event = reader.next();
                    if (event == XMLStreamConstants.START_ELEMENT) {
                        depth++;
                        if (depth == 2) {
                            String name = reader.getLocalName();
                            if (!PATCH_METADATA_ELEMENTS.contains(name)) {
                                String instanceName = attribute(reader, "name");
                                if (instanceName == null && name.equals("comment")) {
                                    instanceName = attribute(reader, "text");
                                }
                                result.add(new ElementSlot(
                                        name,
                                        sanitize(instanceName),
                                        sanitize(attribute(reader, "type")),
                                        sanitize(attribute(reader, "uuid")),
                                        sanitize(attribute(reader, "sha"))));
                            }
                        }
                    } else if (event == XMLStreamConstants.END_ELEMENT) {
                        depth--;
                    }
                }
            } finally {
                reader.close();
            }
        }
        return result;
    }

    private static void setXmlProperty(XMLInputFactory factory, String property, Object value) {
        try {
            factory.setProperty(property, value);
        } catch (IllegalArgumentException ignored) {
            // The JDK provider supports both properties. A different provider may not.
        }
    }

    private static String attribute(XMLStreamReader reader, String name) {
        return reader.getAttributeValue(null, name);
    }

    private Map<String, Object> graphLocalTarget(Path target) {
        Path absolute = target.toAbsolutePath().normalize();
        List<ResolvedInventoryExporter.Source> orderedSources = new ArrayList<>(sources);
        orderedSources.sort(Comparator.comparing(ResolvedInventoryExporter.Source::id));
        List<ResolvedInventoryExporter.Source> containingSources = new ArrayList<>();
        for (ResolvedInventoryExporter.Source source : orderedSources) {
            Path root = source.root().toAbsolutePath().normalize();
            if (absolute.startsWith(root)) {
                containingSources.add(source);
            }
        }
        if (containingSources.size() != 1
                || !Files.isRegularFile(absolute, LinkOption.NOFOLLOW_LINKS)) {
            return null;
        }
        ResolvedInventoryExporter.Source source = containingSources.get(0);
        try {
            Map<String, Object> result = map();
            result.put("kind", "graph-local-file");
            result.put("source_id", source.id());
            result.put("path", portable(source, absolute));
            result.put("sha256", sha256(absolute));
            result.put("definition_index", 0);
            return result;
        } catch (RuntimeException exception) {
            return null;
        }
    }

    private static Map<String, Object> catalogTarget(int variantIndex) {
        Map<String, Object> result = map();
        result.put("kind", "catalog");
        result.put("variant_index", variantIndex);
        return result;
    }

    private List<Map<String, Object>> parameterSnapshotRecords(
            List<ParameterSnapshot> snapshots,
            String status) {
        List<Map<String, Object>> result = new ArrayList<>();
        for (ParameterSnapshot snapshot : snapshots) {
            result.add(snapshot.toMap(
                    result.size(), snapshot.unsupported ? "unsupported" : status));
        }
        return result;
    }

    private List<Map<String, Object>> attributeSnapshotRecords(
            List<AttributeSnapshot> snapshots,
            String status) {
        List<Map<String, Object>> result = new ArrayList<>();
        for (AttributeSnapshot snapshot : snapshots) {
            result.add(snapshot.toMap(
                    result.size(), snapshot.unsupported ? "unsupported" : status));
        }
        return result;
    }

    private static Map<String, ArrayDeque<ParameterSnapshot>> queueParameters(
            List<ParameterSnapshot> values) {
        Map<String, ArrayDeque<ParameterSnapshot>> result = new HashMap<>();
        for (ParameterSnapshot value : values) {
            result.computeIfAbsent(value.name, ignored -> new ArrayDeque<>()).add(value);
        }
        return result;
    }

    private static Map<String, ArrayDeque<AttributeSnapshot>> queueAttributes(
            List<AttributeSnapshot> values) {
        Map<String, ArrayDeque<AttributeSnapshot>> result = new HashMap<>();
        for (AttributeSnapshot value : values) {
            result.computeIfAbsent(value.name, ignored -> new ArrayDeque<>()).add(value);
        }
        return result;
    }

    private static List<Map<String, Object>> notEvaluatedEndpoints(
            List<EndpointSnapshot> endpoints) {
        List<Map<String, Object>> result = new ArrayList<>();
        for (EndpointSnapshot endpoint : endpoints) {
            result.add(endpoint.toMap("not_evaluated", null, null));
        }
        return result;
    }

    private static boolean allResolved(List<Map<String, Object>> endpoints) {
        for (Map<String, Object> endpoint : endpoints) {
            if (!"resolved".equals(endpoint.get("resolution_status"))) {
                return false;
            }
        }
        return true;
    }

    private static NumericSnapshot numeric(Value<?> value) {
        if (value instanceof ValueInt32) {
            return new NumericSnapshot("int32", value.getRaw());
        }
        if (value instanceof ValueFrac32) {
            return new NumericSnapshot("frac32", value.getRaw());
        }
        return null;
    }

    private static String instanceKind(AxoObjectInstanceAbstract object) {
        if (object instanceof AxoObjectInstancePatcher) return "patcher";
        if (object instanceof AxoObjectInstancePatcherObject) return "patchobj";
        if (object instanceof AxoObjectInstanceComment) return "comment";
        if (object instanceof AxoObjectInstanceHyperlink) return "hyperlink";
        if (object instanceof AxoObjectInstanceZombie) return "zombie";
        if (object instanceof AxoObjectInstance) return "obj";
        return "unsupported";
    }

    private static boolean isRelativeType(String value) {
        return value != null && (value.startsWith("./") || value.startsWith("../"));
    }

    private static boolean actualPathEndsWith(AxoObjectAbstract actual, String suffix) {
        return actual != null && actual.sObjFilePath != null && actual.sObjFilePath.endsWith(suffix);
    }

    private String sanitize(String value) {
        if (value == null) {
            return null;
        }
        String result = value;
        for (ResolvedInventoryExporter.Source source : sources) {
            String root = source.root().toAbsolutePath().normalize().toString();
            result = result.replace(root, "source://" + source.id());
            result = result.replace(root.replace(File.separatorChar, '/'), "source://" + source.id());
        }
        if (looksLikeAbsolutePath(result)) {
            currentGraphRedactions++;
            return "<absolute-path>";
        }
        return result;
    }

    private static boolean looksLikeAbsolutePath(String value) {
        if (value.startsWith("/") || value.startsWith("\\\\")) {
            return true;
        }
        return value.length() >= 3
                && Character.isLetter(value.charAt(0))
                && value.charAt(1) == ':'
                && (value.charAt(2) == '\\' || value.charAt(2) == '/');
    }

    private static boolean isGraphFile(Path path) {
        String name = path.getFileName().toString();
        return name.endsWith(".axs") || name.endsWith(".axp");
    }

    private static String portable(ResolvedInventoryExporter.Source source, Path path) {
        Path root = source.root().toAbsolutePath().normalize();
        Path absolute = path.toAbsolutePath().normalize();
        if (!absolute.startsWith(root)) {
            throw new IllegalArgumentException("path escaped configured source root");
        }
        String value = root.relativize(absolute).toString().replace(File.separatorChar, '/');
        if (value.isEmpty() || value.startsWith("/")
                || value.equals("..") || value.startsWith("../")) {
            throw new IllegalArgumentException("non-portable source-relative path");
        }
        return value;
    }

    private static String sha256(Path path) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (InputStream input = Files.newInputStream(path)) {
                byte[] buffer = new byte[65536];
                int read;
                while ((read = input.read(buffer)) >= 0) {
                    digest.update(buffer, 0, read);
                }
            }
            return java.util.HexFormat.of().formatHex(digest.digest());
        } catch (Exception exception) {
            throw new IllegalStateException("unable to hash graph source", exception);
        }
    }

    private static Map<String, Object> failedGraphRecord(
            int graphIndex,
            GraphInput input,
            String hash) {
        Map<String, Object> record = map();
        record.put("schema_version", "legacy-resolved-graph-v0");
        record.put("graph_index", graphIndex);
        record.put("source", sourceMap(input, hash));
        record.put("export_status", "failed");
        record.put("instances", List.of());
        record.put("nets", List.of());
        return record;
    }

    private static Map<String, Object> sourceMap(GraphInput input, String hash) {
        Map<String, Object> source = map();
        source.put("source_id", input.source().id());
        source.put("path", input.path());
        source.put("sha256", hash);
        source.put("file_type", input.path().endsWith(".axs") ? "axs" : "axp");
        return source;
    }

    private static List<Integer> candidates(List<Integer> values) {
        if (values == null || values.isEmpty()) {
            return List.of();
        }
        List<Integer> result = new ArrayList<>();
        for (Integer value : values) {
            if (value != null && value >= 0) {
                result.add(value);
            }
        }
        return List.copyOf(result);
    }

    private static <T> List<T> safeList(List<T> value) {
        return value == null ? List.of() : value;
    }

    private static int identityIndex(List<?> values, Object wanted) {
        if (values == null || wanted == null) {
            return -1;
        }
        for (int index = 0; index < values.size(); index++) {
            if (values.get(index) == wanted) {
                return index;
            }
        }
        return -1;
    }

    private static boolean equalNullable(Object left, Object right) {
        return java.util.Objects.equals(left, right);
    }

    private static Map<String, Object> graphIssue(
            String severity,
            String stage,
            String code,
            GraphInput input,
            int graphIndex,
            String message,
            boolean continued) {
        return issueMap(
                severity, stage, code, "graph", input.source().id(), input.path(),
                graphIndex, null, null, null, null, message, continued, List.of());
    }

    private static Map<String, Object> instanceIssue(
            String severity,
            String stage,
            String code,
            GraphState state,
            int instanceIndex,
            String message,
            boolean continued,
            List<Integer> candidates) {
        return issueMap(
                severity, stage, code, "instance", state.input.source().id(), state.input.path(),
                state.graphIndex, instanceIndex, null, null, null, message, continued, candidates);
    }

    private static Map<String, Object> netIssue(
            String severity,
            String stage,
            String code,
            GraphState state,
            int netIndex,
            String message,
            boolean continued) {
        return issueMap(
                severity, stage, code, "net", state.input.source().id(), state.input.path(),
                state.graphIndex, null, netIndex, null, null, message, continued, List.of());
    }

    private static Map<String, Object> endpointIssue(
            String severity,
            String stage,
            String code,
            GraphState state,
            int netIndex,
            String role,
            int endpointIndex,
            String message,
            boolean continued) {
        return issueMap(
                severity, stage, code, "endpoint", state.input.source().id(), state.input.path(),
                state.graphIndex, null, netIndex, role, endpointIndex, message, continued, List.of());
    }

    private static Map<String, Object> issueMap(
            String severity,
            String stage,
            String code,
            String kind,
            String sourceId,
            String path,
            Integer graphIndex,
            Integer instanceIndex,
            Integer netIndex,
            String endpointRole,
            Integer endpointIndex,
            String message,
            boolean continued,
            List<Integer> candidateIndexes) {
        Map<String, Object> record = map();
        record.put("schema_version", "legacy-resolved-issue-v0");
        record.put("issue_index", 0);
        record.put("severity", severity);
        record.put("stage", stage);
        record.put("code", code);
        Map<String, Object> location = map();
        location.put("kind", kind);
        location.put("source_id", sourceId);
        location.put("path", path);
        location.put("variant_index", null);
        location.put("graph_index", graphIndex);
        location.put("instance_index", instanceIndex);
        location.put("net_index", netIndex);
        location.put("endpoint_role", endpointRole);
        location.put("endpoint_index", endpointIndex);
        record.put("location", location);
        record.put("message", message);
        record.put("processing_continued", continued);
        record.put("facts", List.of());
        List<Integer> uniqueCandidates = new ArrayList<>(new LinkedHashSet<>(candidateIndexes));
        uniqueCandidates.sort(Integer::compareTo);
        record.put("candidate_variant_indexes", uniqueCandidates);
        return record;
    }

    private static Map<String, Object> map() {
        return new LinkedHashMap<>();
    }

    private record GraphInput(
            ResolvedInventoryExporter.Source source,
            String path,
            Path absolutePath) {
    }

    private static final class GraphState {
        final GraphInput input;
        final int graphIndex;
        final String sha256;
        boolean partial;
        boolean failed;

        GraphState(GraphInput input, int graphIndex, String sha256) {
            this.input = input;
            this.graphIndex = graphIndex;
            this.sha256 = sha256;
        }
    }

    private record ElementSlot(
            String elementName,
            String instanceName,
            String typeName,
            String typeUuid,
            String typeSha) {
    }

    private static final class PreInstance {
        final int serializedIndex;
        final String kind;
        final AxoObjectInstanceAbstract original;
        final String instanceName;
        final String requestedName;
        final String requestedUuid;
        final String requestedSha;
        final List<ParameterSnapshot> parameters;
        final List<AttributeSnapshot> attributes;
        AxoObjectInstanceAbstract post;
        Integer postIndex;
        String zombieKind = "none";

        PreInstance(
                int serializedIndex,
                String kind,
                AxoObjectInstanceAbstract original,
                String instanceName,
                String requestedName,
                String requestedUuid,
                String requestedSha,
                List<ParameterSnapshot> parameters,
                List<AttributeSnapshot> attributes) {
            this.serializedIndex = serializedIndex;
            this.kind = kind;
            this.original = original;
            this.instanceName = instanceName;
            this.requestedName = requestedName;
            this.requestedUuid = requestedUuid;
            this.requestedSha = requestedSha;
            this.parameters = parameters;
            this.attributes = attributes;
            if (original instanceof AxoObjectInstanceZombie) {
                this.zombieKind = "serialized-hard";
            }
        }

        static PreInstance unsupported(
                int serializedIndex,
                ElementSlot slot,
                GraphRecordExporter exporter) {
            return new PreInstance(
                    serializedIndex,
                    "unsupported",
                    null,
                    exporter.sanitize(slot.instanceName()),
                    exporter.sanitize(slot.typeName()),
                    exporter.sanitize(slot.typeUuid()),
                    exporter.sanitize(slot.typeSha()),
                    List.of(),
                    List.of());
        }
    }

    private record PreNet(
            int serializedIndex,
            Net original,
            List<EndpointSnapshot> sources,
            List<EndpointSnapshot> destinations,
            boolean unsupported) {
    }

    private record Resolution(
            String status,
            String method,
            List<Map<String, Object>> candidates,
            Map<String, Object> selected) {
        static Resolution empty(String status, String method) {
            return new Resolution(status, method, List.of(), null);
        }

        Map<String, Object> toMap() {
            Map<String, Object> value = map();
            value.put("status", status);
            value.put("method", method);
            value.put("candidates", candidates);
            value.put("legacy_selected", selected);
            return value;
        }
    }

    private record ResolutionAttempt(
            String method,
            List<Map<String, Object>> candidates,
            Map<String, Object> selected,
            List<Integer> candidateIndexes) {
    }

    private record NumericSnapshot(String kind, int raw) {
        Map<String, Object> toMap() {
            Map<String, Object> value = map();
            value.put("kind", kind);
            value.put("raw", raw);
            return value;
        }
    }

    private record PresetSnapshot(int index, NumericSnapshot value) {
        Map<String, Object> toMap() {
            Map<String, Object> result = map();
            result.put("index", index);
            result.put("value", value.toMap());
            return result;
        }
    }

    private record ModulationSnapshot(
            int index,
            String sourceInstanceName,
            String modulatorName,
            int amountRaw) {
        Map<String, Object> toMap() {
            Map<String, Object> result = map();
            result.put("index", index);
            result.put("source_instance_name", sourceInstanceName == null ? "" : sourceInstanceName);
            result.put("modulator_name", modulatorName);
            result.put("amount_raw", amountRaw);
            return result;
        }
    }

    private record ParameterSnapshot(
            String name,
            String legacyType,
            NumericSnapshot value,
            Boolean onParent,
            Boolean frozen,
            Integer midiCc,
            List<PresetSnapshot> presets,
            List<ModulationSnapshot> modulations,
            boolean unsupported) {
        static ParameterSnapshot unavailable(String name, String legacyType) {
            return new ParameterSnapshot(
                    name == null ? "" : name,
                    legacyType,
                    null,
                    null,
                    null,
                    null,
                    List.of(),
                    List.of(),
                    true);
        }

        Map<String, Object> toMap(int index, String status) {
            Map<String, Object> result = map();
            result.put("index", index);
            result.put("name", name == null ? "" : name);
            result.put("legacy_type", legacyType);
            result.put("value_status", status);
            result.put("effective_value", value == null ? null : value.toMap());
            result.put("on_parent", onParent);
            result.put("frozen", frozen);
            result.put("midi_cc", midiCc);
            result.put("presets", presets.stream().map(PresetSnapshot::toMap).toList());
            result.put("modulations", modulations.stream().map(ModulationSnapshot::toMap).toList());
            return result;
        }
    }

    private record AttributePayload(String kind, Object value) {
        Map<String, Object> toMap() {
            Map<String, Object> result = map();
            result.put("kind", kind);
            result.put("value", value);
            return result;
        }
    }

    private record AttributeSnapshot(
            String name,
            String legacyType,
            AttributePayload value,
            boolean unsupported) {
        Map<String, Object> toMap(int index, String status) {
            Map<String, Object> result = map();
            result.put("index", index);
            result.put("name", name == null ? "" : name);
            result.put("legacy_type", legacyType);
            result.put("value_status", status);
            result.put("value", value == null ? null : value.toMap());
            return result;
        }
    }

    private record EndpointSnapshot(int index, String instanceName, String portName) {
        Map<String, Object> toMap(
                String resolutionStatus,
                Integer resolvedInstanceIndex,
                Integer resolvedPortIndex) {
            Map<String, Object> result = map();
            result.put("serialized_index", index);
            Map<String, Object> requested = map();
            requested.put("instance_name", instanceName);
            requested.put("port_name", portName);
            result.put("requested", requested);
            result.put("resolution_status", resolutionStatus);
            result.put("resolved_instance_index", resolvedInstanceIndex);
            result.put("resolved_port_index", resolvedPortIndex);
            return result;
        }
    }

    private record EndpointEvaluation(
            String status,
            Integer instanceIndex,
            Integer portIndex) {
        static EndpointEvaluation notEvaluated() {
            return new EndpointEvaluation("not_evaluated", null, null);
        }
    }

    private record RemovedEndpointResult(
            List<Map<String, Object>> sources,
            List<Map<String, Object>> destinations) {
    }
}
