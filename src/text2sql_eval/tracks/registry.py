from __future__ import annotations

from .base import BaseTrack
from .track_a import TrackA
from .track_b import TrackB
from .track_c import TrackC

TRACK_REGISTRY: dict[str, type[BaseTrack]] = {
    "a": TrackA,
    "b": TrackB,
    "c": TrackC,
}


def get_track(name: str) -> BaseTrack:
    track_type = TRACK_REGISTRY.get(name)
    if track_type is None:
        raise ValueError(f"Unknown track '{name}'. Available: {list(TRACK_REGISTRY)}")
    return track_type()
