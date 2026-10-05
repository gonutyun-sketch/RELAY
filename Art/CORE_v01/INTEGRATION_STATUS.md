# CORE integration snapshot — 2026-10-05

This folder preserves the CORE Blender source, 11 FBX exports, preview renders,
authoring tools, model validation reports, and reference C# samples.

`READ_ME.md`, `UNITY_HANDOFF.md`, and `manifest.json` describe the original model
handoff. In particular, their original reactor placement and notes about future
power effects are historical. Use the saved Unity scene and runtime scripts as
the current integration state:

- `Assets/Scenes/Startup_Graybox.unity`: reduced room dimensions, CORE model
  integration, four powered room fixtures, and three glass-reaching arc branches.
- `Assets/_STARTUP/Art/Core`: imported models, Unity materials, and importer metadata.
- `Assets/_STARTUP/Scripts/CorePowerVisual.cs`: MAIN-powered emitter and room lights.
- `Assets/_STARTUP/Scripts/CorePanelDisplay.cs`: MAIN-powered HEAT/COLD indicators.
- `Assets/_STARTUP/Scripts/CoreElectricalFX.cs`: centre discharge, glass branches,
  and the local blue light.

The `code_samples` folder is reference material outside Unity's Assets folder.
Do not add duplicate copies of these classes to Assets. The user applies all
Unity scene, Inspector, and runtime script changes manually.

The scene and code have been inspected as saved files. This backup does not
claim a successful standalone game build or an automated Unity playtest.

Next planned work: lighting fixture design and placement in the laboratory.
