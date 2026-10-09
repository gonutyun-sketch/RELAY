using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class ExitDoor : MonoBehaviour
    {
        [SerializeField] private CoreModule coreSource;
        [SerializeField] private Rigidbody movingDoor;

        [SerializeField, Min(0.1f)]
        private float liftDistance = 3.1f;

        [SerializeField, Min(0.1f)]
        private float openSeconds = 3f;

        private Vector3 closedPosition;
        private Vector3 openPosition;

        private float elapsed;
        private bool unlocked;
        private bool configured;
        private MonoBehaviour holdOwner;

        public bool IsOpen { get; private set; }
        public CoreModule Source => coreSource;
        public float OpenDuration => Mathf.Max(0.1f, openSeconds);

        private void Awake()
        {
            if (coreSource == null || movingDoor == null)
            {
                Debug.LogError(
                    "ExitDoor: assign Core Source and Moving Door.",
                    this);

                enabled = false;
                return;
            }

            if (!movingDoor.isKinematic || movingDoor.useGravity)
            {
                Debug.LogError(
                    "ExitDoor: Moving Door needs Is Kinematic ON " +
                    "and Use Gravity OFF.", this);

                enabled = false;
                return;
            }

            BoxCollider doorCollider =
                movingDoor.GetComponentInChildren<BoxCollider>();

            if (doorCollider == null ||
                !doorCollider.enabled ||
                doorCollider.isTrigger ||
                doorCollider.attachedRigidbody != movingDoor)
            {
                Debug.LogError(
                    "ExitDoor: DoorPanel needs an enabled, " +
                    "non-trigger Box Collider under Moving Door.",
                    this);

                enabled = false;
                return;
            }

            closedPosition = movingDoor.position;
            openPosition = closedPosition +
                Vector3.up * Mathf.Max(0.1f, liftDistance);

            elapsed = 0f;
            unlocked = false;
            IsOpen = false;
            configured = true;
        }

        public bool TryHoldOpening(MonoBehaviour owner)
        {
            if (!configured ||
                !isActiveAndEnabled ||
                owner == null ||
                unlocked ||
                IsOpen ||
                (holdOwner != null && holdOwner != owner))
            {
                return false;
            }

            holdOwner = owner;
            return true;
        }

        public void ReleaseOpening(MonoBehaviour owner)
        {
            if (holdOwner == owner)
                holdOwner = null;
        }

        private void FixedUpdate()
        {
            if (!configured || movingDoor == null || IsOpen)
                return;

            if (!unlocked)
            {
                if (coreSource == null || !coreSource.IsComplete)
                    return;

                if (holdOwner != null && holdOwner.isActiveAndEnabled)
                    return;

                unlocked = true;
            }

            elapsed = Mathf.Min(
                OpenDuration,
                elapsed + Time.fixedDeltaTime);

            float progress = elapsed / OpenDuration;
            float eased = Mathf.SmoothStep(0f, 1f, progress);

            movingDoor.MovePosition(
                Vector3.Lerp(closedPosition, openPosition, eased));

            if (elapsed >= OpenDuration)
                IsOpen = true;
        }
    }
}