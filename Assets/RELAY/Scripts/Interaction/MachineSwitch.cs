using UnityEngine;
using UnityEngine.Events;

namespace Startup
{
    public class MachineSwitch : Interactable
    {
        [SerializeField] private bool startsOn;
        [SerializeField] private Transform movingPart;
        [SerializeField] private Vector3 offEuler = new Vector3(0f, 0f, -25f);
        [SerializeField] private Vector3 onEuler = new Vector3(0f, 0f, 25f);
        [SerializeField] private UnityEvent<bool> onValueChanged = new UnityEvent<bool>();
        [SerializeField, Min(0f)] private float turnDuration = 0.12f;

        private Quaternion rotationFrom;
        private Quaternion rotationTo;
        private float rotationElapsed;
        private bool animating;
        private bool initialized;

        public bool IsOn { get; private set; }
        public override string Prompt => $"{DisplayName}: {(IsOn ? "ON" : "OFF")} | LMB: toggle";

        protected virtual void Awake()
        {
            if (movingPart == null)
                Debug.LogWarning("MachineSwitch/Lever: assign Moving Part to HandlePivot to see the handle move.", this);
            IsOn = startsOn;
            initialized = true;
            RefreshVisual();
        }

        public override void Interact() => SetState(!IsOn);

        public void SetState(bool state)
        {
            if (IsOn == state) return;
            IsOn = state;
            if (movingPart != null)
            {
                // Start from the visible pose so rapid clicks do not jump backwards.
                rotationFrom = movingPart.localRotation;
                rotationTo = Quaternion.Euler(IsOn ? onEuler : offEuler);
                rotationElapsed = 0f;
                animating = turnDuration > 0f && isActiveAndEnabled;
                if (!animating) RefreshVisual();
            }
            onValueChanged.Invoke(IsOn);
        }

        protected virtual void Update()
        {
            if (!animating) return;
            if (movingPart == null)
            {
                animating = false;
                return;
            }
            rotationElapsed += Time.deltaTime;
            float t = turnDuration <= 0f ? 1f : Mathf.Clamp01(rotationElapsed / turnDuration);
            movingPart.localRotation = Quaternion.Slerp(rotationFrom, rotationTo, Mathf.SmoothStep(0f, 1f, t));
            if (t >= 1f)
            {
                movingPart.localRotation = rotationTo;
                animating = false;
            }
        }

        protected virtual void OnDisable()
        {
            animating = false;
            if (initialized) RefreshVisual();
        }

        private void RefreshVisual()
        {
            if (movingPart != null)
                movingPart.localRotation = Quaternion.Euler(IsOn ? onEuler : offEuler);
        }
    }
}
