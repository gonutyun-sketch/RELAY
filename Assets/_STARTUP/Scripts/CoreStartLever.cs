using UnityEngine;

namespace Startup
{
    [DisallowMultipleComponent]
    public sealed class CoreStartLever : MachineSwitch
    {
        private CoreModule coreSource;

        internal CoreModule CoreSource => coreSource;

        public override bool CanInteract =>
            coreSource != null &&
            !coreSource.IsComplete &&
            (IsOn || coreSource.CanStart);

        public override string Prompt =>
            coreSource != null && coreSource.IsComplete
                ? "Startup complete"
                : IsOn ? "Stop startup" : "Start core";

        internal void BindCoreSource(CoreModule source)
        {
            coreSource = source;
        }

        public override void Interact()
        {
            if (!CanInteract)
                return;

            base.Interact();
        }
    }
}