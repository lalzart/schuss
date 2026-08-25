# Generative Modular Patch Study and JUCE Instrument Shortlist

> Status: proposed
> Proposal revision: 0.1
> Work type: `new-design`
> Original idea: Do some research on interesting mutable instrument patches for modular synths (can include MI modules too) and propose several different JUCE instruments we could create.
> Implementation target: JUCE-independent C++17 Instrument Lab Core with an optional authenticated JUCE 8.0.15 standalone adapter
> Working artifact and evidence level: this completed research proposal at design-proposal evidence only; no DSP source, build, app, device, or listening result
> Decision gate: proposal review is required before any implementation bundle or DSP implementation work.

## 1. Product thesis

### One-sentence thesis

The strongest new instrument is **Murmur Map**: the performer places four to
eight playable sound states on a small map, then steers a seeded route that can
wander, slowly mutate, or lock into a repeatable cycle while three voices turn
the route into audible counterpoint.

### Instrument identity

Murmur Map is an authored-state instrument, not a modular emulator. The
performer creates a few waypoints by shaping pitch, activity, timbre, envelope,
level, and stereo position, and places those waypoints on a two-dimensional
field. The instrument travels between them. Continuous sound properties blend
with the current map position; discrete note and event choices are made only at
semantic event boundaries. The performer can pull the route home, favor local
or distant transitions, let stored decisions erode, or lock the current route.

The core gesture is therefore: **make places, set the machine walking, recognize
a route, and decide how much of it to keep**. That is a distinct performance
identity and a better use of a JUCE screen than reproducing Eurorack knobs and
patch cables.

### Intended user and musical situation

A musician making evolving melodic or textural material who wants more agency
than a randomizer and less editing than a piano roll. The first target is a
private, noncanonical desktop audition instrument suitable for exploratory
playing and deterministic offline comparison.

### In scope

- Research into modular techniques that balance variation, memory, and direct
  performance control, including Mutable Instruments modules.
- Six materially different JUCE instrument concepts and a ranked recommendation.
- A full proposal for one recommended vertical slice, including state, timing,
  controls, equations, resource assumptions, objective renders, and a listening
  gate.
- A new-design composition that may reuse the repository's existing authenticated
  Braids physical closure and narrow adapter if the later implementation bundle
  selects that dependency exactly.
- A JUCE-independent musical Core; JUCE remains an optional audio, MIDI, and UI
  adapter.

### Out of scope

- Copying a Mutable Instruments panel, brand, manual artwork, firmware UI, or
  undocumented behavior.
- Importing Marbles, Frames, Stages, Tides, Rings, Beads, Grids, or any new
  upstream source closure during this proposal.
- Another drum machine, resonator-led instrument, gated drone, or live sampler;
  Schuss already has strong experiments in those areas.
- A generic modular graph editor, arbitrary patch-cable runtime, canonical
  Schuss records/providers, Ksoloti/Gills execution, VST3 packaging, Ableton
  installation, app launch, endpoint access, physical controller work,
  real-time certification, listening claims, distribution, or publication.

## 2. Inputs, constraints, and decision rights

### Inputs and assumptions

- `docs/STATUS.md` reports no active task. Tasks 043 through 047 are complete
  but remain uncommitted in the inherited worktree; this proposal does not
  modify them.
- Instrument Lab is a non-production path from an approved proposal and ready
  bundle to a portable Core, objective renderer, and optional authenticated
  JUCE target. It does not own the musical design.
- The repository already authenticates JUCE 8.0.15 at commit
  `91ad83ae34a81e0833b1a2b0866f54846370ae53` and archive SHA-256
  `04f8d5055382582c757be9da069ea98338005f98248facd9c2804435ac853e70`.
- The repository already has exact, reusable physical closures for selected
  Braids and stmlib files plus the narrow
  `schuss::dsp::mutable_braids_v1::Voice` adapter. That authority establishes
  source identity and prototype build closure only; it is not catalog,
  provider, real-time, audible, distribution, or production approval.
- The current adapter exposes six selected source models: kick, snare, cymbal,
  sine/triangle, FM, and filtered noise. The Murmur Map experiment would use
  only sine/triangle, FM, and filtered noise, with one persistent voice per
  musical lane.
- Mutable Instruments' repository declares STM32F code under MIT and asks
  derivative works not to use Mutable Instruments names. Exact dependency and
  notice closure still requires a task-specific review before any new source
  is consumed or any binary is distributed.

### Deliverables

1. This evidence-labelled Markdown study.
2. Seven patch recipes that can be tried in a modular system.
3. Six ranked JUCE instrument concepts with overlap, feasibility, and failure
   risks.
4. An implementation-ready *proposal* for Murmur Map, stopping before the
   implementation bundle and DSP source.

### Acceptance tests

- At least five first-party modular sources and three software/research peers
  support the mechanism comparison.
- Each candidate has a distinct performer gesture, sound engine, generative
  mechanism, smallest experiment, and reason it is not an existing Schuss
  instrument under another name.
- The recommendation has fixed capacities, executable control equations,
  update timing, gain bounds, state operations, failure behavior, a literal
  comparator, deterministic seed, and explicit evidence limits.
- Source facts, inference, hypotheses, and unresolved decisions remain separate.
- No existing workspace file is edited, staged, committed, launched, installed,
  or published.

### Decisions this work may make

- Rank the candidate instruments.
- Recommend Murmur Map revision 0.1 and define the smallest experiment that
  could falsify its central musical claim.
- Select a prototype-only dependency *candidate* and a bounded evidence ceiling.

### Decisions this work must not make

- It may not activate a numbered task, approve implementation, allocate stable
  identities, extend a source release, select a production provider/backend,
  claim trademark rights, approve distribution, or promote source/build evidence
  to real-time, device, listening, or production evidence.
- It may not make Mutable Instruments ancestry a function category or graph
  identity.

### Working definition

| Artifact | Evidence level | Required observation | Explicitly not implied |
|---|---|---|---|
| `research/proposals/modular-generative-juce-instrument-study.md` | Design proposal | Complete candidate comparison, source ledger, frozen Murmur Map hypothesis, and decision gate | DSP correctness, a build, app launch, sound quality, or implementation approval |
| If later approved: `murmur_map_core` plus retained route/event traces and stereo WAVs | Host-signal/offline | Same semantic traces and PCM for the exact seed/control history across supported block partitions and fresh processes | Live callback headroom, app/device behavior, listening preference, distribution, or canonical integration |
| If later approved: authenticated `Murmur Map.app` | Target build | Exact JUCE tree authenticates and the target compiles/links | App launch, visual QA, endpoints, controller receipt, real-time safety, or audible quality |

## 3. Reference anatomy

### What the useful modular patches are doing

