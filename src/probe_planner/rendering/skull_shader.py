"""Display-only craniotomies in stereotaxic AP/ML millimeters."""

import numpy as np
import pyvista as pv
from vtkmodules.vtkCommonDataModel import vtkDataObject
from vtkmodules.vtkRenderingOpenGL2 import vtkOpenGLTexture, vtkTextureObject


_FRAGMENT = """
in vec2 skullAPMLVSOutput;

vec3 skullRecord(int index)
{
    int width = textureSize(skullOpenings, 0).x;
    return texelFetch(skullOpenings, ivec2(index % width, index / width), 0).rgb;
}

bool skullOpeningContains(vec2 point)
{
    int cursor = 0;
    for (int opening = 0; opening < skullOpeningCount; ++opening)
    {
        vec3 header = skullRecord(cursor);
        int kind = int(header.x);
        int count = int(header.y);
        vec2 low = skullRecord(cursor + 1).xy;
        vec2 high = skullRecord(cursor + 2).xy;
        if (all(greaterThanEqual(point, low)) && all(lessThanEqual(point, high)))
        {
            if (kind == 0) return true;
            if (kind == 1)
            {
                vec3 circle = skullRecord(cursor + 3);
                vec2 delta = point - circle.xy;
                if (dot(delta, delta) <= circle.z * circle.z) return true;
            }
            else if (kind == 2)
            {
                bool inside = false;
                vec2 a = skullRecord(cursor + 3 + count - 1).xy;
                for (int vertex = 0; vertex < count; ++vertex)
                {
                    vec2 b = skullRecord(cursor + 3 + vertex).xy;
                    vec2 edge = b - a;
                    vec2 offset = point - a;
                    float crossProduct = edge.x * offset.y - edge.y * offset.x;
                    if (crossProduct == 0.0 && dot(point - a, point - b) <= 0.0)
                        return true;
                    // Half-open crossings count shared vertices once. Horizontal
                    // edges never enter this branch, so the divisor is nonzero.
                    if ((a.y > point.y) != (b.y > point.y))
                    {
                        float crossing = a.x + (point.y - a.y) * edge.x / edge.y;
                        if (point.x < crossing) inside = !inside;
                    }
                    a = b;
                }
                if (inside) return true;
            }
        }
        cursor += 3 + count;
    }
    return false;
}
"""


class SkullCutoutShader:
    """Keep one shader/actor; upload only ROI records when geometry changes.

    The RGB float texture contains a header (kind, payload length, unused),
    two AP/ML bounding corners, and then either a circle (AP, ML, radius) or
    polygon vertices (AP, ML, unused). It is data, not a rasterized ROI mask.
    """

    def __init__(self, actor, render_window):
        self.render_window = render_window
        self.key = None
        self.texture = vtkOpenGLTexture()
        self.texture.SetColorModeToDirectScalars()
        self.texture.InterpolateOff()
        self.texture.MipmapOff()
        self.texture.RepeatOff()
        actor.GetProperty().SetTexture("skullOpenings", self.texture)
        actor.GetMapper().MapDataArrayToVertexAttribute(
            "skullAPML", "skull_ap_ml", vtkDataObject.FIELD_ASSOCIATION_POINTS, -1)
        shader = actor.GetShaderProperty()
        self.uniforms = shader.GetFragmentCustomUniforms()
        self.uniforms.SetUniformi("skullOpeningCount", 0)
        shader.AddVertexShaderReplacement("//VTK::PositionVC::Dec", True,
            "//VTK::PositionVC::Dec\nin vec2 skullAPML;\nout vec2 skullAPMLVSOutput;", False)
        shader.AddVertexShaderReplacement("//VTK::PositionVC::Impl", True,
            "skullAPMLVSOutput = skullAPML;\n//VTK::PositionVC::Impl", False)
        shader.AddFragmentShaderReplacement("//VTK::Clip::Dec", True,
            "//VTK::Clip::Dec\n" + _FRAGMENT, False)
        # Discard before depth-peeling's early returns, including its depth pass.
        shader.AddFragmentShaderReplacement("//VTK::DepthPeeling::PreColor", True,
            "if (skullOpeningContains(skullAPMLVSOutput)) discard;\n"
            "//VTK::DepthPeeling::PreColor", False)

    def update(self, openings):
        key = tuple((opening.shape, tuple(tuple(p) for p in opening.points_mm))
                    for opening in openings)
        if key == self.key:
            return False
        records = []
        for opening in openings:
            polygon = opening.polygon  # Retain the existing shape validation.
            payload = []
            if opening.shape == "Rectangle":
                kind = 0
                low, high = polygon.min(axis=0), polygon.max(axis=0)
            elif opening.shape == "Circle":
                kind = 1
                center, edge = np.asarray(opening.points_mm, dtype=float)
                radius = np.linalg.norm(edge - center)
                low, high = center - radius, center + radius
                payload.append([*center, radius])
            else:
                kind = 2
                low, high = polygon.min(axis=0), polygon.max(axis=0)
                payload = [[*point, 0] for point in polygon]
            records.extend(([kind, len(payload), 0], [*low, 0], [*high, 0], *payload))

        # VTK resamples oversized textures. Reject instead: resampling would
        # corrupt shape records. Query the active window, not a fixed GPU limit.
        self.render_window.MakeCurrent()
        maximum = vtkTextureObject.GetMaximumTextureSize(self.render_window)
        if maximum < 2:
            raise RuntimeError("The renderer cannot allocate the skull opening texture.")
        width = min(256, maximum)
        height = max(2, (len(records) + width - 1) // width)
        if height > maximum:
            raise ValueError("Too many opening vertices for this GPU's texture size.")
        values = np.zeros((width * height, 3), dtype=np.float32)
        if records:
            values[:len(records)] = records
        image = pv.ImageData(dimensions=(width, height, 1))
        image.point_data.set_scalars(values, "opening_data", deep_copy=True)
        self.texture.SetInputData(image)
        self.uniforms.SetUniformi("skullOpeningCount", len(openings))
        self.key = key
        return True
