using UnityEngine;
using UnityEngine.UI;

namespace Startup
{
    // A local backdrop for the ending buttons. Keep Image on this object.
    // It fades to transparent at the top/right instead of covering the forest.
    [DisallowMultipleComponent]
    [RequireComponent(typeof(Image))]
    [AddComponentMenu("RELAY/Ending Shade")]
    public sealed class RelayEndingShade : BaseMeshEffect
    {
        public override void ModifyMesh(VertexHelper mesh)
        {
            if (!IsActive()) return;

            Rect rect = graphic.rectTransform.rect;
            mesh.Clear();
            const int columns = 24;
            const int rows = 16;

            for (int y = 0; y <= rows; y++)
            {
                float v = (float)y / rows;
                float vertical = 1f - Mathf.SmoothStep(0f, 1f,
                    Mathf.InverseLerp(0.15f, 1f, v));
                for (int x = 0; x <= columns; x++)
                {
                    float u = (float)x / columns;
                    float horizontal = 1f - Mathf.SmoothStep(0f, 1f,
                        Mathf.InverseLerp(0.1f, 1f, u));
                    Color color = new Color(0.025f, 0.035f, 0.043f,
                        0.90f * horizontal * vertical * graphic.color.a);
                    mesh.AddVert(new Vector3(
                        Mathf.Lerp(rect.xMin, rect.xMax, u),
                        Mathf.Lerp(rect.yMin, rect.yMax, v), 0f),
                        color, Vector2.zero);
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
