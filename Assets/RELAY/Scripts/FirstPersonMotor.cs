using UnityEngine;
using UnityEngine.InputSystem;

namespace Startup
{
    [DefaultExecutionOrder(-100)]
    [RequireComponent(typeof(CharacterController))]
    public sealed class FirstPersonMotor : MonoBehaviour
    {
        [SerializeField] private Transform viewCamera;
        [SerializeField, Min(0f)] private float moveSpeed = 2.4f;
        [SerializeField, Min(0f)] private float mouseSensitivity = 0.1f;
        [SerializeField, Range(0f, 0.15f)] private float lookSmoothTime = 0.045f;
        [SerializeField] private float gravity = -20f;

        [Header("Walking Camera")]
        [SerializeField] private bool walkBobEnabled = true;
        [SerializeField, Range(0f, 0.05f)] private float walkBobHeight = 0.05f;
        [SerializeField, Range(0f, 0.02f)] private float walkBobWidth = 0.018f;
        [SerializeField, Min(0.1f)] private float walkBobStepDistance = 1.5f;

        private CharacterController controller;
        private float verticalSpeed;
        private float pitch;
        private float yaw;
        private float targetPitch;
        private float targetYaw;
        private float pitchVelocity;
        private float yawVelocity;
        private bool discardNextMouseDelta = true;
        private int controlReadyFrame = -1;
        private int manipulationFrame = -1;
        private int carriedFrame = -1;
        private Vector3 cameraRestLocalPosition;
        private Vector3 walkBobOffset;
        private float walkBobPhase;
        private bool initialized;

        public bool IsManipulating =>
            manipulationFrame == Time.frameCount;

        public void BlockForManipulation()
        {
            manipulationFrame = Time.frameCount;
        }
        public Transform ViewCamera => viewCamera;
        public Vector3 CameraRestLocalPosition => cameraRestLocalPosition;
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
            cameraRestLocalPosition = viewCamera.localPosition;
            initialized = true;
            ResetLookSmoothing();
        }

        private void OnEnable()
        {
            if (initialized)
            {
                ResetWalkBob();
                ResetLookSmoothing();
            }
        }

        private void Update()
        {
            controlReadyFrame = -1;
            Keyboard keyboard = Keyboard.current;
            Mouse mouse = Mouse.current;
            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
            {
                ResetLookSmoothing();
                ReleaseCursor();
                UpdateWalkBob(0f, false);
                return;
            }
            if (!HasControl)
            {
                ResetLookSmoothing();
                UpdateWalkBob(0f, false);
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

                UpdateLook(mouse);
            }
            else
            {
                // Freeze at the visible angle while dragging a control.
                ResetLookSmoothing();
            }

            Vector2 input = Vector2.zero;
            if (keyboard != null && !IsManipulating)
            {
                input.x = (keyboard.dKey.isPressed ? 1f : 0f) - (keyboard.aKey.isPressed ? 1f : 0f);
                input.y = (keyboard.wKey.isPressed ? 1f : 0f) - (keyboard.sKey.isPressed ? 1f : 0f);
            }
            input = Vector2.ClampMagnitude(input, 1f);
            Vector3 horizontal = transform.right * input.x + transform.forward * input.y;
            if (controller.isGrounded && verticalSpeed < 0f) verticalSpeed = -2f;
            verticalSpeed += gravity * Time.deltaTime;
            Vector3 velocity = horizontal * moveSpeed + Vector3.up * verticalSpeed;
            Vector3 beforeMove = transform.position;
            CollisionFlags flags = controller.Move(velocity * Time.deltaTime);
            if ((flags & CollisionFlags.Above) != 0 && verticalSpeed > 0f) verticalSpeed = 0f;

            // Measure only walking displacement, after collision resolution.
            // Elevator carrying has already happened before this Update.
            Vector3 moved = transform.position - beforeMove;
            moved.y = 0f;
            float distance = moved.magnitude;
            float actualSpeed = distance / Mathf.Max(Time.deltaTime, 0.0001f);
            bool walking = input.sqrMagnitude > 0.01f &&
                           (flags & CollisionFlags.Below) != 0 &&
                           actualSpeed > 0.1f;
            UpdateWalkBob(distance, walking);
        }

