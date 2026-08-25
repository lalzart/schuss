# Layerwell third-party notice routing

Layerwell adds no copied third-party DSP source. It composes the existing Tide
Pit Gills and Pamplist public Cores inside this repository. Pamplist in turn
compiles its configured, locked Ksoloti Extended Macro Voice source read-only.
The exact dependency manifests and retained notices remain the authorities:

- Tide Pit import and Mutable closure:
  `research/prototypes/tide-pit-gills/third_party/THIRD_PARTY_NOTICES.md`
  (`4e198a537ca719925bc407a073350d7708ecb15d0152fe876478e565e23a98aa`).
- Mutable Eurorack Braids package:
  `packages/dsp_sources/mutable_eurorack_braids_v1/THIRD_PARTY_NOTICES.md`
  (`d8b9f775d7adbdae406164e0ddad8cfb79a3e5c4b84afb3e08f1222ec787fb68`).
- Mutable stmlib package:
  `packages/dsp_sources/mutable_stmlib_v1/THIRD_PARTY_NOTICES.md`
  (`73a98e8c100f93d499ad2b389a5a7d59d074aeb9253fca4506f052d0c740c89e`).
- Mutable Ksoloti package:
  `packages/dsp_sources/mutable_ksoloti_v1/THIRD_PARTY_NOTICES.md`
  (`ddc99eecad00ff1387c50675f2a56c9079764ba2f5ea453d0e6816b700cb82f7`).
- Pamplist's Ksoloti Extended, Mutable Instruments Plaits, and stmlib routing:
  `research/prototypes/pamplist/THIRD_PARTY_NOTICES.md`
  (`79a670e45ba454cfcc74a76c9aab84467fd145044b928e34e423efa5e21a1312`).
- Pamplist configured-source authority:
  `research/prototypes/pamplist/source-dependencies.json`
  (`d7b82c51046bf96d68b726eba1ebbfc989e0d03fc4daab47f4e71f6fd71f5c38`).

JUCE 8.0.15 is used only from an authenticated operator-supplied local source
tree for the unlaunched prototype build. Its source-release and license boundary
is recorded in
`research/prototype_support/instrument_lab/juce-8.0.15-source-tree.json`.

This routing file is not a distribution approval. Packaging, JUCE licensing,
notice assembly, signing, notarization, and release review remain deferred.
