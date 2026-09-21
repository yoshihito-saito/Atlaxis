"""Explicit recording-channel profiles for a probe and headstage combination."""

from .model import ChannelMap


def headstage_map(geometry, profile_id):
    profiles = geometry.metadata.get("headstage_profiles", [])
    if profile_id is None:
        return ChannelMap(n_channels=max((p["n_channels"] for p in profiles), default=len(geometry.contacts)))
    profile = next((p for p in profiles if p["id"] == profile_id), None)
    if profile is None:
        raise ValueError(f"No verified headstage profile '{profile_id}' for {geometry.name}.")
    channels = dict(profile["contact_to_channel"])
    groups = [sorted(channels[c.contact_id] for c in geometry.contacts
                     if c.shank_id == shank and c.contact_id in channels)
              for shank in sorted({c.shank_id for c in geometry.contacts})]
    mapping = ChannelMap(channels, profile["n_channels"], groups, headstage_id=profile_id)
    mapping.validate(geometry)
    return mapping


def headstage_label(geometry, mapping):
    return next((p["label"] for p in geometry.metadata.get("headstage_profiles", [])
                 if p["id"] == mapping.headstage_id), "")
