from __future__ import annotations

from .base import BaseTrack
from .track_a import TrackA
from .track_b import TrackB

TRACK_REGISTRY: dict[str, type[BaseTrack]] = {
    "a": TrackA,
    "b": TrackB,
}


def get_track(name: str) -> BaseTrack:
    track_type = TRACK_REGISTRY.get(name)
    if track_type is None:
        raise ValueError(f"Unknown track '{name}'. Available: {list(TRACK_REGISTRY)}")
    return track_type()
