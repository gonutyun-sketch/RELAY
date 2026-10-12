# RELAY AUDIO v02 — sources and changes

The WAV assets combine new procedural sound design with separately assigned CC0 source files.
This is NOT a pack of 73 newly recorded physical sound sources. Some sounds are synthetic;
the provenance for every cue is in catalog.json. The authoring history of third-party raw
recordings cannot be independently certified beyond the supplied files and stated licenses.

## Kenney — Impact Sounds (1.0), 2019
Page: https://kenney.nl/assets/impact-sounds
Archive: https://kenney.nl/media/pages/assets/impact-sounds/87b4ddecda-1677589768/kenney_impact-sounds.zip
License: Creative Commons Zero (CC0 1.0). Original license retained in source_materials/Kenney_LICENSE.txt.
21 distinct source families were used. Each input file is assigned to exactly one output cue.
Numbered variants within each Kenney family were deliberately excluded after a waveform
similarity audit. No Kenney footstep variants are used in the delivered footstep sounds.
Changes: mono downmix; sample-rate conversion at unchanged duration/pitch; trimming;
corrective filtering; short tail damping; level adjustment; some cues add independent synthesis.
No pitch shifting, time stretching, or artificial room reverb.

## Fantozzi (extracted by qubodup) — Fantozzi's Footsteps (Grass/Sand & Stone)
Page: https://opengameart.org/content/fantozzis-footsteps-grasssand-stone
Original archive: https://opengameart.org/sites/default/files/Fantozzi-footsteps.7z
License on source page: CC0. Stone L1/R1/L2/R2 and Sand L1/R1/L2/R2 are used.
Eight separately performed steps, one output per step. Original timing/pitch retained;
silence trim, mono downmix, 44.1-to-48 kHz conversion, corrective EQ and level only.
The Sand steps supply the soft ground/forest footwear layer. No biome recording is implied.

## Thimras — Metal footsteps on concrete
Page: https://opengameart.org/content/metal-footsteps-on-concrete
Original archive: https://opengameart.org/sites/default/files/metal_steps_48k24b.7z
License on source page: CC0. Four separate metal-foot contact recordings used for metal steps.
These are metal-on-concrete Foley, used as the game's metallic contact sound, rather than
a claim that the recording was captured on this game's metal elevator floor.
Changes: silence trim, mono downmix, corrective EQ, level and endpoint fades.

## isaiah658 — Ambient Bird Sounds
Page: https://opengameart.org/content/ambient-bird-sounds
Original file: https://opengameart.org/sites/default/files/birds-isaiah658_0.ogg
License on source page: CC0. Used only for Forest_DistantBird_01.
Changes: a 3.8-second excerpt, mono downmix, corrective EQ, gentle fades, gain.

## syncopika — Bird chirping sounds
Page: https://opengameart.org/content/bird-chirping-sounds
Original file: https://opengameart.org/sites/default/files/birdchirping071414.wav
License on source page: CC0. Used only for Forest_DistantBird_02.
Changes: mono downmix, 44000-to-48000 sample-rate conversion preserving duration/pitch,
corrective EQ, gentle fades, gain. This is a different recording from bird 01.

Source pages checked 2026-10-12. License: https://creativecommons.org/publicdomain/zero/1.0/

The input recording filenames, input SHA-256 hashes, editing parameters, output recipes,
and independent per-cue random seeds are stored in catalog.json. All generated material
is authored for this project; no additional third-party license is imposed on the synthetic layers.
The generator shares mathematical filters/envelopes only, not a recorded base effect.
Source materials and reproducible build scripts are included for inspection.
