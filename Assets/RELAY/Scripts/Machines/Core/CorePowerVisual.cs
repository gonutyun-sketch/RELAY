using UnityEngine;
using UnityEngine.Rendering;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(300)]
    public sealed class CorePowerVisual : MonoBehaviour
    {
        [System.Serializable]
        public sealed class PoweredFixture
        {
            public Light light;
            public MeshRenderer lens;

            [System.NonSerialized] public float fullIntensity;
            [System.NonSerialized] public Color litColor;
            [System.NonSerialized] public MaterialPropertyBlock properties;
        }

        [SerializeField] private PowerModule powerSource = null;
        [SerializeField] private MeshRenderer emitterRenderer = null;

        [SerializeField]
        private Color emissionColor =
            new Color(0.08f, 0.45f, 1f, 1f);

        [SerializeField, Min(0f)] private float emissionStrength = 4f;
        [SerializeField, Min(0.01f)] private float fadeInSeconds = 1f;
        [SerializeField, Min(0.01f)] private float fadeOutSeconds = 0.25f;

        [Header("Existing room lights")]
        [SerializeField]
        private PoweredFixture[] roomFixtures =
            new PoweredFixture[0];
        [SerializeField]
        private Color unlitLensColor =
            new Color32(18, 22, 25, 255);

        [Header("Optional room reflection")]
        [SerializeField] private ReflectionProbe labReflection = null;

        private static readonly int EmissionId =
            Shader.PropertyToID("_EmissionColor");
        private static readonly int BaseColorId =
            Shader.PropertyToID("_BaseColor");

        private MaterialPropertyBlock properties;
        private float amount;
        private bool configured;
        private bool lastPowered;
        private bool reflectionDirty;
        private int reflectionRenderId = -1;

        private void Awake()
        {
            properties = new MaterialPropertyBlock();
            CacheFixtures();
            ApplyVisuals(0f);

            if (powerSource == null || emitterRenderer == null)
            {
                Fail("Assign Power Source and Emitter Renderer.");
                return;
            }

            Material material = emitterRenderer.sharedMaterial;
            if (material == null || !material.HasProperty(EmissionId))
            {
                Fail("Emitter Renderer needs its URP/Lit emitter material.");
                return;
            }

            if (!material.IsKeywordEnabled("_EMISSION"))
            {
                Fail("Enable Emission on RLYK_Emitter and choose a non-black emission color.");
                return;
            }

            for (int i = 0; i < roomFixtures.Length; i++)
            {
                PoweredFixture fixture = roomFixtures[i];
                if (fixture == null || fixture.light == null ||
                    fixture.lens == null || fixture.properties == null)
                {
                    Fail("Room Fixtures element " + i +
                        " needs a Light and a Lens using M_LightFace (URP/Unlit).");
                    return;
                }

                for (int j = 0; j < i; j++)
                {
                    if (roomFixtures[j].light == fixture.light ||
                        roomFixtures[j].lens == fixture.lens)
                    {
                        Fail("Each Room Fixtures element needs a different Light and Lens.");
                        return;
                    }
                }
            }

            if (labReflection != null &&
                (labReflection.mode != ReflectionProbeMode.Realtime ||
                 labReflection.refreshMode != ReflectionProbeRefreshMode.ViaScripting))
            {
                Debug.LogWarning(
                    "CorePowerVisual: set Lab Reflection to Realtime / Via Scripting. " +
                    "Lights still work, but automatic reflection refresh is skipped.", this);
            }

            configured = true;
        }

        private void CacheFixtures()
        {
            if (roomFixtures == null)
                roomFixtures = new PoweredFixture[0];

            foreach (PoweredFixture fixture in roomFixtures)
            {
                if (fixture == null)
                    continue;

                if (fixture.light != null)
                    fixture.fullIntensity = fixture.light.intensity;

                Material material = fixture.lens != null
                    ? fixture.lens.sharedMaterial : null;

                if (material == null || !material.HasProperty(BaseColorId))
                    continue;

                fixture.litColor = material.GetColor(BaseColorId);
                fixture.properties = new MaterialPropertyBlock();
            }
        }

        private void OnEnable()
        {
            amount = 0f;
            lastPowered = false;
            reflectionDirty = true;
            ApplyVisuals(0f);
        }

        private void LateUpdate()
        {
            if (!configured)
                return;

            bool powered = powerSource != null && powerSource.IsOnline;
            if (powered != lastPowered)
            {
                lastPowered = powered;
                reflectionDirty = true;
            }

            float target = powered ? 1f : 0f;
            float seconds = powered ? fadeInSeconds : fadeOutSeconds;

            amount = Mathf.MoveTowards(
                amount, target,
                Time.deltaTime / Mathf.Max(0.01f, seconds));

            ApplyVisuals(amount);

            if (amount == target)
                RefreshReflectionIfNeeded();
        }

        private void ApplyVisuals(float value)
        {
            ApplyEmission(value);

            if (roomFixtures == null)
                return;

            foreach (PoweredFixture fixture in roomFixtures)
            {
                if (fixture == null)
                    continue;

                if (fixture.light != null)
                {
                    fixture.light.intensity = fixture.fullIntensity * value;
                    fixture.light.enabled = value > 0f;
                }

                if (fixture.lens == null || fixture.properties == null)
                    continue;

                // M_LightFace is Unlit, so its visible brightness uses Base Color.
                fixture.lens.GetPropertyBlock(fixture.properties);
                fixture.properties.SetColor(BaseColorId,
                    Color.Lerp(unlitLensColor, fixture.litColor, value));
                fixture.lens.SetPropertyBlock(fixture.properties);
            }
        }

        private void RefreshReflectionIfNeeded()
        {
            if (!reflectionDirty || labReflection == null ||
                !labReflection.isActiveAndEnabled ||
                labReflection.mode != ReflectionProbeMode.Realtime ||
                labReflection.refreshMode != ReflectionProbeRefreshMode.ViaScripting)
                return;

            if (reflectionRenderId >= 0 &&
                !labReflection.IsFinishedRendering(reflectionRenderId))
                return;

            // Refresh once at the end of each power transition, not every frame.
            reflectionRenderId = labReflection.RenderProbe();
            reflectionDirty = false;
        }

        private void ApplyEmission(float value)
        {
            if (properties == null || emitterRenderer == null)
                return;

            emitterRenderer.GetPropertyBlock(properties);
            properties.SetColor(
                EmissionId,
                emissionColor * (Mathf.Max(0f, emissionStrength) * value));
            emitterRenderer.SetPropertyBlock(properties);
        }

        private void OnDisable()
        {
            amount = 0f;
            ApplyVisuals(0f);
        }

        private void Fail(string message)
        {
            Debug.LogError("CorePowerVisual: " + message, this);
            enabled = false;
        }
    }
}
