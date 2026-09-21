"""Offline layouts/profiles for the normal XML configurations in ProbeMaps."""

import json
from math import sqrt
from pathlib import Path
from urllib.parse import quote

from .model import ChannelMap, ProbeBody
from .wiring import headstage_map


LOCK = Path(__file__).resolve().parents[3] / 'third_party' / 'probemaps.lock.json'


def extend_probemaps(entries):
    from .catalog import NEURONEXUS, _body, _probe, _sites

    contacts = _sites(0, 0, [(0, 40 + 20*i) for i in range(32)], 15)
    # Local x=0 is the straight line of site centers. The drawing does not
    # dimension the lateral offset to the tip; the body is schematic.
    outline = [[0, 0, 0], [-10, 40, 0], [-136, 660, 0],
               [-136, 5000, 0], [9, 5000, 0], [9, 40, 0]]
    geometry = _probe('A1x32-Edge-5mm-20-177', 'NeuroNexus', contacts,
                      [ProbeBody(outline, 15, 0)], NEURONEXUS, 41,
                      '32 sites; 20 um pitch; first site 40 um from tip; 620 um span.',
                      site_area_um2=177, provisional=True,
                      geometry_note='15 um thickness variant. Site line defines local x=0; its lateral registration to the tip is undimensioned (unknown error). Body is schematic.')
    entries.append((Path('NeuroNexus') / f'{geometry.name}.json', geometry, ChannelMap(n_channels=32)))

    contacts, bodies = [], []
    for s in range(4):
        xy = [(sqrt(300)/2*(-1)**i, 40+10*i) for i in range(14)]
        xy += [(0, 270+100*s), (0, 370+100*s)]
        contacts += _sites(s, 150*s, xy, 15)
        bodies.append(_body(s, 150*s, 5000, 15, [(40,17.5),(170,30)]))
    geometry = _probe('A4x16-Poly2-lin-5mm-20s-150-160', 'NeuroNexus', contacts, bodies,
                      NEURONEXUS, 92, '14 staggered sites and 2 remote sites per shank; 150 um shank pitch; 17.32 um column separation.',
                      site_area_um2=160, xml_alias='A4x16-Poly2-5mm-20s-lin-160',
                      geometry_note='XML alias matched to the official OA64LP V2 map, page 4, and catalog page 92; the staggered-tip 190 um variant is different.')
    entries.append((Path('NeuroNexus') / f'{geometry.name}.json', geometry, ChannelMap(n_channels=64)))

    lock = json.loads(LOCK.read_text(encoding='utf-8'))
    by_name = {g.name:g for _,g,_ in entries}
    for record in lock['files']:
        if record['status'] != 'mapped':
            continue
        geometry = by_name[record['model']]
        groups = record['groups_dorsal_to_ventral']
        shanks = sorted({c.shank_id for c in geometry.contacts})
        channels = {}
        for shank, group in zip(shanks, groups, strict=True):
            ordered = sorted((c for c in geometry.contacts if c.shank_id == shank),
                             key=lambda c:(-geometry.y_to_base*c.y_um, c.x_um))
            for contact, channel in zip(ordered, group, strict=True):
                channels[contact.contact_id] = channel
        if sorted(channels.values()) != list(range(record['n_channels'])):
            raise ValueError(f'Incomplete ProbeMaps map: {geometry.name}')
        source = f"{lock['repository']}/blob/{lock['revision']}/{quote(record['source_path'])}"
        profile = {'id':'probemaps_normal', 'label':'ProbeMaps normal XML',
                   'n_channels':record['n_channels'], 'contact_to_channel':channels,
                   'source_url':source, 'source_git_blob_sha1':record['git_blob_sha1'],
                   'source_revision':lock['revision'], 'spatial_order_source':lock['spatial_order_source'],
                   'note':'Uses the supplied ProbeMaps normal XML configuration (base-to-tip site order). Select only if your recording uses this XML; confirm Channel ID / Site against the actual probe and connection.'}
        geometry.metadata.setdefault('headstage_profiles', []).append(profile)
        geometry.metadata['connection_label'] = 'Package / headstage'
        geometry.metadata.pop('wiring_unavailable_reason', None)
        headstage_map(geometry, profile['id'])
