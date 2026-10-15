using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class CoolingModule : MonoBehaviour
    {
        [SerializeField] private PoweredSwitch pump;
        [SerializeField] private MachineDial flowValve;
        [SerializeField, Min(0.01f)] private float maxFlow = 100f;
        [SerializeField] private CoreModule coreSource;

        private float temperature = 100f;

        public CoreModule CoreSource => coreSource;
        public float MaxFlow => Mathf.Max(0.01f, maxFlow);
        public float Temperature => temperature;

        public bool IsPumping =>
            isActiveAndEnabled &&
            pump != null &&
            flowValve != null &&
            flowValve.isActiveAndEnabled &&
            pump.IsRunning;

        public float ValveOpening =>
            flowValve == null
                ? 0f
                : Mathf.InverseLerp(
                    flowValve.MinValue,
                    flowValve.MaxValue,
                    flowValve.Value);

        public float Flow =>
            IsPumping ? MaxFlow * ValveOpening : 0f;

        public float Pressure =>
            IsPumping ? 80f - 40f * ValveOpening : 0f;

        public bool IsStable =>
            IsPumping &&
            Flow >= 50f &&
            Pressure >= 45f &&
            Pressure <= 60f &&
            Temperature >= 65f &&
            Temperature <= 75f;

        private void Awake()
        {
            temperature = 100f;

            if (pump == null ||
                flowValve == null ||
                coreSource == null)
            {
                Debug.LogError(
                    "CoolingModule: assign Pump, Flow Valve " +
                    "and Core Source.", this);

                enabled = false;
            }
        }

        private void Update()
        {
            float flowRatio = Mathf.Clamp01(Flow / MaxFlow);

            float coreHeat = coreSource != null
                ? 12f * coreSource.HeatLoad
                : 0f;

            float targetTemperature =
                Mathf.Lerp(100f, 50f, flowRatio) + coreHeat;

            temperature = Mathf.MoveTowards(
                temperature,
                targetTemperature,
                4f * Time.deltaTime);
        }
    }
}