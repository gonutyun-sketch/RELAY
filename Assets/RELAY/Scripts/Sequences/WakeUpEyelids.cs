using UnityEngine;
using UnityEngine.UI;

namespace Startup
{
    // Add this to a full-stretch UI object created by the user.
    // It draws only a runtime screen overlay; it does not create scene objects.
    [DisallowMultipleComponent]
    [AddComponentMenu("RELAY/Wake Up Eyelids")]
    public sealed class WakeUpEyelids : MaskableGraphic
    {
        [SerializeField, Range(0f, 1f)] private float openAmount = 1f;
        [SerializeField, Range(0f, 0.06f)] private float edgeSoftness = 0.025f;

        private const int Segments = 64;

        public float OpenAmount
        {
            get => openAmount;
            set
            {
                float next = Mathf.Clamp01(value);
                if (Mathf.Approximately(openAmount, next)) return;
                openAmount = next;
                SetVerticesDirty();
            }
        }

        protected override void Awake()
        {
            base.Awake();
            raycastTarget = false;
        }

        protected override void OnPopulateMesh(VertexHelper mesh)
        {
            mesh.Clear();
            Rect r = rectTransform.rect;
            float opening = Mathf.Clamp01(openAmount);
            if (r.width <= 0f || r.height <= 0f || opening >= 1f) return;

            if (opening <= 0f)
            {
                AddBand(mesh, r.xMin, r.xMax,
                    r.yMin, r.yMin, r.yMax, r.yMax, 255, 255);
                return;
            }

            float soft = r.height * Mathf.Clamp(edgeSoftness, 0f, 0.06f);
            float extent = (r.height * 0.5f + soft) / 0.7f;

            for (int i = 0; i < Segments; i++)
            {
                float u0 = (float)i / Segments;
                float u1 = (float)(i + 1) / Segments;
                float x0 = Mathf.Lerp(r.xMin, r.xMax, u0);
                float x1 = Mathf.Lerp(r.xMin, r.xMax, u1);
                float gap0 = Gap(u0, opening, extent);
                float gap1 = Gap(u1, opening, extent);
                float feather0 = Mathf.Min(soft, gap0 * 0.65f);
                float feather1 = Mathf.Min(soft, gap1 * 0.65f);

                float upperOuter0 = Mathf.Min(r.yMax, r.center.y + gap0);
                float upperOuter1 = Mathf.Min(r.yMax, r.center.y + gap1);
                float upperInner0 = Mathf.Min(r.yMax, r.center.y + gap0 - feather0);
                float upperInner1 = Mathf.Min(r.yMax, r.center.y + gap1 - feather1);
                AddBand(mesh, x0, x1, upperOuter0, upperOuter1,
                    r.yMax, r.yMax, 255, 255);
                AddBand(mesh, x0, x1, upperInner0, upperInner1,
                    upperOuter0, upperOuter1, 0, 255);

                float lowerOuter0 = Mathf.Max(r.yMin, r.center.y - gap0);
                float lowerOuter1 = Mathf.Max(r.yMin, r.center.y - gap1);
                float lowerInner0 = Mathf.Max(r.yMin, r.center.y - gap0 + feather0);
                float lowerInner1 = Mathf.Max(r.yMin, r.center.y - gap1 + feather1);
                AddBand(mesh, x0, x1, r.yMin, r.yMin,
                    lowerOuter0, lowerOuter1, 255, 255);
                AddBand(mesh, x0, x1, lowerOuter0, lowerOuter1,
                    lowerInner0, lowerInner1, 255, 0);
            }
        }

        private static float Gap(float u, float opening, float extent)
        {
            float x = u * 2f - 1f;
            return opening * extent * (1f - 0.3f * x * x);
        }

        private static void AddBand(VertexHelper mesh, float x0, float x1,
            float lower0, float lower1, float upper0, float upper1,
            byte lowerAlpha, byte upperAlpha)
        {
            int first = mesh.currentVertCount;
            Color32 lower = new Color32(0, 0, 0, lowerAlpha);
            Color32 upper = new Color32(0, 0, 0, upperAlpha);
            mesh.AddVert(new Vector3(x0, lower0, 0f), lower, Vector2.zero);
            mesh.AddVert(new Vector3(x0, upper0, 0f), upper, Vector2.zero);
            mesh.AddVert(new Vector3(x1, upper1, 0f), upper, Vector2.zero);
            mesh.AddVert(new Vector3(x1, lower1, 0f), lower, Vector2.zero);
            mesh.AddTriangle(first, first + 1, first + 2);
            mesh.AddTriangle(first + 2, first + 3, first);
        }
    }
}
