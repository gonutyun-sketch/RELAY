using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class PoweredSwitch : MachineSwitch
    {
        [SerializeField] private PowerModule powerSource;

        private bool HasPower =>
            powerSource != null && powerSource.IsOnline;

        // 이후 냉각 계산에서 사용할 실제 펌프 작동 상태.
        public bool IsRunning =>
            isActiveAndEnabled && IsOn && HasPower;

        // 켜려면 전원이 필요하지만, 끄는 것은 항상 가능.
        public override bool CanInteract => IsOn || HasPower;

        protected override void Awake()
        {
            base.Awake();

            if (powerSource == null)
            {
                Debug.LogError(
                    "PoweredSwitch: assign Power Source.", this);
            }
        }

        public override void Interact()
        {
            if (!CanInteract) return;

            base.Interact();
        }

        private void LateUpdate()
        {
            // 전원이 끊기면 스위치도 OFF로 복귀.
            // 전원이 돌아와도 사용자가 다시 켜야 한다.
            if (IsOn && !HasPower)
                SetState(false);
        }
    }
}