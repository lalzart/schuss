import type { CatalogItem, ExactReference } from "./types";

export const CATALOG_DRAG_MIME = "application/x-schuss-catalog-family";

const ref = (
  stableId: string,
  contentHash: string,
  revision = 1,
): ExactReference => ({ contentHash, revision, stableId });

const direct = (
  displayName: string,
  description: string,
  primaryFunction: string,
  familyId: string,
  familyHash: string,
  contractId: string,
  contractHash: string,
): CatalogItem => ({
  contractReference: ref(contractId, contractHash),
  description,
  displayName,
  familyReference: ref(familyId, familyHash),
  primaryFunction,
  selectable: true,
  statusLabel: "Accepted direct palette · local L2 proof",
});

export const SELECTABLE_CATALOG_ITEMS: readonly CatalogItem[] = [
  direct(
    "Band-limited Saw Oscillator",
    "Generates a band-limited sawtooth audio stream from pitch control.",
    "sound-sources",
    "schuss-family-000031",
    "sha256:544ed1e5f1e297b430557e2957dc1934534cfee3b3fada17eaee571ce34dd4c6",
    "schuss-component-contract-000012",
    "sha256:3f399547dbe7a1a76bdcedc1d1d886ccd49d0620fdbca3fbace6aac0a9d2292c",
  ),
  direct(
    "Band-limited PWM Oscillator",
    "Generates a band-limited pulse audio stream with pitch and pulse-width control.",
    "sound-sources",
    "schuss-family-000032",
    "sha256:45ed87a20e425b0b73c83dcdbb8cb6399e04ee28917f28138a42558cb8546ff1",
    "schuss-component-contract-000013",
    "sha256:2c4d15d5228dadfbf9c5ecb8734e7207b7157fc8960fb4100b461b59f859daa0",
  ),
  direct(
    "Exponential Control Smoother",
    "Smooths a control stream with a stateful exponential response.",
    "modulation-control",
    "schuss-family-000034",
    "sha256:6e9149e8575c33e1d6da3688a94090d9d4f9c5cd241c727a110458d1deb5c9c9",
    "schuss-component-contract-000015",
    "sha256:705b8e11c00d985eb8fd010a2d3fd71cb891f00711ad647b0746cdfb90c6ff81",
  ),
  direct(
    "Audio Soft Clipper",
    "Applies the reviewed audio-rate cubic soft-saturation variant.",
    "shaping-dynamics",
    "schuss-family-000035",
    "sha256:e151b57b4cc1c9bbf46991f7cee14241ccfb8bd44e1c496d5f6bbe5333ccc25b",
    "schuss-component-contract-000016",
    "sha256:c98e44b172cf256439edfe2f51c15499f29ffe39900d9f8de72c339e346762e2",
  ),
  direct(
    "Interpolated Audio VCA",
    "Applies a control-rate gain to audio with retained block interpolation.",
    "shaping-dynamics",
    "schuss-family-000039",
    "sha256:d02d5283f942119f5216ca61b5b4b2edd6e4195445a250d1847dc2bdf7b884c3",
    "schuss-component-contract-000020",
    "sha256:0cf9737582327560e82feb565fd3092993b750938a9669fc43305b5658ac5490",
  ),
  direct(
    "Attack-Decay Envelope",
    "Produces a linear-attack, exponential-decay control envelope from rising triggers.",
    "modulation-control",
    "schuss-family-000033",
    "sha256:283e53937f9be618366d55d7bbc22589d125bfb6e9f45ff9cdb627ba65510e84",
    "schuss-component-contract-000014",
    "sha256:4106dca5893ccbd687374c49552d24b2957a63763c48b1d3d4c670cbdb642e08",
  ),
  direct(
    "Clocked Logic Toggle",
    "Toggles a Boolean state on each rising clock edge.",
    "timing-sequencing",
    "schuss-family-000029",
    "sha256:e02062cfd669e2e584a14305d584da6d46a032836a5d23dd6e1f10d5ddfb5295",
    "schuss-component-contract-000010",
    "sha256:813b4aa7cc9d3c6fab6b34a99db30cc8badfc1912091bb36a9ab161b82f7f848",
  ),
  direct(
    "Pseudo-Euclidean Gate Sequencer",
    "Advances a bounded pseudo-Euclidean gate pattern from an incoming clock.",
    "timing-sequencing",
    "schuss-family-000030",
    "sha256:c28a53226d11aa6ffa85cd5e8e461b425a60ef1d47d7b799febb8d49e8fa722d",
    "schuss-component-contract-000011",
    "sha256:21fde01ba278cd35ef8209805334c9747cb6fe0064a63b5913e38a3e32fcc144",
  ),
  direct(
    "Struck Drum Voice",
    "Generates a struck-drum audio voice with pitch, timbre, color, and strike control.",
    "sound-sources",
    "schuss-family-000037",
    "sha256:f2d6b946ed234e9aa0dbcd5d63410897df2ef0b0f72cb17956e446f3f95a7f29",
    "schuss-component-contract-000018",
    "sha256:5487dab7231dab7e3453b8eba4af2e95caaa55a491692c42624277f1aa89d3c4",
  ),
  direct(
    "Struck Bell Voice",
    "Generates a struck-bell audio voice with pitch, timbre, color, and strike control.",
    "sound-sources",
    "schuss-family-000038",
    "sha256:af55d92c4b87e0fbd6387283d4a3b8235631e5bc1d0c0e850a92403e085677f0",
    "schuss-component-contract-000019",
    "sha256:cf04a87d454b9368db3ea655cdc82b6b281ec1ecbc8d867cc3d35ef482b6ce37",
  ),
  direct(
    "Uniform Noise",
    "Generates uniformly distributed broadband noise.",
    "sound-sources",
    "schuss-family-000004",
    "sha256:290a95bc1812fa61973b7f93ad97a59e0e52b77eba77435eafb6cd61c2ad9848",
    "schuss-component-contract-000022",
    "sha256:d790b11c180bbbf61605c64a7fdb05501e14a95591a939a685ee906d64226df4",
  ),
  direct(
    "Standard ADSR",
    "Generates an attack-decay-sustain-release control contour from a gate.",
    "modulation-control",
    "schuss-family-000007",
    "sha256:bff01afcd25281ffa28d82652627e6a302df2248c0b8f1dd790a1dedb40bb047",
    "schuss-component-contract-000023",
    "sha256:843a4158ebc0a079ad3b3e30e86d79751e8fcb749264cc5ce14f9be3edd3cf9d",
  ),
  direct(
    "Standard Sine LFO",
    "Generates a cyclic sine modulation signal, including an extended slow-range implementation.",
    "modulation-control",
    "schuss-family-000008",
    "sha256:2357a85213ed8917850fb6a4bcce0ffd589865a137e528e41f7362b502d808aa",
    "schuss-component-contract-000024",
    "sha256:128fb745c4e71b1c36d8398f8d368f45b6dc29a516fd86a64ea04b7709801962",
  ),
  direct(
    "Decay Envelope",
    "Generates a decaying control contour from an incoming trigger.",
    "modulation-control",
    "schuss-family-000049",
    "sha256:2896f48f9dc68c0ceededf0497d988178020f64d3cc380e1d24fc76b37f58448",
    "schuss-component-contract-000025",
    "sha256:95129d2611e840fc91f46c12515d054fe015dc0b56c4197029f950a043539019",
  ),
  direct(
    "Control Low-pass Filter",
    "Applies a first-order low-pass response to a control-rate signal.",
    "filters-resonators",
    "schuss-family-000044",
    "sha256:60c1780ca1f9c38039e5fe19827ac9bc8738b4543149a31699763a80166f0e97",
    "schuss-component-contract-000026",
    "sha256:620d541e5c33f4ef59e65d30cad2c7aa61dbc2401acf1a88a463d11a88731e19",
  ),
  direct(
    "Two-pole Resonant Audio Low-pass",
    "Processes an audio-rate signal through a two-pole resonant low-pass whose coefficients update at control rate.",
    "filters-resonators",
    "schuss-family-000050",
    "sha256:f90816a68e938e35bd4096b6a4a27f9c9861b11c4c21d149c97476a306f2c82e",
    "schuss-component-contract-000027",
    "sha256:9917941da88aea188a102a4313766c80e2132b24214c069fa064b37a4f363ab2",
  ),
  direct(
    "Saturating Gain",
    "Applies positive gain with retained saturation behavior.",
    "shaping-dynamics",
    "schuss-family-000058",
    "sha256:edd1d9adc807bc786a68fe059325577d9ac5d6455f11c6e981235b8655b5dcaf",
    "schuss-component-contract-000028",
    "sha256:143d1507a5428aacb489e59309f93f5eb365d17218c41b86383c88fe5e19e203",
  ),
  direct(
    "Two-input Audio Mixer",
    "Combines two audio-rate inputs with independent gains.",
    "mixing-routing",
    "schuss-family-000057",
    "sha256:55ea1c9fb2002723347605c6078ef51b45dde293dbbb1215b40c98e0cf62d6f3",
    "schuss-component-contract-000029",
    "sha256:2dd30b99dac2a5fbca5317107d825fab71d02760f4a737a5d547f0b3d5e7ebea",
  ),
  direct(
    "Audio-rate Addition",
    "Adds two control, audio, or integer values using a type-specific implementation.",
    "mixing-routing",
    "schuss-family-000023",
    "sha256:2097fea546b840536ee651e89da92e6751fb1a824117a69015025787f6786177",
    "schuss-component-contract-000030",
    "sha256:98cc597610458700346655fb8ead28b7decaa6a0b4880ba7732cafa3189f0650",
  ),
  direct(
    "Triggered Value Latch",
    "Copies its input to retained output on a rising trigger edge.",
    "data-math-logic",
    "schuss-family-000054",
    "sha256:d844a166afe5b513501261f93934070d8dfc7de8f875ec62b22a1605103c2b2d",
    "schuss-component-contract-000031",
    "sha256:72a1ca00fbc9561bdfc3a87bc4f19e90f5b8ea927d2799f4c88e63b78465babc",
  ),
] as const;

