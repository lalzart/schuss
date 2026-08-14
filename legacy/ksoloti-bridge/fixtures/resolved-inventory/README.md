# Resolved inventory fixture source

Treat `axoloti-factory/` as a source root with source ID `axoloti-factory`.
The fixture deliberately exercises facts that a map-only or success-only
exporter would lose:

- `multi-overload.axo` has three definitions, two name overloads, and one
  definition with no source UUID;
- `ambiguous-overload.axp` resolves one overload by UUID, resolves a second by
  name, and connects a buffer so legacy promotion replaces the initially
  selected scalar instance while the ambiguity remains explicit;
- `duplicate-first.axo` and `duplicate-second.axo` share an explicit UUID;
- `unsupported-object-element.axo` contains a future object element; its
  failure or partial handling must not stop later files;
- `relative-parent.axp` resolves `./relative-child.axs`, which resolves
  `./relative-leaf.axs`;
- `zombies.axp` contains both a serialized hard zombie and an object that must
  become a zombie during resolution; and
- its nets include valid, missing-instance, and missing-port endpoints.

The source ID is intentional: the legacy generated-object helper resolves its
output directory through the `axoloti-factory` preference ID. A fixture
generator may therefore be run against this tree without changing legacy code;
the Schuss serializer interception must keep the tree byte-identical.
