from dataclasses import dataclass
from math import floor
from typing import Tuple


@dataclass(frozen=True)
class NormalizedCrop:
    """A selected rectangle expressed as fractions of a monitor/stream."""

    x: float
    y: float
    width: float
    height: float

    def validate(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if any(value < 0.0 or value > 1.0 for value in values):
            raise ValueError("Crop fractions must be between 0 and 1")
        if self.width <= 0.0 or self.height <= 0.0:
            raise ValueError("Crop width and height must be positive")
        if self.x + self.width > 1.000001:
            raise ValueError("Crop rectangle exceeds source width")
        if self.y + self.height > 1.000001:
            raise ValueError("Crop rectangle exceeds source height")


def normalized_crop_from_selection(
    x: float,
    y: float,
    width: float,
    height: float,
    canvas_width: int,
    canvas_height: int,
) -> NormalizedCrop:
    if canvas_width <= 0 or canvas_height <= 0:
        raise ValueError("Selection canvas must have a positive size")

    left = max(0.0, min(float(canvas_width), x))
    top = max(0.0, min(float(canvas_height), y))
    right = max(
        left,
        min(float(canvas_width), x + width),
    )
    bottom = max(
        top,
        min(float(canvas_height), y + height),
    )

    crop = NormalizedCrop(
        x=left / canvas_width,
        y=top / canvas_height,
        width=(right - left) / canvas_width,
        height=(bottom - top) / canvas_height,
    )
    crop.validate()
    return crop


def crop_margins_for_stream(
    crop: NormalizedCrop,
    stream_width: int,
    stream_height: int,
) -> Tuple[int, int, int, int]:
    """Return even-output (left, right, top, bottom) crop margins."""

    crop.validate()
    if stream_width < 2 or stream_height < 2:
        raise ValueError("Stream is too small for area recording")

    left = floor(crop.x * stream_width)
    top = floor(crop.y * stream_height)
    right_edge = floor((crop.x + crop.width) * stream_width)
    bottom_edge = floor((crop.y + crop.height) * stream_height)

    left = max(0, min(stream_width - 2, left))
    top = max(0, min(stream_height - 2, top))
    right_edge = max(left + 2, min(stream_width, right_edge))
    bottom_edge = max(top + 2, min(stream_height, bottom_edge))

    # Keep I420/H.264 output dimensions even. Align the start down,
    # then shrink the selected extent by at most one pixel if needed.
    left -= left % 2
    top -= top % 2

    width = right_edge - left
    height = bottom_edge - top
    width -= width % 2
    height -= height % 2

    if width < 2:
        width = 2
    if height < 2:
        height = 2

    if left + width > stream_width:
        width = stream_width - left
        width -= width % 2
    if top + height > stream_height:
        height = stream_height - top
        height -= height % 2

    if width < 2 or height < 2:
        raise ValueError("Selected recording area is too small")

    right = stream_width - (left + width)
    bottom = stream_height - (top + height)
    return left, right, top, bottom
