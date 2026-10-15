using UnityEngine;
using UnityEngine.UI;

namespace Startup
{
    // Keep the Image: this modifies its mesh and does not add another Graphic.
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Image))]
    [AddComponentMenu("RELAY/Terminal Surface")]
    public sealed class RelayTerminalSurface : BaseMeshEffect
    {
        private float nextNoiseTime;
        private int noiseFrame;

        private void Update()
        {
            if (!IsActive() || Time.unscaledTime < nextNoiseTime) return;
            nextNoiseTime = Time.unscaledTime + 0.12f;
            noiseFrame++;
            graphic.SetVerticesDirty();
        }

        public override void ModifyMesh(VertexHelper mesh)
        {
            if (!IsActive()) return;
            mesh.Clear();
            Rect rect = graphic.rectTransform.rect;
            if (rect.width < 20f || rect.height < 20f) return;
            float alpha = graphic.color.a;
            Rounded(mesh, rect, 20f, new Color(0.17f, 0.22f, 0.19f, alpha));
            Rect screen = new Rect(rect.xMin + 3f, rect.yMin + 3f, rect.width - 6f, rect.height - 6f);
            Rounded(mesh, screen, 18f, new Color(0.018f, 0.036f, 0.027f, alpha));

            // Fine, static scanlines. Text is drawn afterward by child objects.
            for (float y = screen.yMin + 2f; y < screen.yMax - 2f; y += 4f)
            {
                float inset = RoundedInset(screen, y, 18f) + 1f;
                Quad(mesh, screen.xMin + inset, y, screen.width - inset * 2f, 1f,
                    new Color(0f, 0f, 0f, 0.16f * alpha));
            }

            // Small, quiet phosphor variations; no global Random state changes.
            uint state = (uint)(noiseFrame + 1) * 747796405u;
            for (int i = 0; i < 38; i++)
            {
                float x = Mathf.Lerp(screen.xMin + 22f, screen.xMax - 30f, Noise(ref state));
                float y = Mathf.Lerp(screen.yMin + 22f, screen.yMax - 22f, Noise(ref state));
                Quad(mesh, x, y, 2f + Noise(ref state) * 6f, 1f,
                    new Color(0.55f, 0.85f, 0.65f, 0.045f * alpha));
            }
        }

        private static float Noise(ref uint value)
        {
            value = value * 1664525u + 1013904223u;
            return (value & 0xffffu) / 65535f;
        }

        private static float RoundedInset(Rect rect, float y, float radius)
        {
            float distance = Mathf.Min(y - rect.yMin, rect.yMax - y);
            if (distance >= radius) return 0f;
            float dy = radius - Mathf.Max(0f, distance);
            return radius - Mathf.Sqrt(Mathf.Max(0f, radius * radius - dy * dy));
        }

        private static void Rounded(VertexHelper mesh, Rect rect, float radius, Color color)
        {
            radius = Mathf.Min(radius, Mathf.Min(rect.width, rect.height) * 0.5f);
            int first = mesh.currentVertCount;
            mesh.AddVert(rect.center, color, Vector2.zero);
            const int steps = 8;
            for (int corner = 0; corner < 4; corner++)
            {
                Vector2 center = new Vector2(
                    corner == 0 || corner == 3 ? rect.xMax - radius : rect.xMin + radius,
                    corner < 2 ? rect.yMax - radius : rect.yMin + radius);
                for (int step = 0; step <= steps; step++)
                {
                    float angle = (corner * 90f + step * 90f / steps) * Mathf.Deg2Rad;
                    mesh.AddVert(center + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)) * radius,
                        color, Vector2.zero);
                }
            }
            int count = 4 * (steps + 1);
            for (int i = 0; i < count; i++)
                mesh.AddTriangle(first, first + 1 + (i + 1) % count, first + 1 + i);
        }

        private static void Quad(VertexHelper mesh, float x, float y, float width, float height, Color color)
        {
            int first = mesh.currentVertCount;
            mesh.AddVert(new Vector3(x, y), color, Vector2.zero);
            mesh.AddVert(new Vector3(x, y + height), color, Vector2.zero);
            mesh.AddVert(new Vector3(x + width, y + height), color, Vector2.zero);
            mesh.AddVert(new Vector3(x + width, y), color, Vector2.zero);
            mesh.AddTriangle(first, first + 1, first + 2);
            mesh.AddTriangle(first + 2, first + 3, first);
        }
    }
}
