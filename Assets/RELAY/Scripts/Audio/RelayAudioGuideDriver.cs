using System;
using System.Collections.Generic;
using UnityEngine;

namespace Startup
{
    // Install manually. No editor automation and no changes to puzzle state.
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(450)]
    public sealed class RelayAudioGuideDriver : MonoBehaviour
    {
        [Header("Existing modules")]
        [SerializeField] private PowerModule power;
        [SerializeField] private CoolingModule cooling;
        [SerializeField] private SignalScope signal;
        [SerializeField] private CoreModule core;
        [SerializeField] private ElevatorModule elevator;

        [Header("Sound positions")]
        [SerializeField] private Transform player;
        [SerializeField] private Transform coreBody;
        [SerializeField] private Transform exitDoor;

        [Header("Existing switches and levers")]
        [SerializeField] private MachineSwitch auxSwitch;
        [SerializeField] private MachineSwitch mainLever;
        [SerializeField] private MachineSwitch pumpSwitch;
        [SerializeField] private MachineSwitch startLever;

        [Header("Existing dials and sliders")]
        [SerializeField] private MachineDial voltageDial;
        [SerializeField] private MachineDial balanceDial;
        [SerializeField] private MachineDial frequencyDial;
        [SerializeField] private MachineDial flowValve;
        [SerializeField] private MachineSlider phaseSlider;
        [SerializeField] private MachineSlider gainSlider;
        [SerializeField] private Vector2 phaseRange = new Vector2(0f, 345f);
        [SerializeField] private Vector2 gainRange = new Vector2(0.25f, 1.25f);

        [Header("Mix - multiplied by the supplied catalog volume")]
        [SerializeField, Range(0f, 1f)] private float controlsLevel = 0.75f;
        [SerializeField, Range(0f, 1f)] private float machineLevel = 0.65f;
        [SerializeField, Range(0f, 1f)] private float ambienceLevel = 0.5f;
        [SerializeField, Range(0f, 1f)] private float footstepsLevel = 0.65f;
        [SerializeField, Range(0f, 1f)] private float uiLevel = 0.6f;
        [SerializeField, Min(0.2f)] private float stepDistance = 1.15f;
        [SerializeField, Min(0.05f)] private float loopFadeSeconds = 0.35f;

        [Serializable] private class Catalog { public Cue[] items; }
        [Serializable]
        private class Cue
        {
            public string file;
            public bool loop;
            public float volume;
            public float max_distance;
        }
        private sealed class Voice
        {
            public Cue cue;
            public AudioSource source;
            public string group;
            public Transform anchor;
            public bool positionOverride;
            public float target;
        }
        private const string ResourceFolder = "RELAY_Audio_v02";
        private static RelayAudioGuideDriver instance;
        private readonly Dictionary<string, Voice> voices = new Dictionary<string, Voice>();
        private readonly Dictionary<string, List<string>> variants = new Dictionary<string, List<string>>();
        private readonly Dictionary<string, int> previousVariant = new Dictionary<string, int>();
        private readonly Dictionary<string, float> playedAt = new Dictionary<string, float>();
        private readonly Dictionary<MachineSwitch, bool> switchStates = new Dictionary<MachineSwitch, bool>();
        private readonly Dictionary<Interactable, float> values = new Dictionary<Interactable, float>();
        private readonly System.Random random = new System.Random();
        private bool ready, wasOnline, wasPumping, wasLocked, wasRunning, wasComplete;
        private bool hot, wasCold;
        private float valveUntil, sliderUntil, travelled, nextAlarm, nextBird;

        private void Awake()
        {
            if (instance != null && instance != this)
            {
                Debug.LogError("RELAY Audio: only one RelayAudioGuideDriver is allowed.", this);
                enabled = false;
                return;
            }
            instance = this;
            TextAsset map = Resources.Load<TextAsset>(ResourceFolder + "/catalog");
            if (map == null)
            {
                Debug.LogError("RELAY Audio: put catalog.json in Assets/RELAY/Resources/RELAY_Audio_v02/.", this);
                enabled = false;
                return;
            }
            Catalog catalog = JsonUtility.FromJson<Catalog>("{\"items\":" + map.text + "}");
            Dictionary<string, AudioClip> clips = new Dictionary<string, AudioClip>();
            foreach (AudioClip clip in Resources.LoadAll<AudioClip>(ResourceFolder))
            {
                if (clips.ContainsKey(clip.name))
                {
                    Debug.LogError("RELAY Audio: duplicate AudioClip name: " + clip.name, this);
                    enabled = false;
                    return;
                }
                clips.Add(clip.name, clip);
            }
            foreach (Cue cue in catalog.items)
            {
                string[] parts = cue.file.Split('/');
                string id = System.IO.Path.GetFileNameWithoutExtension(cue.file);
                if (!clips.TryGetValue(id, out AudioClip clip))
                {
                    Debug.LogWarning("RELAY Audio: missing WAV: " + id, this);
                    continue;
                }
                GameObject child = new GameObject("Audio_" + id);
                child.transform.SetParent(transform, false);
                AudioSource source = child.AddComponent<AudioSource>();
                source.playOnAwake = false;
                source.loop = cue.loop;
                source.clip = clip;
                source.pitch = 1f;
                source.dopplerLevel = 0f;
                source.reverbZoneMix = 0f;
                source.ignoreListenerVolume = false;
                source.ignoreListenerPause = id.StartsWith("UI_", StringComparison.Ordinal);
                source.spatialBlend = (parts[1] == "08_Ambience" || parts[1] == "09_UI" ||
                    parts[1] == "10_Ending" || parts[1] == "07_Footsteps" ||
                    id == "Interaction_Blocked") ? 0f : 1f;
                source.rolloffMode = AudioRolloffMode.Linear;
                source.minDistance = 1.5f;
                source.maxDistance = Mathf.Max(2f, cue.max_distance);
                source.volume = 0f;
                Voice voice = new Voice { cue = cue, source = source, group = parts[1] };
                voice.anchor = AnchorFor(voice.group);
                if (id == "Lab_ExitDoor_Open" && exitDoor != null) voice.anchor = exitDoor;
                voices.Add(id, voice);
                int split = id.LastIndexOf('_');
                if (split > 0 && int.TryParse(id.Substring(split + 1), out int unused))
                {
                    string family = id.Substring(0, split);
                    if (!variants.ContainsKey(family)) variants.Add(family, new List<string>());
                    variants[family].Add(id);
                }
            }
        }

        private Transform AnchorFor(string group)
        {
            switch (group)
            {
                case "01_Controls": case "02_Power": return power != null ? power.transform : player;
                case "03_Cooling": return cooling != null ? cooling.transform : player;
                case "04_Signal": return signal != null ? signal.transform : player;
                case "05_Core": return coreBody != null ? coreBody : (core != null ? core.transform : player);
                case "06_Elevator": return elevator != null ? elevator.transform : player;
                default: return player;
            }
        }

        private void Start()
        {
            if (!enabled || instance != this) return;
            wasOnline = power != null && power.IsOnline;
            wasPumping = cooling != null && cooling.IsPumping;
            wasLocked = signal != null && signal.IsLocked;
            wasRunning = core != null && core.IsStarting;
            wasComplete = core != null && core.IsComplete;
            CaptureSwitch(auxSwitch); CaptureSwitch(mainLever); CaptureSwitch(pumpSwitch); CaptureSwitch(startLever);
            CaptureValue(voltageDial); CaptureValue(balanceDial); CaptureValue(frequencyDial); CaptureValue(flowValve);
            CaptureValue(phaseSlider); CaptureValue(gainSlider);
            nextBird = Time.time + 10f;
            ready = true;
        }

        private void CaptureSwitch(MachineSwitch s) { if (s != null) switchStates[s] = s.IsOn; }
        private void CaptureValue(Interactable control)
        {
            if (control is MachineDial d) values[control] = d.Value;
            else if (control is MachineSlider s) values[control] = s.Value;
        }

        private float Level(Voice v)
        {
            float group = v.group == "01_Controls" ? controlsLevel :
                v.group == "08_Ambience" ? ambienceLevel :
                v.group == "07_Footsteps" ? footstepsLevel :
                v.group == "09_UI" ? uiLevel : machineLevel;
            return Mathf.Clamp01(v.cue.volume * group);
        }

        private string Resolve(string id)
        {
            if (voices.ContainsKey(id)) return id;
            if (!variants.TryGetValue(id, out List<string> options) || options.Count == 0) return null;
            int index = random.Next(options.Count);
            if (options.Count > 1 && previousVariant.TryGetValue(id, out int old) && index == old)
                index = (index + 1 + random.Next(options.Count - 1)) % options.Count;
            previousVariant[id] = index;
            return options[index];
        }

        public static void Play(string id) { if (instance != null) instance.Emit(id, null); }
        public static void PlayAt(string id, Vector3 position) { if (instance != null) instance.Emit(id, position); }
        private void Emit(string id, Vector3? position)
        {
            if (!ready || !isActiveAndEnabled) return;
            if (AudioListener.pause && !id.StartsWith("UI_", StringComparison.Ordinal)) return;
            float gap = id == "Interaction_Blocked" ? .25f : id == "Core_GlassArc" ? .35f : .045f;
            if (playedAt.TryGetValue(id, out float last) && Time.unscaledTime - last < gap) return;
            string key = Resolve(id);
            if (key == null || !voices.TryGetValue(key, out Voice v) || v.cue.loop) return;
            playedAt[id] = Time.unscaledTime;
            v.positionOverride = position.HasValue;
            v.source.transform.position = position ?? (v.anchor != null ? v.anchor.position : transform.position);
            v.source.volume = Level(v);
            v.source.PlayOneShot(v.source.clip, 1f);
        }

        public static void SetLoop(string id, bool playing, float amount = 1f)
        {
            if (instance == null || !instance.ready || !instance.voices.TryGetValue(id, out Voice v) || !v.cue.loop) return;
            v.target = playing ? Mathf.Clamp01(amount) : 0f;
        }
        public static void Stop(string id)
        {
            if (instance == null) return;
            if (!instance.voices.TryGetValue(id, out Voice v))
            {
                if (instance.variants.TryGetValue(id, out List<string> group))
                    foreach (string name in group) Stop(name);
                return;
            }
            v.target = 0f;
            v.source.Stop();
            v.source.volume = 0f;
        }

        private void WatchSwitch(MachineSwitch s, string on, string off)
        {
            if (s == null) return;
            bool old = switchStates.TryGetValue(s, out bool state) && state;
            if (old != s.IsOn) PlayAt(s.IsOn ? on : off, s.transform.position);
            switchStates[s] = s.IsOn;
        }

        private bool Changed(Interactable control, float value)
        {
            bool result = values.TryGetValue(control, out float old) && !Mathf.Approximately(old, value);
            values[control] = value;
            return result;
        }
        private void WatchDial(MachineDial dial)
        {
            if (dial != null && Changed(dial, dial.Value)) PlayAt("Dial_Detent", dial.transform.position);
        }
        private void WatchSlider(MachineSlider slider, Vector2 range)
        {
            if (slider == null) return;
            float old = values.TryGetValue(slider, out float prior) ? prior : slider.Value;
            if (!Changed(slider, slider.Value)) return;
            sliderUntil = Time.time + .12f;
            if (voices.TryGetValue("Slider_Travel_Loop", out Voice v)) v.anchor = slider.transform;
            float epsilon = Mathf.Abs(range.y - range.x) * .0001f;
            bool atEnd = slider.Value <= range.x + epsilon || slider.Value >= range.y - epsilon;
            bool wasEnd = old <= range.x + epsilon || old >= range.y - epsilon;
            if (atEnd && !wasEnd) PlayAt("Slider_EndStop", slider.transform.position);
        }

        private void LateUpdate()
        {
            if (!ready || AudioListener.pause || Time.timeScale <= 0f) return;
            WatchSwitch(auxSwitch, "Switch_On_01", "Switch_Off_01");
            WatchSwitch(pumpSwitch, "Switch_On_02", "Switch_Off_02");
            WatchSwitch(mainLever, "Lever_Engage_01", "Lever_Release_01");
            WatchSwitch(startLever, "Lever_Engage_02", "Lever_Release_02");
            WatchDial(voltageDial); WatchDial(balanceDial); WatchDial(frequencyDial);
            if (flowValve != null && Changed(flowValve, flowValve.Value)) valveUntil = Time.time + .16f;
            if (voices.TryGetValue("Valve_Wheel_Loop", out Voice valve)) valve.anchor = flowValve != null ? flowValve.transform : null;
            WatchSlider(phaseSlider, phaseRange); WatchSlider(gainSlider, gainRange);
            SetLoop("Valve_Wheel_Loop", Time.time < valveUntil);
            SetLoop("Slider_Travel_Loop", Time.time < sliderUntil);

            bool online = power != null && power.IsOnline;
            bool pumping = cooling != null && cooling.IsPumping;
            bool locked = signal != null && signal.IsLocked;
            bool running = core != null && core.IsStarting;
            bool complete = core != null && core.IsComplete;
            bool outside = elevator != null && elevator.HasArrived;
            if (online != wasOnline) { Play(online ? "Power_MainOn" : "Power_MainOff"); if (online) Play("Light_Ignition"); }
            if (pumping != wasPumping)
            {
                if (pumping) { Stop("Pump_Stop"); Play("Pump_Start"); }
                else { Stop("Pump_Start"); Play("Pump_Stop"); Play("Pressure_Release"); }
            }
            if (locked && !wasLocked) Play("Signal_Lock");
            if (!locked && wasLocked && online) Play("Signal_Lost");
            if (running && !wasRunning) Play("Core_Charge");
            if (complete && !wasComplete) { Stop("Core_Charge"); Play("Core_Stable"); }
            if (!running && wasRunning && !complete) { Stop("Core_Charge"); Play("Core_Abort"); }
            SetLoop("Power_Transformer_Loop", online);
            SetLoop("Pump_Run_Loop", pumping);
            SetLoop("Coolant_Flow_Loop", pumping, cooling != null ? cooling.Flow / cooling.MaxFlow : 0f);
            SetLoop("Signal_Electronics_Loop", online);
            SetLoop("Core_Idle_Loop", online && !running && !complete);
            SetLoop("Core_Active_Loop", online && (running || complete));
            SetLoop("Lab_Unpowered_Loop", !online && !outside);
            SetLoop("Lab_Ventilation_Loop", online && !outside);
            SetLoop("Forest_Wind_Loop", outside);
            SetLoop("Pine_Canopy_Loop", outside, .55f);
            if (outside && Time.time >= nextBird)
            {
                Play("Forest_DistantBird"); nextBird = Time.time + 12f + (float)random.NextDouble() * 13f;
            }
            bool warningAllowed = online && core != null && core.isActiveAndEnabled && cooling != null && cooling.isActiveAndEnabled;
            float temperature = cooling != null ? cooling.Temperature : 70f;
            bool nextHot = warningAllowed && (hot ? temperature > 77f : temperature >= 80f);
            bool cold = warningAllowed && temperature < 65f;
            if ((nextHot && !hot) || (cold && !wasCold)) nextAlarm = 0f;
            if (!nextHot) Stop("Core_Heat_Warning");
            if (!cold) Stop("Core_Cold_Warning");
            hot = nextHot; wasCold = cold;
            if ((hot || cold) && Time.time >= nextAlarm)
            {
                Play(hot ? "Core_Heat_Warning" : "Core_Cold_Warning"); nextAlarm = Time.time + 5f;
            }
            wasOnline = online; wasPumping = pumping; wasLocked = locked; wasRunning = running; wasComplete = complete;
            foreach (Voice v in voices.Values)
            {
                if (!v.positionOverride && v.anchor != null) v.source.transform.position = v.anchor.position;
                if (!v.cue.loop) continue;
                float goal = v.target * Level(v);
                v.source.volume = Mathf.MoveTowards(v.source.volume, goal,
                    Time.deltaTime * Mathf.Max(.02f, Level(v)) / Mathf.Max(.05f, loopFadeSeconds));
                if (v.target > 0f && !v.source.isPlaying) v.source.Play();
                if (v.target <= 0f && v.source.volume <= .0001f && v.source.isPlaying) v.source.Stop();
            }
        }

        public static void Walked(float distance, bool walking)
        {
            if (instance == null || !instance.ready) return;
            RelayAudioGuideDriver d = instance;
            if (!walking || distance > .75f || AudioListener.pause || Time.timeScale <= 0f) { d.travelled = 0f; return; }
            d.travelled += Mathf.Max(0f, distance);
            if (d.travelled < d.stepDistance) return;
            d.travelled %= d.stepDistance;
            bool inCage = d.elevator != null && d.elevator.PlayerFullyInside;
            bool forest = d.elevator != null && d.elevator.HasArrived;
            Play(inCage ? "Step_Metal" : forest ? "Step_Forest" : "Step_Concrete");
        }

        // These instance methods can be selected in UI Button/EventTrigger lists.
        public void PlayUiHover() { Play("UI_Hover"); }
        public void PlayUiConfirm() { Play("UI_Confirm"); }
        public void PlayUiBack() { Play("UI_Back"); }

        private void OnDisable()
        {
            foreach (Voice v in voices.Values) { v.target = 0f; if (v.source != null) v.source.Stop(); }
        }
        private void OnDestroy() { if (instance == this) instance = null; }
    }
}
