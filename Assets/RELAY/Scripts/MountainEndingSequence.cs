using System.Collections;
using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(600)]
    public sealed class MountainEndingSequence : MonoBehaviour
    {
        [SerializeField] private ElevatorModule elevator;
        [SerializeField] private FirstPersonMotor motor;
        [SerializeField] private BoxCollider endingArea;
        [SerializeField] private Transform vistaTarget;

        // Retained for the existing Inspector reference.
        // The exit-door sequence owns this overlay.
        [SerializeField] private CanvasGroup screenFade;

        [SerializeField] private CanvasGroup endingTitle;

        [SerializeField, Min(0.1f)]
        private float lookSeconds = 2f;

        [SerializeField, Min(0.1f)]
        private float fadeSeconds = 2f;

        [SerializeField, Min(0f)]
        private float titleHoldSeconds = 3f;

        private CharacterController player;
        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;

        private bool configured;
        private bool started;
        private float lookElapsed;

        private bool interactorWasEnabled;
        private bool dragWasEnabled;

        public bool IsComplete { get; private set; }

        private void Awake()
        {
            if (elevator == null || motor == null ||
                endingArea == null || vistaTarget == null ||
                screenFade == null || endingTitle == null)
            {
                Fail("Assign all six references.");
                return;
            }

            player = motor.GetComponent<CharacterController>();
            interactor = motor.GetComponent<PlayerInteractor>();
            sliderDrag = motor.GetComponent<SliderDragInput>();

            if (player == null || interactor == null ||
                sliderDrag == null || motor.ViewCamera == null)
            {
                Fail("Player needs its existing controller, " +
                     "interaction, slider drag and camera.");
                return;
            }

            if (!endingArea.enabled || !endingArea.isTrigger)
            {
                Fail("Ending Area needs an enabled Box Collider " +
                     "with Is Trigger ON.");
                return;
            }

            if (screenFade == endingTitle ||
                endingTitle.transform.IsChildOf(screenFade.transform))
            {
                Fail("Ending Title must be separate from Screen Fade.");
                return;
            }

            if (!endingTitle.gameObject.activeInHierarchy)
            {
                Fail("Keep the Ending Title object active.");
                return;
            }

            endingTitle.alpha = 0f;
            endingTitle.interactable = false;
            endingTitle.blocksRaycasts = false;

            configured = true;
        }

        private void Fail(string message)
        {
            Debug.LogError("MountainEndingSequence: " + message, this);
            enabled = false;
        }

        private void LateUpdate()
        {
            if (!configured || started)
                return;

            bool canObserve =
                elevator.isActiveAndEnabled &&
                elevator.HasArrived &&
                player.enabled &&
                motor.isActiveAndEnabled &&
                motor.HasControl &&
                endingArea.enabled &&
                endingArea.gameObject.activeInHierarchy;

            if (!canObserve || !PlayerIsInside() || !LookingAtMountains())
            {
                lookElapsed = 0f;
                return;
            }

            lookElapsed += Time.deltaTime;

            if (lookElapsed >= lookSeconds)
                BeginEnding();
        }

        private bool PlayerIsInside()
        {
            Vector3 bodyCenter =
                player.transform.TransformPoint(player.center);

            Vector3 localPoint =
                endingArea.transform.InverseTransformPoint(bodyCenter)
                - endingArea.center;

            Vector3 halfSize = endingArea.size * 0.5f;

            return Mathf.Abs(localPoint.x) <= halfSize.x &&
                   Mathf.Abs(localPoint.y) <= halfSize.y &&
                   Mathf.Abs(localPoint.z) <= halfSize.z;
        }

        private bool LookingAtMountains()
        {
            Transform cameraTransform = motor.ViewCamera;
            Vector3 direction =
                vistaTarget.position - cameraTransform.position;

            if (direction.sqrMagnitude < 0.001f)
                return false;

            return Vector3.Dot(
                cameraTransform.forward, direction.normalized) >= 0.65f;
        }

        private void BeginEnding()
        {
            started = true;

            interactorWasEnabled = interactor.enabled;
            dragWasEnabled = sliderDrag.enabled;

            // Hide machine prompts and the aiming dot.
            // Movement, collision and mouse look stay active.
            sliderDrag.enabled = false;
            interactor.enabled = false;

            StartCoroutine(PlayEnding());
        }

        private IEnumerator PlayEnding()
        {
            yield return FadeTitle(1f);

            yield return new WaitForSecondsRealtime(
                Mathf.Max(0f, titleHoldSeconds));

            yield return FadeTitle(0f);

            // The menu becomes available only after the title disappears.
            IsComplete = true;
        }

        private IEnumerator FadeTitle(float target)
        {
            float start = endingTitle.alpha;
            float duration = Mathf.Max(0.1f, fadeSeconds);
            float elapsed = 0f;

            while (elapsed < duration)
            {
                elapsed += Time.unscaledDeltaTime;
                float t = Mathf.Clamp01(elapsed / duration);

                endingTitle.alpha = Mathf.Lerp(
                    start, target, Mathf.SmoothStep(0f, 1f, t));

                yield return null;
            }

            endingTitle.alpha = target;
        }

        private void OnDisable()
        {
            StopAllCoroutines();

            if (endingTitle != null)
                endingTitle.alpha = 0f;

            if (started)
            {
                if (interactor != null)
                    interactor.enabled = interactorWasEnabled;

                if (sliderDrag != null)
                    sliderDrag.enabled = dragWasEnabled;
            }

            started = false;
            IsComplete = false;
            lookElapsed = 0f;
        }
    }
}