# RELAY forest environment textures

Four 2048 x 2048 RGB PNGs. Each tile spans 2 x 2 metres. Both surfaces are opaque and nonmetallic.

- Floor mean RGB (8-bit): [59.72, 50.88, 39.15]; roughness default 0.84, Unity smoothness 0.16.
- Rock mean RGB (8-bit): [90.6, 96.1, 95.38]; roughness default 0.86, Unity smoothness 0.14.
- Old moss coverage: 14.11%.
- Normals use OpenGL +Y: import as Normal map, disable sRGB, do not flip green.
- Base colors: sRGB enabled. All four maps: Repeat wrap, trilinear/mipmapped sampling.
- Suggested normal strength: floor 0.6-0.85, rock 0.7-1.0.
- Procedural periodic fields and wrapped surface details; no directional baked lighting.
- Uniform roughness guidance supplied; no separate roughness or AO maps in this four-map set.
- The contact sheet is an unlit color/normal inspection, not an in-engine render.
