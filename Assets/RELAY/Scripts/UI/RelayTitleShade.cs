using UnityEngine;
using UnityEngine.UI;

namespace Startup
{
    // This is an Image mesh effect, NOT another Graphic component.
    // Keep the Image on the same object. No texture or shader asset is needed.
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Image))]
    [AddComponentMenu("RELAY/Title Shade")]
    public sealed class RelayTitleShade : BaseMeshEffect
    {
        public override void ModifyMesh(VertexHelper mesh)
        {
            if (!IsActive()) return;
            mesh.Clear();
            Rect r = graphic.rectTransform.rect;
            const int columns = 12;
            const int rows = 8;
            for (int y = 0; y <= rows; y++)
            {
                float v = (float)y / rows;
                for (int x = 0; x <= columns; x++)
                {
                    float u = (float)x / columns;
                    float side = Mathf.SmoothStep(0f, 1f, u);
                    float edge = Mathf.Pow(Mathf.Abs(v * 2f - 1f), 2f) * 0.16f;
                    float opacity = Mathf.Min(0.995f, Mathf.Lerp(0.96f, 0.35f, side) + edge);
                    Color ink = new Color(0.025f, 0.035f, 0.043f, opacity * graphic.color.a);
                    mesh.AddVert(new Vector3(Mathf.Lerp(r.xMin, r.xMax, u),
                        Mathf.Lerp(r.yMin, r.yMax, v), 0f), ink, Vector2.zero);
                }
            }
            for (int y = 0; y < rows; y++)
            {
                for (int x = 0; x < columns; x++)
                {
                    int a = y * (columns + 1) + x;
                    int b = a + columns + 1;
                    mesh.AddTriangle(a, b, b + 1);
                    mesh.AddTriangle(b + 1, a + 1, a);
                }
            }
        }
    }
}
