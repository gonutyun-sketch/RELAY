using TMPro;
using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class CoolingFlowGauge : Interactable
    {
        [SerializeField] private CoolingModule source;
        [SerializeField] private TMP_Text readoutText;
        [SerializeField] private Transform needlePivot;
        [SerializeField] private float minAngle = 135f;
        [SerializeField] private float maxAngle = -135f;

        [SerializeField] private TMP_Text statusText;

        public override bool CanInteract => false;

        public override string Prompt => source == null
            ? "FLOW: NO SOURCE"
            : $"FLOW: {source.Flow:0} L/min\n" +
              $"VALVE: {source.ValveOpening * 100f:0}%";

        public override void Interact() { }

        private void LateUpdate()
        {
            if (readoutText != null)
                readoutText.text = Prompt;

            if (statusText != null)
            {
                statusText.text = source == null
                    ? "NO SOURCE"
                    : $"PRESS: {source.Pressure:0} kPa\n" +
                      $"TEMP: {source.Temperature:0.0} C";
            }

            if (needlePivot == null)
                return;

            float ratio = source == null
                ? 0f
                : Mathf.Clamp01(source.Flow / source.MaxFlow);

            needlePivot.localRotation = Quaternion.Euler(
                0f,
                0f,
                Mathf.Lerp(minAngle, maxAngle, ratio));
        }
    }
}