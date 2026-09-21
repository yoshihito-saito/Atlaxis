"""Translate catalog physical sites to NeuroCarto's hardware routing topology."""

import re
import json
from copy import deepcopy
from collections import deque
from dataclasses import asdict

import numpy as np

from .model import ChannelMap


PART_CODES = {"NP1000": 0, "NP2003": 2003, "NP2013": 2013}
CATEGORIES = ("Full", "Half", "Quarter", "Low", "Excluded")


def is_neuropixels(geometry):
    return geometry.metadata.get("part_number") in PART_CODES


def active_site_ids(geometry, channel_map):
    """Ordinary probes use every contact; only NP sites require active routing.

    Activity does not assign a hardware channel number to an unmapped contact.
    """
    if not is_neuropixels(geometry):
        return {contact.contact_id for contact in geometry.contacts}
    return {site for site, channel in channel_map.contact_to_channel.items()
            if channel not in channel_map.skipped}


def site_topology(geometry):
    """Validate catalog layout before treating site indices as electrode IDs.

    NP1 is staggered physically but still has two logical columns per row.
    NeuroCarto's regular e2p drawing coordinates must not replace this geometry.
    """
    code = PART_CODES.get(geometry.metadata.get("part_number"))
    if code is None:
        raise ValueError("Channel selection supports catalog NP1000, NP2003 and NP2013.")
    shanks, count, pitch = (4 if code == 2013 else 1), (960 if code == 0 else 1280), (20 if code == 0 else 15)
    topology = {}
    for contact in geometry.contacts:
        match = re.fullmatch(r"s(\d+)_front_(\d+)", contact.contact_id)
        if match is None:
            raise ValueError("Neuropixels routing requires the catalog site IDs and geometry.")
        shank, electrode = map(int, match.groups())
        row, column = divmod(electrode, 2)
        x = ((11, 43, 27, 59)[electrode % 4] if code == 0 else (27, 59)[column]) - 35 + 250 * shank
        if (shank != contact.shank_id or not 0 <= shank < shanks or not 0 <= electrode < count
                or not np.allclose((contact.x_um, contact.y_um, contact.z_um),
                                   (x, 200 + pitch * row, -12), atol=1e-6, rtol=0)):
            raise ValueError("Geometry differs from the supported Neuropixels catalog topology.")
        topology[contact.contact_id] = (shank, column, row)
    if len(topology) != shanks * count or len(set(topology.values())) != shanks * count:
        raise ValueError("The complete physical Neuropixels site geometry is required.")
    return code, topology


def _from_neurocarto(geometry, routed, blueprint, source=None):
    code, topology = site_topology(geometry)
    if routed.probe_code != code:
        raise ValueError(f"Expected IMRO type {code}, received {routed.probe_code}.")
    inverse = {value: key for key, value in topology.items()}
    assignments, skipped = {}, []
    for channel, electrode in enumerate(routed.channels):
        if electrode is None:
            continue
        site = inverse.get((electrode.shank, electrode.column, electrode.row))
        if site is None:
            raise ValueError("IMRO contains a site outside this probe's physical geometry.")
        assignments[site] = channel
        if not electrode.in_used:
            skipped.append(channel)
    result = ChannelMap(assignments, 384, [list(range(384))] if skipped else [], skipped,
                        blueprint=dict(blueprint), source_imro=source)
    result.validate(geometry)
    return result


