using System;

namespace Startup
{
    public static class PowerCalibrationRule
    {
        public const float RequiredVoltage = 70f;
        public const float RequiredCurrent = 30f;

        private static float ClampBalance(float value) => Math.Max(0f, Math.Min(100f, value));

        // Preserve the existing coupling between the two physical dials.
        public static float Voltage(float voltageDial, float balanceDial) =>
            Math.Max(0f, voltageDial - ClampBalance(balanceDial) * 0.1f);

        public static float Current(float voltageDial, float balanceDial) =>
            voltageDial * (0.4f + Math.Abs(ClampBalance(balanceDial) - 50f) * 0.008f);

        // Deliberately no gameplay tolerance, rounding, or 70-80 / <=40 band.
        // The existing 5-unit / 10-unit dial steps can reach 70 and 30 exactly.
        public static bool Matches(float voltage, float current) =>
            voltage == RequiredVoltage && current == RequiredCurrent;
    }
}
