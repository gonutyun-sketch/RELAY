using TMPro;
using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(200)]
    public sealed class CoreModule : MonoBehaviour
    {
        [SerializeField] private PowerModule powerSource;
        [SerializeField] private CoolingModule coolingSource;
        [SerializeField] private SignalScope signalSource;
        [SerializeField] private CoreStartLever startLever;
        [SerializeField] private MeshRenderer startupLamp;
        [SerializeField] private TMP_Text statusText;

        private const float HeatRampSeconds = 6f;
        private const float MinimumRunSeconds = 30f;
        private const float StableHoldSeconds = 8f;
        private const float TimeoutSeconds = 60f;
        private const float OverheatTemperature = 90f;

        private bool configured;
        private bool running;
        private float elapsed;
        private float stableElapsed;
        private string idleMessage = "STANDBY";

        public bool IsComplete { get; private set; }

        public bool HasAuxPower =>
    ConnectionsAvailable && powerSource.IsAuxPowered;

        public float StartupProgress
        {
            get
            {
                if (IsComplete)
                    return 1f;

                if (!IsStarting)
                    return 0f;

                float warmup = Mathf.Clamp01(
                    elapsed / MinimumRunSeconds);

                float stability = Mathf.Clamp01(
                    stableElapsed / StableHoldSeconds);

                // Full progress requires both warmup and stabilization.
                float stabilityLimit = 0.85f + 0.15f * stability;

                return Mathf.Min(warmup, stabilityLimit);
            }
        }

        private bool ConnectionsAvailable =>
            configured &&
            isActiveAndEnabled &&
            powerSource != null &&
            powerSource.isActiveAndEnabled &&
            coolingSource != null &&
            coolingSource.isActiveAndEnabled &&
            coolingSource.CoreSource == this &&
            signalSource != null &&
            signalSource.isActiveAndEnabled &&
            startLever != null &&
            startLever.isActiveAndEnabled &&
            startLever.CoreSource == this;

        public bool CanStart =>
            ConnectionsAvailable &&
            !IsComplete &&
            !running &&
            !startLever.IsOn &&
            powerSource.IsOnline &&
            coolingSource.IsStable &&
            signalSource.IsLocked;

        public bool IsStarting =>
            running &&
            ConnectionsAvailable &&
            startLever.IsOn &&
            powerSource.IsOnline;

        public float HeatLoad
        {
            get
            {
                if (!ConnectionsAvailable ||
                    !powerSource.IsOnline ||
                    !startLever.IsOn)
                {
                    return 0f;
                }

                if (IsComplete)
                    return 1f;

                return running
                    ? Mathf.Clamp01(elapsed / HeatRampSeconds)
                    : 0f;
            }
        }

        private void Awake()
        {
            bool valid = true;

            valid &= CheckReference(powerSource, "Power Source");
            valid &= CheckReference(coolingSource, "Cooling Source");
            valid &= CheckReference(signalSource, "Signal Source");
            valid &= CheckReference(startLever, "Start Lever");
            valid &= CheckReference(startupLamp, "Startup Lamp");
            valid &= CheckReference(statusText, "Status Text");

            if (coolingSource != null &&
                coolingSource.CoreSource != this)
            {
                Debug.LogError(
                    "CoreModule: Cooling Module's Core Source " +
                    "must point to this CORE_Module.", this);

                valid = false;
            }

            if (startLever != null &&
                startLever.CoreSource != null &&
                startLever.CoreSource != this)
            {
                Debug.LogError(
                    "CoreModule: Start Lever belongs to another module.",
                    this);

                valid = false;
            }

            if (!valid)
            {
                enabled = false;
                return;
            }

            startLever.BindCoreSource(this);
            startLever.SetState(false);
            configured = true;
            RefreshDisplay();
        }

        private bool CheckReference(
            UnityEngine.Object target,
            string fieldName)
        {
            if (target != null)
                return true;

            Debug.LogError(
                $"CoreModule ({name}): connect '{fieldName}' " +
                "in the Inspector.", this);

            return false;
        }

        private void LateUpdate()
        {
            // Completion is retained for the later exit sequence.
            if (IsComplete)
            {
                if (!ConnectionsAvailable || !powerSource.IsOnline)
                    StopOwnedLever();

                RefreshDisplay();
                return;
            }

            if (!ConnectionsAvailable || !powerSource.IsOnline)
            {
                if (running || (startLever != null && startLever.IsOn))
                    AbortStartup("POWER / CONNECTION LOST");

                RefreshDisplay();
                return;
            }

            if (!startLever.IsOn)
            {
                if (running)
                    AbortStartup("STARTUP CANCELLED");

                RefreshDisplay();
                return;
            }

            if (!running)
            {
                // Recheck when a new startup actually begins.
                if (!coolingSource.IsStable || !signalSource.IsLocked)
                {
                    AbortStartup("STARTUP ABORTED");
                    RefreshDisplay();
                    return;
                }

                running = true;
                elapsed = 0f;
                stableElapsed = 0f;
            }

            elapsed += Time.deltaTime;

            if (coolingSource.Temperature >= OverheatTemperature)
            {
                AbortStartup("OVERHEAT");
                RefreshDisplay();
                return;
            }

            bool stable =
                elapsed >= HeatRampSeconds &&
                coolingSource.IsStable &&
                signalSource.IsLocked;

            stableElapsed = stable
                ? stableElapsed + Time.deltaTime
                : 0f;

            if (elapsed >= MinimumRunSeconds &&
                stableElapsed >= StableHoldSeconds)
            {
                IsComplete = true;
                running = false;
            }
            else if (elapsed >= TimeoutSeconds)
            {
                AbortStartup("STABILIZATION FAILED");
            }

            RefreshDisplay();
        }

        private void AbortStartup(string reason)
        {
            running = false;
            elapsed = 0f;
            stableElapsed = 0f;
            idleMessage = reason;
            StopOwnedLever();
        }

        private void StopOwnedLever()
        {
            if (startLever != null &&
                startLever.CoreSource == this &&
                startLever.IsOn)
            {
                startLever.SetState(false);
            }
        }

        private void RefreshDisplay()
        {
            bool powered =
                ConnectionsAvailable && powerSource.IsOnline;

            if (startupLamp != null)
            {
                bool blinkOn = Mathf.Repeat(elapsed, 1f) < 0.5f;

                startupLamp.enabled =
                    powered && (IsComplete || (running && blinkOn));
            }

            if (statusText == null)
                return;

            if (IsComplete)
            {
                statusText.text = "STARTUP COMPLETE";
            }
            else if (running)
            {
                statusText.text = elapsed < MinimumRunSeconds
                    ? "STARTING"
                    : "STABILIZING";
            }
            else
            {
                statusText.text = idleMessage;
            }
        }

        private void OnDisable()
        {
            running = false;
            elapsed = 0f;
            stableElapsed = 0f;
            StopOwnedLever();

            if (startupLamp != null)
                startupLamp.enabled = false;

            if (statusText != null)
                statusText.text = "OFFLINE";
        }
    }
}