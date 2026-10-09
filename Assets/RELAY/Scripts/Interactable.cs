using UnityEngine;

namespace Startup
{
    public abstract class Interactable : MonoBehaviour
    {
        [SerializeField] private string displayName = "CONTROL";

        public string DisplayName => displayName;
        public abstract string Prompt { get; }
        public virtual bool CanInteract => true;
        public virtual bool CanAdjust => false;

        public abstract void Interact();

        public virtual bool TryInteract()
        {
            if (!CanInteract)
                return false;

            Interact();
            return true;
        }

        public virtual void Adjust(int direction) { }
    }
}