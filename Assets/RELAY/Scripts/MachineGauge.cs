using TMPro;
using UnityEngine;

namespace Startup
{
    public sealed class MachineGauge : Interactable
    {
        [SerializeField] private MachineDial sourceDial;
        [SerializeField] private TMP_Text readoutText;
        [SerializeField] private Transform needlePivot;
        [SerializeField] private float minAngle = 135f;
        [SerializeField] private float maxAngle = -135f;
        [SerializeField] private PowerModule powerSource;

        private float DisplayValue => powerSource != null
            ? powerSource.Voltage
            : (sourceDial != null ? sourceDial.Value : 0f);

        public override bool CanInteract => false;

        public override string Prompt
        {
            get
            {
                if (sourceDial == null)
                    return $"{DisplayName}: NO SOURCE";

                if (powerSource != null)
                {
                    return $"VOLTAGE: {powerSource.Voltage:0.#} V\n"
                         + $"CURRENT: {powerSource.Current:0.#} A";
                }

                return $"{DisplayName}: "
                     + $"{DisplayValue:0.##} {sourceDial.Unit}";
            }
        }

        public override void Interact() { }

        private void LateUpdate()
        {
            if (readoutText != null)
                readoutText.text = Prompt;

            if (needlePivot == null || sourceDial == null)
                return;

            float t = Mathf.InverseLerp(
                sourceDial.MinValue,
                sourceDial.MaxValue,
                DisplayValue);

            needlePivot.localRotation = Quaternion.Euler(
                0f, 0f, Mathf.Lerp(minAngle, maxAngle, t));
        }
    }
}