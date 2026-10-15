using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class MachineSlider : Interactable
    {
        [SerializeField] private float minValue = 0f;
        [SerializeField] private float maxValue = 345f;
        [SerializeField, Min(0.01f)] private float step = 15f;
        [SerializeField] private float initialValue = 0f;

        [SerializeField] private Transform movingPart;

        [SerializeField]
        private Vector3 minPosition =
            new Vector3(-0.25f, 0f, -0.09f);

        [SerializeField]
        private Vector3 maxPosition =
            new Vector3(0.25f, 0f, -0.09f);

        [SerializeField, Min(0f)]
        private float moveDuration = 0.1f;

        private Vector3 moveFrom;
        private Vector3 moveTo;
        private float elapsed;
        private bool moving;

        public float Value { get; private set; }

        public override bool CanAdjust => true;

        public override string Prompt =>
            "Hold LMB and drag | Q / R: fine adjust";

        private void Awake()
        {
            ValidateRange();

            if (movingPart == null)
            {
                Debug.LogError(
                    "MachineSlider: assign Moving Part.", this);

                enabled = false;
                return;
            }

            Value = initialValue;
            movingPart.localPosition = PositionFor(Value);
        }

        private void OnValidate()
        {
            ValidateRange();
        }

        private void ValidateRange()
        {
            maxValue = Mathf.Max(minValue + 0.01f, maxValue);
            step = Mathf.Max(0.01f, step);

            initialValue = Mathf.Clamp(
                initialValue, minValue, maxValue);
        }

        public override void Interact()
        {
            // Left mouse dragging is handled by SliderDragInput.
        }

        public override void Adjust(int direction)
        {
            if (direction == 0 || movingPart == null)
                return;

            float next = Mathf.Clamp(
                Value + (direction > 0 ? step : -step),
                minValue,
                maxValue);

            if (Mathf.Approximately(Value, next))
                return;

            Value = next;
            moveFrom = movingPart.localPosition;
            moveTo = PositionFor(Value);
            elapsed = 0f;
            moving = moveDuration > 0f;

            if (!moving)
                movingPart.localPosition = moveTo;
        }

        public bool TryGetScreenAxis(
            Camera camera,
            out Vector2 axis)
        {
            axis = Vector2.zero;

            if (!isActiveAndEnabled ||
                camera == null ||
                movingPart == null ||
                movingPart.parent == null)
            {
                return false;
            }

            Transform parent = movingPart.parent;

            Vector3 start = camera.WorldToScreenPoint(
                parent.TransformPoint(minPosition));

            Vector3 end = camera.WorldToScreenPoint(
                parent.TransformPoint(maxPosition));

            if (start.z <= camera.nearClipPlane ||
                end.z <= camera.nearClipPlane)
            {
                return false;
            }

            axis = new Vector2(
                end.x - start.x,
                end.y - start.y);

            return axis.sqrMagnitude >= 16f;
        }

        public void DragByNormalized(float amount)
        {
            if (!isActiveAndEnabled || movingPart == null)
                return;

            float current = Mathf.InverseLerp(
                minValue, maxValue, Value);

            float next = Mathf.Clamp01(current + amount);

            Value = Mathf.Lerp(minValue, maxValue, next);
            moving = false;
            movingPart.localPosition = PositionFor(Value);
        }

        private Vector3 PositionFor(float value)
        {
            float t = Mathf.InverseLerp(
                minValue, maxValue, value);

            return Vector3.Lerp(
                minPosition, maxPosition, t);
        }

        private void Update()
        {
            if (!moving || movingPart == null)
                return;

            elapsed += Time.deltaTime;

            float t = Mathf.Clamp01(
                elapsed / Mathf.Max(0.001f, moveDuration));

            movingPart.localPosition = Vector3.Lerp(
                moveFrom,
                moveTo,
                Mathf.SmoothStep(0f, 1f, t));

            if (t >= 1f)
                moving = false;
        }
    }
}