using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;

namespace Startup
{
    // FirstPersonMotor.Awake (-100) must cache the normal camera height first.
    // Start runs before the first Update, so gameplay input cannot leak through.
    [DefaultExecutionOrder(-50)]
    [DisallowMultipleComponent]
    [AddComponentMenu("RELAY/Wake Up Prologue")]
    public sealed class WakeUpPrologue : MonoBehaviour
    {
        [Header("Existing Player / New Overlay")]
        [SerializeField] private FirstPersonMotor motor;
        [SerializeField] private WakeUpEyelids eyelids;

        [Header("Playback")]
        [SerializeField] private bool playOnStart = true;
        [SerializeField, Range(4f, 12f)] private float duration = 8f;
        [SerializeField, Range(0.2f, 0.6f)] private float lyingEyeHeight = 0.28f;
        [SerializeField, Range(0.4f, 1f)] private float lookAmount = 1f;
        [SerializeField] private bool allowSpaceSkip = true;

        private Transform view;
        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;
        private Vector3 restPosition;
        private Quaternion restRotation;
        private bool savedMotorEnabled;
        private bool savedInteractorEnabled;
        private bool savedDragEnabled;
        private bool running;
        private bool finishPending;
        private bool releaseOnFinish;
        private bool waitingForClick;
        private float elapsed;

        public bool IsPlaying => running;

        // Normalized time, rise from lying to standing, pitch/yaw/roll.
        private static readonly float[] PoseTimes =
            { 0f, 0.25f, 0.39f, 0.54f, 0.66f, 0.75f, 0.93f, 1f };
        private static readonly float[] Rise =
            { 0f, 0f, 0.03f, 0.03f, 0.48f, 0.43f, 1f, 1f };
        private static readonly Vector3[] Angles =
        {
            new Vector3(-32f, -8f, -16f),
            new Vector3(-25f, -8f, -13f),
            new Vector3(-12f, -28f, -8f),
            new Vector3(-8f, 24f, -5f),
            new Vector3(10f, 6f, -3f),
            new Vector3(16f, 3f, -1f),
            new Vector3(-1.5f, 0f, 0f),
            Vector3.zero
        };
        private static readonly float[] EyeTimes =
            { 0f, 0.05f, 0.14f, 0.16f, 0.18f, 0.195f,
              0.26f, 0.275f, 0.29f, 0.30f, 0.33f, 1f };
        private static readonly float[] EyeOpen =
            { 0f, 0f, 0.38f, 0.38f, 0f, 0f,
              1f, 1f, 0f, 0f, 1f, 1f };

        public FirstPersonMotor Motor => motor;

        // A title screen calls this in Awake, before this component's Start.
        public void WaitForStartButton()
        {
            playOnStart = false;
        }

        private void Start()
        {
            if (playOnStart) TryBegin();
            else if (!running) ClearOverlay();
        }

        // Called from the title screen's LateUpdate after restoring input components.
        // The intro takes control immediately, before another Update can run.
        public bool TryBegin()
        {
            if (!isActiveAndEnabled || running) return false;

            if (motor == null || eyelids == null ||
                !motor.isActiveAndEnabled || motor.ViewCamera == null)
            {
                Fail("Assign the active Player motor and the new WakeUpOverlay.");
                return false;
            }

            view = motor.ViewCamera;
            interactor = motor.GetComponent<PlayerInteractor>();
            sliderDrag = motor.GetComponent<SliderDragInput>();
            Canvas overlayCanvas = eyelids.canvas;
            RectTransform overlayRect = eyelids.rectTransform;

            if (interactor == null || sliderDrag == null ||
                !interactor.isActiveAndEnabled || !sliderDrag.isActiveAndEnabled ||
                view.parent != motor.transform || motor.CameraRestLocalPosition.y < 0.8f)
            {
                Fail("Use the existing working Player with its direct-child Main Camera.");
                return false;
            }
            if (!eyelids.isActiveAndEnabled || overlayCanvas == null ||
                !overlayCanvas.isActiveAndEnabled ||
                overlayCanvas.renderMode != RenderMode.ScreenSpaceOverlay ||
                overlayRect.parent != overlayCanvas.transform ||
                (overlayRect.anchorMin - Vector2.zero).sqrMagnitude > 0.0001f ||
                (overlayRect.anchorMax - Vector2.one).sqrMagnitude > 0.0001f ||
                overlayRect.offsetMin.sqrMagnitude > 0.01f ||
                overlayRect.offsetMax.sqrMagnitude > 0.01f ||
                (overlayRect.localScale - Vector3.one).sqrMagnitude > 0.0001f ||
                Quaternion.Angle(overlayRect.localRotation, Quaternion.identity) > 0.01f)
            {
                Fail("WakeUpOverlay must be a full-stretch direct child of the Overlay Canvas, with zero offsets, zero rotation and unit scale.");
                return false;
            }

            restPosition = motor.CameraRestLocalPosition;
            restRotation = view.localRotation;
            savedMotorEnabled = motor.enabled;
            savedInteractorEnabled = interactor.enabled;
            savedDragEnabled = sliderDrag.enabled;
            elapsed = 0f;
            finishPending = false;
            releaseOnFinish = false;
            running = true;

            sliderDrag.enabled = false;
            interactor.enabled = false;
            motor.enabled = false;
            // PauseSettings already ignores Escape while the motor is disabled.
            // Its settings, listeners, time scale and audio state stay intact.
            if (EventSystem.current != null)
                EventSystem.current.SetSelectedGameObject(null);

            waitingForClick = !Application.isFocused;
            SetCursor(!waitingForClick);
            ApplyFrame(0f);
            return true;
        }

