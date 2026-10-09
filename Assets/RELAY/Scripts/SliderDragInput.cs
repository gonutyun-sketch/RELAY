using UnityEngine;
using UnityEngine.InputSystem;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-200)]
    public sealed class SliderDragInput : MonoBehaviour
    {
        private FirstPersonMotor motor;
        private PlayerInteractor interactor;
        private Camera viewCamera;
        private MachineSlider dragging;

        private void Awake()
        {
            motor = GetComponent<FirstPersonMotor>();
            interactor = GetComponent<PlayerInteractor>();

            if (motor != null && motor.ViewCamera != null)
                viewCamera = motor.ViewCamera.GetComponent<Camera>();

            if (motor == null ||
                interactor == null ||
                viewCamera == null)
            {
                Debug.LogError(
                    "SliderDragInput: add this component to Player " +
                    "with FirstPersonMotor and PlayerInteractor.", this);

                enabled = false;
            }
        }

        private void Update()
        {
            Mouse mouse = Mouse.current;
            Keyboard keyboard = Keyboard.current;

            bool escapePressed =
                keyboard != null &&
                keyboard.escapeKey.wasPressedThisFrame;

            if (motor == null ||
                interactor == null ||
                viewCamera == null ||
                !motor.isActiveAndEnabled ||
                !interactor.isActiveAndEnabled ||
                !viewCamera.isActiveAndEnabled ||
                !motor.HasControl ||
                mouse == null ||
                escapePressed)
            {
                dragging = null;
                return;
            }

            if (dragging != null)
            {
                // Also suppress look/input on the release frame.
                motor.BlockForManipulation();

                float allowedDistance = interactor.Reach + 0.25f;

                bool tooFar =
                    (viewCamera.transform.position -
                     dragging.transform.position).sqrMagnitude >
                    allowedDistance * allowedDistance;

                if (!mouse.leftButton.isPressed ||
                    !dragging.isActiveAndEnabled ||
                    !dragging.CanInteract ||
                    tooFar ||
                    !dragging.TryGetScreenAxis(
                        viewCamera, out Vector2 axis))
                {
                    dragging = null;
                    return;
                }

                Vector2 delta = mouse.delta.ReadValue();

                float amount =
                    Vector2.Dot(delta, axis) / axis.sqrMagnitude;

                dragging.DragByNormalized(amount);
                return;
            }

            if (!mouse.leftButton.wasPressedThisFrame)
                return;

            if (!interactor.TryGetTarget(out Interactable target))
                return;

            if (!(target is MachineSlider slider) ||
                !slider.CanInteract ||
                !slider.TryGetScreenAxis(viewCamera, out _))
            {
                return;
            }

            dragging = slider;
            motor.BlockForManipulation();

            // Do not apply the mouse movement from before the grab.
        }

        private void OnApplicationFocus(bool focused)
        {
            if (!focused)
                dragging = null;
        }

        private void OnDisable()
        {
            dragging = null;
        }
    }
}