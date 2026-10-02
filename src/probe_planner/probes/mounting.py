"""Dimensional mounting-base envelopes, independent of recording-site geometry."""

import numpy as np


CAMBRIDGE = "https://www.cambridgeneurotech.com/assets/files/Cambridge-NeuroTech-Product-Catalog.pdf"
NP1 = "https://www.neuropixels.org/_files/ugd/328966_9f784121a69f4f56bd314ffdf7f86d2b.pdf"
NP2 = "https://www.neuropixels.org/_files/ugd/328966_2b39661f072d405b8d284c3c73588bc6.pdf"
NEURONEXUS = "https://solutions.neuronexus.com/hubfs/Penetrating_Probe_Catalog_V2.1.pdf"

# Width, height (mm), one-based PDF page. These are diagram-derived estimates,
# not annotated manufacturing dimensions. Each full-array illustration is scaled
# by its shaft-length dimension; tip-detail drawings are not used. See the
# NeuroNexus library README for provenance and limitations.
NEURONEXUS_BASES = {
    "A16x8-5mm-berg-200-160": (3.17, 3.96, 123),
    "A1x32-Edge-5mm-20-177": (1.40, 2.75, 41),
    "A1x64-Edge-6mm-20-177": (1.36, 5.00, 77),
    "A2x32-5mm-100-200-177": (1.36, 4.84, 80),
    "A2x32-5mm-25-200-177": (1.36, 4.78, 79),
    "A2x32-6mm-70-200-177": (1.41, 4.96, 81),
    "A2x32-8mm-35-200-177": (1.37, 4.88, 82),
    "A2x64-Poly4-10mm-20-800-100": (1.67, 4.19, 111),
    "A4x16-3mm-50-200-177": (1.36, 4.70, 88),
    "A4x16-Poly2-lin-5mm-20s-150-160": (1.35, 4.91, 92),
    "A4x16-poly2-5mm-23s-200-177": (1.35, 4.86, 89),
    "A4x16-poly3-5mm-20s-200-160": (1.36, 4.80, 94),
    "A4x32-Poly2-5mm-23s-200-177": (1.64, 3.77, 115),
    "A4x32-Poly2-lin-5mm-20s-150-160": (1.65, 3.57, 116),
    "A4x4-tet-5mm-150-200-121": (1.35, 4.86, 87),
    "A5x12-16-Buz-Lin-5mm-100-200-160-177": (1.09, 3.84, 95),
    "A6x21-poly2-10mm-50-200-160": (1.66, 3.60, 119),
    "A8x16-Edge-5mm-100-200-177": (1.65, 3.45, 122),
    "A8x16-Edge-5mm-30-500-121": (3.72, 4.31, 120),
    "A8x16-Edge-5mm-50-150-177": (1.64, 3.48, 121),
    "A8x8-10mm-200-200-177": (1.52, 4.84, 98),
    "A8x8-10mm-200-200-703": (1.52, 4.84, 98),
    "A8x8-5mm-200-200-177": (1.54, 4.90, 97),
    "A8x8-5mm-200-200-703": (1.54, 4.90, 97),
    "A8x8-Edge-5mm-100-200-177": (1.45, 4.85, 100),
    "A8x8-Edge-5mm-50-150-177": (1.39, 4.98, 99),
    "Buzsaki-5x12": (1.36, 4.87, 102),
    "Buzsaki64": (1.55, 4.99, 101),
    "Buzsaki64L": (1.56, 4.89, 104),
    "Buzsaki64sp": (1.36, 4.80, 105),
    "Buzsaki64spL": (1.40, 4.88, 107),
}


def is_acute_package(geometry):
    """Recognized acute packages; NeuroNexus array names do not imply packaging."""
    if geometry.metadata.get("manufacturer") == "NeuroNexus":
        return geometry.metadata.get("mounting_package_profile") == "neuronexus_a64_smartlink64_acute"
    assembly = geometry.metadata.get("assembly", "-".join(geometry.name.split("-")[:2]))
    return (geometry.metadata.get("manufacturer") == "Cambridge NeuroTech"
            and assembly in {"ASSY-1", "ASSY-37", "ASSY-77", "ASSY-107", "ASSY-407"})


def with_package_base(geometry, mapping):
    """Retain base dimensions while synchronizing NeuroNexus package eligibility."""
    from dataclasses import replace

    if geometry.metadata.get("manufacturer") != "NeuroNexus":
        return geometry
    if geometry.metadata.get("mounting_package_profile") == mapping.headstage_id:
        return geometry
    return replace(geometry, metadata={**geometry.metadata,
                                      "mounting_package_profile": mapping.headstage_id})


