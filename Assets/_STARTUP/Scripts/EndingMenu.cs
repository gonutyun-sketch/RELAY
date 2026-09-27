using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class EndingMenu : MonoBehaviour
    {
        [SerializeField] private MountainEndingSequence ending;
        [SerializeField] private CanvasGroup menuGroup;
        [SerializeField] private Button restartButton;
        [SerializeField] private Button quitButton;

        private bool configured;
        private bool loading;

        private void Awake()
        {
            if (ending == null || menuGroup == null ||
                restartButton == null || quitButton == null ||
                restartButton == quitButton)
            {
                Debug.LogError(
                    "EndingMenu: assign Ending, Menu Group " +
                    "and two separate buttons.", this);

                enabled = false;
                return;
            }

            menuGroup.alpha = 0f;
            menuGroup.interactable = false;
            menuGroup.blocksRaycasts = false;

            restartButton.onClick.AddListener(Restart);
            quitButton.onClick.AddListener(Quit);

            configured = true;
        }

        private void Update()
        {
            if (!configured)
                return;

            bool visible =
                ending != null &&
                ending.isActiveAndEnabled &&
                ending.IsComplete;

            menuGroup.alpha = Mathf.MoveTowards(
                menuGroup.alpha,
                visible ? 1f : 0f,
                Time.unscaledDeltaTime / 0.3f);

            bool cursorAvailable =
                Application.isFocused &&
                Cursor.lockState == CursorLockMode.None;

            bool usable =
                visible &&
                !loading &&
                menuGroup.alpha >= 1f &&
                cursorAvailable;

            menuGroup.interactable = usable;
            menuGroup.blocksRaycasts = usable;
        }

        private bool CanUseMenu =>
            configured &&
            isActiveAndEnabled &&
            !loading &&
            ending != null &&
            ending.isActiveAndEnabled &&
            ending.IsComplete &&
            Application.isFocused &&
            Cursor.lockState == CursorLockMode.None &&
            menuGroup.interactable;

        private void Restart()
        {
            if (!CanUseMenu)
                return;

            // Reload the scene that owns this menu.
            string scenePath = gameObject.scene.path;

            if (string.IsNullOrEmpty(scenePath) ||
                !Application.CanStreamedLevelBeLoaded(scenePath))
            {
                Debug.LogError(
                    "EndingMenu: add Startup_Graybox to the active " +
                    "Build Profiles Scene List and enable its checkbox.",
                    this);
                return;
            }

            loading = true;
            menuGroup.interactable = false;
            menuGroup.blocksRaycasts = false;

            Time.timeScale = 1f;
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;

            try
            {
                AsyncOperation operation = SceneManager.LoadSceneAsync(
                    scenePath, LoadSceneMode.Single);

                if (operation == null)
                {
                    loading = false;
                    Debug.LogError(
                        "EndingMenu: scene reload could not start.", this);
                }
            }
            catch (System.Exception exception)
            {
                loading = false;
                Debug.LogException(exception, this);
            }
        }

        private void Quit()
        {
            if (!CanUseMenu)
                return;

            loading = true;
            menuGroup.interactable = false;
            menuGroup.blocksRaycasts = false;

#if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        private void OnDisable()
        {
            if (!configured)
                return;

            menuGroup.alpha = 0f;
            menuGroup.interactable = false;
            menuGroup.blocksRaycasts = false;
        }

        private void OnDestroy()
        {
            if (restartButton != null)
                restartButton.onClick.RemoveListener(Restart);

            if (quitButton != null)
                quitButton.onClick.RemoveListener(Quit);
        }
    }
}