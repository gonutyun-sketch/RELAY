using UnityEngine;
using UnityEngine.InputSystem;

namespace Startup
{
    [DefaultExecutionOrder(-100)]
    [RequireComponent(typeof(CharacterController))]
    public sealed class FirstPersonMotor : MonoBehaviour
    {
        [SerializeField] private Transform viewCamera;
        [SerializeField, Min(0f)] private float moveSpeed = 4f;
        [SerializeField, Min(0f)] private float sprintSpeed = 6f;
        [SerializeField, Min(0f)] private float mouseSensitivity = 0.1f;
        [SerializeField] private float gravity = -20f;

        private CharacterController controller;
        private float verticalSpeed;
        private float pitch;
        private int controlReadyFrame = -1;
        private int manipulationFrame = -1;

        public bool IsManipulating =>
            manipulationFrame == Time.frameCount;

        public void BlockForManipulation()
        {
            manipulationFrame = Time.frameCount;
        }
        public Transform ViewCamera => viewCamera;
        public bool HasControl => Application.isFocused && Cursor.lockState == CursorLockMode.Locked;
        // The click that captures the cursor must never also activate a control.
        public bool CanInteractThisFrame => isActiveAndEnabled && HasControl && controlReadyFrame == Time.frameCount;

        private void Awake()
        {
            controller = GetComponent<CharacterController>();
            if (viewCamera == null)
            {
                Debug.LogError("FirstPersonMotor: assign View Camera in the Inspector.", this);
                enabled = false;
                return;
            }
            if (viewCamera.parent != transform)
            {
                Debug.LogError("FirstPersonMotor: Main Camera must be a direct child of Player. Stop Play, reparent it, then set LOCAL Position to (0, 1.6, 0).", this);
                enabled = false;
                return;
            }
            if ((transform.lossyScale - Vector3.one).sqrMagnitude > 0.0001f)
            {
                Debug.LogError("FirstPersonMotor: Player and its parents must have Scale (1, 1, 1). Stop Play and correct their scale before testing.", this);
                enabled = false;
                return;
            }
            Vector3 eyePosition = viewCamera.localPosition;
            if (Mathf.Abs(eyePosition.x) > 0.01f || Mathf.Abs(eyePosition.z) > 0.01f)
            {
                Debug.LogError("FirstPersonMotor: camera is offset from the player. Stop Play and set Main Camera LOCAL Position to (0, 1.6, 0), then save the scene.", this);
                enabled = false;
                return;
            }
            pitch = Mathf.DeltaAngle(0f, viewCamera.localEulerAngles.x);
        }

        private void Update()
        {
            controlReadyFrame = -1;
            Keyboard keyboard = Keyboard.current;
            Mouse mouse = Mouse.current;
            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
            {
                ReleaseCursor();
                return;
            }
            if (!HasControl)
            {
                if (Application.isFocused &&
                    mouse != null &&
                    mouse.leftButton.wasPressedThisFrame)
                {
                    // UI buttons receive their own clicks.
                    if (PointerIsOverButton(mouse.position.ReadValue()))
                        return;

                    Cursor.lockState = CursorLockMode.Locked;
                    Cursor.visible = false;

                    if (UnityEngine.EventSystems.EventSystem.current != null)
                    {
                        UnityEngine.EventSystems.EventSystem.current
                            .SetSelectedGameObject(null);
                    }
                }

                // Capturing the cursor never also performs an interaction.
                return;
            }

            if (!IsManipulating)
            {
                controlReadyFrame = Time.frameCount;

                Vector2 look = mouse != null
                    ? mouse.delta.ReadValue()
                    : Vector2.zero;

                transform.Rotate(0f, look.x * mouseSensitivity, 0f);

                pitch = Mathf.Clamp(
                    pitch - look.y * mouseSensitivity,
                    -85f,
                    85f);

                viewCamera.localRotation = Quaternion.Euler(pitch, 0f, 0f);
            }

            Vector2 input = Vector2.zero;
            bool sprint = false;
            if (keyboard != null && !IsManipulating)
            {
                input.x = (keyboard.dKey.isPressed ? 1f : 0f) - (keyboard.aKey.isPressed ? 1f : 0f);
                input.y = (keyboard.wKey.isPressed ? 1f : 0f) - (keyboard.sKey.isPressed ? 1f : 0f);
                sprint = keyboard.leftShiftKey.isPressed;
            }
            input = Vector2.ClampMagnitude(input, 1f);
            Vector3 horizontal = transform.right * input.x + transform.forward * input.y;
            if (controller.isGrounded && verticalSpeed < 0f) verticalSpeed = -2f;
            verticalSpeed += gravity * Time.deltaTime;
            Vector3 velocity = horizontal * (sprint ? sprintSpeed : moveSpeed) + Vector3.up * verticalSpeed;
            CollisionFlags flags = controller.Move(velocity * Time.deltaTime);
            if ((flags & CollisionFlags.Above) != 0 && verticalSpeed > 0f) verticalSpeed = 0f;
        }

        private bool PointerIsOverButton(Vector2 screenPosition)
        {
            var eventSystem =
                UnityEngine.EventSystems.EventSystem.current;

            if (eventSystem == null)
                return false;

            var pointer =
                new UnityEngine.EventSystems.PointerEventData(eventSystem)
                {
                    position = screenPosition
                };

            var results =
                new System.Collections.Generic.List<
                    UnityEngine.EventSystems.RaycastResult>();

            eventSystem.RaycastAll(pointer, results);

            foreach (var result in results)
            {
                var button =
                    result.gameObject.GetComponentInParent<
                        UnityEngine.UI.Button>();

                if (button != null &&
                    button.IsActive() &&
                    button.IsInteractable())
                {
                    return true;
                }
            }

            return false;
        }

        public void CarryBy(Vector3 displacement)
        {
            if (controller == null || !controller.enabled)
                return;

            // Preserve the player's walking position while carrying them.
            controller.enabled = false;
            transform.position += displacement;

            Physics.SyncTransforms();

            controller.enabled = true;

            // Avoid accumulating falling speed while riding.
            verticalSpeed = -2f;
        }

        private void OnApplicationFocus(bool focused)
        {
            if (!focused) ReleaseCursor();
        }

        private void OnDisable() => ReleaseCursor();

        private static void ReleaseCursor()
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
    }
}
