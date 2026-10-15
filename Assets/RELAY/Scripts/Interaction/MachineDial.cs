using UnityEngine;
using UnityEngine.Events;

namespace Startup
{
    public sealed class MachineDial : Interactable
    {
        [SerializeField] private float minValue = 0f;
        [SerializeField] private float maxValue = 100f;
        [SerializeField, Min(0.01f)] private float step = 5f;
        [SerializeField] private float initialValue = 50f;
        [SerializeField] private string unit = "V";

        [SerializeField] private Transform movingPart;
        [SerializeField] private float minAngle = 135f;
        [SerializeField] private float maxAngle = -135f;

        [SerializeField]
        private UnityEvent<float> onValueChanged =
            new UnityEvent<float>();

        public float Value { get; private set; }
        public float MinValue => minValue;
        public float MaxValue => maxValue;
        public string Unit => unit;

        public override bool CanAdjust => true;

        public override string Prompt =>
            $"{DisplayName}: {Value:0.##} {unit} | Q: - | LMB / R: +";

        private void Awake()
        {
            if (movingPart == null)
            {
                Debug.LogWarning(
                    "MachineDial: assign Moving Part.", this);
            }

            ValidateRange();
            Value = initialValue;
            RefreshVisual();
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
            Adjust(1);
        }

        public override void Adjust(int direction)
        {
            if (direction == 0)
                return;

            SetValue(
                Value + (direction > 0 ? step : -step));
        }

        public void SetValue(float value)
        {
            float next = Mathf.Clamp(
                value, minValue, maxValue);

            if (Mathf.Approximately(Value, next))
                return;

            Value = next;
            RefreshVisual();
            onValueChanged.Invoke(Value);
        }

        private void RefreshVisual()
        {
            if (movingPart == null)
                return;

            float t = Mathf.InverseLerp(
                minValue, maxValue, Value);

            movingPart.localRotation = Quaternion.Euler(
                0f,
                0f,
                Mathf.Lerp(minAngle, maxAngle, t));
        }
    }
}