| Patch | Modular signal path | Observable lesson | Primary evidence | Keep, transform, or reject |
|---|---|---|---|---|
| **Looping chance trio** | Master clock into Marbles; `t1/t3` trigger contrasting voices; `X1/X2/X3` provide pitch or timbre; slow `Y` self-modulates bias, spread, or memory | Randomness becomes musical when timing, voltage distribution, quantization, and replayable decisions are independently steerable | [Marbles manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/manual/) | Keep memory-versus-novelty and independent streams; reject panel emulation |
| **Keyframe weather** | Four audio/CV sources into Frames; Tides or another slope generator drives FRAME CV; FR.STEP triggers phrase changes | A performer can author a few meaningful states and animate between them; crossing a state can also be an event | [Frames manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/frames/manual/) | Expand one-dimensional keyframes into a small two-dimensional authored map |
| **Segment ecosystem** | Stages segments are grouped as envelopes/sequences/LFOs; one free-running segment modulates another segment's time or shape; activity signals trigger voices | One small set of components can change function through grouping, looping, and self-patching | [Stages manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/stages/manual/) | Use as the basis of a separate coupled-contour instrument |
| **Clocked ratio lattice** | Tides follows a clock; four outputs run with shifted phase or frequency ratios; sharp low-frequency edges trigger downstream voices | One process can produce related polyrhythms, envelopes, or just-intonation tones across time scales | [Tides 2018 manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/tides_2018/manual/) | Keep for a phase-coupled instrument; deprioritize because Wirefall already occupies drone territory |
| **Probabilistic strum tree** | A master trigger is split through one or more Bernoulli gates; a looping pitch source feeds voices; routed events strum separate timbres or a resonator | Probability is most legible when it routes a known event between alternatives instead of inventing every event | [Branches manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/branches/manual/), [Rings manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/rings/manual/) | Keep mutually exclusive routing; use non-resonator voices in the first candidate to avoid Cinderwheel overlap |
| **Granular clock garden** | Audio into Beads; clock into SEED; a sequence addresses TIME and PITCH; FREEZE captures the buffer; controlled randomization varies later grains | Grain parameters are sampled at grain birth, so a changing control leaves an audible trail rather than dragging all active grains together | [Beads manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/beads/manual/) | Keep birth-time state and memory erosion for a later texture instrument; deprioritize due Layerwell overlap |
| **Topographic rhythm morph** | Slow CV moves Grids X/Y while separate modulation changes channel fill/chaos; triggers address contrasting voices | A low-dimensional map plus per-lane density can traverse a large authored pattern collection coherently | [Grids manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/grids/manual/) | Generalize the map idea from drum patterns to performer-authored sound states; reject another drum implementation |

### Cross-reference anatomy

