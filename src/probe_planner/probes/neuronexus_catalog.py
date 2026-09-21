"""Offline NeuroNexus catalog expansion from dimensioned layouts and wiring facts.

Only generation reads third_party/neuronexus_wiring.json. Runtime imports use
self-contained probe JSONs; no PDF parser or network access is required.
"""

import json
from math import sqrt
from pathlib import Path

from .model import ChannelMap, ProbeBody
from .wiring import headstage_map


WIRING = Path(__file__).resolve().parents[3] / 'third_party' / 'neuronexus_wiring.json'


def extend_neuronexus(entries):
    from .catalog import NEURONEXUS, _body, _probe, _sites

    data = json.loads(WIRING.read_text(encoding='utf-8'))
    assignments = {
        'A4x16-poly2-5mm-23s-200-177': ['activus64_p5'],
        'Buzsaki64L': ['h64lp_p12'],
    }

    def add(name, page, shanks, pitch, length, thickness, xy, profile, maps,
            area=177, note='', edge=False):
        contacts, bodies = [], []
        for s in range(shanks):
            local = xy(s) if callable(xy) else xy
            local = sorted(local, key=lambda p: (p[1], p[0]))
            contacts += _sites(s, s * pitch, local, thickness)
            if edge:
                # The contact-bearing edge is straight; the opposite edge tapers.
                first_y, half = profile[0]
                last_y, max_half = profile[-1]
                x = s * pitch
                outline = [[x, 0, 0], [x-half, first_y, 0],
                           [x+half-2*max_half, last_y, 0],
                           [x+half-2*max_half, length, 0],
                           [x+half, length, 0], [x+half, first_y, 0]]
                bodies.append(ProbeBody(outline, thickness, s))
            else:
                bodies.append(_body(s, s*pitch, length, thickness, profile))
        geometry = _probe(name, 'NeuroNexus', contacts, bodies, NEURONEXUS, page,
                          f'{shanks} shanks; {pitch:g} um tip pitch; sites ordered tip-to-base then left-to-right.',
                          site_area_um2=area)
        if note:
            geometry.metadata.update(geometry_note=note, provisional=True)
        entries.append((Path('NeuroNexus') / f'{name}.json', geometry, ChannelMap(n_channels=len(contacts))))
        assignments[name] = maps

    edge_note = ('Provisional lateral site centers: nominal pad centers along the straight right edge; '
                 'the catalog does not fully dimension their registration to the tip. '
                 'Exact lateral error is unknown. Axial pitch, tip offset and shank pitch follow catalog dimensions.')
    add('A1x64-Edge-6mm-20-177', 77, 1, 0, 6000, 15,
        [(4.5, 40+20*i) for i in range(64)], [(40,13.5),(1300,55)],
        ['activus64_p1','h64lp_p6'], edge=True, note=edge_note)
    for length, pitch, width, thickness, page in (
        (5000,25,97,15,79), (5000,100,106,15,80),
        (6000,70,96,50,81), (8000,35,96,50,82),
    ):
        add(f'A2x32-{length//1000}mm-{pitch}-200-177', page, 2, 200, length, thickness,
            [(0,50+pitch*i) for i in range(32)], [(50,14),(50+31*pitch,width/2)], ['activus64_p2'])

    # A tetrode is a diamond with 25 um nearest-neighbor center spacing.
    d = 25/sqrt(2)
    tet = [(x,50+150*cluster+y) for cluster in range(4)
           for x,y in ((0,0),(-d,d),(d,d),(0,2*d))]
    add('A4x4-tet-5mm-150-200-121',87,4,200,5000,15,tet,
        [(50+d,29),(500+2*d,50)],['h64lp_p7'],area=121)
    add('A4x16-3mm-50-200-177',88,4,200,3000,15,
        [(0,50+50*i) for i in range(16)],[(50,13.5),(800,40.5)],['activus64_p4','h64lp_p8'])
    poly3 = [(0,35+20*i) for i in range(6)] + [(x,45+20*i) for i in range(5) for x in (-sqrt(300),sqrt(300))]
    add('A4x16-poly3-5mm-20s-200-160',94,4,200,5000,15,poly3,
        [(45,27),(135,32)],['activus64_p6'],area=160)

    for length, page, thickness in ((5000,97,15),(10000,98,50)):
        for area in (177,703):
            add(f'A8x8-{length//1000}mm-200-200-{area}',page,8,200,length,thickness,
                [(0,50+200*i) for i in range(8)],[(50,16.5),(1450,41.5)],['h64lp_p10'],area=area)
    for step, pitch, page in ((50,150,99),(100,200,100)):
        add(f'A8x8-Edge-5mm-{step}-{pitch}-177',page,8,pitch,5000,15,
            [(6.5,50+step*i) for i in range(8)],[(50,14),(50+7*step,30)],['h64lp_p11'],
            edge=True,note=edge_note)

    buz_x = [0,-8.5,8.5,-12.5,12.5,-16.5,16.5,-20.5]
    add('Buzsaki64',101,8,200,5000,15,[(x,22+20*i) for i,x in enumerate(buz_x)],
        [(22,14.5),(162,26)],['h64lp_p12'],area=160)
    sp_x = [0,-7,7.5,-9.5,10,-12,12.5,-14.5,15,-17]
    for name,length,page,thickness in (('Buzsaki64sp',5000,105,15),('Buzsaki64spL',10000,107,50)):
        add(name,page,6,200,length,thickness,
            lambda s: [(x,20+20*i) for i,x in enumerate(sp_x)] +
                      ([(0,y) for y in (500,1000,1500,2000)] if s==3 else []),
            [(20,14.5),(200,23.5)],['h64lp_p13'],area=160)

    poly4 = [(x,50+20*r) for r in range(17) for x in ((-10,10) if r<2 else (-30,-10,10,30))]
    add('A2x64-Poly4-10mm-20-800-100',111,2,800,10000,15,poly4,
        [(90,38.5),(370,84.5)],['activus128_p1'],area=100)
    add('A4x32-Poly2-5mm-23s-200-177',115,4,200,5000,15,
        [(15*(-1)**i,50+23*i) for i in range(32)],[(50,26),(763,50)],['activus128_p3'])
    add('A4x32-Poly2-lin-5mm-20s-150-160',116,4,150,5000,15,
        lambda s: [(sqrt(300)/2*(-1)**i,35+10*i) for i in range(30)] +
                  [(0,425+100*s),(0,525+100*s)],
        [(35,16),(325,38.5)],['activus128_p2'],area=160)
    for step,pitch,area,width,page in ((30,500,121,100,120),(50,150,177,76,121),(100,200,177,76,122)):
        half = 11 if area==121 else 14
        pad = 11 if area==121 else 15
        add(f'A8x16-Edge-5mm-{step}-{pitch}-{area}',page,8,pitch,5000,15,
            [(half-pad/2,50+step*i) for i in range(16)],[(50,half),(50+15*step,width/2)],
            ['activus128_p5'],area=area,edge=True,note=edge_note)
    add('A16x8-5mm-berg-200-160',123,16,200,5000,15,
        [(x,22+30*i) for i,x in enumerate(buz_x)],[(22,14),(232,26),(1000,28.5)],
        ['activus128_berg'],area=160)

    reasons = {
        'A6x21-poly2-10mm-50-200-160': 'No matching A6x21 channel map was found in the official 128-channel package PDFs. Geometry corrected: Shank 2 has 23 sites; all others have 21.',
        'Buzsaki-5x12': 'HZ64 probe-pin maps exist, but the complete recording-headstage route is not registered.',
        'A5x12-16-Buz-Lin-5mm-100-200-160-177': 'The available Activus map describes the 3-4 mm variant, not this 5 mm / 6.2 mm design. Its channel assignment is not assumed to match.',
    }
    # These have separate A64 source pages, even where the site-to-pin orders
    # happen to agree. Never apply the A64 connector routing to OA64LP V2.
    a64_pages = {'h64lp_p7':2, 'h64lp_p8':3, 'h64lp_p10':4,
                 'h64lp_p11':5, 'h64lp_p12':6, 'h64lp_p13':7}
    for keys in assignments.values():
        keys += [f'a64_p{a64_pages[k]}' for k in list(keys) if k in a64_pages]
    for _, geometry, mapping in entries:
        if geometry.metadata.get('manufacturer') != 'NeuroNexus':
            continue
        geometry.metadata['catalog_sha256'] = data['catalog_sha256']
        geometry.metadata['connection_label'] = 'Package / headstage'
        geometry.metadata['routing_note'] = 'Choose the exact package / headstage. Other connections remain unassigned.'
        profiles = []
        for key in assignments.get(geometry.name, []):
            record = data['maps'][key]
            groups = record['groups_tip_to_base']
            shanks = sorted({c.shank_id for c in geometry.contacts})
            if len(groups) != len(shanks):
                raise ValueError(f'Wrong shank count in {key} for {geometry.name}')
            count = len(geometry.contacts)
            if count not in (64,128):
                raise ValueError('Only 64/128-channel NeuroNexus models are covered.')
            source_numbers = {}
            for shank, numbers in zip(shanks, groups, strict=True):
                contacts = sorted((c for c in geometry.contacts if c.shank_id == shank),key=lambda c:(c.y_um,c.x_um))
                for contact, number in zip(contacts,numbers,strict=True):
                    source_numbers[contact.contact_id] = number
            connection_ids = (['h64lp_smartlink64_chronic', 'h64lp_intan_rhd64'] if key.startswith('h64lp')
                              else ['a64_smartlink64_acute'] if key.startswith('a64') else [None])
            for connection_id in connection_ids:
                profile = {k:v for k,v in record.items() if k != 'groups_tip_to_base'}
                profile.update(source_numbering=record['numbering'],numbering='zero-based recording channel')
                if connection_id:
                    connection = data['connections'][connection_id]
                    profile.update(id=f'neuronexus_{connection_id}',label=connection['label'],
                                   headstage_source_url=connection['headstage_source_url'],
                                   headstage_source_sha256=connection['headstage_source_sha256'],
                                   headstage_pdf_page=connection['headstage_pdf_page'],connector_pdf_page=1,
                                   note=f"{connection['label']} only. Channel IDs are zero-based amplifier inputs; verify the reference configuration and acquisition order."
                                        + (' Not for OA64LP V2.' if key.startswith('a64') else ''))
                    routing = {site:connection['pin_to_channel'][str(pin)] for site,pin in source_numbers.items()}
                else:
                    profile.update(id=f'neuronexus_activus{count}',
                                   label=f'Activus {count} (AV / AVH / AVI / AVIH)',
                                   note=f'Official Activus {count} channel numbering (0-{count-1}). Use only the AV / AVH / AVI / AVIH package variants listed in this map.')
                    routing = dict(source_numbers)
                if sorted(routing.values()) != list(range(count)):
                    raise ValueError(f'Incomplete or repeated recording channels in {key}')
                profile.update(n_channels=count,contact_to_channel=routing,source_contact_numbers=source_numbers)
                profiles.append(profile)
        if profiles:
            geometry.metadata['headstage_profiles'] = profiles
            for profile in profiles:
                headstage_map(geometry,profile['id'])
        else:
            geometry.metadata['wiring_unavailable_reason'] = reasons[geometry.name]
        if geometry.name == 'A6x21-poly2-10mm-50-200-160':
            # User-requested placeholder IDs, not a manufacturer wiring claim.
            ordered = sorted(geometry.contacts, key=lambda c: (c.shank_id, c.y_um, c.x_um))
            mapping.contact_to_channel = {c.contact_id: i for i, c in enumerate(ordered)}
            mapping.groups = [[mapping.contact_to_channel[c.contact_id] for c in ordered if c.shank_id == s]
                              for s in sorted({c.shank_id for c in ordered})]
            geometry.metadata['provisional_channel_map'] = True
            geometry.metadata['channel_map_note'] = (
                'Provisional Channel IDs 0-127: left-to-right shanks, tip-to-base within each shank. '
                'Assigned at user request; manufacturer recording wiring is not verified.')
            geometry.metadata['routing_note'] = geometry.metadata['channel_map_note']
            mapping.validate(geometry)
