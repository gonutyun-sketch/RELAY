using UnityEngine;
using UnityEngine.UI;

namespace Startup
{
    // PauseSettings runs first (-300), then this, then FirstPersonMotor (-100).
    // Attach to MountainEnding. All boundary distances use its local space.
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-250)]
    public sealed class ForestFogReturn : MonoBehaviour
    {
        [Header("Existing scene references")]
        [SerializeField] private FirstPersonMotor playerMotor;
        [SerializeField] private ElevatorModule elevator;
        [SerializeField] private Transform returnPoint;
        [SerializeField] private CanvasGroup whiteFade;

        [Header("Forest boundary - local metres")]
        [SerializeField, Min(1f)] private float halfWidth = 9.5f;
        [SerializeField, Min(1f)] private float farEdgeZ = 19.5f;
        [SerializeField, Min(0.1f)] private float mistStartDistance = 3.5f;
        [SerializeField, Min(0.1f)] private float returnDistance = 0.85f;

        [Header("Fog")]
        [SerializeField] private Color fogColor = new Color(0.72f, 0.76f, 0.77f, 1f);
        [SerializeField, Range(0.001f, 0.3f)] private float forestDensity = 0.055f;
        [SerializeField, Range(0.01f, 0.6f)] private float edgeDensity = 0.26f;
        [SerializeField, Range(0f, 0.8f)] private float edgeWhiteout = 0.5f;
        [SerializeField, Min(0.1f)] private float forestBlendSeconds = 2f;
        [SerializeField] private bool useFogColoredSky = true;

        [Header("Return transition")]
        [SerializeField, Min(0.2f)] private float fadeInSeconds = 1.1f;
        [SerializeField, Min(0.05f)] private float whiteHoldSeconds = 0.25f;
        [SerializeField, Min(0.2f)] private float fadeOutSeconds = 1.2f;
        [SerializeField, Min(0.1f)] private float cooldownSeconds = 1.5f;

        private enum Phase { Walking, Cover, Hold, Reveal, RestorePending }
        private Phase phase;
        private CharacterController controller;
        private PlayerInteractor interactor;
        private SliderDragInput sliderDrag;
        private Camera viewCamera;
        private bool configured, ownsFog, ownsControls;
        private bool motorWasEnabled, interactorWasEnabled, dragWasEnabled;
        private bool savedFog;
        private FogMode savedFogMode;
        private Color savedFogColor, savedCameraColor;
        private float savedDensity, savedStart, savedEnd;
        private CameraClearFlags savedClearFlags;
        private float forestBlend, edgeBlend, elapsed, coverStartAlpha, cooldown;

        private void Start()
        {
            if (playerMotor == null || elevator == null ||
                returnPoint == null || whiteFade == null)
            {
                Fail("Assign Player Motor, Elevator, Return Point and White Fade.");
                return;
            }

            controller = playerMotor.GetComponent<CharacterController>();
            interactor = playerMotor.GetComponent<PlayerInteractor>();
            sliderDrag = playerMotor.GetComponent<SliderDragInput>();
            viewCamera = playerMotor.ViewCamera != null
                ? playerMotor.ViewCamera.GetComponent<Camera>() : null;
            Image image = whiteFade.GetComponent<Image>();
            Canvas canvas = whiteFade.GetComponentInParent<Canvas>();

            if (controller == null || interactor == null || sliderDrag == null ||
                viewCamera == null || image == null || canvas == null)
            {
                Fail("Use the existing Player, and a UI Image with Canvas Group inside FogCanvas.");
                return;
            }
            if (!whiteFade.gameObject.activeInHierarchy || !image.enabled ||
                !canvas.isActiveAndEnabled ||
                canvas.renderMode != RenderMode.ScreenSpaceOverlay)
            {
                Fail("Keep FogCanvas and FogWhiteout active; use Screen Space - Overlay.");
                return;
            }
            if ((transform.lossyScale - Vector3.one).sqrMagnitude > 0.0001f ||
                mistStartDistance <= returnDistance || returnDistance <= controller.radius)
            {
                Fail("MountainEnding needs scale 1. Mist Start must exceed Return Distance, which must exceed the player radius.");
                return;
            }
            Vector3 home = transform.InverseTransformPoint(returnPoint.position);
            if (returnPoint.IsChildOf(playerMotor.transform) ||
                home.z < 0.5f || home.y < -0.1f || home.y > 1f ||
                EdgeDistance(home) <= mistStartDistance)
            {
                Fail("Place Return Point inside the safe forest entrance, e.g. local (0, 0.08, 3).");
                return;
            }

            image.color = Color.white;
            image.raycastTarget = true;
            whiteFade.interactable = false;
            SetWhiteout(0f, false);
            configured = true;
        }

        private void Update()
        {
            if (!configured) return;

            if (playerMotor == null || elevator == null || returnPoint == null ||
                whiteFade == null || !whiteFade.gameObject.activeInHierarchy)
            {
                Fail("A required object was removed or disabled during play.");
                return;
            }

            if (!ownsFog)
            {
                if (!elevator.HasArrived) return;
                CaptureEnvironment();
            }

            // Pause or loss of focus must not complete a return behind the player's back.
            if (!Application.isFocused || Time.timeScale <= 0f)
            {
                if (phase == Phase.Walking) SetWhiteout(0f, false);
                return;
            }
            float dt = Mathf.Min(Time.deltaTime, 0.05f);

            if (phase != Phase.Walking)
            {
                LockCursor();
                AdvanceReturn(dt);
                return;
            }

            forestBlend = Mathf.MoveTowards(forestBlend, 1f,
                dt / Mathf.Max(0.1f, forestBlendSeconds));
            cooldown = Mathf.Max(0f, cooldown - dt);

            Vector3 local = transform.InverseTransformPoint(playerMotor.transform.position);
            bool atForestHeight = local.y >= -1f && local.y <= 6f && local.z >= 0f;
            float distance = EdgeDistance(local);
            float targetEdge = atForestHeight
                ? 1f - Mathf.InverseLerp(returnDistance, mistStartDistance, distance)
                : 0f;
            edgeBlend = Mathf.MoveTowards(edgeBlend, targetEdge, dt * 2f);
            float easedEdge = Mathf.SmoothStep(0f, 1f, edgeBlend);
            ApplyFog(Mathf.Lerp(forestDensity, edgeDensity, easedEdge));
            SetWhiteout(playerMotor.isActiveAndEnabled && playerMotor.HasControl
                ? easedEdge * edgeWhiteout : 0f, false);

            if (atForestHeight && distance <= returnDistance && cooldown <= 0f &&
                playerMotor.isActiveAndEnabled && playerMotor.HasControl &&
                controller.enabled)
            {
                BeginReturn();
            }
        }

        private float EdgeDistance(Vector3 local)
        {
            // The rear entrance remains open to the elevator.
            return Mathf.Min(halfWidth - Mathf.Abs(local.x), farEdgeZ - local.z);
        }

        private void CaptureEnvironment()
        {
            savedFog = RenderSettings.fog;
            savedFogMode = RenderSettings.fogMode;
            savedFogColor = RenderSettings.fogColor;
            savedDensity = RenderSettings.fogDensity;
            savedStart = RenderSettings.fogStartDistance;
            savedEnd = RenderSettings.fogEndDistance;
            savedClearFlags = viewCamera.clearFlags;
            savedCameraColor = viewCamera.backgroundColor;
            ownsFog = true;
        }

        private void ApplyFog(float density)
        {
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = Color.Lerp(savedFogColor, fogColor, forestBlend);
            RenderSettings.fogDensity = Mathf.Lerp(
                savedFog ? savedDensity : 0f, density, forestBlend);

            if (useFogColoredSky)
            {
                // A skybox does not receive ordinary distance fog.
                viewCamera.clearFlags = CameraClearFlags.SolidColor;
                viewCamera.backgroundColor = Color.Lerp(
                    savedCameraColor, fogColor, forestBlend);
            }
        }

        private void BeginReturn()
        {
            motorWasEnabled = playerMotor.enabled;
            interactorWasEnabled = interactor.enabled;
            dragWasEnabled = sliderDrag.enabled;
            ownsControls = true;

            sliderDrag.enabled = false;
            interactor.enabled = false;
            playerMotor.enabled = false; // Resets bob/look; its OnDisable releases cursor.
            LockCursor();
            coverStartAlpha = whiteFade.alpha;
            SetWhiteout(coverStartAlpha, true);
            phase = Phase.Cover;
            RelayAudioGuideDriver.Stop("Fog_Return");
            RelayAudioGuideDriver.Play("Fog_Enter");
            elapsed = 0f;
        }

        private void AdvanceReturn(float dt)
        {
            elapsed += dt;
            switch (phase)
            {
                case Phase.Cover:
                    float coverT = Mathf.Clamp01(elapsed / Mathf.Max(0.2f, fadeInSeconds));
                    SetWhiteout(Mathf.Lerp(coverStartAlpha, 1f,
                        Mathf.SmoothStep(0f, 1f, coverT)), true);
                    if (coverT >= 1f)
                    {
                        phase = Phase.Hold;
                        elapsed = 0f;
                    }
                    break;

                case Phase.Hold:
                    // White is rendered for at least one complete frame before moving.
                    if (elapsed < Mathf.Max(0.05f, whiteHoldSeconds)) break;
                    if (!controller.enabled)
                    {
                        Fail("Player Character Controller was disabled during return.");
                        return;
                    }
                    playerMotor.CarryBy(returnPoint.position - playerMotor.transform.position);
                    playerMotor.transform.rotation =
                        Quaternion.Euler(0f, returnPoint.eulerAngles.y, 0f);
                    playerMotor.ViewCamera.localRotation = Quaternion.identity;
                    Physics.SyncTransforms();
                    edgeBlend = 0f;
                    forestBlend = 1f;
                    ApplyFog(forestDensity);
                    phase = Phase.Reveal;
                    RelayAudioGuideDriver.Stop("Fog_Enter");
                    RelayAudioGuideDriver.Play("Fog_Return");
                    elapsed = 0f;
                    break;

                case Phase.Reveal:
                    float revealT = Mathf.Clamp01(elapsed / Mathf.Max(0.2f, fadeOutSeconds));
                    SetWhiteout(1f - Mathf.SmoothStep(0f, 1f, revealT), true);
                    if (revealT >= 1f) phase = Phase.RestorePending;
                    break;
            }
        }

        private void LateUpdate()
        {
            if (phase != Phase.RestorePending) return;
            // All Update input has finished, so the release-frame click cannot interact.
            RestoreControls();
            SetWhiteout(0f, false);
            cooldown = cooldownSeconds;
            phase = Phase.Walking;
        }

        private void RestoreControls()
        {
            if (!ownsControls) return;
            ownsControls = false;
            if (playerMotor != null) playerMotor.enabled = motorWasEnabled;
            if (interactor != null) interactor.enabled = interactorWasEnabled;
            if (sliderDrag != null) sliderDrag.enabled = dragWasEnabled;
            // Restoring OnEnable resynchronizes FirstPersonMotor's look smoothing.
            if (Application.isFocused) LockCursor();
        }

        private static void LockCursor()
        {
            if (!Application.isFocused) return;
            Cursor.lockState = CursorLockMode.Locked;
            Cursor.visible = false;
        }

        private void SetWhiteout(float alpha, bool blockClicks)
        {
            if (whiteFade == null) return;
            whiteFade.alpha = Mathf.Clamp01(alpha);
            whiteFade.blocksRaycasts = blockClicks;
        }

        private void Fail(string message)
        {
            Debug.LogError("ForestFogReturn: " + message, this);
            enabled = false;
        }

        private void OnDisable()
        {
            RestoreControls();
            SetWhiteout(0f, false);
            phase = Phase.Walking;
            edgeBlend = forestBlend = elapsed = cooldown = 0f;
            if (!ownsFog) return;
            ownsFog = false;
            RenderSettings.fog = savedFog;
            RenderSettings.fogMode = savedFogMode;
            RenderSettings.fogColor = savedFogColor;
            RenderSettings.fogDensity = savedDensity;
            RenderSettings.fogStartDistance = savedStart;
            RenderSettings.fogEndDistance = savedEnd;
            if (viewCamera != null && useFogColoredSky)
            {
                viewCamera.clearFlags = savedClearFlags;
                viewCamera.backgroundColor = savedCameraColor;
            }
        }
    }
}
