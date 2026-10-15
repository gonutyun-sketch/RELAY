using System;

namespace Startup
{
    // Pure state: no scene creation, UI generation or Unity dependency.
    public sealed class TerminalRecoveryProgress
    {
        private double elapsed;
        private double heldAtFull;
        public int CompletedRecords { get; private set; }
        public bool IsTransferring { get; private set; }
        public bool IsComplete => CompletedRecords == SecuritySequenceRule.PuzzleCount;
        public float Fill { get; private set; }

        public bool Submit(string input)
        {
            if (IsComplete || IsTransferring ||
                !SecuritySequenceRule.IsCorrect(CompletedRecords, input)) return false;
            elapsed = 0d;
            heldAtFull = 0d;
            Fill = 0f;
            IsTransferring = true;
            return true;
        }

        // Returns true once per fully transferred record, after holding 100% on screen.
        public bool Advance(float deltaTime, float transferSeconds, float holdSeconds)
        {
            if (!IsTransferring || float.IsNaN(deltaTime) || float.IsInfinity(deltaTime) || deltaTime <= 0f)
                return false;
            double transfer = Math.Max(0.1d, transferSeconds);
            double hold = Math.Max(0.1d, holdSeconds);
            if (Fill < 1f)
            {
                elapsed += deltaTime;
                Fill = (float)Math.Min(1d, elapsed / transfer);
                // Always give the 100% state a separate visible hold, even after a slow frame.
                return false;
            }
            heldAtFull += deltaTime;
            if (heldAtFull < hold) return false;
            CompletedRecords++;
            IsTransferring = false;
            return true;
        }

        // Esc or focus loss cancels only the unfinished record; it never authorizes a door.
        public void CancelPending()
        {
            if (IsComplete) return;
            IsTransferring = false;
            elapsed = 0d;
            heldAtFull = 0d;
            Fill = 0f;
        }

        public void ResetForPowerLoss()
        {
            CompletedRecords = 0;
            IsTransferring = false;
            elapsed = 0d;
            heldAtFull = 0d;
            Fill = 0f;
        }
    }
}
