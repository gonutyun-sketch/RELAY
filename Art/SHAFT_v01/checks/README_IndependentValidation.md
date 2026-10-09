# Independent FBX validation

The two JSON reports inspect the exported FBX binary files using Blender's parser. They do not import models into Unity or modify the Unity project.

- `shaft_fbx_audit.json`: FBX hashes, axis/unit metadata, model origin and transforms, geometry/index validity, finite UVs and normals, material slot/index validity, and expected Unity bounds.
- `shaft_surface_audit.json`: comparison with manifest bounds, vertex/triangle counts, material order and per-material face counts; complete UV corner indices; inward-facing normal samples from all four rock walls at heights 14–16 metres.

All recorded checks passed for the three exports. The 471 sampled rock-wall polygons all face the shaft interior.

Expected Unity coordinates use the calibrated X-handedness conversion after the export-mesh 180-degree correction. Actual Unity importing, material setup, rendering and the elevator ride remain manual integration checks. Normal sampling is a local sanity check, not proof of every surface across the full shaft.
