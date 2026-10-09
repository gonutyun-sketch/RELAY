using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class ElevatorButton : Interactable
    {
        [SerializeField] private ElevatorModule elevator;
        [SerializeField] private Transform movingPart;

        private const float PressDuration = 0.18f;
        private const float PressDepth = 0.015f;

        private Vector3 restPosition;
        private float pressRemaining;
        private bool initialized;

        public override bool CanInteract =>
            isActiveAndEnabled &&
            elevator != null &&
            elevator.CanRequestDeparture;

        public override string Prompt =>
            elevator != null && elevator.HasArrived
                ? "Surface level"
                : elevator != null && elevator.ReadyForAscent
                    ? "Departure ready"
                    : "Press to ascend";

        private void Awake()
        {
            if (elevator == null || movingPart == null)
            {
                Debug.LogError(
                    "ElevatorButton: assign Elevator and Moving Part.",
                    this);

                enabled = false;
                return;
            }

            restPosition = movingPart.localPosition;
            initialized = true;
        }

        public override void Interact()
        {
            if (!CanInteract || !elevator.TryRequestDeparture())
                return;

            pressRemaining = PressDuration;
        }

        private void Update()
        {
            if (!initialized || pressRemaining <= 0f)
                return;

            pressRemaining = Mathf.Max(
                0f, pressRemaining - Time.deltaTime);

            float progress = 1f - pressRemaining / PressDuration;
            float depth = Mathf.Sin(progress * Mathf.PI) * PressDepth;

            movingPart.localPosition =
                restPosition + Vector3.forward * depth;

            if (pressRemaining <= 0f)
                movingPart.localPosition = restPosition;
        }

        private void OnDisable()
        {
            pressRemaining = 0f;

            if (initialized && movingPart != null)
                movingPart.localPosition = restPosition;
        }
    }
}