def automatic_map(geometry, blueprint, eligible_sites, *, current_map=None, candidate_sites=None):
    """Select a new ROI while optionally locking all existing active channels.

    Density categories apply to new candidates. Locked sites take precedence in
    overlapping ROIs, even if the new density would otherwise remove them.
    """
    from neurocarto.probe_npx.desp import NpxProbeDesp

    code, topology = site_topology(geometry)
    inverse = {value: key for key, value in topology.items()}
    descriptor = NpxProbeDesp()
    channel_map = descriptor.new_channelmap(code)
    locked = active_site_ids(geometry, current_map) if current_map is not None else set()
    previous = _selection_routing(geometry, current_map)[0] if current_map is not None else None
    candidates = set(eligible_sites) if candidate_sites is None else set(candidate_sites) & set(eligible_sites)
    electrodes = descriptor.all_electrodes(channel_map)
    categories = dict(zip(CATEGORIES, (descriptor.CATE_FULL, descriptor.CATE_HALF,
        descriptor.CATE_QUARTER, descriptor.CATE_LOW, descriptor.CATE_EXCLUDED)))
    for electrode in electrodes:
        site = inverse[electrode.electrode]
        category = blueprint.get(site, "Low") if site in candidates else "Excluded"
        electrode.category = descriptor.CATE_SET if site in locked else categories[category]
    routed = descriptor.select_electrodes(channel_map, electrodes, selector="default")
    if previous is not None:
        routed.reference = previous.reference
        for site in locked:
            channel = current_map.contact_to_channel[site]
            electrode = routed.channels[channel]
            if electrode is None or (electrode.shank, electrode.column, electrode.row) != topology[site]:
                raise ValueError("Channel selection attempted to alter an existing active channel.")
            electrode.copy(previous.channels[channel])
    result = _from_neurocarto(geometry, routed, blueprint,
                            routed.to_imro() if len(routed) == 384 else None)
    if any(site not in candidates or blueprint.get(site) == "Excluded"
           for site in result.contact_to_channel if site not in locked):
        raise ValueError("NeuroCarto returned a site excluded by the current target selection.")
    # Retain reference/gain settings through partial selections and ROI removal.
    result.source_imro = _complete_routing(routed, topology)
    return result


def activate_roi(geometry, mapping, roi_id, eligible_sites):
    mapping.validate(geometry)
    roi = next(roi for roi in mapping.rois if roi.id == roi_id)
    if not roi.registered or roi.assigned_sites:
        raise ValueError("Register an unassigned ROI before activating its channels.")
    locked = active_site_ids(geometry, mapping)
    blueprint = dict(mapping.blueprint)
    for site in set(roi.sites) - locked:
        blueprint[site] = roi.density
    result = automatic_map(geometry, blueprint, eligible_sites,
                           current_map=mapping, candidate_sites=roi.sites)
    result.rois = deepcopy(mapping.rois)
    selected = next(row for row in result.rois if row.id == roi_id)
    selected.assigned_sites = sorted(active_site_ids(geometry, result) - locked)
    result.validate(geometry)
    return result


def remove_roi(geometry, mapping, roi_id):
    """Release only this ROI's newly assigned sites, never other ROI/imported sites."""
    result = deepcopy(mapping)
    roi = next(roi for roi in result.rois if roi.id == roi_id)
    for site in roi.assigned_sites:
        result.contact_to_channel.pop(site, None)
    result.rois = [row for row in result.rois if row.id != roi_id]
    retained = set(result.contact_to_channel) | {site for row in result.rois for site in row.sites}
    for site in set(roi.sites) - retained:
        result.blueprint.pop(site, None)
    result.pending_sites = [site for site in result.pending_sites if site in retained]
    result.validate(geometry)
    return result


