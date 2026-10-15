using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace Startup
{
    // PauseSettings starts at -300; the motor at -100 and prologue at -50.
    // Scene Awake calls finish before Start, so the motor's rest pose is ready.
    [DefaultExecutionOrder(-150)]
    [DisallowMultipleComponent]
    [AddComponentMenu("RELAY/Title Menu")]
    public sealed class RelayTitleMenu : MonoBehaviour
    {
        [Header("Existing Player and Prologue")]
        [SerializeField] private FirstPersonMotor motor;
        [SerializeField] private WakeUpPrologue prologue;

        [Header("User-created Title UI")]
        [SerializeField] private CanvasGroup screenGroup;
        [SerializeField] private CanvasGroup contentGroup;
        [SerializeField] private CanvasGroup blackFade;
        [SerializeField] private Button startButton;
        [SerializeField] private Button quitButton;

        [Header("Motion")]
        [SerializeField, Range(0.5f, 2f)] private float appearSeconds = 1.2f;
        [SerializeField, Range(0.3f, 1.2f)] private float startFadeSeconds = 0.65f;
        [SerializeField] private bool subtleCameraDrift = true;

        private enum Phase { Inactive, Arriving, Ready, Leaving, Playing }
        private Phase phase;
        private Transform view;
        private RectTransform contentRect;
        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;
        private Vector3 cameraPosition;
        private Quaternion cameraRotation;
        private Vector2 contentPosition;
        private bool savedMotorEnabled;
        private bool savedInteractorEnabled;
        private bool savedDragEnabled;
        private bool ownsPlayer;
        private bool configured;
        private float elapsed;
        private float menuTime;

        private void Awake()
        {
            if (prologue != null) prologue.WaitForStartButton();
            if (screenGroup != null)
            {
                screenGroup.alpha = 1f;
                screenGroup.interactable = false;
                screenGroup.blocksRaycasts = true;
            }
            if (contentGroup != null) contentGroup.alpha = 0f;
            if (blackFade != null)
            {
                blackFade.alpha = 0f;
                blackFade.interactable = false;
                blackFade.blocksRaycasts = false;
            }
        }

        private void Start()
        {
            if (motor == null || prologue == null ||
                !motor.isActiveAndEnabled || !prologue.isActiveAndEnabled ||
                prologue.Motor != motor || prologue.IsPlaying ||
                screenGroup == null || contentGroup == null || blackFade == null ||
                startButton == null || quitButton == null || startButton == quitButton)
            {
                Fail("Assign Player, the updated WakeUpPrologue, three separate UI groups and two buttons.");
                return;
            }
            view = motor.ViewCamera;
            interactor = motor.GetComponent<PlayerInteractor>();
            sliderDrag = motor.GetComponent<SliderDragInput>();
            if (view == null || interactor == null || sliderDrag == null ||
                !interactor.isActiveAndEnabled || !sliderDrag.isActiveAndEnabled)
            {
                Fail("The existing Player input components must be enabled before Play.");
                return;
            }
            Canvas canvas = screenGroup.GetComponentInParent<Canvas>();
            if (canvas == null || !canvas.isActiveAndEnabled ||
                canvas.renderMode != RenderMode.ScreenSpaceOverlay ||
                screenGroup.transform.parent != canvas.transform ||
                contentGroup == screenGroup || blackFade == screenGroup ||
                blackFade == contentGroup ||
                contentGroup.transform.parent != screenGroup.transform ||
                blackFade.transform.parent != screenGroup.transform ||
                transform.IsChildOf(screenGroup.transform) ||
                !startButton.transform.IsChildOf(contentGroup.transform) ||
                !quitButton.transform.IsChildOf(contentGroup.transform) ||
                !screenGroup.gameObject.activeInHierarchy ||
                !contentGroup.gameObject.activeInHierarchy ||
                !blackFade.gameObject.activeInHierarchy ||
                !(contentGroup.transform is RectTransform) ||
                !FullScreen(screenGroup.transform as RectTransform) ||
                !FullScreen(blackFade.transform as RectTransform) ||
                blackFade.GetComponent<Image>() == null)
            {
                Fail("Follow the TitleScreen / Content / BlackFade hierarchy; keep TitleFlow outside it. Screen and fade must fully stretch.");
                return;
            }

            contentRect = contentGroup.transform as RectTransform;
            contentPosition = contentRect.anchoredPosition;
            cameraPosition = motor.CameraRestLocalPosition;
            cameraRotation = view.localRotation;
            savedMotorEnabled = motor.enabled;
            savedInteractorEnabled = interactor.enabled;
            savedDragEnabled = sliderDrag.enabled;
            BlockPlayer();

            startButton.onClick.AddListener(StartGame);
            quitButton.onClick.AddListener(Quit);
            blackFade.GetComponent<Image>().color = Color.black;
            screenGroup.interactable = true;
            contentGroup.interactable = false;
            contentGroup.blocksRaycasts = false;
            ClearSelection();
            phase = Phase.Arriving;
            configured = true;
        }

        private static bool FullScreen(RectTransform rect)
        {
            return rect != null && rect.anchorMin.sqrMagnitude < 0.0001f &&
                (rect.anchorMax - Vector2.one).sqrMagnitude < 0.0001f &&
                rect.offsetMin.sqrMagnitude < 0.01f && rect.offsetMax.sqrMagnitude < 0.01f &&
                (rect.localScale - Vector3.one).sqrMagnitude < 0.0001f &&
                Quaternion.Angle(rect.localRotation, Quaternion.identity) < 0.01f;
        }

        private void Update()
        {
            if (!configured || phase == Phase.Playing || phase == Phase.Inactive) return;
            ReleaseCursor();
            if (!Application.isFocused) return;

            float dt = Mathf.Min(Time.unscaledDeltaTime, 0.1f);
            elapsed += dt;
            menuTime += dt;
            if (phase == Phase.Arriving)
            {
                float t = Mathf.Clamp01(elapsed / Mathf.Max(0.1f, appearSeconds));
                float eased = 1f - Mathf.Pow(1f - t, 3f);
                contentGroup.alpha = eased;
                contentRect.anchoredPosition = contentPosition + Vector2.right * (12f * (1f - eased));
                if (t >= 1f)
                {
                    phase = Phase.Ready;
                    contentGroup.interactable = true;
                    contentGroup.blocksRaycasts = true;
                    if (EventSystem.current != null)
                        EventSystem.current.SetSelectedGameObject(startButton.gameObject);
                }
            }
            else if (phase == Phase.Leaving)
            {
                float t = Mathf.SmoothStep(0f, 1f,
                    Mathf.Clamp01(elapsed / Mathf.Max(0.1f, startFadeSeconds)));
                blackFade.alpha = t;
                contentGroup.alpha = 1f - t;
            }
        }

        private void LateUpdate()
        {
            if (!configured || !ownsPlayer) return;
            if (phase == Phase.Leaving && elapsed >= Mathf.Max(0.1f, startFadeSeconds))
            {
                BeginPrologue();
                return;
            }
            if (subtleCameraDrift && view != null)
            {
                // Rotation only: the camera remains inside the player collider.
                float yaw = Mathf.Sin(menuTime * 0.13f) * 0.65f;
                float pitch = Mathf.Sin(menuTime * 0.17f) * 0.18f;
                view.localRotation = cameraRotation * Quaternion.Euler(pitch, yaw, 0f);
            }
        }

        private bool CanUseButtons => configured && phase == Phase.Ready &&
            Application.isFocused && Cursor.lockState == CursorLockMode.None;

        private void StartGame()
        {
            if (!CanUseButtons) return;
            // Lock immediately, including repeated clicks in the same frame.
            phase = Phase.Leaving;
            elapsed = 0f;
            contentGroup.interactable = false;
            contentGroup.blocksRaycasts = false;
            blackFade.blocksRaycasts = true;
            ClearSelection();
        }

        private void BeginPrologue()
        {
            // Everything happens after all Update input. The input components
            // cannot process the menu click between restoration and TryBegin.
            RestoreCamera();
            RestorePlayer();
            if (!prologue.TryBegin())
            {
                BlockPlayer();
                blackFade.alpha = 0f;
                blackFade.blocksRaycasts = false;
                contentGroup.alpha = 1f;
                contentGroup.interactable = true;
                contentGroup.blocksRaycasts = true;
                phase = Phase.Ready;
                Debug.LogError("RelayTitleMenu: prologue could not start. Check its Console message and Eyelids reference.", this);
                return;
            }

            // Prologue has already closed the eyelids before this screen hides.
            phase = Phase.Playing;
            screenGroup.alpha = 0f;
            screenGroup.interactable = false;
            screenGroup.blocksRaycasts = false;
            blackFade.blocksRaycasts = false;
            screenGroup.gameObject.SetActive(false);
        }

        private void BlockPlayer()
        {
            sliderDrag.enabled = false;
            interactor.enabled = false;
            motor.enabled = false;
            ownsPlayer = true;
            ReleaseCursor();
        }

        private void RestorePlayer()
        {
            if (!ownsPlayer) return;
            ownsPlayer = false;
            if (motor != null) motor.enabled = savedMotorEnabled;
            if (interactor != null) interactor.enabled = savedInteractorEnabled;
            if (sliderDrag != null) sliderDrag.enabled = savedDragEnabled;
        }

        private void RestoreCamera()
        {
            if (view == null) return;
            view.localPosition = cameraPosition;
            view.localRotation = cameraRotation;
        }

        private void Quit()
        {
            if (!CanUseButtons) return;
            contentGroup.interactable = false;
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        private static void ClearSelection()
        {
            if (EventSystem.current != null)
                EventSystem.current.SetSelectedGameObject(null);
        }

        private static void ReleaseCursor()
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
        }

        private void Fail(string message)
        {
            Debug.LogError("RelayTitleMenu: " + message, this);
            if (screenGroup != null)
            {
                screenGroup.alpha = 0f;
                screenGroup.blocksRaycasts = false;
                screenGroup.interactable = false;
            }
            enabled = false;
        }

        private void OnDisable()
        {
            if (!configured) return;
            if (ownsPlayer)
            {
                RestoreCamera();
                RestorePlayer();
                ReleaseCursor();
            }
            if (screenGroup != null)
            {
                screenGroup.alpha = 0f;
                screenGroup.interactable = false;
                screenGroup.blocksRaycasts = false;
            }
        }

        private void OnDestroy()
        {
            if (startButton != null) startButton.onClick.RemoveListener(StartGame);
            if (quitButton != null) quitButton.onClick.RemoveListener(Quit);
        }
    }
}
