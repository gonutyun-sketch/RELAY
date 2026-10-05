using UnityEngine;
using UnityEngine.Rendering;

namespace Startup
{
    // Attach manually to CORE_FX, under the existing Core_Block.
    // This script only controls the assigned effect objects at runtime.
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(310)]
    public sealed class CoreElectricalFX : MonoBehaviour
    {
        [System.Serializable]
        public sealed class GlassArc
        {
            public LineRenderer core;
            public LineRenderer glow;

            [System.NonSerialized] public Vector3[] points;
            [System.NonSerialized] public MaterialPropertyBlock coreProperties;
            [System.NonSerialized] public MaterialPropertyBlock glowProperties;
            [System.NonSerialized] public float angle;
            [System.NonSerialized] public float sweep;
            [System.NonSerialized] public float contactY;
            [System.NonSerialized] public int rootIndex;
        }

        [SerializeField] private PowerModule powerSource = null;
        [SerializeField] private LineRenderer arcCore = null;
        [SerializeField] private LineRenderer arcGlow = null;
        [SerializeField] private Light coreLight = null;

        [Header("Metres relative to CORE_FX (world scale must be 1)")]
        [SerializeField] private Vector3 lowerContact = new Vector3(0f, -0.25f, 0f);
        [SerializeField] private Vector3 upperContact = new Vector3(0f, 0.25f, 0f);
        [SerializeField, Range(0f, 0.08f)] private float bend = 0.04f;

        [Header("Main arc width (metres)")]
        [SerializeField, Range(0.002f, 0.025f)] private float mainCoreWidth = 0.01f;
        [SerializeField, Range(0.01f, 0.08f)] private float mainGlowWidth = 0.045f;

        [Header("Branches touching the inside of the glass")]
        [SerializeField] private GlassArc[] glassArcs = new GlassArc[0];
        [SerializeField, Range(0.002f, 0.02f)] private float glassCoreWidth = 0.007f;
        [SerializeField, Range(0.01f, 0.08f)] private float glassGlowWidth = 0.032f;
        [SerializeField, Range(0f, 0.1f)] private float glassBend = 0.055f;
        [SerializeField, Min(0.3f)] private float glassRadius = 0.714f;

        [Header("Timing")]
        [SerializeField] private Vector2 pauseSeconds = new Vector2(0.45f, 0.9f);
        [SerializeField] private Vector2 flashSeconds = new Vector2(0.16f, 0.26f);
        [SerializeField, Min(0.01f)] private float fadeInSeconds = 1f;
        [SerializeField, Min(0.01f)] private float fadeOutSeconds = 0.25f;

        private const int PointCount = 13;
        private const float TipWidth = 0.18f;
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private readonly Vector3[] localPoints = new Vector3[PointCount];
        private readonly Vector3[] worldPoints = new Vector3[PointCount];
        private readonly System.Random random = new System.Random(73129);
        private MaterialPropertyBlock coreProperties;
        private MaterialPropertyBlock glowProperties;
        private Vector3 burstStart;
        private Vector3 burstEnd;
        private float fullLightIntensity;
        private float powerAmount;
        private float cooldown;
        private float age;
        private float lifetime;
        private float shapeTimer;
        private bool bursting;
        private bool configured;

        private void Awake()
        {
            HideArc();
            if (coreLight != null)
            {
                fullLightIntensity = coreLight.intensity;
                SetLight(0f);
            }

            if (powerSource == null || arcCore == null || arcGlow == null || coreLight == null)
            {
                Fail("Assign Power Source, Arc Core, Arc Glow and Core Light.");
                return;
            }

            if (arcCore == arcGlow ||
                !arcCore.transform.IsChildOf(transform) ||
                !arcGlow.transform.IsChildOf(transform) ||
                !coreLight.transform.IsChildOf(transform))
            {
                Fail("Use two separate Line Renderers and a Light, all under CORE_FX.");
                return;
            }

            if (!HasArcMaterial(arcCore) || !HasArcMaterial(arcGlow))
            {
                Fail("Both Line Renderers need M_CoreArc (Universal Render Pipeline/Unlit, Transparent, Additive).");
                return;
            }

            coreProperties = new MaterialPropertyBlock();
            glowProperties = new MaterialPropertyBlock();
            ConfigureLine(arcCore, mainCoreWidth);
            ConfigureLine(arcGlow, mainGlowWidth);

            if (glassArcs == null)
                glassArcs = new GlassArc[0];

            var usedLines = new System.Collections.Generic.HashSet<LineRenderer>
            {
                arcCore, arcGlow
            };

            for (int i = 0; i < glassArcs.Length; i++)
            {
                GlassArc branch = glassArcs[i];
                if (branch == null || branch.core == null || branch.glow == null ||
                    !branch.core.transform.IsChildOf(transform) ||
                    !branch.glow.transform.IsChildOf(transform) ||
                    !usedLines.Add(branch.core) || !usedLines.Add(branch.glow) ||
                    !HasArcMaterial(branch.core) || !HasArcMaterial(branch.glow))
                {
                    Fail("Glass Arcs element " + i +
                        " needs two unused Line Renderers under CORE_FX, with M_CoreArc.");
                    return;
                }

                branch.points = new Vector3[PointCount];
                branch.coreProperties = new MaterialPropertyBlock();
                branch.glowProperties = new MaterialPropertyBlock();
                ConfigureLine(branch.core, glassCoreWidth, true);
                ConfigureLine(branch.glow, glassGlowWidth, true);
            }

            configured = true;
        }

        private static bool HasArcMaterial(LineRenderer line)
        {
            Material material = line.sharedMaterial;
            return material != null && material.HasProperty(BaseColorId) &&
                material.shader != null &&
                material.shader.name == "Universal Render Pipeline/Unlit";
        }

        private static void ConfigureLine(LineRenderer line, float width, bool taper = false)
        {
            line.useWorldSpace = true;
            line.loop = false;
            line.alignment = LineAlignment.View;
            line.textureMode = LineTextureMode.Stretch;
            line.widthCurve = AnimationCurve.Linear(0f, 1f, 1f, taper ? TipWidth : 1f);
            line.widthMultiplier = width;
            line.numCapVertices = 2;
            line.numCornerVertices = 1;
            line.shadowCastingMode = ShadowCastingMode.Off;
            line.receiveShadows = false;
            line.lightProbeUsage = LightProbeUsage.Off;
            line.reflectionProbeUsage = ReflectionProbeUsage.Off;
            line.generateLightingData = false;
            line.positionCount = PointCount;
            line.enabled = false;
        }

        private void OnEnable()
        {
            powerAmount = 0f;
            cooldown = 0.25f;
            HideArc();
            SetLight(0f);
        }

        private void LateUpdate()
        {
            if (!configured)
                return;

            bool powered = powerSource != null && powerSource.IsOnline;
            float dt = Time.deltaTime;
            float fade = powered ? fadeInSeconds : fadeOutSeconds;
            powerAmount = Mathf.MoveTowards(powerAmount, powered ? 1f : 0f,
                dt / Mathf.Max(0.01f, fade));
            SetLight(powerAmount);

            // No discharge on AUX, after power loss, or while MAIN is fading in.
            if (!powered || powerAmount < 0.75f)
            {
                HideArc();
                cooldown = 0.25f;
                return;
            }

            if (!bursting)
            {
                cooldown -= dt;
                if (cooldown > 0f)
                    return;

                age = 0f;
                lifetime = RandomRange(flashSeconds, 0.06f);
                shapeTimer = 0f;
                burstStart = lowerContact + ContactOffset();
                burstEnd = upperContact + ContactOffset();
                PrepareGlassArcs();
                bursting = true;
            }

            if (age >= lifetime)
            {
                HideArc();
                cooldown = RandomRange(pauseSeconds, 0.3f);
                return;
            }

            shapeTimer -= dt;
            if (shapeTimer <= 0f)
            {
                BuildArc();
                BuildGlassArcs();
                shapeTimer = 0.035f;
            }

            // Transform every frame so the arc follows the parent without lag.
            for (int i = 0; i < PointCount; i++)
                worldPoints[i] = transform.TransformPoint(localPoints[i]);
            arcCore.SetPositions(worldPoints);
            arcGlow.SetPositions(worldPoints);

            float envelope = Mathf.Clamp01((age + dt) / 0.02f) *
                Mathf.Clamp01((lifetime - age) / 0.08f) * powerAmount;
            SetArcColor(arcCore, coreProperties, new Color(1.1f, 1.7f, 2f, envelope));
            SetArcColor(arcGlow, glowProperties, new Color(0.08f, 0.55f, 1f, envelope * 0.18f));
            arcCore.enabled = true;
            arcGlow.enabled = true;
            DrawGlassArcs(envelope);
            age += dt;
        }

        private void PrepareGlassArcs()
        {
            int firstPanel = random.Next(6);
            for (int i = 0; i < glassArcs.Length; i++)
            {
                GlassArc branch = glassArcs[i];
                // Three branches use alternating panes, away from the metal columns.
                int panel = (firstPanel + i * 2 + i / 3) % 6;
                branch.angle = (panel * 60f + SignedRandom() * 12f) * Mathf.Deg2Rad;
                branch.sweep = SignedRandom() * 0.1f;
                branch.contactY = SignedRandom() * 0.4f;
                branch.rootIndex = PointCount / 2 + (i % 3 - 1) * 2;
            }
        }

        private void BuildGlassArcs()
        {
            float progress = Mathf.Clamp01(age / Mathf.Max(0.06f, lifetime));
            float outerWidth = Mathf.Max(glassCoreWidth, glassGlowWidth);
            float innerRadius = Mathf.Max(0.3f, glassRadius);
            // Leave 1 mm for the faceted inner surface, including the line's halo.
            float endRadius = innerRadius - 0.001f - outerWidth * TipWidth * 0.5f;

            foreach (GlassArc branch in glassArcs)
            {
                float angle = branch.angle + branch.sweep * progress;
                Vector3 outward = new Vector3(Mathf.Sin(angle), 0f, -Mathf.Cos(angle));
                Vector3 tangent = new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle));
                Vector3 end = outward * endRadius + Vector3.up * branch.contactY;
                Vector3 start = localPoints[branch.rootIndex];

                for (int i = 0; i < PointCount; i++)
                {
                    float t = i / (float)(PointCount - 1);
                    Vector3 point = Vector3.Lerp(start, end, t);
                    if (i > 0 && i < PointCount - 1)
                    {
                        float offset = Mathf.Max(0f, glassBend) * Mathf.Sin(t * Mathf.PI);
                        point += tangent * (SignedRandom() * offset);
                        point.y += SignedRandom() * offset;
                    }

                    // Keep the halo inside the glass, not just the centre line.
                    float radiusLimit = innerRadius - 0.001f -
                        outerWidth * Mathf.Lerp(1f, TipWidth, t) * 0.5f;
                    float radius = Mathf.Sqrt(point.x * point.x + point.z * point.z);
                    if (radius > radiusLimit)
                    {
                        point.x *= radiusLimit / radius;
                        point.z *= radiusLimit / radius;
                    }

                    // Keep branches in the gap until they clear the electrode faces.
                    if (radius < 0.28f)
                        point.y = Mathf.Clamp(point.y, -0.20f, 0.20f);
                    point.y = Mathf.Clamp(point.y, -0.48f, 0.48f);
                    branch.points[i] = point;
                }
                // The branch must remain joined to the visible centre arc.
                branch.points[0] = start;
            }
        }

        private void DrawGlassArcs(float envelope)
        {
            for (int i = 0; i < glassArcs.Length; i++)
            {
                GlassArc branch = glassArcs[i];
                float alpha = envelope * Mathf.Clamp01((age - (i % 3) * 0.018f) / 0.025f);
                if (alpha <= 0f)
                {
                    branch.core.enabled = false;
                    branch.glow.enabled = false;
                    continue;
                }

                for (int j = 0; j < PointCount; j++)
                    worldPoints[j] = transform.TransformPoint(branch.points[j]);
                branch.core.SetPositions(worldPoints);
                branch.glow.SetPositions(worldPoints);
                SetArcColor(branch.core, branch.coreProperties,
                    new Color(0.7f, 1.3f, 1.8f, alpha * 0.9f));
                SetArcColor(branch.glow, branch.glowProperties,
                    new Color(0.08f, 0.55f, 1f, alpha * 0.2f));
                branch.core.enabled = true;
                branch.glow.enabled = true;
            }
        }

        private void BuildArc()
        {
            for (int i = 0; i < PointCount; i++)
            {
                float t = i / (float)(PointCount - 1);
                Vector3 point = Vector3.Lerp(burstStart, burstEnd, t);
                if (i > 0 && i < PointCount - 1)
                {
                    float offset = Mathf.Max(0f, bend) * Mathf.Sin(t * Mathf.PI);
                    point.x += SignedRandom() * offset;
                    point.z += SignedRandom() * offset;
                }
                localPoints[i] = point;
            }
        }

        private Vector3 ContactOffset()
        {
            // Keep both ends on the model's 0.184 m radius electrode faces.
            return new Vector3(SignedRandom() * 0.055f, 0f, SignedRandom() * 0.055f);
        }

        private float SignedRandom() => (float)random.NextDouble() * 2f - 1f;

        private float RandomRange(Vector2 limits, float minimum)
        {
            float low = Mathf.Max(minimum, Mathf.Min(limits.x, limits.y));
            float high = Mathf.Max(low, Mathf.Max(limits.x, limits.y));
            return Mathf.Lerp(low, high, (float)random.NextDouble());
        }

        private static void SetArcColor(LineRenderer line,
            MaterialPropertyBlock properties, Color color)
        {
            line.GetPropertyBlock(properties);
            properties.SetColor(BaseColorId, color);
            line.SetPropertyBlock(properties);
        }

        private void SetLight(float amount)
        {
            if (coreLight == null)
                return;
            coreLight.intensity = fullLightIntensity * amount;
            coreLight.enabled = amount > 0f;
        }

        private void HideArc()
        {
            bursting = false;
            if (arcCore != null)
                arcCore.enabled = false;
            if (arcGlow != null)
                arcGlow.enabled = false;
            if (glassArcs == null)
                return;
            foreach (GlassArc branch in glassArcs)
            {
                if (branch == null)
                    continue;
                if (branch.core != null)
                    branch.core.enabled = false;
                if (branch.glow != null)
                    branch.glow.enabled = false;
            }
        }

        private void OnDisable()
        {
            HideArc();
            SetLight(0f);
        }

        private void Fail(string message)
        {
            Debug.LogError("CoreElectricalFX: " + message, this);
            enabled = false;
        }
    }
}
