namespace Startup
{
    public static class SecuritySequenceRule
    {
        public const int MaximumDigits = 4;
        public const int PuzzleCount = 2;

        // Keep the original API for existing callers.
        public static bool IsCorrect(string input) => IsCorrect(0, input);

        public static bool IsCorrect(int puzzleIndex, string input)
        {
            if (puzzleIndex < 0 || puzzleIndex >= PuzzleCount ||
                string.IsNullOrEmpty(input) || input.Length > MaximumDigits)
                return false;
            int value = 0;
            foreach (char digit in input)
            {
                if (digit < '0' || digit > '9') return false;
                value = value * 10 + digit - '0';
            }
            // Record 1: differences are 4, 9, 16, 25, 36.
            // Record 2: odd positions n*(n+1), even positions 9*n.
            return value == (puzzleIndex == 0 ? 92 : 36);
        }

        public static string Display(int puzzleIndex)
        {
            if (puzzleIndex == 0)
                return "SECURITY RECORD 01 / 02\n\n" +
                    "01 : 2\n02 : 6\n03 : 15\n04 : 31\n05 : 56\n06 : [ ? ]\n\n" +
                    "RECOVER MISSING VALUE";
            if (puzzleIndex == 1)
                return "SECURITY RECORD 02 / 02\n\n" +
                    "01 : 2\n02 : 9\n03 : 6\n04 : 18\n05 : 12\n06 : 27\n07 : 20\n08 : [ ? ]\n\n" +
                    "RECOVER MISSING VALUE";
            return "";
        }

        public static bool CanAuthorize(bool powered, bool solved) => powered && solved;
    }
}
