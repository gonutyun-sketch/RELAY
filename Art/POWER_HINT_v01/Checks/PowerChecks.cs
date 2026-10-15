using System;
using Startup;

internal static class PowerChecks
{
    private static int checks;
    private static void Check(bool value, string label)
    { checks++; if (!value) throw new Exception(label); }
    public static void Main()
    {
        int solutions = 0;
        for (int dial = 0; dial <= 100; dial += 5)
            for (int balance = 0; balance <= 100; balance += 10)
            {
                float v = PowerCalibrationRule.Voltage(dial, balance);
                float a = PowerCalibrationRule.Current(dial, balance);
                bool correct = PowerCalibrationRule.Matches(v, a);
                Check(correct == (dial == 75 && balance == 50), "Actual reachable dial grid");
                if (correct) solutions++;
                // One decimal on the current gauge does not conceal a different accepted state.
                bool displayMatches = Math.Round(v, 1) == 70 && Math.Round(a, 1) == 30;
                Check(displayMatches == correct, "Displayed readings agree with acceptance on the reachable grid");
            }
        Check(solutions == 1, "One reachable 70V/30A combination");
        Check(PowerCalibrationRule.Voltage(75,50) == 70f && PowerCalibrationRule.Current(75,50) == 30f,
            "Exact binary float targets are reachable without epsilon");
        foreach (float v in new[] {69f, 69.9f, 69.99f, 70.01f, 70.1f, 71f, 75f, 80f, float.NaN, float.PositiveInfinity})
            Check(!PowerCalibrationRule.Matches(v,30f), "Off voltage rejected");
        foreach (float a in new[] {0f, 29f, 29.9f, 29.99f, 30.01f, 30.1f, 31f, 40f, float.NaN, float.PositiveInfinity})
            Check(!PowerCalibrationRule.Matches(70f,a), "Off current rejected");
        Check(!PowerCalibrationRule.Matches(0f,0f), "Unpowered readings rejected");
        Console.WriteLine("PASS: " + checks + " power calibration checks; unique reachable solution, exact readings, no tolerance.");
    }
}