def activate_rois_balanced(geometry, mapping, eligible_sites):
    """Share free channels fairly across new ROIs, locking existing assignments.

    NeuroCarto supplies each ROI's density/routing candidates. Round-robin
    augmenting paths maximize the minimum new ROI count within those candidates;
    a saturated ROI yields remaining capacity to the others. Each channel has
    one owner even for overlapping ranges. Imported/previous active sites stay.
    """
    mapping.validate(geometry)
    rois = [roi for roi in mapping.rois if roi.registered and not roi.assigned_sites]
    if not rois:
        raise ValueError("Draw and register an unassigned ROI first.")
    locked = active_site_ids(geometry, mapping)
    candidates, orders = [], []
    contacts = {c.contact_id: c for c in geometry.contacts}
    blueprint = dict(mapping.blueprint)
    for roi in rois:
        local_blueprint = dict(mapping.blueprint)
        for site in set(roi.sites) - locked:
            local_blueprint[site] = roi.density
            blueprint[site] = roi.density
        selected = automatic_map(geometry, local_blueprint, eligible_sites,
                                 current_map=mapping, candidate_sites=roi.sites)
        by_channel = {channel: site for site, channel in selected.contact_to_channel.items()
                      if site not in locked}
        candidates.append(by_channel)
        # Spread partial quotas over the ROI's candidate depth range, rather
        # than taking a prefix at one end. No extra sites bypass density selection.
        channels = sorted(by_channel, key=lambda ch: (contacts[by_channel[ch]].y_um,
                                                      contacts[by_channel[ch]].x_um))
        intervals, order = deque([(0, len(channels))]), []
        while intervals:
            low, high = intervals.popleft()
            if low < high:
                mid = (low + high) // 2
                order.append(channels[mid])
                intervals.extend(((low, mid), (mid + 1, high)))
        orders.append(order)

    owners = {}

    def augment(index, seen_rois, seen_channels):
        if index in seen_rois:
            return False
        seen_rois.add(index)
        for channel in orders[index]:
            if channel in seen_channels or owners.get(channel) == index:
                continue
            seen_channels.add(channel)
            owner = owners.get(channel)
            if owner is None or augment(owner, seen_rois, seen_channels):
                owners[channel] = index
                return True
        return False

    counts = [0] * len(rois)
    while True:
        changed = False
        for index in sorted(range(len(rois)), key=lambda i: (counts[i], i)):
            if augment(index, set(), set()):
                counts[index] += 1
                changed = True
        if not changed:
            break

    # Reconstruct only active selections, preserving imported reference/gains.
    baseline = deepcopy(mapping)
    baseline.contact_to_channel = {site: mapping.contact_to_channel[site] for site in locked}
    baseline.skipped = []
    routed, topology = _selection_routing(geometry, baseline)
    assigned = {roi.id: [] for roi in rois}
    for channel, index in owners.items():
        site = candidates[index][channel]
        routed.add_electrode(topology[site])
        assigned[rois[index].id].append(site)
        blueprint[site] = rois[index].density
    result = _from_neurocarto(geometry, routed, blueprint)
    result.rois = deepcopy(mapping.rois)
    for roi in result.rois:
        if roi.id in assigned:
            roi.assigned_sites = sorted(assigned[roi.id])
    if any(result.contact_to_channel.get(site) != mapping.contact_to_channel[site] for site in locked):
        raise ValueError("Balanced selection attempted to alter an existing active channel.")
    result.source_imro = _complete_routing(routed, topology)
    result.validate(geometry)
    return result


def import_imro(geometry, source, blueprint):
    """Validate explicit channel numbers as well as NeuroCarto's parsed routing.

    NeuroCarto reconstructs channel order from electrodes, so malformed duplicate
    or inconsistent channel fields must be rejected before accepting the map.
    """
    from neurocarto.probe_npx.io import parse_imro

    code, _ = site_topology(geometry)
    compact = source.strip()
    blocks = re.findall(r"\(([^()]*)\)", compact)
    if "".join(f"({block})" for block in blocks) != compact or len(blocks) != 385:
        raise ValueError("IMRO must contain a header and exactly 384 channel entries.")
    if tuple(map(int, blocks[0].split(","))) != (code, 384):
        raise ValueError(f"This probe requires IMRO type {code} with 384 channels.")
    entries = [tuple(map(int, block.split())) for block in blocks[1:]]
    if sorted(entry[0] for entry in entries) != list(range(384)):
        raise ValueError("IMRO channel IDs must be unique and cover 0–383.")
    routed = parse_imro(compact)
    canonical = routed.to_imro()
    expected = {int(block.split()[0]): tuple(map(int, block.split()))
                for block in re.findall(r"\(([^()]*)\)", canonical)[1:]}
    if any(expected.get(entry[0]) != entry for entry in entries):
        raise ValueError("IMRO contains inconsistent channel, bank, reference or gain fields.")
    return _from_neurocarto(geometry, routed, blueprint, canonical)


