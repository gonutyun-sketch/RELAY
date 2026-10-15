using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;

namespace Startup
{
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-210)]
    public sealed class ExitTerminal : Interactable
    {
        [Header("Existing scene references")]
        [SerializeField] private CoreModule coreSource;
        [SerializeField] private ExitDoor exitDoor;
        [SerializeField] private FirstPersonMotor motor;

        [Header("Manually assembled UI - keep existing references")]
        [SerializeField] private CanvasGroup screenGroup;
        [SerializeField] private TMP_Text bodyText;
        [SerializeField] private TMP_Text inputText;
        [SerializeField] private TMP_Text feedbackText;
        [SerializeField] private TMP_Text worldStatus;

        [Header("New connections")]
        [SerializeField] private RectTransform progressFill;
        [SerializeField] private Renderer worldScreenRenderer;
        [SerializeField] private AudioSource successSource;
        [SerializeField] private AudioClip successClip;
        [SerializeField, Range(0f, 1f)] private float successVolume = 0.65f;

        [Header("Timing")]
        [SerializeField, Min(20f)] private float charactersPerSecond = 80f;
        [SerializeField, Min(0.1f)] private float transferSeconds = 2.5f;
        [SerializeField, Min(0.1f)] private float acceptedHoldSeconds = 0.9f;

        private static readonly Key[] NumberKeys =
        {
            Key.Digit0, Key.Digit1, Key.Digit2, Key.Digit3, Key.Digit4,
            Key.Digit5, Key.Digit6, Key.Digit7, Key.Digit8, Key.Digit9
        };
        private static readonly Key[] NumpadKeys =
        {
            Key.Numpad0, Key.Numpad1, Key.Numpad2, Key.Numpad3, Key.Numpad4,
            Key.Numpad5, Key.Numpad6, Key.Numpad7, Key.Numpad8, Key.Numpad9
        };
        private static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");
        private static readonly int EmissionColorId = Shader.PropertyToID("_EmissionColor");
        private readonly TerminalRecoveryProgress recovery = new TerminalRecoveryProgress();
        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;
        private Material originalScreenMaterial;
        private Material runtimeScreenMaterial;
        private bool screenWasPowered;
        private bool configured, open, booted, closing, lostFocus;
        private bool motorWasEnabled, interactorWasEnabled, dragWasEnabled;
        private CursorLockMode savedLock;
        private bool savedCursorVisible;
        private string digits = "";
        private float visibleCharacters, sessionTime, feedbackRemaining;
        private int characterCount, transferStartedFrame;

        public CoreModule CoreSource => coreSource;
        public ExitDoor ControlledDoor => exitDoor;
        public bool IsSolved => recovery.IsComplete;
        public bool IsPowered => configured && coreSource != null && coreSource.HasExitPower;
        public override bool CanInteract => configured && !open && !IsSolved;
        public override string Prompt => IsPowered ? "Use terminal" : "No power";

        private void Awake()
        {
            if (coreSource == null || exitDoor == null || motor == null || screenGroup == null ||
                bodyText == null || inputText == null || feedbackText == null || worldStatus == null)
            { Fail("Assign the eight existing references, including World Status from StatusCanvas."); return; }
            interactor = motor.GetComponent<PlayerInteractor>();
            sliderDrag = motor.GetComponent<SliderDragInput>();
            if (interactor == null || sliderDrag == null || exitDoor.Source != coreSource || exitDoor.SecurityTerminal != this)
            { Fail("Use the existing Player and the matching Core / Exit Door / Security Terminal references."); return; }

            Canvas canvas = screenGroup.GetComponentInParent<Canvas>();
            RectTransform screenRect = screenGroup.transform as RectTransform;
            if (canvas == null || canvas.rootCanvas.renderMode != RenderMode.ScreenSpaceOverlay ||
                screenGroup.GetComponent<Canvas>() != null || screenRect == null ||
                transform.IsChildOf(screenGroup.transform) || motor.transform.IsChildOf(screenGroup.transform) ||
                !bodyText.transform.IsChildOf(screenGroup.transform) || !inputText.transform.IsChildOf(screenGroup.transform) ||
                !feedbackText.transform.IsChildOf(screenGroup.transform) || bodyText == inputText ||
                inputText == feedbackText || bodyText == feedbackText)
            { Fail("Screen Group needs TerminalScreen under the overlay Canvas and three distinct text children."); return; }
            if (worldStatus.transform.IsChildOf(screenGroup.transform) || !worldStatus.transform.IsChildOf(transform))
            { Fail("World Status must be EXIT_Terminal > StatusCanvas > WorldStatus. Do not assign FooterText."); return; }
            if (screenRect.anchorMin.sqrMagnitude > 0.0001f ||
                (screenRect.anchorMax - Vector2.one).sqrMagnitude > 0.0001f ||
                screenRect.offsetMin.sqrMagnitude > 0.01f || screenRect.offsetMax.sqrMagnitude > 0.01f)
            { Fail("TerminalScreen needs full-stretch anchors and all four offsets at 0."); return; }

            // Hide only the validated overlay; never create or assemble scene objects.
            HideScreen();
            worldStatus.text = "";
            if (progressFill == null || worldScreenRenderer == null || successSource == null || successClip == null)
            { Fail("Assign Progress Fill, World Screen Renderer, Success Source and Success Clip (v02 guide)."); return; }
            if (!progressFill.IsChildOf(screenGroup.transform) || progressFill == screenRect ||
                bodyText.transform.IsChildOf(progressFill) || inputText.transform.IsChildOf(progressFill) ||
                feedbackText.transform.IsChildOf(progressFill) ||
                progressFill.GetComponent<UnityEngine.UI.Image>() == null)
            { Fail("Progress Fill must be the empty Image TerminalPanel > ProgressTrack > ProgressFill, not a panel or text."); return; }
            if (!worldScreenRenderer.transform.IsChildOf(transform) || worldScreenRenderer.sharedMaterials.Length != 1 ||
                !successSource.transform.IsChildOf(transform) || successSource.transform.IsChildOf(screenGroup.transform))
            { Fail("Use the single-material CRT screen Renderer and an AudioSource on EXIT_Terminal."); return; }
            originalScreenMaterial = worldScreenRenderer.sharedMaterial;
            if (originalScreenMaterial == null || !originalScreenMaterial.HasProperty(BaseColorId) ||
                !originalScreenMaterial.HasProperty(EmissionColorId))
            { Fail("The CRT screen needs its external RLYT_CRTScreen material using URP/Lit."); return; }

            // Instance exists only in Play mode; the shared .mat asset is never edited.
            runtimeScreenMaterial = new Material(originalScreenMaterial);
            runtimeScreenMaterial.name = originalScreenMaterial.name + " (terminal runtime)";
            runtimeScreenMaterial.EnableKeyword("_EMISSION");
            worldScreenRenderer.sharedMaterial = runtimeScreenMaterial;
            successSource.playOnAwake = false;
            successSource.loop = false;
            successSource.spatialBlend = 0f;
            successSource.reverbZoneMix = 0f;
            successSource.ignoreListenerVolume = false;
            successSource.ignoreListenerPause = false;
            configured = true;
            SetProgress(0f);
            UpdateWorldScreen(true);
        }

        private void Fail(string message)
        {
            Debug.LogError("ExitTerminal: " + message, this);
            enabled = false;
        }

        public override void Interact() { TryInteract(); }
        public override bool TryInteract()
        {
            if (!CanInteract || !IsPowered || motor == null || !motor.CanInteractThisFrame ||
                !interactor.isActiveAndEnabled || Time.timeScale <= 0f) return false;
            motorWasEnabled = motor.enabled;
            interactorWasEnabled = interactor.enabled;
            dragWasEnabled = sliderDrag.enabled;
            savedLock = Cursor.lockState;
            savedCursorVisible = Cursor.visible;
            open = true;
            closing = lostFocus = false;
            sessionTime = feedbackRemaining = 0f;
            digits = "";
            recovery.CancelPending();
            SetProgress(0f);
            sliderDrag.enabled = false;
            interactor.enabled = false;
            motor.enabled = false;
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(null);
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
            screenGroup.gameObject.SetActive(true);
            screenGroup.alpha = 0f;
            screenGroup.interactable = false;
            screenGroup.blocksRaycasts = true;
            ShowPuzzle(!booted);
            return true;
        }

        private void ShowPuzzle(bool typewriter)
        {
            bodyText.text = Monospaced(SecuritySequenceRule.Display(recovery.CompletedRecords));
            bodyText.maxVisibleCharacters = int.MaxValue;
            bodyText.ForceMeshUpdate();
            characterCount = bodyText.textInfo.characterCount;
            booted = !typewriter;
            visibleCharacters = booted ? characterCount : 0;
            bodyText.maxVisibleCharacters = Mathf.FloorToInt(visibleCharacters);
            SetFeedback(booted ? "AWAITING VALUE" : "RESTORING LOCAL RECORD...");
            RefreshInput();
        }

        private void Update()
        {
            if (!configured || !open || closing) return;
            if (!Application.isFocused)
            { lostFocus = closing = true; return; }
            if (!IsPowered) { closing = true; return; }
            sessionTime += Time.unscaledDeltaTime;
            screenGroup.alpha = Mathf.MoveTowards(screenGroup.alpha, 1f, Time.unscaledDeltaTime / 0.12f);
            Keyboard keyboard = Keyboard.current;
            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
            { closing = true; return; }
            if (Time.timeScale <= 0f || recovery.IsTransferring) return;
            if (!booted)
            {
                visibleCharacters = Mathf.Min(characterCount,
                    visibleCharacters + Mathf.Max(20f, charactersPerSecond) * Time.unscaledDeltaTime);
                bodyText.maxVisibleCharacters = Mathf.FloorToInt(visibleCharacters);
                if (visibleCharacters < characterCount) return;
                booted = true;
                SetFeedback("AWAITING VALUE");
                RefreshInput();
                return; // Do not consume a key held during boot.
            }
            if (feedbackRemaining > 0f)
            {
                feedbackRemaining -= Time.unscaledDeltaTime;
                if (feedbackRemaining <= 0f) SetFeedback("AWAITING VALUE");
            }
            if (keyboard != null)
            {
                bool edited = false;
                if (keyboard.backspaceKey.wasPressedThisFrame && digits.Length > 0)
                { digits = digits.Substring(0, digits.Length - 1); edited = true; }
                for (int number = 0; number < 10; number++)
                    if (digits.Length < SecuritySequenceRule.MaximumDigits &&
                        (keyboard[NumberKeys[number]].wasPressedThisFrame || keyboard[NumpadKeys[number]].wasPressedThisFrame))
                    { digits += (char)('0' + number); edited = true; }
                if (edited) { feedbackRemaining = 0f; SetFeedback("AWAITING VALUE"); }
                if (keyboard.enterKey.wasPressedThisFrame || keyboard.numpadEnterKey.wasPressedThisFrame)
                {
                    if (recovery.Submit(digits))
                    {
                        transferStartedFrame = Time.frameCount;
                        SetFeedback("VALUE VERIFIED / TRANSFERRING RECORD...");
                        RefreshTransfer();
                        return;
                    }
                    SetFeedback(digits.Length == 0 ? "ENTER A VALUE" : "VALUE REJECTED / TRY AGAIN");
                    feedbackRemaining = 1.5f;
                    RelayAudioGuideDriver.Play("Interaction_Blocked");
                }
            }
            RefreshInput();
        }

        private void LateUpdate()
        {
            if (!configured) return;
            // Evaluate power AFTER CoreModule.Update; door authorization cannot win a power-loss race.
            bool powered = IsPowered;
            if (!powered && !IsSolved)
            { recovery.ResetForPowerLoss(); booted = false; if (open) closing = true; }
            UpdateWorldScreen();
            if (!open) return;
            if (!Application.isFocused) { lostFocus = closing = true; }
            if (closing) { recovery.CancelPending(); CloseSession(); return; }
            if (!recovery.IsTransferring || Time.timeScale <= 0f || transferStartedFrame == Time.frameCount) return;

            bool finishedRecord = recovery.Advance(Time.unscaledDeltaTime, transferSeconds, acceptedHoldSeconds);
            RefreshTransfer();
            if (!finishedRecord) return;
            if (IsSolved)
            {
                // The source is on the physical terminal so hiding the overlay cannot cut the sound.
                successSource.PlayOneShot(successClip, successVolume);
                CloseSession();
            }
            else
            {
                RelayAudioGuideDriver.Play("UI_Confirm");
                digits = "";
                feedbackRemaining = 0f;
                SetProgress(0f);
                ShowPuzzle(true);
            }
        }

        private void RefreshTransfer()
        {
            SetProgress(recovery.Fill);
            // Never show 100% until the actual fill reaches 1.
            int percent = Mathf.FloorToInt(recovery.Fill * 100f);
            inputText.text = Monospaced("TRANSFER: " + percent.ToString("000") + "%");
            if (recovery.Fill >= 1f)
                SetFeedback(recovery.CompletedRecords == 0 ? "RECORD RESTORED" : "ACCESS GRANTED");
        }

        private void SetProgress(float amount)
        {
            // A plain Image without a Sprite still works: change its anchors, not Image.fillAmount.
            progressFill.anchorMin = Vector2.zero;
            progressFill.anchorMax = new Vector2(Mathf.Clamp01(amount), 1f);
            progressFill.offsetMin = progressFill.offsetMax = Vector2.zero;
        }

        private void RefreshInput()
        {
            bool cursor = booted && Mathf.FloorToInt(sessionTime * 2f) % 2 == 0;
            inputText.text = Monospaced(!booted ? "INPUT: [ ---- ]" :
                "INPUT: [ " + digits.PadRight(SecuritySequenceRule.MaximumDigits, ' ') + (cursor ? "_" : " ") + " ]");
        }
        private static string Monospaced(string text) => "<mspace=0.65em>" + text + "</mspace>";
        private void SetFeedback(string text) { feedbackText.text = Monospaced(text); }

        private void UpdateWorldScreen(bool force = false)
        {
            if (worldStatus != null && worldStatus.text.Length > 0) worldStatus.text = "";
            bool powered = IsPowered;
            if (runtimeScreenMaterial == null || (!force && powered == screenWasPowered)) return;
            screenWasPowered = powered;
            runtimeScreenMaterial.SetColor(BaseColorId, powered ? (Color)new Color32(10, 28, 64, 255) : new Color32(2, 3, 5, 255));
            runtimeScreenMaterial.SetColor(EmissionColorId, powered ? (Color)new Color32(18, 65, 170, 255) : Color.black);
        }

        private void HideScreen()
        {
            if (screenGroup == null) return;
            screenGroup.alpha = 0f;
            screenGroup.interactable = false;
            screenGroup.blocksRaycasts = false;
            screenGroup.gameObject.SetActive(false);
        }

        private void CloseSession()
        {
            if (!open) return;
            open = closing = false;
            HideScreen();
            if (EventSystem.current != null) EventSystem.current.SetSelectedGameObject(null);
            if (motor != null) motor.enabled = motorWasEnabled;
            if (interactor != null) interactor.enabled = interactorWasEnabled;
            if (sliderDrag != null) sliderDrag.enabled = dragWasEnabled;
            bool release = lostFocus || !Application.isFocused;
            Cursor.lockState = release ? CursorLockMode.None : savedLock;
            Cursor.visible = release || savedCursorVisible;
        }

        private void OnApplicationFocus(bool focused)
        {
            if (focused || !open) return;
            lostFocus = closing = true;
            if (screenGroup != null) screenGroup.alpha = 0f;
        }
        private void OnDisable()
        {
            recovery.CancelPending();
            if (open) CloseSession();
            else if (configured) HideScreen();
            if (runtimeScreenMaterial != null)
            {
                runtimeScreenMaterial.SetColor(BaseColorId, new Color32(2, 3, 5, 255));
                runtimeScreenMaterial.SetColor(EmissionColorId, Color.black);
                screenWasPowered = false;
            }
        }
        private void OnDestroy()
        {
            if (runtimeScreenMaterial == null) return;
            if (worldScreenRenderer != null && worldScreenRenderer.sharedMaterial == runtimeScreenMaterial)
                worldScreenRenderer.sharedMaterial = originalScreenMaterial;
            Destroy(runtimeScreenMaterial);
        }
    }
}
