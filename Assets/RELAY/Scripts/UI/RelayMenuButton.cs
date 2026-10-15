using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Startup
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Button))]
    [AddComponentMenu("RELAY/Menu Button")]
    public sealed class RelayMenuButton : MonoBehaviour,
        IPointerEnterHandler, IPointerExitHandler,
        IPointerDownHandler, IPointerUpHandler, ISelectHandler, IDeselectHandler
    {
        [SerializeField] private TMP_Text label;
        [SerializeField] private Image underline;
        [SerializeField] private bool primary = true;
        [SerializeField] private float focusWidth = 320f;

        private Button button;
        private Vector2 labelPosition;
        private bool hovered;
        private bool selected;
        private bool pressed;
        private bool ready;
        private float focus;
        private float press;

        private static readonly Color MainInk = new Color(0.90f, 0.89f, 0.86f, 1f);
        private static readonly Color QuietInk = new Color(0.50f, 0.53f, 0.53f, 1f);
        private static readonly Color WarmInk = new Color(0.78f, 0.69f, 0.51f, 1f);

        private void Awake()
        {
            button = GetComponent<Button>();
            if (label == null || underline == null ||
                !label.transform.IsChildOf(transform) ||
                !underline.transform.IsChildOf(transform))
            {
                Debug.LogError("RelayMenuButton: assign this button's Label and Underline children.", this);
                enabled = false;
                return;
            }
            button.transition = Selectable.Transition.None;
            labelPosition = label.rectTransform.anchoredPosition;
            label.raycastTarget = false;
            underline.raycastTarget = false;
            ready = true;
            Draw();
        }

        private void Update()
        {
            if (!ready) return;
            bool usable = button.IsInteractable();
            float target = usable && (hovered || selected) ? 1f : 0f;
            float speed = Time.unscaledDeltaTime / 0.16f;
            focus = Mathf.MoveTowards(focus, target, speed);
            press = Mathf.MoveTowards(press, usable && pressed ? 1f : 0f,
                Time.unscaledDeltaTime / 0.07f);
            Draw();
        }

        private void Draw()
        {
            float eased = 1f - Mathf.Pow(1f - focus, 3f);
            Color idle = primary ? MainInk : QuietInk;
            label.color = Color.Lerp(idle, WarmInk, eased);
            label.rectTransform.anchoredPosition = labelPosition + Vector2.right * (8f * eased + 2f * press);
            float width = Mathf.Lerp(primary ? 28f : 0f, Mathf.Max(32f, focusWidth), eased);
            underline.rectTransform.SetSizeWithCurrentAnchors(RectTransform.Axis.Horizontal, width);
            Color line = WarmInk;
            line.a = Mathf.Lerp(primary ? 0.45f : 0f, 0.85f, eased);
            underline.color = line;
        }

        public void OnPointerEnter(PointerEventData data)
        {
            hovered = true;
            if (button != null && button.IsInteractable() && EventSystem.current != null)
                EventSystem.current.SetSelectedGameObject(gameObject);
        }
        public void OnPointerExit(PointerEventData data) { hovered = false; pressed = false; }
        public void OnPointerDown(PointerEventData data)
        {
            if (data.button == PointerEventData.InputButton.Left) pressed = true;
        }
        public void OnPointerUp(PointerEventData data) { pressed = false; }
        public void OnSelect(BaseEventData data) { selected = true; }
        public void OnDeselect(BaseEventData data) { selected = false; }
        private void OnDisable()
        {
            hovered = selected = pressed = false;
            focus = press = 0f;
            if (ready) Draw();
        }
    }
}