export const DISABLED_CATALOG_ITEMS: readonly CatalogItem[] = [
  {
    contractReference: null,
    description: "Processes buffered stereo audio through granular, pitch, feedback, and spatial modes.",
    disabledReason: "Catalogued only; no exact selectable component contract.",
    displayName: "Granular Buffer Processor",
    familyReference: ref(
      "schuss-family-000006",
      "sha256:2c40db48493577e9d6eed850410ffb458cdd42aa188e9d1568092906b61c9eda",
    ),
    primaryFunction: "sampling-buffers",
    selectable: false,
    statusLabel: "Catalogued only · unresolved",
  },
  {
    contractReference: ref(
      "schuss-component-contract-000017",
      "sha256:7bc2c3561f38bd72660fc2de9dadb97418e5ecb81db280accfe55fb8a69b8ea8",
    ),
    description: "Processes stereo audio through the retained Rings-derived reverb implementation.",
    disabledReason: "Contracted and bound, but not an accepted direct-palette promotion.",
    displayName: "Rings-derived Stereo Reverb",
    familyReference: ref(
      "schuss-family-000036",
      "sha256:3f959ec098fb2ebd2c6fce0794bf39efaa791210675d441f578d098914e79710",
    ),
    primaryFunction: "delay-reverb",
    selectable: false,
    statusLabel: "Bound · unresolved · not selectable",
  },
  {
    contractReference: null,
    description: "Writes formatted text fields to the Gills OLED through a device-specific service object.",
    disabledReason: "Device-profile service; not suitable for standalone palette promotion.",
    displayName: "Gills Text Display",
    familyReference: ref(
      "schuss-family-000025",
      "sha256:e0a2886bf7edae940acdd7a919cddaea8a7465409e13f3ba0af4f716d95b7b1d",
    ),
    primaryFunction: "interface-system",
    selectable: false,
    statusLabel: "Catalogued only · profile-owned",
  },
] as const;

export const ALL_CATALOG_ITEMS: readonly CatalogItem[] = [
  ...SELECTABLE_CATALOG_ITEMS,
  ...DISABLED_CATALOG_ITEMS,
];

export const CATALOG_CATEGORIES = [
  ...new Set(SELECTABLE_CATALOG_ITEMS.map((item) => item.primaryFunction)),
].sort();

export function catalogItemByFamily(familyId: string): CatalogItem | undefined {
  return ALL_CATALOG_ITEMS.find((item) => item.familyReference.stableId === familyId);
}

export function filterCatalogItems(
  items: readonly CatalogItem[],
  query: string,
  category: string,
): CatalogItem[] {
  const normalizedQuery = query.trim().toLocaleLowerCase();
  return items.filter((item) => {
    const categoryMatches = category === "all" || item.primaryFunction === category;
    const queryMatches = normalizedQuery.length === 0
      || `${item.displayName} ${item.description} ${item.primaryFunction}`
        .toLocaleLowerCase()
        .includes(normalizedQuery);
    return categoryMatches && queryMatches;
  });
}

