"""Channel-aligned NeuroScope / CellExplorer companions, in local micrometers.

Run with --probemaps-source-dir PATH to copy the pinned source XMLs as well.
No acquisition channel is invented for an unassigned site.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree as ET

import numpy as np
from scipy.io import savemat

from .importers import load_geometry_json
from .library import probe_library_path
from .probemaps import LOCK
from .wiring import headstage_map


def channel_companions(geometry, mapping, *, active_sites=None, note='', xml_channel_offset=0):
    """Return XML text and MAT bytes using unchanged device-channel indices.

    MAT row i describes zero-based device channel i. Unmapped inputs retain NaN
    coordinates and connected=false; they must not shift subsequent channels.
    chanCoords.channel is one-based for MATLAB; shank remains zero-based, as in
    the Atlaxis importer. Library coordinates are probe-local, not atlas-space.
    """
    mapping.validate(geometry)
    count = mapping.n_channels
    active_sites = set(mapping.contact_to_channel) if active_sites is None else set(active_sites)
    if not active_sites.issubset(mapping.contact_to_channel):
        raise ValueError('Active coordinates require an assigned channel.')
    xyz = np.full((count, 3), np.nan)
    shanks = np.full(count, -1, dtype=np.int32)
    sites = np.full(count, '', dtype=object)
    active = np.zeros(count, dtype=bool)
    groups = {}
    for c in geometry.contacts:
        channel = mapping.contact_to_channel.get(c.contact_id)
        if channel is None:
            continue
        xyz[channel] = [c.x_um, c.y_um, c.z_um]
        shanks[channel] = c.shank_id
        sites[channel] = c.contact_id
        active[channel] = c.contact_id in active_sites and channel not in mapping.skipped
        groups.setdefault(c.shank_id, []).append(channel)
    root = ET.Element('parameters', version='1.0')
    root.append(ET.Comment('Channel-group template; add actual acquisition metadata. '+note.replace('--','- -')))
    ET.SubElement(ET.SubElement(root,'acquisitionSystem'),'nChannels').text = str(count)
    anatomy = ET.SubElement(ET.SubElement(root,'anatomicalDescription'),'channelGroups')
    for shank in sorted(groups):
        anatomy.append(ET.Comment(f'Zero-based shank {shank}'))
        group = ET.SubElement(anatomy,'group')
        for channel in sorted(groups[shank], key=lambda ch:(-geometry.y_to_base*xyz[ch,1], xyz[ch,0])):
            ET.SubElement(group,'channel',skip='0' if active[channel] else '1').text = str(channel)
    missing = np.flatnonzero(shanks < 0)
    if len(missing):
        anatomy.append(ET.Comment('Unassigned inputs; no inferred coordinates'))
        group = ET.SubElement(anatomy,'group')
        for channel in missing:
            ET.SubElement(group,'channel',skip='1').text = str(channel)
    ET.indent(root)
    xml = '<?xml version="1.0" encoding="utf-8"?>\n'+ET.tostring(root,encoding='unicode')+'\n'
    coords = {
        'x':xyz[:,0], 'y':xyz[:,1], 'z':xyz[:,2],
        'channel':np.arange(1,count+1,dtype=np.int32), 'shank':shanks,
        'site_id':sites, 'connected':shanks >= 0, 'active':active,
        'units':'um', 'shank_index_base':0, 'source':geometry.name,
        'headstage_id':mapping.headstage_id or '',
        'coordinate_system':'Probe-local XYZ; +y toward base' if geometry.y_to_base == 1 else 'Probe-local XYZ; -y toward base',
        'notes':note,
        'provisional':bool(geometry.metadata.get('provisional_channel_map')),
        'combined_xml_channel':np.arange(count,dtype=np.int32)+xml_channel_offset,
    }
    stream = io.BytesIO()
    savemat(stream, {'chanCoords':coords}, oned_as='column', do_compression=True)
    return xml, stream.getvalue()


def _copy_probemaps(library, source_dir):
    lock = json.loads(LOCK.read_text(encoding='utf-8'))
    for record in lock['files']:
        data = (source_dir / record['source_path']).read_bytes()
        digest = hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
        if digest != record['git_blob_sha1']:
            raise ValueError(f"XML differs from pinned ProbeMaps source: {record['source_path']}")
        folder = library / 'NeuroNexus' / record['folder'] / 'ProbeMaps'
        folder.mkdir(parents=True, exist_ok=True)
        name = Path(record['source_path']).name
        (folder / name).write_bytes(data)
        url = f"{lock['repository']}/blob/{lock['revision']}/{quote(record['source_path'])}"
        (folder / 'README.md').write_text(
            f'# Original ProbeMaps XML\n\n[Source]({url}) · git blob `{digest}`.\n\n'
            'Original bytes and channel order are preserved. This XML includes upstream\n'
            'acquisition settings; use the settings of your actual recording.\n\n'
            + (record.get('reason') or 'The corresponding normal XML profile is selectable in Atlaxis; other headstage profiles remain separate.')
            +'\n', encoding='utf-8')
        if record['status'] == 'reference_only':
            (folder.parent / 'README.md').write_text(
                '# Reference XML only\n\n'+record['reason']+'\n\n'
                'No importable probe JSON or inferred channel-coordinate file is supplied.\n'
                'The original XML and provenance are in ProbeMaps/.\n',encoding='utf-8')


def write_library_companions(library, source_dir=None):
    models, pairs, deferred = 0, 0, 0
    # Only the established flat geometry library, never source/manifest JSONs.
    for manufacturer in ('NeuroNexus','Cambridge NeuroTech','Neuropixels'):
        for path in sorted((library / manufacturer).glob('*.json')):
            if path.name.startswith('.'):
                continue  # The Cambridge converter's .manifest.json is not geometry.
            geometry, mapping = load_geometry_json(path)
            folder = path.with_suffix('')
            folder.mkdir(exist_ok=True)
            lines = [f'# {geometry.name}', '', f'Import [the existing geometry JSON](../{quote(path.name)}).', '',
                     'XML uses zero-based local channels. CellExplorer MAT uses one-based channel IDs;',
                     'MAT row i+1 always describes device channel i. XYZ are local micrometers.',
                     'XML groups list sites base-to-tip within each left-to-right shank.',
                     'Unassigned inputs have NaN coordinates and connected=false; they are not renumbered.',
                     'Shank IDs are zero-based. For CellExplorer, rename the selected MAT file to',
                     '`<session>.chanCoords.channelInfo.mat`. XML files are channel-group templates;',
                     'merge actual acquisition metadata before use.', '']
            models += 1
            if manufacturer == 'Neuropixels':
                lines += ['Select active channels in Atlaxis, then Save & update. The planning folder',
                          'receives current per-probe XML/chanCoords companions. No static all-site',
                          'acquisition map is supplied. IMRO remains a separate manual Export.']
            else:
                profiles = geometry.metadata.get('headstage_profiles', [])
                variants = [(p['id'],headstage_map(geometry,p['id']),p['note']) for p in profiles]
                if not profiles and mapping.contact_to_channel:
                    label = 'provisional' if geometry.metadata.get('provisional_channel_map') else 'recording'
                    variants = [(label,mapping,geometry.metadata.get('channel_map_note','Supplied recording wiring.'))]
                if not variants:
                    deferred += 1
                    lines += ['No confirmed recording-channel map is available. No XML or acquisition',
                              'chanCoords is generated; the existing geometry JSON is unchanged.']
                for label, channels, note in variants:
                    stem = f'{geometry.name}__{label}'
                    xml, mat = channel_companions(geometry,channels,note=note)
                    (folder / f'{stem}.xml').write_text(xml,encoding='utf-8')
                    (folder / f'{stem}.chanCoords.channelInfo.mat').write_bytes(mat)
                    lines += [f'## {label}', '', note, '',
                              f'- [XML]({quote(stem)}.xml)',
                              f'- [CellExplorer coordinates]({quote(stem)}.chanCoords.channelInfo.mat)', '']
                    pairs += 1
            if manufacturer == 'NeuroNexus':
                lines += ['', 'Any original ProbeMaps XML is kept separately in `ProbeMaps/`.']
            (folder / 'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    if source_dir is not None:
        _copy_probemaps(library,source_dir)
    print(f'{models} model folders; {pairs} XML/MAT pairs; {deferred} unassigned models deferred; NP exports follow selection.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,default=probe_library_path())
    parser.add_argument('--probemaps-source-dir',type=Path)
    args = parser.parse_args()
    write_library_companions(args.library,args.probemaps_source_dir)
