namespace Startup
{
    public sealed class MachineLever : MachineSwitch
    {
        private PowerModule powerSource;
        internal PowerModule PowerSource => powerSource;

        public override bool CanInteract => IsOn || powerSource == null || powerSource.CanEngage;

        // Hover explains the action, never whether the hidden conditions are correct.
        public override string Prompt => IsOn ? "Release lever" : "Pull lever";

        internal void BindPowerSource(PowerModule source) => powerSource = source;

        public override void Interact()
        {
            if (!CanInteract) return;
            base.Interact();
        }
    }
}