        private void Update()
        {
            if (!running || finishPending) return;

            if (!Application.isFocused)
            {
                waitingForClick = true;
                SetCursor(false);
                return;
            }

            Keyboard keyboard = Keyboard.current;
            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
            {
                // Escape exits the intro and releases the pointer.
                // The next click only captures it, using the existing motor rule.
                releaseOnFinish = true;
                finishPending = true;
                return;
            }
            if (allowSpaceSkip && keyboard != null &&
                keyboard.spaceKey.wasPressedThisFrame)
            {
                finishPending = true;
                return;
            }

            if (Cursor.lockState != CursorLockMode.Locked)
                waitingForClick = true;

            if (waitingForClick)
            {
                Mouse mouse = Mouse.current;
                if (mouse != null && mouse.leftButton.wasPressedThisFrame)
                {
                    waitingForClick = false;
                    SetCursor(true);
                }
                // Do not advance the sequence on the focus-capture click.
                return;
            }

            if (Time.timeScale <= 0f) return;
            elapsed += Mathf.Min(Time.deltaTime, 0.1f);
            if (elapsed >= Mathf.Max(4f, duration))
                finishPending = true;
        }

        private void LateUpdate()
        {
            if (!running) return;
            if (finishPending)
            {
                // All Update input handlers have finished for this frame.
                Finish(!releaseOnFinish && !waitingForClick && Application.isFocused);
                return;
            }
            ApplyFrame(Mathf.Clamp01(elapsed / Mathf.Max(4f, duration)));
        }

        private void ApplyFrame(float t)
        {
            int i = Segment(PoseTimes, t);
            float blend = Blend(PoseTimes[i], PoseTimes[i + 1], t);
            float rise = Mathf.Lerp(Rise[i], Rise[i + 1], blend);
            float low = Mathf.Clamp(lyingEyeHeight, 0.2f, restPosition.y - 0.1f);
            Vector3 position = restPosition;
            position.y = Mathf.Lerp(low, restPosition.y, rise);
            view.localPosition = position;

            Quaternion a = Quaternion.Euler(Angles[i] * lookAmount);
            Quaternion b = Quaternion.Euler(Angles[i + 1] * lookAmount);
            view.localRotation = restRotation * Quaternion.Slerp(a, b, blend);

            int eye = Segment(EyeTimes, t);
            eyelids.OpenAmount = Mathf.Lerp(EyeOpen[eye], EyeOpen[eye + 1],
                Blend(EyeTimes[eye], EyeTimes[eye + 1], t));
        }

        private static int Segment(float[] times, float t)
        {
            for (int i = 0; i < times.Length - 2; i++)
                if (t <= times[i + 1]) return i;
            return times.Length - 2;
        }

        private static float Blend(float from, float to, float t)
        {
            return Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(from, to, t));
        }

        private void Finish(bool captureCursor)
        {
            if (!running) return;
            running = false;
            finishPending = false;
            ClearOverlay();

            // Restore the exact saved pose BEFORE OnEnable re-syncs mouse look.
            if (view != null)
            {
                view.localPosition = restPosition;
                view.localRotation = restRotation;
            }
            if (motor != null) motor.enabled = savedMotorEnabled;
            if (interactor != null) interactor.enabled = savedInteractorEnabled;
            if (sliderDrag != null) sliderDrag.enabled = savedDragEnabled;
            SetCursor(captureCursor && motor != null && motor.isActiveAndEnabled);
        }

        private void ClearOverlay()
        {
            if (eyelids != null) eyelids.OpenAmount = 1f;
        }

        private void Fail(string message)
        {
            ClearOverlay();
            Debug.LogError("WakeUpPrologue: " + message, this);
            enabled = false;
        }

        private static void SetCursor(bool captured)
        {
            Cursor.lockState = captured ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !captured;
        }

        private void OnApplicationFocus(bool focused)
        {
            if (running && !focused)
            {
                waitingForClick = true;
                SetCursor(false);
            }
        }

        private void OnDisable()
        {
            if (running) Finish(false);
            else ClearOverlay();
        }
    }
}