        private void UpdateLook(Mouse mouse)
        {
            float dt = Time.unscaledDeltaTime;
            if (dt <= 0f)
                return;

            Vector2 look = mouse != null && !discardNextMouseDelta
                ? mouse.delta.ReadValue()
                : Vector2.zero;
            discardNextMouseDelta = false;

            // Mouse delta is already a per-frame displacement: do not multiply by dt.
            targetYaw += look.x * mouseSensitivity;
            targetPitch = Mathf.Clamp(
                targetPitch - look.y * mouseSensitivity, -85f, 85f);

            if (lookSmoothTime <= 0f)
            {
                yaw = targetYaw;
                pitch = targetPitch;
                yawVelocity = 0f;
                pitchVelocity = 0f;
            }
            else
            {
                // Keep yaw continuous so a fast turn is not reversed at 180 degrees.
                yaw = Mathf.SmoothDamp(yaw, targetYaw, ref yawVelocity,
                    lookSmoothTime, Mathf.Infinity, dt);
                pitch = Mathf.SmoothDamp(pitch, targetPitch, ref pitchVelocity,
                    lookSmoothTime, Mathf.Infinity, dt);
            }

            // Rebase both angles together to preserve their difference and precision.
            float turns = Mathf.Floor((yaw + 180f) / 360f) * 360f;
            yaw -= turns;
            targetYaw -= turns;

            transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
            viewCamera.localRotation = Quaternion.Euler(pitch, 0f, 0f);
        }

        private void ResetLookSmoothing()
        {
            if (!initialized || viewCamera == null)
                return;

            yaw = Mathf.DeltaAngle(0f, transform.localEulerAngles.y);
            pitch = Mathf.Clamp(
                Mathf.DeltaAngle(0f, viewCamera.localEulerAngles.x), -85f, 85f);
            targetYaw = yaw;
            targetPitch = pitch;
            yawVelocity = 0f;
            pitchVelocity = 0f;
            discardNextMouseDelta = true;
        }

        private void UpdateWalkBob(float distance, bool walking)
        {
            // ElevatorModule owns camera vibration during an ascent.
            if (carriedFrame == Time.frameCount)
            {
                walkBobOffset = Vector3.zero;
                walkBobPhase = 0f;
                return;
            }

            if (!walkBobEnabled)
            {
                ResetWalkBob();
                return;
            }

            Vector3 target = Vector3.zero;
            if (walking && HasControl && !IsManipulating)
            {
                walkBobPhase = (walkBobPhase +
                    distance * Mathf.PI * 2f /
                    Mathf.Max(0.1f, walkBobStepDistance)) % (Mathf.PI * 4f);

                float strength = Mathf.Clamp01(distance /
                    Mathf.Max(moveSpeed * Time.deltaTime, 0.0001f));
                target = new Vector3(
                    Mathf.Sin(walkBobPhase * 0.5f) * walkBobWidth,
                    Mathf.Sin(walkBobPhase) * walkBobHeight,
                    0f) * strength;
            }

            float blend = 1f - Mathf.Exp(-12f * Time.deltaTime);
            walkBobOffset = Vector3.Lerp(walkBobOffset, target, blend);

            if (!walking && walkBobOffset.sqrMagnitude < 0.00000001f)
            {
                walkBobOffset = Vector3.zero;
                walkBobPhase = 0f;
            }

            viewCamera.localPosition = cameraRestLocalPosition + walkBobOffset;
        }

        private void ResetWalkBob()
        {
            walkBobOffset = Vector3.zero;
            walkBobPhase = 0f;
            if (initialized && viewCamera != null)
                viewCamera.localPosition = cameraRestLocalPosition;
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

            carriedFrame = Time.frameCount;

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
            if (!focused)
            {
                ResetLookSmoothing();
                ReleaseCursor();
            }
        }

        private void OnDisable()
        {
            ResetLookSmoothing();
            ResetWalkBob();
            ReleaseCursor();
        }

        private static void ReleaseCursor()
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }
    }
}
