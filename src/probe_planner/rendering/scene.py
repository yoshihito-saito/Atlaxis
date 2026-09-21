import numpy as np
import pyvista as pv
from vtkmodules.vtkRenderingCore import vtkRenderer

from probe_planner.atlas.sections import probe_positions
from probe_planner.probes.neuropixels import active_site_ids
from probe_planner.rendering.regions import default_hidden_regions, label_surface


def load_display_mesh(path, progress, *, atlas=None):
    """Prepare/cache a display-only surface off the UI thread; units stay µm."""
    maximum_faces = 50_000
    stat = path.stat()
    cache_dir = path.parent.parent / "probe_planner_cache"
    suffix = ""
    excluded = default_hidden_regions(atlas) if atlas is not None else set()
    if excluded:
        from brainglobe_atlasapi.descriptors import ANNOTATION_FILENAME

        annotation_stat = (atlas.backend.root_dir / ANNOTATION_FILENAME).stat()
        ids = "-".join(map(str, sorted(excluded)))
        suffix = f"-shell-v2-without-{ids}-{annotation_stat.st_size}-{annotation_stat.st_mtime_ns}"
    cache = cache_dir / f"{path.stem}-{stat.st_size}-{stat.st_mtime_ns}-50k-v1{suffix}.vtp"
    if cache.exists():
        progress("Loading cached brain surface…")
        return pv.read(cache)
    progress("Preparing lightweight brain surface (first load only)…")
    mesh = (label_surface(atlas, None, excluded_ids=excluded) if excluded
            else pv.read(path)).triangulate()
    if mesh.n_cells > maximum_faces:
        mesh = mesh.decimate(1.0 - maximum_faces / mesh.n_cells)
    mesh = mesh.compute_normals(cell_normals=False, point_normals=True)
    cache_dir.mkdir(exist_ok=True)
    temporary = cache.with_suffix(".tmp.vtp")
    mesh.save(temporary)
    temporary.replace(cache)
    return mesh


class Scene:
    def __init__(self, plotter):
        self.plotter = plotter
        self.probe_actors = {}
        self.region_actor = None
        self.brain_outline_actor = None
        self.region_mapper = None
        self.region_blocks = {}
        self.region_opacity = 0.25
        self.signature = None
        plotter.set_background("#101216")
        plotter.enable_anti_aliasing("fxaa")
        # Contacts are fixed-pixel position markers, including when their true
        # centers lie inside a schematic body. Share the camera, not its depth.
        self.contact_renderer = vtkRenderer()
        self.contact_renderer.SetLayer(1)
        self.contact_renderer.SetInteractive(False)
        self.contact_renderer.SetActiveCamera(plotter.camera)
        self.contact_renderer.PreserveColorBufferOn()
        self.contact_renderer.PreserveDepthBufferOff()
        window = plotter.render_window
        window.SetNumberOfLayers(max(window.GetNumberOfLayers(), 2))
        window.AddRenderer(self.contact_renderer)

    def set_brain_outline(self, mesh):
        if self.brain_outline_actor is not None:
            self.plotter.remove_actor(self.brain_outline_actor, render=False)
        self.brain_outline_actor = self.plotter.add_mesh(
            mesh, color="white", opacity=0.2, smooth_shading=True, lighting=False,
            show_scalar_bar=False, pickable=False, reset_camera=False, render=False)

    def set_region_meshes(self, meshes, structures):
        if self.region_actor is not None:
            self.plotter.remove_actor(self.region_actor, render=False)
        self.region_actor = self.region_mapper = None
        self.region_blocks = {}
        if not meshes:
            return
        dataset = pv.MultiBlock({str(region_id): mesh for region_id, mesh in meshes.items()})
        self.region_actor, self.region_mapper = self.plotter.add_composite(
            dataset, color="white", opacity=self.region_opacity, show_scalar_bar=False,
            smooth_shading=False, ambient=0.4, diffuse=0.6,
            reset_camera=False, render=False)
        for index, region_id in enumerate(meshes, 1):
            self.region_blocks[region_id] = index
            self.region_mapper.block_attr[index].color = tuple(structures[region_id]["rgb_triplet"])
            self.region_mapper.block_attr[index].visible = True

    def select_regions(self, region_ids):
        for region_id, index in self.region_blocks.items():
            self.region_mapper.block_attr[index].visible = region_id in region_ids

    def set_region_opacity(self, opacity):
        self.region_opacity = opacity
        if self.region_actor is not None:
            self.region_actor.prop.opacity = opacity

    def clear_probe(self):
        for actors in self.probe_actors.values():
            for actor, _, _ in actors:
                self.contact_renderer.RemoveActor(actor)
                self.plotter.remove_actor(actor, render=False)
        self.probe_actors = {}

    def show_probes(self, probes, selected, frame, fit=False):
        signature = tuple((p.id, id(p.geometry), id(p.channel_map)) for p in probes)
        if signature != self.signature:
            geometry_changed = (self.signature is None or
                [key[:2] for key in signature] != [key[:2] for key in self.signature])
            self.clear_probe()
            for probe in probes:
                actors = []
                for body in probe.geometry.display_bodies:
                    count = len(body.outline_um)
                    faces = [count, *range(count - 1, -1, -1), count, *range(count, 2 * count)]
                    for i in range(count):
                        j = (i + 1) % count
                        faces.extend([4, i, j, j + count, i + count])
                    mesh = pv.PolyData(body.vertices, faces).triangulate()
                    actor = self.plotter.add_mesh(mesh, color="#9aa9bc", reset_camera=False, render=False)
                    actors.append((actor, "body", body.shank_id))
                    edge = self.plotter.add_mesh(mesh.extract_feature_edges(), color="#00fff0",
                        line_width=1, lighting=False, reset_camera=False, render=False)
                    actors.append((edge, "edge", body.shank_id))
                active_sites = active_site_ids(probe.geometry, probe.channel_map)
                for shank in sorted({c.shank_id for c in probe.geometry.contacts}):
                    for active in (True, False):
                        mask = [c.shank_id == shank and
                                ((c.contact_id in active_sites) == active)
                                for c in probe.geometry.contacts]
                        if any(mask):
                            actor = self.plotter.add_points(probe.geometry.points[mask], point_size=5 if active else 7,
                                render_points_as_spheres=True, reset_camera=False, render=False)
                            self.contact_renderer.AddActor(actor)
                            # Render once in the contact layer: drawing in both
                            # layers would compound 50% opacity into 75%.
                            self.plotter.renderer.RemoveActor(actor)
                            actors.append((actor, "active" if active else "inactive", shank))
                self.probe_actors[probe.id] = actors
            self.signature = signature
            fit = fit or geometry_changed
        for probe in probes:
            matrix, _ = probe_positions(probe, frame=frame)
            for actor, role, shank in self.probe_actors[probe.id]:
                actor.user_matrix = matrix
                highlighted = probe is selected and shank == probe.selected_shank_id
                if role == "edge":
                    actor.SetVisibility(highlighted)
                    continue
                color = ("#9aa9bc" if probe is selected else "#525f72") if role == "body" else (
                    "#ff19ef" if role == "active" else "#616977")
                actor.prop.color = color
                actor.prop.opacity = 0.5 if role == "active" else 1.0
        if fit:
            self.plotter.reset_camera()
        self.plotter.render()
