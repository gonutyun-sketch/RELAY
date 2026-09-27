using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Startup
{
    // Quiet contextual prompts; all UI objects are assembled by the user.
    public sealed class PlayerInteractor : MonoBehaviour
    {
        [SerializeField] private FirstPersonMotor motor;
        [SerializeField] private Camera viewCamera;
        [SerializeField] private TMP_Text promptText;
        [SerializeField, Min(0.1f)] private float reach = 2.5f;
        [SerializeField] private LayerMask raycastMask = Physics.DefaultRaycastLayers;
        [SerializeField] private CanvasGroup promptGroup;
        [SerializeField] private Image aimDot;
        [SerializeField, Min(0.01f)] private float fadeSeconds = 0.12f;
        [SerializeField, Min(0f)] private float clickFeedbackSeconds = 0.16f;

        private readonly Color idleDot = new Color32(240, 240, 232, 125);
        private readonly Color focusedDot = new Color32(240, 240, 232, 255);
        private readonly Color failedDot = new Color32(235, 65, 65, 255);
        private bool showPrompt;
        private float clickFeedbackRemaining;
        private float feedbackDuration;
        private bool feedbackFailed;

        public float Reach => reach;

        public bool TryGetTarget(out Interactable target)
        {
            target = null;

            if (!isActiveAndEnabled || viewCamera == null)
                return false;

            Ray ray = viewCamera.ViewportPointToRay(
                new Vector3(0.5f, 0.5f, 0f));

            if (!Physics.Raycast(
                ray,
                out RaycastHit hit,
                reach,
                raycastMask,
                QueryTriggerInteraction.Ignore))
            {
                return false;
            }

            target = hit.collider.GetComponentInParent<Interactable>();

            return target != null && target.isActiveAndEnabled;
        }

        private void Awake()
        {
            if (motor == null || viewCamera == null || promptText == null || promptGroup == null || aimDot == null)
            {
                Debug.LogError("PlayerInteractor: assign Motor, View Camera, Prompt Text, Prompt Group and Aim Dot.", this);
                enabled = false;
                return;
            }
            if (motor.ViewCamera != viewCamera.transform)
            {
                Debug.LogError("PlayerInteractor: use the same Main Camera as FirstPersonMotor.", this);
                enabled = false;
                return;
            }
            promptGroup.alpha = 0f;
            promptGroup.interactable = false;
            promptGroup.blocksRaycasts = false;
            // TMP creates a material instance for these overrides; the font asset is not edited.
            promptText.outlineWidth = 0.12f;
            promptText.outlineColor = new Color32(0, 0, 0, 180);
        }

        private void Update()
        {
            bool playing = motor.isActiveAndEnabled && motor.HasControl;
            aimDot.enabled = playing;
            aimDot.color = idleDot;
            showPrompt = false;
            if (!playing) clickFeedbackRemaining = 0f;

            if (!motor.isActiveAndEnabled) return;
            if (!motor.HasControl)
            {
                promptText.text = "Click to continue";
                showPrompt = true;
                return;
            }
            // First click captures the cursor only, with no success or failure pulse.
            if (!motor.CanInteractThisFrame)
            {
                if (motor.IsManipulating)
                {
                    aimDot.color = focusedDot;
                    promptText.text = "Release LMB to let go";
                    showPrompt = true;
                }

                return;
            }

            Ray ray = viewCamera.ViewportPointToRay(new Vector3(0.5f, 0.5f, 0f));
            if (!Physics.Raycast(ray, out RaycastHit hit, reach, raycastMask, QueryTriggerInteraction.Ignore)) return;
            Interactable target = hit.collider.GetComponentInParent<Interactable>();
            if (target == null || !target.isActiveAndEnabled) return;

            bool canInteract = target.CanInteract;
            bool canAdjust = target.CanAdjust;
            bool supportsAttempt = target is MachineSwitch || target is ElevatorButton;
            // A lever can be attempted even when locked. Gauges remain read-only.
            if (!canInteract && !canAdjust && !supportsAttempt) return;

            Mouse mouse = Mouse.current;
            Keyboard keyboard = Keyboard.current;
            if (mouse != null && mouse.leftButton.wasPressedThisFrame && (canInteract || supportsAttempt))
            {
                if (canInteract)
                {
                    target.Interact();
                    BeginFeedback(false);
                }
                else
                {
                    // Do not operate the lever or expose the reason/answer in the prompt.
                    BeginFeedback(true);
                }
            }
            else if (canAdjust && keyboard != null)
            {
                int direction = (keyboard.rKey.wasPressedThisFrame ? 1 : 0) - (keyboard.qKey.wasPressedThisFrame ? 1 : 0);
                if (direction != 0) target.Adjust(direction);
            }

            if (target == null || !target.isActiveAndEnabled) return;
            aimDot.color = focusedDot;
            showPrompt = true;
            if (target is MachineLever lever)
                promptText.text = lever.Prompt;
            else if (target is CoreStartLever coreLever)
                promptText.text = coreLever.Prompt;
            else if (target is MachineSwitch toggle)
                promptText.text = toggle.IsOn ? "Switch off" : "Switch on";
            else if (target is MachineDial)
                promptText.text = "Click to increase / Q to decrease";
            else if (target is MachineSlider slider)
                promptText.text = slider.Prompt;
            else
                promptText.text = target.Prompt;
        }

        private void BeginFeedback(bool failed)
        {
            feedbackFailed = failed;
            // 0.16 s for normal input; 0.20 s for a refused lever attempt at current settings.
            feedbackDuration = Mathf.Max(0f, clickFeedbackSeconds) * (failed ? 1.25f : 1f);
            clickFeedbackRemaining = feedbackDuration;
        }

        private void LateUpdate()
        {
            promptGroup.alpha = Mathf.MoveTowards(promptGroup.alpha, showPrompt ? 1f : 0f,
                Time.unscaledDeltaTime / Mathf.Max(0.01f, fadeSeconds));

            float size = 4f;
            if (clickFeedbackRemaining > 0f && feedbackDuration > 0f)
            {
                float progress = Mathf.Clamp01(1f - clickFeedbackRemaining / feedbackDuration);
                if (feedbackFailed)
                {
                    // A single red 4 -> 8 -> 4 pulse, anchored to the existing center dot.
                    size = progress < 0.4f
                        ? Mathf.Lerp(4f, 8f, Mathf.SmoothStep(0f, 1f, progress / 0.4f))
                        : Mathf.Lerp(8f, 4f, Mathf.SmoothStep(0f, 1f, (progress - 0.4f) / 0.6f));
                    float recover = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01((progress - 0.5f) / 0.5f));
                    aimDot.color = Color.Lerp(failedDot, aimDot.color, recover);
                }
                else if (progress < 0.25f)
                    size = Mathf.Lerp(4f, 2.5f, Mathf.SmoothStep(0f, 1f, progress / 0.25f));
                else if (progress < 0.55f)
                    size = Mathf.Lerp(2.5f, 6f, Mathf.SmoothStep(0f, 1f, (progress - 0.25f) / 0.30f));
                else
                    size = Mathf.Lerp(6f, 4f, Mathf.SmoothStep(0f, 1f, (progress - 0.55f) / 0.45f));

                clickFeedbackRemaining = Mathf.Max(0f, clickFeedbackRemaining - Time.unscaledDeltaTime);
            }
            aimDot.rectTransform.SetSizeWithCurrentAnchors(RectTransform.Axis.Horizontal, size);
            aimDot.rectTransform.SetSizeWithCurrentAnchors(RectTransform.Axis.Vertical, size);
        }

        private void OnDisable()
        {
            clickFeedbackRemaining = 0f;
            if (promptGroup != null) promptGroup.alpha = 0f;
            if (aimDot != null) aimDot.enabled = false;
            if (promptText != null) promptText.text = "";
        }
    }
}
