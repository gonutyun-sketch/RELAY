using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(400)]
    public sealed class DoorRevealSequence : MonoBehaviour
    {
        [SerializeField] private CoreModule coreSource;
        [SerializeField] private ExitDoor exitDoor;
        [SerializeField] private FirstPersonMotor motor;
        [SerializeField] private Transform revealPoint;
        [SerializeField] private CanvasGroup screenFade;

        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;
        private Camera viewCamera;

        private Vector3 savedCameraPosition;
        private Quaternion savedCameraRotation;
        private float savedFieldOfView;

        private bool motorWasEnabled;
        private bool interactorWasEnabled;
        private bool dragWasEnabled;
        private bool hadControl;
        private bool cursorReleased;

        private bool ready;
        private bool played;
        private bool playing;

        private void Start()
        {
            if (coreSource == null ||
                exitDoor == null ||
                motor == null ||
                revealPoint == null ||
                screenFade == null)
            {
                Fail("Assign all five Inspector references.");
                return;
            }

            interactor = motor.GetComponent<PlayerInteractor>();
            sliderDrag = motor.GetComponent<SliderDragInput>();

            if (motor.ViewCamera != null)
                viewCamera = motor.ViewCamera.GetComponent<Camera>();

            if (interactor == null ||
                sliderDrag == null ||
                viewCamera == null)
            {
                Fail("Player needs its existing input scripts and camera.");
                return;
            }

            if (exitDoor.Source != coreSource)
            {
                Fail("Core Source must match Exit Door's Core Source.");
                return;
            }

            screenFade.alpha = 0f;
            screenFade.interactable = false;
            screenFade.blocksRaycasts = false;

            if (!exitDoor.TryHoldOpening(this))
            {
                Fail("Could not reserve the door opening.");
                return;
            }

            ready = true;
        }

        private void Fail(string message)
        {
            Debug.LogError("DoorRevealSequence: " + message, this);
            enabled = false;
        }

        private void Update()
        {
            if (!playing)
                return;

            Keyboard keyboard = Keyboard.current;

            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
            {
                cursorReleased = true;
                UnlockCursor();
            }
        }

        private void LateUpdate()
        {
            if (!ready || played || !coreSource.IsComplete)
                return;

            // Wait until the player is actually controlling the game.
            if (!motor.isActiveAndEnabled || !motor.HasControl)
                return;

            played = true;
            StartCoroutine(PlaySequence());
        }

        private IEnumerator PlaySequence()
        {
            savedCameraPosition = viewCamera.transform.localPosition;
            savedCameraRotation = viewCamera.transform.localRotation;
            savedFieldOfView = viewCamera.fieldOfView;

            motorWasEnabled = motor.enabled;
            interactorWasEnabled = interactor.enabled;
            dragWasEnabled = sliderDrag.enabled;
            hadControl = motor.HasControl;
            cursorReleased = false;
            playing = true;

            sliderDrag.enabled = false;
            interactor.enabled = false;
            motor.enabled = false;
            Cursor.visible = false;

            yield return FadeTo(1f);

            viewCamera.transform.SetPositionAndRotation(
                revealPoint.position,
                revealPoint.rotation);

            viewCamera.fieldOfView = 55f;

            yield return FadeTo(0f);
            yield return new WaitForSeconds(0.3f);

            exitDoor.ReleaseOpening(this);

            float waited = 0f;
            float timeout = exitDoor.OpenDuration + 2f;

            while (exitDoor != null &&
                   exitDoor.isActiveAndEnabled &&
                   !exitDoor.IsOpen &&
                   waited < timeout)
            {
                waited += Time.deltaTime;
                yield return null;
            }

            if (exitDoor == null || !exitDoor.IsOpen)
            {
                Debug.LogWarning(
                    "DoorRevealSequence: door did not finish opening. " +
                    "Returning control to the player.", this);
            }

            yield return new WaitForSeconds(0.5f);
            yield return FadeTo(1f);

            RestoreCamera();

            yield return FadeTo(0f);

            RestoreControls();
        }

        private IEnumerator FadeTo(float target)
        {
            float start = screenFade.alpha;
            float elapsed = 0f;
            const float duration = 0.2f;

            while (elapsed < duration)
            {
                elapsed += Time.unscaledDeltaTime;

                float t = Mathf.Clamp01(elapsed / duration);

                screenFade.alpha = Mathf.Lerp(
                    start, target, Mathf.SmoothStep(0f, 1f, t));

                yield return null;
            }

            screenFade.alpha = target;
        }

        private void RestoreCamera()
        {
            if (viewCamera == null)
                return;

            viewCamera.transform.localPosition = savedCameraPosition;
            viewCamera.transform.localRotation = savedCameraRotation;
            viewCamera.fieldOfView = savedFieldOfView;
        }

        private void RestoreControls()
        {
            if (!playing)
                return;

            if (motor != null)
                motor.enabled = motorWasEnabled;

            if (interactor != null)
                interactor.enabled = interactorWasEnabled;

            if (sliderDrag != null)
                sliderDrag.enabled = dragWasEnabled;

            bool capture =
                hadControl &&
                Application.isFocused &&
                !cursorReleased;

            Cursor.lockState = capture
                ? CursorLockMode.Locked
                : CursorLockMode.None;

            Cursor.visible = !capture;
            playing = false;
        }

        private static void UnlockCursor()
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        private void OnApplicationFocus(bool focused)
        {
            if (playing && !focused)
            {
                cursorReleased = true;
                UnlockCursor();
            }
        }

        private void OnDisable()
        {
            ready = false;
            StopAllCoroutines();

            if (exitDoor != null)
                exitDoor.ReleaseOpening(this);

            if (playing)
            {
                RestoreCamera();
                RestoreControls();
            }

            if (screenFade != null)
                screenFade.alpha = 0f;
        }
    }
}