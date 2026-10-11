using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Startup
{
    // Attach to the existing Canvas, outside the PauseMenu object.
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-300)]
    public sealed class PauseSettings : MonoBehaviour
    {
        [SerializeField] private FirstPersonMotor motor;
        [SerializeField] private CanvasGroup menuGroup;
        [SerializeField] private Slider volumeSlider;
        [SerializeField] private Slider sensitivitySlider;
        [SerializeField] private Toggle headBobToggle;
        [SerializeField] private Button resumeButton;
        [SerializeField] private Button quitButton;

        private const string VolumeKey = "RELAY.Settings.Volume";
        private const string SensitivityKey = "RELAY.Settings.Sensitivity";
        private const string HeadBobKey = "RELAY.Settings.HeadBob";

        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;
        private bool configured;
        private bool resumeRequested;
        private bool savedMotorEnabled;
        private bool savedInteractorEnabled;
        private bool savedDragEnabled;
        private bool savedAudioPause;
        private float savedTimeScale;

        public bool IsOpen { get; private set; }

        private void Start()
        {
            if (motor == null || menuGroup == null ||
                volumeSlider == null || sensitivitySlider == null ||
                headBobToggle == null || resumeButton == null ||
                quitButton == null || volumeSlider == sensitivitySlider ||
                resumeButton == quitButton)
            {
                Fail("Assign all seven references to separate controls.");
                return;
            }

            if (transform.IsChildOf(menuGroup.transform) ||
                motor.transform.IsChildOf(menuGroup.transform) ||
                !volumeSlider.transform.IsChildOf(menuGroup.transform) ||
                !sensitivitySlider.transform.IsChildOf(menuGroup.transform) ||
                !headBobToggle.transform.IsChildOf(menuGroup.transform) ||
                !resumeButton.transform.IsChildOf(menuGroup.transform) ||
                !quitButton.transform.IsChildOf(menuGroup.transform))
            {
                Fail("Attach this script to Canvas; use controls inside PauseMenu.");
                return;
            }

            interactor = motor.GetComponent<PlayerInteractor>();
            sliderDrag = motor.GetComponent<SliderDragInput>();
            if (interactor == null || sliderDrag == null)
            {
                Fail("Player needs PlayerInteractor and SliderDragInput.");
                return;
            }

            volumeSlider.minValue = 0f;
            volumeSlider.maxValue = 1f;
            volumeSlider.wholeNumbers = false;
            sensitivitySlider.minValue = 0.02f;
            sensitivitySlider.maxValue = 0.25f;
            sensitivitySlider.wholeNumbers = false;

            float volume = Mathf.Clamp01(PlayerPrefs.GetFloat(VolumeKey, 1f));
            float sensitivity = Mathf.Clamp(PlayerPrefs.GetFloat(
                SensitivityKey, motor.MouseSensitivity), 0.02f, 0.25f);
            bool bob = PlayerPrefs.GetInt(
                HeadBobKey, motor.WalkBobEnabled ? 1 : 0) != 0;

            volumeSlider.SetValueWithoutNotify(volume);
            sensitivitySlider.SetValueWithoutNotify(sensitivity);
            headBobToggle.SetIsOnWithoutNotify(bob);
            SetVolume(volume);
            SetSensitivity(sensitivity);
            SetHeadBob(bob);

            volumeSlider.onValueChanged.AddListener(SetVolume);
            sensitivitySlider.onValueChanged.AddListener(SetSensitivity);
            headBobToggle.onValueChanged.AddListener(SetHeadBob);
            resumeButton.onClick.AddListener(RequestResume);
            quitButton.onClick.AddListener(Quit);

            menuGroup.alpha = 1f;
            menuGroup.interactable = true;
            menuGroup.blocksRaycasts = true;
            menuGroup.gameObject.SetActive(false);
            configured = true;
        }

        private void Fail(string message)
        {
            Debug.LogError("PauseSettings: " + message, this);
            enabled = false;
        }

        private void Update()
        {
            if (!configured || !Application.isFocused || Keyboard.current == null)
                return;

            if (!Keyboard.current.escapeKey.wasPressedThisFrame)
                return;

            if (IsOpen)
                RequestResume();
            else if (motor.isActiveAndEnabled && interactor.isActiveAndEnabled &&
                     Time.timeScale > 0f)
                Open();
        }

        private void Open()
        {
            savedTimeScale = Time.timeScale;
            savedAudioPause = AudioListener.pause;
            savedMotorEnabled = motor.enabled;
            savedInteractorEnabled = interactor.enabled;
            savedDragEnabled = sliderDrag.enabled;

            IsOpen = true;
            resumeRequested = false;
            sliderDrag.enabled = false;
            interactor.enabled = false;
            motor.enabled = false;
            Time.timeScale = 0f;
            AudioListener.pause = true;

            menuGroup.gameObject.SetActive(true);
            menuGroup.interactable = true;
            menuGroup.blocksRaycasts = true;
            ClearSelection();
            SetCursor(false);
        }

        private void RequestResume()
        {
            if (IsOpen)
                resumeRequested = true;
        }

        private void LateUpdate()
        {
            if (!configured || !IsOpen)
                return;

            // Restore only after this frame's game input has finished.
            // ESC / the Resume click cannot also operate a machine.
            if (resumeRequested)
                Close(Application.isFocused);
            else if (!menuGroup.gameObject.activeInHierarchy)
                Close(false);
            else
                SetCursor(false);
        }

        private void Close(bool captureCursor)
        {
            if (!IsOpen)
                return;

            IsOpen = false;
            resumeRequested = false;
            Time.timeScale = savedTimeScale;
            AudioListener.pause = savedAudioPause;
            if (menuGroup != null)
                menuGroup.gameObject.SetActive(false);

            ClearSelection();
            if (motor != null) motor.enabled = savedMotorEnabled;
            if (interactor != null) interactor.enabled = savedInteractorEnabled;
            if (sliderDrag != null) sliderDrag.enabled = savedDragEnabled;
            SetCursor(captureCursor && motor != null && motor.isActiveAndEnabled);
            PlayerPrefs.Save();
        }

        private void SetVolume(float value)
        {
            value = Mathf.Clamp01(value);
            AudioListener.volume = value;
            PlayerPrefs.SetFloat(VolumeKey, value);
        }

        private void SetSensitivity(float value)
        {
            motor.MouseSensitivity = value;
            PlayerPrefs.SetFloat(SensitivityKey, motor.MouseSensitivity);
        }

        private void SetHeadBob(bool value)
        {
            motor.WalkBobEnabled = value;
            PlayerPrefs.SetInt(HeadBobKey, value ? 1 : 0);
        }

        private void Quit()
        {
            if (!IsOpen) return;
            PlayerPrefs.Save();
#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        private static void SetCursor(bool captured)
        {
            Cursor.lockState = captured ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !captured;
        }

        private static void ClearSelection()
        {
            if (EventSystem.current != null)
                EventSystem.current.SetSelectedGameObject(null);
        }

        private void OnDisable()
        {
            if (!configured) return;
            Close(false);
            if (menuGroup != null) menuGroup.gameObject.SetActive(false);
            PlayerPrefs.Save();
        }

        private void OnDestroy()
        {
            if (volumeSlider != null) volumeSlider.onValueChanged.RemoveListener(SetVolume);
            if (sensitivitySlider != null) sensitivitySlider.onValueChanged.RemoveListener(SetSensitivity);
            if (headBobToggle != null) headBobToggle.onValueChanged.RemoveListener(SetHeadBob);
            if (resumeButton != null) resumeButton.onClick.RemoveListener(RequestResume);
            if (quitButton != null) quitButton.onClick.RemoveListener(Quit);
        }
    }
}