| Function | Observable behavior | Evidence | Design implication | Confidence |
|---|---|---|---|---|
| Controlled randomness | Marbles shapes clock jitter, trigger routing, voltage distribution, smoothing/quantization, and replay probability separately | First-party manual | Never expose one vague `RANDOM` amount; separate route, memory, density, and pitch constraints | High |
| Loop erosion | Marbles and the Turing Machine both move between changing material and locked loops | First-party manuals | Make the lock state exact and visible; slow mutation must operate on stored semantic decisions | High |
| Authored interpolation | Frames stores keyframes and provides several interpolation curves; external CV can scan or step them | First-party manual | Store musical states, not raw pixels or host controls; continuous and categorical fields need different laws | High |
| Related multi-rate motion | Tides creates phase/frequency-related outputs and can lock to irregular repetitive clocks at low rates | First-party manual | Generate related lanes from one musical timeline instead of free-running host timers | High |
| Functional regrouping | Stages changes from independent functions to grouped multi-segment shapes according to grouping and loop state | First-party manual | A separate contour instrument can expose reconfiguration as the main gesture | High |
| Birth-time capture | Beads freezes parameters per grain; event-sourced systems separate decisions from projections | First-party manual | Event state should be frozen at the event, not reread inconsistently during a voice lifetime | High |
| Resonant excitation | Rings separates trigger, pitch, and excitation and can synthesize a fallback exciter | First-party manual | Resonator concepts must specify all three domains; source similarity does not prove algorithm identity | High |
| Smooth/stepped/burst uncertainty | Wogglebug exposes several correlated random signals plus clock, PLL, lag, and disturbance | [Make Noise Wogglebug product/manual page](https://www.makenoisemusic.com/modules/wogglebug/) | A family of related uncertainty signals is more performable than unrelated PRNG calls | Medium-high |

## 4. Adjacent landscape

### Candidate JUCE instruments

| Rank | Working title | Patch DNA | Performer gesture and response | Smallest meaningful experiment | Why it is distinct in Schuss | Main risk / estimated effort |
|---:|---|---|---|---|---|---|
| **1** | **Murmur Map** | Frames + Marbles/Turing memory + Grids-like 2D locality | Place 4–8 sound waypoints, watch and steer a route, then lock or erode its remembered transitions | Four fixed waypoints, three fixed voices, 16-transition memory, route/event trace, 60–90 s renders | Melody/control-space instrument; not drums, resonator counterpoint, drone, or sampling | Interpolation may sound like parameter soup; medium effort, best JUCE payoff |
| **2** | **Relay Bloom** | Branches + constrained permutations/change ringing | Four voices continually exchange order; `CALL` changes the allowed adjacent swaps and `CHANCE` decides when | Four simple FM voices, one chord, adjacent-swap rows, deterministic route trace | Orchestration/permutation is primary; no existing Schuss instrument does that | Can feel like an arpeggiator; low-medium effort |
| **3** | **Contour Colony** | Stages + Tides + Wogglebug-style related motion | Group six slope cells, let activity in one bend another, and move between envelope, LFO, and audio-rate behavior | Four cells with fixed-capacity coupling matrix and two audio-rate cells | A reconfigurable modulation/synthesis organism, not a fixed drone | Stability and comprehensibility; high effort |
| **4** | **Tidal Lattice** | Tides ratio outputs + weak oscillator coupling | Tune four related cycles, increase coupling until phase coincidences create rhythms/chords, then disturb the lock | Four phase accumulators, rational ratios, one weak-coupling term, coincidence events | Phase relation is the instrument; more harmonic than Wirefall | Drone overlap and aliasing; medium effort |
| **5** | **Thread Memory** | Turing/Marbles loop memory + Beads birth-time grains | Feed or generate a sound, let a 16-slot decision tape choose grain age/pitch/size, then freeze or fray it | Internal source, 2 s buffer, 12 grains, one loop-erode control | Granular decision memory rather than Layerwell's explicit captured layers | Buffer/state/plugin-input complexity and sampler overlap; medium-high effort |
| **6** | **Cell Weather** | Grids map thinking + cellular automata | Paint a small cell field; local births/deaths become note, density, and timbre gestures while macro controls change the rule family | 8x8 binary automaton with three readout paths and deterministic mapping | Rule-field composition rather than authored rhythm studies | Extensive musical prior art and weak steering; medium effort but highest musical risk |

### Product and software peers

| Product or project | Type | Relevant mechanism | Distinguishing behavior | Source | Design implication |
|---|---|---|---|---|---|
| Music Thing Modular Turing Machine | Hardware/open program | Shift-register-like random looping sequence with variable loop length and gradual locking | The player steers a changing pattern until it is worth keeping; changes are intentionally irreversible in the original workflow | [Official Workshop Computer program](https://computer.musicthing.co.uk/programs/03-turing-machine/index.html) | Memory should be a performance decision, not hidden preset generation |
| VCV Audible Instruments | Software modular collection | Direct software versions based on MI modules including Frames, Stages, and Marbles | Faithful module-level modular workflow already exists | [VCV Library](https://library.vcvrack.com/AudibleInstruments) | A JUCE instrument should compose mechanisms into a new gesture, not compete as a rack clone |
| Stochas | Open-source JUCE sequencer | Per-step probability, polyrhythm, chain conditions, scale-aware MIDI | Deep grid editing and MIDI generation, but no sound engine | [Project introduction](https://stochas.org/stochas/), [source](https://github.com/surge-synthesizer/stochas) | Avoid another probability piano roll; integrate generation and sound consequence |
| Wotja | Generative software system | Separate scale, harmony, next-note, rhythm, pattern, and cell rules | Broad rule-authoring environment and multi-cell composition | [Current guide](https://wotja.com/pdf/wotja_com_guide.pdf) | Murmur Map should remain a small instrument, not a general rule language |
| Nodal | Research/composition software | Musical agents traverse a user-created graph whose nodes emit events | Explicit graph authoring balances emergence and composer control | [Generative Composition with Nodal](https://www.researchgate.net/publication/228749312_Generative_Composition_with_Nodal) | Graph traversal in music is established prior art; the proposed contribution must be interaction and state integration, not “a novel graph walker” |
| Graphical synthesizer interpolators | Research/software class | Presets placed in a 2D pane and interpolated at a cursor | Known sounds constrain an otherwise complex parameter space | [SMC 2019 framework](https://eprints.bournemouth.ac.uk/32726/) | The 2D sound map is established; test whether looping route memory makes it a performable instrument |
| Eurorack/VCV generative case study | Academic modular patch | Marbles + Stages + Branches drive two Plaits voices | The exact broad combination of random sequence, structural modulation, probability filtering, and macro voices has already been studied | [Open-access paper](https://openresearch.lsbu.ac.uk/download/a5539e9bd69095d8095352784d38ca632eec62b88aa14036566c4f6143f39629/267054/Eurorack-VCV_Rack_Randell_Rietveld_v3d-final-Open-Access.pdf) | Do not claim novelty for merely putting those modules in one software instrument |
| Existing Schuss audition library | Local prototypes | Cinderwheel, Pamplist, Generative Drums, Tide Pit, Wirefall | Resonator, percussion, mutation, drone, and sampler territory already exists | `research/prototype_support/instrument_library/audition-library-v2.json` | Favor melodic control-space and orchestration concepts |

## 5. Synthesis and engineering research

| Paper, source, or standard | Mechanism | Evidence strength | Applicability | Limitation |
|---|---|---|---|---|
| Tong, Faloutsos, and Pan, *Random Walk with Restart: Fast Solutions and Applications* | A walker follows graph links but returns to a query/home node with a restart probability | Primary computer-science paper | Gives `HOME` a precise meaning and a stationary tendency instead of vague random bias | Designed for graph proximity, not musical timing or subjective quality; [paper](https://www.cs.cmu.edu/~htong/pdf/KAIS08_tong.pdf) |
| O'Neill, *PCG: A Family of Simple Fast Space-Efficient Statistically Good Algorithms for Random Number Generation* | Small-state generator combining an LCG state transition and output permutation | Author technical report and reference material | Candidate deterministic PRNG with explicit state and stream selection | Statistical quality does not establish musical quality; [paper page](https://www.pcg-random.org/paper.html) |
| McCormack et al., *Generative Composition with Nodal* | State-based musical agents traverse a user-authored graph | Primary system paper | Direct prior art for graph-based semi-generative composition | Nodes are event-oriented; Murmur Map additionally binds route position to continuous sound-state interpolation |
| McPherson et al., *A Framework for the Development and Evaluation of Graphical Interpolation for Synthesizer Parameter Mappings* | Evaluation framework for 2D preset maps and interpolation | Primary conference paper | Supports a bounded map UI and warns that interpolation choice matters | Does not solve categorical parameter changes or generative traversal |
| Le Vaillant and Dutoit, synthesizer preset interpolation research | Parameter interpolation can be perceptually irregular; categorical/routing parameters are a special problem | Peer-reviewed paper/thesis | Justifies event-boundary categorical choice and forbids blindly averaging model IDs or scale choices | Neural latent interpolation is outside the minimal experiment; [2024 record](https://orbi.umons.ac.be/handle/20.500.12907/49507) |
| Burraston et al., *Cellular Automata in MIDI based Computer Music* | Automata state/history can be mapped to MIDI with user-defined mappings | Primary ICMC paper | Prior art and warning for Cell Weather | CA behavior alone is not a usable instrument; mapping dominates; [paper](https://quod.lib.umich.edu/cgi/p/pod/dod-idx/cellular-automata-in-midi-based-computer-music.pdf?c=icmc%3Bidno%3Dbbp2372.2004.047%3Bformat%3Dpdf) |
| Mutable Instruments Eurorack repository | Published module source and repository-level license/trademark guidance | First-party source repository | Lawful candidate reference or dependency after exact closure review | Repository-level license summary does not replace per-closure validation; [repository](https://github.com/pichenettes/eurorack) |
| Current Schuss Braids/stmlib packages and adapter | Exact selected source bytes, notice files, and six-model C++17 adapter | Exact local retained authority | Murmur Map can test the control concept without importing a parallel source shelf | The adapter is not a provider or distribution approval; `contracts/task038/source-release-01.json`, `packages/dsp_sources/mutable_eurorack_braids_v1/SOURCE_PACKAGE.json`, `packages/dsp_adapters/mutable_braids_v1/ADAPTER.json` |
| Existing Generative Drums results | Four Braids voices, deterministic multi-block renders, and bounded synthetic callback-kernel measurements on the M1 Pro | Exact local retained evidence for a different instrument | Makes a three-voice prototype plausible | Does not prove Murmur Map cost, live real-time behavior, or listening quality; `research/prototypes/generative-drum-machine/contract/RESULTS.md` |

## 6. Musical-practice research

Only Relay Bloom uses a situated practice as a structural influence. Murmur Map
does not need a cultural identity claim.

| Named practice, community, place, and period | Source and source relationship | Structural principle | Possible translation | Context or restriction | Decision / risk |
|---|---|---|---|---|---|
| English method ringing in tower-bell communities, England and later international communities, seventeenth century to present | The Central Council of Church Bell Ringers' living framework defines rows, changes, methods, and compositions; academic work documents computational use | Each row is a permutation; successive changes transform the order under constraints; structured variation returns to known states | Relay Bloom lets four synthesis voices exchange adjacent positions; a probabilistic `CALL` selects from bounded legal changes | Do not copy bell recordings, named methods, place notation, religious framing, community identity, or claim the result performs change ringing. Attribution remains required. Practitioner review would be needed if the cultural identity became product-facing. | Use only the adjacent-exchange principle in a neutral research prototype; [Central Council framework](https://framework.cccbr.org.uk/edition1/fundamentals.html), [computer-composition prior art](https://www.tandfonline.com/doi/abs/10.1080/09298217908570271) |

The abstraction loses the embodied coordination, acoustics, social learning,
and communal function of ringing. Relay Bloom would therefore be *influenced by
the permutation constraint*, not a digital bell-ringing instrument.

## 7. Computer-science transfer search

| Concept and home field | Existing audio prior art found | Proposed mapping | Musical benefit | Failure mode | Falsifying experiment |
|---|---|---|---|---|---|
| Random walk with restart / graph mining | Nodal uses graph-walking musical agents; Markov systems and graph sequencers are common | Waypoints are graph nodes; `HOME` is literal restart probability; distance-weighted transitions define locality | The route can explore while retaining a performer-chosen center | It behaves like an opaque Markov arpeggiator | Compare map route against matched independent scene draws; fail if route gestures are not audible or preferred |
| Replay buffer with probabilistic replacement / streaming memory | Turing Machine and Marbles are strong musical prior art | A fixed ring stores destination waypoint IDs; `MEMORY` is the probability of replaying a stored destination instead of replacing it | Exact lock, gradual erosion, and repeatable seed behavior share one transparent state model | The loop is either obvious or changes too quickly to recognize | Render memory values 0, .5, .9, and 1; fail if measured recurrence is not ordered or listeners cannot distinguish lock from fresh chance |
| Radial-basis interpolation / spatial mapping | Frames, graphical preset interpolators, vector synths, and learned latent maps are prior art | Gaussian weights blend continuous semantic parameters around the route position | The map has an audible geography and user-authored landmarks | Averaging unrelated patches yields bland or unstable sound | Move one waypoint while replaying an identical locked route; fail if the affected region is not localized or categorical zippering occurs |
| Birth-time snapshots / event systems | Beads freezes parameters per grain; event-sourced systems separate decisions from projections | Each note event snapshots pitch, model-independent timbre targets, envelope, pan, and level; active voices do not reread scene selection | A moving map leaves articulated trails rather than smearing active notes | Abrupt event discontinuities click or sound arbitrary | Stress waypoint crossings and rapid route changes; require bounded discontinuity bridge and zero clip/non-finite events |
| Cellular automata / discrete dynamical systems | Extensive ICMC and commercial/research prior art exists | Cell Weather maps local field activity to three voice lanes | Rich deterministic complexity from small rules | Mapping is harder to play than the automaton is to implement | Build only if a paper prototype lets users predict macro changes after two minutes; otherwise reject |

## 8. Novelty map

### Common elements

- Seeded random or probabilistic note/event generation.
- Looping random sequences with a memory or mutation amount.
- Preset/keyframe interpolation and two-dimensional sound maps.
- Graph- or Markov-based event traversal.
- Macro-oscillator voices, resonators, granular buffers, and cellular automata.

### Less-common combinations found

- Frames already combines authored interpolation with keyframe-crossing pulses.
- Marbles combines clock variation, trigger routing, correlated voltages,
  quantization, and replayable random choices.
- Grids combines a two-dimensional map with density-controlled event extraction.
- Nodal combines user-authored graph structure and wandering musical agents.
- Existing research explicitly patches Marbles, Stages, Branches, and Plaits.

### Proposed contribution

The bounded contribution is not a new random walk or a new interpolation
algorithm. It is the **instrument interaction contract**:

1. the performer authors a small geography of complete musical states;
2. the route through that geography is a visible semantic state;
3. route destinations live in a replay/replace memory ring with an exact lock;
4. continuous parameters interpolate by position while discrete pitch/event
   decisions snapshot only at event boundaries; and
5. the same route state drives sound, UI feedback, deterministic renders, and
   recall semantics.

Searches run on 2026-08-25 included `synthesizer random walk preset morph`,
`audio plugin random walk with restart music`, `generative synthesizer 2D sound
map random walk scene interpolation`, `modular synth random walk keyframe
morphing Frames Marbles`, graph-agent composition, graphical preset
interpolation, cellular-automata music, VCV Audible Instruments, Stochas, and
Wotja. Frames, Nodal, graphical interpolators, Markov systems, and a recent
random-walk/cellular generative synth were found. The exact interaction above
was **not found in this bounded search**; that is not a global novelty claim.

### Rejected or deferred directions

| Direction | Reason rejected or deferred | Evidence or risk |
|---|---|---|
| Direct Marbles/Frames/Stages clone | VCV already supplies faithful module-shaped software; a clone would have weak product identity | VCV Audible Instruments and MI manuals |
| Another Grids-derived drum instrument | Pamplist and Generative Drums already cover authored/generative percussion; Grids-like map extraction is established | Local audition library and Grids manual |
| Resonator-first rain/chime instrument | Attractive patch, but Cinderwheel already owns resonant counterpoint territory | Local audition library |
| Granular capture first | Beads provides rich inspiration, but Layerwell already occupies explicit live-sampling territory and new input/buffer state raises scope | Beads manual and Task 044 status |
| Cellular automata as recommendation | Extensive prior art; results depend more on mapping than the automaton, and steering is hard to explain | ICMC research |
| Neural latent preset interpolation | Training data, model runtime, nondeterminism, and source/asset closure obscure the central interaction hypothesis | Preset-interpolation research; unnecessary for the four-waypoint experiment |
| Generic modular patch environment | Violates the bounded instrument goal and duplicates Schuss graph-authoring concerns | Project architecture |

## 9. Recommended architecture: Murmur Map 0.1

### Signal flow

```text
accepted UI / semantic actions
        |
        v
waypoint store (2..8) ---- selected HOME waypoint
        |                         |
        +----> weighted complete transition graph
                              |
PCG32 semantic draws -------->+--> destination memory ring (2..32)
                                   | replay or replace by MEMORY
                                   v
                         raised-cosine edge traveler
                                   |
                     2D position + node-arrival events
                                   |
               Gaussian semantic-state interpolation
                    |                              |
          continuous targets              event-boundary snapshots
                    |                              |
                    +----------> three fixed voice lanes
                                  anchor / thread / spark
                                             |
                   selected authenticated Braids adapter candidates
                       sine-triangle / FM / filtered-noise
                                             |
                    envelopes + discontinuity bridges + stereo pan
                                             |
                         bounded sum -> DC block -> stereo out
```

The DSP topology remains instrument-owned and transparent. Waypoints are not
presets for a JUCE graph; they are bounded semantic data consumed by one
portable Core.

### Fixed model and capacities

- Waypoints: minimum 2, maximum 8; four defaults.
- Waypoint coordinate: `x,y` each in `[0,1]`.
- Destination memory: 2 to 32 node IDs; default 16.
- Voices: exactly three persistent monophonic lanes: `anchor`, `thread`, and
  `spark`.
- Pending semantic events: 64 per block; excess events are rejected and counted,
  never allocated dynamically.
- Maximum host block: 512 frames.
- Route trace presented to UI: latest 64 accepted positions via a bounded
  audio-to-UI snapshot/mailbox, never direct shared mutation.
- PRNG: one explicit PCG32 state/stream for route destinations plus one derived
  per-lane stream for event choices. Random draws occur only at semantic ticks
  or node arrivals, never once per host callback.

### Executable DSP contract

| Mechanism | Equation or pseudocode | Coefficients/ranges | Gain and stability bound | Update timing | Failure behavior |
|---|---|---|---|---|---|
| Transition weights | For current node `i`, compute `q_j = exp(-d(i,j)/T)` for `j != i`; draw `u_home,u_route`; if `i != HOME` and `u_home < H`, select HOME, otherwise sample normalized `q` with `u_route`; ties use node ID order | `T = 0.05 * 40^ROAM`, `ROAM in [0,1]`; `H in [0,1]`; exactly two route-stream draws per fresh destination, including the HOME branch | Normalize in double; if sum is non-finite or `<= 0`, choose lowest valid `j != i`; no fresh self-edge | At each node arrival when a fresh destination is required | Reject invalid coordinates transactionally; deterministic fallback and diagnostic on numeric failure |
| Memory ring | At slot `h`: if valid and `u < M`, reuse `ring[h]`; else generate destination and replace; `h=(h+1) mod L` | `M in [0,1]`; exact lock at `M=1`; fresh decisions at `M=0`; `L in [2,32]` | Stores validated node IDs only; deleting a node rewrites its slots to HOME at the next block boundary | Once per route transition | Invalid stored ID resolves to HOME and increments repair counter; no out-of-range access |
| Edge travel | `s = clamp((tick-start)/duration,0,1)`; `e(s)=0.5-0.5*cos(pi*s)`; `p=(1-e)a_i+e a_j` | Edge duration `D = B * (0.5 + d(i,j))`; `B` is 0.25 to 8 quarter notes, logarithmic | Position is convex and remains inside `[0,1]^2`; exact arrival at `s=1` | Route phase advances on an absolute Q32 musical timeline; position updates every 1/64 quarter note and at exact arrival | Invalid tempo/duration rejects control transaction; phase overflow is checked and fails silent |
| Scene weights | `r_i=exp(-||p-a_i||^2/(2R^2)); w_i=r_i/sum(r)` | `R in [0.05,1]`, default 0.28 | `w_i >= 0`, sum is 1 within double epsilon; if underflow, nearest waypoint gets weight 1 | Control-rate update at 1/64 quarter; per-sample smoothing consumes targets | Non-finite waypoint field rejects state; underflow fallback is deterministic |
| Continuous semantic blend | Interpolate normalized timbre, color, activity, decay-log, level-dB, and pan targets: `c=sum(w_i*c_i)`; map to DSP domains after interpolation | Timbre/color/activity `[0,1]`; decay 40 ms..4 s in log domain; level -60..-6 dB; pan `[-1,1]` | Parameter targets clamp to declared ranges; one-pole/linear 128-sample slew prevents steps | New target at control tick; slew every output sample | Non-finite target holds last accepted value and latches diagnostic |
| Event snapshot | At a lane tick, draw waypoint index from `w`; snapshot that waypoint's pitch offset and the current interpolated continuous targets; fire if `u < Density * activity_lane` | Global density `[0,1]`; pitch offsets integer `[-24,+24]`; root MIDI note 24..84; fixed nine-choice scale enum | Pitch clamps to MIDI 12..108 before adapter conversion; event payload is immutable after creation | Anchor on node arrival; Thread every 1/2 quarter; Spark every 1/4 quarter with activity gate | Queue overflow drops newest event, increments counter, and never corrupts prior events |
| Voice lane | Persistent fixed model per lane: anchor=sine/triangle, thread=FM, spark=filtered noise; on event set pitch/parameters, strike, and restart envelope | Source adapter `int16` domains derived from normalized values; fixed model in revision 0.1 | 48-sample old-tail bridge on retrigger; envelope max 1 | Events applied before rendering the event's exact output sample; source renders at its required rate if selected | Missing/authentication-failed source dependency fails configuration; render rejection clears host output |
| Envelope | Attack 1 ms, exponential decay from snapshot; `g[n+1]=g[n]*exp(-1/(tau*Fs))` after attack | `tau` 40 ms..4 s; attack exactly 48 host frames at 48 kHz | `0 <= g <= 1`; denormals flushed by explicit floor at `1e-7` | Per sample | Invalid coefficient silences that voice and latches fault |
| Stereo pan/mix | Equal-power `L=cos(pi*(pan+1)/4)`, `R=sin(...)`; each lane contributes `0.24 * level * envelope * source` | Per-lane ceiling 0.24; three lanes | Pre-DC-block absolute worst-case sum <= 0.72 for normalized sources; final hard bound `[-0.98,0.98]` counts any clamp | Per sample | Any non-finite intermediate clears the complete output block and latches fault |
| DC blocker | `y[n]=x[n]-x[n-1]+0.995*y[n-1]` per channel | `R=0.995` at 48 kHz | Stable because `|R|<1`; state clears on reset | Per sample | Non-finite state clears both channel states and current block |

The selected Braids models are a prototype dependency candidate, not the
identity of Murmur Map. If the ready-bundle audit shows that source-rate
conversion or global RNG behavior would dominate the experiment, revision 0.1
must instead use project-owned sine, two-operator FM, and filtered-noise voices
with the same public topology. That choice is frozen before DSP edits, not made
mid-implementation.

### State and timing model

- Host audio is stereo, 48 kHz, blocks 1 through 512 frames. Other rates are
  outside revision 0.1 rather than silently resampled.
- The absolute sample interval is half-open: a block processes
  `[block_start, block_start + frames)`. An event at `block_start` is applied
  before that sample; an event exactly at the end belongs to the next block.
- GUI continuous controls publish one coherent bounded snapshot and become
  accepted at the next block boundary. Sample-offset semantic actions supplied
  by a tested host adapter retain their exact offset.
- Musical phase is persistent Q32 quarter-note time with carried integer
  remainder. Changing tempo preserves route phase; changing route length takes
  effect at the next node arrival.
- Random state advances only for a named semantic decision. Therefore changing
  the host block partition cannot change route or note choices.
- **Reset:** restore the four default waypoints, seed, route ring, HOME, route
  phase, voice state, diagnostics, and output history.
- **Panic:** clear voice/envelope/DC states and pending audio events, but keep
  route, seed, waypoints, and phase. New events may sound afterward.
- **Run false:** stop route and event phase at the next block boundary while
  existing tails decay; resume from the preserved phase.
- **Lock:** set accepted `MEMORY=1` without rewriting the ring. Unlock restores
  the prior non-unity memory target.
- **Reseed:** at the next node boundary, replace PRNG states, invalidate the
  route ring, choose HOME as the current node, and start a fresh route. Existing
  audio tails continue.
- **Capture/replace waypoint:** copy accepted semantic edit controls into the
  selected waypoint at the next block boundary. Raw pointer, mouse, or MIDI
  values never become authoritative state.
- **Delete waypoint:** transactionally remove the selected node and repair
  memory slots to HOME. Deletion is rejected when only two nodes remain.
- **Recall:** revision 0.1 is reset-boundary equivalent, not sample-continuous.
  A recalled state restores waypoints, controls, seed, route ring/head, current
  and destination nodes, and normalized travel phase, then reconstructs fresh
  voices and resumes at the next block boundary with tails cleared.
- **State-equivalence rule:** after transactional recall followed by the same
  reset-boundary start and future semantic event sequence, route/event traces
  and PCM must be byte-identical on the authenticated environment. Arbitrary
  mid-tail sample-continuous equivalence is explicitly not claimed.
- **Endpoint reconnect:** no Core state change. Physical endpoint selection and
  reconnect behavior are outside this revision.
- **Non-finite recovery:** reject non-finite control/state transactions; if a
  non-finite value appears inside processing, clear the full output block and
  latch a fault until Reset.

### Control and performance mapping

| Control or gesture | Range or states | DSP mapping | Perceptual role | Safety or pickup behavior |
|---|---|---|---|---|
| `RUN` | off/on | Gate route/event timeline; tails remain active | Start and stop growth without losing place | Accepted only at block boundary |
| `TEMPO` | 30..240 BPM | Q32 quarter-note increment | Global pace | Log/linear UI mapping; clamp before publish |
| `TRAVEL` | 0.25..8 quarters base | Edge duration `B` | Fast darting to slow migration | Logarithmic; no zero duration |
| `MEMORY` | 0..1 | Probability of reusing each stored destination | Fresh chance through slow erosion to exact loop | Virtual notch/indicator at exactly 1; accepted state shown |
| `LENGTH` | integer 2..32 | Active destination-ring length | Phrase span | Changes at next node arrival |
| `ROAM` | 0..1 | Transition temperature `T` | Local wandering to broad jumps | Smoothed as semantic target; affects only fresh decisions |
| `HOME` | 0..1 | Random-walk restart probability | Gravitational pull toward selected landmark | At `1`, a fresh decision returns to HOME whenever the current node differs; from HOME it samples a non-self destination; stored route still replays if MEMORY says so |
| `RADIUS` | 0.05..1 | Gaussian scene influence width | Isolated islands to blended continent | Clamp; nearest fallback |
| `DENSITY` | 0..1 | Multiplies lane activity probability | Sparse to busy | Exact zero forbids all new events and must render silence after tails expire |
| `ROOT` | MIDI note 24..84 | Adds to waypoint interval | Register | Integer only; event-boundary update |
| `SCALE` | Chromatic, Major, Natural Minor, Dorian, Mixolydian, Major pentatonic, Minor pentatonic, Whole tone, or Octatonic half-whole | Quantizes root + waypoint offsets to the nearest member; an exact-distance tie chooses the lower pitch | Pitch vocabulary | Enum validated transactionally; Minor pentatonic is the default |
| Map drag | accepted waypoint `x,y` in `[0,1]` | Changes graph distances and interpolation field | Compose geography | UI proposal shown immediately, accepted Core position shown distinctly |
| Waypoint edit | per-lane activity, interval, timbre, color, decay, level, pan | Edits pending semantic waypoint state | Compose what each place means | `CAPTURE/REPLACE` required; no accidental write-through |
| `CAPTURE/REPLACE` | action | Transactional waypoint update | Commit a sound place | Disabled unless pending state validates |
| `HOME HERE` | action | Select current waypoint as restart node | Establish center | Node ID from accepted selection only |
| `LOCK/UNLOCK` | action | Store prior memory, force exact 1, or restore | Catch/release a route | Button reflects accepted lock state |
| `RESEED` | action | Deferred boundary reseed and ring invalidation | Deliberately abandon the current route | Confirmation/press gesture; no hidden automatic reseed |
| `PANIC` | action | Clear sounding state only | Immediate silence | Always available; accepted counter visible |

No physical Launch Control 3 map is selected by this proposal. A later bundle
may reuse its authenticated topology, but map dragging, waypoint capture, and
accepted-state feedback make the JUCE surface the primary revision 0.1
controller. Any hardware mapping must target these public facets, not DSP nodes.

### Parameter interactions and edge cases

- `MEMORY=1` repeats the stored node-ID cycle exactly even if `ROAM` or `HOME`
  moves; those controls affect only future fresh/replaced decisions.
- `MEMORY=0` ignores valid slots and replaces each one. The ring remains visible
  so turning memory upward immediately begins preserving recent decisions.
- A replayed destination may equal the current node after ring wrap or a graph
  edit. This is a legal dwell: distance is zero, duration is `0.5 * B`, route
  position remains exact, and the arrival event still occurs. Fresh decisions
  never create self-edges.
- `HOME=1` is not a stuck state: a fresh choice away from HOME is required while
  already at HOME, and the next fresh choice from any other node returns HOME.
- Moving a waypoint during a locked route changes geometry and timbre without
  changing destination IDs. This is an intended performance gesture and must
  not consume PRNG state.
- Deleting the HOME node selects the lowest remaining node ID as HOME before
  route-slot repair.
- At small `RADIUS`, the nearest-scene fallback prevents silence or NaN between
  distant nodes. At large `RADIUS`, the UI warns that the map is broadly mixed.
- Categorical scale, root, node IDs, and fixed voice models never interpolate.
- The filtered-noise spark lane ignores pitch perceptually if its source model
  does; its pitch field still remains a valid, bounded event value for trace
  parity and possible native-source substitution.
- With `DENSITY=0`, no new events occur. `Panic` plus density zero is exact
  immediate silence; density zero alone allows existing tails to decay.
- If all waypoint lane activities are zero, the route still advances visibly
  but generates no new audio.

### Failure behavior

- Invalid waypoint count, duplicate node ID, non-finite coordinate/control,
  unknown enum, unsupported sample rate, or stale dependency authority fails
  closed with a stable diagnostic. The last accepted state remains intact.
- Oversized blocks, null buffers, arithmetic overflow, non-finite audio, or an
  impossible event capacity clear the complete output block and increment a
  diagnostic counter.
- No audio-thread path allocates, locks, performs file/network I/O, parses JSON,
  or calls the UI.
- Missing JUCE or Mutable configured source roots are prerequisites, never
  passes. Fetching remains disabled unless a later task explicitly authorizes
  the exact pinned archive path.

## 10. Target and resource feasibility

| Constraint | Assumption or measured value | Evidence | Budget or limit | Status |
|---|---|---|---|---|
| Target | JUCE-independent C++17 Core plus optional JUCE 8.0.15 standalone | ADR 0016 and Instrument Lab | No JUCE type in Core API | Feasible by architecture |
| Sample rate | Exact 48 kHz in revision 0.1 | Existing prototypes and source adapter practice | Reject other rates | Proposed |
| Block size | 1, 16, 64, 128, 511, 512 in deterministic matrix; max 512 | Instrument Lab precedent | Fixed max 512 | Proposed |
| Voices | Three persistent source voices | Existing adapter exposes suitable models | Approximately 54 KiB opaque adapter storage plus bounded instrument state if Braids path selected | Plausible; measure in bundle |
| Route/map state | 8 waypoints, 32 destinations, 64 UI trace points, 64 events/block | Proposed fixed capacities | No process allocation | Proposed |
| CPU | Existing four-Braids-voice drum Core measured maxima of 0.064/0.130/0.209 ms at 64/128/512 frames on this M1 Pro under a different stress case | Retained local results | Murmur Map must run its own benchmark; no inherited real-time claim | Plausible, unproved |
| Numeric model | Double for control/map weights, float host mix, exact integer IDs/phase/PRNG | New design | No cross-architecture byte identity claim; exact-environment block/fresh-process identity required | Proposed |
| JUCE dependency | Accepted source release `schuss-source-release-000007@1`, JUCE 8.0.15 | Exact local authority | Private development only; distribution review required | Available, not activated |
| Mutable dependency candidate | Source releases `000008@1` and `000009@1`, exact 12+5 file closures, narrow adapter | Exact local authority | No new source files; notice/distribution review remains separate | Available candidate |
| Licensing | MI STM32 repository declares MIT; JUCE authority records AGPL-or-commercial | First-party repository and local records | No distribution decision in this proposal | Open gate |
| Latency | No lookahead; block-boundary GUI control acceptance up to 512 frames | Proposed contract | Report actual adapter/device latency separately | Host-model only |
| UI | Dense map plus one selected-waypoint editor; all displays from accepted snapshots | Existing Schuss accepted-state rule | No raw-input-as-state; 30 Hz UI snapshot is sufficient | Feasible |

## 11. Minimal experiment

### Central hypothesis

`HYPOTHESIS`: A small authored sound map plus visible destination memory will
produce evolution that is more recognizable, steerable, and worth preserving
than matched independent random scene selection, without requiring step editing.

This hypothesis is false if the route controls cannot be heard, if interpolation
mostly produces bland/unstable intermediate sounds, if the locked route does not
repeat exactly, or if a listener does not prefer the map route to the matched
independent comparator.

### Smallest vertical slice

- Four predefined but editable waypoints at the corners of the map.
- Three fixed voice lanes and no reverb/delay.
- Complete distance-weighted graph, one HOME node, 16-slot destination memory.
- Exactly the public controls and state operations above, but no MIDI endpoint,
  controller, VST3, preset browser, canonical identity, or Ksoloti target.
- One deterministic renderer and a restrained standalone map/editor if Core
  evidence passes.

### Frozen default waypoints

Each lane cell is the exact tuple `(interval semitones, activity, timbre,
color, decay ms, level dB, pan)`.

| ID / position | Anchor lane | Thread lane | Spark lane | Character |
|---|---|---|---|---|
| `A (0.12,0.18)` | `(0, 0.85, 0.20, 0.28, 900, -12, -0.35)` | `(7, 0.30, 0.25, 0.20, 240, -18, 0.15)` | `(-12, 0.12, 0.18, 0.22, 110, -24, -0.10)` | low and sheltered |
| `B (0.82,0.16)` | `(5, 0.70, 0.42, 0.55, 600, -13, -0.10)` | `(12, 0.78, 0.72, 0.68, 180, -17, 0.35)` | `(0, 0.25, 0.64, 0.72, 90, -22, 0.65)` | clear and kinetic |
| `C (0.78,0.84)` | `(12, 0.60, 0.70, 0.80, 1400, -15, 0.45)` | `(3, 0.58, 0.88, 0.92, 320, -18, 0.70)` | `(7, 0.72, 0.82, 0.90, 160, -21, -0.55)` | high and brittle |
| `D (0.18,0.80)` | `(-5, 0.78, 0.32, 0.18, 750, -13, -0.55)` | `(10, 0.36, 0.46, 0.30, 420, -19, -0.25)` | `(-7, 0.48, 0.28, 0.36, 260, -23, 0.20)` | shadowed return |

Frozen global defaults are `RUN=true`, `TEMPO=120 BPM`, `TRAVEL=0.5` quarter,
`MEMORY=0.85`, `LENGTH=16`, `ROAM=0.55`, `HOME=0.10`, `RADIUS=0.28`,
`DENSITY=0.70`, `ROOT=48`, `SCALE=Minor pentatonic`, HOME node `A`, and seed
`0x4D55524D41503031`.

### Test signals and gestures

| Field | Bound value |
|---|---|
| Sample rate and supported block sizes | 48,000 Hz; `1,16,64,128,511,512` frames |
| Deterministic seed | `0x4D55524D41503031` (`MURMAP01`) with separately derived route/anchor/thread/spark streams |
| Event/sample timeline convention | Half-open absolute frame ranges; event applied before its exact sample; GUI snapshots accepted at next block boundary |
| Literal condition IDs and count | 9 primary conditions: `MM01_LOCKED`, `MM02_SLOW_EROSION`, `MM03_FRESH`, `MM04_HOME_PULL`, `MM05_MOVE_WAYPOINT`, `MM06_CAPTURE_REPLACE`, `MM07_RESEED`, `MM08_EXTREMES`, `MM09_EXACT_SILENCE`; plus the comparator below |
| Falsifying comparator condition | `MM10_WHITE_SCENE`: same seed family, voice set, scale, average lane density, and duration, but independently selects a waypoint at every event with no route, locality, or destination memory |
| Output names and kinds | `<condition>-events.json`, `<condition>-route.json`, `<condition>-metrics.json`, `<condition>-stereo.wav`, plus `manifest.json` with SHA-256 |
| Objective tolerances | Exact trace and PCM bytes across supported partitions/fresh processes on authenticated environment; zero non-finite/overflow/clip/capacity faults; peak `<0.98`; absolute DC mean `<0.01`; locked post-fill destination recurrence `=1`; exact silence all-zero after Panic |
| Artifact retention policy and location | Refuse overwrite; reproduce to `build/murmur-map-evidence`; retain frozen expected manifest and compact canonical traces under the eventual contract only after review |

Condition timeline:

- `MM01_LOCKED`: 96 s, fill 16 route slots with `MEMORY=0`, set
  `MEMORY=1` at 24 s, then require exact destination-cycle recurrence.
- `MM02_SLOW_EROSION`: 120 s at `MEMORY=0.92`.
- `MM03_FRESH`: 96 s at `MEMORY=0`.
- `MM04_HOME_PULL`: 96 s; HOME ramps 0 to 0.85 at 32 s without consuming an
  extra random draw.
- `MM05_MOVE_WAYPOINT`: locked route; move waypoint C at 32 s. Destination IDs
  must remain identical while only route geometry and C-influenced semantic
  regions change.
- `MM06_CAPTURE_REPLACE`: at 32 s, commit a new valid state to waypoint B;
  active voices retain their snapshots and later events use the new state.
- `MM07_RESEED`: reseed at the first node boundary after 32 s; old tails bridge,
  the ring invalidates, and a new deterministic route begins from HOME.
- `MM08_EXTREMES`: 48 s at maximum tempo/density, minimum travel/radius, maximum
  route length, and rapidly changing valid controls.
- `MM09_EXACT_SILENCE`: Panic at frame 0, `DENSITY=0`, all waypoint activities
  zero; every PCM sample is exactly zero while the route trace remains valid.
- `MM10_WHITE_SCENE`: 120 s comparator, matched aggregate activity and pitch
  pool without route state.

### Measurements

- Block-partition and fresh-process byte identity.
- Destination recurrence at lags 2 through 32 and route edit rate per cycle.
- Node occupancy, transition matrix, HOME-return latency, and map-distance
  distribution.
- Per-lane event counts, pitch range, inter-onset distribution, simultaneous
  event count, and dropped-event count.
- Audio peak, RMS, crest factor, absolute DC mean, clamp/non-finite count, and
  discontinuity proxy around events and waypoint operations.
- Synthetic callback-kernel median, p99, maximum, allocation count, and failure
  count at blocks 64/128/512, reported as host feasibility only.

### Listening protocol

After objective host-signal checks pass, create six randomized 45-second A/B
pairs comparing slow erosion to the matched white-scene comparator. The user
does not see condition labels and scores:

1. audible sense of a place/route;
2. coherent change without obvious short-loop fatigue;
3. usefulness of HOME, MEMORY, and moving one waypoint;
4. preference for continuing to play the result.

Advance only if route controls are correctly identified in at least 5 of 6
trials, slow erosion is preferred in at least 4 of 6 pairs, and no safety or
interpolation artifact is rated worse than 2 on a 5-point scale. This later
protocol would establish only bounded listening evidence for the exact build
and conditions.

### Stop or pivot conditions

- Stop if proposal or bundle fingerprint changes, dependency closure is stale,
  or readiness validation fails.
- Pivot to native voices if Braids source-rate/RNG mechanics obscure the route
  hypothesis or require a new shared abstraction before the experiment.
- Pivot from Gaussian blending to two-endpoint edge interpolation if map
  intermediates repeatedly lose level or identity.
- Reduce to two voices if the event trace is legible but the three-lane sound is
  consistently overcrowded.
- Reject Murmur Map if the matched comparator is not perceptually worse or route
  gestures are not reliably audible.
- Stop before app launch, endpoint/controller access, VST3, target hardware,
  canonical promotion, distribution, or production work without separate
  authorization.

## 12. Acceptance and evidence matrix

| Claim | Acceptance check | Evidence level | Current result | Artifact |
|---|---|---|---|---|
| Modular mechanisms are accurately decomposed | First-party manuals support each observable behavior | Catalog/research | Passed for proposal | This proposal and source ledger |
| Six candidates are materially different | Candidate matrix separates gesture, generator, voice, overlap, and experiment | Design proposal | Passed for proposal | Section 4 |
| Murmur Map has bounded novelty language | Prior-art search records Frames, maps, graph agents, and MI/VCV combinations | Design proposal | Passed for proposal | Sections 4, 7, 8 |
| Murmur Map is implementation-ready | Ready bundle has no unresolved required field and binds exact proposal bytes | Ready implementation contract | Not run; approval required | Proposed `research/prototypes/murmur-map/contract/` |
| Route is block-invariant | Exact semantic route/event traces at all six block sizes and fresh process | Host structural/signal | Not run | Future trace manifest |
| Audio is deterministic and safe | Exact WAV bytes plus peak/DC/non-finite/clip bounds | Host signal | Not run | Future evidence manifest |
| Source dependency is exact | Existing package/source release and adapter authenticate without new source shelf | Source | Candidate authority exists; consumer audit not run | Local Task 038 authorities |
| Standalone target builds | Authenticated JUCE 8.0.15 configure/build/tests | Target build | Not run | Future build receipt |
| Audio callback is safe | Live device deadline, allocation, xrun, lifecycle measurements | Live real-time | Deferred | Separate authorized evidence |
| UI/device works | Launched app, accepted-state visual inspection, endpoint and controller receipt | App/device | Deferred | Separate authorized evidence |
| Instrument is musically worthwhile | Frozen blind comparison and gesture-identification thresholds pass | Listening | Deferred | Future listening record |
| Production/distribution is acceptable | Canonical architecture, licensing, packaging, and release review | Production integration | Deferred | Separate task |

## 13. Implementation plan

### Implementation-ready bundle

- Proposed bundle path: `research/prototypes/murmur-map/contract/`
- Proposal fingerprint and approval reference: to be computed from the immutable
  approved bytes of this path by the bundle generator; approval must explicitly
  name revision 0.1 and Murmur Map's architecture.
- `validate_implementation_bundle.py --phase ready`: NOT RUN — proposal review
  is the current stop gate.

### Files expected to change after approval

- New `research/prototypes/murmur-map/` consumer only.
- Its implementation-ready contract, prototype index, topology, semantic
  control descriptor, Core/renderer/tests, and optional JUCE adapter.
- Existing shared source packages and adapters should remain byte-identical.
- Instrument Lab files change only if a demonstrated missing generic mechanic
  is separately reviewed; this proposal does not assume such a change.

### Focused tests

- Route graph construction, stable tie-breaking, HOME restart, temperature,
  memory reuse/replace, exact lock, deletion repair, reseed boundary.
- Waypoint transactions, interpolation normalization/locality, categorical
  event snapshot, control ranges, invalid input, state operations, and recall
  equivalence.
- Event ordering/capacity, three voice lanes, envelope/bridge, gain/DC safety,
  no process allocation, and accepted-state snapshot coherence.
- All literal experiment conditions and the white-scene comparator.

### Adjacent regression tests

- Task 038 source-package and adapter authentication.
- Instrument Lab repository/consumer validation.
- If the existing Braids adapter is consumed, its focused tests and the exact
  source-dependent boundary only; do not replay unrelated prototypes by default.
- `current` once after implementation freeze.

### Expensive or hardware checks

- One explicit native/JUCE plan and build after the Core freezes.
- One fresh-root reproduction after freeze.
- No live audio, endpoint, physical MIDI, Ableton, hardware, network fetch,
  installation, or device work without new authorization.

### Deferred work

- Relay Bloom, Contour Colony, Tidal Lattice, Thread Memory, and Cell Weather
  implementation.
- VST3/AU, arbitrary host rates, MIDI note-pool capture, controller mapping,
  preset library, canonical Schuss identity/provider, Ksoloti/Gills feasibility,
  packaging, and publication.

### Dependency contract

- JUCE: exact local source release `schuss-source-release-000007@1`, version
  8.0.15, commit and archive hash stated in section 2; fetching disabled;
  private-use target only; distribution requires new legal/license review.
- Mutable candidate: exact source releases `000008@1` and `000009@1`, existing
  physical package manifests and notices, no upstream mutation, no new source
  files, and no Mutable Instruments name or visual branding for the derivative.
- The ready bundle must choose either this exact adapter route or a wholly
  project-owned native three-voice route and freeze the comparator. It must not
  silently mix the two or call behavioral similarity source equivalence.

## 14. Claim-to-source ledger

| ID | State | Claim | Source | Source type | Notes or proof gap |
|---|---|---|---|---|---|
| C-001 | EVIDENCE | Marbles separates random timing, trigger routing, voltage generation, distribution, quantization/slew, and replayable choices | [Marbles manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/marbles/manual/) | First-party manual | Public behavior only |
| C-002 | EVIDENCE | Frames stores keyframes, interpolates channel values, can be CV-scanned, and emits a pulse at keyframe crossings | [Frames manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/frames/manual/) | First-party manual | Does not prescribe a 2D map |
| C-003 | EVIDENCE | Stages groups segments by gate-patch topology and supports self-patched free-running generators, sequences, and loops | [Stages manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/stages/manual/) | First-party manual | Contour Colony remains hypothetical |
| C-004 | EVIDENCE | Tides creates related phase/frequency outputs and clock-locked functions across modulation/audio ranges | [Tides manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/tides_2018/manual/) | First-party manual | Tidal Lattice is not a Tides reimplementation claim |
| C-005 | EVIDENCE | Branches routes each input event between mutually exclusive outcomes under probability control | [Branches manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/branches/manual/) | First-party manual | Mechanism is common Bernoulli routing |
| C-006 | EVIDENCE | Rings separates excitation, pitch, and strum and exposes modal/string resonator behavior | [Rings manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/rings/manual/) | First-party manual | No Rings source selected |
| C-007 | EVIDENCE | Beads samples key playback parameters at grain birth and supports clock/probability, freeze, and addressable buffer time | [Beads manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/beads/manual/) | First-party manual | No Beads source selected |
| C-008 | EVIDENCE | Grids interpolates a 2D authored rhythm map and extracts events with per-channel density | [Grids manual](https://pichenettes.github.io/mutable-instruments-documentation/modules/grids/manual/) | First-party manual | No Grids data/code use proposed |
| C-009 | EVIDENCE | The Turing Machine exposes a continuum from changing sequences to locked loops with bounded lengths | [Official documentation](https://computer.musicthing.co.uk/programs/03-turing-machine/index.html) | First-party project documentation | Behavior inspiration only |
| C-010 | EVIDENCE | Faithful MI-derived module software and graph-based/probabilistic sequencers already exist | [VCV](https://library.vcvrack.com/AudibleInstruments), [Stochas](https://stochas.org/stochas/), [Nodal paper](https://www.researchgate.net/publication/228749312_Generative_Composition_with_Nodal) | Product/source/research | Prevents broad novelty claims |
| C-011 | EVIDENCE | Two-dimensional preset interpolation is established and categorical parameter handling is difficult | [SMC framework](https://eprints.bournemouth.ac.uk/32726/), [2024 interpolation paper](https://orbi.umons.ac.be/handle/20.500.12907/49507) | Peer-reviewed research | Perceptual smoothness still requires listening |
| C-012 | EVIDENCE | MI repository-level guidance declares STM32F code MIT and asks derivatives not to use MI names | [Official repository](https://github.com/pichenettes/eurorack) | First-party source/license declaration | Exact closure and distribution still require review |
| C-013 | EVIDENCE | Schuss retains exact Braids/stmlib closures and a narrow six-model adapter | Local Task 038 records and package manifests | Exact local authority | Runtime/provider/distribution claims excluded |
| C-014 | INFERENCE | Three source voices plus a small graph/map engine are plausible on the current M1 Pro | Existing four-voice Generative Drums retained benchmark plus smaller proposed voice count | Local measured evidence plus reasoning | Murmur Map must measure its own cost; no real-time claim |
| C-015 | HYPOTHESIS | Visible route memory over authored sound states is more steerable and musically valuable than matched independent scene draws | MM01–MM10 objective/listening experiment | Proposed falsifiable experiment | Central open musical claim |
| C-016 | HYPOTHESIS | Separating continuous interpolation from event-boundary categorical snapshots prevents most unstable preset morphs | Stress/locality tests and later listening | Proposed falsifiable experiment | May still require two-endpoint interpolation pivot |
| C-017 | UNRESOLVED | Existing Braids adapter or project-owned native voices are the cleaner source for revision 0.1 | Ready-bundle dependency audit and comparator | Required pre-implementation decision | Must be frozen before DSP edits |
| C-018 | UNRESOLVED | Murmur Map's map/route gesture is compelling in actual use | Later blinded listening and launched UI exercise | Listening/device gap | Proposal cannot answer this |

## 15. Open questions and decision gate

### Open questions

1. Should revision 0.1 use the exact existing Braids adapter, or native voices
   so the experiment isolates route/map behavior? Recommendation: make a tiny
   offline dependency comparator during bundle readiness and choose one before
   implementation; do not support two runtime voice systems in the slice.
2. Does Gaussian all-waypoint blending preserve stronger identity than simple
   interpolation along the current edge? Recommendation: freeze Gaussian first
   and retain edge-only interpolation as the falsifying pivot.
3. Is a three-voice output clearer than two voices? Recommendation: retain three
   in the proposal but make two-voice reduction an explicit stop/pivot rule.
4. Should MIDI-held notes replace the scale table? Recommendation: defer until
   the map gesture works; MIDI would otherwise add endpoint and note-lifecycle
   questions to the first proof.
5. Which follow-up should come next if Murmur Map succeeds? Recommendation:
   Relay Bloom for a compact contrasting orchestration instrument; Contour
   Colony only after its stability/interaction paper prototype is convincing.

### Recommendation

Approve **Murmur Map 0.1** as the next proposal to take through bundle readiness.
It fills the clearest gap in the current library, makes unusually good use of a
JUCE interface, has a precise deterministic experiment, reuses available source
infrastructure if appropriate, and leaves five genuinely different follow-ups.

### Approval requested

Approval should say:

> Approve `research/proposals/modular-generative-juce-instrument-study.md`
> revision 0.1 and its Murmur Map architecture for an implementation-ready
> Sonic Research Lab bundle at `research/prototypes/murmur-map/contract/`.
> Freeze either the exact Task 038 Braids adapter route or the native three-voice
> route before DSP edits. Implement only the Core/offline/JUCE-target vertical
> slice through host-signal and authenticated target-build evidence. Do not
> launch the app, access endpoints/devices, install a plugin, claim real-time or
> listening success, allocate canonical Schuss identity, distribute, publish,
> stage, commit, or push.

The bundle must bind the post-review SHA-256 of this proposal and the user's
approval reference. No implementation authority is inferred from the current
research request.

## 16. Implementation record

Not applicable. Proposal only; no implementation bundle, DSP source, build,
app launch, device action, listening test, or production integration was
performed.
