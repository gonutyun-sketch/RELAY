using UnityEngine;
using UnityEngine.Rendering;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class SignalScope : MonoBehaviour
    {
        [SerializeField] private PowerModule powerSource;
        [SerializeField] private MachineDial frequencyDial;
        [SerializeField] private MachineSlider phaseSlider;
        [SerializeField] private MachineSlider gainSlider;

        [SerializeField] private LineRenderer referenceWave;
        [SerializeField] private LineRenderer currentWave;
        [SerializeField] private MeshRenderer lockLamp;

        [SerializeField] private float referenceFrequency = 3.5f;
        [SerializeField] private float referencePhase = 105f;

        [SerializeField, Range(0.25f, 1.25f)]
        private float referenceGain = 0.8f;

        [SerializeField, Min(0.1f)]
        private float lockHoldSeconds = 3f;

        private const int PointCount = 129;
        private const float ScreenWidth = 1.18f;
        private const float BaseAmplitude = 0.20f;

        private const float FrequencyTolerance = 0.03f;
        private const float PhaseTolerance = 6f;
        private const float GainTolerance = 0.035f;

        private readonly Vector3[] referencePoints =
            new Vector3[PointCount];

        private readonly Vector3[] currentPoints =
            new Vector3[PointCount];

        private bool configured;
        private float stableSeconds;

        private float RequiredHold =>
            Mathf.Max(0.1f, lockHoldSeconds);

        private bool HasSignal =>
            configured &&
            isActiveAndEnabled &&
            powerSource != null &&
            powerSource.IsOnline &&
            frequencyDial != null &&
            frequencyDial.isActiveAndEnabled &&
            phaseSlider != null &&
            phaseSlider.isActiveAndEnabled &&
            gainSlider != null &&
            gainSlider.isActiveAndEnabled &&
            referenceWave != null &&
            currentWave != null &&
            lockLamp != null;

        private bool MatchesReference =>
            Mathf.Abs(
                frequencyDial.Value - referenceFrequency)
                <= FrequencyTolerance &&
            Mathf.Abs(
                Mathf.DeltaAngle(
                    phaseSlider.Value, referencePhase))
                <= PhaseTolerance &&
            Mathf.Abs(
                gainSlider.Value - referenceGain)
                <= GainTolerance;

        public bool IsLocked =>
            HasSignal &&
            MatchesReference &&
            stableSeconds >= RequiredHold;

        private void Awake()
        {
            bool valid = true;

            valid &= CheckReference(powerSource, "Power Source");
            valid &= CheckReference(frequencyDial, "Frequency Dial");
            valid &= CheckReference(phaseSlider, "Phase Slider");
            valid &= CheckReference(gainSlider, "Gain Slider");
            valid &= CheckReference(referenceWave, "Reference Wave");
            valid &= CheckReference(currentWave, "Current Wave");
            valid &= CheckReference(lockLamp, "Lock Lamp");

            if (phaseSlider != null && phaseSlider == gainSlider)
            {
                Debug.LogError(
                    "SignalScope: Phase Slider and Gain Slider " +
                    "must be different controls.", this);

                valid = false;
            }

            if (referenceWave != null &&
                referenceWave == currentWave)
            {
                Debug.LogError(
                    "SignalScope: Reference Wave and Current Wave " +
                    "must be different Line Renderers.", this);

                valid = false;
            }

            if (!valid)
            {
                enabled = false;
                return;
            }

            configured = true;
            stableSeconds = 0f;

            ConfigureLine(referenceWave, 0.016f);
            ConfigureLine(currentWave, 0.008f);
            SetLamp(false);
        }

        private bool CheckReference(
            UnityEngine.Object target,
            string fieldName)
        {
            if (target != null)
                return true;

            Debug.LogError(
                $"SignalScope ({name}): connect '{fieldName}' " +
                "in the Inspector.", this);

            return false;
        }

        private void ConfigureLine(LineRenderer line, float width)
        {
            line.enabled = false;
            line.useWorldSpace = false;
            line.loop = false;
            line.alignment = LineAlignment.View;
            line.positionCount = PointCount;
            line.startWidth = width;
            line.endWidth = width;
            line.startColor = Color.white;
            line.endColor = Color.white;
            line.shadowCastingMode = ShadowCastingMode.Off;
            line.receiveShadows = false;
        }

        private void LateUpdate()
        {
            bool powered = HasSignal;
            SetWaveVisibility(powered);

            if (!powered)
            {
                stableSeconds = 0f;
                SetLamp(false);
                return;
            }

            DrawWave(
                referenceWave,
                referencePoints,
                referenceFrequency,
                referencePhase,
                referenceGain);

            DrawWave(
                currentWave,
                currentPoints,
                frequencyDial.Value,
                phaseSlider.Value,
                gainSlider.Value);

            if (MatchesReference)
            {
                stableSeconds = Mathf.Min(
                    RequiredHold,
                    stableSeconds + Time.deltaTime);
            }
            else
            {
                stableSeconds = 0f;
            }

            SetLamp(IsLocked);
        }

        private void DrawWave(
            LineRenderer line,
            Vector3[] points,
            float frequency,
            float phaseDegrees,
            float gain)
        {
            float phase = phaseDegrees * Mathf.Deg2Rad;

            float amplitude =
                BaseAmplitude * Mathf.Clamp(gain, 0f, 1.25f);

            for (int i = 0; i < PointCount; i++)
            {
                float t = i / (float)(PointCount - 1);
                float x = (t - 0.5f) * ScreenWidth;

                float angle =
                    t * frequency * Mathf.PI * 2f - phase;

                float y = Mathf.Sin(angle) * amplitude;

                points[i] = new Vector3(x, y, 0f);
            }

            line.SetPositions(points);
        }

        private void SetWaveVisibility(bool visible)
        {
            if (referenceWave != null)
                referenceWave.enabled = visible;

            if (currentWave != null)
                currentWave.enabled = visible;
        }

        private void SetLamp(bool lit)
        {
            if (lockLamp != null)
                lockLamp.enabled = lit;
        }

        private void OnDisable()
        {
            stableSeconds = 0f;
            SetWaveVisibility(false);
            SetLamp(false);
        }
    }
}