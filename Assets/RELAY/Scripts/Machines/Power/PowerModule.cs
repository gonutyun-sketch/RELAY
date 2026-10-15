using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(100)]
    public sealed class PowerModule : MonoBehaviour
    {
        [SerializeField] private MachineSwitch auxPower;
        [SerializeField] private MachineDial voltageDial;
        [SerializeField] private MachineDial balanceDial;
        [SerializeField] private MachineLever mainLever;
        private bool configured;

        private bool ControlsAvailable =>
            configured && isActiveAndEnabled
            && auxPower != null && auxPower.isActiveAndEnabled
            && voltageDial != null && voltageDial.isActiveAndEnabled
            && balanceDial != null && balanceDial.isActiveAndEnabled
            && mainLever != null && mainLever.isActiveAndEnabled;

        public bool IsAuxPowered => ControlsAvailable && auxPower.IsOn;
        public float Voltage => IsAuxPowered ? PowerCalibrationRule.Voltage(voltageDial.Value, balanceDial.Value) : 0f;
        public float Current => IsAuxPowered ? PowerCalibrationRule.Current(voltageDial.Value, balanceDial.Value) : 0f;
        public bool CanEngage => IsAuxPowered && PowerCalibrationRule.Matches(Voltage, Current);
        public bool IsOnline => CanEngage && mainLever.IsOn;

        // Keep this API for existing consumers; do not expose a solution in hover text.
        public string BlockedReason
        {
            get
            {
                if (!ControlsAvailable) return "Power module unavailable";
                if (!auxPower.IsOn) return "AUX power off";
                if (Voltage != PowerCalibrationRule.RequiredVoltage) return "Voltage fault";
                if (Current != PowerCalibrationRule.RequiredCurrent) return "Current fault";
                return "";
            }
        }

        private void Awake()
        {
            if (mainLever != null)
            {
                if (mainLever.PowerSource != null && mainLever.PowerSource != this)
                {
                    Debug.LogError("PowerModule: MAIN is connected to another module.", this);
                    enabled = false;
                    return;
                }
                mainLever.BindPowerSource(this);
            }
            if (auxPower == null || voltageDial == null || balanceDial == null || mainLever == null ||
                auxPower == mainLever || voltageDial == balanceDial)
            {
                Debug.LogError("PowerModule: assign separate AUX, Voltage Dial, Balance Dial and MAIN controls.", this);
                enabled = false;
                return;
            }
            // 75 on the voltage control and 50 on balance produce measured 70 V / 30 A.
            if (voltageDial.MinValue > 75f || voltageDial.MaxValue < 75f ||
                balanceDial.MinValue > 50f || balanceDial.MaxValue < 50f)
            {
                Debug.LogError("PowerModule: Voltage Dial must include 75 and Balance Dial must include 50.", this);
                enabled = false;
                return;
            }
            configured = true;
        }

        private void Update()
        {
            // A changed setting trips MAIN. Restoring the values never re-engages it automatically.
            if (mainLever != null && mainLever.IsOn && !CanEngage) mainLever.SetState(false);
        }

        private void OnDisable()
        {
            if (mainLever != null && mainLever.PowerSource == this) mainLever.SetState(false);
        }
    }
}
