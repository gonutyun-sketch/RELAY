using UnityEngine;

namespace Startup
{
    // All controls share the same raycast entry point.
    public abstract class Interactable : MonoBehaviour
    {
        [SerializeField] private string displayName = "CONTROL";
        public string DisplayName => displayName;
        public abstract string Prompt { get; }
        public virtual bool CanInteract => true;
        public virtual bool CanAdjust => false;
        public abstract void Interact();
        public virtual void Adjust(int direction) { }
    }
}
