using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;

namespace Startup
{
    // Attach to the wall note. All paper graphics, text and colliders are assembled manually.
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-220)]
    public sealed class PowerHintInspect : Interactable
    {
        [SerializeField] private FirstPersonMotor motor;
        [SerializeField] private CanvasGroup viewGroup;
        [SerializeField] private RectTransform paperPivot;
        [SerializeField, Range(0.02f, 0.3f)] private float dragSensitivity = 0.08f;

        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;
        private Canvas overlayCanvas;
        private bool configured, open, closing, lostFocus, canDrag;
        private bool savedMotor, savedInteractor, savedDrag, savedVisible;
        private CursorLockMode savedLock;
        private Vector3 restScale;
        private Vector2 restPosition;
        private Quaternion restRotation;
        private Vector2 tilt, slide;
        private float zoom = 1f;
        private int openedFrame;

        public override bool CanInteract => configured && !open;
        public override string Prompt => "Inspect";

        private void Awake()
        {
            if (motor == null || viewGroup == null || paperPivot == null)
            { Fail("Assign Motor, View Group and Paper Pivot."); return; }
            interactor = motor.GetComponent<PlayerInteractor>();
            sliderDrag = motor.GetComponent<SliderDragInput>();
            overlayCanvas = viewGroup.GetComponentInParent<Canvas>();
            RectTransform viewRect = viewGroup.transform as RectTransform;
            if (interactor == null || sliderDrag == null || overlayCanvas == null || viewRect == null ||
                overlayCanvas.rootCanvas.renderMode != RenderMode.ScreenSpaceOverlay ||
                viewGroup.GetComponent<Canvas>() != null || paperPivot == viewRect ||
                !paperPivot.IsChildOf(viewGroup.transform) || transform.IsChildOf(viewGroup.transform) ||
                motor.transform.IsChildOf(viewGroup.transform))
            { Fail("View Group must be Canvas > PowerHintView; Paper Pivot must be its separate child, not a world canvas."); return; }
            if (viewRect.anchorMin.sqrMagnitude > 0.0001f ||
                (viewRect.anchorMax - Vector2.one).sqrMagnitude > 0.0001f ||
                viewRect.offsetMin.sqrMagnitude > 0.01f || viewRect.offsetMax.sqrMagnitude > 0.01f)
            { Fail("PowerHintView needs full-stretch anchors and all four offsets at 0."); return; }
            restScale = paperPivot.localScale;
            restPosition = paperPivot.anchoredPosition;
            restRotation = paperPivot.localRotation;
            configured = true;
            HideView();
        }

        private void Fail(string message)
        {
            Debug.LogError("PowerHintInspect: " + message, this);
            enabled = false;
        }

        public override void Interact() { TryInteract(); }
        public override bool TryInteract()
        {
            if (!CanInteract || !motor.CanInteractThisFrame || !interactor.isActiveAndEnabled || Time.timeScale <= 0f)
                return false;
            savedMotor = motor.enabled;
            savedInteractor = interactor.enabled;
            savedDrag = sliderDrag.enabled;
            savedLock = Cursor.lockState;
            savedVisible = Cursor.visible;
            open = true;
            closing = lostFocus = canDrag = false;
            openedFrame = Time.frameCount;
            tilt = slide = Vector2.zero;
            zoom = 1f;
            sliderDrag.enabled = false;
            interactor.enabled = false;
            motor.enabled = false;
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(null);
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
            paperPivot.localRotation = restRotation;
            paperPivot.anchoredPosition = restPosition;
            paperPivot.localScale = restScale * 0.94f;
            viewGroup.gameObject.SetActive(true);
            viewGroup.alpha = 0f;
            viewGroup.interactable = false;
            viewGroup.blocksRaycasts = true;
            return true;
        }

        private void Update()
        {
            if (!open || closing) return;
            if (!Application.isFocused) { lostFocus = closing = true; return; }
            Mouse mouse = Mouse.current;
            Keyboard keyboard = Keyboard.current;
            if (Time.frameCount != openedFrame &&
                ((keyboard != null && keyboard.escapeKey.wasPressedThisFrame) ||
                 (mouse != null && mouse.rightButton.wasPressedThisFrame)))
            { closing = true; return; }

            // Release the opening click before any inspection drag can begin.
            if (mouse != null && Time.frameCount != openedFrame)
            {
                if (!mouse.leftButton.isPressed) canDrag = true;
                if (canDrag && mouse.leftButton.isPressed)
                {
                    Vector2 delta = mouse.delta.ReadValue() / Mathf.Max(0.01f, overlayCanvas.rootCanvas.scaleFactor);
                    tilt.x = Mathf.Clamp(tilt.x - delta.y * dragSensitivity, -12f, 12f);
                    tilt.y = Mathf.Clamp(tilt.y + delta.x * dragSensitivity, -18f, 18f);
                    slide.x = Mathf.Clamp(slide.x + delta.x * 0.12f, -40f, 40f);
                    slide.y = Mathf.Clamp(slide.y + delta.y * 0.12f, -30f, 30f);
                }
                float wheel = Mathf.Clamp(mouse.scroll.ReadValue().y / 120f, -1f, 1f);
                zoom = Mathf.Clamp(zoom + wheel * 0.1f, 0.85f, 1.15f);
            }
            viewGroup.alpha = Mathf.MoveTowards(viewGroup.alpha, 1f, Time.unscaledDeltaTime / 0.16f);
            float blend = 1f - Mathf.Exp(-14f * Time.unscaledDeltaTime);
            paperPivot.localRotation = Quaternion.Slerp(paperPivot.localRotation,
                restRotation * Quaternion.Euler(tilt.x, tilt.y, 0f), blend);
            paperPivot.anchoredPosition = Vector2.Lerp(paperPivot.anchoredPosition, restPosition + slide, blend);
            paperPivot.localScale = Vector3.Lerp(paperPivot.localScale, restScale * zoom, blend);
        }

        private void LateUpdate()
        {
            // Restore controls only after other scripts finish Update: Esc cannot also open Pause.
            if (open && closing) CloseView();
        }

        private void HideView()
        {
            viewGroup.alpha = 0f;
            viewGroup.interactable = false;
            viewGroup.blocksRaycasts = false;
            viewGroup.gameObject.SetActive(false);
        }

        private void CloseView()
        {
            if (!open) return;
            open = closing = false;
            if (viewGroup != null) HideView();
            if (paperPivot != null)
            {
                paperPivot.localRotation = restRotation;
                paperPivot.anchoredPosition = restPosition;
                paperPivot.localScale = restScale;
            }
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(null);
            if (motor != null) motor.enabled = savedMotor;
            if (interactor != null) interactor.enabled = savedInteractor;
            if (sliderDrag != null) sliderDrag.enabled = savedDrag;
            bool release = lostFocus || !Application.isFocused;
            Cursor.lockState = release ? CursorLockMode.None : savedLock;
            Cursor.visible = release || savedVisible;
        }

        private void OnApplicationFocus(bool focused)
        {
            if (focused || !open) return;
            lostFocus = closing = true;
            if (viewGroup != null) viewGroup.alpha = 0f;
        }

        private void OnDisable()
        {
            if (open) CloseView();
            else if (configured && viewGroup != null) HideView();
        }
    }
}
