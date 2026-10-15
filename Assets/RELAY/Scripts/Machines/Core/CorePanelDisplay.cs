using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(300)]
    public sealed class CorePanelDisplay : MonoBehaviour
    {
        [SerializeField] private PowerModule powerSource = null;
        [SerializeField] private CoreModule coreSource = null;
        [SerializeField] private CoolingModule coolingSource = null;
        [SerializeField] private Transform fillPivot = null;
        [SerializeField] private MeshRenderer fillRenderer = null;
        [SerializeField] private MeshRenderer heatLamp = null;
        [SerializeField] private MeshRenderer coldLamp = null;

        private Vector3 fullScale;
        private bool warning;
        private bool critical;
        private float blinkElapsed;

        private void Awake()
        {
            ResetWarnings();

            if (powerSource == null || coreSource == null ||
                coolingSource == null || fillPivot == null ||
                fillRenderer == null || heatLamp == null || coldLamp == null)
            {
                Debug.LogError(
                    "CorePanelDisplay: assign Power Source, Core Source, " +
                    "Cooling Source, Fill Pivot, Fill Renderer, Heat Lamp and Cold Lamp.", this);
                enabled = false;
                return;
            }

            if (heatLamp == coldLamp)
            {
                Debug.LogError(
                    "CorePanelDisplay: Heat Lamp and Cold Lamp " +
                    "must reference different renderers.", this);
                enabled = false;
                return;
            }

            if (!fillRenderer.transform.IsChildOf(fillPivot))
            {
                Debug.LogError(
                    "CorePanelDisplay: Fill Renderer must belong " +
                    "to the Fill object under FillPivot.", this);
                enabled = false;
                return;
            }

            fullScale = fillPivot.localScale;
            if (fullScale.x <= 0f)
            {
                Debug.LogError(
                    "CorePanelDisplay: FillPivot needs a positive X scale.", this);
                enabled = false;
                return;
            }

            SetFill(0f);
        }

        private void LateUpdate()
        {
            // The panel and its warnings require MAIN power, not AUX alone.
            bool powered = powerSource != null && powerSource.IsOnline &&
                coreSource != null && coreSource.isActiveAndEnabled;

            SetFill(powered ? coreSource.StartupProgress : 0f);

            if (!powered || coolingSource == null ||
                !coolingSource.isActiveAndEnabled)
            {
                ResetWarnings();
                return;
            }

            float temperature = coolingSource.Temperature;
            coldLamp.enabled = temperature < 65f;

            // Keep the existing temperature thresholds and hysteresis.
            if (warning)
            {
                if (temperature <= 77f)
                    warning = false;
            }
            else if (temperature >= 80f)
            {
                warning = true;
            }

            bool wasCritical = critical;
            if (!warning)
                critical = false;
            else if (critical)
            {
                if (temperature <= 82f)
                    critical = false;
            }
            else if (temperature >= 85f)
                critical = true;

            if (critical && !wasCritical)
                blinkElapsed = 0f;

            bool blinkOn = true;
            if (critical)
            {
                blinkOn = blinkElapsed < 0.5f;
                blinkElapsed = Mathf.Repeat(blinkElapsed + Time.deltaTime, 1f);
            }
            else
                blinkElapsed = 0f;

            heatLamp.enabled = warning && blinkOn;
        }

        private void SetFill(float progress)
        {
            progress = Mathf.Clamp01(progress);
            Vector3 scale = fullScale;
            scale.x *= Mathf.Max(0.0001f, progress);
            fillPivot.localScale = scale;
            fillRenderer.enabled = progress > 0f;
        }

        private void ResetWarnings()
        {
            warning = false;
            critical = false;
            blinkElapsed = 0f;
            if (heatLamp != null)
                heatLamp.enabled = false;
            if (coldLamp != null)
                coldLamp.enabled = false;
        }

        private void OnDisable()
        {
            if (fillRenderer != null)
                fillRenderer.enabled = false;
            ResetWarnings();
        }
    }
}
