using TMPro;
using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-150)]
    public sealed class ElevatorModule : MonoBehaviour
    {
        [SerializeField] private ExitDoor exitDoor;
        [SerializeField] private CharacterController player;
        [SerializeField] private BoxCollider boardingArea;
        [SerializeField] private Rigidbody leftDoor;
        [SerializeField] private Rigidbody rightDoor;
        [SerializeField] private TMP_Text statusText;

        [SerializeField, Min(0.1f)]
        private float doorTravel = 1.25f;

        [SerializeField, Min(0.1f)]
        private float doorMoveSeconds = 1.5f;

        [SerializeField] private Transform arrivalPoint;
        [SerializeField] private Light surfaceLight;

        [SerializeField, Min(1f)]
        private float rideSeconds = 8f;

        private enum Phase
        {
            Boarding,
            Closing,
            Rising,
            Opening,
            Arrived
        }

        private Phase phase;
        private bool configured;
        private bool rideActive;

        private float closeAmount;
        private float rideElapsed;

        private Vector3 leftOpen;
        private Vector3 rightOpen;
        private Vector3 leftClosed;
        private Vector3 rightClosed;

        private RigidbodyInterpolation leftInterpolation;
        private RigidbodyInterpolation rightInterpolation;

        private FirstPersonMotor motor;
        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;
        private Transform viewCamera;

        private bool interactorWasEnabled;
        private bool dragWasEnabled;

        private Vector3 rideStart;
        private Vector3 rideEnd;
        private Vector3 passengerStart;
        private Vector3 cameraRestPosition;

        public bool HasArrived =>
            configured &&
            (phase == Phase.Opening || phase == Phase.Arrived);

        public bool PlayerFullyInside
        {
            get
            {
                if (player == null || !player.enabled ||
                    !player.gameObject.activeInHierarchy ||
                    boardingArea == null || !boardingArea.enabled ||
                    !boardingArea.gameObject.activeInHierarchy)
                {
                    return false;
                }

                Bounds cabin = boardingArea.bounds;
                Bounds body = player.bounds;

                return cabin.Contains(body.min) &&
                       cabin.Contains(body.max);
            }
        }

        public bool CanRequestDeparture =>
            configured &&
            isActiveAndEnabled &&
            exitDoor != null &&
            exitDoor.isActiveAndEnabled &&
            exitDoor.IsOpen &&
            phase == Phase.Boarding &&
            closeAmount <= 0f &&
            PlayerFullyInside;

        public bool ReadyForAscent =>
            configured &&
            isActiveAndEnabled &&
            phase == Phase.Closing &&
            closeAmount >= 1f &&
            PlayerFullyInside;

        private void Awake()
        {
            if (exitDoor == null || player == null ||
                boardingArea == null || leftDoor == null ||
                rightDoor == null || arrivalPoint == null)
            {
                Fail("Assign Exit Door, Player, Boarding Area, " +
                     "both doors and Arrival Point.");
                return;
            }

            motor = player.GetComponent<FirstPersonMotor>();
            interactor = player.GetComponent<PlayerInteractor>();
            sliderDrag = player.GetComponent<SliderDragInput>();
            viewCamera = motor != null ? motor.ViewCamera : null;

            if (motor == null || interactor == null ||
                sliderDrag == null || viewCamera == null)
            {
                Fail("Player needs its existing movement, " +
                     "interaction, slider drag and camera references.");
                return;
            }

            if (!boardingArea.enabled || !boardingArea.isTrigger ||
                !boardingArea.transform.IsChildOf(transform))
            {
                Fail("Boarding Area must be an enabled trigger " +
                     "inside ELEVATOR_Module.");
                return;
            }

            if (arrivalPoint.IsChildOf(transform) ||
                player.transform.IsChildOf(transform))
            {
                Fail("Arrival Point and Player must be outside " +
                     "the elevator hierarchy.");
                return;
            }

            if (leftDoor == rightDoor ||
                !ValidateDoor(leftDoor) || !ValidateDoor(rightDoor))
            {
                Fail("Use two separate, direct-child kinematic doors " +
                     "with solid colliders and Use Gravity OFF.");
                return;
            }

            leftOpen = leftDoor.transform.localPosition;
            rightOpen = rightDoor.transform.localPosition;

            leftClosed = leftOpen + Vector3.right * doorTravel;
            rightClosed = rightOpen + Vector3.left * doorTravel;

            leftInterpolation = leftDoor.interpolation;
            rightInterpolation = rightDoor.interpolation;

            if (surfaceLight != null)
                surfaceLight.enabled = false;

            phase = Phase.Boarding;
            configured = true;
        }

        private bool ValidateDoor(Rigidbody door)
        {
            Collider panel = door.GetComponentInChildren<Collider>();

            return door.transform.parent == transform &&
                   door.isKinematic &&
                   !door.useGravity &&
                   panel != null &&
                   panel.enabled &&
                   !panel.isTrigger &&
                   panel.attachedRigidbody == door;
        }

        private void Fail(string message)
        {
            Debug.LogError("ElevatorModule: " + message, this);
            enabled = false;
        }

        public bool TryRequestDeparture()
        {
            if (!CanRequestDeparture)
                return false;

            phase = Phase.Closing;
            return true;
        }

        private void FixedUpdate()
        {
            if (!configured || phase == Phase.Rising)
                return;

            // Leaving before departure cancels the request.
            if (phase == Phase.Closing && !PlayerFullyInside)
                phase = Phase.Boarding;

            float target = phase == Phase.Closing ? 1f : 0f;

            closeAmount = Mathf.MoveTowards(
                closeAmount,
                target,
                Time.fixedDeltaTime / Mathf.Max(0.1f, doorMoveSeconds));

            float eased = Mathf.SmoothStep(0f, 1f, closeAmount);

            leftDoor.MovePosition(transform.TransformPoint(
                Vector3.Lerp(leftOpen, leftClosed, eased)));

            rightDoor.MovePosition(transform.TransformPoint(
                Vector3.Lerp(rightOpen, rightClosed, eased)));
        }

        private void Update()
        {
            if (!configured)
                return;

            if (ReadyForAscent &&
                motor.isActiveAndEnabled &&
                motor.HasControl)
            {
                BeginRide();
            }

            if (phase != Phase.Rising)
                return;

            rideElapsed += Time.deltaTime;

            float t = Mathf.Clamp01(
                rideElapsed / Mathf.Max(1f, rideSeconds));

            float eased = Mathf.SmoothStep(0f, 1f, t);

            Vector3 previousPosition = transform.position;
            Vector3 nextPosition =
                Vector3.Lerp(rideStart, rideEnd, eased);

            transform.position = nextPosition;

            SetDoorsImmediately(leftClosed, rightClosed);

            // Carry first; normal walking runs afterward at order -100.
            motor.CarryBy(nextPosition - previousPosition);

            float envelope = Mathf.Sin(t * Mathf.PI);

            viewCamera.localPosition = cameraRestPosition +
                Vector3.up *
                (Mathf.Sin(rideElapsed * 23f) * 0.004f * envelope);

            if (t >= 1f)
            {
                viewCamera.localPosition = cameraRestPosition;
                RestoreDoorInterpolation();

                if (surfaceLight != null)
                    surfaceLight.enabled = true;

                phase = Phase.Opening;
            }
        }

        private void BeginRide()
        {
            rideStart = transform.position;
            rideEnd = arrivalPoint.position;
            passengerStart = player.transform.position;
            cameraRestPosition = viewCamera.localPosition;

            interactorWasEnabled = interactor.enabled;
            dragWasEnabled = sliderDrag.enabled;

            // Walking and mouse look remain enabled.
            // Disable machine interaction during the journey.
            sliderDrag.enabled = false;
            interactor.enabled = false;

            leftDoor.interpolation = RigidbodyInterpolation.None;
            rightDoor.interpolation = RigidbodyInterpolation.None;

            rideElapsed = 0f;
            rideActive = true;
            phase = Phase.Rising;
        }

        private void LateUpdate()
        {
            if (!configured)
                return;

            if (phase == Phase.Opening && closeAmount <= 0f)
            {
                phase = Phase.Arrived;
                RestoreInteractions();
            }

            if (statusText != null)
                statusText.text = phase.ToString().ToUpperInvariant();
        }

        private void SetDoorsImmediately(Vector3 left, Vector3 right)
        {
            if (leftDoor != null)
                leftDoor.position = transform.TransformPoint(left);

            if (rightDoor != null)
                rightDoor.position = transform.TransformPoint(right);
        }

        private void RestoreDoorInterpolation()
        {
            if (leftDoor != null)
                leftDoor.interpolation = leftInterpolation;

            if (rightDoor != null)
                rightDoor.interpolation = rightInterpolation;
        }

        private void RestoreInteractions()
        {
            if (!rideActive)
                return;

            if (interactor != null)
                interactor.enabled = interactorWasEnabled;

            if (sliderDrag != null)
                sliderDrag.enabled = dragWasEnabled;

            rideActive = false;
        }

        private void OnDisable()
        {
            if (!configured)
                return;

            bool returnToBoarding = rideActive;

            if (returnToBoarding)
            {
                transform.position = rideStart;

                if (viewCamera != null)
                    viewCamera.localPosition = cameraRestPosition;

                if (surfaceLight != null)
                    surfaceLight.enabled = false;

                phase = Phase.Boarding;
            }

            closeAmount = 0f;
            SetDoorsImmediately(leftOpen, rightOpen);
            RestoreDoorInterpolation();

            if (returnToBoarding && motor != null && player != null)
            {
                motor.CarryBy(
                    passengerStart - player.transform.position);
            }

            RestoreInteractions();

            if (phase != Phase.Arrived)
                phase = Phase.Boarding;
        }
    }
}