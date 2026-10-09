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

        [SerializeField] private float minVoltage = 70f;
        [SerializeField] private float maxVoltage = 80f;
        [SerializeField] private float maxCurrent = 40f;

        private bool configured;

        private bool ControlsAvailable =>
            configured && isActiveAndEnabled
            && auxPower != null && auxPower.isActiveAndEnabled
            && voltageDial != null && voltageDial.isActiveAndEnabled
            && balanceDial != null && balanceDial.isActiveAndEnabled
            && mainLever != null && mainLever.isActiveAndEnabled;

        private float Balance =>
            Mathf.Clamp(balanceDial.Value, 0f, 100f);

        public bool IsAuxPowered =>
            ControlsAvailable && auxPower.IsOn;

        // 부하 분배 조절에 따른 전압 변화를 단순화한 게임용 계산.
        public float Voltage => IsAuxPowered
            ? Mathf.Max(0f, voltageDial.Value - Balance * 0.1f)
            : 0f;

        // 중앙에서 멀어질수록 불필요한 전류 부담이 커진다.
        public float Current => IsAuxPowered
            ? voltageDial.Value
                * (0.4f + Mathf.Abs(Balance - 50f) * 0.008f)
            : 0f;

        public bool CanEngage =>
            IsAuxPowered
            && Voltage >= minVoltage
            && Voltage <= maxVoltage
            && Current <= maxCurrent;

        public bool IsOnline =>
            CanEngage && mainLever.IsOn;

        // 내부 상태 설명용. 현재 조준 안내에는 표시하지 않는다.
        public string BlockedReason
        {
            get
            {
                if (!ControlsAvailable)
                    return "Power module unavailable";
                if (!auxPower.IsOn)
                    return "AUX power off";
                if (Voltage < minVoltage || Voltage > maxVoltage)
                    return "Voltage fault";
                if (Current > maxCurrent)
                    return "Overcurrent";

                return "";
            }
        }

        private void Awake()
        {
            if (mainLever != null)
            {
                if (mainLever.PowerSource != null
                    && mainLever.PowerSource != this)
                {
                    Debug.LogError(
                        "PowerModule: MAIN is connected to another module.",
                        this);
                    enabled = false;
                    return;
                }

                mainLever.BindPowerSource(this);
            }

            if (auxPower == null || voltageDial == null
                || balanceDial == null || mainLever == null
                || auxPower == mainLever
                || voltageDial == balanceDial)
            {
                Debug.LogError(
                    "PowerModule: assign separate AUX, Voltage Dial, "
                    + "Balance Dial and MAIN controls.", this);
                enabled = false;
                return;
            }

            if (minVoltage > maxVoltage
                || minVoltage < voltageDial.MinValue
                || maxVoltage > voltageDial.MaxValue
                || maxCurrent <= 0f)
            {
                Debug.LogError(
                    "PowerModule: check voltage and current limits.",
                    this);
                enabled = false;
                return;
            }

            configured = true;
        }

        private void Update()
        {
            // 条件이 깨지면 해제한다. 복구 후 자동 재투입하지 않는다.
            if (mainLever != null && mainLever.IsOn && !CanEngage)
                mainLever.SetState(false);
        }

        private void OnDisable()
        {
            if (mainLever != null && mainLever.PowerSource == this)
                mainLever.SetState(false);
        }
    }
}