def export_imro(geometry, mapping):
    if len(mapping.contact_to_channel) != 384 or not mapping.source_imro:
        raise ValueError("IMRO export requires a complete 384-channel generated or imported map.")
    restored = import_imro(geometry, mapping.source_imro, mapping.blueprint)
    if restored.contact_to_channel != mapping.contact_to_channel or restored.skipped != mapping.skipped:
        raise ValueError("Stored IMRO no longer matches the current channel map. Generate again.")
    return mapping.source_imro + "\n"


def _selection_routing(geometry, mapping):
    """Reconstruct the exact selected routing, rejecting invented channel IDs."""
    from neurocarto.probe_npx.npx import ChannelMap as NpxChannelMap, e2cb
    from neurocarto.probe_npx.io import parse_imro

    mapping.validate(geometry)
    code, topology = site_topology(geometry)
    if mapping.n_channels != 384:
        raise ValueError("Neuropixels channel maps must address 384 hardware channels.")
    if mapping.source_imro is not None:
        stored = import_imro(geometry, mapping.source_imro, {})
        if any(stored.contact_to_channel.get(site) != channel
               for site, channel in mapping.contact_to_channel.items()):
            raise ValueError("Stored IMRO does not preserve the selected site/channel assignments.")
        routed = parse_imro(mapping.source_imro.strip())
        for site in set(stored.contact_to_channel) - set(mapping.contact_to_channel):
            routed.del_electrode(topology[site])
        return routed, topology
    routed = NpxChannelMap(code)
    for site, channel in mapping.contact_to_channel.items():
        coordinate = topology[site]
        if int(e2cb(routed.probe_type, coordinate)[0]) != channel:
            raise ValueError(f"Site {site} does not route to hardware channel {channel}.")
        routed.add_electrode(coordinate)
    return routed, topology


def export_acquisition_imro(geometry, mapping):
    """Complete unassigned acquisition slots without changing target selection.

    IMRO has no per-channel target-selection flag. The caller must also export
    the original selection and disclose that the added sites will be recorded.
    Missing slots use the first available site in shank / row / column order.
    """
    routed, topology = _selection_routing(geometry, mapping)
    return _complete_routing(routed, topology) + "\n"


def _complete_routing(routed, topology):
    from neurocarto.probe_npx.npx import e2cb

    for coordinate in sorted(topology.values(), key=lambda value: (value[0], value[2], value[1])):
        channel = int(e2cb(routed.probe_type, coordinate)[0])
        if routed.channels[channel] is None:
            routed.add_electrode(coordinate)
        if len(routed) == 384:
            break
    if len(routed) != 384:
        raise ValueError("Unable to complete the acquisition map without changing selected channels.")
    return routed.to_imro()


def export_selection(geometry, mapping, *, acquisition_imro=None):
    """Lossless target selection, including partial maps and density categories."""
    _selection_routing(geometry, mapping)
    payload = {"format": "atlaxis-neuropixels-selection", "version": 1,
               "part_number": geometry.metadata["part_number"],
               "selected_channels": sorted(mapping.contact_to_channel[site]
                   for site in active_site_ids(geometry, mapping)),
               "channel_map": asdict(mapping)}
    if acquisition_imro is not None:
        payload["acquisition_imro"] = acquisition_imro.strip()
    return json.dumps(payload, indent=2, allow_nan=False) + "\n"


def import_selection(geometry, source):
    payload = json.loads(source)
    if (payload.get("format") != "atlaxis-neuropixels-selection" or payload.get("version") != 1
            or payload.get("part_number") != geometry.metadata.get("part_number")):
        raise ValueError("Selection file does not match this Neuropixels probe type.")
    mapping = ChannelMap(**payload["channel_map"])
    _selection_routing(geometry, mapping)
    selected = sorted(mapping.contact_to_channel[site] for site in active_site_ids(geometry, mapping))
    if payload.get("selected_channels") != selected:
        raise ValueError("Selection file channel list disagrees with its site assignments.")
    if payload.get("acquisition_imro") is not None:
        acquisition = import_imro(geometry, payload["acquisition_imro"], {})
        if any(acquisition.contact_to_channel.get(site) != channel
               for site, channel in mapping.contact_to_channel.items()):
            raise ValueError("Acquisition IMRO disagrees with the saved selection.")
    return mapping
