"""SceneV2 public contract: scenes can draw only inside the reserved stage."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Protocol, Tuple

from PIL import Image, ImageDraw

from engine import blueprint_engine as bp

STAGE_BOUNDS = (48, 400, 672, 950)
STAGE_SIZE = (STAGE_BOUNDS[2] - STAGE_BOUNDS[0], STAGE_BOUNDS[3] - STAGE_BOUNDS[1])


@dataclass(frozen=True)
class FrameContext:
    frame: int
    frame_count: int
    fps: int
    progress: float
    beat: int
    beat_progress: float
    stage_bounds: Tuple[int, int, int, int]
    theme: Mapping[str, tuple[int, int, int]]


class StageSurface:
    """A stage-local image. Coordinates outside the stage are clipped by Pillow."""

    def __init__(self, size: tuple[int, int] = STAGE_SIZE):
        self.image = Image.new("RGBA", size, (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.width, self.height = size


class SceneV2(Protocol):
    SCENE: dict

    def draw_stage(self, surface: StageSurface, context: FrameContext) -> None: ...


THEME = MappingProxyType({
    name: getattr(bp, name)
    for name in ("BG", "WHITE", "MUTED", "DIM", "TEAL", "AMBER", "RED", "BLUE", "GREEN")
})


def frame_context(frame: int, frame_count: int, fps: int = 30) -> FrameContext:
    progress = 0.0 if frame_count <= 1 else frame / (frame_count - 1)
    if progress < .3:
        beat, start, end = 1, 0.0, .3
    elif progress < .6:
        beat, start, end = 2, .3, .6
    else:
        beat, start, end = 3, .6, 1.0
    return FrameContext(
        frame=frame, frame_count=frame_count, fps=fps, progress=progress,
        beat=beat, beat_progress=min(1.0, max(0.0, (progress - start) / (end - start))),
        stage_bounds=STAGE_BOUNDS, theme=THEME,
    )

