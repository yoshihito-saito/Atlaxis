import numpy as np
import pyvista as pv
from vtkmodules.vtkRenderingCore import vtkRenderer
from vtkmodules.vtkRenderingOpenGL2 import vtkOpenGLPolyDataMapper

from probe_planner.atlas.coordinates import probe_to_stereotaxic_matrix
from probe_planner.probes.neuropixels import active_site_ids
from probe_planner.rendering.regions import default_hidden_regions, label_surface
from probe_planner.rendering.skull_shader import SkullCutoutShader
from probe_planner.rendering.skull_walls import craniotomy_walls
from probe_planner.implant.drive import drive_surfaces


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
        suffix = f"-shell-v3-without-{ids}-{annotation_stat.st_size}-{annotation_stat.st_mtime_ns}"
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
        self.drive_actors = {}
        self.drive_signatures = {}
        self.region_actor = None
        self.brain_outline_actor = None
        self.skull_actor = None
        self.skull_landmark_actors = []
        self.skull_mesh = None
        self.skull_cutouts = None
        self.skull_wall_actor = None
        self.skull_wall_key = None
        self.skull_wall_incomplete = 0
        self.region_mapper = None
        self.region_blocks = {}
        self.region_opacity = 0.25
        self.signature = None
        self.atlas_display_matrix = np.eye(4)
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
        self.brain_outline_actor.user_matrix = self.atlas_display_matrix

    def set_atlas_frame(self, frame):
        self.atlas_display_matrix = frame.atlas_to_display_matrix if frame else np.eye(4)
        for actor in (self.brain_outline_actor, self.region_actor):
            if actor is not None:
                actor.user_matrix = self.atlas_display_matrix

    @staticmethod
    def probe_display_matrix(probe, frame):
        matrix = probe_to_stereotaxic_matrix(probe.geometry, probe.pose)
        return frame.stereo_to_display_matrix @ matrix if frame else matrix

    def set_skull(self, mesh_mm, frame, *, visible=True, opacity=1.0, openings=(), landmarks=None):
        if mesh_mm is None or not mesh_mm.n_cells or frame is None:
            if self.skull_wall_actor is not None:
                self.plotter.remove_actor(self.skull_wall_actor, render=False)
            self.skull_wall_actor = self.skull_wall_key = None
            self.skull_wall_incomplete = 0
            for actor in self.skull_landmark_actors:
                self.plotter.remove_actor(actor, render=False)
            self.skull_landmark_actors = []
            if self.skull_actor is not None:
                self.plotter.remove_actor(self.skull_actor, render=False)
                self.skull_actor = self.skull_mesh = None
                self.skull_cutouts = None
                self.plotter.render()
            return
        changed = False
        if mesh_mm is not self.skull_mesh or self.skull_actor is None:
            mesh = mesh_mm.copy()
            mesh.clear_data()
            mesh = mesh.compute_normals(cell_normals=False, point_normals=True,
                                        split_vertices=False, consistent_normals=True)
            # A dedicated attribute keeps ROI coordinates independent of VTK's
            # automatic VBO normalization and the actor's atlas transform.
            mesh.point_data["skull_ap_ml"] = np.asarray(mesh.points[:, :2], dtype=np.float32)
            mesh.points *= 1000  # Stereo mm -> atlas physical µm, exactly once.
            # PyVista's default DataSetMapper does not expose the custom vertex
            # attributes required by the skull cutout shader.
            mapper = vtkOpenGLPolyDataMapper()
            mapper.SetInputData(mesh)
            mapper.ScalarVisibilityOff()
            actor = pv.Actor(mapper=mapper)
            actor.prop.color = "#ded6be"
            actor.prop.opacity = opacity
            actor.prop.interpolation = "phong"
            actor.prop.ambient = 0.3
            actor.prop.diffuse = 0.7
            actor.prop.show_edges = False
            cutouts = SkullCutoutShader(actor, self.plotter.render_window)
            cutouts.update(openings)
            if self.skull_actor is not None:
                self.plotter.remove_actor(self.skull_actor, render=False)
            self.plotter.add_actor(actor, pickable=False, reset_camera=False, render=False)
            self.skull_actor = actor
            self.skull_cutouts = cutouts
            self.skull_mesh = mesh_mm
            for marker in self.skull_landmark_actors:
                self.plotter.remove_actor(marker, render=False)
            self.skull_landmark_actors = []
            for name, color in (("Bregma", "#ff7865"), ("Lambda", "#68bfff")):
                if name in (landmarks or {}):
                    points = pv.PolyData(np.asarray([landmarks[name]], dtype=float) * 1000)
                    marker = self.plotter.add_mesh(points, color=color, point_size=9,
                        render_points_as_spheres=True, lighting=False, pickable=False,
                        reset_camera=False, render=False)
                    self.skull_landmark_actors.append(marker)
            changed = True
        changed = self.skull_cutouts.update(openings) or changed
        wall_key = (id(mesh_mm), self.skull_cutouts.key)
        if wall_key != self.skull_wall_key:
            walls, incomplete = craniotomy_walls(mesh_mm, openings)
            if self.skull_wall_actor is not None:
                self.plotter.remove_actor(self.skull_wall_actor, render=False)
            self.skull_wall_actor = None
            if walls.n_cells:
                walls.points *= 1000
                self.skull_wall_actor = self.plotter.add_mesh(walls, color="#f1e8cf",
                    opacity=opacity, lighting=True, ambient=.4, diffuse=.6,
                    show_scalar_bar=False, pickable=False, reset_camera=False, render=False)
            self.skull_wall_key = wall_key
            self.skull_wall_incomplete = incomplete
            changed = True
        matrix = frame.stereo_to_display_matrix
        if not np.array_equal(self.skull_actor.user_matrix, matrix):
            self.skull_actor.user_matrix = matrix
            changed = True
        if self.skull_actor.visibility != visible:
            self.skull_actor.visibility = visible
            changed = True
        if self.skull_actor.prop.opacity != opacity:
            self.skull_actor.prop.opacity = opacity
            changed = True
        for marker in self.skull_landmark_actors:
            marker.user_matrix = matrix
            marker.visibility = visible
        if self.skull_wall_actor is not None:
            self.skull_wall_actor.user_matrix = matrix
            self.skull_wall_actor.visibility = visible
            self.skull_wall_actor.prop.opacity = opacity
        if changed:
            self.plotter.render()

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
        self.region_actor.user_matrix = self.atlas_display_matrix
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

    def show_drives(self, probes, frame):
        mounted = {probe.id for probe in probes if probe.drive is not None}
        for probe_id in list(self.drive_actors):
            if probe_id not in mounted:
                for actor in self.drive_actors.pop(probe_id):
                    self.plotter.remove_actor(actor, render=False)
                self.drive_signatures.pop(probe_id, None)
        for probe in probes:
            mount = probe.drive
            if mount is None:
                continue
            key = (id(probe.geometry), mount.model_id, tuple(mount.attachment_um), mount.mount_height_mm,
                   mount.travel_mm, mount.body_height_mm, mount.raised_lower_mm, mount.body_gap_mm,
                   mount.lateral_offset_mm)
            if key != self.drive_signatures.get(probe.id):
                for actor in self.drive_actors.get(probe.id, []):
                    self.plotter.remove_actor(actor, render=False)
                actors = []
                for mesh, role in drive_surfaces(probe.geometry, mount):
                    actors.append(self.plotter.add_mesh(mesh,
                        color="#d5aa42" if role == "screw" else "#c5c9cf",
                        opacity=1.0,
                        show_edges=role == "carriage", edge_color="#353c45",
                        style="wireframe" if role in ("footprint", "reference") else "surface",
                        line_width=2, lighting=role not in ("footprint", "reference"),
                        ambient=.3, diffuse=.7, specular=.5, specular_power=25,
                        smooth_shading=role == "screw", pickable=False, reset_camera=False, render=False))
                self.drive_actors[probe.id] = actors
                self.drive_signatures[probe.id] = key
            matrix = self.probe_display_matrix(probe, frame)
            for actor in self.drive_actors[probe.id]:
                actor.user_matrix = matrix

    def show_probes(self, probes, selected, frame, fit=False):
        self.set_atlas_frame(frame)
        if self.skull_actor is not None and frame is not None:
            matrix = frame.stereo_to_display_matrix
            for actor in (self.skull_actor, self.skull_wall_actor, *self.skull_landmark_actors):
                if actor is None:
                    continue
                if not np.array_equal(actor.user_matrix, matrix):
                    actor.user_matrix = matrix
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
                    actors.append((actor, "base" if body is probe.geometry.mounting_base else "body", body.shank_id))
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
            matrix = self.probe_display_matrix(probe, frame)
            for actor, role, shank in self.probe_actors[probe.id]:
                actor.user_matrix = matrix
                highlighted = probe is selected and shank == probe.selected_shank_id
                if role == "edge":
                    actor.SetVisibility(highlighted)
                    continue
                color = ("#59656f" if role == "base" else
                         ("#9aa9bc" if probe is selected else "#525f72") if role == "body" else
                         "#ff19ef" if role == "active" else "#616977")
                actor.prop.color = color
                actor.prop.opacity = 0.5 if role == "active" else 1.0
        self.show_drives(probes, frame)
        if fit:
            self.plotter.reset_camera()
        self.plotter.render()