def base_specification(geometry):
    """Width/height/thickness in mm; zero is unknown, diagram estimates are labeled."""
    if is_acute_package(geometry):
        return (0., 0., 0.), "Acute probe packages are not modeled."
    manufacturer = geometry.metadata.get("manufacturer")
    if manufacturer == "NeuroNexus":
        dimensions = NEURONEXUS_BASES.get(geometry.name)
        if dimensions is None:
            return (0., 0., .3), "NeuroNexus base width/height unspecified; common planning thickness 0.3 mm."
        width, height, page = dimensions
        return (width, height, .3), (
            f"NeuroNexus {geometry.name}: base envelope estimated from the full-array drawing, "
            f"scaled by the labeled shaft length (PDF p. {page}); not dimensioned CAD. "
            "Common planning thickness 0.3 mm; cable, connector and epoxy overhang excluded. "
            "Physical dimensional error is unknown. " + NEURONEXUS)
    if manufacturer == "Cambridge NeuroTech":
        assembly = geometry.metadata.get("assembly", "-".join(geometry.name.split("-")[:2]))
        dimensions = {"ASSY-350": (2.6, 7.6, .3), "ASSY-236": (2., 7.6, .3),
                      "ASSY-79": (0., 7.6, .3), "ASSY-116": (0., 7.6, .3),
                      "ASSY-156": (0., 7.6, .3)}.get(assembly)
        if dimensions is None:
            return (0., 0., .3), f"{assembly} package width/height unspecified; common planning thickness 0.3 mm."
        note = " Thickness 0.3 mm is a user-approved common planning value." if assembly not in {
            "ASSY-350", "ASSY-79", "ASSY-116", "ASSY-156"} else ""
        return dimensions, f"{assembly} interface chip; Cambridge catalog, PDF pp. 26–27.{note} {CAMBRIDGE}"
    if geometry.name == "Neuropixels-1.0-single-shank" and manufacturer == "Neuropixels":
        return (6.2, 10.7, 1.2), f"NP1 probe base, Si spacer (nominal); metal-cap thickness 1.8 mm. {NP1}"
    if geometry.name in ("Neuropixels-2.0-single-shank", "Neuropixels-2.0-four-shank") and manufacturer == "Neuropixels":
        return (3.5, 14., 1.28), f"NP2 base/SMD, Si spacer (nominal); metal-cap thickness 1.83 mm. {NP2}"
    return (0., 0., 0.), "Mounting package dimensions are not specified for this probe."


def root_bounds(geometry):
    """Locate the modeled shaft/base shoulder without changing shaft geometry."""
    outlines = [np.asarray(body.outline_um, dtype=float) for body in geometry.shaft_bodies]
    shoulders = []
    for points in outlines:
        following = np.roll(points, -1, axis=0)
        heights = points[:, 1] * geometry.y_to_base
        epsilon = 32 * np.finfo(float).eps * max(1., np.abs(points).max())
        horizontal = ((np.abs(points[:, 1] - following[:, 1]) <= epsilon)
                      & (np.abs(points[:, 0] - following[:, 0]) > epsilon)
                      & (heights < heights.max() - epsilon) & (heights > heights.min() + epsilon))
        shoulders.extend(heights[horizontal])
    bottom = max(shoulders) if shoulders else max((p[:, 1] * geometry.y_to_base).max() for p in outlines)
    vertices = np.vstack([body.vertices for body in geometry.shaft_bodies])
    proximal = vertices[vertices[:, 1] * geometry.y_to_base >= bottom]
    return bottom, (proximal[:, 0].min() + proximal[:, 0].max()) / 2, (proximal[:, 2] * geometry.y_to_base).min()


def make_base(geometry, dimensions_mm):
    """Box envelope centered across shaft roots, flush with their front face.

    Centering and the flush front are explicit planning assumptions; the cited
    dimensions do not establish package-to-electrode registration or taper.
    """
    from .model import ProbeBody

    if is_acute_package(geometry):
        raise ValueError("Microdrive mounting is available for chronic probe packages only.")
    dimensions = np.asarray(dimensions_mm, dtype=float)
    if dimensions.shape != (3,) or not np.isfinite(dimensions).all() or np.any(dimensions <= 0):
        raise ValueError("Enter probe base width, height and thickness before attaching.")
    width, height, thickness = dimensions * 1000
    bottom, center, front = root_bounds(geometry)
    sign = geometry.y_to_base
    z = (front + thickness / 2) * sign
    outline = [[center - width/2, bottom*sign, z], [center + width/2, bottom*sign, z],
               [center + width/2, (bottom+height)*sign, z], [center - width/2, (bottom+height)*sign, z]]
    return ProbeBody(outline, float(thickness))


def base_dimensions(geometry):
    body = geometry.mounting_base
    if body is None:
        return base_specification(geometry)[0]
    points = np.asarray(body.outline_um)
    return (float(np.ptp(points[:, 0])) / 1000, float(np.ptp(points[:, 1])) / 1000,
            body.thickness_um / 1000)
